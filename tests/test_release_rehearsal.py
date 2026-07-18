#!/usr/bin/env python3
"""Clean-source detached-checkout release rehearsal regressions."""

from __future__ import annotations

import json
import os
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
from build_release import PACKAGE_FILE_PATHS  # noqa: E402


RELEASE_ID = "2099-01-02"
NOTES = "release-notes/SYNTHETIC-2099-01-02.md"


BUILD_STUB = '''#!/usr/bin/env python3
import argparse
import json
import socket
from pathlib import Path

PACKAGE_FILE_PATHS = {paths!r}

def compare_complete_packages(first, second):
    return ()

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
            )

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
