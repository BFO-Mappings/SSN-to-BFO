#!/usr/bin/env python3
"""Rehearse one release from two clean detached checkouts of an exact commit."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping
from urllib.parse import urlsplit

from build_release import PACKAGE_FILE_PATHS, compare_complete_packages
from check_release import EXPECTED_DIRECTORIES
from release_archive import (
    AtomicNoReplaceUnsupportedError,
    archive_filename,
    atomic_rename_noreplace,
    canonical_member_names,
    sidecar_filename,
)
from release_context import SOURCE_COMMIT_PATTERN, parse_formal_release_context
from release_manifest import ReleaseManifest, load_and_validate_release_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
GIT_BASE_ARGUMENTS = (
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "init.templateDir=",
    "-c",
    "core.autocrlf=false",
    "-c",
    "core.fsmonitor=false",
    "-c",
    "credential.helper=",
)
SITE_CUSTOMIZE = '''"""Deny Python network access during release rehearsal."""
import socket

def _offline(*args, **kwargs):
    raise RuntimeError("release rehearsal prohibits Python network access")

socket.socket.connect = _offline
socket.socket.connect_ex = _offline
socket.socket.sendto = _offline
if hasattr(socket.socket, "sendmsg"):
    socket.socket.sendmsg = _offline
socket.create_connection = _offline
socket.getaddrinfo = _offline
socket.gethostbyname = _offline
socket.gethostbyname_ex = _offline
socket.gethostbyaddr = _offline
socket.getnameinfo = _offline
'''


@dataclass(frozen=True)
class RehearsalIssue:
    code: str
    field: str
    message: str

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return self.field, self.code, self.message


@dataclass(frozen=True)
class TrackedPathSnapshot:
    path: str
    entry_type: str
    content: bytes
    mode: int
    mtime_ns: int


@dataclass(frozen=True)
class RepositorySnapshot:
    head: str
    symbolic_head: str | None
    status: bytes
    worktree_listing: bytes
    index_path: str
    index_content: bytes
    index_size: int
    index_mtime_ns: int
    tracked_paths: tuple[TrackedPathSnapshot, ...]


@dataclass(frozen=True)
class OwnedDirectory:
    """A recursively cleaned directory identified by its creation-time inode."""

    path: Path
    st_dev: int
    st_ino: int
    file_type: int


@dataclass(frozen=True)
class CandidateResult:
    checkout: Path
    environment: Mapping[str, str]
    package_dir: Path
    archive_path: Path
    sidecar_path: Path
    manifest: ReleaseManifest
    archive_sha256: str


@dataclass(frozen=True)
class RehearsalResult:
    release_identifier: str
    source_commit: str
    archive_sha256: str
    output_dir: Path | None
    package_file_count: int
    archive_member_count: int


class ReleaseRehearsalError(ValueError):
    """One or more deterministic release-rehearsal failures."""

    def __init__(self, issues: Iterable[RehearsalIssue]):
        self.issues = tuple(sorted(set(issues), key=lambda value: value.sort_key))
        super().__init__("; ".join(format_issue(issue) for issue in self.issues))


def format_issue(issue: RehearsalIssue) -> str:
    return f"ERROR [{issue.code}] {issue.field}: {issue.message}"


def rehearsal_issue(code: str, field: str, message: str) -> RehearsalIssue:
    return RehearsalIssue(code, field, message)


def _sanitized_environment(home: Path, base: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = dict(os.environ if base is None else base)
    for key in tuple(environment):
        if key.startswith("GIT_") or key in {
            "HOME",
            "XDG_CONFIG_HOME",
            "LC_ALL",
            "LANG",
            "TZ",
            "PYTHONPATH",
            "PYTHONHOME",
        }:
            environment.pop(key, None)
    home.mkdir(parents=True, exist_ok=True)
    xdg = home / "xdg"
    xdg.mkdir(exist_ok=True)
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_LFS_SKIP_SMUDGE": "1",
            "GCM_INTERACTIVE": "Never",
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(xdg),
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
        }
    )
    return environment


def _run(
    command: list[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=dict(environment),
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        umask=0o022,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or f"command exited {completed.returncode}")
    return completed


def _git(
    repository: Path,
    environment: Mapping[str, str],
    *arguments: str,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return _run(
        ["git", *GIT_BASE_ARGUMENTS, "-C", str(repository), *arguments],
        cwd=repository,
        environment=environment,
        input_bytes=input_bytes,
        check=check,
    )


def _git_text(repository: Path, environment: Mapping[str, str], *arguments: str) -> str:
    return _git(repository, environment, *arguments).stdout.decode("ascii").strip()


def _safe_notes_path(value: str) -> bool:
    if not value or "\\" in value or ":" in value or value.startswith("/") or urlsplit(value).scheme:
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} or part.startswith(".") for part in parts):
        return False
    return PurePosixPath(value).as_posix() == value


def _tracked_path_snapshots(repository: Path, environment: Mapping[str, str]) -> tuple[TrackedPathSnapshot, ...]:
    values: list[TrackedPathSnapshot] = []
    output = _git(repository, environment, "ls-files", "-z", "--stage").stdout
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode_text, _, stage = metadata.decode("ascii").split()
        if stage != "0":
            raise ReleaseRehearsalError(
                (rehearsal_issue("DIRTY_INVOKING_CHECKOUT", "index", "nonzero index stage found"),)
            )
        path_text = os.fsdecode(encoded_path)
        expected_mode = int(mode_text, 8)
        if expected_mode not in {0o100644, 0o100755, 0o120000}:
            raise ReleaseRehearsalError(
                (rehearsal_issue("UNSUPPORTED_SOURCE_ENTRY", path_text, f"unsupported Git mode {mode_text}"),)
            )
        path = repository / path_text
        status = path.lstat()
        if stat.S_ISLNK(status.st_mode):
            entry_type = "symlink"
            content = os.fsencode(os.readlink(path))
        elif stat.S_ISREG(status.st_mode):
            entry_type = "file"
            content = path.read_bytes()
        else:
            raise ReleaseRehearsalError(
                (rehearsal_issue("UNSUPPORTED_SOURCE_ENTRY", path_text, "tracked path is not a regular file or symlink"),)
            )
        values.append(
            TrackedPathSnapshot(
                path=path_text,
                entry_type=entry_type,
                content=content,
                mode=stat.S_IMODE(status.st_mode),
                mtime_ns=status.st_mtime_ns,
            )
        )
    return tuple(values)


def snapshot_repository(repository: Path, environment: Mapping[str, str]) -> RepositorySnapshot:
    head = _git_text(repository, environment, "rev-parse", "HEAD")
    symbolic = _git(repository, environment, "symbolic-ref", "-q", "HEAD", check=False)
    symbolic_head = symbolic.stdout.decode("ascii").strip() if symbolic.returncode == 0 else None
    status_value = _git(repository, environment, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    worktrees = _git(repository, environment, "worktree", "list", "--porcelain", "-z").stdout
    index_text = _git_text(repository, environment, "rev-parse", "--git-path", "index")
    index_path = Path(index_text)
    if not index_path.is_absolute():
        index_path = repository / index_path
    index_status = index_path.stat()
    return RepositorySnapshot(
        head=head,
        symbolic_head=symbolic_head,
        status=status_value,
        worktree_listing=worktrees,
        index_path=str(index_path.resolve()),
        index_content=index_path.read_bytes(),
        index_size=index_status.st_size,
        index_mtime_ns=index_status.st_mtime_ns,
        tracked_paths=_tracked_path_snapshots(repository, environment),
    )


def repository_snapshot_issues(
    repository: Path,
    environment: Mapping[str, str],
    expected: RepositorySnapshot,
) -> tuple[RehearsalIssue, ...]:
    try:
        actual = snapshot_repository(repository, environment)
    except Exception as exc:
        return (rehearsal_issue("SOURCE_STATE_VALIDATION_FAILED", "repository", str(exc)),)
    issues: list[RehearsalIssue] = []
    for field in ("head", "symbolic_head", "status", "worktree_listing", "index_path", "index_content", "index_size", "index_mtime_ns"):
        if getattr(actual, field) != getattr(expected, field):
            issues.append(rehearsal_issue("INVOKING_REPOSITORY_MUTATED", field, "state differs from pre-rehearsal snapshot"))
    expected_paths = {value.path: value for value in expected.tracked_paths}
    actual_paths = {value.path: value for value in actual.tracked_paths}
    if expected_paths.keys() != actual_paths.keys():
        issues.append(rehearsal_issue("INVOKING_REPOSITORY_MUTATED", "tracked_paths", "path inventory differs"))
    else:
        for path in expected_paths:
            if expected_paths[path] != actual_paths[path]:
                issues.append(rehearsal_issue("INVOKING_REPOSITORY_MUTATED", path, "tracked state differs"))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _validate_source_commit(repository: Path, environment: Mapping[str, str], source_commit: str) -> None:
    if SOURCE_COMMIT_PATTERN.fullmatch(source_commit) is None:
        raise ReleaseRehearsalError(
            (rehearsal_issue("SOURCE_COMMIT_FORMAT", "source_commit", "expected 40 lowercase hexadecimal characters"),)
        )
    result = _git(repository, environment, "cat-file", "-t", source_commit, check=False)
    if result.returncode != 0:
        raise ReleaseRehearsalError(
            (rehearsal_issue("SOURCE_COMMIT_NOT_FOUND", "source_commit", "object is not present locally"),)
        )
    object_type = result.stdout.decode("ascii").strip()
    if object_type != "commit":
        raise ReleaseRehearsalError(
            (rehearsal_issue("SOURCE_OBJECT_NOT_COMMIT", "source_commit", f"object type is {object_type}"),)
        )
    head = _git_text(repository, environment, "rev-parse", "HEAD")
    if head != source_commit:
        raise ReleaseRehearsalError(
            (rehearsal_issue("INVOKING_HEAD_MISMATCH", "source_commit", f"HEAD is {head}"),)
        )


def _validate_notes_identity(
    repository: Path,
    environment: Mapping[str, str],
    source_commit: str,
    notes_relative: str,
) -> bytes:
    if not _safe_notes_path(notes_relative):
        raise ReleaseRehearsalError(
            (rehearsal_issue("RELEASE_NOTES_PATH", "notes", "expected safe repository-relative POSIX path"),)
        )
    result = _git(
        repository,
        environment,
        "ls-tree",
        "-z",
        source_commit,
        "--",
        notes_relative,
    ).stdout
    records = [value for value in result.split(b"\0") if value]
    if len(records) != 1:
        raise ReleaseRehearsalError(
            (rehearsal_issue("RELEASE_NOTES_NOT_COMMITTED", "notes", "path is not one committed file"),)
        )
    metadata, path = records[0].split(b"\t", 1)
    mode, object_type, _ = metadata.decode("ascii").split()
    if os.fsdecode(path) != notes_relative or object_type != "blob" or mode not in {"100644", "100755"}:
        raise ReleaseRehearsalError(
            (rehearsal_issue("RELEASE_NOTES_NOT_REGULAR", "notes", "committed path is not a regular file"),)
        )
    return _git(repository, environment, "show", f"{source_commit}:{notes_relative}").stdout


def _verify_checkout_tree(checkout: Path, environment: Mapping[str, str], source_commit: str) -> None:
    issues: list[RehearsalIssue] = []
    output = _git(checkout, environment, "ls-tree", "-rz", "--full-tree", source_commit).stdout
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        relative = os.fsdecode(encoded_path)
        path = checkout / relative
        if object_type != "blob" or mode not in {"100644", "100755", "120000"}:
            issues.append(rehearsal_issue("UNSUPPORTED_SOURCE_ENTRY", relative, f"{mode} {object_type}"))
            continue
        try:
            path_status = path.lstat()
        except FileNotFoundError:
            issues.append(rehearsal_issue("TEMP_CHECKOUT_CONTENT_MISMATCH", relative, "path is absent"))
            continue
        if mode == "120000":
            if not stat.S_ISLNK(path_status.st_mode):
                issues.append(rehearsal_issue("TEMP_CHECKOUT_CONTENT_MISMATCH", relative, "expected symlink"))
                continue
            content = os.fsencode(os.readlink(path))
            actual_id = _git(checkout, environment, "hash-object", "--stdin", input_bytes=content).stdout.decode("ascii").strip()
        else:
            if not stat.S_ISREG(path_status.st_mode):
                issues.append(rehearsal_issue("TEMP_CHECKOUT_CONTENT_MISMATCH", relative, "expected regular file"))
                continue
            actual_id = _git_text(checkout, environment, "hash-object", "--no-filters", "--", relative)
            expected_mode = 0o755 if mode == "100755" else 0o644
            if stat.S_IMODE(path_status.st_mode) != expected_mode:
                issues.append(rehearsal_issue("TEMP_CHECKOUT_MODE_MISMATCH", relative, f"expected {expected_mode:o}"))
        if actual_id != object_id:
            issues.append(rehearsal_issue("TEMP_CHECKOUT_CONTENT_MISMATCH", relative, "blob identity differs"))
    if issues:
        raise ReleaseRehearsalError(issues)


def _checkout_clean_issues(checkout: Path, environment: Mapping[str, str], source_commit: str) -> tuple[RehearsalIssue, ...]:
    issues: list[RehearsalIssue] = []
    head = _git_text(checkout, environment, "rev-parse", "HEAD")
    if head != source_commit:
        issues.append(rehearsal_issue("TEMP_CHECKOUT_HEAD_MISMATCH", "source_commit", f"HEAD is {head}"))
    symbolic = _git(checkout, environment, "symbolic-ref", "-q", "HEAD", check=False)
    if symbolic.returncode == 0:
        issues.append(rehearsal_issue("TEMP_CHECKOUT_NOT_DETACHED", "checkout", "HEAD is symbolic"))
    status_value = _git(
        checkout,
        environment,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
    ).stdout
    if status_value:
        issues.append(rehearsal_issue("TEMP_CHECKOUT_DIRTY", "checkout", "tracked, untracked, or ignored residue exists"))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _candidate_environment(candidate_root: Path, guard_directory: Path) -> dict[str, str]:
    environment = _sanitized_environment(candidate_root / "home")
    temporary = candidate_root / "tmp"
    temporary.mkdir(exist_ok=True)
    blocked_proxy = "http://127.0.0.1:9"
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": str(guard_directory),
            "SOURCE_DATE_EPOCH": "0",
            "TMPDIR": str(temporary),
            "HTTP_PROXY": blocked_proxy,
            "HTTPS_PROXY": blocked_proxy,
            "FTP_PROXY": blocked_proxy,
            "ALL_PROXY": blocked_proxy,
            "NO_PROXY": "",
            "http_proxy": blocked_proxy,
            "https_proxy": blocked_proxy,
            "ftp_proxy": blocked_proxy,
            "all_proxy": blocked_proxy,
            "no_proxy": "",
        }
    )
    return environment


def _phase_command(
    code: str,
    field: str,
    command: list[str],
    *,
    checkout: Path,
    environment: Mapping[str, str],
) -> None:
    completed = _run(command, cwd=checkout, environment=environment, check=False)
    if completed.returncode == 0:
        return
    output = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
    nested = [line for line in output.splitlines() if line.startswith("ERROR [")]
    detail = nested[0] if nested else f"command exited {completed.returncode}"
    raise ReleaseRehearsalError((rehearsal_issue(code, field, detail),))


def _candidate_integrity_issues(
    checkout: Path,
    environment: Mapping[str, str],
    source_commit: str,
) -> tuple[RehearsalIssue, ...]:
    """Return exact checkout-state and commit-tree diagnostics after a phase."""

    issues = list(_checkout_clean_issues(checkout, environment, source_commit))
    try:
        _verify_checkout_tree(checkout, environment, source_commit)
    except ReleaseRehearsalError as exc:
        issues.extend(
            rehearsal_issue("TEMP_CHECKOUT_MUTATED", issue.field, issue.message)
            for issue in exc.issues
        )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _run_candidate_phase(
    code: str,
    field: str,
    command: list[str],
    *,
    checkout: Path,
    phase_environment: Mapping[str, str],
    git_environment: Mapping[str, str],
    source_commit: str,
) -> None:
    """Run one phase and prove the candidate remained an exact clean checkout."""

    primary: ReleaseRehearsalError | None = None
    try:
        _phase_command(code, field, command, checkout=checkout, environment=phase_environment)
    except ReleaseRehearsalError as exc:
        primary = exc
    integrity = _candidate_integrity_issues(checkout, git_environment, source_commit)
    if primary is not None or integrity:
        raise ReleaseRehearsalError((*(primary.issues if primary is not None else ()), *integrity))


def _build_candidate(
    candidate_root: Path,
    invoking_repository: Path,
    source_commit: str,
    release_identifier: str,
    release_date: str,
    git_tag: str,
    notes_relative: str,
    expected_notes: bytes,
    guard_directory: Path,
) -> CandidateResult:
    checkout = candidate_root / "checkout"
    git_environment = _sanitized_environment(candidate_root / "git-home")
    clone = [
        "git",
        *GIT_BASE_ARGUMENTS,
        "clone",
        "--local",
        "--no-hardlinks",
        "--no-checkout",
        "--no-tags",
        "--no-recurse-submodules",
        str(invoking_repository),
        str(checkout),
    ]
    try:
        _run(clone, cwd=candidate_root, environment=git_environment)
    except Exception as exc:
        raise ReleaseRehearsalError(
            (rehearsal_issue("TEMP_CHECKOUT_CREATION_FAILED", "checkout", str(exc)),)
        ) from exc
    _git(checkout, git_environment, "remote", "remove", "origin")
    _git(checkout, git_environment, "checkout", "--detach", "--force", source_commit)
    if _git_text(checkout, git_environment, "cat-file", "-t", source_commit) != "commit":
        raise ReleaseRehearsalError(
            (rehearsal_issue("SOURCE_OBJECT_NOT_COMMIT", "source_commit", "candidate object is not a commit"),)
        )
    initial_integrity = _candidate_integrity_issues(checkout, git_environment, source_commit)
    if initial_integrity:
        raise ReleaseRehearsalError(initial_integrity)
    notes_path = checkout / notes_relative
    if notes_path.is_symlink() or not notes_path.is_file() or notes_path.read_bytes() != expected_notes:
        raise ReleaseRehearsalError(
            (rehearsal_issue("RELEASE_NOTES_IDENTITY_MISMATCH", "notes", "candidate notes differ from commit"),)
        )

    package_parent = candidate_root / "package"
    artifact_parent = candidate_root / "artifacts"
    package_parent.mkdir()
    artifact_parent.mkdir()
    package = package_parent / release_identifier
    archive = artifact_parent / archive_filename(release_identifier)
    sidecar = artifact_parent / sidecar_filename(release_identifier)
    environment = _candidate_environment(candidate_root, guard_directory)
    python = sys.executable
    common = [
        "--release-id", release_identifier,
        "--release-date", release_date,
        "--source-commit", source_commit,
        "--git-tag", git_tag,
    ]
    _run_candidate_phase(
        "PACKAGE_BUILD_FAILED",
        "package",
        [python, "-B", "tools/build_release.py", *common, "--notes", notes_relative, "--output-dir", str(package)],
        checkout=checkout,
        phase_environment=environment,
        git_environment=git_environment,
        source_commit=source_commit,
    )
    _run_candidate_phase(
        "PACKAGE_VALIDATION_FAILED",
        "package",
        [python, "-B", "tools/check_release.py", "validate", "--package-dir", str(package)],
        checkout=checkout,
        phase_environment=environment,
        git_environment=git_environment,
        source_commit=source_commit,
    )
    manifest = load_and_validate_release_manifest(package / "manifest.json")
    if manifest.source_commit != source_commit:
        raise ReleaseRehearsalError(
            (rehearsal_issue("SOURCE_EVIDENCE_MISMATCH", "manifest.source_commit", "manifest differs from requested commit"),)
        )
    archive_common = [
        "--package-dir", str(package),
        "--release-id", release_identifier,
        "--source-commit", source_commit,
    ]
    _run_candidate_phase(
        "ARCHIVE_BUILD_FAILED",
        "archive",
        [
            python,
            "-B",
            "tools/release_archive.py",
            "build-candidate",
            *archive_common,
            "--candidate-dir",
            str(artifact_parent),
        ],
        checkout=checkout,
        phase_environment=environment,
        git_environment=git_environment,
        source_commit=source_commit,
    )
    _run_candidate_phase(
        "ARCHIVE_VALIDATION_FAILED",
        "archive",
        [
            python,
            "-B",
            "tools/release_archive.py",
            "validate",
            *archive_common,
            "--archive",
            str(archive),
            "--sidecar",
            str(sidecar),
        ],
        checkout=checkout,
        phase_environment=environment,
        git_environment=git_environment,
        source_commit=source_commit,
    )
    return CandidateResult(
        checkout=checkout,
        environment=environment,
        package_dir=package,
        archive_path=archive,
        sidecar_path=sidecar,
        manifest=manifest,
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    )


def _output_path_issues(
    output_dir: Path,
    repository: Path,
    *,
    ignored_staging: Path | None = None,
) -> tuple[RehearsalIssue, ...]:
    issues: list[RehearsalIssue] = []
    if not output_dir.is_absolute():
        issues.append(rehearsal_issue("OUTPUT_PATH", "output_dir", "expected absolute path"))
        return tuple(issues)
    if os.path.lexists(output_dir):
        issues.append(rehearsal_issue("OUTPUT_EXISTS", "output_dir", "destination already exists"))
    parent = output_dir.parent
    if not parent.is_dir():
        issues.append(rehearsal_issue("OUTPUT_PARENT", "output_dir", "real parent directory is absent"))
        return tuple(issues)
    current = Path(parent.anchor)
    for component in parent.parts[1:]:
        current = current / component
        if current.is_symlink():
            issues.append(rehearsal_issue("OUTPUT_SYMLINK", "output_dir", "parent path contains a symlink"))
            break
    if parent.resolve() != parent:
        issues.append(rehearsal_issue("OUTPUT_PATH", "output_dir", "parent must be canonical"))
    candidate = parent / output_dir.name
    try:
        candidate.relative_to(repository)
    except ValueError:
        pass
    else:
        issues.append(rehearsal_issue("OUTPUT_INSIDE_REPOSITORY", "output_dir", "destination must be external"))
    try:
        for sibling in parent.iterdir():
            if sibling == ignored_staging:
                continue
            if sibling.name.startswith(".release-rehearsal-output-"):
                issues.append(
                    rehearsal_issue("OUTPUT_EXISTS", "output_dir", "unrelated rehearsal staging sibling exists")
                )
                break
    except OSError as exc:
        issues.append(rehearsal_issue("OUTPUT_PARENT", "output_dir", str(exc)))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _temporary_parent_outside_repository(repository: Path) -> Path:
    repository = repository.resolve()
    for candidate in (Path("/tmp"),):
        try:
            resolved = candidate.resolve()
            resolved.relative_to(repository)
        except ValueError:
            if resolved.is_dir() and not resolved.is_symlink():
                return resolved
        except OSError:
            continue
    try:
        fallback = Path(tempfile.gettempdir()).resolve()
        fallback.relative_to(repository)
    except ValueError:
        if fallback.is_dir() and not fallback.is_symlink():
            return fallback
    except OSError:
        pass
    raise ReleaseRehearsalError(
        (rehearsal_issue("TEMPORARY_ROOT", "repository", "no real temporary parent exists outside the repository"),)
    )


def _staged_output_path_issues(result: Path, release_identifier: str) -> tuple[RehearsalIssue, ...]:
    package_prefix = f"releases/{release_identifier}"
    expected = {
        "releases",
        package_prefix,
        *(f"{package_prefix}/{directory}" for directory in EXPECTED_DIRECTORIES),
        *(f"{package_prefix}/{path}" for path in PACKAGE_FILE_PATHS),
        archive_filename(release_identifier),
        sidecar_filename(release_identifier),
    }
    observed: set[str] = set()
    issues: list[RehearsalIssue] = []
    for path in result.rglob("*"):
        relative = path.relative_to(result).as_posix()
        observed.add(relative)
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            issues.append(rehearsal_issue("STAGED_OUTPUT_PATH_SET", relative, "staged path is not a real regular file or directory"))
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        issues.append(
            rehearsal_issue("STAGED_OUTPUT_PATH_SET", "output_dir", f"missing={missing!r}; extra={extra!r}")
        )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _copy_candidate_output(candidate: CandidateResult, result: Path, release_identifier: str) -> None:
    releases = result / "releases"
    releases.mkdir()
    shutil.copytree(candidate.package_dir, releases / release_identifier)
    (result / candidate.archive_path.name).write_bytes(candidate.archive_path.read_bytes())
    (result / candidate.sidecar_path.name).write_bytes(candidate.sidecar_path.read_bytes())


def _validate_staged_output(
    candidate: CandidateResult,
    result: Path,
    release_identifier: str,
    source_commit: str,
) -> None:
    issues = _staged_output_path_issues(result, release_identifier)
    if issues:
        raise ReleaseRehearsalError(issues)
    staged_package = result / "releases" / release_identifier
    staged_archive = result / archive_filename(release_identifier)
    staged_sidecar = result / sidecar_filename(release_identifier)
    _phase_command(
        "STAGED_PACKAGE_VALIDATION_FAILED",
        "output_dir",
        [sys.executable, "-B", "tools/check_release.py", "validate", "--package-dir", str(staged_package)],
        checkout=candidate.checkout,
        environment=candidate.environment,
    )
    _phase_command(
        "STAGED_ARCHIVE_VALIDATION_FAILED",
        "output_dir",
        [
            sys.executable,
            "-B",
            "tools/release_archive.py",
            "validate",
            "--package-dir",
            str(staged_package),
            "--archive",
            str(staged_archive),
            "--sidecar",
            str(staged_sidecar),
            "--release-id",
            release_identifier,
            "--source-commit",
            source_commit,
        ],
        checkout=candidate.checkout,
        environment=candidate.environment,
    )
    try:
        manifest = load_and_validate_release_manifest(staged_package / "manifest.json")
    except Exception as exc:
        raise ReleaseRehearsalError(
            (rehearsal_issue("STAGED_PACKAGE_VALIDATION_FAILED", "manifest.json", str(exc)),)
        ) from exc
    if manifest.source_commit != source_commit:
        raise ReleaseRehearsalError(
            (rehearsal_issue("SOURCE_EVIDENCE_MISMATCH", "manifest.source_commit", "staged manifest differs from requested commit"),)
        )
    package_issues = compare_complete_packages(candidate.package_dir, staged_package)
    if package_issues:
        raise ReleaseRehearsalError(
            tuple(
                rehearsal_issue("STAGED_PACKAGE_CONTENT_MISMATCH", issue.field, issue.message)
                for issue in package_issues
            )
        )
    staged_archive_bytes = staged_archive.read_bytes()
    if staged_archive_bytes != candidate.archive_path.read_bytes():
        raise ReleaseRehearsalError(
            (rehearsal_issue("STAGED_ARCHIVE_CONTENT_MISMATCH", "archive", "staged archive differs from candidate A"),)
        )
    if hashlib.sha256(staged_archive_bytes).hexdigest() != candidate.archive_sha256:
        raise ReleaseRehearsalError(
            (rehearsal_issue("STAGED_ARCHIVE_CHECKSUM_MISMATCH", "archive", "staged archive hash differs from candidate A"),)
        )
    if staged_sidecar.read_bytes() != candidate.sidecar_path.read_bytes():
        raise ReleaseRehearsalError(
            (rehearsal_issue("STAGED_SIDECAR_CONTENT_MISMATCH", "sidecar", "staged sidecar differs from candidate A"),)
        )


def _stage_output(
    candidate: CandidateResult,
    output_dir: Path,
    release_identifier: str,
    source_commit: str,
) -> OwnedDirectory:
    """Create one validated output directory that is itself the rename source."""

    try:
        staging_path = Path(tempfile.mkdtemp(prefix=".release-rehearsal-output-", dir=output_dir.parent))
        staging = _capture_owned_directory(staging_path, "output_staging")
    except OSError as exc:
        raise ReleaseRehearsalError(
            (rehearsal_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", f"unable to create output staging directory: {exc}"),)
        ) from exc
    primary: ReleaseRehearsalError | None = None
    try:
        _copy_candidate_output(candidate, staging.path, release_identifier)
        _validate_staged_output(candidate, staging.path, release_identifier, source_commit)
    except ReleaseRehearsalError as exc:
        primary = exc
    except Exception as exc:
        primary = ReleaseRehearsalError(
            (rehearsal_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", str(exc)),)
        )
    if primary is not None:
        cleanup = _cleanup_staged_wrapper(staging)
        raise ReleaseRehearsalError((*primary.issues, *cleanup))
    return staging


def _cleanup_staged_wrapper(wrapper: OwnedDirectory | None) -> tuple[RehearsalIssue, ...]:
    return _cleanup_owned_path(wrapper, "output_staging")


def _capture_owned_directory(path: Path, field: str) -> OwnedDirectory:
    """Capture the lstat identity of a newly created cleanup-owned directory."""

    try:
        status = os.lstat(path)
    except OSError as exc:
        raise ReleaseRehearsalError((rehearsal_issue("CLEANUP_FAILED", field, str(exc)),)) from exc
    file_type = stat.S_IFMT(status.st_mode)
    if file_type != stat.S_IFDIR:
        raise ReleaseRehearsalError(
            (rehearsal_issue("CLEANUP_FAILED", field, "created path is not a real directory"),)
        )
    return OwnedDirectory(path=path, st_dev=status.st_dev, st_ino=status.st_ino, file_type=file_type)


def _owned_directory_matches(owned: OwnedDirectory, path: Path | None = None) -> bool:
    try:
        status = os.lstat(owned.path if path is None else path)
    except OSError:
        return False
    return (
        status.st_dev == owned.st_dev
        and status.st_ino == owned.st_ino
        and stat.S_IFMT(status.st_mode) == owned.file_type
    )


def _cleanup_owned_path(owned: OwnedDirectory | None, field: str) -> tuple[RehearsalIssue, ...]:
    """Remove only an identity-matched real directory; never follow replacements."""

    if owned is None:
        return ()
    try:
        status = os.lstat(owned.path)
    except FileNotFoundError:
        return (rehearsal_issue("CLEANUP_FAILED", field, "owned directory path is missing"),)
    except OSError as exc:
        return (rehearsal_issue("CLEANUP_FAILED", field, str(exc)),)
    if (
        status.st_dev != owned.st_dev
        or status.st_ino != owned.st_ino
        or stat.S_IFMT(status.st_mode) != owned.file_type
        or not stat.S_ISDIR(status.st_mode)
    ):
        return (rehearsal_issue("CLEANUP_FAILED", field, "path no longer identifies the owned directory"),)
    if not shutil.rmtree.avoids_symlink_attacks:
        return (rehearsal_issue("CLEANUP_FAILED", field, "platform cannot safely remove an owned directory"),)
    try:
        shutil.rmtree(owned.path)
    except OSError as exc:
        return (rehearsal_issue("CLEANUP_FAILED", field, str(exc)),)
    if os.path.lexists(owned.path):
        return (rehearsal_issue("CLEANUP_FAILED", field, "owned directory remains"),)
    return ()


def _merge_rehearsal_failure(
    primary: ReleaseRehearsalError | None,
    issues: Iterable[RehearsalIssue],
) -> ReleaseRehearsalError | None:
    values = tuple(issues)
    if primary is None:
        return ReleaseRehearsalError(values) if values else None
    return ReleaseRehearsalError((*primary.issues, *values))


def rehearse_release(
    command: str,
    release_identifier: str,
    release_date: str,
    git_tag: str,
    source_commit: str,
    notes_relative: str,
    *,
    output_dir: Path | None = None,
    repository_root: Path = REPO_ROOT,
) -> RehearsalResult:
    context = parse_formal_release_context(release_identifier, release_date, git_tag, source_commit)
    repository = Path(repository_root).resolve()
    if command not in {"verify", "build"}:
        raise ReleaseRehearsalError((rehearsal_issue("REHEARSAL_COMMAND", "command", "expected verify or build"),))
    if command == "build":
        if output_dir is None:
            raise ReleaseRehearsalError((rehearsal_issue("OUTPUT_REQUIRED", "output_dir", "build requires output"),))
        output_dir = Path(output_dir)
        output_issues = _output_path_issues(output_dir, repository)
        if output_issues:
            raise ReleaseRehearsalError(output_issues)
    elif output_dir is not None:
        raise ReleaseRehearsalError((rehearsal_issue("OUTPUT_PROHIBITED", "output_dir", "verify retains no output"),))

    staged_output: OwnedDirectory | None = None
    git_home_directory: OwnedDirectory | None = None
    temporary: OwnedDirectory | None = None
    first_root: OwnedDirectory | None = None
    second_root: OwnedDirectory | None = None
    invocation_environment: Mapping[str, str] | None = None
    before: RepositorySnapshot | None = None
    failure: ReleaseRehearsalError | None = None
    result: RehearsalResult | None = None
    temporary_parent = _temporary_parent_outside_repository(repository)

    try:
        try:
            git_home_path = Path(tempfile.mkdtemp(prefix="release-rehearsal-git-", dir=temporary_parent))
            git_home_directory = _capture_owned_directory(git_home_path, "git_home")
        except OSError as exc:
            raise ReleaseRehearsalError(
                (rehearsal_issue("TEMP_CHECKOUT_CREATION_FAILED", "git_home", str(exc)),)
            ) from exc
        invocation_environment = _sanitized_environment(git_home_directory.path / "home")
        try:
            top = Path(_git_text(repository, invocation_environment, "rev-parse", "--show-toplevel")).resolve()
        except Exception as exc:
            raise ReleaseRehearsalError(
                (rehearsal_issue("NOT_GIT_WORKTREE", "repository", str(exc)),)
            ) from exc
        if top != repository:
            raise ReleaseRehearsalError(
                (rehearsal_issue("NOT_REPOSITORY_ROOT", "repository", "script root differs from Git top-level"),)
            )
        _validate_source_commit(repository, invocation_environment, context.source_commit)
        initial_status = _git(
            repository,
            invocation_environment,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ).stdout
        if initial_status:
            raise ReleaseRehearsalError(
                (rehearsal_issue("DIRTY_INVOKING_CHECKOUT", "repository", "staged, tracked, or untracked changes exist"),)
            )
        before = snapshot_repository(repository, invocation_environment)
        expected_notes = _validate_notes_identity(
            repository,
            invocation_environment,
            context.source_commit,
            notes_relative,
        )
        try:
            temporary_path = Path(tempfile.mkdtemp(prefix="release-rehearsal-", dir=temporary_parent))
            temporary = _capture_owned_directory(temporary_path, "candidate_root")
        except OSError as exc:
            raise ReleaseRehearsalError(
                (rehearsal_issue("TEMP_CHECKOUT_CREATION_FAILED", "candidate_root", str(exc)),)
            ) from exc
        guard = temporary.path / "offline-python"
        guard.mkdir()
        (guard / "sitecustomize.py").write_text(SITE_CUSTOMIZE, encoding="utf-8")
        first_root_path = temporary.path / "candidate-a"
        second_root_path = temporary.path / "candidate-b"
        first_root_path.mkdir()
        second_root_path.mkdir()
        first_root = _capture_owned_directory(first_root_path, "candidate_a")
        second_root = _capture_owned_directory(second_root_path, "candidate_b")
        if command == "build":
            assert output_dir is not None
            for candidate_root in (first_root, second_root):
                try:
                    output_dir.resolve(strict=False).relative_to(candidate_root.path.resolve())
                except ValueError:
                    continue
                raise ReleaseRehearsalError(
                    (rehearsal_issue("OUTPUT_INSIDE_CANDIDATE", "output_dir", "destination overlaps a candidate root"),)
                )
        first = _build_candidate(
            first_root.path,
            repository,
            context.source_commit,
            context.release_identifier,
            context.release_date,
            context.git_tag,
            notes_relative,
            expected_notes,
            guard,
        )
        second = _build_candidate(
            second_root.path,
            repository,
            context.source_commit,
            context.release_identifier,
            context.release_date,
            context.git_tag,
            notes_relative,
            expected_notes,
            guard,
        )
        package_issues = compare_complete_packages(first.package_dir, second.package_dir)
        if package_issues:
            raise ReleaseRehearsalError(
                tuple(rehearsal_issue(value.code, value.field, value.message) for value in package_issues)
            )
        if first.manifest != second.manifest:
            raise ReleaseRehearsalError(
                (rehearsal_issue("NONDETERMINISTIC_PACKAGE_REBUILD", "manifest", "parsed models differ"),)
            )
        if first.archive_path.read_bytes() != second.archive_path.read_bytes() or first.sidecar_path.read_bytes() != second.sidecar_path.read_bytes():
            raise ReleaseRehearsalError(
                (rehearsal_issue("NONDETERMINISTIC_ARCHIVE_REBUILD", "archive", "candidate bytes differ"),)
            )
        if first.archive_sha256 != second.archive_sha256:
            raise ReleaseRehearsalError(
                (rehearsal_issue("NONDETERMINISTIC_ARCHIVE_REBUILD", "archive_sha256", "hashes differ"),)
            )
        if command == "build":
            assert output_dir is not None
            staged_output = _stage_output(
                first,
                output_dir,
                release_identifier,
                context.source_commit,
            )
        result = RehearsalResult(
            release_identifier=release_identifier,
            source_commit=source_commit,
            archive_sha256=first.archive_sha256,
            output_dir=output_dir,
            package_file_count=len(PACKAGE_FILE_PATHS),
            archive_member_count=len(canonical_member_names(release_identifier)),
        )
    except ReleaseRehearsalError as exc:
        failure = exc
    except Exception as exc:
        failure = ReleaseRehearsalError(
            (rehearsal_issue("PACKAGE_BUILD_FAILED", "rehearsal", str(exc)),)
        )

    # Source nonmutation is checked before any possible destination publication.
    if before is not None and invocation_environment is not None:
        failure = _merge_rehearsal_failure(
            failure,
            repository_snapshot_issues(repository, invocation_environment, before),
        )

    # Candidate roots are always removed before an external output can exist.
    # If a child path was replaced, leave its parent in place rather than let a
    # recursive parent cleanup remove an object whose identity we refused.
    candidate_cleanup = (
        *_cleanup_owned_path(first_root, "candidate_a"),
        *_cleanup_owned_path(second_root, "candidate_b"),
    )
    if not candidate_cleanup or all(
        owned is None or not os.path.lexists(owned.path)
        for owned in (first_root, second_root)
    ):
        candidate_cleanup = (*candidate_cleanup, *_cleanup_owned_path(temporary, "candidate_root"))
    failure = _merge_rehearsal_failure(failure, candidate_cleanup)

    # This is the final invoking-checkout observation and still has its owned
    # Git environment available.  Nothing after publication consults or cleans
    # the published output pathname.
    if failure is None and before is not None and invocation_environment is not None:
        failure = _merge_rehearsal_failure(
            failure,
            repository_snapshot_issues(repository, invocation_environment, before),
        )

    failure = _merge_rehearsal_failure(failure, _cleanup_owned_path(git_home_directory, "git_home"))

    if failure is None and command == "build":
        assert output_dir is not None and staged_output is not None
        late_output_issues = _output_path_issues(
            output_dir,
            repository,
            ignored_staging=staged_output.path,
        )
        if late_output_issues:
            failure = ReleaseRehearsalError(late_output_issues)
        else:
            try:
                atomic_rename_noreplace(staged_output.path, output_dir)
            except FileExistsError:
                failure = ReleaseRehearsalError(
                    (rehearsal_issue("OUTPUT_EXISTS", "output_dir", "destination appeared before publication"),)
                )
            except AtomicNoReplaceUnsupportedError as exc:
                failure = ReleaseRehearsalError(
                    (rehearsal_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", str(exc)),)
                )
            except OSError as exc:
                failure = ReleaseRehearsalError(
                    (rehearsal_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", str(exc)),)
                )
            except Exception as exc:
                failure = ReleaseRehearsalError(
                    (rehearsal_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", str(exc)),)
                )
            else:
                # The inode moved to an external name.  The final no-replace
                # rename is the last mutation and the output is never cleanup-owned.
                staged_output = None

    # A wrapper around the platform syscall can raise after a successful rename.
    # Relinquish ownership only if the destination still identifies our inode;
    # otherwise preserve the replacement and report the unsafe missing staging.
    if failure is not None and staged_output is not None and not os.path.lexists(staged_output.path):
        if output_dir is not None and _owned_directory_matches(staged_output, output_dir):
            staged_output = None

    failure = _merge_rehearsal_failure(failure, _cleanup_staged_wrapper(staged_output))

    if failure is not None:
        raise failure
    assert result is not None
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "build"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--release-id", required=True)
        subparser.add_argument("--release-date", required=True)
        subparser.add_argument("--git-tag", required=True)
        subparser.add_argument("--source-commit", required=True)
        subparser.add_argument("--notes", required=True)
        if name == "build":
            subparser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = rehearse_release(
            args.command,
            args.release_id,
            args.release_date,
            args.git_tag,
            args.source_commit,
            args.notes,
            output_dir=getattr(args, "output_dir", None),
        )
    except Exception as exc:
        print(str(exc))
        return 1
    print("Release rehearsal: PASS")
    print(f"Release identifier: {result.release_identifier}")
    print(f"Source commit: {result.source_commit}")
    print(f"Package files: {result.package_file_count}")
    print(f"Archive members: {result.archive_member_count}")
    print(f"Archive SHA-256: {result.archive_sha256}")
    print(f"Output retained: {'yes' if result.output_dir is not None else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
