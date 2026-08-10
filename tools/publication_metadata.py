#!/usr/bin/env python3
"""Load and validate governed publication identity and release metadata."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import tomllib
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit

from rdflib import Graph, Literal, RDF, RDFS, OWL, URIRef

from release_context import (
    FormalReleaseContext,
    FormalReleaseContextError,
    parse_formal_release_context,
    validate_formal_release_context,
    validate_release_identifier as validate_context_release_identifier,
)


SCHEMA_VERSION = 4
PRODUCT_ORDER = (
    "integrated",
    "alignment_core",
    "strict_bfo_mapping",
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
    "formal_release_status_iri",
)
PRODUCT_FIELDS = (
    "path",
    "stable_ontology_iri",
    "release_iri_suffix",
    "label",
    "description",
    "product_type_iri",
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
LANGUAGE_LITERAL = "language_literal"
PLAIN_LITERAL = "plain_literal"
TYPED_LITERAL = "typed_literal"
IRI_OBJECT = "iri"
RDF_TYPE_IRI = str(RDF.type)
OWL_ONTOLOGY_IRI = str(OWL.Ontology)
OWL_IMPORTS_IRI = str(OWL.imports)
DCTERMS_NAMESPACE = "http://purl.org/dc/terms/"
ADMS_NAMESPACE = "http://www.w3.org/ns/adms#"
XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema#"
METADATA_PREFIXES = (
    ("adms", ADMS_NAMESPACE),
    ("dcterms", DCTERMS_NAMESPACE),
)
METADATA_PREDICATE_QNAMES = {
    str(RDFS.label): "rdfs:label",
    DCTERMS_NAMESPACE + "description": "dcterms:description",
    DCTERMS_NAMESPACE + "type": "dcterms:type",
    ADMS_NAMESPACE + "status": "adms:status",
    DCTERMS_NAMESPACE + "license": "dcterms:license",
    str(RDFS.seeAlso): "rdfs:seeAlso",
    str(RDFS.comment): "rdfs:comment",
    str(OWL.versionIRI): "owl:versionIRI",
    str(OWL.versionInfo): "owl:versionInfo",
    DCTERMS_NAMESPACE + "issued": "dcterms:issued",
}
RELEASE_ONLY_PREDICATES = frozenset(
    {
        str(OWL.versionIRI),
        str(OWL.versionInfo),
        DCTERMS_NAMESPACE + "issued",
    }
)
INTEGRATED_EXTERNAL_IMPORTS = (
    "http://www.w3.org/ns/sosa/sampling/",
    "http://www.w3.org/ns/ssn/",
    "http://www.w3.org/ns/ssn/systems/",
    "https://www.commoncoreontologies.org/2024-11-06/CommonCoreOntologiesMerged",
)


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
    formal_release_status_iri: str


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
class ValidationIssue:
    code: str
    field: str
    message: str


@dataclass(frozen=True)
class OntologyMetadataTriple:
    """One ordered governed ontology annotation for deterministic emission."""

    product_key: str
    ontology_iri: str
    predicate_iri: str
    object_kind: str
    value: str
    language: str | None = None
    datatype_iri: str | None = None

    @property
    def predicate_turtle(self) -> str:
        return METADATA_PREDICATE_QNAMES.get(
            self.predicate_iri,
            f"<{self.predicate_iri}>",
        )

    @property
    def object_turtle(self) -> str:
        if self.object_kind == IRI_OBJECT:
            return f"<{self.value}>"
        if self.object_kind == LANGUAGE_LITERAL and self.language is not None:
            return json.dumps(self.value, ensure_ascii=False) + f"@{self.language}"
        if self.object_kind == PLAIN_LITERAL:
            return json.dumps(self.value, ensure_ascii=False)
        if self.object_kind == TYPED_LITERAL and self.datatype_iri == XSD_NAMESPACE + "date":
            return json.dumps(self.value, ensure_ascii=False) + "^^xsd:date"
        raise ValueError(f"unsupported ontology metadata object kind {self.object_kind!r}")


class PublicationMetadataError(ValueError):
    """One or more deterministic publication-metadata validation failures."""

    def __init__(self, issues: tuple[ValidationIssue, ...] | list[ValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(format_issue(issue) for issue in self.issues))


def format_issue(issue: ValidationIssue) -> str:
    return f"ERROR [{issue.code}] {issue.field}: {issue.message}"


def _issue(code: str, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def _product(metadata: PublicationMetadata, product_key: str) -> ProductPublicationMetadata:
    for product in metadata.products:
        if product.key == product_key:
            return product
    raise PublicationMetadataError(
        [_issue("UNKNOWN_PRODUCT", f"products.{product_key}", "product is not governed")]
    )


def release_version_iri(
    metadata: PublicationMetadata,
    product_key: str,
    context: FormalReleaseContext,
) -> str:
    """Return one governed immutable product version IRI."""

    validated = validate_formal_release_context(context)
    product = _product(metadata, product_key)
    return (
        f"{metadata.publication.release_iri_base}/"
        f"{validated.release_identifier}/{product.release_iri_suffix}"
    )


def release_project_imports(
    metadata: PublicationMetadata,
    product_key: str,
    context: FormalReleaseContext,
) -> tuple[str, ...]:
    """Return the exact formal import list without stable project imports."""

    validate_formal_release_context(context)
    _product(metadata, product_key)
    if product_key == "integrated":
        return INTEGRATED_EXTERNAL_IMPORTS
    if product_key == "alignment_core":
        return ()
    if product_key == "strict_bfo_mapping":
        return (release_version_iri(metadata, "alignment_core", context),)
    if product_key == "cco_extension":
        return (release_version_iri(metadata, "strict_bfo_mapping", context),)
    raise PublicationMetadataError(
        [_issue("UNKNOWN_PRODUCT", f"products.{product_key}", "product is not governed")]
    )


def ontology_metadata_triples(
    metadata: PublicationMetadata,
    product_key: str,
    context: FormalReleaseContext | None = None,
) -> tuple[OntologyMetadataTriple, ...]:
    """Return exact development or formal annotations in governed order."""

    product = _product(metadata, product_key)
    publication = metadata.publication
    subject = product.stable_ontology_iri
    language = publication.default_language
    if context is not None:
        validate_formal_release_context(context)
    static = (
        OntologyMetadataTriple(
            product_key,
            subject,
            str(RDFS.label),
            LANGUAGE_LITERAL,
            product.label,
            language,
        ),
        OntologyMetadataTriple(
            product_key,
            subject,
            DCTERMS_NAMESPACE + "description",
            LANGUAGE_LITERAL,
            product.description,
            language,
        ),
        OntologyMetadataTriple(
            product_key,
            subject,
            DCTERMS_NAMESPACE + "type",
            IRI_OBJECT,
            product.product_type_iri,
        ),
        OntologyMetadataTriple(
            product_key,
            subject,
            publication.development_status_property_iri,
            IRI_OBJECT,
            publication.development_status_iri
            if context is None
            else publication.formal_release_status_iri,
        ),
        OntologyMetadataTriple(
            product_key,
            subject,
            DCTERMS_NAMESPACE + "license",
            IRI_OBJECT,
            publication.license_iri,
        ),
        OntologyMetadataTriple(
            product_key,
            subject,
            str(RDFS.seeAlso),
            IRI_OBJECT,
            publication.repository_iri,
        ),
        OntologyMetadataTriple(
            product_key,
            subject,
            str(RDFS.comment),
            LANGUAGE_LITERAL,
            publication.generated_warning,
            language,
        ),
    )
    if context is None:
        return static
    return (
        *static,
        OntologyMetadataTriple(
            product_key,
            subject,
            str(OWL.versionIRI),
            IRI_OBJECT,
            release_version_iri(metadata, product_key, context),
        ),
        OntologyMetadataTriple(
            product_key,
            subject,
            str(OWL.versionInfo),
            PLAIN_LITERAL,
            context.release_identifier,
        ),
        OntologyMetadataTriple(
            product_key,
            subject,
            DCTERMS_NAMESPACE + "issued",
            TYPED_LITERAL,
            context.release_date,
            datatype_iri=XSD_NAMESPACE + "date",
        ),
    )


def ontology_metadata_rdf_triples(
    metadata: PublicationMetadata,
    product_key: str,
    context: FormalReleaseContext | None = None,
) -> tuple[tuple[URIRef, URIRef, URIRef | Literal], ...]:
    """Convert governed metadata to immutable RDF terms without changing order."""

    converted: list[tuple[URIRef, URIRef, URIRef | Literal]] = []
    for value in ontology_metadata_triples(metadata, product_key, context):
        target: URIRef | Literal
        if value.object_kind == IRI_OBJECT:
            target = URIRef(value.value)
        elif value.object_kind == TYPED_LITERAL:
            target = Literal(value.value, datatype=URIRef(value.datatype_iri))
        elif value.object_kind == PLAIN_LITERAL:
            target = Literal(value.value)
        else:
            target = Literal(value.value, lang=value.language)
        converted.append(
            (URIRef(value.ontology_iri), URIRef(value.predicate_iri), target)
        )
    return tuple(converted)


def canonical_ontology_prefixes(
    prefixes: tuple[tuple[str, str], ...],
    context: FormalReleaseContext | None = None,
) -> tuple[tuple[str, str], ...]:
    """Return canonical prefixes, inserting formal xsd after rdfs."""

    if context is None:
        return prefixes
    validate_formal_release_context(context)
    without_xsd = tuple(value for value in prefixes if value[0] != "xsd")
    if len(without_xsd) != len(prefixes):
        supplied = tuple(namespace for prefix, namespace in prefixes if prefix == "xsd")
        if supplied != (XSD_NAMESPACE,):
            raise PublicationMetadataError(
                [_issue("INVALID_XSD_PREFIX", "ontology_prefixes.xsd", "expected XML Schema namespace")]
            )
    result: list[tuple[str, str]] = []
    inserted = False
    for value in without_xsd:
        result.append(value)
        if value[0] == "rdfs":
            result.append(("xsd", XSD_NAMESPACE))
            inserted = True
    if not inserted:
        raise PublicationMetadataError(
            [_issue("MISSING_RDFS_PREFIX", "ontology_prefixes", "formal rendering requires rdfs")]
        )
    return tuple(result)


def render_ontology_header_bytes(
    metadata: PublicationMetadata,
    product_key: str,
    imports: tuple[str, ...],
    *,
    generated_notice: str,
    prefixes: tuple[tuple[str, str], ...],
    import_turtle_terms: tuple[str, ...] | None = None,
    context: FormalReleaseContext | None = None,
) -> bytes:
    """Render the canonical generated preamble and ontology statement."""

    product = _product(metadata, product_key)
    if import_turtle_terms is None:
        import_turtle_terms = tuple(f"<{value}>" for value in imports)
    if len(import_turtle_terms) != len(imports):
        raise PublicationMetadataError(
            [
                _issue(
                    "IMPORT_RENDERING_MISMATCH",
                    f"products.{product_key}.imports",
                    "each governed import must have exactly one Turtle rendering",
                )
            ]
        )

    canonical_prefixes = canonical_ontology_prefixes(prefixes, context)
    lines = [generated_notice, ""]
    lines.extend(
        f"@prefix {prefix}: <{namespace}> ." for prefix, namespace in canonical_prefixes
    )
    lines.extend(["", f"<{product.stable_ontology_iri}> a owl:Ontology ;"])
    for value in ontology_metadata_triples(metadata, product_key, context):
        lines.append(f"    {value.predicate_turtle} {value.object_turtle} ;")

    if not import_turtle_terms:
        lines[-1] = lines[-1][:-2] + " ."
    elif len(import_turtle_terms) == 1:
        lines.append(f"    owl:imports {import_turtle_terms[0]} .")
    else:
        lines.append(f"    owl:imports {import_turtle_terms[0]},")
        lines.extend(f"        {value}," for value in import_turtle_terms[1:-1])
        lines.append(f"        {import_turtle_terms[-1]} .")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def validate_serialized_ontology_header(
    serialized_bytes: bytes,
    metadata: PublicationMetadata,
    product_key: str,
    expected_imports: tuple[str, ...],
    *,
    generated_notice: str,
    prefixes: tuple[tuple[str, str], ...],
    import_turtle_terms: tuple[str, ...] | None = None,
    mode: str = "development",
    context: FormalReleaseContext | None = None,
) -> tuple[ValidationIssue, ...]:
    """Strictly parse and validate graph semantics plus canonical header bytes."""

    try:
        text = serialized_bytes.decode("utf-8")
        graph = Graph().parse(data=text, format="turtle")
    except Exception as exc:
        return (
            _issue(
                "TURTLE_PARSE",
                f"products.{product_key}.serialized_ontology",
                f"cannot strictly parse UTF-8 Turtle: {type(exc).__name__}: {exc}",
            ),
        )

    issues = list(
        validate_emitted_ontology_metadata(
            graph,
            metadata,
            product_key,
            expected_imports,
            mode=mode,
            context=context,
        )
    )
    expected_header = render_ontology_header_bytes(
        metadata,
        product_key,
        expected_imports,
        generated_notice=generated_notice,
        prefixes=prefixes,
        import_turtle_terms=import_turtle_terms,
        context=context,
    )
    remainder = serialized_bytes[len(expected_header) :] if serialized_bytes.startswith(expected_header) else None
    canonical_boundary = remainder == b"" or (
        remainder is not None
        and remainder.startswith(b"\n")
        and not remainder.startswith(b"\n\n")
    )
    canonical_final_newline = serialized_bytes.endswith(b"\n") and not serialized_bytes.endswith(b"\n\n")
    if remainder is None or not canonical_boundary or not canonical_final_newline:
        issues.append(
            _issue(
                "NONCANONICAL_ONTOLOGY_HEADER",
                f"products.{product_key}.serialized_ontology_header",
                "generated preamble and ontology header differ from canonical byte rendering",
            )
        )
    return tuple(sorted(set(issues), key=lambda value: (value.code, value.field, value.message)))


def strip_emitted_ontology_header(
    graph: Graph,
    metadata: PublicationMetadata,
    product_key: str,
    expected_imports: tuple[str, ...],
    context: FormalReleaseContext | None = None,
) -> Graph:
    """Return a copy containing only governed/structural logical content."""

    product = _product(metadata, product_key)
    ontology = URIRef(product.stable_ontology_iri)
    removed = {
        (ontology, RDF.type, OWL.Ontology),
        *((ontology, OWL.imports, URIRef(value)) for value in expected_imports),
        *ontology_metadata_rdf_triples(metadata, product_key, context),
    }
    result = Graph()
    for triple in graph:
        if triple not in removed:
            result.add(triple)
    return result


def validate_emitted_ontology_metadata(
    graph: Graph,
    metadata: PublicationMetadata,
    product_key: str,
    expected_imports: tuple[str, ...],
    mode: str = "development",
    context: FormalReleaseContext | None = None,
) -> tuple[ValidationIssue, ...]:
    """Validate exact ontology identity, imports, and governed metadata."""

    issues: list[ValidationIssue] = []
    if mode not in {"development", "release"}:
        return (
            _issue(
                "UNSUPPORTED_METADATA_MODE",
                "ontology_metadata.mode",
                "expected development or release",
            ),
        )
    if (mode == "release") != (context is not None):
        return (
            _issue(
                "RELEASE_CONTEXT_REQUIRED",
                "ontology_metadata.context",
                "release mode requires a complete context and development mode prohibits one",
            ),
        )
    if context is not None:
        try:
            validate_formal_release_context(context)
        except FormalReleaseContextError as exc:
            return tuple(
                _issue(value.code, f"release_context.{value.field}", value.message)
                for value in exc.issues
            )

    product = _product(metadata, product_key)
    ontology = URIRef(product.stable_ontology_iri)
    declarations = set(graph.triples((None, RDF.type, OWL.Ontology)))
    expected_declaration = {(ontology, RDF.type, OWL.Ontology)}
    if declarations != expected_declaration:
        issues.append(
            _issue(
                "ONTOLOGY_DECLARATION_MISMATCH",
                f"products.{product_key}.stable_ontology_iri",
                f"expected {sorted(map(str, expected_declaration))}, got "
                f"{sorted(map(str, declarations))}",
            )
        )

    imports = set(graph.triples((None, OWL.imports, None)))
    expected_import_triples = {
        (ontology, OWL.imports, URIRef(value)) for value in expected_imports
    }
    if imports != expected_import_triples:
        issues.append(
            _issue(
                "IMPORT_POLICY_MISMATCH",
                f"products.{product_key}.imports",
                f"expected {sorted(map(str, expected_import_triples))}, got "
                f"{sorted(map(str, imports))}",
            )
        )

    expected_metadata = ontology_metadata_rdf_triples(metadata, product_key, context)
    expected_by_predicate = {
        predicate: triple for triple in expected_metadata for predicate in (triple[1],)
    }
    governed_predicates = set(expected_by_predicate)
    formal_issue_codes = {
        URIRef(metadata.publication.development_status_property_iri): "FORMAL_STATUS_MISMATCH",
        OWL.versionIRI: "VERSION_IRI_MISMATCH",
        OWL.versionInfo: "VERSION_INFO_MISMATCH",
        URIRef(DCTERMS_NAMESPACE + "issued"): "ISSUED_DATE_MISMATCH",
    }
    for predicate, expected in expected_by_predicate.items():
        observed = set(graph.triples((None, predicate, None)))
        if observed != {expected}:
            issues.append(
                _issue(
                    formal_issue_codes.get(predicate, "ONTOLOGY_METADATA_MISMATCH")
                    if context is not None
                    else "ONTOLOGY_METADATA_MISMATCH",
                    f"products.{product_key}.{predicate}",
                    f"expected {expected!r}, got {sorted(map(repr, observed))}",
                )
            )

    allowed_subject_triples = {
        *expected_declaration,
        *expected_import_triples,
        *expected_metadata,
    }
    extra_subject_triples = set(graph.triples((ontology, None, None))) - allowed_subject_triples
    if extra_subject_triples:
        issues.append(
            _issue(
                "UNAPPROVED_ONTOLOGY_METADATA",
                f"products.{product_key}.ontology_subject",
                "ontology subject contains unapproved triples: "
                + ", ".join(sorted(map(repr, extra_subject_triples))),
            )
        )

    for predicate in governed_predicates:
        misplaced = {
            triple
            for triple in graph.triples((None, predicate, None))
            if triple[0] != ontology
        }
        if misplaced:
            issues.append(
                _issue(
                    "MISPLACED_ONTOLOGY_METADATA",
                    f"products.{product_key}.{predicate}",
                    "metadata occurs on a non-ontology subject",
                )
            )

    if context is None:
        for predicate_iri in RELEASE_ONLY_PREDICATES:
            triples = set(graph.triples((None, URIRef(predicate_iri), None)))
            if triples:
                issues.append(
                    _issue(
                        "RELEASE_METADATA_IN_DEVELOPMENT",
                        f"products.{product_key}.{predicate_iri}",
                        "formal-release metadata is prohibited in development output",
                    )
                )

    controlled_iris = (
        URIRef(product.product_type_iri),
        URIRef(metadata.publication.development_status_iri),
        URIRef(metadata.publication.formal_release_status_iri),
    )
    for controlled in controlled_iris:
        if any(True for _ in graph.triples((controlled, RDF.type, None))):
            issues.append(
                _issue(
                    "CONTROLLED_IRI_DECLARATION",
                    f"products.{product_key}.controlled_iri",
                    f"declaration triples for {controlled} are prohibited",
                )
            )

    return tuple(sorted(set(issues), key=lambda value: (value.code, value.field, value.message)))


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


def validate_metadata(
    metadata: PublicationMetadata,
    *,
    product_order: tuple[str, ...] = PRODUCT_ORDER,
) -> tuple[ValidationIssue, ...]:
    """Return semantic issues in deterministic policy order."""

    issues: list[ValidationIssue] = []
    if type(metadata.schema_version) is not int:
        issues.append(_issue("WRONG_TYPE", "schema_version", "expected integer 4"))
    elif metadata.schema_version != SCHEMA_VERSION:
        issues.append(_issue("SCHEMA_VERSION", "schema_version", "expected schema version 4"))

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
                "schema version 4 requires the exact language code 'en'",
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
        (
            publication.formal_release_status_iri,
            "publication.formal_release_status_iri",
            "INVALID_FORMAL_STATUS_IRI",
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
    if publication.formal_release_status_iri == publication.development_status_iri:
        issues.append(
            _issue(
                "STATUS_IRI_COLLISION",
                "publication.formal_release_status_iri",
                "formal release status must differ from development status",
            )
        )

    keys = tuple(product.key for product in metadata.products)
    if set(keys) != set(product_order) or len(keys) != len(product_order):
        issues.append(
            _issue("PRODUCT_SET", "products", "expected exactly: " + ", ".join(product_order))
        )
    elif keys != product_order:
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


def load_metadata(
    path: str | Path,
    *,
    product_order: tuple[str, ...] = PRODUCT_ORDER,
) -> PublicationMetadata:
    """Load UTF-8 TOML and return validated schema-4 metadata."""

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
            issues.append(_issue("WRONG_TYPE", "schema_version", "expected integer 4"))
    elif schema_version != SCHEMA_VERSION:
        issues.append(_issue("SCHEMA_VERSION", "schema_version", "expected schema version 4"))

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
        _table(top["products"], "products", product_order, issues)
        if "products" in top
        else {}
    )
    if set(products_table) == set(product_order) and tuple(products_table) != product_order:
        issues.append(_issue("PRODUCT_ORDER", "products", "products are not in canonical order"))

    release_base = publication_values.get("release_iri_base")
    products: list[ProductPublicationMetadata] = []
    for key in product_order:
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
    semantic_issues = validate_metadata(
        metadata,
        product_order=product_order,
    )
    if semantic_issues:
        raise PublicationMetadataError(semantic_issues)
    return metadata


def validate_release_identifier(value: str) -> str:
    """Compatibility wrapper for the schema-4 date-only release grammar."""

    try:
        return validate_context_release_identifier(value)
    except FormalReleaseContextError as exc:
        raise PublicationMetadataError(
            [_issue(issue.code, "release_id", issue.message) for issue in exc.issues]
        ) from exc


def validate_release_context(
    release_id: str,
    release_date: str,
    git_tag: str,
    source_commit: str,
) -> FormalReleaseContext:
    """Compatibility wrapper returning a complete formal-release context."""

    try:
        return parse_formal_release_context(
            release_id,
            release_date,
            git_tag,
            source_commit,
        )
    except FormalReleaseContextError as exc:
        raise PublicationMetadataError(
            [_issue(issue.code, issue.field, issue.message) for issue in exc.issues]
        ) from exc


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
