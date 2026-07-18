#!/usr/bin/env python3
"""Run the standard local validation suite for SSN-to-BFO mapping work."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TMP_DIR = Path("/tmp/ssn-to-bfo-validation-suite")
BYTECODE_CACHE_ENVIRONMENT = "SSN_TO_BFO_VALIDATION_PYCACHE"
BYTECODE_GUARD_ENVIRONMENT = "SSN_TO_BFO_VALIDATION_GUARD"


BYTECODE_SITE_CUSTOMIZE = f'''"""Propagate validation bytecode isolation to helper subprocesses."""

import os
import subprocess

_CACHE_ENVIRONMENT = {BYTECODE_CACHE_ENVIRONMENT!r}
_GUARD_ENVIRONMENT = {BYTECODE_GUARD_ENVIRONMENT!r}
_MARKER = "_ssn_to_bfo_validation_bytecode_guard"

if not getattr(subprocess, _MARKER, False):
    _original_popen = subprocess.Popen

    def _guarded_popen(*args, **kwargs):
        supplied = kwargs.get("env")
        environment = os.environ.copy() if supplied is None else dict(supplied)
        cache = environment.get(_CACHE_ENVIRONMENT, os.environ[_CACHE_ENVIRONMENT])
        guard = environment.get(_GUARD_ENVIRONMENT, os.environ[_GUARD_ENVIRONMENT])
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPYCACHEPREFIX"] = cache
        python_path = environment.get("PYTHONPATH", "")
        entries = [entry for entry in python_path.split(os.pathsep) if entry]
        if guard not in entries:
            entries.append(guard)
        environment["PYTHONPATH"] = os.pathsep.join(entries)
        environment[_CACHE_ENVIRONMENT] = cache
        environment[_GUARD_ENVIRONMENT] = guard
        kwargs["env"] = environment
        return _original_popen(*args, **kwargs)

    subprocess.Popen = _guarded_popen
    setattr(subprocess, _MARKER, True)
'''


@dataclass
class StepResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class OwnedTemporaryDirectory:
    path: Path
    device: int
    inode: int
    file_type: int


def command_text(command: list[str]) -> str:
    return shlex.join(command)


def run_command(name: str, command: list[str], *, environment: dict[str, str] | None = None) -> StepResult:
    print(f"\n==> {name}")
    print(f"$ {command_text(command)}")
    owned_cache = validation_bytecode_cache()
    try:
        child_environment = validation_child_environment(owned_cache, environment)
        proc = subprocess.run(command, cwd=REPO_ROOT, env=child_environment)
    finally:
        cleanup_errors = cleanup_owned_temporary_directory(owned_cache)
    passed = proc.returncode == 0 and not cleanup_errors
    if cleanup_errors:
        primary = "PASS" if proc.returncode == 0 else f"FAIL ({proc.returncode})"
        status = primary + "; " + "; ".join(cleanup_errors)
    else:
        status = "PASS" if passed else f"FAIL ({proc.returncode})"
    print(f"{name}: {status}")
    return StepResult(name=name, passed=passed, detail=status)


def parse_ttl_check() -> StepResult:
    code = (
        "from rdflib import Graph; "
        "Graph().parse('SSN2BFO.ttl', format='turtle'); "
        "print('SSN2BFO.ttl parse OK')"
    )
    return run_command("Turtle parse check", [sys.executable, "-c", code])


def external_temporary_directory(prefix: str) -> OwnedTemporaryDirectory:
    """Create a temporary directory that cannot be nested in this repository."""

    candidates = (Path("/tmp"), Path(tempfile.gettempdir()))
    for candidate in candidates:
        try:
            parent = candidate.resolve()
            parent.relative_to(REPO_ROOT)
        except ValueError:
            if parent.is_dir() and not parent.is_symlink():
                path = Path(tempfile.mkdtemp(prefix=prefix, dir=parent))
                info = os.lstat(path)
                if not stat.S_ISDIR(info.st_mode):
                    raise RuntimeError("external temporary path is not a directory")
                return OwnedTemporaryDirectory(
                    path=path,
                    device=info.st_dev,
                    inode=info.st_ino,
                    file_type=stat.S_IFMT(info.st_mode),
                )
        except OSError:
            continue
    raise RuntimeError("no external temporary directory is available for Python bytecode")


def cleanup_owned_temporary_directory(owned: OwnedTemporaryDirectory) -> tuple[str, ...]:
    """Remove one identity-owned directory without following a replacement path."""

    try:
        info = os.lstat(owned.path)
    except OSError as exc:
        return (f"CLEANUP_FAILED external bytecode cache: {exc.strerror}",)
    identity = (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))
    expected = (owned.device, owned.inode, owned.file_type)
    if identity != expected:
        return ("CLEANUP_FAILED external bytecode cache: owned path identity changed",)
    if not stat.S_ISDIR(info.st_mode):
        return ("CLEANUP_FAILED external bytecode cache: owned path is not a directory",)
    try:
        shutil.rmtree(owned.path)
    except OSError as exc:
        return (f"CLEANUP_FAILED external bytecode cache: {exc.strerror}",)
    return ()


def validation_child_environment(
    owned_cache: OwnedTemporaryDirectory,
    environment: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build the enforced bytecode-isolated environment for one validation step."""

    cache_directory = owned_cache.path / "pycache"
    guard_directory = owned_cache.path / "guard"
    cache_directory.mkdir()
    guard_directory.mkdir()
    (guard_directory / "sitecustomize.py").write_text(BYTECODE_SITE_CUSTOMIZE, encoding="utf-8")

    child_environment = os.environ.copy()
    if environment is not None:
        child_environment.update(environment)
    child_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    child_environment["PYTHONPYCACHEPREFIX"] = str(cache_directory)
    child_environment[BYTECODE_CACHE_ENVIRONMENT] = str(cache_directory)
    child_environment[BYTECODE_GUARD_ENVIRONMENT] = str(guard_directory)
    python_path = child_environment.get("PYTHONPATH", "")
    entries = [
        entry
        for entry in python_path.split(os.pathsep)
        if entry and entry != str(guard_directory)
    ]
    entries.insert(0, str(guard_directory))
    child_environment["PYTHONPATH"] = os.pathsep.join(entries)
    return child_environment


def compile_check() -> StepResult:
    return run_command(
        "Python compile check",
        [
            sys.executable,
            "-m",
            "py_compile",
            "tools/run_validation_suite.py",
            "tools/test_elk_instance_mapping_entailments.py",
            "tools/test_full_sosa_closure_hermit.py",
            "tools/test_object_property_typing_probes.py",
            "tools/test_instance_data.py",
            "tools/compare_mappings.py",
            "tools/coms_row_identity.py",
            "tools/product_dispositions.py",
            "tools/modular_products.py",
            "tools/generate_mapping_from_coms.py",
            "tools/check_coms_mapping.py",
            "tools/watch_coms_mapping.py",
            "tools/publication_metadata.py",
            "tools/check_publication_metadata.py",
            "tools/release_context.py",
            "tools/release_manifest.py",
            "tools/build_release.py",
            "tools/check_release.py",
            "tools/release_archive.py",
            "tools/rehearse_release.py",
            "tests/test_generate_mapping_from_coms.py",
            "tests/test_coms_row_identity.py",
            "tests/test_product_dispositions.py",
            "tests/test_modular_products.py",
            "tests/test_strict_bfo_mapping.py",
            "tests/test_cco_extension.py",
            "tests/test_bfo_projection.py",
            "tests/test_publication_metadata.py",
            "tests/test_release_context.py",
            "tests/test_release_rendering.py",
            "tests/test_release_manifest.py",
            "tests/test_build_release.py",
            "tests/test_release_archive.py",
            "tests/test_release_rehearsal.py",
        ],
    )


def print_summary(results: list[StepResult], report_paths: dict[str, Path], used_temp_reports: bool) -> int:
    print("\n==> Validation suite summary")
    print(f"Report output mode: {'temporary' if used_temp_reports else 'canonical'}")
    for label, path in report_paths.items():
        print(f"{label}: {path}")

    failed = [result for result in results if not result.passed]
    for result in results:
        print(f"- {result.name}: {'PASS' if result.passed else 'FAIL'}")

    if failed:
        print(f"\nValidation suite: FAIL ({len(failed)} failed step{'s' if len(failed) != 1 else ''})")
        return 1

    print("\nValidation suite: PASS")
    return 0


def validation_bytecode_cache() -> OwnedTemporaryDirectory:
    """Create one identity-owned external cache for a validation step."""

    return external_temporary_directory("ssn-to-bfo-validation-pycache-")


def run_validation_suite(args: argparse.Namespace) -> int:
    tmp_dir = Path(args.tmp_dir)
    if args.write_reports:
        smoke_report = REPO_ROOT / "reports/instance-data-smoke-test.md"
        elk_report = REPO_ROOT / "reports/elk-instance-mapping-entailments.md"
        full_sosa_hermit_report = REPO_ROOT / "reports/full-sosa-closure-hermit-check.md"
    else:
        smoke_report = tmp_dir / "instance-data-smoke-test.md"
        elk_report = tmp_dir / "elk-instance-mapping-entailments.md"
        full_sosa_hermit_report = tmp_dir / "full-sosa-closure-hermit-check.md"

    report_paths = {
        "instance smoke report": smoke_report,
        "ELK entailment report": elk_report,
        "full SOSA closure HermiT report": full_sosa_hermit_report,
    }

    results: list[StepResult] = []
    results.append(parse_ttl_check())
    if results[-1].passed:
        results.append(
            run_command(
                "COMS row-identity focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_coms_row_identity.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "COMS product-disposition focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_product_dispositions.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Alignment-core modular-product focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_modular_products.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Strict-BFO modular-product focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_strict_bfo_mapping.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "CCO-extension modular-product focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_cco_extension.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "BFO-projection modular-product focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_bfo_projection.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Publication metadata focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_publication_metadata.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Formal release-context focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_release_context.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Formal ontology-rendering focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_release_rendering.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Release manifest focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_release_manifest.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Release package build and validation focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_build_release.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Release archive focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_release_archive.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Release rehearsal focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_release_rehearsal.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Publication metadata development check",
                [sys.executable, "tools/check_publication_metadata.py"],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "COMS generator focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_generate_mapping_from_coms.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "COMS workbook freshness and candidate quality check",
                [sys.executable, "tools/check_coms_mapping.py", "--check-only"],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Instance-data smoke test",
                [sys.executable, "tools/test_instance_data.py", "--output", str(smoke_report)],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "ELK instance mapping entailment test",
                [
                    sys.executable,
                    "tools/test_elk_instance_mapping_entailments.py",
                    "--output",
                    str(elk_report),
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Full local SOSA closure HermiT check",
                [
                    sys.executable,
                    "tools/test_full_sosa_closure_hermit.py",
                    "--output",
                    str(full_sosa_hermit_report),
                ],
            )
        )
    if results[-1].passed:
        results.append(compile_check())
    if results[-1].passed:
        results.append(run_command("Git whitespace check", ["git", "diff", "--check"]))

    return print_summary(results, report_paths, not args.write_reports)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-reports",
        action="store_true",
        help="Write validation reports to canonical reports/ paths instead of temporary outputs.",
    )
    parser.add_argument(
        "--tmp-dir",
        default=str(DEFAULT_TMP_DIR),
        help=f"Temporary report directory used unless --write-reports is set. Default: {DEFAULT_TMP_DIR}",
    )
    args = parser.parse_args()

    return run_validation_suite(args)


if __name__ == "__main__":
    raise SystemExit(main())
