#!/usr/bin/env python3
"""Read-only validation for one SOSA-2023 formal release package."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import sosa_2023_build_release as build
import sosa_2023_release_manifest as manifest
import sosa_2023_release_runtime as runtime
from release_context import parse_formal_release_context


REPO_ROOT = Path(__file__).resolve().parents[1]

PRODUCT_ORDER = build.PRODUCT_ORDER
PRODUCT_PACKAGE_PATHS = build.PRODUCT_PACKAGE_PATHS
INCLUDED_FILE_PATHS = build.INCLUDED_FILE_PATHS
PACKAGE_FILE_PATHS = build.PACKAGE_FILE_PATHS
CHECKSUM_PATHS = build.CHECKSUM_PATHS
DEVELOPMENT_OUTPUT_PATHS = build.DEVELOPMENT_OUTPUT_PATHS

ReleasePackageIssue = runtime.ReleasePackageIssue
ResolvedValidationToolchain = runtime.ResolvedValidationToolchain

package_issue = runtime.package_issue


def _safe_relative_path(
    value: str,
    *,
    field: str,
) -> Path:
    path = Path(value)

    if path.is_absolute():
        raise ValueError(
            f"{field}: absolute paths are prohibited"
        )

    if any(
        part in ("", ".", "..")
        for part in path.parts
    ):
        raise ValueError(
            f"{field}: non-canonical relative path "
            f"{value!r}"
        )

    return path


def _expected_directories() -> tuple[str, ...]:
    values: set[str] = set()

    for relative in PACKAGE_FILE_PATHS:
        parent = Path(relative).parent

        while parent != Path("."):
            values.add(
                parent.as_posix()
            )
            parent = parent.parent

    return tuple(sorted(values))


EXPECTED_DIRECTORY_PATHS = _expected_directories()


def _layout_issues(
    package_dir: Path,
) -> tuple[ReleasePackageIssue, ...]:
    package_dir = Path(package_dir)

    issues: list[ReleasePackageIssue] = []

    if package_dir.is_symlink():
        return (
            package_issue(
                "PACKAGE_SYMLINK",
                "package_dir",
                "package root must not be a symlink",
            ),
        )

    if not package_dir.is_dir():
        return (
            package_issue(
                "PACKAGE_MISSING",
                "package_dir",
                "package directory is absent",
            ),
        )

    observed_files: list[str] = []
    observed_directories: list[str] = []

    for path in sorted(
        package_dir.rglob("*"),
        key=lambda item: (
            item.relative_to(
                package_dir
            ).as_posix()
        ),
    ):
        relative = path.relative_to(
            package_dir
        ).as_posix()

        if path.is_symlink():
            issues.append(
                package_issue(
                    "PACKAGE_SYMLINK",
                    relative,
                    "package entries must not "
                    "be symlinks",
                )
            )
            continue

        if path.is_file():
            observed_files.append(
                relative
            )
        elif path.is_dir():
            observed_directories.append(
                relative
            )
        else:
            issues.append(
                package_issue(
                    "PACKAGE_SPECIAL_FILE",
                    relative,
                    "package contains a "
                    "non-regular entry",
                )
            )

    if tuple(observed_files) != (
        PACKAGE_FILE_PATHS
    ):
        issues.append(
            package_issue(
                "PACKAGE_FILE_INVENTORY",
                "package",
                "expected "
                f"{PACKAGE_FILE_PATHS!r}, "
                f"got {tuple(observed_files)!r}",
            )
        )

    if tuple(observed_directories) != (
        EXPECTED_DIRECTORY_PATHS
    ):
        issues.append(
            package_issue(
                "PACKAGE_DIRECTORY_INVENTORY",
                "package",
                "expected "
                f"{EXPECTED_DIRECTORY_PATHS!r}, "
                f"got "
                f"{tuple(observed_directories)!r}",
            )
        )

    return tuple(
        sorted(
            set(issues),
            key=lambda value: value.sort_key,
        )
    )


def _copied_input_issues(
    package_dir: Path,
    repository_root: Path,
    release_manifest: manifest.ReleaseManifest,
) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []

    try:
        notes_record = next(
            value
            for value in release_manifest.inputs
            if value.key == "release_notes"
        )
    except StopIteration:
        return (
            package_issue(
                "RELEASE_NOTES_INPUT",
                "inputs",
                "release_notes input record is absent",
            ),
        )

    try:
        notes_relative = _safe_relative_path(
            notes_record.source_path,
            field="release_notes.source_path",
        )
    except ValueError as exc:
        return (
            package_issue(
                "INPUT_SOURCE_PATH",
                "release_notes",
                str(exc),
            ),
        )

    notes_source = (
        repository_root
        / notes_relative
    )

    if not notes_source.is_file():
        return (
            package_issue(
                "INPUT_SOURCE_MISSING",
                notes_record.source_path,
                "release-note source is absent",
            ),
        )

    try:
        expected_inputs = build.collect_inputs(
            repository_root,
            notes_record.source_path,
        )
    except Exception as exc:
        return (
            package_issue(
                "INPUT_EVIDENCE",
                "inputs",
                str(exc),
            ),
        )

    if release_manifest.inputs != (
        expected_inputs
    ):
        issues.append(
            package_issue(
                "INPUT_EVIDENCE_MISMATCH",
                "inputs",
                "manifest input records differ "
                "from repository authority bytes",
            )
        )

    for record in release_manifest.inputs:
        if record.package_path is None:
            continue

        try:
            source_relative = _safe_relative_path(
                record.source_path,
                field=(
                    f"{record.key}.source_path"
                ),
            )

            package_relative = _safe_relative_path(
                record.package_path,
                field=(
                    f"{record.key}.package_path"
                ),
            )
        except ValueError as exc:
            issues.append(
                package_issue(
                    "INPUT_PATH",
                    record.key,
                    str(exc),
                )
            )
            continue

        source = (
            repository_root
            / source_relative
        )

        packaged = (
            package_dir
            / package_relative
        )

        if not source.is_file():
            issues.append(
                package_issue(
                    "COPIED_INPUT_SOURCE_MISSING",
                    record.source_path,
                    "repository source is absent",
                )
            )
            continue

        if not packaged.is_file():
            issues.append(
                package_issue(
                    "COPIED_INPUT_MISSING",
                    record.package_path,
                    "package copy is absent",
                )
            )
            continue

        if packaged.read_bytes() != (
            source.read_bytes()
        ):
            issues.append(
                package_issue(
                    "COPIED_INPUT_MISMATCH",
                    record.package_path,
                    "package copy differs "
                    "byte-for-byte from source",
                )
            )

    return tuple(
        sorted(
            set(issues),
            key=lambda value: value.sort_key,
        )
    )


def _formal_product_issues(
    package_dir: Path,
    context,
    release_manifest: manifest.ReleaseManifest,
) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []

    try:
        with tempfile.TemporaryDirectory(
            prefix="sosa-2023-package-render-check-"
        ) as directory:
            metadata, rendered = (
                build.render_formal_products(context, package_dir / 'sources/SOSA-2023-to-BFO-COMS.xlsx', package_dir / 'sources/sosa-2023-publication-metadata.toml', Path(directory), ro_product_config_path=package_dir / 'sources/sosa-2023-ro-product.toml', ro_workbook_path=package_dir / 'sources/SOSA-2023-to-RO-COMS.xlsx')
            )

            expected_bytes = (
                build.formal_product_bytes(
                    rendered
                )
            )

            for key in PRODUCT_ORDER:
                relative = (
                    PRODUCT_PACKAGE_PATHS[
                        key
                    ]
                )

                observed = (
                    package_dir
                    / relative
                ).read_bytes()

                if observed != (
                    expected_bytes[key]
                ):
                    issues.append(
                        package_issue(
                            "FORMAL_PRODUCT_MISMATCH",
                            relative,
                            "bytes differ from "
                            "same-package-input "
                            "formal rendering",
                        )
                    )

            expected_products = (
                build.collect_product_records(
                    rendered,
                    metadata,
                    context,
                )
            )

            if release_manifest.products != (
                expected_products
            ):
                issues.append(
                    package_issue(
                        "PRODUCT_EVIDENCE_MISMATCH",
                        "products",
                        "manifest product records "
                        "differ from recomputed "
                        "formal products",
                    )
                )

            catalog = (
                package_dir
                / "catalog-v001.xml"
            ).read_bytes()

            issues.extend(
                build.validate_catalog_bytes(
                    catalog,
                    metadata,
                    context,
                )
            )

    except Exception as exc:
        issues.append(
            package_issue(
                "FORMAL_RENDERING",
                "products",
                str(exc),
            )
        )

    return tuple(
        sorted(
            set(issues),
            key=lambda value: value.sort_key,
        )
    )


def _evidence_issues(
    package_dir: Path,
    repository_root: Path,
    release_manifest: manifest.ReleaseManifest,
    toolchain: ResolvedValidationToolchain,
) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []

    try:
        expected_dependencies = (
            build.collect_dependencies(
                repository_root
            )
        )
    except Exception as exc:
        issues.append(
            package_issue(
                "DEPENDENCY_EVIDENCE",
                "dependencies",
                str(exc),
            )
        )
    else:
        if release_manifest.dependencies != (
            expected_dependencies
        ):
            issues.append(
                package_issue(
                    "DEPENDENCY_EVIDENCE_MISMATCH",
                    "dependencies",
                    "manifest dependency records "
                    "differ from pinned "
                    "repository dependencies",
                )
            )

    try:
        expected_environment = (
            build.collect_validation_environment(
                repository_root,
                toolchain,
            )
        )
    except Exception as exc:
        issues.append(
            package_issue(
                "VALIDATION_ENVIRONMENT",
                "validation_environment",
                str(exc),
            )
        )
    else:
        if (
            release_manifest.validation_environment
            != expected_environment
        ):
            issues.append(
                package_issue(
                    "VALIDATION_ENVIRONMENT_MISMATCH",
                    "validation_environment",
                    "manifest validation "
                    "environment differs from "
                    "declared runtime",
                )
            )

    try:
        expected_included = (
            build.collect_included_files(
                package_dir
            )
        )
    except Exception as exc:
        issues.append(
            package_issue(
                "INCLUDED_FILE_EVIDENCE",
                "included_files",
                str(exc),
            )
        )
    else:
        if release_manifest.included_files != (
            expected_included
        ):
            issues.append(
                package_issue(
                    "INCLUDED_FILE_EVIDENCE_MISMATCH",
                    "included_files",
                    "manifest included-file "
                    "records differ from "
                    "package bytes",
                )
            )

    return tuple(
        sorted(
            set(issues),
            key=lambda value: value.sort_key,
        )
    )


def _local_path_leakage_issues(
    package_dir: Path,
    repository_root: Path,
) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []

    prohibited = (
        str(
            repository_root.resolve()
        ).encode("utf-8"),
        b"file://",
        build.TEMP_PREFIX.encode(
            "utf-8"
        ),
        b"-sosa-2023-build-work",
    )

    for relative in PACKAGE_FILE_PATHS:
        value = (
            package_dir
            / relative
        ).read_bytes()

        for marker in prohibited:
            if (
                marker
                and marker in value
            ):
                issues.append(
                    package_issue(
                        "LOCAL_PATH_LEAKAGE",
                        relative,
                        "contains prohibited "
                        "local-build marker "
                        f"{marker.decode('utf-8', errors='replace')!r}",
                    )
                )

    return tuple(
        sorted(
            set(issues),
            key=lambda value: value.sort_key,
        )
    )


def validate_release_package(
    package_dir: Path,
    *,
    repository_root: Path = REPO_ROOT,
    toolchain: ResolvedValidationToolchain | None = None,
    reconstruct: bool = True,
) -> tuple[ReleasePackageIssue, ...]:
    """Validate package bytes without modifying the package."""

    package_dir = Path(
        package_dir
    )

    repository_root = Path(
        repository_root
    ).resolve()

    snapshots = (
        build.snapshot_development_outputs(
            repository_root
        )
    )

    issues: list[
        ReleasePackageIssue
    ] = list(
        _layout_issues(
            package_dir
        )
    )

    if issues:
        issues.extend(
            build.development_snapshot_issues(
                repository_root,
                snapshots,
            )
        )

        return tuple(
            sorted(
                set(issues),
                key=lambda value: value.sort_key,
            )
        )

    try:
        release_manifest = (
            manifest
            .load_and_validate_release_manifest(
                package_dir
                / "manifest.json"
            )
        )
    except Exception as exc:
        issues.append(
            package_issue(
                "MANIFEST_VALIDATION",
                "manifest.json",
                str(exc),
            )
        )

        issues.extend(
            build.development_snapshot_issues(
                repository_root,
                snapshots,
            )
        )

        return tuple(
            sorted(
                set(issues),
                key=lambda value: value.sort_key,
            )
        )

    if package_dir.name != (
        release_manifest.release_identifier
    ):
        issues.append(
            package_issue(
                "PACKAGE_BASENAME",
                "package_dir",
                "expected "
                f"{release_manifest.release_identifier!r}, "
                f"got {package_dir.name!r}",
            )
        )

    try:
        context = (
            parse_formal_release_context(
                release_manifest.release_identifier,
                release_manifest.release_date,
                release_manifest.git_tag,
                release_manifest.source_commit,
            )
        )
    except Exception as exc:
        issues.append(
            package_issue(
                "RELEASE_CONTEXT",
                "manifest.json",
                str(exc),
            )
        )

        issues.extend(
            build.development_snapshot_issues(
                repository_root,
                snapshots,
            )
        )

        return tuple(
            sorted(
                set(issues),
                key=lambda value: value.sort_key,
            )
        )

    notes = (
        package_dir
        / "RELEASE-NOTES.md"
    ).read_bytes()

    issues.extend(
        runtime.validate_release_notes_bytes(
            notes,
            template_bytes=(
                repository_root
                / "release-notes/TEMPLATE.md"
            ).read_bytes(),
        )
    )

    issues.extend(
        _copied_input_issues(
            package_dir,
            repository_root,
            release_manifest,
        )
    )

    issues.extend(
        _formal_product_issues(
            package_dir,
            context,
            release_manifest,
        )
    )

    sums = (
        package_dir
        / "SHA256SUMS"
    ).read_bytes()

    issues.extend(
        build.validate_sha256sums_bytes(
            package_dir,
            sums,
        )
    )

    try:
        resolved_toolchain = (
            toolchain
            or runtime.resolve_validation_toolchain(
                repository_root
            )
        )
    except Exception as exc:
        issues.append(
            package_issue(
                "VALIDATION_TOOLCHAIN",
                "validation_environment",
                str(exc),
            )
        )

        issues.extend(
            build.development_snapshot_issues(
                repository_root,
                snapshots,
            )
        )

        return tuple(
            sorted(
                set(issues),
                key=lambda value: value.sort_key,
            )
        )

    issues.extend(
        _evidence_issues(
            package_dir,
            repository_root,
            release_manifest,
            resolved_toolchain,
        )
    )

    issues.extend(
        _local_path_leakage_issues(
            package_dir,
            repository_root,
        )
    )

    if release_manifest.product_order != (
        PRODUCT_ORDER
    ):
        issues.append(
            package_issue(
                "PRODUCT_ORDER",
                "product_order",
                "manifest product order differs "
                "from package authority",
            )
        )

    if issues:
        issues.extend(
            build.development_snapshot_issues(
                repository_root,
                snapshots,
            )
        )

        return tuple(
            sorted(
                set(issues),
                key=lambda value: value.sort_key,
            )
        )

    if reconstruct:
        try:
            notes_record = next(
                value
                for value in release_manifest.inputs
                if value.key == "release_notes"
            )

            with tempfile.TemporaryDirectory(
                prefix=(
                    "sosa-2023-release-package-"
                    "validation-"
                )
            ) as directory:
                reconstructed = (
                    Path(directory)
                    / context.release_identifier
                )

                build.assemble_release_package(
                    context,
                    notes,
                    notes_record.source_path,
                    reconstructed,
                    repository_root,
                    resolved_toolchain,
                    snapshots,
                )

                issues.extend(
                    build.compare_complete_packages(
                        package_dir,
                        reconstructed,
                    )
                )

        except Exception as exc:
            issues.append(
                package_issue(
                    "PACKAGE_RECONSTRUCTION",
                    "package",
                    str(exc),
                )
            )

    issues.extend(
        build.development_snapshot_issues(
            repository_root,
            snapshots,
        )
    )

    return tuple(
        sorted(
            set(issues),
            key=lambda value: value.sort_key,
        )
    )


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--package-dir",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--no-reconstruct",
        action="store_true",
        help=(
            "Skip independent complete-package "
            "reconstruction. Intended only for "
            "builder-internal prepublication checks."
        ),
    )

    return parser.parse_args(
        argv
    )


def main(
    argv: list[str] | None = None,
) -> int:
    args = parse_args(
        argv
    )

    issues = validate_release_package(
        args.package_dir,
        reconstruct=(
            not args.no_reconstruct
        ),
    )

    if issues:
        for issue in issues:
            print(
                runtime.format_issue(
                    issue
                )
            )

        return 1

    print(
        "SOSA-2023 release package "
        f"validation: PASS ({args.package_dir})"
    )

    print(
        "Regular files:",
        len(PACKAGE_FILE_PATHS),
    )

    print(
        "Checksummed files:",
        len(CHECKSUM_PATHS),
    )

    print(
        "Development artifacts checked:",
        len(DEVELOPMENT_OUTPUT_PATHS),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
