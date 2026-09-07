#!/usr/bin/env python3
"""Load and validate the approved SOSA source-version authority."""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config/sosa-source-version.toml"

FULL_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SOURCE_IDENTITY = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

EXPECTED_REPOSITORY = "https://github.com/w3c/sdw-sosa-ssn"
EXPECTED_EDITION_LABEL = "Semantic Sensor Network Ontology - 2023 Edition"
EXPECTED_EDITION_VERSION_IRI = "http://www.w3.org/ns/sosa/2023/"
EXPECTED_W3C_TR_IRI = "https://www.w3.org/TR/vocab-ssn-2023/"
EXPECTED_DEVELOPMENT_ALIAS = "sosa-next"


@dataclass(frozen=True)
class SourceFile:
    local_path: str
    upstream_path: str
    sha256: str


@dataclass(frozen=True)
class SourceVersionAuthority:
    schema_version: int
    status: str
    source_identity: str
    development_alias: str
    edition_label: str
    edition_version_iri: str
    w3c_tr_iri: str
    upstream_repository: str
    upstream_commit: str
    upstream_commit_date: str
    source_files: tuple[SourceFile, ...]
    overlay_path: str
    overlay_sha256: str
    overlay_bound_upstream_commit: str
    overlay_purpose: str


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_exact_keys(
    value: dict[str, object],
    expected: set[str],
    label: str,
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(
            f"{label}: noncanonical keys; missing={missing}; extra={extra}"
        )


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{label}: expected nonempty string")
    return value


def _require_safe_relative_path(value: object, label: str) -> str:
    text = _require_string(value, label)
    file_path = Path(text)
    if (
        file_path.is_absolute()
        or ".." in file_path.parts
        or text.startswith("./")
        or "\\" in text
        or "//" in text
    ):
        raise RuntimeError(f"{label}: unsafe or noncanonical path {text!r}")
    if file_path.as_posix() != text:
        raise RuntimeError(f"{label}: noncanonical path {text!r}")
    return text


def load_source_version_authority(
    config_path: Path = CONFIG_PATH,
) -> SourceVersionAuthority:
    with config_path.open("rb") as handle:
        document = tomllib.load(handle)

    _require_exact_keys(
        document,
        {
            "schema_version",
            "status",
            "source_identity",
            "development_alias",
            "edition_label",
            "edition_version_iri",
            "w3c_tr_iri",
            "upstream_repository",
            "upstream_commit",
            "upstream_commit_date",
            "source_files",
            "local_overlay",
        },
        "document",
    )

    schema_version = document["schema_version"]
    if isinstance(schema_version, bool) or schema_version != 1:
        raise RuntimeError(
            f"schema_version: expected integer 1, got {schema_version!r}"
        )

    status = _require_string(document["status"], "status")
    if status != "approved":
        raise RuntimeError(f"status: expected 'approved', got {status!r}")

    upstream_commit = _require_string(
        document["upstream_commit"],
        "upstream_commit",
    )
    if FULL_GIT_SHA.fullmatch(upstream_commit) is None:
        raise RuntimeError(
            "upstream_commit: expected full lowercase 40-character Git SHA"
        )

    source_identity = _require_string(
        document["source_identity"],
        "source_identity",
    )
    if SOURCE_IDENTITY.fullmatch(source_identity) is None:
        raise RuntimeError(
            f"source_identity: noncanonical component {source_identity!r}"
        )

    expected_identity = f"sosa-2023-{upstream_commit}"
    if source_identity != expected_identity:
        raise RuntimeError(
            "source_identity: must use the complete approved upstream commit; "
            f"expected {expected_identity!r}, got {source_identity!r}"
        )

    development_alias = _require_string(
        document["development_alias"],
        "development_alias",
    )
    if development_alias != EXPECTED_DEVELOPMENT_ALIAS:
        raise RuntimeError(
            "development_alias: expected "
            f"{EXPECTED_DEVELOPMENT_ALIAS!r}, got {development_alias!r}"
        )

    edition_label = _require_string(
        document["edition_label"],
        "edition_label",
    )
    if edition_label != EXPECTED_EDITION_LABEL:
        raise RuntimeError(
            f"edition_label: expected {EXPECTED_EDITION_LABEL!r}"
        )

    edition_version_iri = _require_string(
        document["edition_version_iri"],
        "edition_version_iri",
    )
    if edition_version_iri != EXPECTED_EDITION_VERSION_IRI:
        raise RuntimeError(
            "edition_version_iri: expected "
            f"{EXPECTED_EDITION_VERSION_IRI!r}"
        )

    w3c_tr_iri = _require_string(
        document["w3c_tr_iri"],
        "w3c_tr_iri",
    )
    if w3c_tr_iri != EXPECTED_W3C_TR_IRI:
        raise RuntimeError(
            f"w3c_tr_iri: expected {EXPECTED_W3C_TR_IRI!r}"
        )

    upstream_repository = _require_string(
        document["upstream_repository"],
        "upstream_repository",
    )
    if upstream_repository != EXPECTED_REPOSITORY:
        raise RuntimeError(
            f"upstream_repository: expected {EXPECTED_REPOSITORY!r}"
        )

    upstream_commit_date = _require_string(
        document["upstream_commit_date"],
        "upstream_commit_date",
    )
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", upstream_commit_date) is None:
        raise RuntimeError(
            "upstream_commit_date: expected canonical YYYY-MM-DD"
        )

    raw_source_files = document["source_files"]
    if not isinstance(raw_source_files, list):
        raise RuntimeError("source_files: expected array of tables")
    if len(raw_source_files) != 8:
        raise RuntimeError(
            f"source_files: expected exactly 8 upstream files, got "
            f"{len(raw_source_files)}"
        )

    source_files: list[SourceFile] = []
    local_paths: set[str] = set()
    upstream_paths: set[str] = set()

    for index, raw_item in enumerate(raw_source_files):
        label = f"source_files[{index}]"
        if not isinstance(raw_item, dict):
            raise RuntimeError(f"{label}: expected table")
        _require_exact_keys(
            raw_item,
            {"local_path", "upstream_path", "sha256"},
            label,
        )

        local_path = _require_safe_relative_path(
            raw_item["local_path"],
            f"{label}.local_path",
        )
        upstream_path = _require_safe_relative_path(
            raw_item["upstream_path"],
            f"{label}.upstream_path",
        )
        digest = _require_string(
            raw_item["sha256"],
            f"{label}.sha256",
        )

        if not local_path.startswith("src/sosa-next/imports/"):
            raise RuntimeError(
                f"{label}.local_path: outside governed SOSA source directory"
            )
        if not local_path.endswith(".ttl"):
            raise RuntimeError(f"{label}.local_path: expected Turtle file")
        if not upstream_path.endswith(".ttl"):
            raise RuntimeError(f"{label}.upstream_path: expected Turtle file")
        if SHA256.fullmatch(digest) is None:
            raise RuntimeError(
                f"{label}.sha256: expected lowercase SHA-256"
            )
        if local_path in local_paths:
            raise RuntimeError(
                f"{label}.local_path: duplicate {local_path!r}"
            )
        if upstream_path in upstream_paths:
            raise RuntimeError(
                f"{label}.upstream_path: duplicate {upstream_path!r}"
            )

        local_paths.add(local_path)
        upstream_paths.add(upstream_path)
        source_files.append(
            SourceFile(
                local_path=local_path,
                upstream_path=upstream_path,
                sha256=digest,
            )
        )

    raw_overlay = document["local_overlay"]
    if not isinstance(raw_overlay, dict):
        raise RuntimeError("local_overlay: expected table")

    _require_exact_keys(
        raw_overlay,
        {
            "path",
            "sha256",
            "bound_upstream_commit",
            "purpose",
        },
        "local_overlay",
    )

    overlay_path = _require_safe_relative_path(
        raw_overlay["path"],
        "local_overlay.path",
    )
    overlay_sha256 = _require_string(
        raw_overlay["sha256"],
        "local_overlay.sha256",
    )
    overlay_bound_upstream_commit = _require_string(
        raw_overlay["bound_upstream_commit"],
        "local_overlay.bound_upstream_commit",
    )
    overlay_purpose = _require_string(
        raw_overlay["purpose"],
        "local_overlay.purpose",
    )

    if SHA256.fullmatch(overlay_sha256) is None:
        raise RuntimeError(
            "local_overlay.sha256: expected lowercase SHA-256"
        )
    if overlay_path in local_paths:
        raise RuntimeError(
            "local_overlay.path: overlay must remain separate from upstream files"
        )
    if overlay_bound_upstream_commit != upstream_commit:
        raise RuntimeError(
            "local_overlay.bound_upstream_commit: must equal upstream_commit"
        )

    return SourceVersionAuthority(
        schema_version=1,
        status=status,
        source_identity=source_identity,
        development_alias=development_alias,
        edition_label=edition_label,
        edition_version_iri=edition_version_iri,
        w3c_tr_iri=w3c_tr_iri,
        upstream_repository=upstream_repository,
        upstream_commit=upstream_commit,
        upstream_commit_date=upstream_commit_date,
        source_files=tuple(source_files),
        overlay_path=overlay_path,
        overlay_sha256=overlay_sha256,
        overlay_bound_upstream_commit=overlay_bound_upstream_commit,
        overlay_purpose=overlay_purpose,
    )


def validate_source_version_files(
    authority: SourceVersionAuthority,
    repo_root: Path = REPO_ROOT,
) -> dict[str, str]:
    expected = {
        item.local_path: item.sha256
        for item in authority.source_files
    }
    expected[authority.overlay_path] = authority.overlay_sha256

    actual: dict[str, str] = {}

    for relative_path, expected_digest in expected.items():
        file_path = repo_root / relative_path
        if not file_path.is_file() or file_path.is_symlink():
            raise RuntimeError(
                f"Required governed source file is missing or not regular: "
                f"{relative_path}"
            )

        actual_digest = sha256_file(file_path)
        actual[relative_path] = actual_digest

        if actual_digest != expected_digest:
            raise RuntimeError(
                f"SHA-256 mismatch for {relative_path}: "
                f"expected {expected_digest}, got {actual_digest}"
            )

    return actual
