#!/usr/bin/env python3
"""Build and validate the canonical uncompressed release-package USTAR archive."""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import os
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import urlsplit

from build_release import PACKAGE_FILE_PATHS
from check_release import EXPECTED_DIRECTORIES, validate_release_package
from release_context import SOURCE_COMMIT_PATTERN, validate_release_identifier
from release_manifest import load_and_validate_release_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PREFIX = "SSN2BFO-"
DIRECTORY_MODE = 0o755
FILE_MODE = 0o644
CANONICAL_MTIME = 0
USTAR_RECORD_SIZE = 512
USTAR_MAGIC = b"ustar\0"
USTAR_VERSION = b"00"
USTAR_EOF = b"\0" * (USTAR_RECORD_SIZE * 2)
AT_FDCWD = -100
RENAME_NOREPLACE = 1
RENAME_EXCL = 0x00000004

# This is intentionally independent from package traversal and lexical sorting.
ARCHIVE_MEMBER_TEMPLATES = (
    "SSN2BFO-{release_id}/",
    "SSN2BFO-{release_id}/LICENSE",
    "SSN2BFO-{release_id}/RELEASE-NOTES.md",
    "SSN2BFO-{release_id}/SHA256SUMS",
    "SSN2BFO-{release_id}/SSN2BFO.ttl",
    "SSN2BFO-{release_id}/catalog-v001.xml",
    "SSN2BFO-{release_id}/manifest.json",
    "SSN2BFO-{release_id}/current-ssn-sosa/",
    "SSN2BFO-{release_id}/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    "SSN2BFO-{release_id}/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    "SSN2BFO-{release_id}/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
    "SSN2BFO-{release_id}/evidence/",
    "SSN2BFO-{release_id}/evidence/coms-product-dispositions.json",
    "SSN2BFO-{release_id}/sources/",
    "SSN2BFO-{release_id}/sources/SSN2BFO-COMS.xlsx",
    "SSN2BFO-{release_id}/sources/publication-metadata.toml",
)


@dataclass(frozen=True)
class ReleaseArchiveIssue:
    code: str
    field: str
    message: str

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return self.field, self.code, self.message


@dataclass(frozen=True)
class ReleaseArchiveResult:
    archive_path: Path
    sidecar_path: Path
    archive_sha256: str
    member_names: tuple[str, ...]


@dataclass(frozen=True)
class _RawArchiveMember:
    name: str
    content: bytes
    is_directory: bool


@dataclass(frozen=True)
class _OwnedDirectory:
    """A directory created by this process and safe to remove only by identity."""

    path: Path
    st_dev: int
    st_ino: int
    file_type: int


class ReleaseArchiveError(ValueError):
    """One or more deterministic archive construction or validation failures."""

    def __init__(self, issues: Iterable[ReleaseArchiveIssue]):
        self.issues = tuple(sorted(set(issues), key=lambda value: value.sort_key))
        super().__init__("; ".join(format_issue(issue) for issue in self.issues))


class AtomicNoReplaceUnsupportedError(OSError):
    """The host cannot provide the required no-replace rename primitive."""


def format_issue(issue: ReleaseArchiveIssue) -> str:
    return f"ERROR [{issue.code}] {issue.field}: {issue.message}"


def archive_issue(code: str, field: str, message: str) -> ReleaseArchiveIssue:
    return ReleaseArchiveIssue(code, field, message)


def archive_filename(release_identifier: str) -> str:
    return f"{ARCHIVE_PREFIX}{validate_release_identifier(release_identifier)}.tar"


def sidecar_filename(release_identifier: str) -> str:
    return archive_filename(release_identifier) + ".sha256"


def archive_top_level(release_identifier: str) -> str:
    return f"{ARCHIVE_PREFIX}{validate_release_identifier(release_identifier)}"


def canonical_member_names(release_identifier: str) -> tuple[str, ...]:
    release_id = validate_release_identifier(release_identifier)
    return tuple(template.format(release_id=release_id) for template in ARCHIVE_MEMBER_TEMPLATES)


def canonical_directory_names(release_identifier: str) -> frozenset[str]:
    return frozenset(name for name in canonical_member_names(release_identifier) if name.endswith("/"))


def canonical_sidecar_bytes(release_identifier: str, archive_bytes: bytes) -> bytes:
    digest = hashlib.sha256(archive_bytes).hexdigest()
    return f"{digest}  {archive_filename(release_identifier)}\n".encode("ascii")


def _package_layout_issues(package_dir: Path) -> tuple[ReleaseArchiveIssue, ...]:
    issues: list[ReleaseArchiveIssue] = []
    if not package_dir.is_dir() or package_dir.is_symlink():
        return (archive_issue("PACKAGE_DIRECTORY", "package_dir", "expected real directory"),)
    files: list[str] = []
    directories: list[str] = []
    for path in sorted(package_dir.rglob("*"), key=lambda value: value.relative_to(package_dir).as_posix()):
        relative = path.relative_to(package_dir).as_posix()
        if path.is_symlink():
            issues.append(archive_issue("PACKAGE_SYMLINK", relative, "symlinks are prohibited"))
        elif path.is_dir():
            directories.append(relative)
        elif path.is_file():
            files.append(relative)
        else:
            issues.append(archive_issue("PACKAGE_SPECIAL_FILE", relative, "unsupported filesystem entry"))
    if tuple(files) != PACKAGE_FILE_PATHS:
        issues.append(archive_issue("PACKAGE_FILE_SET", "package", "regular-file inventory differs"))
    if tuple(directories) != EXPECTED_DIRECTORIES:
        issues.append(archive_issue("PACKAGE_DIRECTORY_SET", "package", "directory inventory differs"))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _archive_layout_authority_issues(release_identifier: str) -> tuple[ReleaseArchiveIssue, ...]:
    top = archive_top_level(release_identifier)
    members = canonical_member_names(release_identifier)
    files = tuple(name[len(top) + 1 :] for name in members if not name.endswith("/"))
    directories = tuple(name[len(top) + 1 : -1] for name in members if name.endswith("/") and name != top + "/")
    issues: list[ReleaseArchiveIssue] = []
    if frozenset(files) != frozenset(PACKAGE_FILE_PATHS) or len(files) != len(PACKAGE_FILE_PATHS):
        issues.append(archive_issue("ARCHIVE_LAYOUT_AUTHORITY", "archive", "file authority differs from package authority"))
    if directories != EXPECTED_DIRECTORIES:
        issues.append(archive_issue("ARCHIVE_LAYOUT_AUTHORITY", "archive", "directory authority differs from package authority"))
    expected_member_count = (
        1
        + len(EXPECTED_DIRECTORIES)
        + len(PACKAGE_FILE_PATHS)
    )
    if (
        len(members) != expected_member_count
        or len(set(members)) != expected_member_count
    ):
        issues.append(
            archive_issue(
                "ARCHIVE_LAYOUT_AUTHORITY",
                "archive",
                f"expected exactly {expected_member_count} unique members",
            )
        )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _octal_field(value: int, width: int) -> bytes:
    if value < 0 or value >= 8 ** (width - 1):
        raise ValueError(f"value {value} does not fit {width}-byte octal field")
    return f"{value:0{width - 1}o}".encode("ascii") + b"\0"


def _checksum_field(value: int) -> bytes:
    if value < 0 or value >= 8**6:
        raise ValueError(f"checksum {value} does not fit canonical field")
    return f"{value:06o}".encode("ascii") + b"\0 "


def _canonical_header(name: str, *, is_directory: bool, size: int) -> bytes:
    encoded_name = name.encode("ascii")
    if len(encoded_name) > 100:
        raise ReleaseArchiveError((archive_issue("ARCHIVE_NAME_OVERFLOW", name, "USTAR name field exceeds 100 bytes"),))
    if is_directory:
        if not name.endswith("/") or size != 0:
            raise ReleaseArchiveError((archive_issue("ARCHIVE_METADATA_MISMATCH", name, "invalid directory metadata"),))
        mode = DIRECTORY_MODE
        type_flag = b"5"
    else:
        if name.endswith("/"):
            raise ReleaseArchiveError((archive_issue("ARCHIVE_METADATA_MISMATCH", name, "regular file name ends with slash"),))
        mode = FILE_MODE
        type_flag = b"0"

    header = bytearray(USTAR_RECORD_SIZE)
    header[0 : len(encoded_name)] = encoded_name
    header[100:108] = _octal_field(mode, 8)
    header[108:116] = _octal_field(0, 8)
    header[116:124] = _octal_field(0, 8)
    header[124:136] = _octal_field(size, 12)
    header[136:148] = _octal_field(CANONICAL_MTIME, 12)
    header[148:156] = b" " * 8
    header[156:157] = type_flag
    header[257:263] = USTAR_MAGIC
    header[263:265] = USTAR_VERSION
    header[329:337] = _octal_field(0, 8)
    header[337:345] = _octal_field(0, 8)
    checksum = sum(header)
    header[148:156] = _checksum_field(checksum)
    return bytes(header)


def canonical_archive_bytes(package_dir: Path, release_identifier: str) -> bytes:
    """Serialize one exact validated package layout as canonical raw POSIX USTAR."""

    package_dir = Path(package_dir)
    issues = (*_archive_layout_authority_issues(release_identifier), *_package_layout_issues(package_dir))
    if issues:
        raise ReleaseArchiveError(issues)
    expected_name = validate_release_identifier(release_identifier)
    if package_dir.name != expected_name:
        raise ReleaseArchiveError(
            (archive_issue("PACKAGE_BASENAME", "package_dir", f"expected {expected_name!r}"),)
        )

    top = archive_top_level(release_identifier)
    parts: list[bytes] = []
    for member_name in canonical_member_names(release_identifier):
        is_directory = member_name.endswith("/")
        if is_directory:
            parts.append(_canonical_header(member_name, is_directory=True, size=0))
            continue
        relative = member_name[len(top) + 1 :]
        content = (package_dir / relative).read_bytes()
        parts.append(_canonical_header(member_name, is_directory=False, size=len(content)))
        parts.append(content)
        padding = (-len(content)) % USTAR_RECORD_SIZE
        if padding:
            parts.append(b"\0" * padding)
    parts.append(USTAR_EOF)
    return b"".join(parts)


def _safe_archive_name(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/"):
        return False
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False
    normalized = value[:-1] if value.endswith("/") else value
    if not normalized or urlsplit(normalized).scheme:
        return False
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} or part.startswith(".") for part in parts):
        return False
    return PurePosixPath(normalized).as_posix() == normalized


def _validate_output_paths(
    archive_path: Path,
    sidecar_path: Path,
    release_identifier: str,
    *,
    require_absent: bool,
) -> tuple[ReleaseArchiveIssue, ...]:
    issues: list[ReleaseArchiveIssue] = []
    expected_archive = archive_filename(release_identifier)
    expected_sidecar = sidecar_filename(release_identifier)
    if archive_path.name != expected_archive:
        issues.append(archive_issue("ARCHIVE_FILENAME", "archive", f"expected {expected_archive!r}"))
    if sidecar_path.name != expected_sidecar:
        issues.append(archive_issue("ARCHIVE_SIDECAR_FILENAME", "sidecar", f"expected {expected_sidecar!r}"))
    if archive_path.parent != sidecar_path.parent:
        issues.append(archive_issue("ARCHIVE_OUTPUT_PARENT", "output", "archive and sidecar must share a parent"))
    if not archive_path.parent.is_dir() or archive_path.parent.is_symlink():
        issues.append(archive_issue("ARCHIVE_OUTPUT_PARENT", "output", "expected real existing parent"))
    if require_absent:
        for path, field in ((archive_path, "archive"), (sidecar_path, "sidecar")):
            if os.path.lexists(path):
                issues.append(archive_issue("OUTPUT_EXISTS", field, "output already exists"))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _package_validation_issues(package_dir: Path, repository_root: Path) -> tuple[ReleaseArchiveIssue, ...]:
    return tuple(
        archive_issue("PACKAGE_VALIDATION_FAILED", value.field, f"[{value.code}] {value.message}")
        for value in validate_release_package(package_dir, repository_root=repository_root)
    )


def _manifest_commit_issue(package_dir: Path, source_commit: str) -> tuple[ReleaseArchiveIssue, ...]:
    try:
        manifest = load_and_validate_release_manifest(package_dir / "manifest.json")
    except Exception as exc:
        return (archive_issue("PACKAGE_VALIDATION_FAILED", "manifest.json", str(exc)),)
    if manifest.source_commit == source_commit:
        return ()
    return (
        archive_issue(
            "SOURCE_EVIDENCE_MISMATCH",
            "manifest.source_commit",
            f"expected {source_commit}, got {manifest.source_commit}",
        ),
    )


def _rename_noreplace_syscall(source: Path, destination: Path) -> None:
    """Rename exactly once without overwrite, or fail closed when unsupported."""

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform.startswith("linux"):
        function = getattr(libc, "renameat2", None)
        if function is None:
            raise AtomicNoReplaceUnsupportedError(errno.ENOSYS, "renameat2 is unavailable")
        function.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        function.restype = ctypes.c_int
        result = function(AT_FDCWD, source_bytes, AT_FDCWD, destination_bytes, RENAME_NOREPLACE)
    elif sys.platform == "darwin":
        function = getattr(libc, "renamex_np", None)
        if function is None:
            raise AtomicNoReplaceUnsupportedError(errno.ENOSYS, "renamex_np is unavailable")
        function.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        function.restype = ctypes.c_int
        result = function(source_bytes, destination_bytes, RENAME_EXCL)
    else:
        raise AtomicNoReplaceUnsupportedError(errno.ENOSYS, f"no no-replace rename for {sys.platform}")
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def atomic_rename_noreplace(source: Path, destination: Path) -> None:
    """Publish one file or directory atomically without ever replacing a destination."""

    _rename_noreplace_syscall(Path(source), Path(destination))


def _capture_owned_directory(path: Path, field: str) -> _OwnedDirectory:
    """Capture the non-following identity of a directory created by this process."""

    try:
        status = os.lstat(path)
    except OSError as exc:
        raise ReleaseArchiveError((archive_issue("CLEANUP_FAILED", field, str(exc)),)) from exc
    file_type = stat.S_IFMT(status.st_mode)
    if file_type != stat.S_IFDIR:
        raise ReleaseArchiveError(
            (archive_issue("CLEANUP_FAILED", field, "created path is not a real directory"),)
        )
    return _OwnedDirectory(path=path, st_dev=status.st_dev, st_ino=status.st_ino, file_type=file_type)


def _owned_directory_matches(owned: _OwnedDirectory, path: Path | None = None) -> bool:
    """Check ownership with lstat so a replacement symlink is never followed."""

    try:
        status = os.lstat(owned.path if path is None else path)
    except OSError:
        return False
    return (
        status.st_dev == owned.st_dev
        and status.st_ino == owned.st_ino
        and stat.S_IFMT(status.st_mode) == owned.file_type
    )


def _cleanup_owned_directory(owned: _OwnedDirectory | None, field: str) -> tuple[ReleaseArchiveIssue, ...]:
    """Remove only a directory which still identifies the path we created."""

    if owned is None:
        return ()
    try:
        status = os.lstat(owned.path)
    except FileNotFoundError:
        return (archive_issue("CLEANUP_FAILED", field, "owned directory path is missing"),)
    except OSError as exc:
        return (archive_issue("CLEANUP_FAILED", field, str(exc)),)
    if (
        status.st_dev != owned.st_dev
        or status.st_ino != owned.st_ino
        or stat.S_IFMT(status.st_mode) != owned.file_type
        or not stat.S_ISDIR(status.st_mode)
    ):
        return (archive_issue("CLEANUP_FAILED", field, "path no longer identifies the owned directory"),)
    if not shutil.rmtree.avoids_symlink_attacks:
        return (archive_issue("CLEANUP_FAILED", field, "platform cannot safely remove an owned directory"),)
    try:
        shutil.rmtree(owned.path)
    except OSError as exc:
        return (archive_issue("CLEANUP_FAILED", field, str(exc)),)
    if os.path.lexists(owned.path):
        return (archive_issue("CLEANUP_FAILED", field, "owned directory remains"),)
    return ()


def _archive_output_issues(
    output_dir: Path,
    *,
    repository_root: Path,
    ignored_staging: Path | None = None,
) -> tuple[ReleaseArchiveIssue, ...]:
    """Validate an absent external output directory without adopting siblings."""

    issues: list[ReleaseArchiveIssue] = []
    if not output_dir.is_absolute():
        return (archive_issue("ARCHIVE_OUTPUT_PATH", "output_dir", "expected absolute path"),)
    if os.path.lexists(output_dir):
        issues.append(archive_issue("OUTPUT_EXISTS", "output_dir", "destination already exists"))
    parent = output_dir.parent
    if not parent.is_dir() or parent.is_symlink():
        issues.append(archive_issue("ARCHIVE_OUTPUT_PARENT", "output_dir", "expected real existing parent"))
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))
    current = Path(parent.anchor)
    for component in parent.parts[1:]:
        current = current / component
        if current.is_symlink():
            issues.append(archive_issue("ARCHIVE_OUTPUT_PATH", "output_dir", "parent path contains a symlink"))
            break
    try:
        output_dir.relative_to(repository_root.resolve())
    except ValueError:
        pass
    else:
        issues.append(archive_issue("ARCHIVE_OUTPUT_PATH", "output_dir", "destination must be external to the repository"))
    try:
        for sibling in parent.iterdir():
            if sibling == ignored_staging:
                continue
            if sibling.name.startswith(".release-archive-output-"):
                issues.append(
                    archive_issue("OUTPUT_EXISTS", "output_dir", "unrelated archive staging sibling exists")
                )
                break
    except OSError as exc:
        issues.append(archive_issue("ARCHIVE_OUTPUT_PARENT", "output_dir", str(exc)))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _candidate_layout_issues(candidate_dir: Path, release_identifier: str) -> tuple[ReleaseArchiveIssue, ...]:
    expected = {archive_filename(release_identifier), sidecar_filename(release_identifier)}
    observed: set[str] = set()
    issues: list[ReleaseArchiveIssue] = []
    try:
        for path in candidate_dir.iterdir():
            observed.add(path.name)
            if path.is_symlink() or not path.is_file():
                issues.append(archive_issue("ARCHIVE_OUTPUT_LAYOUT", path.name, "expected regular evidence file"))
    except OSError as exc:
        return (archive_issue("ARCHIVE_OUTPUT_LAYOUT", "candidate_dir", str(exc)),)
    if observed != expected:
        issues.append(
            archive_issue(
                "ARCHIVE_OUTPUT_LAYOUT",
                "candidate_dir",
                f"missing={sorted(expected - observed)!r}; extra={sorted(observed - expected)!r}",
            )
        )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def build_archive_candidate(
    package_dir: Path,
    candidate_dir: Path,
    release_identifier: str,
    source_commit: str,
    *,
    repository_root: Path = REPO_ROOT,
) -> ReleaseArchiveResult:
    """Construct and validate a pair inside a caller-owned private directory.

    This function deliberately does not publish anything externally.  The
    caller owns candidate_dir and is responsible for identity-safe cleanup.
    """

    if SOURCE_COMMIT_PATTERN.fullmatch(source_commit) is None:
        raise ReleaseArchiveError(
            (archive_issue("SOURCE_COMMIT_FORMAT", "source_commit", "expected 40 lowercase hexadecimal characters"),)
        )
    package_dir = Path(package_dir)
    candidate_dir = Path(candidate_dir)
    issues: list[ReleaseArchiveIssue] = []
    try:
        candidate_status = os.lstat(candidate_dir)
    except OSError as exc:
        issues.append(archive_issue("ARCHIVE_CANDIDATE_DIRECTORY", "candidate_dir", str(exc)))
    else:
        if not stat.S_ISDIR(candidate_status.st_mode) or stat.S_ISLNK(candidate_status.st_mode):
            issues.append(archive_issue("ARCHIVE_CANDIDATE_DIRECTORY", "candidate_dir", "expected empty real directory"))
        else:
            try:
                if any(candidate_dir.iterdir()):
                    issues.append(archive_issue("ARCHIVE_CANDIDATE_DIRECTORY", "candidate_dir", "expected empty directory"))
            except OSError as exc:
                issues.append(archive_issue("ARCHIVE_CANDIDATE_DIRECTORY", "candidate_dir", str(exc)))
    issues.extend(_package_validation_issues(package_dir, Path(repository_root).resolve()))
    issues.extend(_manifest_commit_issue(package_dir, source_commit))
    if issues:
        raise ReleaseArchiveError(issues)

    archive_bytes = canonical_archive_bytes(package_dir, release_identifier)
    sidecar_bytes = canonical_sidecar_bytes(release_identifier, archive_bytes)
    archive_path = candidate_dir / archive_filename(release_identifier)
    sidecar_path = candidate_dir / sidecar_filename(release_identifier)
    try:
        archive_path.write_bytes(archive_bytes)
        sidecar_path.write_bytes(sidecar_bytes)
    except OSError as exc:
        raise ReleaseArchiveError((archive_issue("ARCHIVE_BUILD_FAILED", "candidate_dir", str(exc)),)) from exc

    validation_issues = validate_release_archive(
        package_dir,
        archive_path,
        sidecar_path,
        release_identifier,
        source_commit,
        repository_root=repository_root,
    )
    layout_issues = _candidate_layout_issues(candidate_dir, release_identifier)
    byte_issues: list[ReleaseArchiveIssue] = []
    if archive_path.read_bytes() != archive_bytes:
        byte_issues.append(archive_issue("ARCHIVE_CONTENT_MISMATCH", "archive", "candidate archive differs from constructed bytes"))
    if sidecar_path.read_bytes() != sidecar_bytes:
        byte_issues.append(archive_issue("ARCHIVE_CHECKSUM_MISMATCH", "sidecar", "candidate sidecar differs from constructed bytes"))
    if validation_issues or layout_issues or byte_issues:
        raise ReleaseArchiveError((*validation_issues, *layout_issues, *byte_issues))
    return ReleaseArchiveResult(
        archive_path=archive_path,
        sidecar_path=sidecar_path,
        archive_sha256=hashlib.sha256(archive_bytes).hexdigest(),
        member_names=canonical_member_names(release_identifier),
    )


def build_release_archive(
    package_dir: Path,
    output_dir: Path,
    release_identifier: str,
    source_commit: str,
    *,
    repository_root: Path = REPO_ROOT,
) -> ReleaseArchiveResult:
    """Publish a complete validated archive pair by one no-replace directory rename."""

    output_dir = Path(output_dir)
    repository_root = Path(repository_root).resolve()
    if SOURCE_COMMIT_PATTERN.fullmatch(source_commit) is None:
        raise ReleaseArchiveError(
            (archive_issue("SOURCE_COMMIT_FORMAT", "source_commit", "expected 40 lowercase hexadecimal characters"),)
        )
    preflight = _archive_output_issues(output_dir, repository_root=repository_root)
    if preflight:
        raise ReleaseArchiveError(preflight)
    try:
        staging_path = Path(tempfile.mkdtemp(prefix=".release-archive-output-", dir=output_dir.parent))
        staging: _OwnedDirectory | None = _capture_owned_directory(staging_path, "archive_staging")
    except ReleaseArchiveError:
        raise
    except OSError as exc:
        raise ReleaseArchiveError(
            (archive_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", f"unable to create archive staging directory: {exc}"),)
        ) from exc

    primary: tuple[ReleaseArchiveIssue, ...] = ()
    result: ReleaseArchiveResult | None = None
    try:
        candidate = build_archive_candidate(
            package_dir,
            staging.path,
            release_identifier,
            source_commit,
            repository_root=repository_root,
        )
        late_preflight = _archive_output_issues(
            output_dir,
            repository_root=repository_root,
            ignored_staging=staging.path,
        )
        if late_preflight:
            primary = late_preflight
        else:
            try:
                atomic_rename_noreplace(staging.path, output_dir)
            except FileExistsError:
                primary = (archive_issue("OUTPUT_EXISTS", "output_dir", "destination appeared before publication"),)
            except AtomicNoReplaceUnsupportedError as exc:
                primary = (archive_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", str(exc)),)
            except OSError as exc:
                primary = (archive_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", str(exc)),)
            except Exception as exc:
                primary = (archive_issue("ATOMIC_PUBLICATION_FAILED", "output_dir", str(exc)),)
            else:
                # The same directory inode now has an external name.  It is no
                # longer temporary cleanup-owned, even if later reporting fails.
                staging = None
                result = ReleaseArchiveResult(
                    archive_path=output_dir / candidate.archive_path.name,
                    sidecar_path=output_dir / candidate.sidecar_path.name,
                    archive_sha256=candidate.archive_sha256,
                    member_names=candidate.member_names,
                )
    except ReleaseArchiveError as exc:
        primary = exc.issues
    except OSError as exc:
        primary = (archive_issue("ARCHIVE_BUILD_FAILED", "archive", str(exc)),)
    except Exception as exc:
        primary = (archive_issue("ARCHIVE_BUILD_FAILED", "archive", str(exc)),)

    # A test hook or platform wrapper can report an error after the syscall
    # succeeds.  Relinquish only when the destination still has our inode;
    # otherwise retain the external replacement and report unsafe cleanup.
    if primary and staging is not None and not os.path.lexists(staging.path):
        if _owned_directory_matches(staging, output_dir):
            staging = None

    cleanup = _cleanup_owned_directory(staging, "archive_staging")
    if primary or cleanup:
        raise ReleaseArchiveError((*primary, *cleanup))
    assert result is not None
    return result


def _parse_numeric(field: bytes, width: int, name: str, member_name: str) -> int:
    if len(field) != width or field[-1:] != b"\0" or any(value < ord("0") or value > ord("7") for value in field[:-1]):
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, f"noncanonical {name} numeric field"),)
        )
    value = int(field[:-1].decode("ascii"), 8)
    try:
        canonical = _octal_field(value, width)
    except ValueError as exc:
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, f"{name} numeric field overflows canonical encoding"),)
        ) from exc
    if field != canonical:
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, f"noncanonical {name} numeric encoding"),)
        )
    return value


def _parse_checksum(header: bytes, member_name: str) -> int:
    field = header[148:156]
    if len(field) != 8 or field[6:] != b"\0 " or any(value < ord("0") or value > ord("7") for value in field[:6]):
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "noncanonical checksum field"),)
        )
    declared = int(field[:6].decode("ascii"), 8)
    if field != _checksum_field(declared):
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "noncanonical checksum encoding"),)
        )
    calculated = sum(header[:148] + b" " * 8 + header[156:])
    if declared != calculated:
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "header checksum differs"),)
        )
    return declared


def _parse_name(header: bytes) -> str:
    field = header[0:100]
    try:
        terminator = field.index(0)
    except ValueError as exc:
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_METADATA_MISMATCH", "archive", "name field lacks NUL terminator"),)
        ) from exc
    if any(field[terminator + 1 :]):
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_METADATA_MISMATCH", "archive", "name field has nonzero unused bytes"),)
        )
    try:
        return field[:terminator].decode("ascii")
    except UnicodeDecodeError as exc:
        raise ReleaseArchiveError(
            (archive_issue("UNSAFE_ARCHIVE_MEMBER", "archive", "member name is not ASCII"),)
        ) from exc


def _parse_raw_archive(archive_bytes: bytes, release_identifier: str) -> tuple[_RawArchiveMember, ...]:
    if len(archive_bytes) % USTAR_RECORD_SIZE:
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_PARSE_FAILED", "archive", "archive length is not a multiple of 512"),)
        )
    expected = canonical_member_names(release_identifier)
    expected_directories = canonical_directory_names(release_identifier)
    members: list[_RawArchiveMember] = []
    seen: set[str] = set()
    offset = 0
    while True:
        if offset + USTAR_RECORD_SIZE > len(archive_bytes):
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_PARSE_FAILED", "archive", "archive ends before EOF records"),)
            )
        header = archive_bytes[offset : offset + USTAR_RECORD_SIZE]
        if header == b"\0" * USTAR_RECORD_SIZE:
            if len(archive_bytes) < offset + len(USTAR_EOF) or archive_bytes[offset : offset + len(USTAR_EOF)] != USTAR_EOF:
                raise ReleaseArchiveError(
                    (archive_issue("ARCHIVE_METADATA_MISMATCH", "archive", "archive must end with exactly two zero records"),)
                )
            if len(archive_bytes) != offset + len(USTAR_EOF):
                raise ReleaseArchiveError(
                    (archive_issue("ARCHIVE_METADATA_MISMATCH", "archive", "data follows the governed two-record EOF"),)
                )
            break

        member_name = _parse_name(header)
        if not _safe_archive_name(member_name):
            raise ReleaseArchiveError(
                (archive_issue("UNSAFE_ARCHIVE_MEMBER", member_name or "archive", "unsafe member name"),)
            )
        if member_name in seen:
            raise ReleaseArchiveError(
                (archive_issue("DUPLICATE_ARCHIVE_MEMBER", member_name, "member name is not unique"),)
            )
        seen.add(member_name)
        index = len(members)
        if index >= len(expected) or member_name != expected[index]:
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_MEMBER_ORDER", member_name, "member differs from canonical order"),)
            )
        is_directory = member_name in expected_directories
        type_flag = header[156:157]
        expected_type = b"5" if is_directory else b"0"
        if type_flag != expected_type:
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_MEMBER_TYPE", member_name, "type flag differs from canonical member type"),)
            )
        _parse_checksum(header, member_name)
        if header[257:263] != USTAR_MAGIC or header[263:265] != USTAR_VERSION:
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "magic or version differs from POSIX USTAR"),)
            )
        if any(header[345:500]) or any(header[500:512]):
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "prefix or unused bytes are nonzero"),)
            )
        if any(header[157:257]) or any(header[265:329]):
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "link or owner name field is nonempty"),)
            )
        mode = _parse_numeric(header[100:108], 8, "mode", member_name)
        uid = _parse_numeric(header[108:116], 8, "uid", member_name)
        gid = _parse_numeric(header[116:124], 8, "gid", member_name)
        size = _parse_numeric(header[124:136], 12, "size", member_name)
        mtime = _parse_numeric(header[136:148], 12, "mtime", member_name)
        device_major = _parse_numeric(header[329:337], 8, "device major", member_name)
        device_minor = _parse_numeric(header[337:345], 8, "device minor", member_name)
        expected_mode = DIRECTORY_MODE if is_directory else FILE_MODE
        if mode != expected_mode or uid != 0 or gid != 0 or mtime != CANONICAL_MTIME or device_major != 0 or device_minor != 0:
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "member metadata differs from canonical values"),)
            )
        if is_directory and (not member_name.endswith("/") or size != 0):
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "directory metadata differs from canonical values"),)
            )
        expected_header = _canonical_header(member_name, is_directory=is_directory, size=size)
        if header != expected_header:
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "raw header differs from canonical USTAR bytes"),)
            )
        offset += USTAR_RECORD_SIZE
        if offset + size > len(archive_bytes):
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_PARSE_FAILED", member_name, "regular-file body is truncated"),)
            )
        content = archive_bytes[offset : offset + size]
        offset += size
        padding = (-size) % USTAR_RECORD_SIZE
        if offset + padding > len(archive_bytes):
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_PARSE_FAILED", member_name, "regular-file padding is truncated"),)
            )
        if any(archive_bytes[offset : offset + padding]):
            raise ReleaseArchiveError(
                (archive_issue("ARCHIVE_METADATA_MISMATCH", member_name, "regular-file padding is nonzero"),)
            )
        offset += padding
        members.append(_RawArchiveMember(member_name, content, is_directory))
    if tuple(member.name for member in members) != expected:
        raise ReleaseArchiveError(
            (archive_issue("ARCHIVE_MEMBER_ORDER", "archive", f"expected exact {len(expected)}-member inventory"),)
        )
    return tuple(members)


def _materialize_package(
    members: tuple[_RawArchiveMember, ...],
    release_identifier: str,
    package_dir: Path,
) -> tuple[_OwnedDirectory, Path | None, tuple[ReleaseArchiveIssue, ...]]:
    extraction_path = Path(tempfile.mkdtemp(prefix="release-archive-validation-"))
    extraction_root = _capture_owned_directory(extraction_path, "archive_extraction")
    extracted = extraction_root.path / release_identifier
    top = archive_top_level(release_identifier)
    try:
        extracted.mkdir(mode=DIRECTORY_MODE)
        for relative in EXPECTED_DIRECTORIES:
            (extracted / relative).mkdir(mode=DIRECTORY_MODE)
        for member in members:
            if member.is_directory:
                continue
            relative = member.name[len(top) + 1 :]
            expected = (package_dir / relative).read_bytes()
            if member.content != expected:
                return extraction_root, None, (archive_issue("ARCHIVE_CONTENT_MISMATCH", member.name, "bytes differ from package"),)
            destination = extracted / relative
            destination.write_bytes(member.content)
            destination.chmod(FILE_MODE)
        return extraction_root, extracted, ()
    except OSError as exc:
        return extraction_root, None, (archive_issue("ARCHIVE_PARSE_FAILED", "archive", str(exc)),)


def validate_release_archive(
    package_dir: Path,
    archive_path: Path,
    sidecar_path: Path,
    release_identifier: str,
    source_commit: str,
    *,
    repository_root: Path = REPO_ROOT,
) -> tuple[ReleaseArchiveIssue, ...]:
    """Read-only raw USTAR and sidecar validation before safe materialization."""

    package_dir = Path(package_dir)
    archive_path = Path(archive_path)
    sidecar_path = Path(sidecar_path)
    repository_root = Path(repository_root).resolve()
    issues: list[ReleaseArchiveIssue] = list(_archive_layout_authority_issues(release_identifier))
    issues.extend(_validate_output_paths(archive_path, sidecar_path, release_identifier, require_absent=False))
    issues.extend(_package_layout_issues(package_dir))
    if SOURCE_COMMIT_PATTERN.fullmatch(source_commit) is None:
        issues.append(archive_issue("SOURCE_COMMIT_FORMAT", "source_commit", "expected 40 lowercase hexadecimal characters"))
    if not archive_path.is_file() or archive_path.is_symlink():
        issues.append(archive_issue("ARCHIVE_MISSING", "archive", "expected regular archive file"))
    if not sidecar_path.is_file() or sidecar_path.is_symlink():
        issues.append(archive_issue("ARCHIVE_SIDECAR_MISSING", "sidecar", "expected regular sidecar file"))
    if issues:
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))

    archive_bytes = archive_path.read_bytes()
    sidecar_bytes = sidecar_path.read_bytes()
    expected_sidecar = canonical_sidecar_bytes(release_identifier, archive_bytes)
    if sidecar_bytes != expected_sidecar:
        return (archive_issue("ARCHIVE_CHECKSUM_MISMATCH", "sidecar", "bytes differ from canonical checksum sidecar"),)
    try:
        members = _parse_raw_archive(archive_bytes, release_identifier)
    except ReleaseArchiveError as exc:
        return exc.issues

    extraction_root: _OwnedDirectory | None = None
    primary_issues: list[ReleaseArchiveIssue] = []
    try:
        extraction_root, extracted, materialization_issues = _materialize_package(members, release_identifier, package_dir)
        if materialization_issues:
            primary_issues.extend(materialization_issues)
        else:
            assert extracted is not None
            primary_issues.extend(_package_validation_issues(extracted, repository_root))
            primary_issues.extend(_manifest_commit_issue(extracted, source_commit))
            regenerated = canonical_archive_bytes(extracted, release_identifier)
            if regenerated != archive_bytes:
                primary_issues.append(archive_issue("ARCHIVE_METADATA_MISMATCH", "archive", "canonical regeneration differs"))
            if canonical_sidecar_bytes(release_identifier, regenerated) != sidecar_bytes:
                primary_issues.append(archive_issue("ARCHIVE_CHECKSUM_MISMATCH", "sidecar", "canonical regeneration differs"))
    except ReleaseArchiveError as exc:
        primary_issues.extend(exc.issues)
    finally:
        cleanup_issues = _cleanup_owned_directory(extraction_root, "archive_extraction")
        primary_issues.extend(cleanup_issues)
    return tuple(sorted(set(primary_issues), key=lambda value: value.sort_key))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--package-dir", required=True, type=Path)
    build.add_argument("--output-dir", required=True, type=Path)
    build.add_argument("--release-id", required=True)
    build.add_argument("--source-commit", required=True)

    candidate = subparsers.add_parser("build-candidate")
    candidate.add_argument("--package-dir", required=True, type=Path)
    candidate.add_argument("--candidate-dir", required=True, type=Path)
    candidate.add_argument("--release-id", required=True)
    candidate.add_argument("--source-commit", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--package-dir", required=True, type=Path)
    validate.add_argument("--archive", required=True, type=Path)
    validate.add_argument("--sidecar", required=True, type=Path)
    validate.add_argument("--release-id", required=True)
    validate.add_argument("--source-commit", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "build":
            result = build_release_archive(
                args.package_dir,
                args.output_dir,
                args.release_id,
                args.source_commit,
            )
            print("Release archive build: PASS")
            print(f"Archive SHA-256: {result.archive_sha256}")
            print(f"Archive members: {len(result.member_names)}")
            return 0
        if args.command == "build-candidate":
            result = build_archive_candidate(
                args.package_dir,
                args.candidate_dir,
                args.release_id,
                args.source_commit,
            )
            print("Release archive candidate build: PASS")
            print(f"Archive SHA-256: {result.archive_sha256}")
            print(f"Archive members: {len(result.member_names)}")
            return 0
        issues = validate_release_archive(
            args.package_dir,
            args.archive,
            args.sidecar,
            args.release_id,
            args.source_commit,
        )
        if issues:
            for issue in issues:
                print(format_issue(issue))
            return 1
        print("Release archive validation: PASS")
        print(f"Archive members: {len(canonical_member_names(args.release_id))}")
        return 0
    except Exception as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
