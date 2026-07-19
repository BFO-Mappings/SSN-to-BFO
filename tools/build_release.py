#!/usr/bin/env python3
"""Build one deterministic formal-release candidate package."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import shlex
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping
from xml.etree import ElementTree
from xml.sax.saxutils import quoteattr

from rdflib import Graph, RDF, OWL, URIRef

import generate_mapping_from_coms as coms
import publication_metadata as publication
from product_dispositions import load_disposition_document
from release_context import FormalReleaseContext, parse_formal_release_context, validate_formal_release_context
from release_manifest import (
    FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS,
    INCLUDED_FILE_PATH_ORDER,
    PRODUCT_ORDER,
    ReleaseManifest,
    ReleaseManifestDependency,
    ReleaseManifestHermitResult,
    ReleaseManifestIncludedFile,
    ReleaseManifestInput,
    ReleaseManifestProduct,
    ReleaseManifestValidation,
    ReleaseManifestValidationEnvironment,
    build_release_manifest,
    canonical_manifest_bytes,
    load_and_validate_release_manifest,
    release_manifest_sha256,
    sha256_bytes,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_FILE_PATHS = (
    "LICENSE",
    "RELEASE-NOTES.md",
    "SHA256SUMS",
    "SSN2BFO.ttl",
    "catalog-v001.xml",
    "current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    "current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    "current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
    "current-ssn-sosa/ssn-sosa-cco-extension.ttl",
    "evidence/coms-product-dispositions.json",
    "manifest.json",
    "sources/SSN2BFO-COMS.xlsx",
    "sources/publication-metadata.toml",
)
CHECKSUM_PATHS = tuple(path for path in PACKAGE_FILE_PATHS if path != "SHA256SUMS")
INCLUDED_FILE_PATHS = tuple(
    path for path in PACKAGE_FILE_PATHS if path not in {"manifest.json", "SHA256SUMS"}
)
if INCLUDED_FILE_PATHS != INCLUDED_FILE_PATH_ORDER:
    raise RuntimeError("package and manifest included-file authorities differ")
PRODUCT_PACKAGE_PATHS = {
    "integrated": "SSN2BFO.ttl",
    "alignment_core": "current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    "strict_bfo_mapping": "current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    "bfo_projection": "current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
    "cco_extension": "current-ssn-sosa/ssn-sosa-cco-extension.ttl",
}
BYTE_AFFECTING_MODULES = (
    "tools/coms_row_identity.py",
    "tools/product_dispositions.py",
    "tools/publication_metadata.py",
    "tools/release_context.py",
    "tools/generate_mapping_from_coms.py",
    "tools/modular_products.py",
    "tools/release_manifest.py",
    "tools/build_release.py",
)
DEPENDENCY_KEYS = (
    "sosa",
    "sosa_sampling",
    "ssn",
    "ssn_systems",
    "merged_cco_bfo",
)
DEPENDENCY_ROLES = (
    "pinned source ontology validation dependency",
    "pinned source ontology validation dependency",
    "pinned source ontology validation dependency",
    "pinned source ontology validation dependency",
    "pinned merged CCO/BFO validation dependency",
)
DEVELOPMENT_OUTPUT_PATHS = (
    "SSN2BFO.ttl",
    "reports/coms-generation-validation.md",
    "reports/coms-source-term-coverage.md",
    "reports/coms-vs-pre-coms-legacy-diff.md",
    "reports/coms-product-dispositions.json",
    "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
    "releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
)
GOVERNED_CLOSURE_COUNTS = {
    "integrated": 105,
    "alignment_core": 29,
    "strict_bfo_mapping": 48,
    "bfo_projection": 48,
    "cco_extension": 105,
}
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
CATALOG_NAMESPACE = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
TEMP_PREFIX = ".release-package-build-"
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


@dataclass(frozen=True)
class ReleasePackageIssue:
    code: str
    field: str
    message: str

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return self.field, self.code, self.message


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


@dataclass(frozen=True)
class AssembledReleasePackage:
    manifest: ReleaseManifest
    manifest_bytes: bytes
    catalog_bytes: bytes
    sha256sums_bytes: bytes


@dataclass(frozen=True)
class ReleasePackageResult:
    output_dir: Path
    manifest: ReleaseManifest
    manifest_sha256: str
    catalog_sha256: str
    sha256sums_sha256: str
    file_hashes: tuple[tuple[str, str], ...]


class ReleasePackageError(ValueError):
    """One or more deterministic release-package failures."""

    def __init__(self, issues: Iterable[ReleasePackageIssue]):
        self.issues = tuple(sorted(set(issues), key=lambda value: value.sort_key))
        super().__init__("; ".join(format_issue(issue) for issue in self.issues))


def format_issue(issue: ReleasePackageIssue) -> str:
    return f"ERROR [{issue.code}] {issue.field}: {issue.message}"


def package_issue(code: str, field: str, message: str) -> ReleasePackageIssue:
    return ReleasePackageIssue(code, field, message)


def _sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def snapshot_development_outputs(repository_root: Path) -> tuple[DevelopmentSnapshot, ...]:
    snapshots: list[DevelopmentSnapshot] = []
    for relative in DEVELOPMENT_OUTPUT_PATHS:
        path = repository_root / relative
        content = path.read_bytes()
        snapshots.append(
            DevelopmentSnapshot(relative, content, sha256_bytes(content), path.stat().st_mtime_ns)
        )
    return tuple(snapshots)


def development_snapshot_issues(
    repository_root: Path,
    snapshots: Iterable[DevelopmentSnapshot],
) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []
    for snapshot in snapshots:
        path = repository_root / snapshot.path
        if not path.is_file():
            issues.append(package_issue("DEVELOPMENT_OUTPUT_MISSING", snapshot.path, "file is absent"))
            continue
        content = path.read_bytes()
        if content != snapshot.content or sha256_bytes(content) != snapshot.sha256:
            issues.append(package_issue("DEVELOPMENT_OUTPUT_MUTATED", snapshot.path, "bytes changed"))
        if path.stat().st_mtime_ns != snapshot.mtime_ns:
            issues.append(package_issue("DEVELOPMENT_OUTPUT_MTIME", snapshot.path, "mtime changed"))
    return tuple(sorted(issues, key=lambda value: value.sort_key))


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


def canonical_catalog_bytes(
    metadata: publication.PublicationMetadata,
    context: FormalReleaseContext,
) -> bytes:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<catalog xmlns="{CATALOG_NAMESPACE}">',
    ]
    for key in PRODUCT_ORDER:
        version_iri = publication.release_version_iri(metadata, key, context)
        lines.append(
            f"  <uri name={quoteattr(version_iri)} uri={quoteattr(PRODUCT_PACKAGE_PATHS[key])}/>"
        )
    lines.append("</catalog>")
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_catalog_bytes(
    value: bytes,
    metadata: publication.PublicationMetadata,
    context: FormalReleaseContext,
) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []
    if any(token in value for token in (b"<!DOCTYPE", b"<!ENTITY", b"<!--")):
        return (
            package_issue(
                "CATALOG_PROHIBITED_XML",
                "catalog-v001.xml",
                "DTD, entity, and comments are prohibited",
            ),
        )
    try:
        root = ElementTree.fromstring(value)
    except (ElementTree.ParseError, UnicodeDecodeError) as exc:
        return (package_issue("CATALOG_XML", "catalog-v001.xml", str(exc)),)
    if root.tag != f"{{{CATALOG_NAMESPACE}}}catalog":
        issues.append(package_issue("CATALOG_ROOT", "catalog-v001.xml", "wrong catalog namespace or root"))
    entries = [(child.attrib.get("name"), child.attrib.get("uri")) for child in root]
    expected = [
        (publication.release_version_iri(metadata, key, context), PRODUCT_PACKAGE_PATHS[key])
        for key in PRODUCT_ORDER
    ]
    if entries != expected:
        issues.append(package_issue("CATALOG_ENTRIES", "catalog-v001.xml", "version-IRI mappings differ"))
    canonical = canonical_catalog_bytes(metadata, context)
    if value != canonical:
        issues.append(package_issue("NONCANONICAL_CATALOG", "catalog-v001.xml", "bytes differ from canonical XML"))
    return tuple(sorted(set(issues), key=lambda item: item.sort_key))


def canonical_sha256sums_bytes(package_dir: Path) -> bytes:
    lines = [f"{_sha256(package_dir / path)}  {path}" for path in CHECKSUM_PATHS]
    return ("\n".join(lines) + "\n").encode("ascii")


def validate_sha256sums_bytes(package_dir: Path, value: bytes) -> tuple[ReleasePackageIssue, ...]:
    expected = canonical_sha256sums_bytes(package_dir)
    if value == expected:
        return ()
    return (package_issue("NONCANONICAL_CHECKSUMS", "SHA256SUMS", "bytes differ from exact canonical checksums"),)


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


def collect_validation_environment(
    repository_root: Path,
    toolchain: ResolvedValidationToolchain,
) -> ReleaseManifestValidationEnvironment:
    toolchain_path = "config/validation-toolchain.env"
    requirements_path = "requirements/validation.txt"
    return ReleaseManifestValidationEnvironment(
        python_implementation=platform.python_implementation(),
        python_version=platform.python_version(),
        java_vendor=toolchain.java_vendor,
        java_version=toolchain.java_version,
        java_vm_name=toolchain.java_vm_name,
        robot_artifact=toolchain.robot_artifact,
        robot_version=toolchain.robot_version,
        robot_sha256=toolchain.robot_jar_sha256,
        toolchain_path=toolchain_path,
        toolchain_sha256=_sha256(repository_root / toolchain_path),
        requirements_path=requirements_path,
        requirements_sha256=_sha256(repository_root / requirements_path),
    )


def canonical_dependency_paths() -> tuple[Path, ...]:
    """Return the fixed closure paths from the COMS generator's production authorities."""

    return (*coms.SOURCE_IMPORTS, coms.BFO_VALIDATION_DEPENDENCY)


def collect_dependencies(repository_root: Path) -> tuple[ReleaseManifestDependency, ...]:
    dependencies: list[ReleaseManifestDependency] = []
    for key, role, authority_path in zip(
        DEPENDENCY_KEYS,
        DEPENDENCY_ROLES,
        canonical_dependency_paths(),
        strict=True,
    ):
        relative = authority_path.as_posix()
        path = repository_root / relative
        graph = Graph().parse(path, format="turtle")
        ontology_iris = sorted(
            str(value) for value in graph.subjects(RDF.type, OWL.Ontology) if isinstance(value, URIRef)
        )
        if len(ontology_iris) != 1:
            raise ReleasePackageError((package_issue("DEPENDENCY_ONTOLOGY_IDENTITY", relative, f"expected one ontology IRI, got {ontology_iris!r}"),))
        version_iris = sorted(
            str(value) for value in graph.objects(URIRef(ontology_iris[0]), OWL.versionIRI) if isinstance(value, URIRef)
        )
        if len(version_iris) > 1:
            raise ReleasePackageError((package_issue("DEPENDENCY_VERSION_IDENTITY", relative, f"expected at most one version IRI, got {version_iris!r}"),))
        dependencies.append(
            ReleaseManifestDependency(
                key=key,
                role=role,
                path=relative,
                ontology_iri=ontology_iris[0],
                version_iri=version_iris[0] if version_iris else None,
                sha256=_sha256(path),
                byte_size=path.stat().st_size,
            )
        )
    return tuple(dependencies)


def render_formal_products(
    context: FormalReleaseContext,
    workbook_path: Path,
    metadata_path: Path,
    disposition_path: Path,
):
    rows, stats = coms.read_workbook(workbook_path)
    processed = coms.validate_and_process_rows(rows, coms.Resolver(), stats)
    audits = tuple(row.identity_audit for row in processed)
    disposition = load_disposition_document(disposition_path)
    metadata = publication.load_metadata(metadata_path)
    rendered = coms.render_formal_product_set(processed, audits, disposition, metadata, context)
    return metadata, rendered


def formal_product_bytes(rendered) -> dict[str, bytes]:
    return {
        "integrated": rendered.integrated.serialized_bytes,
        "alignment_core": rendered.alignment_core.serialized_bytes,
        "strict_bfo_mapping": rendered.strict_bfo_mapping.serialized_bytes,
        "bfo_projection": rendered.bfo_projection.serialized_bytes,
        "cco_extension": rendered.cco_extension.serialized_bytes,
    }


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


def run_independent_reasoning(
    package_dir: Path,
    temporary_root: Path,
    toolchain: ResolvedValidationToolchain,
) -> tuple[ReleaseManifestHermitResult, ...]:
    paths = {key: package_dir / relative for key, relative in PRODUCT_PACKAGE_PATHS.items()}
    with verified_robot_launcher(toolchain, temporary_root) as launcher:
        results = {
            "integrated": coms.run_candidate_hermit(
                paths["integrated"], temporary_root / "integrated"
            ),
            "alignment_core": coms.run_alignment_core_hermit(
                paths["alignment_core"], temporary_root / "alignment-core"
            ),
            "strict_bfo_mapping": coms.run_strict_bfo_hermit(
                paths["strict_bfo_mapping"],
                paths["alignment_core"],
                temporary_root / "strict-bfo",
            ),
            "bfo_projection": coms.run_bfo_projection_hermit(
                paths["bfo_projection"],
                paths["strict_bfo_mapping"],
                paths["alignment_core"],
                temporary_root / "bfo-projection",
            ),
            "cco_extension": coms.run_cco_extension_hermit(
                paths["cco_extension"],
                paths["strict_bfo_mapping"],
                paths["alignment_core"],
                temporary_root / "cco-extension",
            ),
        }
    evidence: list[ReleaseManifestHermitResult] = []
    issues: list[ReleasePackageIssue] = []
    for key in PRODUCT_ORDER:
        result = results[key]
        if result.robot_path is None or Path(result.robot_path).resolve() != launcher:
            issues.append(
                package_issue(
                    "UNVERIFIED_ROBOT_EXECUTION",
                    key,
                    "reasoning did not use the controlled verified Java/ROBOT launcher",
                )
            )
        expected = next(
            count
            for product_key, count in FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS
            if product_key == key
        )
        if result.closure_triple_count != expected:
            issues.append(package_issue("HERMIT_CLOSURE_COUNT", key, f"expected {expected}, got {result.closure_triple_count}"))
        if not result.passed:
            issues.append(package_issue("HERMIT_FAILED", key, result.robot_output or "independent reasoning failed"))
        evidence.append(
            ReleaseManifestHermitResult(
                product_key=key,
                status="PASS" if result.passed else "FAIL",
                fixed_closure_triple_count=result.closure_triple_count,
                return_code=-1 if result.return_code is None else result.return_code,
                reasoned_output_produced=result.reasoned_output_produced,
                named_unsatisfiable_class_count=len(result.unsat_classes),
                owl_nothing_equivalent_named_class_count=-1 if result.owl_nothing_count is None else result.owl_nothing_count,
            )
        )
    if issues:
        raise ReleasePackageError(issues)
    return tuple(evidence)


def collect_product_records(rendered, metadata, context) -> tuple[ReleaseManifestProduct, ...]:
    results = {
        "integrated": rendered.integrated,
        "alignment_core": rendered.alignment_core,
        "strict_bfo_mapping": rendered.strict_bfo_mapping,
        "bfo_projection": rendered.bfo_projection,
        "cco_extension": rendered.cco_extension,
    }
    metadata_by_key = {value.key: value for value in metadata.products}
    products: list[ReleaseManifestProduct] = []
    for key in PRODUCT_ORDER:
        result = results[key]
        products.append(
            ReleaseManifestProduct(
                key=key,
                path=PRODUCT_PACKAGE_PATHS[key],
                stable_ontology_iri=metadata_by_key[key].stable_ontology_iri,
                version_iri=publication.release_version_iri(metadata, key, context),
                imports=publication.release_project_imports(metadata, key, context),
                sha256=result.sha256,
                byte_size=len(result.serialized_bytes),
                ontology_declaration_count=result.ontology_declaration_triple_count,
                import_count=result.import_triple_count,
                static_metadata_count=result.metadata_annotation_count,
                formal_metadata_count=result.formal_metadata_annotation_count,
                logical_triple_count=result.logical_triple_count,
                total_triple_count=result.total_triple_count,
                direct_governed_axiom_count=result.governed_axiom_count,
                governed_closure_axiom_count=GOVERNED_CLOSURE_COUNTS[key],
                reasoning_mode="independent",
            )
        )
    return tuple(products)


def collect_inputs(
    repository_root: Path,
    notes_relative: str,
    *,
    notes_bytes: bytes | None = None,
) -> tuple[ReleaseManifestInput, ...]:
    records = (
        ("coms_workbook", "mappings/SSN2BFO-COMS.xlsx", "sources/SSN2BFO-COMS.xlsx"),
        ("publication_metadata", "config/publication-metadata.toml", "sources/publication-metadata.toml"),
        ("product_dispositions", "reports/coms-product-dispositions.json", "evidence/coms-product-dispositions.json"),
        ("release_notes", notes_relative, "RELEASE-NOTES.md"),
        ("license", "LICENSE", "LICENSE"),
        *(("module_" + Path(path).stem, path, None) for path in BYTE_AFFECTING_MODULES),
    )
    results: list[ReleaseManifestInput] = []
    for key, source, destination in records:
        if key == "release_notes" and notes_bytes is not None:
            content = notes_bytes
        else:
            content = (repository_root / source).read_bytes()
        results.append(
            ReleaseManifestInput(
                key=key,
                source_path=source,
                package_path=destination,
                sha256=sha256_bytes(content),
                byte_size=len(content),
            )
        )
    return tuple(results)


def collect_included_files(package_dir: Path) -> tuple[ReleaseManifestIncludedFile, ...]:
    roles = {
        "LICENSE": "project license",
        "RELEASE-NOTES.md": "release notes",
        "SSN2BFO.ttl": "formal integrated ontology product",
        "catalog-v001.xml": "formal version-IRI catalog",
        "current-ssn-sosa/ssn-sosa-alignment-core.ttl": "formal alignment-core ontology product",
        "current-ssn-sosa/ssn-sosa-bfo-mapping.ttl": "formal strict-BFO ontology product",
        "current-ssn-sosa/ssn-sosa-bfo-projection.ttl": "formal BFO-projection ontology product",
        "current-ssn-sosa/ssn-sosa-cco-extension.ttl": "formal CCO-extension ontology product",
        "evidence/coms-product-dispositions.json": "governed product-disposition evidence",
        "sources/SSN2BFO-COMS.xlsx": "governed COMS workbook",
        "sources/publication-metadata.toml": "governed publication metadata",
    }
    return tuple(
        ReleaseManifestIncludedFile(
            path=relative,
            role=roles[relative],
            sha256=_sha256(package_dir / relative),
            byte_size=(package_dir / relative).stat().st_size,
        )
        for relative in INCLUDED_FILE_PATHS
    )


def _copy_package_inputs(repository_root: Path, notes_bytes: bytes, package_dir: Path) -> None:
    copies = {
        "LICENSE": (repository_root / "LICENSE").read_bytes(),
        "RELEASE-NOTES.md": notes_bytes,
        "sources/SSN2BFO-COMS.xlsx": (
            repository_root / "mappings/SSN2BFO-COMS.xlsx"
        ).read_bytes(),
        "sources/publication-metadata.toml": (
            repository_root / "config/publication-metadata.toml"
        ).read_bytes(),
        "evidence/coms-product-dispositions.json": (
            repository_root / "reports/coms-product-dispositions.json"
        ).read_bytes(),
    }
    for relative, content in copies.items():
        destination = package_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


def _validate_paths(context: FormalReleaseContext, notes_source: Path, output_dir: Path, repository_root: Path) -> str:
    if output_dir.name != context.release_identifier:
        raise ReleasePackageError((package_issue("OUTPUT_BASENAME", "output_dir", f"expected basename {context.release_identifier!r}"),))
    if os.path.lexists(output_dir):
        raise ReleasePackageError((package_issue("OUTPUT_EXISTS", "output_dir", "output directory already exists"),))
    if not output_dir.parent.is_dir():
        raise ReleasePackageError((package_issue("OUTPUT_PARENT", "output_dir", "parent directory does not exist"),))
    resolved_repo = repository_root.resolve()
    resolved_notes = notes_source.resolve()
    try:
        relative = resolved_notes.relative_to(resolved_repo).as_posix()
    except ValueError as exc:
        raise ReleasePackageError((package_issue("NOTES_OUTSIDE_REPOSITORY", "notes_source", "notes must be inside repository"),)) from exc
    if relative == "release-notes/TEMPLATE.md":
        raise ReleasePackageError((package_issue("RELEASE_NOTES_TEMPLATE", "notes_source", "template cannot be packaged"),))
    if notes_source.is_symlink():
        raise ReleasePackageError((package_issue("RELEASE_NOTES_SYMLINK", "notes_source", "notes must be a regular repository file"),))
    if not resolved_notes.is_file():
        raise ReleasePackageError((package_issue("RELEASE_NOTES_MISSING", "notes_source", "notes file is absent"),))
    return relative


def assemble_release_package(
    context: FormalReleaseContext,
    notes_bytes: bytes,
    notes_relative: str,
    package_dir: Path,
    repository_root: Path,
    toolchain: ResolvedValidationToolchain,
    snapshots: tuple[DevelopmentSnapshot, ...],
) -> AssembledReleasePackage:
    """Construct one complete deterministic package without proving a second rebuild."""

    package_dir = Path(package_dir)
    repository_root = repository_root.resolve()
    if os.path.lexists(package_dir):
        raise ReleasePackageError(
            (package_issue("ASSEMBLY_OUTPUT_EXISTS", "package_dir", "assembly directory exists"),)
        )
    if not package_dir.parent.is_dir():
        raise ReleasePackageError(
            (package_issue("ASSEMBLY_PARENT", "package_dir", "assembly parent does not exist"),)
        )
    note_issues = validate_release_notes_bytes(
        notes_bytes,
        template_bytes=(repository_root / "release-notes/TEMPLATE.md").read_bytes(),
    )
    if note_issues:
        raise ReleasePackageError(note_issues)
    package_dir.mkdir()
    reasoning_root = package_dir.parent / f".{package_dir.name}-reasoning"
    try:
        metadata, rendered = render_formal_products(
            context,
            repository_root / "mappings/SSN2BFO-COMS.xlsx",
            repository_root / "config/publication-metadata.toml",
            repository_root / "reports/coms-product-dispositions.json",
        )
        for key, value in formal_product_bytes(rendered).items():
            destination = package_dir / PRODUCT_PACKAGE_PATHS[key]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(value)
        _copy_package_inputs(repository_root, notes_bytes, package_dir)
        catalog = canonical_catalog_bytes(metadata, context)
        catalog_issues = validate_catalog_bytes(catalog, metadata, context)
        if catalog_issues:
            raise ReleasePackageError(catalog_issues)
        (package_dir / "catalog-v001.xml").write_bytes(catalog)
        hermit = run_independent_reasoning(package_dir, reasoning_root, toolchain)
        environment = collect_validation_environment(repository_root, toolchain)
        dependencies = collect_dependencies(repository_root)
        snapshot_issues = development_snapshot_issues(repository_root, snapshots)
        if snapshot_issues:
            raise ReleasePackageError(snapshot_issues)
        validation = ReleaseManifestValidation(
            strict_turtle_parsing=True,
            formal_metadata_validation=True,
            serialized_header_validation=True,
            governed_axiom_reconciliation=True,
            import_graph_validation=True,
            catalog_validation=True,
            checksum_validation=True,
            development_artifact_nonmutation=True,
            deterministic_package_rebuild=True,
            hermit_results=hermit,
        )
        manifest = build_release_manifest(
            release_identifier=context.release_identifier,
            release_date=context.release_date,
            git_tag=context.git_tag,
            source_commit=context.source_commit,
            repository_iri=metadata.publication.repository_iri,
            inputs=collect_inputs(
                repository_root,
                notes_relative,
                notes_bytes=notes_bytes,
            ),
            product_order=PRODUCT_ORDER,
            products=collect_product_records(rendered, metadata, context),
            dependencies=dependencies,
            validation_environment=environment,
            validation=validation,
            included_files=collect_included_files(package_dir),
        )
        manifest_bytes = canonical_manifest_bytes(manifest)
        (package_dir / "manifest.json").write_bytes(manifest_bytes)
        load_and_validate_release_manifest(package_dir / "manifest.json")
        sums = canonical_sha256sums_bytes(package_dir)
        (package_dir / "SHA256SUMS").write_bytes(sums)
        checksum_issues = validate_sha256sums_bytes(package_dir, sums)
        if checksum_issues:
            raise ReleasePackageError(checksum_issues)
        return AssembledReleasePackage(
            manifest=manifest,
            manifest_bytes=manifest_bytes,
            catalog_bytes=catalog,
            sha256sums_bytes=sums,
        )
    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(reasoning_root, ignore_errors=True)


def compare_complete_packages(
    first: Path,
    second: Path,
) -> tuple[ReleasePackageIssue, ...]:
    """Compare the normalized complete 13-file inventories of two package candidates."""

    issues: list[ReleasePackageIssue] = []
    observed: list[tuple[str, ...]] = []
    for package_dir in (first, second):
        paths = tuple(
            path.relative_to(package_dir).as_posix()
            for path in sorted(
                package_dir.rglob("*"),
                key=lambda value: value.relative_to(package_dir).as_posix(),
            )
            if path.is_file() and not path.is_symlink()
        )
        observed.append(paths)
    if observed[0] != PACKAGE_FILE_PATHS or observed[1] != PACKAGE_FILE_PATHS:
        issues.append(
            package_issue(
                "NONDETERMINISTIC_PACKAGE_REBUILD",
                "package",
                f"expected path set {PACKAGE_FILE_PATHS!r}; got {observed!r}",
            )
        )
        return tuple(issues)
    for relative in PACKAGE_FILE_PATHS:
        if (first / relative).read_bytes() != (second / relative).read_bytes():
            issues.append(
                package_issue(
                    "NONDETERMINISTIC_PACKAGE_REBUILD",
                    relative,
                    "complete package rebuild bytes differ",
                )
            )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def build_release_package(
    context: FormalReleaseContext,
    notes_source: Path,
    output_dir: Path,
    repository_root: Path = REPO_ROOT,
) -> ReleasePackageResult:
    validated_context = validate_formal_release_context(context)
    repository_root = repository_root.resolve()
    notes_source = Path(notes_source)
    output_dir = Path(output_dir)
    notes_relative = _validate_paths(validated_context, notes_source, output_dir, repository_root)
    notes_bytes = notes_source.read_bytes()
    note_issues = validate_release_notes_bytes(
        notes_bytes,
        template_bytes=(repository_root / "release-notes/TEMPLATE.md").read_bytes(),
    )
    if note_issues:
        raise ReleasePackageError(note_issues)
    snapshots = snapshot_development_outputs(repository_root)
    toolchain = resolve_validation_toolchain(repository_root)
    wrapper = Path(tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=output_dir.parent))
    first_parent = wrapper / "candidate-a"
    second_parent = wrapper / "candidate-b"
    first_parent.mkdir()
    second_parent.mkdir()
    package_dir = first_parent / validated_context.release_identifier
    comparison_dir = second_parent / validated_context.release_identifier
    published = False
    try:
        assembled = assemble_release_package(
            validated_context,
            notes_bytes,
            notes_relative,
            package_dir,
            repository_root,
            toolchain,
            snapshots,
        )
        assemble_release_package(
            validated_context,
            notes_bytes,
            notes_relative,
            comparison_dir,
            repository_root,
            toolchain,
            snapshots,
        )
        comparison_issues = compare_complete_packages(package_dir, comparison_dir)
        if comparison_issues:
            raise ReleasePackageError(comparison_issues)

        from check_release import validate_release_package

        package_issues = validate_release_package(
            package_dir,
            repository_root=repository_root,
            toolchain=toolchain,
        )
        if package_issues:
            raise ReleasePackageError(package_issues)
        snapshot_issues = development_snapshot_issues(repository_root, snapshots)
        if snapshot_issues:
            raise ReleasePackageError(snapshot_issues)
        os.replace(package_dir, output_dir)
        published = True
        final_issues = development_snapshot_issues(repository_root, snapshots)
        if final_issues:
            shutil.rmtree(output_dir)
            published = False
            raise ReleasePackageError(final_issues)
        file_hashes = tuple((path, _sha256(output_dir / path)) for path in PACKAGE_FILE_PATHS)
        return ReleasePackageResult(
            output_dir=output_dir,
            manifest=assembled.manifest,
            manifest_sha256=release_manifest_sha256(assembled.manifest_bytes),
            catalog_sha256=sha256_bytes(assembled.catalog_bytes),
            sha256sums_sha256=sha256_bytes(assembled.sha256sums_bytes),
            file_hashes=file_hashes,
        )
    except Exception:
        if published and output_dir.exists():
            shutil.rmtree(output_dir)
        raise
    finally:
        shutil.rmtree(wrapper, ignore_errors=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--release-date", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--git-tag", required=True)
    parser.add_argument("--notes", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        context = parse_formal_release_context(
            args.release_id,
            args.release_date,
            args.git_tag,
            args.source_commit,
        )
        result = build_release_package(context, args.notes, args.output_dir, REPO_ROOT)
    except Exception as exc:
        print(str(exc))
        return 1
    print(f"Release package: {result.output_dir}")
    print(f"Manifest SHA-256: {result.manifest_sha256}")
    print(f"Catalog SHA-256: {result.catalog_sha256}")
    print(f"SHA256SUMS SHA-256: {result.sha256sums_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
