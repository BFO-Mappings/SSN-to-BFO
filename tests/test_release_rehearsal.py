#!/usr/bin/env python3
"""Clean-source detached-checkout release rehearsal regressions."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import rehearse_release as rehearsal  # noqa: E402
import run_validation_suite as validation_runner  # noqa: E402
import build_release as production_build  # noqa: E402
import release_archive as archive_tool  # noqa: E402

PACKAGE_FILE_PATHS = production_build.PACKAGE_FILE_PATHS


RELEASE_ID = "2099-01-02"
NOTES = "release-notes/SYNTHETIC-2099-01-02.md"


BUILD_STUB = '''#!/usr/bin/env python3
import argparse
import json
import socket
import sys
from pathlib import Path
from types import SimpleNamespace

PACKAGE_FILE_PATHS = {paths!r}

def compare_complete_packages(first, second):
    return ()

def resolve_validation_toolchain(repository_root):
    return SimpleNamespace(
        java_executable=Path(sys.executable).resolve(),
        robot_jar=Path("/etc/hosts"),
        java_heap="4G",
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--release-date", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--git-tag", required=True)
    parser.add_argument("--notes", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    probes = (
        lambda: socket.socket().connect(("127.0.0.1", 9)),
        lambda: socket.socket().connect_ex(("127.0.0.1", 9)),
        lambda: socket.socket().sendto(b"x", ("127.0.0.1", 9)),
        lambda: socket.create_connection(("example.invalid", 80)),
        lambda: socket.getaddrinfo("example.invalid", 80),
        lambda: socket.gethostbyname("example.invalid"),
    )
    for probe in probes:
        try:
            probe()
        except RuntimeError:
            pass
        else:
            raise SystemExit("offline socket guard was not installed")
    args.output_dir.mkdir()
    for relative in PACKAGE_FILE_PATHS:
        path = args.output_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "manifest.json":
            source_commit = "0" * 40 if Path("SOURCE_MISMATCH").exists() else args.source_commit
            value = json.dumps({{"source_commit": source_commit}}, sort_keys=True).encode() + b"\\n"
        elif relative == "RELEASE-NOTES.md":
            value = Path(args.notes).read_bytes()
        else:
            value = ("fixture:" + relative + "\\n").encode()
        if Path("NONDETERMINISTIC").exists() and "candidate-b" in str(args.output_dir) and relative == "LICENSE":
            value += b"candidate-b\\n"
        path.write_bytes(value)
    if Path("MUTATE_CHECKOUT").exists():
        Path("tracked.txt").write_text("mutated\\n", encoding="utf-8")
    if Path("MUTATE_AFTER_PACKAGE_BUILD").exists() or Path("MUTATE_THEN_RESTORE").exists():
        Path("tracked.txt").write_text("mutated-after-package-build\\n", encoding="utf-8")
    if Path("IGNORED_AFTER_PACKAGE_BUILD").exists():
        Path("ignored-cache/from-package-build").parent.mkdir(exist_ok=True)
        Path("ignored-cache/from-package-build").write_text("ignored\\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''.format(paths=PACKAGE_FILE_PATHS)


CHECK_STUB = '''#!/usr/bin/env python3
import argparse
import socket
from pathlib import Path
from build_release import PACKAGE_FILE_PATHS

EXPECTED_DIRECTORIES = ("current-ssn-sosa", "evidence", "sources")

class Issue:
    def __init__(self, code, field, message):
        self.code = code
        self.field = field
        self.message = message

def validate_release_package(package_dir, repository_root=None):
    package_dir = Path(package_dir)
    observed = tuple(
        path.relative_to(package_dir).as_posix()
        for path in sorted(package_dir.rglob("*"), key=lambda value: value.relative_to(package_dir).as_posix())
        if path.is_file()
    )
    if observed != PACKAGE_FILE_PATHS:
        return (Issue("PACKAGE_FILE_SET", "package", "inventory differs"),)
    if (package_dir / "LICENSE").read_bytes() != b"fixture:LICENSE\\n" and "candidate-b" not in str(package_dir):
        return (Issue("PACKAGE_CONTENT_MISMATCH", "LICENSE", "copied bytes differ"),)
    return ()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("validate",))
    parser.add_argument("--package-dir", required=True, type=Path)
    args = parser.parse_args()
    if Path("CHECK_NETWORK_ATTEMPT").exists():
        try:
            socket.create_connection(("example.invalid", 80))
        except RuntimeError:
            pass
        else:
            raise SystemExit("offline socket guard was not installed for package validation")
    if Path("MUTATE_THEN_RESTORE").exists():
        Path("tracked.txt").write_text("tracked\\n", encoding="utf-8")
    if Path("MUTATE_AFTER_PACKAGE_VALIDATION").exists():
        Path("tracked.txt").write_text("mutated-after-package-validation\\n", encoding="utf-8")
    if Path("IGNORED_AFTER_PACKAGE_VALIDATION").exists():
        Path("ignored-cache/from-package-validation").parent.mkdir(exist_ok=True)
        Path("ignored-cache/from-package-validation").write_text("ignored\\n", encoding="utf-8")
    if Path("ignored-cache").exists():
        raise SystemExit("ignored invoking-checkout residue entered a candidate")
    issues = validate_release_package(args.package_dir)
    if issues:
        for issue in issues:
            print(f"ERROR [{{issue.code}}] {{issue.field}}: {{issue.message}}")
        return 1
    print("Release package validation: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''


CONTEXT_STUB = '''import re
from types import SimpleNamespace
SOURCE_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\\Z")
def validate_release_identifier(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ValueError("invalid release identifier")
    return value
def parse_formal_release_context(release_identifier, release_date, git_tag, source_commit):
    validate_release_identifier(release_identifier)
    if release_date != release_identifier or git_tag != "v" + release_identifier:
        raise ValueError("invalid synthetic formal context")
    if SOURCE_COMMIT_PATTERN.fullmatch(source_commit) is None:
        raise ValueError("invalid source commit")
    return SimpleNamespace(
        release_identifier=release_identifier,
        release_date=release_date,
        git_tag=git_tag,
        source_commit=source_commit,
    )
'''


MANIFEST_STUB = '''import json
from types import SimpleNamespace
ReleaseManifest = SimpleNamespace
def load_and_validate_release_manifest(source):
    return SimpleNamespace(**json.loads(source.read_bytes()))
'''


def run_git(repository: Path, *arguments: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(completed.stderr.decode())
    return completed


class ReleaseRehearsalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="release-rehearsal-tests-")).resolve()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.repository = self.root / "repository"
        self.repository.mkdir()
        (self.repository / "tools").mkdir()
        (self.repository / "release-notes").mkdir()
        shutil.copy2(REPO_ROOT / "tools/release_archive.py", self.repository / "tools/release_archive.py")
        shutil.copy2(REPO_ROOT / "tools/rehearse_release.py", self.repository / "tools/rehearse_release.py")
        (self.repository / "tools/build_release.py").write_text(BUILD_STUB, encoding="utf-8")
        (self.repository / "tools/check_release.py").write_text(CHECK_STUB, encoding="utf-8")
        (self.repository / "tools/release_context.py").write_text(CONTEXT_STUB, encoding="utf-8")
        (self.repository / "tools/release_manifest.py").write_text(MANIFEST_STUB, encoding="utf-8")
        shutil.copy2(REPO_ROOT / NOTES, self.repository / NOTES)
        (self.repository / "tracked.txt").write_text("tracked\n", encoding="utf-8")
        (self.repository / ".gitignore").write_text("__pycache__/\n*.pyc\nignored-cache/\n", encoding="utf-8")
        run_git(self.repository, "init", "-q")
        run_git(self.repository, "add", ".")
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_AUTHOR_NAME": "Release Test",
                "GIT_AUTHOR_EMAIL": "release@example.invalid",
                "GIT_COMMITTER_NAME": "Release Test",
                "GIT_COMMITTER_EMAIL": "release@example.invalid",
                "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
                "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            }
        )
        subprocess.run(["git", "-C", str(self.repository), "commit", "-q", "-m", "fixture"], env=environment, check=True)
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()
        self.host_home = self.root / "invoking-home"
        self.host_bin = self.host_home / "bin"
        self.host_jar = self.host_home / "tools/robot/robot.jar"
        self.host_bin.mkdir(parents=True)
        self.host_jar.parent.mkdir(parents=True)
        self.host_java = self.host_bin / "java"
        self.host_robot = self.host_bin / "robot"
        self.host_java.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.host_java.chmod(0o755)
        self.host_jar.write_bytes(b"fixture robot jar\n")
        self.host_robot.write_text(
            '#!/bin/sh\njava -Xmx4G -jar ~/tools/robot/robot.jar "$@"\n',
            encoding="utf-8",
        )
        self.host_robot.chmod(0o755)
        self.verified_toolchain = production_build.ResolvedValidationToolchain(
            java_executable=self.host_java,
            java_vendor="Fixture Java Vendor",
            java_version="22.0.2",
            java_vm_name="Fixture Java VM",
            robot_executable=self.host_robot,
            robot_jar=self.host_jar,
            robot_artifact="https://example.invalid/robot.jar",
            robot_version="1.9.7",
            robot_jar_sha256=production_build.sha256_bytes(self.host_jar.read_bytes()),
            java_heap="4G",
        )
        resolver = mock.patch.object(
            rehearsal,
            "resolve_validation_toolchain",
            return_value=self.verified_toolchain,
        )
        self.mock_resolver = resolver.start()
        self.addCleanup(resolver.stop)

    def manifest_loader(self, path: Path):
        return types.SimpleNamespace(**json.loads(path.read_bytes()))

    def rehearse(self, command: str = "verify", *, output: Path | None = None, notes: str = NOTES):
        with mock.patch.object(rehearsal, "load_and_validate_release_manifest", side_effect=self.manifest_loader):
            return rehearsal.rehearse_release(
                command,
                RELEASE_ID,
                RELEASE_ID,
                "v" + RELEASE_ID,
                self.commit,
                notes,
                output_dir=output,
                repository_root=self.repository,
            )

    def commit_fixture_path(self, relative: str, value: str = "yes\n") -> None:
        path = self.repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        run_git(self.repository, "add", relative)
        run_git(
            self.repository,
            "-c", "user.name=Release Test",
            "-c", "user.email=release@example.invalid",
            "commit", "-q", "-m", f"fixture {relative}",
        )
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()

    def assert_codes(self, raised: unittest.case._AssertRaisesContext, *codes: str) -> None:
        self.assertTrue(set(codes) <= {issue.code for issue in raised.exception.issues})

    def bytecode_snapshot(self, path: Path) -> dict[str, object]:
        info = os.lstat(path)
        return {
            "bytes": path.read_bytes(),
            "file_type": stat.S_IFMT(info.st_mode),
            "mode": info.st_mode,
            "size": info.st_size,
            "mtime_ns": info.st_mtime_ns,
            "device": info.st_dev,
            "inode": info.st_ino,
        }

    def create_preexisting_bytecode(self) -> dict[Path, dict[str, object]]:
        paths = {
            self.repository / "tools/__pycache__/preexisting.pyc": b"preexisting-pyc\x00sentinel\n",
            self.repository / "tests/__pycache__/preexisting.pyo": b"preexisting-pyo\x00sentinel\n",
        }
        for index, (path, content) in enumerate(paths.items()):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o640)
            timestamp = 1_700_000_000_000_000_000 + index
            os.utime(path, ns=(timestamp, timestamp))
        return {path: self.bytecode_snapshot(path) for path in paths}

    def repository_bytecode_paths(self) -> set[str]:
        return {
            path.relative_to(self.repository).as_posix()
            for path in self.repository.rglob("*")
            if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}
        }

    def test_validation_runner_preserves_preexisting_bytecode_and_isolates_child_compilation(self) -> None:
        before = self.create_preexisting_bytecode()
        before_paths = self.repository_bytecode_paths()
        (self.repository / "validation_module.py").write_text("VALUE = 7\n", encoding="utf-8")
        script = '''
import json
import os
import subprocess
import sys

inner = r"""
import json
import os
import py_compile
from pathlib import Path
import validation_module

compiled = py_compile.compile("validation_module.py", doraise=True)
Path("bytecode-report.json").write_text(json.dumps({
    "dont_write": os.environ["PYTHONDONTWRITEBYTECODE"],
    "cache": os.environ["PYTHONPYCACHEPREFIX"],
    "compiled": compiled,
    "value": validation_module.VALUE,
}, sort_keys=True), encoding="utf-8")
"""
subprocess.run(
    [sys.executable, "-c", inner],
    env={"PYTHONPATH": "."},
    check=True,
)
'''
        with mock.patch.object(validation_runner, "REPO_ROOT", self.repository):
            result = validation_runner.run_command("bytecode isolation fixture", [sys.executable, "-c", script])
        self.assertTrue(result.passed, result.detail)
        report = json.loads((self.repository / "bytecode-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["dont_write"], "1")
        cache = Path(report["cache"])
        self.assertFalse(cache.is_relative_to(self.repository))
        self.assertTrue(Path(report["compiled"]).is_relative_to(cache))
        self.assertFalse(cache.parent.exists())
        self.assertEqual(self.repository_bytecode_paths(), before_paths)
        for path, snapshot in before.items():
            self.assertEqual(self.bytecode_snapshot(path), snapshot)
            self.assertTrue(path.parent.is_dir())

    def test_validation_runner_failure_preserves_preexisting_bytecode_and_cleans_external_cache(self) -> None:
        before = self.create_preexisting_bytecode()
        before_paths = self.repository_bytecode_paths()
        (self.repository / "validation_module.py").write_text("VALUE = 7\n", encoding="utf-8")
        script = '''
import json
import os
import py_compile
from pathlib import Path
import validation_module

compiled = py_compile.compile("validation_module.py", doraise=True)
Path("failed-bytecode-report.json").write_text(json.dumps({
    "cache": os.environ["PYTHONPYCACHEPREFIX"],
    "compiled": compiled,
    "value": validation_module.VALUE,
}, sort_keys=True), encoding="utf-8")
raise SystemExit(7)
'''
        with mock.patch.object(validation_runner, "REPO_ROOT", self.repository):
            result = validation_runner.run_command("failing bytecode fixture", [sys.executable, "-c", script])
        self.assertFalse(result.passed)
        self.assertIn("FAIL (7)", result.detail)
        report = json.loads((self.repository / "failed-bytecode-report.json").read_text(encoding="utf-8"))
        cache = Path(report["cache"])
        self.assertTrue(Path(report["compiled"]).is_relative_to(cache))
        self.assertFalse(cache.parent.exists())
        self.assertEqual(self.repository_bytecode_paths(), before_paths)
        for path, snapshot in before.items():
            self.assertEqual(self.bytecode_snapshot(path), snapshot)

    def test_validation_runner_refuses_replacement_directory_cleanup(self) -> None:
        with mock.patch.object(validation_runner, "REPO_ROOT", self.repository):
            owned = validation_runner.validation_bytecode_cache()
        shutil.rmtree(owned.path)
        owned.path.mkdir()
        sentinel = owned.path / "sentinel.bin"
        sentinel.write_bytes(b"unrelated replacement directory\n")
        errors = validation_runner.cleanup_owned_temporary_directory(owned)
        self.assertEqual(errors, ("CLEANUP_FAILED external bytecode cache: owned path identity changed",))
        self.assertEqual(sentinel.read_bytes(), b"unrelated replacement directory\n")
        self.assertTrue(owned.path.is_dir())
        shutil.rmtree(owned.path)

    def test_validation_runner_refuses_replacement_symlink_cleanup(self) -> None:
        with mock.patch.object(validation_runner, "REPO_ROOT", self.repository):
            owned = validation_runner.validation_bytecode_cache()
        shutil.rmtree(owned.path)
        target = self.root / "unrelated-bytecode-target"
        target.mkdir()
        sentinel = target / "sentinel.bin"
        sentinel.write_bytes(b"unrelated symlink target\n")
        owned.path.symlink_to(target, target_is_directory=True)
        errors = validation_runner.cleanup_owned_temporary_directory(owned)
        self.assertEqual(errors, ("CLEANUP_FAILED external bytecode cache: owned path identity changed",))
        self.assertTrue(owned.path.is_symlink())
        self.assertEqual(sentinel.read_bytes(), b"unrelated symlink target\n")
        owned.path.unlink()

    def test_validation_runner_compile_step_enforces_external_cache_environment(self) -> None:
        captured: dict[str, object] = {}

        def record_run(command, *, cwd, env):
            captured.update({"command": command, "cwd": cwd, "env": env})
            return subprocess.CompletedProcess(command, 0)

        with mock.patch.object(validation_runner, "REPO_ROOT", self.repository), mock.patch.object(
            validation_runner.subprocess,
            "run",
            side_effect=record_run,
        ):
            result = validation_runner.compile_check()
        self.assertTrue(result.passed, result.detail)
        self.assertEqual(captured["command"][1:3], ["-m", "py_compile"])
        environment = captured["env"]
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")
        cache = Path(environment["PYTHONPYCACHEPREFIX"])
        self.assertFalse(cache.is_relative_to(self.repository))
        self.assertFalse(cache.parent.exists())

    def build_staging_candidate(self, label: str):
        candidate_root = self.root / label
        candidate_root.mkdir()
        guard = self.root / f"{label}-guard"
        guard.mkdir()
        (guard / "sitecustomize.py").write_text(rehearsal.SITE_CUSTOMIZE, encoding="utf-8")
        with mock.patch.object(rehearsal, "load_and_validate_release_manifest", side_effect=self.manifest_loader):
            return rehearsal._build_candidate(
                candidate_root,
                self.repository,
                self.commit,
                RELEASE_ID,
                RELEASE_ID,
                "v" + RELEASE_ID,
                NOTES,
                (self.repository / NOTES).read_bytes(),
                guard,
                self.verified_toolchain,
            )

    def create_production_toolchain_fixture(self):
        repository = self.root / "production-toolchain-repository"
        (repository / "tools").mkdir(parents=True)
        (repository / "config").mkdir()
        for source in (REPO_ROOT / "tools").glob("*.py"):
            shutil.copy2(source, repository / "tools" / source.name)
        java_bin = self.root / "production-host/bin"
        host_home = self.root / "production-host/home"
        robot_bin = host_home / "bin"
        robot_jar = host_home / "tools/robot/robot.jar"
        java_bin.mkdir(parents=True)
        robot_bin.mkdir(parents=True)
        robot_jar.parent.mkdir(parents=True)
        java = java_bin / "java"
        java.write_text(
            "#!/bin/sh\n"
            "for argument in \"$@\"; do\n"
            "  if [ \"$argument\" = \"--version\" ]; then\n"
            "    printf 'ROBOT version 1.9.7\\n'\n"
            "    exit 0\n"
            "  fi\n"
            "done\n"
            "printf '    java.vendor = Fixture Vendor\\n' >&2\n"
            "printf '    java.version = 22.0.2\\n' >&2\n"
            "printf '    java.vm.name = Fixture VM\\n' >&2\n",
            encoding="utf-8",
        )
        java.chmod(0o755)
        robot_jar.write_bytes(b"deterministic fake robot jar\n")
        robot = robot_bin / "robot"
        robot.write_text(
            '#!/bin/sh\njava -Xmx4G -jar ~/tools/robot/robot.jar "$@"\n',
            encoding="utf-8",
        )
        robot.chmod(0o755)
        robot_hash = production_build.sha256_bytes(robot_jar.read_bytes())
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        (repository / "config/validation-toolchain.env").write_text(
            "\n".join(
                (
                    f"VALIDATION_PYTHON_VERSION={python_version}",
                    "VALIDATION_JAVA_DISTRIBUTION=fixture",
                    "VALIDATION_JAVA_VERSION=22",
                    "VALIDATION_ROBOT_VERSION=1.9.7",
                    "VALIDATION_ROBOT_URL=https://example.invalid/robot.jar",
                    f"VALIDATION_ROBOT_SHA256={robot_hash}",
                    "VALIDATION_ROBOT_JAVA_HEAP=4G",
                    "",
                )
            ),
            encoding="utf-8",
        )
        run_git(repository, "init", "-q")
        run_git(repository, "add", ".")
        run_git(
            repository,
            "-c", "user.name=Release Test",
            "-c", "user.email=release@example.invalid",
            "commit", "-q", "-m", "committed production resolver fixture",
        )
        invoking_environment = os.environ.copy()
        invoking_environment.update(
            {
                "HOME": str(host_home),
                "PATH": os.pathsep.join((str(robot_bin), str(java_bin), os.defpath)),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        return repository, host_home, java, robot, robot_jar, invoking_environment

    def run_candidate_toolchain_resolver(
        self,
        repository: Path,
        environment: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        script = (
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, 'tools')\n"
            "import build_release\n"
            "try:\n"
            "    value = build_release.resolve_validation_toolchain(Path.cwd())\n"
            "except Exception as exc:\n"
            "    print(str(exc))\n"
            "    raise SystemExit(1)\n"
            "print(json.dumps({\n"
            "    'java': str(value.java_executable),\n"
            "    'jar': str(value.robot_jar),\n"
            "    'hash': value.robot_jar_sha256,\n"
            "    'robot_version': value.robot_version,\n"
            "    'java_vendor': value.java_vendor,\n"
            "    'java_version': value.java_version,\n"
            "    'java_vm': value.java_vm_name,\n"
            "    'heap': value.java_heap,\n"
            "    'dont_write': os.environ['PYTHONDONTWRITEBYTECODE'],\n"
            "    'cache': os.environ['PYTHONPYCACHEPREFIX'],\n"
            "}, sort_keys=True))\n"
        )
        return subprocess.run(
            [sys.executable, "-B", "-c", script],
            cwd=repository,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def test_toolchain_preflight_failure_precedes_candidate_state_and_preserves_detail(self) -> None:
        detail = (
            "ERROR [UNVERIFIED_ROBOT_ARTIFACT] validation_environment.robot_artifact: "
            "resolved ROBOT JAR is not a regular file"
        )
        with mock.patch.object(
            rehearsal,
            "resolve_validation_toolchain",
            side_effect=RuntimeError(detail),
        ), mock.patch.object(rehearsal.tempfile, "mkdtemp") as make_temporary, mock.patch.object(
            rehearsal,
            "_build_candidate",
        ) as build_candidate, self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            self.rehearse()
        self.assert_codes(raised, "PACKAGE_BUILD_FAILED")
        self.assertIn(detail, str(raised.exception))
        make_temporary.assert_not_called()
        build_candidate.assert_not_called()

    def test_candidate_private_wrappers_control_path_and_keep_home_xdg_sanitized(self) -> None:
        observed: list[dict[str, object]] = []
        original_phase = rehearsal._phase_command
        invoking_home = self.host_home
        invoking_path = os.pathsep.join((str(self.host_bin), os.environ.get("PATH", "")))
        inherited_cache = "/some/shared/inherited/cache"

        def record_phase(code, field, command, *, checkout, environment):
            toolchain_bin = Path(environment["PATH"].split(os.pathsep)[0])
            wrapper = toolchain_bin / "robot"
            wrapper_status = wrapper.lstat()
            content = wrapper.read_text(encoding="utf-8")
            probe = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        "import json, os, subprocess, sys; "
                        "nested = subprocess.run([sys.executable, '-B', '-c', "
                        "'import json, os; print(json.dumps({\\\"dont_write\\\": "
                        "os.environ[\\\"PYTHONDONTWRITEBYTECODE\\\"], \\\"cache\\\": "
                        "os.environ[\\\"PYTHONPYCACHEPREFIX\\\"]}, sort_keys=True))'], "
                        "env=os.environ.copy(), check=True, capture_output=True, text=True); "
                        "print(json.dumps({'dont_write': os.environ['PYTHONDONTWRITEBYTECODE'], "
                        "'cache': os.environ['PYTHONPYCACHEPREFIX'], "
                        "'nested': json.loads(nested.stdout)}, sort_keys=True))"
                    ),
                ],
                cwd=checkout,
                env=dict(environment),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            reported_environment = json.loads(probe.stdout)
            observed.append(
                {
                    "code": code,
                    "wrapper": wrapper,
                    "toolchain": toolchain_bin.parent,
                    "content": content,
                    "mode": stat.S_IMODE(wrapper_status.st_mode),
                    "regular": stat.S_ISREG(wrapper_status.st_mode),
                    "candidate_root": checkout.parent,
                    "checkout": checkout,
                    "cache": Path(environment["PYTHONPYCACHEPREFIX"]),
                    "home": Path(environment["HOME"]),
                    "xdg": Path(environment["XDG_CONFIG_HOME"]),
                    "resolved_robot": shutil.which("robot", path=environment["PATH"]),
                    "reported_environment": reported_environment,
                }
            )
            return original_phase(code, field, command, checkout=checkout, environment=environment)

        with mock.patch.dict(
            os.environ,
            {
                "HOME": str(invoking_home),
                "PATH": invoking_path,
                "PYTHONPYCACHEPREFIX": inherited_cache,
                rehearsal.VALIDATION_PYCACHE_ENVIRONMENT: inherited_cache,
                rehearsal.VALIDATION_GUARD_ENVIRONMENT: "/some/shared/inherited/guard",
            },
        ), mock.patch.object(
            rehearsal,
            "_phase_command",
            side_effect=record_phase,
        ):
            result = self.rehearse()
        self.assertEqual(result.source_commit, self.commit)
        self.assertEqual(len(observed), 8)
        wrappers = {value["wrapper"] for value in observed}
        candidate_roots = {value["candidate_root"] for value in observed}
        toolchains = {value["toolchain"] for value in observed}
        checkouts = {value["checkout"] for value in observed}
        caches = {value["cache"] for value in observed}
        homes = {value["home"] for value in observed}
        xdgs = {value["xdg"] for value in observed}
        self.assertEqual(len(wrappers), 2)
        self.assertEqual(len(candidate_roots), 2)
        self.assertEqual(len(toolchains), 2)
        self.assertEqual(len(checkouts), 2)
        self.assertEqual(len(caches), 2)
        self.assertEqual(len(homes), 2)
        self.assertEqual(len(xdgs), 2)
        self.assertTrue(all(home != invoking_home and home.name == "home" for home in homes))
        self.assertTrue(all(xdg != invoking_home and xdg.parent in homes for xdg in xdgs))
        for cache in caches:
            owner = next(root for root in candidate_roots if cache.is_relative_to(root))
            other = next(root for root in candidate_roots if root != owner)
            checkout = next(path for path in checkouts if path.parent == owner)
            self.assertTrue(cache.is_absolute())
            self.assertEqual(cache, owner / "python-bytecode-cache")
            self.assertFalse(cache.is_relative_to(checkout))
            self.assertFalse(cache.is_relative_to(self.repository))
            self.assertFalse(cache.is_relative_to(other))
            self.assertNotEqual(str(cache), inherited_cache)
        self.assertEqual(
            {value["code"] for value in observed},
            {"PACKAGE_BUILD_FAILED", "PACKAGE_VALIDATION_FAILED", "ARCHIVE_BUILD_FAILED", "ARCHIVE_VALIDATION_FAILED"},
        )
        contents = {value["content"] for value in observed}
        self.assertEqual(len(contents), 1)
        content = contents.pop()
        self.assertEqual(content.count("\n"), 2)
        self.assertTrue(content.endswith("\n"))
        self.assertNotIn("~", content)
        self.assertNotIn("$HOME", content)
        self.assertEqual(
            shlex.split(content.splitlines()[1]),
            [str(self.host_java), "-Xmx4G", "-jar", str(self.host_jar), "$@"],
        )
        for value in observed:
            self.assertTrue(value["regular"])
            self.assertEqual(value["mode"], 0o755)
            self.assertEqual(value["resolved_robot"], str(value["wrapper"]))
            self.assertEqual(
                value["reported_environment"],
                {
                    "cache": str(value["cache"]),
                    "dont_write": "1",
                    "nested": {
                        "cache": str(value["cache"]),
                        "dont_write": "1",
                    },
                },
            )
        self.assertTrue(all(not os.path.lexists(path) for path in wrappers))
        self.assertTrue(all(not path.exists() for path in candidate_roots | toolchains | checkouts | caches | homes | xdgs))

    def test_candidate_bytecode_caches_isolate_explicit_and_nested_compilation(self) -> None:
        inherited_cache = "/some/shared/inherited/cache"
        repository_bytecode_before = self.repository_bytecode_paths()
        observed: dict[Path, dict[str, object]] = {}
        original_phase = rehearsal._phase_command

        def compile_probe(code, field, command, *, checkout, environment):
            candidate_root = checkout.parent
            if candidate_root not in observed:
                module = candidate_root / "candidate_bytecode_probe.py"
                module.write_text("VALUE = 17\n", encoding="utf-8")
                label = candidate_root.name
                script = r'''
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

module = Path(sys.argv[1])
label = sys.argv[2]
cache = Path(os.environ["PYTHONPYCACHEPREFIX"])
compiled = Path(py_compile.compile(str(module), doraise=True))
sentinel = cache / (label + ".sentinel")
sentinel.write_text(label + "\n", encoding="utf-8")
nested = subprocess.run(
    [
        sys.executable,
        "-B",
        "-c",
        "import json, os; print(json.dumps({\"cache\": os.environ[\"PYTHONPYCACHEPREFIX\"], \"dont_write\": os.environ[\"PYTHONDONTWRITEBYTECODE\"]}, sort_keys=True))",
    ],
    env=os.environ.copy(),
    check=True,
    capture_output=True,
    text=True,
)
print(json.dumps({
    "cache": str(cache),
    "compiled": str(compiled),
    "dont_write": os.environ["PYTHONDONTWRITEBYTECODE"],
    "entries": sorted(path.relative_to(cache).as_posix() for path in cache.rglob("*") if path.is_file()),
    "nested": json.loads(nested.stdout),
    "sentinel": str(sentinel),
    "sentinel_bytes": sentinel.read_bytes().decode("ascii"),
}, sort_keys=True))
'''
                completed = subprocess.run(
                    [sys.executable, "-B", "-c", script, str(module), label],
                    cwd=checkout,
                    env=dict(environment),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )
                observed[candidate_root] = json.loads(completed.stdout)
            return original_phase(code, field, command, checkout=checkout, environment=environment)

        with mock.patch.dict(
            os.environ,
            {
                "PYTHONPYCACHEPREFIX": inherited_cache,
                rehearsal.VALIDATION_PYCACHE_ENVIRONMENT: inherited_cache,
                rehearsal.VALIDATION_GUARD_ENVIRONMENT: "/some/shared/inherited/guard",
            },
        ), mock.patch.object(rehearsal, "_phase_command", side_effect=compile_probe):
            result = self.rehearse()
        self.assertEqual(result.source_commit, self.commit)
        self.assertEqual(len(observed), 2)
        roots = set(observed)
        caches = {Path(value["cache"]) for value in observed.values()}
        self.assertEqual(len(caches), 2)
        for candidate_root, report in observed.items():
            cache = Path(report["cache"])
            checkout = candidate_root / "checkout"
            other_root = next(root for root in roots if root != candidate_root)
            self.assertTrue(cache.is_absolute())
            self.assertEqual(cache, candidate_root / "python-bytecode-cache")
            self.assertNotEqual(str(cache), inherited_cache)
            self.assertFalse(cache.is_relative_to(checkout))
            self.assertFalse(cache.is_relative_to(self.repository))
            self.assertFalse(cache.is_relative_to(other_root))
            self.assertTrue(Path(report["compiled"]).is_relative_to(cache))
            self.assertTrue(Path(report["sentinel"]).is_relative_to(cache))
            self.assertEqual(report["sentinel_bytes"], candidate_root.name + "\n")
            self.assertIn(candidate_root.name + ".sentinel", report["entries"])
            self.assertNotIn(other_root.name + ".sentinel", report["entries"])
            self.assertEqual(report["dont_write"], "1")
            self.assertEqual(
                report["nested"],
                {"cache": str(cache), "dont_write": "1"},
            )
        self.assertEqual(self.repository_bytecode_paths(), repository_bytecode_before)
        self.assertTrue(all(not root.exists() for root in roots))
        self.assertTrue(all(not cache.exists() for cache in caches))

    def test_home_relative_wrapper_is_reverified_through_candidate_absolute_wrapper(self) -> None:
        repository, host_home, java, original_robot, robot_jar, invoking_environment = (
            self.create_production_toolchain_fixture()
        )
        self.assertIn("~/tools/robot/robot.jar", original_robot.read_text(encoding="utf-8"))
        with mock.patch.dict(os.environ, invoking_environment, clear=True), mock.patch.object(
            rehearsal,
            "resolve_validation_toolchain",
            production_build.resolve_validation_toolchain,
        ):
            verified = rehearsal._preflight_validation_toolchain(repository)
            candidate_root = self.root / "production-candidate"
            candidate_root.mkdir()
            guard = candidate_root / "offline-python"
            guard.mkdir()
            (guard / "sitecustomize.py").write_text(rehearsal.SITE_CUSTOMIZE, encoding="utf-8")
            toolchain_bin = rehearsal._provision_candidate_toolchain(candidate_root, verified)
            candidate_environment = rehearsal._candidate_environment(
                candidate_root,
                repository,
                repository,
                guard,
                toolchain_bin,
            )
        self.assertEqual(verified.java_executable, java.resolve())
        self.assertEqual(verified.robot_jar, robot_jar.resolve())
        self.assertEqual(verified.robot_executable, original_robot.resolve())
        self.assertFalse((Path(candidate_environment["HOME"]) / "tools/robot/robot.jar").exists())
        self.assertNotEqual(Path(candidate_environment["HOME"]), host_home)
        wrapper = toolchain_bin / "robot"
        self.assertEqual(shutil.which("robot", path=candidate_environment["PATH"]), str(wrapper))
        completed = self.run_candidate_toolchain_resolver(repository, candidate_environment)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertNotIn("UNVERIFIED_ROBOT_ARTIFACT", completed.stdout + completed.stderr)
        resolved = json.loads(completed.stdout)
        self.assertEqual(
            resolved,
            {
                "hash": production_build.sha256_bytes(robot_jar.read_bytes()),
                "heap": "4G",
                "jar": str(robot_jar.resolve()),
                "java": str(java.resolve()),
                "java_vendor": "Fixture Vendor",
                "java_version": "22.0.2",
                "java_vm": "Fixture VM",
                "robot_version": "1.9.7",
                "dont_write": "1",
                "cache": str(candidate_root / "python-bytecode-cache"),
            },
        )

        wrapper_bytes = wrapper.read_bytes()
        java_bytes = java.read_bytes()
        jar_bytes = robot_jar.read_bytes()

        def restore_fixture() -> None:
            if os.path.lexists(robot_jar):
                if robot_jar.is_dir() and not robot_jar.is_symlink():
                    shutil.rmtree(robot_jar)
                else:
                    robot_jar.unlink()
            robot_jar.write_bytes(jar_bytes)
            java.write_bytes(java_bytes)
            java.chmod(0o755)
            wrapper.write_bytes(wrapper_bytes)
            wrapper.chmod(0o755)

        scenarios = (
            ("missing_jar", lambda: robot_jar.unlink(), "resolved ROBOT JAR is not a regular file"),
            ("changed_jar", lambda: robot_jar.write_bytes(b"changed jar\n"), "ROBOT_SHA256_MISMATCH"),
            (
                "nonregular_jar",
                lambda: (robot_jar.unlink(), robot_jar.mkdir()),
                "resolved ROBOT JAR is not a regular file",
            ),
            ("nonexecutable_java", lambda: java.chmod(0o644), "resolved Java executable is not an executable file"),
            (
                "mutated_wrapper",
                lambda: wrapper.write_text(
                    '#!/bin/sh\njava -Xmx4G -jar ~/tools/robot/robot.jar "$@"\n',
                    encoding="utf-8",
                ),
                "resolved ROBOT JAR is not a regular file",
            ),
        )
        for name, mutate, diagnostic in scenarios:
            with self.subTest(case=name):
                restore_fixture()
                mutate()
                failure = self.run_candidate_toolchain_resolver(repository, candidate_environment)
                self.assertNotEqual(failure.returncode, 0)
                self.assertIn(diagnostic, failure.stdout + failure.stderr)
        restore_fixture()

    def test_toolchain_paths_do_not_leak_into_governed_candidate_outputs(self) -> None:
        leaked: list[tuple[str, str]] = []
        sensitive_paths: set[Path] = set()
        candidate_models: list[str] = []
        results: list[rehearsal.RehearsalResult] = []
        original_build = rehearsal._build_candidate
        original_rehearse = rehearsal.rehearse_release

        def inspect_candidate(candidate_root, *args, **kwargs):
            candidate = original_build(candidate_root, *args, **kwargs)
            toolchain_bin = Path(candidate.environment["PATH"].split(os.pathsep)[0])
            guard_directory = Path(args[7])
            candidate_sensitive = {
                Path(candidate_root),
                candidate.checkout,
                toolchain_bin.parent,
                toolchain_bin,
                toolchain_bin / "robot",
                Path(candidate.environment["PYTHONPYCACHEPREFIX"]),
                Path(candidate.environment["HOME"]),
                Path(candidate.environment["XDG_CONFIG_HOME"]),
                Path(candidate.environment["TMPDIR"]),
                self.host_home,
                self.host_java,
                self.host_jar,
                guard_directory,
            }
            sensitive_paths.update(candidate_sensitive)
            sensitive = tuple(
                str(path).encode("utf-8")
                for path in sorted(candidate_sensitive, key=lambda value: str(value))
            )
            governed_values: list[tuple[str, bytes]] = [
                *(
                    (f"package:{path.relative_to(candidate.package_dir).as_posix()}", path.read_bytes())
                    for path in candidate.package_dir.rglob("*")
                    if path.is_file()
                ),
                ("manifest:raw", (candidate.package_dir / "manifest.json").read_bytes()),
                ("manifest:model", repr(candidate.manifest).encode("utf-8")),
                ("SHA256SUMS", (candidate.package_dir / "SHA256SUMS").read_bytes()),
                ("archive:raw", candidate.archive_path.read_bytes()),
                ("sidecar", candidate.sidecar_path.read_bytes()),
                ("candidate:model", repr(candidate).encode("utf-8")),
            ]
            for member in archive_tool._parse_raw_archive(candidate.archive_path.read_bytes(), RELEASE_ID):
                if not member.is_directory:
                    governed_values.append((f"archive-member:{member.name}", member.content))
            for label, content in governed_values:
                for value in sensitive:
                    if value and value in content:
                        leaked.append((label, value.decode("utf-8")))
            candidate_models.append(repr(candidate))
            return candidate

        def fixture_rehearse(
            command,
            release_identifier,
            release_date,
            git_tag,
            source_commit,
            notes_relative,
            *,
            output_dir=None,
        ):
            with mock.patch.object(
                rehearsal,
                "load_and_validate_release_manifest",
                side_effect=self.manifest_loader,
            ):
                result = original_rehearse(
                    command,
                    release_identifier,
                    release_date,
                    git_tag,
                    source_commit,
                    notes_relative,
                    output_dir=output_dir,
                    repository_root=self.repository,
                )
            results.append(result)
            return result

        standard_output = io.StringIO()
        standard_error = io.StringIO()
        arguments = [
            "verify",
            "--release-id",
            RELEASE_ID,
            "--release-date",
            RELEASE_ID,
            "--git-tag",
            "v" + RELEASE_ID,
            "--source-commit",
            self.commit,
            "--notes",
            NOTES,
        ]
        with mock.patch.dict(os.environ, {"HOME": str(self.host_home)}), mock.patch.object(
            rehearsal,
            "_build_candidate",
            side_effect=inspect_candidate,
        ), mock.patch.object(
            rehearsal,
            "rehearse_release",
            side_effect=fixture_rehearse,
        ), contextlib.redirect_stdout(standard_output), contextlib.redirect_stderr(standard_error):
            return_code = rehearsal.main(arguments)
        self.assertEqual(return_code, 0, standard_output.getvalue() + standard_error.getvalue())
        self.assertEqual(leaked, [])
        self.assertEqual(len(results), 1)
        stable_values = (
            *candidate_models,
            repr(results[0]),
            standard_output.getvalue(),
            standard_error.getvalue(),
        )
        for path in sensitive_paths:
            encoded = str(path)
            for value in stable_values:
                self.assertNotIn(encoded, value)
        self.assertIn("Release rehearsal: PASS", standard_output.getvalue())
        self.assertEqual(standard_error.getvalue(), "")
        self.assertTrue(sensitive_paths)
        self.assertTrue(all(not os.path.lexists(path) for path in sensitive_paths if "invoking-home" not in str(path)))

    def test_candidate_toolchain_cleanup_after_wrapper_and_each_phase_failure(self) -> None:
        environment = rehearsal._sanitized_environment(self.root / "toolchain-cleanup-snapshot")
        before = rehearsal.snapshot_repository(self.repository, environment)
        scenarios = (
            "wrapper",
            "PACKAGE_BUILD_FAILED",
            "PACKAGE_VALIDATION_FAILED",
            "ARCHIVE_BUILD_FAILED",
            "ARCHIVE_VALIDATION_FAILED",
        )
        for target in scenarios:
            with self.subTest(boundary=target):
                wrappers: list[Path] = []
                caches: list[Path] = []
                original_provision = rehearsal._provision_candidate_toolchain
                original_phase = rehearsal._phase_command
                failed = False

                def provision(candidate_root, toolchain):
                    nonlocal failed
                    toolchain_bin = original_provision(candidate_root, toolchain)
                    wrappers.append(toolchain_bin / "robot")
                    if target == "wrapper" and not failed:
                        failed = True
                        raise rehearsal.ReleaseRehearsalError(
                            (rehearsal.rehearsal_issue("PACKAGE_BUILD_FAILED", "toolchain", "injected after wrapper"),)
                        )
                    return toolchain_bin

                def phase(code, field, command, *, checkout, environment):
                    nonlocal failed
                    caches.append(Path(environment["PYTHONPYCACHEPREFIX"]))
                    result = original_phase(code, field, command, checkout=checkout, environment=environment)
                    if code == target and not failed:
                        failed = True
                        raise rehearsal.ReleaseRehearsalError(
                            (rehearsal.rehearsal_issue(code, field, "injected after phase"),)
                        )
                    return result

                with mock.patch.object(
                    rehearsal,
                    "_provision_candidate_toolchain",
                    side_effect=provision,
                ), mock.patch.object(rehearsal, "_phase_command", side_effect=phase), self.assertRaises(
                    rehearsal.ReleaseRehearsalError
                ):
                    self.rehearse()
                self.assertTrue(failed)
                self.assertTrue(wrappers)
                self.assertTrue(all(not os.path.lexists(path) for path in wrappers))
                self.assertTrue(all(not path.parents[1].exists() for path in wrappers))
                self.assertTrue(all(not path.exists() for path in caches))
                self.assertEqual(rehearsal.snapshot_repository(self.repository, environment), before)

    def test_verify_uses_two_clean_detached_clones_and_leaves_no_result(self) -> None:
        environment = rehearsal._sanitized_environment(self.root / "snapshot-environment")
        before = rehearsal.snapshot_repository(self.repository, environment)
        candidate_roots: list[Path] = []
        candidate_notes: list[bytes] = []
        original = rehearsal._build_candidate

        def record_candidate(candidate_root, *args, **kwargs):
            candidate_roots.append(candidate_root)
            candidate = original(candidate_root, *args, **kwargs)
            candidate_notes.append((candidate.checkout / NOTES).read_bytes())
            return candidate

        with mock.patch.object(rehearsal, "_build_candidate", side_effect=record_candidate):
            result = self.rehearse()
        self.assertEqual(result.source_commit, self.commit)
        self.assertEqual((result.package_file_count, result.archive_member_count), (13, 17))
        self.assertIsNone(result.output_dir)
        self.assertEqual(rehearsal.snapshot_repository(self.repository, environment), before)
        self.assertEqual(len(candidate_roots), 2)
        self.assertNotEqual(candidate_roots[0], candidate_roots[1])
        self.assertTrue(all(not path.exists() for path in candidate_roots))
        self.assertEqual(candidate_notes, [(REPO_ROOT / NOTES).read_bytes(), (REPO_ROOT / NOTES).read_bytes()])

    def test_verify_cli_uses_the_committed_repository_root(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "tools/rehearse_release.py",
                "verify",
                "--release-id",
                RELEASE_ID,
                "--release-date",
                RELEASE_ID,
                "--git-tag",
                "v" + RELEASE_ID,
                "--source-commit",
                self.commit,
                "--notes",
                NOTES,
            ],
            cwd=self.repository,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Release rehearsal: PASS", completed.stdout)
        self.assertIn(f"Source commit: {self.commit}", completed.stdout)

    def test_build_atomically_publishes_exact_result_layout(self) -> None:
        output = self.root / "external" / "result"
        output.parent.mkdir()
        candidate_roots: list[Path] = []
        original_build = rehearsal._build_candidate
        original_rename = rehearsal.atomic_rename_noreplace
        publication_calls = 0

        def record_candidate(candidate_root, *args, **kwargs):
            candidate_roots.append(candidate_root)
            return original_build(candidate_root, *args, **kwargs)

        def assert_publication_boundary(source, destination):
            nonlocal publication_calls
            if Path(destination) == output:
                publication_calls += 1
                self.assertFalse(output.exists())
                self.assertTrue(all(not path.exists() for path in candidate_roots))
            return original_rename(source, destination)

        with mock.patch.object(rehearsal, "_build_candidate", side_effect=record_candidate), mock.patch.object(
            rehearsal,
            "atomic_rename_noreplace",
            side_effect=assert_publication_boundary,
        ):
            result = self.rehearse("build", output=output)
        self.assertEqual(publication_calls, 1)
        self.assertEqual(result.output_dir, output)
        observed = {path.relative_to(output).as_posix() for path in output.rglob("*")}
        expected = {
            "releases",
            f"releases/{RELEASE_ID}",
            *(f"releases/{RELEASE_ID}/{directory}" for directory in rehearsal.EXPECTED_DIRECTORIES),
            *(f"releases/{RELEASE_ID}/{path}" for path in PACKAGE_FILE_PATHS),
            f"SSN2BFO-{RELEASE_ID}.tar",
            f"SSN2BFO-{RELEASE_ID}.tar.sha256",
        }
        self.assertEqual(observed, expected)
        self.assertFalse(any(path.name.startswith(".release-rehearsal-output-") for path in output.parent.iterdir()))

    def test_source_commit_syntax_existence_and_object_type_are_enforced(self) -> None:
        environment = rehearsal._sanitized_environment(self.root / "git-environment")
        for value, code in ((self.commit[:12], "SOURCE_COMMIT_FORMAT"), ("A" * 40, "SOURCE_COMMIT_FORMAT"), ("f" * 40, "SOURCE_COMMIT_NOT_FOUND")):
            with self.subTest(value=value), self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
                rehearsal._validate_source_commit(self.repository, environment, value)
            self.assertIn(code, {issue.code for issue in raised.exception.issues})
        blob = run_git(self.repository, "hash-object", "-w", "--stdin", input_bytes=b"blob").stdout.decode().strip()
        tree = run_git(self.repository, "rev-parse", "HEAD^{tree}").stdout.decode().strip()
        run_git(
            self.repository,
            "-c", "user.name=Release Test",
            "-c", "user.email=release@example.invalid",
            "tag", "-a", "object-fixture", "-m", "object fixture",
        )
        tag = run_git(self.repository, "rev-parse", "refs/tags/object-fixture^{tag}").stdout.decode().strip()
        run_git(self.repository, "tag", "-d", "object-fixture")
        for value in (blob, tree, tag):
            with self.subTest(object=value), self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
                rehearsal._validate_source_commit(self.repository, environment, value)
            self.assertIn("SOURCE_OBJECT_NOT_COMMIT", {issue.code for issue in raised.exception.issues})

    def test_detached_invoking_head_is_accepted_and_preserved(self) -> None:
        run_git(self.repository, "checkout", "--detach", "-q", self.commit)
        result = self.rehearse()
        self.assertEqual(result.source_commit, self.commit)
        symbolic = subprocess.run(
            ["git", "-C", str(self.repository), "symbolic-ref", "-q", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(symbolic.returncode, 0)

    def test_requested_commit_must_equal_invoking_head(self) -> None:
        previous = self.commit
        (self.repository / "second.txt").write_text("second\n", encoding="utf-8")
        run_git(self.repository, "add", "second.txt")
        run_git(
            self.repository,
            "-c", "user.name=Release Test",
            "-c", "user.email=release@example.invalid",
            "commit", "-q", "-m", "second",
        )
        environment = rehearsal._sanitized_environment(self.root / "head-environment")
        with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            rehearsal._validate_source_commit(self.repository, environment, previous)
        self.assertIn("INVOKING_HEAD_MISMATCH", {issue.code for issue in raised.exception.issues})

    def test_staged_unstaged_and_nonignored_untracked_files_are_rejected(self) -> None:
        scenarios = (
            ("staged", lambda: ((self.repository / "tracked.txt").write_text("staged\n"), run_git(self.repository, "add", "tracked.txt"))),
            ("unstaged", lambda: (self.repository / "tracked.txt").write_text("unstaged\n")),
            ("untracked", lambda: (self.repository / "untracked.txt").write_text("untracked\n")),
        )
        for name, mutate in scenarios:
            with self.subTest(case=name):
                mutate()
                with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
                    self.rehearse()
                self.assertIn("DIRTY_INVOKING_CHECKOUT", {issue.code for issue in raised.exception.issues})
                run_git(self.repository, "reset", "--hard", "-q", self.commit)
                (self.repository / "untracked.txt").unlink(missing_ok=True)

    def test_unsupported_gitlink_is_rejected_before_worktree_access(self) -> None:
        run_git(
            self.repository,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{self.commit},vendor/module",
        )
        environment = rehearsal._sanitized_environment(self.root / "gitlink-environment")
        with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            rehearsal.snapshot_repository(self.repository, environment)
        self.assertIn("UNSUPPORTED_SOURCE_ENTRY", {issue.code for issue in raised.exception.issues})

    def test_ignored_cache_is_permitted_but_cannot_enter_candidates(self) -> None:
        ignored = self.repository / "ignored-cache/value"
        ignored.parent.mkdir()
        ignored.write_text("ignored\n", encoding="utf-8")
        result = self.rehearse()
        self.assertEqual(result.source_commit, self.commit)
        self.assertEqual(ignored.read_text(encoding="utf-8"), "ignored\n")

    def test_candidate_integrity_rejects_staged_untracked_ignored_bytes_and_modes(self) -> None:
        candidate_root = self.root / "direct-candidate"
        candidate = self.build_staging_candidate("direct-candidate")
        checkout = candidate.checkout
        git_environment = rehearsal._sanitized_environment(candidate_root / "integrity-home")
        scenarios = (
            ("staged", lambda: ((checkout / "tracked.txt").write_text("staged\n", encoding="utf-8"), rehearsal._git(checkout, git_environment, "add", "tracked.txt"))),
            ("untracked", lambda: (checkout / "untracked.txt").write_text("untracked\n", encoding="utf-8")),
            ("ignored", lambda: ((checkout / "ignored-cache").mkdir(), (checkout / "ignored-cache/value").write_text("ignored\n", encoding="utf-8"))),
            ("mode", lambda: (checkout / "tracked.txt").chmod(0o755)),
        )
        for name, mutate in scenarios:
            with self.subTest(case=name):
                mutate()
                issues = rehearsal._candidate_integrity_issues(checkout, git_environment, self.commit)
                self.assertIn("TEMP_CHECKOUT_DIRTY", {issue.code for issue in issues})
                if name == "mode":
                    self.assertIn("TEMP_CHECKOUT_MUTATED", {issue.code for issue in issues})
                rehearsal._git(checkout, git_environment, "reset", "--hard", "-q", self.commit)
                rehearsal._git(checkout, git_environment, "clean", "-fdx", "-q")

    def test_candidate_integrity_exposes_head_dirty_and_commit_tree_diagnostics(self) -> None:
        self.commit_fixture_path("second-commit.txt")
        candidate = self.build_staging_candidate("candidate-diagnostics")
        checkout = candidate.checkout
        environment = rehearsal._sanitized_environment(self.root / "candidate-diagnostics-home")

        previous = rehearsal._git_text(checkout, environment, "rev-parse", "HEAD^")
        rehearsal._git(checkout, environment, "checkout", "--detach", "--force", previous)
        issues = rehearsal._candidate_integrity_issues(checkout, environment, self.commit)
        self.assertIn("TEMP_CHECKOUT_HEAD_MISMATCH", {issue.code for issue in issues})
        rehearsal._git(checkout, environment, "checkout", "--detach", "--force", self.commit)

        dirty_cases = (
            ("staged", lambda: ((checkout / "tracked.txt").write_text("staged\n", encoding="utf-8"), rehearsal._git(checkout, environment, "add", "tracked.txt"))),
            ("tracked", lambda: (checkout / "tracked.txt").write_text("tracked-change\n", encoding="utf-8")),
            ("untracked", lambda: (checkout / "extra.txt").write_text("extra\n", encoding="utf-8")),
            ("ignored", lambda: ((checkout / "ignored-cache").mkdir(), (checkout / "ignored-cache/value").write_text("ignored\n", encoding="utf-8"))),
        )
        for name, mutate in dirty_cases:
            with self.subTest(dirty=name):
                mutate()
                issues = rehearsal._candidate_integrity_issues(checkout, environment, self.commit)
                self.assertIn("TEMP_CHECKOUT_DIRTY", {issue.code for issue in issues})
                rehearsal._git(checkout, environment, "reset", "--hard", "-q", self.commit)
                rehearsal._git(checkout, environment, "clean", "-fdx", "-q")

        mutation_cases = (
            ("regular-bytes", lambda: (rehearsal._git(checkout, environment, "update-index", "--assume-unchanged", "tracked.txt"), (checkout / "tracked.txt").write_text("clean-status mutation\n", encoding="utf-8"))),
            ("missing", lambda: (rehearsal._git(checkout, environment, "update-index", "--assume-unchanged", "tracked.txt"), (checkout / "tracked.txt").unlink())),
            ("mode", lambda: (rehearsal._git(checkout, environment, "update-index", "--assume-unchanged", "tracked.txt"), (checkout / "tracked.txt").chmod(0o755))),
        )
        for name, mutate in mutation_cases:
            with self.subTest(tree=name):
                mutate()
                issues = rehearsal._candidate_integrity_issues(checkout, environment, self.commit)
                self.assertIn("TEMP_CHECKOUT_MUTATED", {issue.code for issue in issues})
                rehearsal._git(checkout, environment, "update-index", "--no-assume-unchanged", "tracked.txt")
                rehearsal._git(checkout, environment, "reset", "--hard", "-q", self.commit)

        link = self.repository / "link.txt"
        link.symlink_to("tracked.txt")
        run_git(self.repository, "add", "link.txt")
        run_git(self.repository, "-c", "user.name=Release Test", "-c", "user.email=release@example.invalid", "commit", "-q", "-m", "symlink fixture")
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()
        link_candidate = self.build_staging_candidate("candidate-link-diagnostics")
        link_checkout = link_candidate.checkout
        link_environment = rehearsal._sanitized_environment(self.root / "candidate-link-diagnostics-home")
        rehearsal._git(link_checkout, link_environment, "update-index", "--assume-unchanged", "link.txt")
        (link_checkout / "link.txt").unlink()
        (link_checkout / "link.txt").symlink_to("second-commit.txt")
        issues = rehearsal._candidate_integrity_issues(link_checkout, link_environment, self.commit)
        self.assertIn("TEMP_CHECKOUT_MUTATED", {issue.code for issue in issues})

    def test_notes_must_be_safe_committed_regular_file(self) -> None:
        with mock.patch.object(rehearsal, "load_and_validate_release_manifest", side_effect=self.manifest_loader):
            for value in (
                "../notes.md",
                ".hidden",
                "release-notes//notes.md",
                "release-notes/./notes.md",
                "release-notes\\notes.md",
                "https://example.invalid/notes.md",
                "release-notes/notes:copy.md",
                "untracked.md",
                "/absolute",
            ):
                with self.subTest(value=value), self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
                    rehearsal.rehearse_release(
                        "verify", RELEASE_ID, RELEASE_ID, "v" + RELEASE_ID, self.commit, value,
                        repository_root=self.repository,
                    )
                self.assertTrue({"RELEASE_NOTES_PATH", "RELEASE_NOTES_NOT_COMMITTED"} & {issue.code for issue in raised.exception.issues})

        link = self.repository / "release-notes/LINK.md"
        link.symlink_to("SYNTHETIC-2099-01-02.md")
        run_git(self.repository, "add", "release-notes/LINK.md")
        run_git(self.repository, "-c", "user.name=Release Test", "-c", "user.email=release@example.invalid", "commit", "-q", "-m", "notes link")
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()
        with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            self.rehearse(notes="release-notes/LINK.md")
        self.assertIn("RELEASE_NOTES_NOT_REGULAR", {issue.code for issue in raised.exception.issues})

    def test_checkout_mutation_after_build_is_detected_and_cleaned(self) -> None:
        (self.repository / "MUTATE_CHECKOUT").write_text("yes\n", encoding="utf-8")
        run_git(self.repository, "add", "MUTATE_CHECKOUT")
        run_git(self.repository, "-c", "user.name=Release Test", "-c", "user.email=release@example.invalid", "commit", "-q", "-m", "mutation fixture")
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()
        with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            self.rehearse()
        self.assertIn("TEMP_CHECKOUT_MUTATED", {issue.code for issue in raised.exception.issues})
        self.assertFalse(run_git(self.repository, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)

    def test_cross_checkout_package_nondeterminism_prevents_output(self) -> None:
        (self.repository / "NONDETERMINISTIC").write_text("yes\n", encoding="utf-8")
        run_git(self.repository, "add", "NONDETERMINISTIC")
        run_git(self.repository, "-c", "user.name=Release Test", "-c", "user.email=release@example.invalid", "commit", "-q", "-m", "nondeterminism fixture")
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()
        output = self.root / "external" / "result"
        output.parent.mkdir()
        environment = rehearsal._sanitized_environment(self.root / "failure-snapshot-environment")
        before = rehearsal.snapshot_repository(self.repository, environment)
        with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            self.rehearse("build", output=output)
        self.assertIn("NONDETERMINISTIC_PACKAGE_REBUILD", {issue.code for issue in raised.exception.issues})
        self.assertFalse(output.exists())
        self.assertEqual(rehearsal.snapshot_repository(self.repository, environment), before)

    def test_manifest_source_commit_mismatch_prevents_output(self) -> None:
        (self.repository / "SOURCE_MISMATCH").write_text("yes\n", encoding="utf-8")
        run_git(self.repository, "add", "SOURCE_MISMATCH")
        run_git(self.repository, "-c", "user.name=Release Test", "-c", "user.email=release@example.invalid", "commit", "-q", "-m", "source mismatch fixture")
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()
        output = self.root / "external" / "result"
        output.parent.mkdir()
        with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            self.rehearse("build", output=output)
        self.assertIn("SOURCE_EVIDENCE_MISMATCH", {issue.code for issue in raised.exception.issues})
        self.assertFalse(output.exists())

    def test_archive_nondeterminism_prevents_output(self) -> None:
        original = rehearsal._build_candidate
        calls = 0

        def changed_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            result = original(*args, **kwargs)
            if calls == 2:
                result.archive_path.write_bytes(result.archive_path.read_bytes() + b"changed")
            return result

        output = self.root / "external" / "result"
        output.parent.mkdir()
        with mock.patch.object(rehearsal, "_build_candidate", side_effect=changed_second), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse("build", output=output)
        self.assertIn("NONDETERMINISTIC_ARCHIVE_REBUILD", {issue.code for issue in raised.exception.issues})
        self.assertFalse(output.exists())

    def test_output_must_be_absolute_absent_external_and_unambiguous(self) -> None:
        existing = self.root / "existing"
        existing.mkdir()
        inside = self.repository / "result"
        for value, code in ((Path("relative"), "OUTPUT_PATH"), (existing, "OUTPUT_EXISTS"), (inside, "OUTPUT_INSIDE_REPOSITORY")):
            with self.subTest(value=value), self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
                self.rehearse("build", output=value)
            self.assertIn(code, {issue.code for issue in raised.exception.issues})

        real_parent = self.root / "real-output-parent"
        real_parent.mkdir()
        linked_parent = self.root / "linked-output-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            self.rehearse("build", output=linked_parent / "result")
        self.assertTrue({"OUTPUT_SYMLINK", "OUTPUT_PATH"} & {issue.code for issue in raised.exception.issues})

    def test_destination_is_rechecked_before_atomic_publication(self) -> None:
        output = self.root / "external" / "result"
        output.parent.mkdir()
        original = rehearsal.atomic_rename_noreplace

        def occupy_at_final_rename(source, destination):
            self.assertEqual(Path(destination), output)
            output.mkdir()
            (output / "racer.txt").write_bytes(b"racing destination\n")
            return original(source, destination)

        with mock.patch.object(rehearsal, "atomic_rename_noreplace", side_effect=occupy_at_final_rename), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse("build", output=output)
        self.assertIn("OUTPUT_EXISTS", {issue.code for issue in raised.exception.issues})
        self.assertEqual((output / "racer.txt").read_bytes(), b"racing destination\n")
        self.assertFalse(any(path.name.startswith(".release-rehearsal-output-") for path in output.parent.iterdir()))

    def test_hidden_rehearsal_staging_siblings_are_rejected_without_adoption(self) -> None:
        parent = self.root / "external"
        parent.mkdir()
        replacement_target = self.root / "replacement-target"
        replacement_target.mkdir()
        (replacement_target / "sentinel").write_bytes(b"target\n")
        cases = (
            ("directory", lambda path: (path.mkdir(), (path / "sentinel").write_bytes(b"directory\n"))),
            ("file", lambda path: path.write_bytes(b"file\n")),
            ("symlink", lambda path: path.symlink_to(replacement_target, target_is_directory=True)),
            ("multiple", lambda path: (path.mkdir(), (parent / ".release-rehearsal-output-second").write_bytes(b"second\n"))),
        )
        for name, create in cases:
            with self.subTest(case=name):
                sibling = parent / ".release-rehearsal-output-unrelated"
                create(sibling)
                before = {
                    path.name: (path.lstat().st_mode, path.readlink() if path.is_symlink() else path.read_bytes() if path.is_file() else None)
                    for path in parent.iterdir()
                }
                with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
                    self.rehearse("build", output=parent / f"result-{name}")
                self.assert_codes(raised, "OUTPUT_EXISTS")
                after = {
                    path.name: (path.lstat().st_mode, path.readlink() if path.is_symlink() else path.read_bytes() if path.is_file() else None)
                    for path in parent.iterdir()
                }
                self.assertEqual(after, before)
                for path in list(parent.iterdir()):
                    if path.is_symlink() or path.is_file():
                        path.unlink()
                    else:
                        shutil.rmtree(path)

        ordinary = parent / "ordinary-sibling"
        ordinary.write_bytes(b"ordinary\n")
        output = parent / "ordinary-result"
        self.rehearse("build", output=output)
        self.assertEqual(ordinary.read_bytes(), b"ordinary\n")

    def test_postpublication_failure_never_treats_published_output_as_cleanup_owned(self) -> None:
        parent = self.root / "external"
        parent.mkdir()
        original = rehearsal.atomic_rename_noreplace

        output = parent / "complete-after-error"

        def publish_then_raise(source, destination):
            original(source, destination)
            raise RuntimeError("injected after successful publication")

        with mock.patch.object(rehearsal, "atomic_rename_noreplace", side_effect=publish_then_raise), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse("build", output=output)
        self.assert_codes(raised, "ATOMIC_PUBLICATION_FAILED")
        self.assertTrue(output.is_dir())
        self.assertTrue((output / f"SSN2BFO-{RELEASE_ID}.tar").is_file())
        self.assertFalse(any(path.name.startswith(".release-rehearsal-output-") for path in parent.iterdir()))

        directory_replacement = parent / "directory-replacement"
        sentinel = self.root / "directory-sentinel"
        sentinel.mkdir()
        (sentinel / "sentinel").write_bytes(b"preserve directory replacement\n")

        def publish_replace_directory_then_raise(source, destination):
            original(source, destination)
            shutil.rmtree(destination)
            shutil.copytree(sentinel, destination)
            raise RuntimeError("replacement after publication")

        with mock.patch.object(rehearsal, "atomic_rename_noreplace", side_effect=publish_replace_directory_then_raise), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse("build", output=directory_replacement)
        self.assert_codes(raised, "ATOMIC_PUBLICATION_FAILED", "CLEANUP_FAILED")
        self.assertEqual((directory_replacement / "sentinel").read_bytes(), b"preserve directory replacement\n")

        link_replacement = parent / "link-replacement"
        link_target = self.root / "link-sentinel"
        link_target.mkdir()
        (link_target / "sentinel").write_bytes(b"preserve symlink replacement\n")

        def publish_replace_symlink_then_raise(source, destination):
            original(source, destination)
            shutil.rmtree(destination)
            destination.symlink_to(link_target, target_is_directory=True)
            raise RuntimeError("symlink replacement after publication")

        with mock.patch.object(rehearsal, "atomic_rename_noreplace", side_effect=publish_replace_symlink_then_raise), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse("build", output=link_replacement)
        self.assert_codes(raised, "ATOMIC_PUBLICATION_FAILED", "CLEANUP_FAILED")
        self.assertTrue(link_replacement.is_symlink())
        self.assertEqual((link_target / "sentinel").read_bytes(), b"preserve symlink replacement\n")

    def test_phase_boundary_detects_package_build_mutation_before_package_validation(self) -> None:
        self.commit_fixture_path("MUTATE_AFTER_PACKAGE_BUILD")
        commands: list[str] = []
        original = rehearsal._phase_command

        def record_phase(code, field, command, **kwargs):
            commands.append(Path(command[2]).name)
            return original(code, field, command, **kwargs)

        with mock.patch.object(rehearsal, "_phase_command", side_effect=record_phase), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse()
        self.assert_codes(raised, "TEMP_CHECKOUT_MUTATED")
        self.assertEqual(commands, ["build_release.py"])

    def test_phase_boundary_detects_package_validation_mutation_and_ignored_residue(self) -> None:
        for marker in ("MUTATE_AFTER_PACKAGE_VALIDATION", "IGNORED_AFTER_PACKAGE_VALIDATION", "IGNORED_AFTER_PACKAGE_BUILD"):
            with self.subTest(marker=marker):
                self.commit_fixture_path(marker)
                commands: list[str] = []
                original = rehearsal._phase_command

                def record_phase(code, field, command, **kwargs):
                    commands.append(Path(command[2]).name)
                    return original(code, field, command, **kwargs)

                with mock.patch.object(rehearsal, "_phase_command", side_effect=record_phase), self.assertRaises(
                    rehearsal.ReleaseRehearsalError
                ) as raised:
                    self.rehearse()
                self.assert_codes(
                    raised,
                    "TEMP_CHECKOUT_DIRTY" if marker.startswith("IGNORED_") else "TEMP_CHECKOUT_MUTATED",
                )
                if marker == "IGNORED_AFTER_PACKAGE_BUILD":
                    self.assertEqual(commands, ["build_release.py"])
                else:
                    self.assertEqual(commands, ["build_release.py", "check_release.py"])
                run_git(self.repository, "rm", "-q", marker)
                run_git(
                    self.repository,
                    "-c", "user.name=Release Test",
                    "-c", "user.email=release@example.invalid",
                    "commit", "-q", "-m", f"remove {marker}",
                )
                self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()

    def test_mutate_then_restore_is_rejected_before_later_phase_can_restore_it(self) -> None:
        self.commit_fixture_path("MUTATE_THEN_RESTORE")
        commands: list[str] = []
        original = rehearsal._phase_command

        def record_phase(code, field, command, **kwargs):
            commands.append(Path(command[2]).name)
            return original(code, field, command, **kwargs)

        with mock.patch.object(rehearsal, "_phase_command", side_effect=record_phase), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse()
        self.assert_codes(raised, "TEMP_CHECKOUT_MUTATED")
        self.assertEqual(commands, ["build_release.py"])

    def test_phase_boundary_detects_tracked_and_ignored_residue_after_each_archive_phase(self) -> None:
        archive_script = self.repository / "tools/release_archive.py"
        value = archive_script.read_text(encoding="utf-8")
        hook = '''\nif Path("MUTATE_AFTER_ARCHIVE_BUILD").exists() and len(sys.argv) > 1 and sys.argv[1] == "build-candidate":\n    Path("tracked.txt").write_text("mutated-after-archive-build\\n", encoding="utf-8")\nif Path("MUTATE_AFTER_ARCHIVE_VALIDATION").exists() and len(sys.argv) > 1 and sys.argv[1] == "validate":\n    Path("tracked.txt").write_text("mutated-after-archive-validation\\n", encoding="utf-8")\nif Path("IGNORED_AFTER_ARCHIVE_BUILD").exists() and len(sys.argv) > 1 and sys.argv[1] == "build-candidate":\n    Path("ignored-cache/from-archive-build").parent.mkdir(exist_ok=True)\n    Path("ignored-cache/from-archive-build").write_text("ignored\\n", encoding="utf-8")\nif Path("IGNORED_AFTER_ARCHIVE_VALIDATION").exists() and len(sys.argv) > 1 and sys.argv[1] == "validate":\n    Path("ignored-cache/from-archive-validation").parent.mkdir(exist_ok=True)\n    Path("ignored-cache/from-archive-validation").write_text("ignored\\n", encoding="utf-8")\n\n'''
        archive_script.write_text(value.replace("from pathlib import Path, PurePosixPath\n", "from pathlib import Path, PurePosixPath\n" + hook), encoding="utf-8")
        run_git(self.repository, "add", "tools/release_archive.py")
        run_git(
            self.repository,
            "-c", "user.name=Release Test",
            "-c", "user.email=release@example.invalid",
            "commit", "-q", "-m", "archive phase hooks",
        )
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()
        cases = (
            ("MUTATE_AFTER_ARCHIVE_BUILD", "TEMP_CHECKOUT_MUTATED", ["build_release.py", "check_release.py", "release_archive.py:build-candidate"]),
            ("MUTATE_AFTER_ARCHIVE_VALIDATION", "TEMP_CHECKOUT_MUTATED", ["build_release.py", "check_release.py", "release_archive.py:build-candidate", "release_archive.py:validate"]),
            ("IGNORED_AFTER_ARCHIVE_BUILD", "TEMP_CHECKOUT_DIRTY", ["build_release.py", "check_release.py", "release_archive.py:build-candidate"]),
            ("IGNORED_AFTER_ARCHIVE_VALIDATION", "TEMP_CHECKOUT_DIRTY", ["build_release.py", "check_release.py", "release_archive.py:build-candidate", "release_archive.py:validate"]),
        )
        for marker, expected_code, expected_commands in cases:
            with self.subTest(marker=marker):
                self.commit_fixture_path(marker)
                commands: list[str] = []
                original = rehearsal._phase_command

                def record_phase(code, field, command, **kwargs):
                    label = Path(command[2]).name
                    if label == "release_archive.py":
                        label += ":" + command[3]
                    commands.append(label)
                    return original(code, field, command, **kwargs)

                with mock.patch.object(rehearsal, "_phase_command", side_effect=record_phase), self.assertRaises(
                    rehearsal.ReleaseRehearsalError
                ) as raised:
                    self.rehearse()
                self.assert_codes(raised, expected_code)
                self.assertEqual(commands, expected_commands)
                run_git(self.repository, "rm", "-q", marker)
                run_git(
                    self.repository,
                    "-c", "user.name=Release Test",
                    "-c", "user.email=release@example.invalid",
                    "commit", "-q", "-m", f"remove {marker}",
                )
                self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()

    def test_package_and_archive_subprocess_network_attempts_are_blocked(self) -> None:
        self.commit_fixture_path("CHECK_NETWORK_ATTEMPT")
        self.assertEqual(self.rehearse().source_commit, self.commit)
        run_git(self.repository, "rm", "-q", "CHECK_NETWORK_ATTEMPT")
        archive_script = self.repository / "tools/release_archive.py"
        value = archive_script.read_text(encoding="utf-8")
        injection = '''\nif Path("ARCHIVE_NETWORK_ATTEMPT").exists():\n    import socket\n    socket.create_connection(("example.invalid", 80))\n\n'''
        archive_script.write_text(value.replace("from pathlib import Path, PurePosixPath\n", "from pathlib import Path, PurePosixPath\n" + injection), encoding="utf-8")
        run_git(self.repository, "add", "tools/release_archive.py")
        self.commit_fixture_path("ARCHIVE_NETWORK_ATTEMPT")
        with self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            self.rehearse()
        self.assert_codes(raised, "ARCHIVE_BUILD_FAILED")

    def test_staged_output_revalidation_blocks_mutated_missing_and_extra_paths(self) -> None:
        scenarios = (
            ("package", lambda result: (result / "releases" / RELEASE_ID / "LICENSE").write_bytes(b"changed\n"), "STAGED_PACKAGE_VALIDATION_FAILED"),
            ("archive", lambda result: (result / f"SSN2BFO-{RELEASE_ID}.tar").write_bytes(b"changed"), "STAGED_ARCHIVE_VALIDATION_FAILED"),
            ("sidecar", lambda result: (result / f"SSN2BFO-{RELEASE_ID}.tar.sha256").write_bytes(b"changed"), "STAGED_ARCHIVE_VALIDATION_FAILED"),
            ("missing", lambda result: (result / "releases" / RELEASE_ID / "LICENSE").unlink(), "STAGED_OUTPUT_PATH_SET"),
            ("extra", lambda result: (result / "extra.txt").write_bytes(b"extra\n"), "STAGED_OUTPUT_PATH_SET"),
        )
        candidate = self.build_staging_candidate("staged-revalidation-candidate")
        original = rehearsal._copy_candidate_output
        for name, mutate, expected in scenarios:
            with self.subTest(case=name):
                output = self.root / "external" / f"result-{name}"
                output.parent.mkdir(exist_ok=True)

                def copy_then_mutate(candidate, result, release_identifier, selected=mutate):
                    original(candidate, result, release_identifier)
                    selected(result)

                with mock.patch.object(rehearsal, "load_and_validate_release_manifest", side_effect=self.manifest_loader), mock.patch.object(
                    rehearsal, "_copy_candidate_output", side_effect=copy_then_mutate
                ), self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
                    rehearsal._stage_output(candidate, output, RELEASE_ID, self.commit)
                self.assert_codes(raised, expected)
                self.assertFalse(output.exists())
                self.assertFalse(any(path.name.startswith(".release-rehearsal-output-") for path in output.parent.iterdir()))

    def test_staged_output_byte_comparisons_run_after_revalidation_boundaries(self) -> None:
        scenarios = (
            ("package", lambda result: (result / "releases" / RELEASE_ID / "LICENSE").write_bytes(b"changed\n"), "STAGED_PACKAGE_CONTENT_MISMATCH"),
            ("archive", lambda result: (result / f"SSN2BFO-{RELEASE_ID}.tar").write_bytes(b"changed"), "STAGED_ARCHIVE_CONTENT_MISMATCH"),
            ("sidecar", lambda result: (result / f"SSN2BFO-{RELEASE_ID}.tar.sha256").write_bytes(b"changed"), "STAGED_SIDECAR_CONTENT_MISMATCH"),
        )
        candidate = self.build_staging_candidate("staged-comparison-candidate")
        original_copy = rehearsal._copy_candidate_output
        original_phase = rehearsal._phase_command
        for name, mutate, expected in scenarios:
            with self.subTest(case=name):
                output = self.root / "external" / f"comparison-{name}"
                output.parent.mkdir(exist_ok=True)

                def copy_then_mutate(candidate, result, release_identifier, selected=mutate):
                    original_copy(candidate, result, release_identifier)
                    selected(result)

                def skip_only_staged(code, field, command, **kwargs):
                    if code.startswith("STAGED_"):
                        return None
                    return original_phase(code, field, command, **kwargs)

                with mock.patch.object(rehearsal, "load_and_validate_release_manifest", side_effect=self.manifest_loader), mock.patch.object(
                    rehearsal, "_copy_candidate_output", side_effect=copy_then_mutate
                ), mock.patch.object(rehearsal, "_phase_command", side_effect=skip_only_staged), self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
                    rehearsal._stage_output(candidate, output, RELEASE_ID, self.commit)
                self.assert_codes(raised, expected)
                self.assertFalse(output.exists())

    def test_cleanup_failures_preserve_the_primary_diagnostic_and_block_publication(self) -> None:
        self.commit_fixture_path("MUTATE_AFTER_PACKAGE_BUILD")
        original_cleanup = rehearsal._cleanup_owned_path

        def cleanup_with_candidate_failure(path, field):
            issues = original_cleanup(path, field)
            if field in {"candidate_a", "candidate_b"}:
                return (*issues, rehearsal.rehearsal_issue("CLEANUP_FAILED", field, "injected candidate cleanup failure"))
            return issues

        with mock.patch.object(rehearsal, "_cleanup_owned_path", side_effect=cleanup_with_candidate_failure), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse()
        self.assert_codes(raised, "TEMP_CHECKOUT_MUTATED", "CLEANUP_FAILED")
        self.assertTrue({"candidate_a", "candidate_b"} <= {issue.field for issue in raised.exception.issues if issue.code == "CLEANUP_FAILED"})
        run_git(self.repository, "rm", "-q", "MUTATE_AFTER_PACKAGE_BUILD")
        run_git(
            self.repository,
            "-c", "user.name=Release Test",
            "-c", "user.email=release@example.invalid",
            "commit", "-q", "-m", "remove mutation marker",
        )
        self.commit = run_git(self.repository, "rev-parse", "HEAD").stdout.decode().strip()

        output = self.root / "external" / "cleanup-staging"
        output.parent.mkdir(exist_ok=True)
        candidate = self.build_staging_candidate("cleanup-staging-candidate")
        original_copy = rehearsal._copy_candidate_output

        def copy_with_extra(candidate, result, release_identifier):
            original_copy(candidate, result, release_identifier)
            (result / "extra.txt").write_bytes(b"extra\n")

        def cleanup_with_staging_failure(path, field):
            issues = original_cleanup(path, field)
            if field == "output_staging":
                return (*issues, rehearsal.rehearsal_issue("CLEANUP_FAILED", field, "injected staging cleanup failure"))
            return issues

        with mock.patch.object(rehearsal, "load_and_validate_release_manifest", side_effect=self.manifest_loader), mock.patch.object(
            rehearsal, "_copy_candidate_output", side_effect=copy_with_extra
        ), mock.patch.object(rehearsal, "_cleanup_owned_path", side_effect=cleanup_with_staging_failure), self.assertRaises(rehearsal.ReleaseRehearsalError) as raised:
            rehearsal._stage_output(candidate, output, RELEASE_ID, self.commit)
        self.assert_codes(raised, "STAGED_OUTPUT_PATH_SET", "CLEANUP_FAILED")
        self.assertFalse(output.exists())

    def test_invoking_index_bytes_and_mtime_are_preserved_after_success_and_failure(self) -> None:
        environment = rehearsal._sanitized_environment(self.root / "index-environment")
        index_path = Path(rehearsal._git_text(self.repository, environment, "rev-parse", "--git-path", "index"))
        if not index_path.is_absolute():
            index_path = self.repository / index_path
        before = (index_path.read_bytes(), index_path.stat().st_mtime_ns)
        self.rehearse()
        self.assertEqual((index_path.read_bytes(), index_path.stat().st_mtime_ns), before)
        self.commit_fixture_path("MUTATE_AFTER_PACKAGE_BUILD")
        before_failure = (index_path.read_bytes(), index_path.stat().st_mtime_ns)
        with self.assertRaises(rehearsal.ReleaseRehearsalError):
            self.rehearse()
        self.assertEqual((index_path.read_bytes(), index_path.stat().st_mtime_ns), before_failure)


if __name__ == "__main__":
    unittest.main()
