#!/usr/bin/env python3
"""Load and validate governed publication identity and release metadata."""

from __future__ import annotations

import hashlib
import ipaddress
import re
import tomllib
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit


SCHEMA_VERSION = 2
PRODUCT_ORDER = (
    "integrated",
    "alignment_core",
    "strict_bfo_mapping",
    "bfo_projection",
    "cco_extension",
)
TOP_LEVEL_FIELDS = ("schema_version", "publication", "products")
PUBLICATION_FIELDS = (
    "project_title",
    "default_language",
    "release_iri_base",
    "license_iri",
    "repository_iri",
    "generated_warning",
    "development_status_property_iri",
    "development_status_iri",
)
PRODUCT_FIELDS = (
    "path",
    "stable_ontology_iri",
    "release_iri_suffix",
    "label",
    "description",
    "product_type_iri",
)
RELEASE_IDENTIFIER_PATTERN = re.compile(
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})(?:\.(?P<sequence>[1-9][0-9]*))?\Z"
)
GIT_TAG_PATTERN = re.compile(
    r"v(?P<release>[0-9]{4}-[0-9]{2}-[0-9]{2}(?:\.[1-9][0-9]*)?)\Z"
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class PublicationSettings:
    project_title: str
    default_language: str
    release_iri_base: str
    license_iri: str
    repository_iri: str
    generated_warning: str
    development_status_property_iri: str
    development_status_iri: str


@dataclass(frozen=True)
class ProductPublicationMetadata:
    key: str
    path: str
    stable_ontology_iri: str
    release_iri_suffix: str
    label: str
    description: str
    product_type_iri: str
    release_iri_base: str


# Compatibility name retained for existing generator and modular-product imports.
ProductMetadata = ProductPublicationMetadata


@dataclass(frozen=True)
class PublicationMetadata:
    schema_version: int
    publication: PublicationSettings
    products: tuple[ProductPublicationMetadata, ...]

    @property
    def release_iri_base(self) -> str:
        """Compatibility accessor for the schema-1 public API."""

        return self.publication.release_iri_base


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
    issues.extend(_text_form_issues(value, field))
    return value


def _text_form_issues(value: str, field: str) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    if unicodedata.normalize("NFC", value) != value:
        issues.append(_issue("NON_NFC_TEXT", field, "value must be Unicode NFC-normalized"))
    if any(unicodedata.category(character) == "Cc" for character in value):
        issues.append(
            _issue(
                "CONTROL_CHARACTER",
                field,
                "value must not contain control characters or span multiple lines",
            )
        )
    return tuple(issues)


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


def _absolute_http_iri_issue(
    value: str,
    *,
    allow_trailing_slash: bool,
    allow_fragment: bool = False,
) -> str | None:
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
    if parsed.username is not None or parsed.password is not None:
        return "must not contain user information"
    if not _valid_hostname(hostname):
        return "must include a nonempty valid hostname"
    if parsed.query or "?" in value:
        return "must not contain a query string"
    if (parsed.fragment or "#" in value) and not allow_fragment:
        return "must not contain a fragment"
    if not allow_trailing_slash and parsed.path.endswith("/"):
        return "must not end with '/'"
    if any(segment in {".", ".."} for segment in parsed.path.split("/")):
        return "must not contain '.' or '..' path segments"
    return None


def _duplicate_issues(
    products: tuple[ProductPublicationMetadata, ...],
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


def _iri_validation(
    value: str,
    field: str,
    code: str,
    issues: list[ValidationIssue],
    *,
    allow_trailing_slash: bool,
    allow_fragment: bool = False,
) -> None:
    problem = _absolute_http_iri_issue(
        value,
        allow_trailing_slash=allow_trailing_slash,
        allow_fragment=allow_fragment,
    )
    if problem:
        issues.append(_issue(code, field, problem))


def validate_metadata(metadata: PublicationMetadata) -> tuple[ValidationIssue, ...]:
    """Return semantic issues in deterministic policy order."""

    issues: list[ValidationIssue] = []
    if type(metadata.schema_version) is not int:
        issues.append(_issue("WRONG_TYPE", "schema_version", "expected integer 2"))
    elif metadata.schema_version != SCHEMA_VERSION:
        issues.append(_issue("SCHEMA_VERSION", "schema_version", "expected schema version 2"))

    publication = metadata.publication
    for attribute in PUBLICATION_FIELDS:
        value = getattr(publication, attribute)
        if not isinstance(value, str):
            issues.append(_issue("WRONG_TYPE", f"publication.{attribute}", "expected a string"))
        elif not value or not value.strip():
            issues.append(_issue("EMPTY_STRING", f"publication.{attribute}", "value must be nonempty"))
        else:
            issues.extend(_text_form_issues(value, f"publication.{attribute}"))
    if publication.default_language != "en":
        issues.append(
            _issue(
                "UNSUPPORTED_LANGUAGE",
                "publication.default_language",
                "schema version 2 requires the exact language code 'en'",
            )
        )
    if (
        isinstance(publication.generated_warning, str)
        and publication.generated_warning.strip()
        and publication.generated_warning
        != " ".join(publication.generated_warning.split())
    ):
        issues.append(
            _issue(
                "NONCANONICAL_WHITESPACE",
                "publication.generated_warning",
                "warning must be one logical literal with normalized whitespace",
            )
        )
    publication_iris = (
        (
            publication.release_iri_base,
            "publication.release_iri_base",
            "INVALID_RELEASE_BASE",
            False,
            False,
        ),
        (
            publication.license_iri,
            "publication.license_iri",
            "INVALID_LICENSE_IRI",
            True,
            False,
        ),
        (
            publication.repository_iri,
            "publication.repository_iri",
            "INVALID_REPOSITORY_IRI",
            False,
            False,
        ),
        (
            publication.development_status_property_iri,
            "publication.development_status_property_iri",
            "INVALID_STATUS_PROPERTY_IRI",
            False,
            True,
        ),
        (
            publication.development_status_iri,
            "publication.development_status_iri",
            "INVALID_STATUS_IRI",
            False,
            False,
        ),
    )
    for value, field, code, allow_trailing_slash, allow_fragment in publication_iris:
        if isinstance(value, str) and value.strip():
            _iri_validation(
                value,
                field,
                code,
                issues,
                allow_trailing_slash=allow_trailing_slash,
                allow_fragment=allow_fragment,
            )

    keys = tuple(product.key for product in metadata.products)
    if set(keys) != set(PRODUCT_ORDER) or len(keys) != len(PRODUCT_ORDER):
        issues.append(
            _issue("PRODUCT_SET", "products", "expected exactly: " + ", ".join(PRODUCT_ORDER))
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
            else:
                issues.extend(_text_form_issues(value, f"{prefix}.{attribute}"))
        if product.release_iri_base != publication.release_iri_base:
            issues.append(
                _issue(
                    "RELEASE_BASE_MISMATCH",
                    f"{prefix}.release_iri_base",
                    "product release base differs from publication release base",
                )
            )
        if isinstance(product.path, str) and product.path.strip():
            problem = _path_issue(product.path)
            if problem:
                issues.append(_issue("UNSAFE_PRODUCT_PATH", f"{prefix}.path", problem))
        if isinstance(product.release_iri_suffix, str) and product.release_iri_suffix.strip():
            problem = _suffix_issue(product.release_iri_suffix)
            if problem:
                issues.append(
                    _issue("UNSAFE_RELEASE_SUFFIX", f"{prefix}.release_iri_suffix", problem)
                )
        if isinstance(product.stable_ontology_iri, str) and product.stable_ontology_iri.strip():
            _iri_validation(
                product.stable_ontology_iri,
                f"{prefix}.stable_ontology_iri",
                "INVALID_STABLE_IRI",
                issues,
                allow_trailing_slash=True,
            )
        if isinstance(product.product_type_iri, str) and product.product_type_iri.strip():
            _iri_validation(
                product.product_type_iri,
                f"{prefix}.product_type_iri",
                "INVALID_PRODUCT_TYPE_IRI",
                issues,
                allow_trailing_slash=False,
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
    issues.extend(
        _duplicate_issues(
            metadata.products,
            "product_type_iri",
            "DUPLICATE_PRODUCT_TYPE_IRI",
            "product-type IRI",
        )
    )
    return tuple(issues)


def load_metadata(path: str | Path) -> PublicationMetadata:
    """Load UTF-8 TOML and return validated schema-2 metadata."""

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
            issues.append(_issue("WRONG_TYPE", "schema_version", "expected integer 2"))
    elif schema_version != SCHEMA_VERSION:
        issues.append(_issue("SCHEMA_VERSION", "schema_version", "expected schema version 2"))

    publication_table = (
        _table(top["publication"], "publication", PUBLICATION_FIELDS, issues)
        if "publication" in top
        else {}
    )
    publication_values = {
        field: _string(publication_table[field], f"publication.{field}", issues)
        for field in PUBLICATION_FIELDS
        if field in publication_table
    }

    products_table = (
        _table(top["products"], "products", PRODUCT_ORDER, issues)
        if "products" in top
        else {}
    )
    if set(products_table) == set(PRODUCT_ORDER) and tuple(products_table) != PRODUCT_ORDER:
        issues.append(_issue("PRODUCT_ORDER", "products", "products are not in canonical order"))

    release_base = publication_values.get("release_iri_base")
    products: list[ProductPublicationMetadata] = []
    for key in PRODUCT_ORDER:
        if key not in products_table:
            continue
        product_table = _table(
            products_table[key],
            f"products.{key}",
            PRODUCT_FIELDS,
            issues,
        )
        values = {
            field: _string(product_table[field], f"products.{key}.{field}", issues)
            for field in PRODUCT_FIELDS
            if field in product_table
        }
        if all(values.get(field) is not None for field in PRODUCT_FIELDS) and release_base:
            products.append(
                ProductPublicationMetadata(
                    key=key,
                    path=values["path"],
                    stable_ontology_iri=values["stable_ontology_iri"],
                    release_iri_suffix=values["release_iri_suffix"],
                    label=values["label"],
                    description=values["description"],
                    product_type_iri=values["product_type_iri"],
                    release_iri_base=release_base,
                )
            )

    if issues:
        raise PublicationMetadataError(issues)

    publication = PublicationSettings(
        **{field: publication_values[field] for field in PUBLICATION_FIELDS}
    )
    metadata = PublicationMetadata(
        schema_version=schema_version,
        publication=publication,
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
