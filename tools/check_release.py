#!/usr/bin/env python3
"""Read-only validation for deterministic formal-release packages."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from release_context import FormalReleaseContextError, parse_formal_release_context
from release_manifest import (
    PRODUCT_ORDER,
    ReleaseManifestError,
    load_and_validate_release_manifest,
)

from build_release import (
    CHECKSUM_PATHS,
    DEVELOPMENT_OUTPUT_PATHS,
    PACKAGE_FILE_PATHS,
    PRODUCT_PACKAGE_PATHS,
    ReleasePackageIssue,
    ResolvedValidationToolchain,
    assemble_release_package,
    canonical_catalog_bytes,
    collect_dependencies,
    collect_included_files,
    collect_inputs,
    collect_product_records,
    collect_validation_environment,
    compare_complete_packages,
    development_snapshot_issues,
    formal_product_bytes,
    package_issue,
    render_formal_products,
    resolve_validation_toolchain,
    snapshot_development_outputs,
    validate_catalog_bytes,
    validate_release_notes_bytes,
    validate_sha256sums_bytes,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DIRECTORIES = (
    "current-ssn-sosa",
    "evidence",
    "sources",
)


def _layout_issues(package_dir: Path) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []
    if not package_dir.is_dir() or package_dir.is_symlink():
        return (package_issue("PACKAGE_DIRECTORY", "package_dir", "expected real directory"),)
    observed_files: list[str] = []
    observed_directories: list[str] = []
    for path in sorted(package_dir.rglob("*"), key=lambda value: value.relative_to(package_dir).as_posix()):
        relative = path.relative_to(package_dir).as_posix()
        if path.is_symlink():
            issues.append(package_issue("PACKAGE_SYMLINK", relative, "symlinks are prohibited"))
        elif path.is_dir():
            observed_directories.append(relative)
        elif path.is_file():
            observed_files.append(relative)
        else:
            issues.append(package_issue("PACKAGE_SPECIAL_FILE", relative, "only regular files and directories are permitted"))
        if any(part.startswith(".") for part in path.relative_to(package_dir).parts):
            issues.append(package_issue("PACKAGE_HIDDEN_PATH", relative, "hidden paths are prohibited"))
    if tuple(observed_files) != PACKAGE_FILE_PATHS:
        missing = sorted(set(PACKAGE_FILE_PATHS) - set(observed_files))
        extra = sorted(set(observed_files) - set(PACKAGE_FILE_PATHS))
        issues.append(package_issue("PACKAGE_FILE_SET", "package", f"missing={missing!r}; extra={extra!r}"))
    if tuple(observed_directories) != EXPECTED_DIRECTORIES:
        missing = sorted(set(EXPECTED_DIRECTORIES) - set(observed_directories))
        extra = sorted(set(observed_directories) - set(EXPECTED_DIRECTORIES))
        issues.append(package_issue("PACKAGE_DIRECTORY_SET", "package", f"missing={missing!r}; extra={extra!r}"))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _copied_input_issues(package_dir: Path, repository_root: Path, manifest) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []
    by_key = {value.key: value for value in manifest.inputs}
    release_notes = by_key.get("release_notes")
    if release_notes is None:
        return (package_issue("RELEASE_NOTES_INPUT", "inputs", "release_notes input is absent"),)
    notes_source = repository_root / release_notes.source_path
    if not notes_source.is_file():
        issues.append(package_issue("INPUT_SOURCE_MISSING", release_notes.source_path, "recorded release-notes source is absent"))
        return tuple(issues)
    try:
        expected_inputs = collect_inputs(repository_root, release_notes.source_path)
    except (OSError, ValueError) as exc:
        return (package_issue("INPUT_EVIDENCE", "inputs", str(exc)),)
    if manifest.inputs != expected_inputs:
        issues.append(package_issue("INPUT_EVIDENCE_MISMATCH", "inputs", "manifest input records differ from repository bytes"))
    for record in manifest.inputs:
        if record.package_path is None:
            continue
        package_path = package_dir / record.package_path
        source_path = repository_root / record.source_path
        if not package_path.is_file() or not source_path.is_file():
            issues.append(package_issue("COPIED_INPUT_MISSING", record.package_path, "source or package copy is absent"))
        elif package_path.read_bytes() != source_path.read_bytes():
            issues.append(package_issue("COPIED_INPUT_MISMATCH", record.package_path, "package copy differs byte-for-byte from source"))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _local_path_leakage_issues(package_dir: Path, repository_root: Path) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []
    prohibited = (
        str(repository_root).encode("utf-8"),
        b"file://",
        b"/.release-package-build-",
    )
    for relative in PACKAGE_FILE_PATHS:
        value = (package_dir / relative).read_bytes()
        for marker in prohibited:
            if marker and marker in value:
                issues.append(package_issue("LOCAL_PATH_LEAKAGE", relative, f"contains prohibited marker {marker.decode('utf-8', errors='replace')!r}"))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def validate_release_package(
    package_dir: Path,
    *,
    repository_root: Path = REPO_ROOT,
    toolchain: ResolvedValidationToolchain | None = None,
) -> tuple[ReleasePackageIssue, ...]:
    """Independently validate package bytes without modifying the package."""

    package_dir = Path(package_dir)
    repository_root = Path(repository_root).resolve()
    snapshots = snapshot_development_outputs(repository_root)
    issues: list[ReleasePackageIssue] = list(_layout_issues(package_dir))
    if issues:
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))
    try:
        manifest = load_and_validate_release_manifest(package_dir / "manifest.json")
    except ReleaseManifestError as exc:
        issues.extend(package_issue(value.code, value.field, value.message) for value in exc.issues)
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))
    if package_dir.name != manifest.release_identifier:
        issues.append(package_issue("PACKAGE_BASENAME", "package_dir", f"expected {manifest.release_identifier!r}, got {package_dir.name!r}"))
    try:
        context = parse_formal_release_context(
            manifest.release_identifier,
            manifest.release_date,
            manifest.git_tag,
            manifest.source_commit,
        )
    except FormalReleaseContextError as exc:
        issues.extend(package_issue(value.code, value.field, value.message) for value in exc.issues)
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))

    note_issues = validate_release_notes_bytes(
        (package_dir / "RELEASE-NOTES.md").read_bytes(),
        template_bytes=(repository_root / "release-notes/TEMPLATE.md").read_bytes(),
    )
    issues.extend(note_issues)
    issues.extend(_copied_input_issues(package_dir, repository_root, manifest))
    try:
        package_metadata, rendered = render_formal_products(
            context,
            package_dir / "sources/SSN2BFO-COMS.xlsx",
            package_dir / "sources/publication-metadata.toml",
            package_dir / "evidence/coms-product-dispositions.json",
        )
    except Exception as exc:
        issues.append(package_issue("FORMAL_RENDERING", "products", str(exc)))
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))

    expected_bytes = formal_product_bytes(rendered)
    for key in PRODUCT_ORDER:
        path = package_dir / PRODUCT_PACKAGE_PATHS[key]
        if path.read_bytes() != expected_bytes[key]:
            issues.append(package_issue("FORMAL_PRODUCT_MISMATCH", PRODUCT_PACKAGE_PATHS[key], "bytes differ from same-input formal rendering"))
    expected_products = collect_product_records(rendered, package_metadata, context)
    if manifest.products != expected_products:
        issues.append(package_issue("PRODUCT_EVIDENCE_MISMATCH", "products", "manifest product records differ from recomputed formal products"))
    if manifest.product_order != PRODUCT_ORDER:
        issues.append(package_issue("PRODUCT_ORDER", "product_order", "canonical product order differs"))

    catalog_value = (package_dir / "catalog-v001.xml").read_bytes()
    issues.extend(validate_catalog_bytes(catalog_value, package_metadata, context))
    sums_value = (package_dir / "SHA256SUMS").read_bytes()
    issues.extend(validate_sha256sums_bytes(package_dir, sums_value))
    try:
        resolved_toolchain = toolchain or resolve_validation_toolchain(repository_root)
        expected_dependencies = collect_dependencies(repository_root)
        expected_environment = collect_validation_environment(repository_root, resolved_toolchain)
    except Exception as exc:
        issues.append(package_issue("VALIDATION_EVIDENCE", "validation_environment", str(exc)))
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))
    if manifest.dependencies != expected_dependencies:
        issues.append(package_issue("DEPENDENCY_EVIDENCE_MISMATCH", "dependencies", "records differ from explicit pinned files"))
    if manifest.validation_environment != expected_environment:
        issues.append(package_issue("VALIDATION_ENVIRONMENT_MISMATCH", "validation_environment", "records differ from current declared toolchain"))
    expected_included = collect_included_files(package_dir)
    if manifest.included_files != expected_included:
        issues.append(package_issue("INCLUDED_FILE_EVIDENCE_MISMATCH", "included_files", "records differ from package files"))
    issues.extend(_local_path_leakage_issues(package_dir, repository_root))

    if issues:
        issues.extend(development_snapshot_issues(repository_root, snapshots))
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))

    with tempfile.TemporaryDirectory(prefix="release-package-validation-") as directory:
        try:
            notes_relative = next(
                value.source_path for value in manifest.inputs if value.key == "release_notes"
            )
            reconstructed = Path(directory) / context.release_identifier
            assemble_release_package(
                context,
                (package_dir / "RELEASE-NOTES.md").read_bytes(),
                notes_relative,
                reconstructed,
                repository_root,
                resolved_toolchain,
                snapshots,
            )
            issues.extend(compare_complete_packages(package_dir, reconstructed))
        except Exception as exc:
            issues.append(
                package_issue(
                    "PACKAGE_RECONSTRUCTION",
                    "package",
                    str(exc),
                )
            )
            return tuple(sorted(set(issues), key=lambda value: value.sort_key))
    issues.extend(development_snapshot_issues(repository_root, snapshots))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="Validate one existing package read-only.")
    validate.add_argument("--package-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    issues = validate_release_package(args.package_dir)
    if issues:
        for issue in issues:
            print(f"ERROR [{issue.code}] {issue.field}: {issue.message}")
        return 1
    print(f"Release package validation: PASS ({args.package_dir})")
    print(f"Regular files: {len(PACKAGE_FILE_PATHS)}")
    print(f"Checksummed files: {len(CHECKSUM_PATHS)}")
    print(f"Development artifacts checked: {len(DEVELOPMENT_OUTPUT_PATHS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
