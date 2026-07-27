#!/usr/bin/env python3
"""Run the standard local validation suite for SSN-to-BFO mapping work."""

from __future__ import annotations

import argparse
import os
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
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


OWNED_CACHE_MARKER = ".ssn-to-bfo-owned-validation-cache"
OWNED_CACHE_IDENTITY_ERROR = "CLEANUP_FAILED external bytecode cache: owned path identity changed"


@dataclass(eq=False)
class OwnedTemporaryDirectory:
    path: Path
    directory_fd: int = field(repr=False)
    device: int
    inode: int
    file_type: int
    marker_name: str
    marker_fd: int = field(repr=False)
    marker_token: bytes = field(repr=False)
    marker_device: int
    marker_inode: int
    marker_file_type: int
    cleanup_result: tuple[str, ...] | None = None

    def __copy__(self):
        raise TypeError("owned temporary directories cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("owned temporary directories cannot be copied")


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

    required_flags = ("O_DIRECTORY", "O_CLOEXEC", "O_NOFOLLOW")
    if any(not hasattr(os, name) for name in required_flags):
        raise RuntimeError("platform cannot pin an owned external bytecode cache directory")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    marker_flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW
    candidates = (Path("/tmp"), Path(tempfile.gettempdir()))
    for candidate in candidates:
        path: Path | None = None
        directory_fd = -1
        marker_fd = -1
        complete = False
        try:
            parent = candidate.resolve()
            parent.relative_to(REPO_ROOT)
        except ValueError:
            if parent.is_dir() and not parent.is_symlink():
                try:
                    path = Path(tempfile.mkdtemp(prefix=prefix, dir=parent))
                    directory_fd = os.open(path, directory_flags)
                    os.set_inheritable(directory_fd, False)
                    path_info = os.lstat(path)
                    directory_info = os.fstat(directory_fd)
                    path_identity = (
                        path_info.st_dev,
                        path_info.st_ino,
                        stat.S_IFMT(path_info.st_mode),
                    )
                    directory_identity = (
                        directory_info.st_dev,
                        directory_info.st_ino,
                        stat.S_IFMT(directory_info.st_mode),
                    )
                    if (
                        path_identity != directory_identity
                        or directory_identity[2] != stat.S_IFDIR
                        or os.get_inheritable(directory_fd)
                    ):
                        raise RuntimeError("external temporary path is not a pinned real directory")

                    marker_token = secrets.token_bytes(32)
                    marker_fd = os.open(
                        OWNED_CACHE_MARKER,
                        marker_flags,
                        0o600,
                        dir_fd=directory_fd,
                    )
                    os.set_inheritable(marker_fd, False)
                    os.fchmod(marker_fd, 0o600)
                    remaining = memoryview(marker_token)
                    while remaining:
                        written = os.write(marker_fd, remaining)
                        if written <= 0:
                            raise OSError("unable to write owned-cache marker")
                        remaining = remaining[written:]
                    marker_info = os.fstat(marker_fd)
                    if (
                        not stat.S_ISREG(marker_info.st_mode)
                        or stat.S_IMODE(marker_info.st_mode) != 0o600
                        or os.get_inheritable(marker_fd)
                    ):
                        raise RuntimeError("owned-cache marker is not a private regular file")
                    owned = OwnedTemporaryDirectory(
                        path=path,
                        directory_fd=directory_fd,
                        device=directory_info.st_dev,
                        inode=directory_info.st_ino,
                        file_type=stat.S_IFMT(directory_info.st_mode),
                        marker_name=OWNED_CACHE_MARKER,
                        marker_fd=marker_fd,
                        marker_token=marker_token,
                        marker_device=marker_info.st_dev,
                        marker_inode=marker_info.st_ino,
                        marker_file_type=stat.S_IFMT(marker_info.st_mode),
                    )
                    complete = True
                    return owned
                except OSError:
                    pass
                finally:
                    if not complete:
                        if marker_fd >= 0:
                            os.close(marker_fd)
                        if path is not None and directory_fd >= 0:
                            try:
                                path_info = os.lstat(path)
                                directory_info = os.fstat(directory_fd)
                                if (
                                    (path_info.st_dev, path_info.st_ino, stat.S_IFMT(path_info.st_mode))
                                    == (
                                        directory_info.st_dev,
                                        directory_info.st_ino,
                                        stat.S_IFMT(directory_info.st_mode),
                                    )
                                    and stat.S_ISDIR(path_info.st_mode)
                                    and shutil.rmtree.avoids_symlink_attacks
                                ):
                                    shutil.rmtree(path)
                            except OSError:
                                pass
                            os.close(directory_fd)
                        elif path is not None:
                            try:
                                os.rmdir(path)
                            except OSError:
                                pass
                if path is not None and os.path.lexists(path):
                    raise RuntimeError("external temporary path is not a directory")
        except OSError:
            continue
    raise RuntimeError("no external temporary directory is available for Python bytecode")


def cleanup_owned_temporary_directory(owned: OwnedTemporaryDirectory) -> tuple[str, ...]:
    """Remove one pinned, marked directory once without following replacements."""

    if owned.cleanup_result is not None:
        return owned.cleanup_result
    result: tuple[str, ...] = (OWNED_CACHE_IDENTITY_ERROR,)
    try:
        if owned.directory_fd < 0:
            return result
        if owned.marker_fd < 0:
            return result
        directory_info = os.fstat(owned.directory_fd)
        path_info = os.lstat(owned.path)
        expected_directory = (owned.device, owned.inode, owned.file_type)
        descriptor_identity = (
            directory_info.st_dev,
            directory_info.st_ino,
            stat.S_IFMT(directory_info.st_mode),
        )
        path_identity = (
            path_info.st_dev,
            path_info.st_ino,
            stat.S_IFMT(path_info.st_mode),
        )
        if (
            descriptor_identity != expected_directory
            or path_identity != descriptor_identity
            or descriptor_identity[2] != stat.S_IFDIR
        ):
            return result

        expected_marker = (
            owned.marker_device,
            owned.marker_inode,
            owned.marker_file_type,
        )
        marker_descriptor_info = os.fstat(owned.marker_fd)
        marker_info = os.stat(
            owned.marker_name,
            dir_fd=owned.directory_fd,
            follow_symlinks=False,
        )
        marker_path_info = os.lstat(owned.path / owned.marker_name)
        marker_identity = (
            marker_info.st_dev,
            marker_info.st_ino,
            stat.S_IFMT(marker_info.st_mode),
        )
        marker_path_identity = (
            marker_path_info.st_dev,
            marker_path_info.st_ino,
            stat.S_IFMT(marker_path_info.st_mode),
        )
        marker_descriptor_identity = (
            marker_descriptor_info.st_dev,
            marker_descriptor_info.st_ino,
            stat.S_IFMT(marker_descriptor_info.st_mode),
        )
        if (
            marker_descriptor_identity != expected_marker
            or marker_identity != expected_marker
            or marker_path_identity != expected_marker
            or marker_identity[2] != stat.S_IFREG
            or stat.S_IMODE(marker_descriptor_info.st_mode) != 0o600
            or stat.S_IMODE(marker_info.st_mode) != 0o600
            or stat.S_IMODE(marker_path_info.st_mode) != 0o600
            or os.get_inheritable(owned.marker_fd)
        ):
            return result

        os.lseek(owned.marker_fd, 0, os.SEEK_SET)
        marker_bytes = bytearray()
        while len(marker_bytes) <= len(owned.marker_token):
            chunk = os.read(
                owned.marker_fd,
                len(owned.marker_token) + 1 - len(marker_bytes),
            )
            if not chunk:
                break
            marker_bytes.extend(chunk)
        if bytes(marker_bytes) != owned.marker_token:
            return result

        if not shutil.rmtree.avoids_symlink_attacks:
            return result
        # Python's portable rmtree API cannot remove the root directory by its
        # already-open descriptor. Its symlink-resistant implementation is used
        # only after descriptor, pathname, and private-marker agreement, and the
        # pinned descriptor remains open until recursive deletion completes.
        shutil.rmtree(owned.path)
        result = ()
    except OSError:
        result = (OWNED_CACHE_IDENTITY_ERROR,)
    finally:
        close_failed = False
        if owned.marker_fd >= 0:
            try:
                os.close(owned.marker_fd)
            except OSError:
                close_failed = True
            owned.marker_fd = -1
        if owned.directory_fd >= 0:
            try:
                os.close(owned.directory_fd)
            except OSError:
                close_failed = True
            owned.directory_fd = -1
        if close_failed and not result:
            result = ("CLEANUP_FAILED external bytecode cache: unable to close owned descriptor",)
        owned.cleanup_result = result
    return result


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
            "tools/robot_template_generation_pilot.py",
            "tools/robot_property_chain_generation_pilot.py",
            "tools/robot_reconstruction_validation.py",
            "tools/validate_robot_reconstruction.py",
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
            "tests/test_robot_template_generation_pilot.py",
            "tests/test_robot_property_chain_generation_pilot.py",
            "tests/test_robot_reconstruction_validation.py",
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
            "tests/test_placeholder_catalog_migration.py",
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
                "Placeholder and catalog migration focused tests",
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_placeholder_catalog_migration.py",
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
                "ROBOT reconstruction focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "tests.test_robot_template_generation_pilot",
                    "tests.test_robot_property_chain_generation_pilot",
                    "tests.test_robot_reconstruction_validation",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Complete ROBOT reconstruction check",
                [
                    sys.executable,
                    "tools/validate_robot_reconstruction.py",
                    "--output-dir",
                    str(tmp_dir / "robot-reconstruction"),
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
