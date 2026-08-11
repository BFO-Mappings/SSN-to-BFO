#!/usr/bin/env python3
"""Shared verified runtime mechanics for the SOSA-2023 release package."""

from __future__ import annotations

import hashlib
import os
import platform
import re
import shlex
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping


REQUIRED_RELEASE_NOTE_HEADINGS = (
    "Release identity",
    "Included products",
    "Product selection guidance",
    "Governed axiom and closure summary",
    "Import graph",
    "BFO projection notice",
    "Validation summary",
    "Known limitations",
    "Deferred functionality",
    "License scope",
    "Dependencies",
    "Reproduction",
)


OFFLINE_JAVA_OPTIONS = (
    "-Djava.net.useSystemProxies=true",
    "-Dhttp.proxyHost=127.0.0.1",
    "-Dhttp.proxyPort=9",
    "-Dhttps.proxyHost=127.0.0.1",
    "-Dhttps.proxyPort=9",
    "-Dftp.proxyHost=127.0.0.1",
    "-Dftp.proxyPort=9",
    "-Dhttp.nonProxyHosts=",
)


PROXY_ENVIRONMENT_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "FTP_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "ftp_proxy",
    "all_proxy",
    "no_proxy",
)


def sha256_bytes(value: bytes) -> str:
    """Return the lowercase SHA-256 digest of one byte string."""

    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class ReleasePackageIssue:
    code: str
    field: str
    message: str

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return self.field, self.code, self.message


class ReleasePackageError(ValueError):
    """One or more deterministic release-package failures."""

    def __init__(self, issues: Iterable[ReleasePackageIssue]):
        self.issues = tuple(sorted(set(issues), key=lambda value: value.sort_key))
        super().__init__("; ".join(format_issue(issue) for issue in self.issues))


@dataclass(frozen=True)
class DevelopmentSnapshot:
    path: str
    content: bytes
    sha256: str
    mtime_ns: int


@dataclass(frozen=True)
class ResolvedValidationToolchain:
    java_executable: Path
    java_vendor: str
    java_version: str
    java_vm_name: str
    robot_executable: Path
    robot_jar: Path
    robot_artifact: str
    robot_version: str
    robot_jar_sha256: str
    java_heap: str

    def java_robot_command(self, *arguments: str) -> tuple[str, ...]:
        return (
            str(self.java_executable),
            f"-Xmx{self.java_heap}",
            *OFFLINE_JAVA_OPTIONS,
            "-jar",
            str(self.robot_jar),
            *arguments,
        )


def format_issue(issue: ReleasePackageIssue) -> str:
    return f"ERROR [{issue.code}] {issue.field}: {issue.message}"


def package_issue(code: str, field: str, message: str) -> ReleasePackageIssue:
    return ReleasePackageIssue(code, field, message)


def _sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def validate_release_notes_bytes(
    value: bytes,
    *,
    template_bytes: bytes | None = None,
) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        return (package_issue("RELEASE_NOTES_UTF8", "release_notes", str(exc)),)
    if not text:
        issues.append(package_issue("RELEASE_NOTES_EMPTY", "release_notes", "notes are empty"))
    if "\r" in text:
        issues.append(package_issue("RELEASE_NOTES_LINE_ENDING", "release_notes", "CRLF and bare CR are prohibited"))
    if not text.endswith("\n") or text.endswith("\n\n"):
        issues.append(package_issue("RELEASE_NOTES_FINAL_NEWLINE", "release_notes", "expected exactly one final newline"))
    controls = sorted({ord(character) for character in text if ord(character) < 32 and character != "\n"})
    if controls:
        issues.append(package_issue("RELEASE_NOTES_CONTROL", "release_notes", f"control characters are prohibited: {controls}"))
    headings = tuple(
        line[2:] for line in text.splitlines() if line.startswith("# ") and not line.startswith("## ")
    )
    for heading in REQUIRED_RELEASE_NOTE_HEADINGS:
        if heading not in headings:
            issues.append(package_issue("RELEASE_NOTES_HEADING", "release_notes", f"missing top-level heading {heading!r}"))
    if template_bytes is not None and value == template_bytes:
        issues.append(package_issue("RELEASE_NOTES_TEMPLATE", "release_notes", "unmodified template is prohibited"))
    marker = re.search(r"(?i)(?:\bTODO\b|\bTBD\b|<release-id>)", text)
    if marker is not None:
        issues.append(package_issue("RELEASE_NOTES_PLACEHOLDER", "release_notes", f"unresolved marker {marker.group(0)!r}"))
    return tuple(sorted(set(issues), key=lambda item: item.sort_key))


def _load_toolchain(repository_root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (repository_root / "config/validation-toolchain.env").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, separator, value = line.partition("=")
            if not separator or not key or not value:
                raise ReleasePackageError((package_issue("TOOLCHAIN_DECLARATION", "config/validation-toolchain.env", f"invalid line {line!r}"),))
            values[key] = value
    return values


def offline_subprocess_environment(
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return a deterministic subprocess environment that denies remote URL access."""

    environment = dict(os.environ if base is None else base)
    for key in PROXY_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    blocked_proxy = "http://127.0.0.1:9"
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "FTP_PROXY", "ALL_PROXY"):
        environment[key] = blocked_proxy
        environment[key.lower()] = blocked_proxy
    environment["NO_PROXY"] = ""
    environment["no_proxy"] = ""
    return environment


def _unverified_robot_artifact(message: str) -> ReleasePackageError:
    return ReleasePackageError(
        (package_issue("UNVERIFIED_ROBOT_ARTIFACT", "validation_environment.robot_artifact", message),)
    )


def _resolve_robot_wrapper() -> tuple[Path, Path, Path]:
    located = shutil.which("robot")
    if located is None:
        raise _unverified_robot_artifact("ROBOT executable not found on PATH")
    robot_executable = Path(located).resolve()
    try:
        text = robot_executable.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise _unverified_robot_artifact(
            f"cannot inspect resolved ROBOT wrapper {robot_executable}: {exc}"
        ) from exc

    commands: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            tokens = shlex.split(stripped)
        except ValueError as exc:
            raise _unverified_robot_artifact(f"cannot parse ROBOT wrapper command: {exc}") from exc
        if tokens and tokens[0] == "exec":
            tokens = tokens[1:]
        if "-jar" in tokens:
            commands.append(tokens)
    if len(commands) != 1:
        raise _unverified_robot_artifact(
            f"expected exactly one local Java -jar command, found {len(commands)}"
        )
    command = commands[0]
    jar_index = command.index("-jar")
    if jar_index == 0 or jar_index + 1 >= len(command):
        raise _unverified_robot_artifact("ROBOT wrapper has an incomplete Java -jar command")

    java_token = command[0]
    if "/" in java_token:
        java_executable = Path(java_token).expanduser().resolve()
    else:
        located_java = shutil.which(java_token)
        if located_java is None:
            raise _unverified_robot_artifact(
                f"Java executable {java_token!r} from ROBOT wrapper is not on PATH"
            )
        java_executable = Path(located_java).resolve()
    jar_text = os.path.expandvars(os.path.expanduser(command[jar_index + 1]))
    if "$" in jar_text:
        raise _unverified_robot_artifact("ROBOT JAR path contains an unresolved variable")
    robot_jar = Path(jar_text)
    if not robot_jar.is_absolute():
        raise _unverified_robot_artifact("ROBOT JAR path is relative and therefore ambiguous")
    robot_jar = robot_jar.resolve()
    if not java_executable.is_file() or not os.access(java_executable, os.X_OK):
        raise _unverified_robot_artifact("resolved Java executable is not an executable file")
    if not robot_jar.is_file():
        raise _unverified_robot_artifact("resolved ROBOT JAR is not a regular file")
    return robot_executable, java_executable, robot_jar


def _normalized_java_property(output: str, name: str) -> str:
    match = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", output, re.MULTILINE)
    if match is None:
        raise ReleasePackageError(
            (package_issue("JAVA_IDENTITY", f"validation_environment.{name}", "property is absent"),)
        )
    value = " ".join(match.group(1).split())
    if not value:
        raise ReleasePackageError(
            (package_issue("JAVA_IDENTITY", f"validation_environment.{name}", "property is empty"),)
        )
    return value


def resolve_validation_toolchain(repository_root: Path) -> ResolvedValidationToolchain:
    """Resolve and verify the exact Java executable and ROBOT JAR used for reasoning."""

    repository_root = repository_root.resolve()
    declaration = _load_toolchain(repository_root)
    robot_executable, java_executable, robot_jar = _resolve_robot_wrapper()
    environment = offline_subprocess_environment()
    java = subprocess.run(
        [str(java_executable), *OFFLINE_JAVA_OPTIONS, "-XshowSettings:properties", "-version"],
        cwd=repository_root,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    java_text = "\n".join(part for part in (java.stdout, java.stderr) if part).strip()
    if java.returncode != 0:
        raise ReleasePackageError(
            (package_issue("JAVA_IDENTITY", "validation_environment.java", "Java identity probe failed"),)
        )
    java_vendor = _normalized_java_property(java_text, "java.vendor")
    java_version = _normalized_java_property(java_text, "java.version")
    java_vm_name = _normalized_java_property(java_text, "java.vm.name")
    expected_java = declaration["VALIDATION_JAVA_VERSION"]
    if java_version != expected_java and not java_version.startswith(expected_java + "."):
        raise ReleasePackageError(
            (
                package_issue(
                    "JAVA_VERSION_MISMATCH",
                    "validation_environment.java_version",
                    f"expected {expected_java}.x, got {java_version}",
                ),
            )
        )
    expected_python = declaration["VALIDATION_PYTHON_VERSION"]
    python_version = platform.python_version()
    if python_version != expected_python and not python_version.startswith(expected_python + "."):
        raise ReleasePackageError(
            (
                package_issue(
                    "PYTHON_VERSION_MISMATCH",
                    "validation_environment.python_version",
                    f"expected {expected_python}.x, got {python_version}",
                ),
            )
        )

    robot_hash = _sha256(robot_jar)
    expected_robot_hash = declaration["VALIDATION_ROBOT_SHA256"]
    if robot_hash != expected_robot_hash:
        raise ReleasePackageError(
            (
                package_issue(
                    "ROBOT_SHA256_MISMATCH",
                    "validation_environment.robot_sha256",
                    f"expected {expected_robot_hash}, got {robot_hash}",
                ),
            )
        )
    robot = subprocess.run(
        [
            str(java_executable),
            *OFFLINE_JAVA_OPTIONS,
            "-jar",
            str(robot_jar),
            "--version",
        ],
        cwd=repository_root,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    robot_text = "\n".join(part for part in (robot.stdout, robot.stderr) if part).strip()
    robot_match = re.search(r"ROBOT version ([0-9.]+)", robot_text)
    if robot.returncode != 0 or robot_match is None:
        raise _unverified_robot_artifact("unable to obtain a version from the resolved ROBOT JAR")
    expected_robot = declaration["VALIDATION_ROBOT_VERSION"]
    if robot_match.group(1) != expected_robot:
        raise ReleasePackageError(
            (
                package_issue(
                    "ROBOT_VERSION_MISMATCH",
                    "validation_environment.robot_version",
                    f"expected {expected_robot}, got {robot_match.group(1)}",
                ),
            )
        )
    return ResolvedValidationToolchain(
        java_executable=java_executable,
        java_vendor=java_vendor,
        java_version=java_version,
        java_vm_name=java_vm_name,
        robot_executable=robot_executable,
        robot_jar=robot_jar,
        robot_artifact=declaration["VALIDATION_ROBOT_URL"],
        robot_version=robot_match.group(1),
        robot_jar_sha256=robot_hash,
        java_heap=declaration["VALIDATION_ROBOT_JAVA_HEAP"],
    )


@contextmanager
def verified_robot_launcher(
    toolchain: ResolvedValidationToolchain,
    temporary_root: Path,
) -> Iterator[Path]:
    """Expose a controlled `robot` command for COMS reasoners using the verified runtime."""

    launcher_directory = temporary_root / "verified-toolchain"
    launcher_directory.mkdir(parents=True, exist_ok=False)
    launcher = launcher_directory / "robot"
    command = toolchain.java_robot_command()
    launcher.write_text(
        "#!/bin/sh\nexec "
        + " ".join(shlex.quote(value) for value in command)
        + ' "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o700)
    updates = offline_subprocess_environment()
    updates["PATH"] = str(launcher_directory) + os.pathsep + os.environ.get("PATH", "")
    governed_keys = (*PROXY_ENVIRONMENT_KEYS, "PATH")
    previous = {key: os.environ.get(key) for key in governed_keys}
    try:
        for key in governed_keys:
            if key in updates:
                os.environ[key] = updates[key]
            else:
                os.environ.pop(key, None)
        yield launcher.resolve()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
