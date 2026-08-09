#!/usr/bin/env python3
"""Derive and validate deterministic COMS product-disposition evidence."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import product_role_policy
from coms_row_identity import (
    CANONICALIZATION_VERSION,
    AuthoritativeAxiomIdentity,
    CanonicalRowExpression,
    CanonicalRowInput,
    ExpressionNode,
    RowLocation,
    canonical_row_json,
    source_expression_sha256,
)
from publication_metadata import PublicationMetadata


SCHEMA_VERSION = 1
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
AXIOM_ID_RE = re.compile(r"sha256:([0-9a-f]{64})\Z")

TARGET_CATEGORIES = (
    "target_neutral",
    "bfo_bearing",
    "cco_bearing",
    "mixed_bfo_cco",
)
MAPPING_TYPES = (
    "class_mapping",
    "object_property_mapping",
    "property_chain",
    "domain",
    "range",
    "explicit_blank",
)
COVERAGE_CLASSIFICATIONS = (
    "class_mapping",
    "relation_mapping",
    "property_chain",
    "property_typing",
    "explicitly_unmapped",
)
DISPOSITION_STATUSES = (
    "emitted_unchanged",
    "provided_through_import",
    "provided_transitively",
    "not_applicable",
    "deferred",
)
REASON_CODES = (
    "TARGET_SPECIFIC",
    "NO_APPROVED_TRANSFORMATION_RULE",
    "EXPLICITLY_UNMAPPED_SOURCE_ROW",
)

SOURCE_NAMESPACES = (
    "http://www.w3.org/ns/sosa/",
    "http://www.w3.org/ns/sosa/sampling/",
    "http://www.w3.org/ns/ssn/",
    "http://www.w3.org/ns/ssn/systems/",
)
BFO_NAMESPACE = "http://purl.obolibrary.org/obo/BFO_"
CCO_NAMESPACE = "https://www.commoncoreontologies.org/"
STRUCTURAL_NAMESPACES = (
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "http://www.w3.org/2000/01/rdf-schema#",
    "http://www.w3.org/2002/07/owl#",
)
SUPPORTED_PREDICATE_IRIS = frozenset(
    {
        "http://www.w3.org/2000/01/rdf-schema#subClassOf",
        "http://www.w3.org/2002/07/owl#equivalentClass",
        "http://www.w3.org/2000/01/rdf-schema#subPropertyOf",
        "http://www.w3.org/2002/07/owl#equivalentProperty",
        "http://www.w3.org/2002/07/owl#propertyChainAxiom",
        "http://www.w3.org/2000/01/rdf-schema#domain",
        "http://www.w3.org/2000/01/rdf-schema#range",
    }
)
SUPPORTED_POLICY_PRODUCTS = frozenset(
    {
        "integrated",
        "alignment_core",
        "strict_bfo_mapping",
        "bfo_projection",
        "cco_extension",
    }
)

PRODUCT_ROLE_ORDER = tuple(
    product_role_policy.load_product_role_policy().role_order
)
POLICY_PRODUCTS = frozenset(PRODUCT_ROLE_ORDER)

if (
    len(PRODUCT_ROLE_ORDER) != len(POLICY_PRODUCTS)
    or POLICY_PRODUCTS != SUPPORTED_POLICY_PRODUCTS
):
    raise RuntimeError(
        "product-role policy role_order must contain each supported "
        "disposition role exactly once"
    )


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    row_id: str = ""
    axiom_id: str = ""
    field: str = ""
    message: str = ""


class ProductDispositionError(ValueError):
    """One or more expected disposition parsing or validation failures."""

    def __init__(self, issues: Iterable[ValidationIssue]):
        self.issues = sort_issues(issues)
        super().__init__(" | ".join(format_issue(issue) for issue in self.issues))


@dataclass(frozen=True)
class ProductDisposition:
    status: str
    reason_code: str | None = None


@dataclass(frozen=True)
class RequiredInputHashes:
    workbook_sha256: str
    generator_sha256: str
    row_identity_module_sha256: str
    disposition_module_sha256: str
    publication_metadata_sha256: str


@dataclass(frozen=True)
class DispositionAxiomInput:
    identity: AuthoritativeAxiomIdentity
    subject_iri: str
    predicate_iri: str
    target_iris: tuple[str, ...]


@dataclass(frozen=True)
class DispositionRowInput:
    row_id: str
    location: RowLocation
    subject_lexical: str
    predicate_lexical: str | None
    authoritative_target_lexical: str | None
    canonical_row: CanonicalRowExpression
    source_expression_sha256: str
    mapping_type: str
    reasoning: str
    authoritative_axioms: tuple[DispositionAxiomInput, ...]


@dataclass(frozen=True)
class EntityReference:
    lexical: str
    iri: str


@dataclass(frozen=True)
class DispositionAxiomRecord:
    axiom_id: str
    canonical_expression: str
    referenced_iris: tuple[str, ...]
    target_category: str
    product_dispositions: tuple[tuple[str, ProductDisposition], ...]


@dataclass(frozen=True)
class DispositionRowRecord:
    row_id: str
    location: RowLocation
    subject: EntityReference
    predicate: EntityReference | None
    authoritative_target_lexical: str | None
    canonical_row_expression: CanonicalRowExpression
    source_expression_sha256: str
    mapping_type: str
    coverage_classification: str
    reasoning: str
    authoritative_axioms: tuple[DispositionAxiomRecord, ...]
    row_product_dispositions: tuple[tuple[str, ProductDisposition], ...] | None


@dataclass(frozen=True)
class DispositionSummary:
    governed_row_count: int
    unique_row_id_count: int
    authoritative_axiom_count: int
    unique_authoritative_axiom_count: int
    zero_axiom_row_count: int
    target_neutral_axiom_count: int
    bfo_bearing_axiom_count: int
    cco_bearing_axiom_count: int
    mixed_bfo_cco_axiom_count: int
    class_mapping_row_count: int
    relation_mapping_row_count: int
    property_chain_row_count: int
    property_typing_row_count: int
    explicitly_unmapped_row_count: int


@dataclass(frozen=True)
class DispositionDocument:
    schema_version: int
    canonicalization_version: str
    input_hashes: RequiredInputHashes
    product_order: tuple[str, ...]
    summary: DispositionSummary
    rows: tuple[DispositionRowRecord, ...]


def issue(
    code: str,
    message: str,
    *,
    row_id: str = "",
    axiom_id: str = "",
    field: str = "",
) -> ValidationIssue:
    return ValidationIssue(code, row_id, axiom_id, field, message)


def sort_issues(issues: Iterable[ValidationIssue]) -> tuple[ValidationIssue, ...]:
    return tuple(
        sorted(
            issues,
            key=lambda value: (
                value.code,
                value.row_id,
                value.axiom_id,
                value.field,
                value.message,
            ),
        )
    )


def format_issue(value: ValidationIssue) -> str:
    context = " ".join(
        part
        for part in (
            value.row_id,
            value.axiom_id,
            value.field,
        )
        if part
    )
    return f"ERROR [{value.code}]" + (f" {context}" if context else "") + f": {value.message}"


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_namespace(value: str, namespaces: tuple[str, ...]) -> bool:
    return any(value.startswith(namespace) for namespace in namespaces)


def _expression_iris(node: ExpressionNode | None) -> tuple[str, ...]:
    if node is None:
        return ()
    if node.kind == "named":
        if node.iri is None:
            raise ProductDispositionError(
                [issue("ROW_EXPRESSION_MISMATCH", "named expression lacks an IRI")]
            )
        return (node.iri,)
    if node.kind in {"intersection", "union"}:
        return tuple(iri for child in node.children for iri in _expression_iris(child))
    if node.kind == "some":
        if node.property_iri is None or node.filler is None:
            raise ProductDispositionError(
                [issue("ROW_EXPRESSION_MISMATCH", "existential expression is incomplete")]
            )
        return (node.property_iri, *_expression_iris(node.filler))
    raise ProductDispositionError(
        [issue("ROW_EXPRESSION_MISMATCH", f"unsupported expression node {node.kind!r}")]
    )


def axiom_input_from_canonical_row(
    identity: AuthoritativeAxiomIdentity,
    row: CanonicalRowInput,
) -> DispositionAxiomInput:
    """Build one axiom-level neutral input from a resolved canonical row."""

    if row.predicate_iri is None:
        raise ProductDispositionError(
            [
                issue(
                    "INCOMPLETE_ZERO_AXIOM_ROW",
                    "a zero-axiom row cannot be adapted as an authoritative axiom",
                    row_id=row.row_id,
                    field="predicate",
                )
            ]
        )
    if row.expression is not None:
        target_iris = _expression_iris(row.expression)
    elif row.target_property_iri is not None:
        target_iris = (row.target_property_iri,)
    else:
        target_iris = row.property_chain
    return DispositionAxiomInput(
        identity=identity,
        subject_iri=row.subject_iri,
        predicate_iri=row.predicate_iri,
        target_iris=tuple(target_iris),
    )


def referenced_iris(axiom_input: DispositionAxiomInput) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                nfc(axiom_input.subject_iri),
                nfc(axiom_input.predicate_iri),
                *(nfc(value) for value in axiom_input.target_iris),
            }
        )
    )


def classify_target_category(axiom_input: DispositionAxiomInput) -> str:
    """Classify target vocabulary from structured, resolved axiom terms."""

    issues: list[ValidationIssue] = []
    axiom_id = f"sha256:{axiom_input.identity.sha256}"
    if not _is_namespace(axiom_input.subject_iri, SOURCE_NAMESPACES):
        issues.append(
            issue(
                "UNEXPECTED_TARGET_VOCABULARY",
                f"governed subject is outside approved source namespaces: {axiom_input.subject_iri}",
                axiom_id=axiom_id,
                field="subject.iri",
            )
        )
    if axiom_input.predicate_iri not in SUPPORTED_PREDICATE_IRIS:
        issues.append(
            issue(
                "UNEXPECTED_TARGET_VOCABULARY",
                f"unsupported mapping or typing predicate IRI: {axiom_input.predicate_iri}",
                axiom_id=axiom_id,
                field="predicate.iri",
            )
        )

    has_bfo = False
    has_cco = False
    for value in axiom_input.target_iris:
        if value.startswith(BFO_NAMESPACE):
            has_bfo = True
        elif value.startswith(CCO_NAMESPACE):
            has_cco = True
        elif _is_namespace(value, SOURCE_NAMESPACES) or _is_namespace(value, STRUCTURAL_NAMESPACES):
            continue
        else:
            issues.append(
                issue(
                    "UNEXPECTED_TARGET_VOCABULARY",
                    f"target IRI is outside approved namespaces: {value}",
                    axiom_id=axiom_id,
                    field="referenced_iris",
                )
            )
    if issues:
        raise ProductDispositionError(issues)
    if has_bfo and has_cco:
        return "mixed_bfo_cco"
    if has_bfo:
        return "bfo_bearing"
    if has_cco:
        return "cco_bearing"
    return "target_neutral"


def _disposition(status: str, reason_code: str | None = None) -> ProductDisposition:
    return ProductDisposition(status=status, reason_code=reason_code)


DISPOSITION_MATRIX = {
    "target_neutral": {
        "integrated": _disposition("emitted_unchanged"),
        "alignment_core": _disposition("emitted_unchanged"),
        "strict_bfo_mapping": _disposition("provided_through_import"),
        "bfo_projection": _disposition("provided_transitively"),
        "cco_extension": _disposition("provided_transitively"),
    },
    "bfo_bearing": {
        "integrated": _disposition("emitted_unchanged"),
        "alignment_core": _disposition("not_applicable", "TARGET_SPECIFIC"),
        "strict_bfo_mapping": _disposition("emitted_unchanged"),
        "bfo_projection": _disposition("provided_through_import"),
        "cco_extension": _disposition("provided_through_import"),
    },
    "cco_bearing": {
        "integrated": _disposition("emitted_unchanged"),
        "alignment_core": _disposition("not_applicable", "TARGET_SPECIFIC"),
        "strict_bfo_mapping": _disposition("deferred", "NO_APPROVED_TRANSFORMATION_RULE"),
        "bfo_projection": _disposition("deferred", "NO_APPROVED_TRANSFORMATION_RULE"),
        "cco_extension": _disposition("emitted_unchanged"),
    },
    "mixed_bfo_cco": {
        "integrated": _disposition("emitted_unchanged"),
        "alignment_core": _disposition("not_applicable", "TARGET_SPECIFIC"),
        "strict_bfo_mapping": _disposition("deferred", "NO_APPROVED_TRANSFORMATION_RULE"),
        "bfo_projection": _disposition("deferred", "NO_APPROVED_TRANSFORMATION_RULE"),
        "cco_extension": _disposition("emitted_unchanged"),
    },
}


def derive_product_dispositions(
    target_category: str,
    product_keys: Iterable[str],
) -> tuple[tuple[str, ProductDisposition], ...]:
    if target_category not in DISPOSITION_MATRIX:
        raise ProductDispositionError(
            [issue("UNKNOWN_TARGET_CATEGORY", f"unknown target category {target_category!r}")]
        )
    keys = tuple(product_keys)
    unknown = sorted(set(keys) - POLICY_PRODUCTS)
    missing = sorted(POLICY_PRODUCTS - set(keys))
    issues = [issue("UNKNOWN_PRODUCT", f"unknown product {key!r}", field="product_order") for key in unknown]
    issues.extend(
        issue("MISSING_PRODUCT_DISPOSITION", f"missing product {key!r}", field="product_order")
        for key in missing
    )
    if issues:
        raise ProductDispositionError(issues)
    return tuple((key, DISPOSITION_MATRIX[target_category][key]) for key in keys)


def derive_zero_axiom_dispositions(
    product_keys: Iterable[str],
) -> tuple[tuple[str, ProductDisposition], ...]:
    keys = tuple(product_keys)
    unknown = sorted(set(keys) - POLICY_PRODUCTS)
    missing = sorted(POLICY_PRODUCTS - set(keys))
    if unknown or missing:
        raise ProductDispositionError(
            [
                *[issue("UNKNOWN_PRODUCT", f"unknown product {key!r}") for key in unknown],
                *[
                    issue("MISSING_PRODUCT_DISPOSITION", f"missing product {key!r}")
                    for key in missing
                ],
            ]
        )
    return tuple(
        (key, _disposition("deferred", "EXPLICITLY_UNMAPPED_SOURCE_ROW"))
        for key in keys
    )


def coverage_classification(mapping_type: str) -> str:
    values = {
        "class_mapping": "class_mapping",
        "object_property_mapping": "relation_mapping",
        "property_chain": "property_chain",
        "domain": "property_typing",
        "range": "property_typing",
        "explicit_blank": "explicitly_unmapped",
    }
    try:
        return values[mapping_type]
    except KeyError as exc:
        raise ProductDispositionError(
            [issue("ROW_EXPRESSION_MISMATCH", f"unknown mapping type {mapping_type!r}")]
        ) from exc


def _normalize_canonical_expression(value: CanonicalRowExpression) -> CanonicalRowExpression:
    return CanonicalRowExpression(
        canonicalization=nfc(value.canonicalization),
        mapping_type=nfc(value.mapping_type),
        predicate_iri=None if value.predicate_iri is None else nfc(value.predicate_iri),
        subject_iri=nfc(value.subject_iri),
        target=None if value.target is None else nfc(value.target),
    )


def _validate_hashes(values: RequiredInputHashes) -> None:
    issues = []
    for field in values.__dataclass_fields__:
        value = getattr(values, field)
        if SHA256_RE.fullmatch(value) is None:
            issues.append(issue("INVALID_INPUT_HASH", "expected 64 lowercase hexadecimal characters", field=field))
    if issues:
        raise ProductDispositionError(issues)


def _build_summary(rows: tuple[DispositionRowRecord, ...]) -> DispositionSummary:
    categories = Counter(
        axiom.target_category
        for row in rows
        for axiom in row.authoritative_axioms
    )
    coverage = Counter(row.coverage_classification for row in rows)
    axiom_ids = [axiom.axiom_id for row in rows for axiom in row.authoritative_axioms]
    return DispositionSummary(
        governed_row_count=len(rows),
        unique_row_id_count=len({row.row_id for row in rows}),
        authoritative_axiom_count=len(axiom_ids),
        unique_authoritative_axiom_count=len(set(axiom_ids)),
        zero_axiom_row_count=sum(not row.authoritative_axioms for row in rows),
        target_neutral_axiom_count=categories["target_neutral"],
        bfo_bearing_axiom_count=categories["bfo_bearing"],
        cco_bearing_axiom_count=categories["cco_bearing"],
        mixed_bfo_cco_axiom_count=categories["mixed_bfo_cco"],
        class_mapping_row_count=coverage["class_mapping"],
        relation_mapping_row_count=coverage["relation_mapping"],
        property_chain_row_count=coverage["property_chain"],
        property_typing_row_count=coverage["property_typing"],
        explicitly_unmapped_row_count=coverage["explicitly_unmapped"],
    )


def build_disposition_document(
    row_inputs: Iterable[DispositionRowInput],
    publication_metadata: PublicationMetadata,
    input_hashes: RequiredInputHashes,
) -> DispositionDocument:
    """Build canonical disposition evidence from resolved COMS row inputs."""

    _validate_hashes(input_hashes)
    # Publication metadata remains provenance input, but materialized
    # ontology products do not define the disposition-role taxonomy.
    product_keys = PRODUCT_ROLE_ORDER
    rows: list[DispositionRowRecord] = []
    issues: list[ValidationIssue] = []
    seen_rows: set[str] = set()
    seen_axioms: set[str] = set()

    for source in sorted(row_inputs, key=lambda value: value.row_id):
        if source.row_id in seen_rows:
            issues.append(
                issue(
                    "DUPLICATE_DISPOSITION_ROW",
                    "RowID appears more than once",
                    row_id=source.row_id,
                )
            )
            continue
        seen_rows.add(source.row_id)
        canonical = _normalize_canonical_expression(source.canonical_row)
        location = RowLocation(
            nfc(source.location.worksheet),
            source.location.row_number,
        )
        if source.mapping_type != canonical.mapping_type:
            issues.append(
                issue(
                    "ROW_EXPRESSION_MISMATCH",
                    f"{location.text}: source mapping type {source.mapping_type!r} "
                    f"does not match canonical mapping type {canonical.mapping_type!r}",
                    row_id=source.row_id,
                    field="mapping_type",
                )
            )
            continue
        if not _is_namespace(canonical.subject_iri, SOURCE_NAMESPACES):
            issues.append(
                issue(
                    "UNEXPECTED_TARGET_VOCABULARY",
                    f"governed subject is outside approved source namespaces: {canonical.subject_iri}",
                    row_id=source.row_id,
                    field="subject.iri",
                )
            )
        if canonical.predicate_iri is not None and canonical.predicate_iri not in SUPPORTED_PREDICATE_IRIS:
            issues.append(
                issue(
                    "UNEXPECTED_TARGET_VOCABULARY",
                    f"unsupported mapping or typing predicate IRI: {canonical.predicate_iri}",
                    row_id=source.row_id,
                    field="predicate.iri",
                )
            )
        expected_hash = source_expression_sha256(canonical)
        if source.source_expression_sha256 != expected_hash:
            issues.append(
                issue(
                    "EXPRESSION_HASH_MISMATCH",
                    f"expected {expected_hash}, got {source.source_expression_sha256}",
                    row_id=source.row_id,
                    field="source_expression_sha256",
                )
            )

        row_axioms: list[DispositionAxiomRecord] = []
        for axiom_input in source.authoritative_axioms:
            axiom_id = f"sha256:{axiom_input.identity.sha256}"
            if (
                axiom_input.subject_iri != canonical.subject_iri
                or axiom_input.predicate_iri != canonical.predicate_iri
            ):
                issues.append(
                    issue(
                        "ROW_EXPRESSION_MISMATCH",
                        "axiom subject or predicate differs from its canonical row",
                        row_id=source.row_id,
                        axiom_id=axiom_id,
                    )
                )
            actual_digest = sha256_text(nfc(axiom_input.identity.canonical_axiom))
            if axiom_input.identity.sha256 != actual_digest:
                issues.append(
                    issue(
                        "AXIOM_ID_MISMATCH",
                        f"expected sha256:{actual_digest}, got {axiom_id}",
                        row_id=source.row_id,
                        axiom_id=axiom_id,
                    )
                )
            if axiom_id in seen_axioms:
                issues.append(
                    issue(
                        "DUPLICATE_AUTHORITATIVE_AXIOM",
                        "canonical authoritative axiom appears more than once",
                        row_id=source.row_id,
                        axiom_id=axiom_id,
                    )
                )
            seen_axioms.add(axiom_id)
            try:
                category = classify_target_category(axiom_input)
                dispositions = derive_product_dispositions(category, product_keys)
            except ProductDispositionError as exc:
                issues.extend(
                    issue(
                        value.code,
                        value.message,
                        row_id=source.row_id,
                        axiom_id=value.axiom_id or axiom_id,
                        field=value.field,
                    )
                    for value in exc.issues
                )
                continue
            row_axioms.append(
                DispositionAxiomRecord(
                    axiom_id=axiom_id,
                    canonical_expression=nfc(axiom_input.identity.canonical_axiom),
                    referenced_iris=referenced_iris(axiom_input),
                    target_category=category,
                    product_dispositions=dispositions,
                )
            )

        row_axioms.sort(key=lambda value: value.axiom_id)
        is_zero = not row_axioms
        row_dispositions = derive_zero_axiom_dispositions(product_keys) if is_zero else None
        predicate = None
        target = None
        if not is_zero:
            if source.predicate_lexical is None or source.authoritative_target_lexical is None:
                issues.append(
                    issue(
                        "INCOMPLETE_ZERO_AXIOM_ROW",
                        "mapped rows require predicate and authoritative target values",
                        row_id=source.row_id,
                    )
                )
            elif canonical.predicate_iri is None:
                issues.append(
                    issue(
                        "ROW_EXPRESSION_MISMATCH",
                        "mapped canonical row lacks predicate IRI",
                        row_id=source.row_id,
                    )
                )
            else:
                predicate = EntityReference(nfc(source.predicate_lexical), nfc(canonical.predicate_iri))
                target = nfc(source.authoritative_target_lexical)
        elif (
            source.mapping_type != "explicit_blank"
            or source.predicate_lexical is not None
            or source.authoritative_target_lexical is not None
            or canonical.predicate_iri is not None
        ):
            issues.append(
                issue(
                    "INCOMPLETE_ZERO_AXIOM_ROW",
                    "zero-axiom rows must be explicit_blank with null predicate and target",
                    row_id=source.row_id,
                )
            )

        try:
            coverage = coverage_classification(source.mapping_type)
        except ProductDispositionError as exc:
            issues.extend(
                issue(value.code, value.message, row_id=source.row_id, field=value.field)
                for value in exc.issues
            )
            continue
        rows.append(
            DispositionRowRecord(
                row_id=nfc(source.row_id),
                location=location,
                subject=EntityReference(nfc(source.subject_lexical), nfc(canonical.subject_iri)),
                predicate=predicate,
                authoritative_target_lexical=target,
                canonical_row_expression=canonical,
                source_expression_sha256=source.source_expression_sha256,
                mapping_type=source.mapping_type,
                coverage_classification=coverage,
                reasoning=nfc(source.reasoning),
                authoritative_axioms=tuple(row_axioms),
                row_product_dispositions=row_dispositions,
            )
        )
    if issues:
        raise ProductDispositionError(issues)
    result_rows = tuple(sorted(rows, key=lambda value: value.row_id))
    return DispositionDocument(
        schema_version=SCHEMA_VERSION,
        canonicalization_version=CANONICALIZATION_VERSION,
        input_hashes=input_hashes,
        product_order=product_keys,
        summary=_build_summary(result_rows),
        rows=result_rows,
    )


def _disposition_object(value: ProductDisposition) -> dict[str, object]:
    result: dict[str, object] = {"status": nfc(value.status)}
    if value.reason_code is not None:
        result["reason_code"] = nfc(value.reason_code)
    return result


def _disposition_map_object(
    values: tuple[tuple[str, ProductDisposition], ...],
    product_order: tuple[str, ...],
) -> dict[str, object]:
    by_name = {nfc(key): value for key, value in values}
    ordered_keys = [key for key in product_order if key in by_name]
    ordered_keys.extend(sorted(set(by_name) - set(product_order)))
    return {key: _disposition_object(by_name[key]) for key in ordered_keys}


def _canonical_object(value: CanonicalRowExpression) -> dict[str, object]:
    return {
        "canonicalization": nfc(value.canonicalization),
        "mapping_type": nfc(value.mapping_type),
        "predicate_iri": None if value.predicate_iri is None else nfc(value.predicate_iri),
        "subject_iri": nfc(value.subject_iri),
        "target": None if value.target is None else nfc(value.target),
    }


def disposition_document_object(document: DispositionDocument) -> dict[str, object]:
    hashes = document.input_hashes
    summary = document.summary
    product_order = tuple(nfc(key) for key in document.product_order)
    rows = sorted(document.rows, key=lambda value: nfc(value.row_id))
    return {
        "schema_version": document.schema_version,
        "canonicalization_version": nfc(document.canonicalization_version),
        "workbook_sha256": hashes.workbook_sha256,
        "generator_sha256": hashes.generator_sha256,
        "row_identity_module_sha256": hashes.row_identity_module_sha256,
        "disposition_module_sha256": hashes.disposition_module_sha256,
        "publication_metadata_sha256": hashes.publication_metadata_sha256,
        "product_order": list(product_order),
        "summary": {
            field: getattr(summary, field)
            for field in summary.__dataclass_fields__
        },
        "rows": [
            {
                "row_id": nfc(row.row_id),
                "location": {
                    "worksheet": nfc(row.location.worksheet),
                    "row": row.location.row_number,
                },
                "subject": {
                    "lexical": nfc(row.subject.lexical),
                    "iri": nfc(row.subject.iri),
                },
                "predicate": None
                if row.predicate is None
                else {
                    "lexical": nfc(row.predicate.lexical),
                    "iri": nfc(row.predicate.iri),
                },
                "authoritative_target_lexical": None
                if row.authoritative_target_lexical is None
                else nfc(row.authoritative_target_lexical),
                "canonical_row_expression": _canonical_object(row.canonical_row_expression),
                "source_expression_sha256": nfc(row.source_expression_sha256),
                "mapping_type": nfc(row.mapping_type),
                "coverage_classification": nfc(row.coverage_classification),
                "reasoning": nfc(row.reasoning),
                "authoritative_axioms": [
                    {
                        "axiom_id": nfc(axiom.axiom_id),
                        "canonical_expression": nfc(axiom.canonical_expression),
                        "referenced_iris": sorted(nfc(value) for value in axiom.referenced_iris),
                        "target_category": nfc(axiom.target_category),
                        "product_dispositions": _disposition_map_object(
                            axiom.product_dispositions,
                            product_order,
                        ),
                    }
                    for axiom in sorted(
                        row.authoritative_axioms,
                        key=lambda value: nfc(value.axiom_id),
                    )
                ],
                "row_product_dispositions": None
                if row.row_product_dispositions is None
                else _disposition_map_object(
                    row.row_product_dispositions,
                    product_order,
                ),
            }
            for row in rows
        ],
    }


def serialize_disposition_document(document: DispositionDocument) -> bytes:
    """Serialize using the governed human-diffable JSON form."""

    text = json.dumps(
        disposition_document_object(document),
        ensure_ascii=False,
        indent=2,
    )
    return (text + "\n").encode("utf-8")


TOP_LEVEL_KEYS = (
    "schema_version",
    "canonicalization_version",
    "workbook_sha256",
    "generator_sha256",
    "row_identity_module_sha256",
    "disposition_module_sha256",
    "publication_metadata_sha256",
    "product_order",
    "summary",
    "rows",
)
SUMMARY_KEYS = tuple(DispositionSummary.__dataclass_fields__)
ROW_KEYS = (
    "row_id",
    "location",
    "subject",
    "predicate",
    "authoritative_target_lexical",
    "canonical_row_expression",
    "source_expression_sha256",
    "mapping_type",
    "coverage_classification",
    "reasoning",
    "authoritative_axioms",
    "row_product_dispositions",
)
AXIOM_KEYS = (
    "axiom_id",
    "canonical_expression",
    "referenced_iris",
    "target_category",
    "product_dispositions",
)


def _expect_object(
    value: object,
    keys: tuple[str, ...],
    field: str,
    issues: list[ValidationIssue],
    *,
    row_id: str = "",
    axiom_id: str = "",
) -> dict[str, object]:
    if not isinstance(value, dict):
        issues.append(issue("WRONG_TYPE", "expected JSON object", row_id=row_id, axiom_id=axiom_id, field=field))
        return {}
    missing = [key for key in keys if key not in value]
    extra = sorted(set(value) - set(keys))
    issues.extend(
        issue("MISSING_FIELD", f"missing required field {key!r}", row_id=row_id, axiom_id=axiom_id, field=field)
        for key in missing
    )
    issues.extend(
        issue("UNKNOWN_FIELD", f"unknown field {key!r}", row_id=row_id, axiom_id=axiom_id, field=field)
        for key in extra
    )
    return value


def _required_string(
    value: object,
    field: str,
    issues: list[ValidationIssue],
    *,
    row_id: str = "",
    axiom_id: str = "",
) -> str:
    if not isinstance(value, str):
        issues.append(issue("WRONG_TYPE", "expected string", row_id=row_id, axiom_id=axiom_id, field=field))
        return ""
    return value


def _parse_dispositions(
    value: object,
    field: str,
    issues: list[ValidationIssue],
    *,
    row_id: str,
    axiom_id: str = "",
) -> tuple[tuple[str, ProductDisposition], ...]:
    if not isinstance(value, dict):
        issues.append(issue("WRONG_TYPE", "expected product-disposition object", row_id=row_id, axiom_id=axiom_id, field=field))
        return ()
    result = []
    for product, raw in value.items():
        if not isinstance(raw, dict):
            issues.append(issue("WRONG_TYPE", "expected disposition object", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}"))
            continue
        extra = sorted(set(raw) - {"status", "reason_code"})
        if "status" not in raw:
            issues.append(issue("MISSING_FIELD", "missing status", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}"))
        for key in extra:
            issues.append(issue("UNKNOWN_FIELD", f"unknown field {key!r}", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}"))
        status = _required_string(raw.get("status"), f"{field}.{product}.status", issues, row_id=row_id, axiom_id=axiom_id)
        reason_raw = raw.get("reason_code")
        reason = None if reason_raw is None else _required_string(reason_raw, f"{field}.{product}.reason_code", issues, row_id=row_id, axiom_id=axiom_id)
        result.append((str(product), ProductDisposition(status, reason)))
    return tuple(result)


def _parse_canonical(
    value: object,
    field: str,
    issues: list[ValidationIssue],
    row_id: str,
) -> CanonicalRowExpression:
    keys = ("canonicalization", "mapping_type", "predicate_iri", "subject_iri", "target")
    raw = _expect_object(value, keys, field, issues, row_id=row_id)
    predicate = raw.get("predicate_iri")
    if predicate is not None and not isinstance(predicate, str):
        issues.append(issue("WRONG_TYPE", "expected string or null", row_id=row_id, field=f"{field}.predicate_iri"))
        predicate = None
    target = raw.get("target")
    if target is not None and not isinstance(target, str):
        issues.append(issue("WRONG_TYPE", "expected string or null", row_id=row_id, field=f"{field}.target"))
        target = None
    return CanonicalRowExpression(
        canonicalization=_required_string(raw.get("canonicalization"), f"{field}.canonicalization", issues, row_id=row_id),
        mapping_type=_required_string(raw.get("mapping_type"), f"{field}.mapping_type", issues, row_id=row_id),
        predicate_iri=predicate,
        subject_iri=_required_string(raw.get("subject_iri"), f"{field}.subject_iri", issues, row_id=row_id),
        target=target,
    )


def _parse_document(raw: object) -> DispositionDocument:
    issues: list[ValidationIssue] = []
    top = _expect_object(raw, TOP_LEVEL_KEYS, "document", issues)
    product_raw = top.get("product_order")
    if not isinstance(product_raw, list) or not all(isinstance(value, str) for value in product_raw):
        issues.append(issue("WRONG_TYPE", "expected array of product strings", field="product_order"))
        products: tuple[str, ...] = ()
    else:
        products = tuple(product_raw)

    summary_raw = _expect_object(top.get("summary"), SUMMARY_KEYS, "summary", issues)
    summary_values: dict[str, int] = {}
    for key in SUMMARY_KEYS:
        value = summary_raw.get(key)
        if type(value) is not int or value < 0:
            issues.append(issue("WRONG_TYPE", "expected nonnegative integer", field=f"summary.{key}"))
            value = 0
        summary_values[key] = value

    rows_raw = top.get("rows")
    if not isinstance(rows_raw, list):
        issues.append(issue("WRONG_TYPE", "expected array", field="rows"))
        rows_raw = []
    rows: list[DispositionRowRecord] = []
    for index, row_value in enumerate(rows_raw):
        field = f"rows[{index}]"
        row_raw = _expect_object(row_value, ROW_KEYS, field, issues)
        row_id = _required_string(row_raw.get("row_id"), f"{field}.row_id", issues)
        location_raw = _expect_object(row_raw.get("location"), ("worksheet", "row"), f"{field}.location", issues, row_id=row_id)
        worksheet = nfc(
            _required_string(
                location_raw.get("worksheet"),
                f"{field}.location.worksheet",
                issues,
                row_id=row_id,
            )
        )
        row_number = location_raw.get("row")
        if type(row_number) is not int or row_number < 1:
            issues.append(issue("WRONG_TYPE", "expected positive integer", row_id=row_id, field=f"{field}.location.row"))
            row_number = 1
        subject_raw = _expect_object(row_raw.get("subject"), ("lexical", "iri"), f"{field}.subject", issues, row_id=row_id)
        subject = EntityReference(
            _required_string(subject_raw.get("lexical"), f"{field}.subject.lexical", issues, row_id=row_id),
            _required_string(subject_raw.get("iri"), f"{field}.subject.iri", issues, row_id=row_id),
        )
        predicate_raw = row_raw.get("predicate")
        predicate = None
        if predicate_raw is not None:
            predicate_object = _expect_object(predicate_raw, ("lexical", "iri"), f"{field}.predicate", issues, row_id=row_id)
            predicate = EntityReference(
                _required_string(predicate_object.get("lexical"), f"{field}.predicate.lexical", issues, row_id=row_id),
                _required_string(predicate_object.get("iri"), f"{field}.predicate.iri", issues, row_id=row_id),
            )
        target_raw = row_raw.get("authoritative_target_lexical")
        target = None if target_raw is None else _required_string(target_raw, f"{field}.authoritative_target_lexical", issues, row_id=row_id)
        canonical = _parse_canonical(row_raw.get("canonical_row_expression"), f"{field}.canonical_row_expression", issues, row_id)

        axioms_raw = row_raw.get("authoritative_axioms")
        if not isinstance(axioms_raw, list):
            issues.append(issue("WRONG_TYPE", "expected array", row_id=row_id, field=f"{field}.authoritative_axioms"))
            axioms_raw = []
        axioms: list[DispositionAxiomRecord] = []
        for axiom_index, axiom_value in enumerate(axioms_raw):
            axiom_field = f"{field}.authoritative_axioms[{axiom_index}]"
            axiom_raw = _expect_object(axiom_value, AXIOM_KEYS, axiom_field, issues, row_id=row_id)
            axiom_id = _required_string(axiom_raw.get("axiom_id"), f"{axiom_field}.axiom_id", issues, row_id=row_id)
            refs_raw = axiom_raw.get("referenced_iris")
            if not isinstance(refs_raw, list) or not all(isinstance(value, str) for value in refs_raw):
                issues.append(issue("WRONG_TYPE", "expected array of IRI strings", row_id=row_id, axiom_id=axiom_id, field=f"{axiom_field}.referenced_iris"))
                refs: tuple[str, ...] = ()
            else:
                refs = tuple(refs_raw)
            axioms.append(
                DispositionAxiomRecord(
                    axiom_id=axiom_id,
                    canonical_expression=_required_string(axiom_raw.get("canonical_expression"), f"{axiom_field}.canonical_expression", issues, row_id=row_id, axiom_id=axiom_id),
                    referenced_iris=refs,
                    target_category=_required_string(axiom_raw.get("target_category"), f"{axiom_field}.target_category", issues, row_id=row_id, axiom_id=axiom_id),
                    product_dispositions=_parse_dispositions(axiom_raw.get("product_dispositions"), f"{axiom_field}.product_dispositions", issues, row_id=row_id, axiom_id=axiom_id),
                )
            )
        row_dispositions_raw = row_raw.get("row_product_dispositions")
        row_dispositions = None
        if row_dispositions_raw is not None:
            row_dispositions = _parse_dispositions(row_dispositions_raw, f"{field}.row_product_dispositions", issues, row_id=row_id)
        rows.append(
            DispositionRowRecord(
                row_id=row_id,
                location=RowLocation(worksheet, row_number),
                subject=subject,
                predicate=predicate,
                authoritative_target_lexical=target,
                canonical_row_expression=canonical,
                source_expression_sha256=_required_string(row_raw.get("source_expression_sha256"), f"{field}.source_expression_sha256", issues, row_id=row_id),
                mapping_type=_required_string(row_raw.get("mapping_type"), f"{field}.mapping_type", issues, row_id=row_id),
                coverage_classification=_required_string(row_raw.get("coverage_classification"), f"{field}.coverage_classification", issues, row_id=row_id),
                reasoning=_required_string(row_raw.get("reasoning"), f"{field}.reasoning", issues, row_id=row_id),
                authoritative_axioms=tuple(axioms),
                row_product_dispositions=row_dispositions,
            )
        )
    if issues:
        raise ProductDispositionError(issues)
    return DispositionDocument(
        schema_version=top.get("schema_version") if type(top.get("schema_version")) is int else 0,
        canonicalization_version=str(top.get("canonicalization_version", "")),
        input_hashes=RequiredInputHashes(
            workbook_sha256=str(top.get("workbook_sha256", "")),
            generator_sha256=str(top.get("generator_sha256", "")),
            row_identity_module_sha256=str(top.get("row_identity_module_sha256", "")),
            disposition_module_sha256=str(top.get("disposition_module_sha256", "")),
            publication_metadata_sha256=str(top.get("publication_metadata_sha256", "")),
        ),
        product_order=products,
        summary=DispositionSummary(**summary_values),
        rows=tuple(rows),
    )


def load_disposition_document(path: str | Path) -> DispositionDocument:
    """Load UTF-8 disposition JSON and enforce its exact governed schema."""

    source = Path(path)
    try:
        data = source.read_bytes()
        text = data.decode("utf-8")
        raw = json.loads(text)
    except OSError as exc:
        raise ProductDispositionError(
            [issue("DISPOSITION_IO", f"cannot read disposition document: {exc}", field=str(source))]
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductDispositionError(
            [issue("DISPOSITION_JSON_PARSE", f"cannot parse UTF-8 JSON: {exc}", field=str(source))]
        ) from exc
    return _parse_document(raw)


def _validate_disposition_values(
    values: tuple[tuple[str, ProductDisposition], ...],
    expected: tuple[tuple[str, ProductDisposition], ...],
    *,
    row_id: str,
    axiom_id: str,
    field: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    names = [name for name, _ in values]
    expected_names = [name for name, _ in expected]
    for product in sorted(set(expected_names) - set(names)):
        issues.append(issue("MISSING_PRODUCT_DISPOSITION", f"missing product {product!r}", row_id=row_id, axiom_id=axiom_id, field=field))
    for product in sorted(set(names) - set(expected_names)):
        issues.append(issue("UNKNOWN_PRODUCT", f"unknown product {product!r}", row_id=row_id, axiom_id=axiom_id, field=field))
    by_name = dict(values)
    for product, required in expected:
        actual = by_name.get(product)
        if actual is None:
            continue
        if actual.status not in DISPOSITION_STATUSES:
            issues.append(issue("UNKNOWN_DISPOSITION_STATUS", f"unknown status {actual.status!r}", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}.status"))
        if actual.reason_code is not None and actual.reason_code not in REASON_CODES:
            issues.append(issue("INVALID_REASON_CODE", f"unknown reason code {actual.reason_code!r}", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}.reason_code"))
        if required.reason_code is None and actual.reason_code is not None:
            issues.append(issue("PROHIBITED_REASON_CODE", "reason_code is prohibited for this status", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}.reason_code"))
        if required.reason_code is not None and actual.reason_code is None:
            issues.append(issue("MISSING_REASON_CODE", f"expected {required.reason_code}", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}.reason_code"))
        elif required.reason_code is not None and actual.reason_code != required.reason_code:
            issues.append(issue("INVALID_REASON_CODE", f"expected {required.reason_code}, got {actual.reason_code}", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}.reason_code"))
        if actual != required:
            issues.append(issue("DISPOSITION_POLICY_MISMATCH", f"expected {required}, got {actual}", row_id=row_id, axiom_id=axiom_id, field=f"{field}.{product}"))
    return issues


def validate_disposition_document(
    document: DispositionDocument,
    expected_row_inputs: Iterable[DispositionRowInput],
    publication_metadata: PublicationMetadata,
    expected_hashes: RequiredInputHashes,
) -> tuple[ValidationIssue, ...]:
    """Reconcile a disposition document with structured authoritative inputs."""

    issues: list[ValidationIssue] = []
    try:
        expected = build_disposition_document(
            expected_row_inputs,
            publication_metadata,
            expected_hashes,
        )
    except ProductDispositionError as exc:
        return exc.issues

    if document.schema_version != SCHEMA_VERSION:
        issues.append(issue("SCHEMA_VERSION", f"expected {SCHEMA_VERSION}, got {document.schema_version}", field="schema_version"))
    if document.canonicalization_version != CANONICALIZATION_VERSION:
        issues.append(issue("ROW_EXPRESSION_MISMATCH", f"expected {CANONICALIZATION_VERSION}, got {document.canonicalization_version}", field="canonicalization_version"))
    hash_codes = {
        "workbook_sha256": "STALE_WORKBOOK",
        "generator_sha256": "STALE_GENERATOR",
        "row_identity_module_sha256": "STALE_ROW_IDENTITY_MODULE",
        "disposition_module_sha256": "STALE_DISPOSITION_MODULE",
        "publication_metadata_sha256": "STALE_PUBLICATION_METADATA",
    }
    for field, code in hash_codes.items():
        actual = getattr(document.input_hashes, field)
        required = getattr(expected_hashes, field)
        if actual != required:
            issues.append(issue(code, f"expected {required}, got {actual}", field=field))
    if document.product_order != expected.product_order:
        issues.append(issue("PRODUCT_ORDER_MISMATCH", f"expected {expected.product_order}, got {document.product_order}", field="product_order"))

    actual_rows: dict[str, DispositionRowRecord] = {}
    for row in document.rows:
        if row.row_id in actual_rows:
            issues.append(issue("DUPLICATE_DISPOSITION_ROW", "RowID appears more than once", row_id=row.row_id))
        actual_rows[row.row_id] = row
    expected_rows = {row.row_id: row for row in expected.rows}
    for row_id in sorted(set(expected_rows) - set(actual_rows)):
        issues.append(issue("MISSING_DISPOSITION_ROW", "governed row is absent", row_id=row_id))
    for row_id in sorted(set(actual_rows) - set(expected_rows)):
        issues.append(issue("UNKNOWN_DISPOSITION_ROW", "document row is not governed", row_id=row_id))

    for row_id in sorted(set(actual_rows) & set(expected_rows)):
        actual = actual_rows[row_id]
        required = expected_rows[row_id]
        if actual.location != required.location:
            issues.append(issue("ROW_LOCATION_MISMATCH", f"expected {required.location.text}, got {actual.location.text}", row_id=row_id, field="location"))
        if actual.canonical_row_expression != required.canonical_row_expression:
            issues.append(issue("ROW_EXPRESSION_MISMATCH", "canonical row expression differs", row_id=row_id, field="canonical_row_expression"))
        if actual.source_expression_sha256 != required.source_expression_sha256:
            issues.append(issue("EXPRESSION_HASH_MISMATCH", f"expected {required.source_expression_sha256}, got {actual.source_expression_sha256}", row_id=row_id, field="source_expression_sha256"))
        for field in (
            "subject",
            "predicate",
            "authoritative_target_lexical",
            "mapping_type",
            "coverage_classification",
            "reasoning",
        ):
            if getattr(actual, field) != getattr(required, field):
                issues.append(issue("ROW_EXPRESSION_MISMATCH", "row value differs from governed input", row_id=row_id, field=field))

        actual_axioms: dict[str, DispositionAxiomRecord] = {}
        for axiom in actual.authoritative_axioms:
            if axiom.axiom_id in actual_axioms:
                issues.append(issue("UNKNOWN_AUTHORITATIVE_AXIOM", "axiom ID appears more than once", row_id=row_id, axiom_id=axiom.axiom_id))
            actual_axioms[axiom.axiom_id] = axiom
        required_axioms = {axiom.axiom_id: axiom for axiom in required.authoritative_axioms}
        for axiom_id in sorted(set(required_axioms) - set(actual_axioms)):
            issues.append(issue("MISSING_AUTHORITATIVE_AXIOM", "expected axiom is absent", row_id=row_id, axiom_id=axiom_id))
        for axiom_id in sorted(set(actual_axioms) - set(required_axioms)):
            issues.append(issue("UNKNOWN_AUTHORITATIVE_AXIOM", "unexpected axiom is present", row_id=row_id, axiom_id=axiom_id))
        for axiom_id in sorted(set(actual_axioms) & set(required_axioms)):
            axiom = actual_axioms[axiom_id]
            expected_axiom = required_axioms[axiom_id]
            match = AXIOM_ID_RE.fullmatch(axiom.axiom_id)
            computed = sha256_text(axiom.canonical_expression)
            if match is None or match.group(1) != computed:
                issues.append(issue("AXIOM_ID_MISMATCH", f"canonical expression hashes to sha256:{computed}", row_id=row_id, axiom_id=axiom_id))
            if axiom.canonical_expression != expected_axiom.canonical_expression:
                issues.append(issue("AXIOM_EXPRESSION_MISMATCH", "canonical axiom expression differs", row_id=row_id, axiom_id=axiom_id))
            if tuple(sorted(axiom.referenced_iris)) != expected_axiom.referenced_iris:
                issues.append(issue("REFERENCED_IRI_MISMATCH", f"expected {expected_axiom.referenced_iris}, got {axiom.referenced_iris}", row_id=row_id, axiom_id=axiom_id))
            if axiom.target_category not in TARGET_CATEGORIES:
                issues.append(issue("UNKNOWN_TARGET_CATEGORY", f"unknown category {axiom.target_category!r}", row_id=row_id, axiom_id=axiom_id))
            if axiom.target_category != expected_axiom.target_category:
                issues.append(issue("TARGET_CATEGORY_MISMATCH", f"expected {expected_axiom.target_category}, got {axiom.target_category}", row_id=row_id, axiom_id=axiom_id))
            issues.extend(_validate_disposition_values(axiom.product_dispositions, expected_axiom.product_dispositions, row_id=row_id, axiom_id=axiom_id, field="product_dispositions"))
        if not actual.authoritative_axioms:
            if actual.mapping_type != "explicit_blank" or actual.coverage_classification != "explicitly_unmapped" or actual.predicate is not None or actual.authoritative_target_lexical is not None or actual.row_product_dispositions is None:
                issues.append(issue("INCOMPLETE_ZERO_AXIOM_ROW", "zero-axiom row fields are incomplete", row_id=row_id))
            elif required.row_product_dispositions is not None:
                issues.extend(_validate_disposition_values(actual.row_product_dispositions, required.row_product_dispositions, row_id=row_id, axiom_id="", field="row_product_dispositions"))
        elif actual.row_product_dispositions is not None:
            issues.append(issue("INCOMPLETE_ZERO_AXIOM_ROW", "mapped row must use axiom-level dispositions", row_id=row_id, field="row_product_dispositions"))

    if document.summary != expected.summary:
        for field in SUMMARY_KEYS:
            actual = getattr(document.summary, field)
            required = getattr(expected.summary, field)
            if actual != required:
                issues.append(issue("SUMMARY_MISMATCH", f"expected {required}, got {actual}", field=f"summary.{field}"))
    return sort_issues(issues)


def validate_disposition_file(
    path: str | Path,
    expected_row_inputs: Iterable[DispositionRowInput],
    publication_metadata: PublicationMetadata,
    expected_hashes: RequiredInputHashes,
) -> tuple[DispositionDocument, tuple[ValidationIssue, ...]]:
    """Load, reconcile, and require canonical serialized bytes."""

    source = Path(path)
    document = load_disposition_document(source)
    issues = list(
        validate_disposition_document(
            document,
            expected_row_inputs,
            publication_metadata,
            expected_hashes,
        )
    )
    if source.read_bytes() != serialize_disposition_document(document):
        issues.append(
            issue(
                "NONCANONICAL_SERIALIZATION",
                "loaded bytes differ from canonical disposition serialization",
                field=str(source),
            )
        )
    return document, sort_issues(issues)
