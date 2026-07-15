#!/usr/bin/env python3
"""Load and validate governed publication identity and release metadata."""

from __future__ import annotations

import hashlib
import ipaddress
import re
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit


PRODUCT_ORDER = (
    "integrated",
    "alignment_core",
    "strict_bfo_mapping",
    "bfo_projection",
    "cco_extension",
)
TOP_LEVEL_FIELDS = ("schema_version", "publication", "products")
PUBLICATION_FIELDS = ("release_iri_base",)
PRODUCT_FIELDS = ("path", "stable_ontology_iri", "release_iri_suffix")
RELEASE_IDENTIFIER_PATTERN = re.compile(
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})(?:\.(?P<sequence>[1-9][0-9]*))?\Z"
)
GIT_TAG_PATTERN = re.compile(
    r"v(?P<release>[0-9]{4}-[0-9]{2}-[0-9]{2}(?:\.[1-9][0-9]*)?)\Z"
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class ProductMetadata:
    key: str
    path: str
    stable_ontology_iri: str
    release_iri_suffix: str
    release_iri_base: str


@dataclass(frozen=True)
class PublicationMetadata:
    schema_version: int
    release_iri_base: str
    products: tuple[ProductMetadata, ...]


@dataclass(frozen=True)
class ReleaseContext:
    release_identifier: str
    git_tag: str


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    field: str
    message: str


class PublicationMetadataError(ValueError):
    """One or more deterministic publication-metadata validation failures."""

    def __init__(self, issues: tuple[ValidationIssue, ...] | list[ValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(format_issue(issue) for issue in self.issues))


def format_issue(issue: ValidationIssue) -> str:
    return f"ERROR [{issue.code}] {issue.field}: {issue.message}"


def _issue(code: str, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def _table(
    value: object,
    field: str,
    expected_fields: tuple[str, ...],
    issues: list[ValidationIssue],
) -> dict[str, object]:
    if not isinstance(value, dict):
        issues.append(_issue("WRONG_TYPE", field, "expected a TOML table"))
        return {}
    for name in expected_fields:
        if name not in value:
            issues.append(_issue("MISSING_FIELD", f"{field}.{name}", "required field is missing"))
    for name in sorted(set(value) - set(expected_fields)):
        issues.append(_issue("UNKNOWN_FIELD", f"{field}.{name}", "field is not permitted"))
    return value


def _string(value: object, field: str, issues: list[ValidationIssue]) -> str | None:
    if not isinstance(value, str):
        issues.append(_issue("WRONG_TYPE", field, "expected a string"))
        return None
    if not value or not value.strip():
        issues.append(_issue("EMPTY_STRING", field, "value must be nonempty"))
        return None
    return value


def _path_issue(value: str) -> str | None:
    if PureWindowsPath(value).drive:
        return "must not contain a Windows drive or UNC path"
    if "\\" in value:
        return "must use POSIX '/' separators and must not contain backslashes"
    if "?" in value or "#" in value:
        return "must not contain a query string or fragment"
    path = PurePosixPath(value)
    if path.is_absolute():
        return "must be repository-relative"
    segments = value.split("/")
    if ".." in segments:
        return "must not contain '..' path segments"
    if "" in segments or "." in segments or path.as_posix() != value:
        return "must be a normalized POSIX path without empty or '.' segments"
    return None


def _suffix_issue(value: str) -> str | None:
    if value.startswith("/") or value.endswith("/"):
        return "must be relative and must not begin or end with '/'"
    if "\\" in value:
        return "must use POSIX '/' separators and must not contain backslashes"
    if "?" in value or "#" in value:
        return "must not contain a query string or fragment"
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return "must be a relative IRI path suffix"
    path = PurePosixPath(value)
    segments = value.split("/")
    if ".." in segments:
        return "must not contain '..' segments"
    if "" in segments or "." in segments or path.is_absolute() or path.as_posix() != value:
        return "must be a normalized POSIX suffix without empty or '.' segments"
    return None


def _valid_hostname(value: str | None) -> bool:
    if not value:
        return False
    if ":" in value:
        try:
            ipaddress.ip_address(value)
        except ValueError:
            return False
        return True
    try:
        hostname = value.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    if hostname.endswith("."):
        hostname = hostname[:-1]
    if not hostname or len(hostname) > 253:
        return False
    label_pattern = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")
    return all(label_pattern.fullmatch(label) is not None for label in hostname.split("."))


def _absolute_http_iri_issue(value: str, *, allow_trailing_slash: bool) -> str | None:
    if any(character.isspace() for character in value):
        return "must not contain whitespace"
    if "\\" in value:
        return "must not contain backslashes"
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return "must be a valid absolute HTTP IRI"
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "must be an absolute HTTP IRI"
    if not _valid_hostname(hostname):
        return "must include a nonempty valid hostname"
    if "?" in value or "#" in value:
        return "must not contain a query string or fragment"
    if not allow_trailing_slash and value.endswith("/"):
        return "must not end with '/'"
    return None


def _duplicate_issues(
    products: tuple[ProductMetadata, ...],
    attribute: str,
    code: str,
    label: str,
) -> list[ValidationIssue]:
    first_by_value: dict[str, str] = {}
    issues: list[ValidationIssue] = []
    for product in products:
        value = getattr(product, attribute)
        if not isinstance(value, str):
            continue
        first_key = first_by_value.get(value)
        if first_key is None:
            first_by_value[value] = product.key
            continue
        issues.append(
            _issue(
                code,
                f"products.{product.key}.{attribute}",
                f"duplicates {label} declared for products.{first_key}",
            )
        )
    return issues


def validate_metadata(metadata: PublicationMetadata) -> tuple[ValidationIssue, ...]:
    """Return semantic issues in deterministic policy order."""

    issues: list[ValidationIssue] = []
    if type(metadata.schema_version) is not int:
        issues.append(_issue("WRONG_TYPE", "schema_version", "expected integer 1"))
    elif metadata.schema_version != 1:
        issues.append(_issue("SCHEMA_VERSION", "schema_version", "expected schema version 1"))

    release_base = metadata.release_iri_base
    if not isinstance(release_base, str):
        issues.append(_issue("WRONG_TYPE", "publication.release_iri_base", "expected a string"))
    elif not release_base or not release_base.strip():
        issues.append(_issue("EMPTY_STRING", "publication.release_iri_base", "value must be nonempty"))
    else:
        problem = _absolute_http_iri_issue(release_base, allow_trailing_slash=False)
        if problem:
            issues.append(_issue("INVALID_RELEASE_BASE", "publication.release_iri_base", problem))

    keys = tuple(product.key for product in metadata.products)
    if set(keys) != set(PRODUCT_ORDER) or len(keys) != len(PRODUCT_ORDER):
        issues.append(
            _issue(
                "PRODUCT_SET",
                "products",
                "expected exactly: " + ", ".join(PRODUCT_ORDER),
            )
        )
    elif keys != PRODUCT_ORDER:
        issues.append(_issue("PRODUCT_ORDER", "products", "products are not in canonical order"))

    for product in metadata.products:
        prefix = f"products.{product.key}"
        for attribute in PRODUCT_FIELDS:
            value = getattr(product, attribute)
            if not isinstance(value, str):
                issues.append(_issue("WRONG_TYPE", f"{prefix}.{attribute}", "expected a string"))
            elif not value or not value.strip():
                issues.append(_issue("EMPTY_STRING", f"{prefix}.{attribute}", "value must be nonempty"))
        if isinstance(product.path, str) and product.path.strip():
            problem = _path_issue(product.path)
            if problem:
                issues.append(_issue("UNSAFE_PRODUCT_PATH", f"{prefix}.path", problem))
        if isinstance(product.stable_ontology_iri, str) and product.stable_ontology_iri.strip():
            problem = _absolute_http_iri_issue(
                product.stable_ontology_iri,
                allow_trailing_slash=True,
            )
            if problem:
                issues.append(_issue("INVALID_STABLE_IRI", f"{prefix}.stable_ontology_iri", problem))
        if isinstance(product.release_iri_suffix, str) and product.release_iri_suffix.strip():
            problem = _suffix_issue(product.release_iri_suffix)
            if problem:
                issues.append(_issue("UNSAFE_RELEASE_SUFFIX", f"{prefix}.release_iri_suffix", problem))
        if product.release_iri_base != metadata.release_iri_base:
            issues.append(
                _issue(
                    "RELEASE_BASE_MISMATCH",
                    f"{prefix}.release_iri_base",
                    "product release base differs from publication release base",
                )
            )

    issues.extend(_duplicate_issues(metadata.products, "path", "DUPLICATE_PATH", "path"))
    issues.extend(
        _duplicate_issues(
            metadata.products,
            "stable_ontology_iri",
            "DUPLICATE_STABLE_IRI",
            "stable ontology IRI",
        )
    )
    issues.extend(
        _duplicate_issues(
            metadata.products,
            "release_iri_suffix",
            "DUPLICATE_RELEASE_SUFFIX",
            "release IRI suffix",
        )
    )
    return tuple(issues)


def load_metadata(path: str | Path) -> PublicationMetadata:
    """Load UTF-8 TOML and return validated metadata in canonical order."""

    source = Path(path)
    try:
        with source.open("rb") as handle:
            raw = tomllib.load(handle)
    except OSError as exc:
        raise PublicationMetadataError(
            [_issue("METADATA_IO", str(source), f"cannot read metadata: {exc}")]
        ) from exc
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise PublicationMetadataError(
            [_issue("TOML_PARSE", str(source), f"cannot parse UTF-8 TOML: {exc}")]
        ) from exc

    issues: list[ValidationIssue] = []
    top = _table(raw, "metadata", TOP_LEVEL_FIELDS, issues)

    schema_version = top.get("schema_version")
    if type(schema_version) is not int:
        if "schema_version" in top:
            issues.append(_issue("WRONG_TYPE", "schema_version", "expected integer 1"))
    elif schema_version != 1:
        issues.append(_issue("SCHEMA_VERSION", "schema_version", "expected schema version 1"))

    publication = (
        _table(top["publication"], "publication", PUBLICATION_FIELDS, issues)
        if "publication" in top
        else {}
    )
    release_base = (
        _string(
            publication["release_iri_base"],
            "publication.release_iri_base",
            issues,
        )
        if "release_iri_base" in publication
        else None
    )

    products_table = (
        _table(top["products"], "products", PRODUCT_ORDER, issues)
        if "products" in top
        else {}
    )
    products: list[ProductMetadata] = []
    for key in PRODUCT_ORDER:
        if key not in products_table:
            continue
        product_table = _table(
            products_table[key],
            f"products.{key}",
            PRODUCT_FIELDS,
            issues,
        )
        path_value = (
            _string(product_table["path"], f"products.{key}.path", issues)
            if "path" in product_table
            else None
        )
        stable_iri = (
            _string(
                product_table["stable_ontology_iri"],
                f"products.{key}.stable_ontology_iri",
                issues,
            )
            if "stable_ontology_iri" in product_table
            else None
        )
        suffix = (
            _string(
                product_table["release_iri_suffix"],
                f"products.{key}.release_iri_suffix",
                issues,
            )
            if "release_iri_suffix" in product_table
            else None
        )
        if path_value is not None and stable_iri is not None and suffix is not None and release_base:
            products.append(
                ProductMetadata(
                    key=key,
                    path=path_value,
                    stable_ontology_iri=stable_iri,
                    release_iri_suffix=suffix,
                    release_iri_base=release_base,
                )
            )

    if issues:
        raise PublicationMetadataError(issues)

    metadata = PublicationMetadata(
        schema_version=schema_version,
        release_iri_base=release_base,
        products=tuple(products),
    )
    semantic_issues = validate_metadata(metadata)
    if semantic_issues:
        raise PublicationMetadataError(semantic_issues)
    return metadata


def validate_release_identifier(value: str) -> str:
    """Validate and return a canonical date-based release identifier."""

    if not isinstance(value, str):
        raise PublicationMetadataError(
            [_issue("RELEASE_ID_FORMAT", "release_id", "expected YYYY-MM-DD or YYYY-MM-DD.N")]
        )
    match = RELEASE_IDENTIFIER_PATTERN.fullmatch(value)
    if match is None:
        raise PublicationMetadataError(
            [_issue("RELEASE_ID_FORMAT", "release_id", "expected YYYY-MM-DD or YYYY-MM-DD.N")]
        )
    try:
        parsed_date = date.fromisoformat(match.group("date"))
    except ValueError as exc:
        raise PublicationMetadataError(
            [_issue("RELEASE_DATE_INVALID", "release_id", f"invalid calendar date: {match.group('date')}")]
        ) from exc
    if parsed_date.isoformat() != match.group("date"):
        raise PublicationMetadataError(
            [_issue("RELEASE_ID_FORMAT", "release_id", "date must be zero-padded YYYY-MM-DD")]
        )
    return value


def validate_release_context(release_id: str, git_tag: str) -> ReleaseContext:
    """Validate a release identifier and its supplied intended Git tag."""

    release_identifier = validate_release_identifier(release_id)
    tag_match = GIT_TAG_PATTERN.fullmatch(git_tag) if isinstance(git_tag, str) else None
    if tag_match is None:
        raise PublicationMetadataError(
            [_issue("GIT_TAG_FORMAT", "git_tag", "expected v<release-id>")]
        )
    try:
        validate_release_identifier(tag_match.group("release"))
    except PublicationMetadataError as exc:
        raise PublicationMetadataError(
            [_issue("GIT_TAG_FORMAT", "git_tag", "expected v<release-id>")]
        ) from exc
    expected = f"v{release_identifier}"
    if git_tag != expected:
        raise PublicationMetadataError(
            [_issue("RELEASE_TAG_MISMATCH", "git_tag", f"expected {expected}, got {git_tag}")]
        )
    return ReleaseContext(release_identifier=release_identifier, git_tag=git_tag)


def build_version_iri(product: ProductMetadata, release_id: str) -> str:
    """Build the canonical immutable version IRI for one product."""

    release_identifier = validate_release_identifier(release_id)
    return f"{product.release_iri_base}/{release_identifier}/{product.release_iri_suffix}"


def validate_version_iri(product: ProductMetadata, release_id: str, observed_iri: str) -> None:
    """Require an observed version IRI to match canonical construction."""

    expected = build_version_iri(product, release_id)
    if observed_iri != expected:
        raise PublicationMetadataError(
            [
                _issue(
                    "VERSION_IRI_MISMATCH",
                    f"products.{product.key}.version_iri",
                    f"expected {expected}, got {observed_iri}",
                )
            ]
        )


def is_sha256(value: object) -> bool:
    """Return whether value is exactly 64 lowercase hexadecimal characters."""

    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def sha256_file(path: str | Path) -> str:
    """Calculate a file SHA-256 using bounded-memory streaming reads."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
