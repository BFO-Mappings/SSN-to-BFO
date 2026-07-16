#!/usr/bin/env python3
"""Select, generate, and validate governed modular ontology products."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rdflib import BNode, Graph, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection

from coms_row_identity import (
    AuthoritativeAxiomIdentity,
    CanonicalRowAudit,
    CanonicalRowExpression,
    CanonicalRowInput,
    ExpressionNode,
    RowLocation,
    canonical_authoritative_axioms,
    canonicalize_processed_row,
    source_expression_sha256,
)
from product_dispositions import (
    DispositionDocument,
    ProductDisposition,
    axiom_input_from_canonical_row,
    classify_target_category,
    derive_product_dispositions,
)
from publication_metadata import (
    METADATA_PREFIXES,
    ProductMetadata,
    PublicationMetadata,
    release_project_imports,
    render_ontology_header_bytes,
    strip_emitted_ontology_header,
    validate_serialized_ontology_header,
)
from release_context import FormalReleaseContext


ALIGNMENT_CORE_KEY = "alignment_core"
ALIGNMENT_CORE_AXIOM_COUNT = 29
ALIGNMENT_CORE_DOMAIN_COUNT = 15
ALIGNMENT_CORE_RANGE_COUNT = 14
ALIGNMENT_CORE_LOGICAL_TRIPLE_COUNT = 53
ALIGNMENT_CORE_TOTAL_TRIPLE_COUNT = 61
ALIGNMENT_CORE_FORMAL_TOTAL_TRIPLE_COUNT = 64
ALIGNMENT_CORE_FIXED_CLOSURE_TRIPLE_COUNT = 1212
ALIGNMENT_CORE_NAMED_TARGET_COUNT = 26
ALIGNMENT_CORE_UNION_TARGET_COUNT = 3

STRICT_BFO_MAPPING_KEY = "strict_bfo_mapping"
STRICT_BFO_AXIOM_COUNT = 19
STRICT_BFO_SUBCLASS_COUNT = 3
STRICT_BFO_EQUIVALENT_CLASS_COUNT = 3
STRICT_BFO_DIRECT_SUBPROPERTY_COUNT = 9
STRICT_BFO_PROPERTY_CHAIN_COUNT = 2
STRICT_BFO_DOMAIN_COUNT = 1
STRICT_BFO_RANGE_COUNT = 1
STRICT_BFO_LOGICAL_TRIPLE_COUNT = 125
STRICT_BFO_TOTAL_TRIPLE_COUNT = 134
STRICT_BFO_FORMAL_TOTAL_TRIPLE_COUNT = 137
STRICT_BFO_UNION_COUNT = 6
STRICT_BFO_INTERSECTION_COUNT = 6
STRICT_BFO_EXISTENTIAL_COUNT = 6
STRICT_BFO_RDF_LIST_COUNT = 14
STRICT_BFO_PROJECT_CLOSURE_AXIOM_COUNT = 48
STRICT_BFO_PROJECT_GRAPH_TRIPLE_COUNT = 195
STRICT_BFO_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT = 194
STRICT_BFO_FIXED_CLOSURE_TRIPLE_COUNT = 14986
STRICT_BFO_FORMAL_PROJECT_GRAPH_TRIPLE_COUNT = 201
STRICT_BFO_FORMAL_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT = 200
STRICT_BFO_FORMAL_FIXED_CLOSURE_TRIPLE_COUNT = 14992
ALIGNMENT_CORE_IMPORT_IRI = (
    "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core"
)

CCO_EXTENSION_KEY = "cco_extension"
CCO_EXTENSION_AXIOM_COUNT = 57
CCO_EXTENSION_CCO_BEARING_COUNT = 25
CCO_EXTENSION_MIXED_COUNT = 32
CCO_EXTENSION_SUBCLASS_COUNT = 31
CCO_EXTENSION_EQUIVALENT_CLASS_COUNT = 7
CCO_EXTENSION_DIRECT_SUBPROPERTY_COUNT = 16
CCO_EXTENSION_PROPERTY_CHAIN_COUNT = 3
CCO_EXTENSION_DOMAIN_COUNT = 0
CCO_EXTENSION_RANGE_COUNT = 0
CCO_EXTENSION_LOGICAL_TRIPLE_COUNT = 934
CCO_EXTENSION_TOTAL_TRIPLE_COUNT = 943
CCO_EXTENSION_FORMAL_TOTAL_TRIPLE_COUNT = 946
CCO_EXTENSION_NAMED_TARGET_COUNT = 20
CCO_EXTENSION_COMPLEX_TARGET_COUNT = 37
CCO_EXTENSION_UNION_COUNT = 7
CCO_EXTENSION_INTERSECTION_COUNT = 86
CCO_EXTENSION_EXISTENTIAL_COUNT = 95
CCO_EXTENSION_RDF_LIST_COUNT = 96
CCO_EXTENSION_SOURCE_TERM_COUNT = 61
CCO_EXTENSION_CCO_TERM_COUNT = 42
CCO_EXTENSION_BFO_TERM_COUNT = 18
CCO_EXTENSION_PROJECT_CLOSURE_AXIOM_COUNT = 105
CCO_EXTENSION_PROJECT_GRAPH_TRIPLE_COUNT = 1138
CCO_EXTENSION_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT = 1136
CCO_EXTENSION_FIXED_CLOSURE_TRIPLE_COUNT = 15928
CCO_EXTENSION_FORMAL_PROJECT_GRAPH_TRIPLE_COUNT = 1147
CCO_EXTENSION_FORMAL_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT = 1145
CCO_EXTENSION_FORMAL_FIXED_CLOSURE_TRIPLE_COUNT = 15937
STRICT_BFO_IMPORT_IRI = (
    "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping"
)

GENERATED_NOTICE = (
    "# GENERATED FILE: produced from mappings/SSN2BFO-COMS.xlsx and governed "
    "product dispositions; do not edit directly."
)

SOURCE_NAMESPACES = (
    "http://www.w3.org/ns/sosa/",
    "http://www.w3.org/ns/sosa/sampling/",
    "http://www.w3.org/ns/ssn/",
    "http://www.w3.org/ns/ssn/systems/",
)
STRUCTURAL_NAMESPACES = (
    str(RDF),
    str(RDFS),
    str(OWL),
)
BFO_NAMESPACE = "http://purl.obolibrary.org/obo/BFO_"
CCO_NAMESPACE = "https://www.commoncoreontologies.org/"
RO_NAMESPACE = "http://purl.obolibrary.org/obo/RO_"

PREFIXES = (
    *METADATA_PREFIXES,
    ("owl", str(OWL)),
    ("rdf", str(RDF)),
    ("rdfs", str(RDFS)),
    ("sampling", "http://www.w3.org/ns/sosa/sampling/"),
    ("sosa", "http://www.w3.org/ns/sosa/"),
    ("ssn", "http://www.w3.org/ns/ssn/"),
    ("ssn-system", "http://www.w3.org/ns/ssn/systems/"),
)
STRICT_BFO_PREFIXES = (("bfo", "http://purl.obolibrary.org/obo/"), *PREFIXES)
CCO_EXTENSION_PREFIXES = (
    ("cco", CCO_NAMESPACE),
    *STRICT_BFO_PREFIXES,
)

BFO_PROJECTION_KEY = "bfo_projection"
BFO_PROJECTION_AXIOM_COUNT = 0
BFO_PROJECTION_LOGICAL_TRIPLE_COUNT = 0
BFO_PROJECTION_TOTAL_TRIPLE_COUNT = 9
BFO_PROJECTION_FORMAL_TOTAL_TRIPLE_COUNT = 12
BFO_PROJECTION_PROJECT_CLOSURE_AXIOM_COUNT = 48
BFO_PROJECTION_PROJECT_GRAPH_TRIPLE_COUNT = 204
BFO_PROJECTION_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT = 202
BFO_PROJECTION_FORMAL_PROJECT_GRAPH_TRIPLE_COUNT = 213
BFO_PROJECTION_FORMAL_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT = 211
BFO_PROJECTION_PREFIXES = (
    *METADATA_PREFIXES,
    ("owl", str(OWL)),
    ("rdf", str(RDF)),
    ("rdfs", str(RDFS)),
)


@dataclass(frozen=True)
class ProductSelectionPolicy:
    categories: tuple[str, ...]
    expected_count: int
    expected_category_counts: tuple[tuple[str, int], ...]
    expected_disposition_totals: tuple[tuple[str, str, str | None, int], ...]


PRODUCT_SELECTION = {
    ALIGNMENT_CORE_KEY: ProductSelectionPolicy(
        ("target_neutral",),
        ALIGNMENT_CORE_AXIOM_COUNT,
        (("target_neutral", ALIGNMENT_CORE_AXIOM_COUNT),),
        (
            ("target_neutral", "emitted_unchanged", None, 29),
            ("bfo_bearing", "not_applicable", "TARGET_SPECIFIC", 19),
            ("cco_bearing", "not_applicable", "TARGET_SPECIFIC", 25),
            ("mixed_bfo_cco", "not_applicable", "TARGET_SPECIFIC", 32),
        ),
    ),
    STRICT_BFO_MAPPING_KEY: ProductSelectionPolicy(
        ("bfo_bearing",),
        STRICT_BFO_AXIOM_COUNT,
        (("bfo_bearing", STRICT_BFO_AXIOM_COUNT),),
        (
            ("target_neutral", "provided_through_import", None, 29),
            ("bfo_bearing", "emitted_unchanged", None, 19),
            ("cco_bearing", "deferred", "NO_APPROVED_TRANSFORMATION_RULE", 25),
            ("mixed_bfo_cco", "deferred", "NO_APPROVED_TRANSFORMATION_RULE", 32),
        ),
    ),
    CCO_EXTENSION_KEY: ProductSelectionPolicy(
        ("cco_bearing", "mixed_bfo_cco"),
        CCO_EXTENSION_AXIOM_COUNT,
        (
            ("cco_bearing", CCO_EXTENSION_CCO_BEARING_COUNT),
            ("mixed_bfo_cco", CCO_EXTENSION_MIXED_COUNT),
        ),
        (
            ("target_neutral", "provided_transitively", None, 29),
            ("bfo_bearing", "provided_through_import", None, 19),
            ("cco_bearing", "emitted_unchanged", None, 25),
            ("mixed_bfo_cco", "emitted_unchanged", None, 32),
        ),
    ),
    BFO_PROJECTION_KEY: ProductSelectionPolicy(
        (),
        BFO_PROJECTION_AXIOM_COUNT,
        (),
        (
            ("target_neutral", "provided_transitively", None, 29),
            ("bfo_bearing", "provided_through_import", None, 19),
            ("cco_bearing", "deferred", "NO_APPROVED_TRANSFORMATION_RULE", 25),
            ("mixed_bfo_cco", "deferred", "NO_APPROVED_TRANSFORMATION_RULE", 32),
        ),
    ),
}

PREDICATE_QNAMES = {
    str(RDFS.subClassOf): "rdfs:subClassOf",
    str(OWL.equivalentClass): "owl:equivalentClass",
    str(RDFS.subPropertyOf): "rdfs:subPropertyOf",
    str(OWL.equivalentProperty): "owl:equivalentProperty",
    str(OWL.propertyChainAxiom): "owl:propertyChainAxiom",
    str(RDFS.domain): "rdfs:domain",
    str(RDFS.range): "rdfs:range",
}

NAMED_DECLARATION_TYPES = frozenset(
    {
        OWL.Class,
        RDFS.Class,
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.AnnotationProperty,
        RDF.Property,
    }
)
AXIOM_ID_RE = re.compile(r"sha256:([0-9a-f]{64})\Z")


@dataclass(frozen=True)
class ModularProductValidationIssue:
    code: str
    row_id: str = ""
    axiom_id: str = ""
    field: str = ""
    message: str = ""

    @property
    def sort_key(self) -> tuple[str, str, str, str, str]:
        return (self.code, self.row_id, self.axiom_id, self.field, self.message)


class ModularProductError(ValueError):
    """One or more expected modular-product failures."""

    def __init__(self, issues: Iterable[ModularProductValidationIssue]):
        self.issues = tuple(sorted(issues, key=lambda value: value.sort_key))
        super().__init__(" | ".join(format_issue(issue) for issue in self.issues))


@dataclass(frozen=True)
class ModularProductMetadata:
    product_key: str
    path: str
    stable_ontology_iri: str


@dataclass(frozen=True)
class SelectedProductAxiom:
    row_id: str
    location: RowLocation
    source_expression_sha256: str
    canonical_row: CanonicalRowExpression
    canonical_input: CanonicalRowInput
    identity: AuthoritativeAxiomIdentity
    target_category: str
    disposition: ProductDisposition

    @property
    def axiom_id(self) -> str:
        return f"sha256:{self.identity.sha256}"


@dataclass(frozen=True)
class SelectedProductRow:
    row_id: str
    location: RowLocation
    axioms: tuple[SelectedProductAxiom, ...]


@dataclass(frozen=True)
class ProductDispositionTotal:
    target_category: str
    status: str
    reason_code: str | None
    count: int


@dataclass(frozen=True)
class ProductDispositionReconciliation:
    product_key: str
    governed_axiom_count: int
    selected_axioms: tuple[SelectedProductAxiom, ...]
    disposition_totals: tuple[ProductDispositionTotal, ...]


@dataclass(frozen=True)
class ModularReasoningResult:
    source_product_key: str
    source_product_sha256: str
    closure_triple_count: int
    return_code: int | None
    reasoned_output_produced: bool
    owl_nothing_count: int | None
    named_unsatisfiable_count: int


@dataclass(frozen=True)
class ModularProductResult:
    metadata: ModularProductMetadata
    selected_rows: tuple[SelectedProductRow, ...]
    serialized_bytes: bytes
    governed_axiom_count: int
    logical_triple_count: int
    ontology_declaration_triple_count: int
    metadata_annotation_count: int
    formal_metadata_annotation_count: int
    total_triple_count: int
    domain_axiom_count: int
    range_axiom_count: int
    named_target_count: int
    union_target_count: int
    subclass_axiom_count: int
    equivalent_class_axiom_count: int
    direct_subproperty_axiom_count: int
    property_chain_axiom_count: int
    intersection_expression_count: int
    existential_restriction_count: int
    rdf_list_count: int
    import_triple_count: int
    sha256: str


def issue(
    code: str,
    message: str,
    *,
    row_id: str = "",
    axiom_id: str = "",
    field: str = "",
) -> ModularProductValidationIssue:
    return ModularProductValidationIssue(code, row_id, axiom_id, field, message)


def format_issue(value: ModularProductValidationIssue) -> str:
    context = " ".join(part for part in (value.row_id, value.axiom_id, value.field) if part)
    return f"ERROR [{value.code}]" + (f" {context}" if context else "") + f": {value.message}"


def _product_metadata(
    publication_metadata: PublicationMetadata,
    product_key: str,
) -> ModularProductMetadata:
    products = {product.key: product for product in publication_metadata.products}
    product = products.get(product_key)
    if product is None:
        raise ModularProductError(
            [issue("UNKNOWN_PRODUCT", f"publication metadata has no product {product_key!r}")]
        )
    return ModularProductMetadata(product.key, product.path, product.stable_ontology_iri)


def _unique_by_row_id(
    values: Iterable[CanonicalRowInput] | Iterable[CanonicalRowAudit],
    *,
    kind: str,
) -> tuple[dict[str, CanonicalRowInput | CanonicalRowAudit], list[ModularProductValidationIssue]]:
    result: dict[str, CanonicalRowInput | CanonicalRowAudit] = {}
    issues: list[ModularProductValidationIssue] = []
    for value in values:
        if value.row_id in result:
            issues.append(
                issue(
                    "DUPLICATE_ROW_ID",
                    f"RowID occurs more than once in {kind}",
                    row_id=value.row_id,
                )
            )
            continue
        result[value.row_id] = value
    return result, issues


def _single_product_disposition(
    values: tuple[tuple[str, ProductDisposition], ...],
    product_key: str,
    *,
    row_id: str,
    axiom_id: str,
    issues: list[ModularProductValidationIssue],
) -> ProductDisposition | None:
    matches = [value for key, value in values if key == product_key]
    if len(matches) != 1:
        issues.append(
            issue(
                "WRONG_PRODUCT_DISPOSITION",
                f"expected exactly one disposition for {product_key!r}, found {len(matches)}",
                row_id=row_id,
                axiom_id=axiom_id,
                field="product_dispositions",
            )
        )
        return None
    return matches[0]


def reconcile_product_axioms(
    product_key: str,
    processed_rows: Iterable[CanonicalRowInput],
    canonical_audits: Iterable[CanonicalRowAudit],
    disposition_document: DispositionDocument,
) -> ProductDispositionReconciliation:
    """Reconcile every governed identity and derive a product selection."""

    issues: list[ModularProductValidationIssue] = []
    selection_policy = PRODUCT_SELECTION.get(product_key)
    if selection_policy is None:
        raise ModularProductError(
            [issue("UNSUPPORTED_PRODUCT", f"generation is not implemented for {product_key!r}")]
        )
    selected_categories = frozenset(selection_policy.categories)

    processed_by_id, duplicate_processed = _unique_by_row_id(
        processed_rows,
        kind="processed rows",
    )
    audit_by_id, duplicate_audits = _unique_by_row_id(
        canonical_audits,
        kind="canonical audits",
    )
    issues.extend(duplicate_processed)
    issues.extend(duplicate_audits)

    disposition_by_id = {}
    for row in disposition_document.rows:
        if row.row_id in disposition_by_id:
            issues.append(
                issue(
                    "DUPLICATE_ROW_ID",
                    "RowID occurs more than once in disposition rows",
                    row_id=row.row_id,
                )
            )
        disposition_by_id[row.row_id] = row

    processed_ids = set(processed_by_id)
    audit_ids = set(audit_by_id)
    disposition_ids = set(disposition_by_id)
    for row_id in sorted(processed_ids - audit_ids):
        issues.append(issue("MISSING_CANONICAL_AUDIT", "processed RowID lacks an audit", row_id=row_id))
    for row_id in sorted(audit_ids - processed_ids):
        issues.append(issue("UNEXPECTED_CANONICAL_AUDIT", "audit RowID is not processed", row_id=row_id))
    for row_id in sorted(processed_ids - disposition_ids):
        issues.append(issue("MISSING_DISPOSITION_ROW", "processed RowID lacks a disposition row", row_id=row_id))
    for row_id in sorted(disposition_ids - processed_ids):
        issues.append(issue("UNEXPECTED_DISPOSITION_ROW", "disposition RowID is not processed", row_id=row_id))

    selected: list[SelectedProductAxiom] = []
    seen_axioms: set[str] = set()
    disposition_counts: dict[tuple[str, str, str | None], int] = {}
    for row_id in sorted(processed_ids & audit_ids & disposition_ids):
        canonical_input = processed_by_id[row_id]
        audit = audit_by_id[row_id]
        disposition_row = disposition_by_id[row_id]
        assert isinstance(canonical_input, CanonicalRowInput)
        assert isinstance(audit, CanonicalRowAudit)

        if canonical_input.location != audit.location or canonical_input.location != disposition_row.location:
            issues.append(
                issue(
                    "ROW_LOCATION_MISMATCH",
                    f"processed {canonical_input.location.text}; audit {audit.location.text}; "
                    f"disposition {disposition_row.location.text}",
                    row_id=row_id,
                    field="location",
                )
            )
        try:
            canonical_expression = canonicalize_processed_row(canonical_input)
            calculated_hash = source_expression_sha256(canonical_expression)
            calculated_axioms = canonical_authoritative_axioms(canonical_input)
        except Exception as exc:
            issues.append(
                issue(
                    "CANONICAL_EXPRESSION_MISMATCH",
                    f"cannot canonicalize processed row: {exc}",
                    row_id=row_id,
                )
            )
            continue
        if canonical_expression != audit.expression or canonical_expression != disposition_row.canonical_row_expression:
            issues.append(
                issue(
                    "CANONICAL_EXPRESSION_MISMATCH",
                    "processed, audit, and disposition canonical row expressions differ",
                    row_id=row_id,
                    field="canonical_row_expression",
                )
            )
        if calculated_hash != audit.source_expression_sha256 or calculated_hash != disposition_row.source_expression_sha256:
            issues.append(
                issue(
                    "EXPRESSION_HASH_MISMATCH",
                    f"computed {calculated_hash}; audit {audit.source_expression_sha256}; "
                    f"disposition {disposition_row.source_expression_sha256}",
                    row_id=row_id,
                    field="source_expression_sha256",
                )
            )

        calculated_by_id = {f"sha256:{value.sha256}": value for value in calculated_axioms}
        audit_by_axiom = {f"sha256:{value.sha256}": value for value in audit.authoritative_axioms}
        disposition_axiom_ids = [value.axiom_id for value in disposition_row.authoritative_axioms]
        if len(disposition_axiom_ids) != len(set(disposition_axiom_ids)):
            issues.append(
                issue(
                    "DUPLICATE_AUTHORITATIVE_AXIOM",
                    "disposition row contains a duplicate axiom ID",
                    row_id=row_id,
                )
            )
        disposition_by_axiom = {value.axiom_id: value for value in disposition_row.authoritative_axioms}
        all_ids = set(calculated_by_id) | set(audit_by_axiom) | set(disposition_by_axiom)
        for axiom_id in sorted(all_ids):
            identity = calculated_by_id.get(axiom_id)
            audited = audit_by_axiom.get(axiom_id)
            disposition_axiom = disposition_by_axiom.get(axiom_id)
            if identity is None or audited is None or disposition_axiom is None:
                issues.append(
                    issue(
                        "AUTHORITATIVE_AXIOM_RECONCILIATION",
                        "axiom identity is missing from processed, audit, or disposition input",
                        row_id=row_id,
                        axiom_id=axiom_id,
                    )
                )
                continue
            if identity.canonical_axiom != audited.canonical_axiom or identity.canonical_axiom != disposition_axiom.canonical_expression:
                issues.append(
                    issue(
                        "CANONICAL_EXPRESSION_MISMATCH",
                        "canonical authoritative expressions differ",
                        row_id=row_id,
                        axiom_id=axiom_id,
                    )
                )
            try:
                category = classify_target_category(
                    axiom_input_from_canonical_row(identity, canonical_input)
                )
            except Exception as exc:
                issues.append(
                    issue(
                        "TARGET_CATEGORY_MISMATCH",
                        f"cannot classify structured axiom: {exc}",
                        row_id=row_id,
                        axiom_id=axiom_id,
                    )
                )
                continue
            if category != disposition_axiom.target_category:
                issues.append(
                    issue(
                        "TARGET_CATEGORY_MISMATCH",
                        f"computed {category}, disposition records {disposition_axiom.target_category}",
                        row_id=row_id,
                        axiom_id=axiom_id,
                    )
                )
            product_disposition = _single_product_disposition(
                disposition_axiom.product_dispositions,
                product_key,
                row_id=row_id,
                axiom_id=axiom_id,
                issues=issues,
            )
            expected = dict(
                derive_product_dispositions(category, disposition_document.product_order)
            )[product_key]
            if product_disposition != expected:
                issues.append(
                    issue(
                        "WRONG_PRODUCT_DISPOSITION",
                        f"expected {expected}, got {product_disposition}",
                        row_id=row_id,
                        axiom_id=axiom_id,
                    )
                )
                continue
            disposition_key = (
                category,
                product_disposition.status,
                product_disposition.reason_code,
            )
            disposition_counts[disposition_key] = (
                disposition_counts.get(disposition_key, 0) + 1
            )
            if category not in selected_categories or product_disposition.status != "emitted_unchanged":
                continue
            if axiom_id in seen_axioms:
                issues.append(
                    issue(
                        "DUPLICATE_AUTHORITATIVE_AXIOM",
                        "selected axiom ID occurs more than once",
                        row_id=row_id,
                        axiom_id=axiom_id,
                    )
                )
                continue
            seen_axioms.add(axiom_id)
            selected.append(
                SelectedProductAxiom(
                    row_id=row_id,
                    location=canonical_input.location,
                    source_expression_sha256=calculated_hash,
                    canonical_row=canonical_expression,
                    canonical_input=canonical_input,
                    identity=identity,
                    target_category=category,
                    disposition=product_disposition,
                )
            )

    if len(selected) != selection_policy.expected_count:
        issues.append(
            issue(
                "PRODUCT_AXIOM_COUNT_MISMATCH",
                f"expected {selection_policy.expected_count} selected axioms, got {len(selected)}",
            )
        )
    category_counts = {
        category: sum(value.target_category == category for value in selected)
        for category in selected_categories
    }
    expected_category_counts = dict(selection_policy.expected_category_counts)
    if category_counts != expected_category_counts:
        issues.append(
            issue(
                "PRODUCT_CATEGORY_COUNT_MISMATCH",
                f"expected category counts {expected_category_counts}, got {category_counts}",
            )
        )
    expected_disposition_counts = {
        (category, status, reason): count
        for category, status, reason, count in selection_policy.expected_disposition_totals
    }
    if disposition_counts != expected_disposition_counts:
        issues.append(
            issue(
                "PRODUCT_DISPOSITION_COUNT_MISMATCH",
                f"expected disposition totals {expected_disposition_counts}, "
                f"got {disposition_counts}",
            )
        )
    if issues:
        raise ModularProductError(issues)
    selected_values = tuple(sorted(selected, key=lambda value: value.axiom_id))
    totals = tuple(
        ProductDispositionTotal(category, status, reason, count)
        for category, status, reason, count in selection_policy.expected_disposition_totals
    )
    return ProductDispositionReconciliation(
        product_key=product_key,
        governed_axiom_count=sum(value.count for value in totals),
        selected_axioms=selected_values,
        disposition_totals=totals,
    )


def select_product_axioms(
    product_key: str,
    processed_rows: Iterable[CanonicalRowInput],
    canonical_audits: Iterable[CanonicalRowAudit],
    disposition_document: DispositionDocument,
) -> tuple[SelectedProductAxiom, ...]:
    """Compatibility wrapper returning directly emitted unchanged axioms."""

    return reconcile_product_axioms(
        product_key,
        processed_rows,
        canonical_audits,
        disposition_document,
    ).selected_axioms


def _iri(value: str) -> str:
    if not value or any(character.isspace() for character in value) or any(
        character in value for character in "<>\"{}|^`\\"
    ):
        raise ModularProductError([issue("INVALID_IRI", f"cannot serialize IRI {value!r}")])
    return f"<{value}>"


def _bnode(axiom_id: str, path: str) -> str:
    match = AXIOM_ID_RE.fullmatch(axiom_id)
    if match is None:
        raise ModularProductError([issue("INVALID_AXIOM_ID", f"invalid axiom ID {axiom_id!r}")])
    safe_path = re.sub(r"[^A-Za-z0-9_]", "_", path)
    return f"_:a{match.group(1)}_{safe_path}"


def _expression_turtle(
    expression: ExpressionNode,
    axiom_id: str,
    path: str,
) -> tuple[str, list[str]]:
    if expression.kind == "named":
        if expression.iri is None:
            raise ModularProductError([issue("UNSUPPORTED_EXPRESSION", "named expression lacks IRI", axiom_id=axiom_id)])
        return _iri(expression.iri), []
    if expression.kind in {"intersection", "union"}:
        if not expression.children:
            raise ModularProductError([issue("UNSUPPORTED_EXPRESSION", f"{expression.kind} has no operands", axiom_id=axiom_id)])
        node = _bnode(axiom_id, path)
        list_nodes = [_bnode(axiom_id, f"{path}_list_{index}") for index in range(len(expression.children))]
        predicate = "owl:intersectionOf" if expression.kind == "intersection" else "owl:unionOf"
        lines = [f"{node} rdf:type owl:Class .", f"{node} {predicate} {list_nodes[0]} ."]
        child_lines: list[str] = []
        for index, child in enumerate(expression.children):
            child_token, nested = _expression_turtle(child, axiom_id, f"{path}_child_{index}")
            rest = list_nodes[index + 1] if index + 1 < len(list_nodes) else "rdf:nil"
            lines.append(f"{list_nodes[index]} rdf:first {child_token} .")
            lines.append(f"{list_nodes[index]} rdf:rest {rest} .")
            child_lines.extend(nested)
        lines.extend(child_lines)
        return node, lines
    if expression.kind == "some":
        if expression.property_iri is None or expression.filler is None:
            raise ModularProductError([issue("UNSUPPORTED_EXPRESSION", "existential restriction is incomplete", axiom_id=axiom_id)])
        node = _bnode(axiom_id, path)
        filler, nested = _expression_turtle(expression.filler, axiom_id, f"{path}_filler")
        return node, [
            f"{node} rdf:type owl:Restriction .",
            f"{node} owl:onProperty {_iri(expression.property_iri)} .",
            f"{node} owl:someValuesFrom {filler} .",
            *nested,
        ]
    raise ModularProductError(
        [issue("UNSUPPORTED_EXPRESSION", f"unsupported expression kind {expression.kind!r}", axiom_id=axiom_id)]
    )


def render_authoritative_axiom_lines(
    row: CanonicalRowInput,
    axiom_id: str,
) -> tuple[str, ...]:
    """Render one governed authoritative axiom without an RDF serializer."""

    if row.predicate_iri is None:
        raise ModularProductError(
            [issue("MISSING_PREDICATE", "selected axiom lacks predicate", row_id=row.row_id, axiom_id=axiom_id)]
        )
    predicate = PREDICATE_QNAMES.get(row.predicate_iri)
    if predicate is None:
        raise ModularProductError(
            [issue("UNSUPPORTED_PREDICATE", f"unsupported predicate {row.predicate_iri}", row_id=row.row_id, axiom_id=axiom_id)]
        )
    if row.expression is not None:
        target, structural = _expression_turtle(row.expression, axiom_id, "target")
        return tuple([f"{_iri(row.subject_iri)} {predicate} {target} .", *structural])
    if row.target_property_iri is not None:
        return (f"{_iri(row.subject_iri)} {predicate} {_iri(row.target_property_iri)} .",)
    if row.property_chain:
        list_nodes = [_bnode(axiom_id, f"chain_list_{index}") for index in range(len(row.property_chain))]
        lines = [f"{_iri(row.subject_iri)} {predicate} {list_nodes[0]} ."]
        for index, member in enumerate(row.property_chain):
            rest = list_nodes[index + 1] if index + 1 < len(list_nodes) else "rdf:nil"
            lines.append(f"{list_nodes[index]} rdf:first {_iri(member)} .")
            lines.append(f"{list_nodes[index]} rdf:rest {rest} .")
        return tuple(lines)
    raise ModularProductError(
        [issue("MISSING_TARGET", "selected axiom lacks a structured target", row_id=row.row_id, axiom_id=axiom_id)]
    )


def _axiom_turtle(value: SelectedProductAxiom) -> list[str]:
    return list(render_authoritative_axiom_lines(value.canonical_input, value.axiom_id))


def _turtle_bytes(
    publication_metadata: PublicationMetadata,
    metadata: ModularProductMetadata,
    selected: tuple[SelectedProductAxiom, ...],
    *,
    imports: tuple[str, ...] = (),
    prefixes: tuple[tuple[str, str], ...] = PREFIXES,
    context: FormalReleaseContext | None = None,
) -> bytes:
    header = render_ontology_header_bytes(
        publication_metadata,
        metadata.product_key,
        imports,
        generated_notice=GENERATED_NOTICE,
        prefixes=prefixes,
        context=context,
    )
    lines = header.decode("utf-8").rstrip("\n").splitlines()
    if selected:
        lines.append("")
    for index, value in enumerate(sorted(selected, key=lambda item: item.axiom_id)):
        lines.extend(_axiom_turtle(value))
        if index + 1 < len(selected):
            lines.append("")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _selected_rows(selected: tuple[SelectedProductAxiom, ...]) -> tuple[SelectedProductRow, ...]:
    by_row: dict[str, list[SelectedProductAxiom]] = {}
    for value in selected:
        by_row.setdefault(value.row_id, []).append(value)
    return tuple(
        SelectedProductRow(
            row_id=row_id,
            location=values[0].location,
            axioms=tuple(sorted(values, key=lambda item: item.axiom_id)),
        )
        for row_id, values in sorted(by_row.items())
    )


def _expression_kind_count(expression: ExpressionNode | None, kind: str) -> int:
    if expression is None:
        return 0
    count = int(expression.kind == kind)
    count += sum(_expression_kind_count(child, kind) for child in expression.children)
    count += _expression_kind_count(expression.filler, kind)
    return count


def build_alignment_core(
    selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
    context: FormalReleaseContext | None = None,
) -> ModularProductResult:
    selected = tuple(sorted(selected_axioms, key=lambda value: value.axiom_id))
    metadata = _product_metadata(publication_metadata, ALIGNMENT_CORE_KEY)
    issues: list[ModularProductValidationIssue] = []
    if len(selected) != ALIGNMENT_CORE_AXIOM_COUNT:
        issues.append(issue("PRODUCT_AXIOM_COUNT_MISMATCH", f"expected 29 axioms, got {len(selected)}"))
    axiom_ids = [value.axiom_id for value in selected]
    if len(axiom_ids) != len(set(axiom_ids)):
        issues.append(issue("DUPLICATE_AUTHORITATIVE_AXIOM", "selected axiom IDs must be unique"))
    row_ids = [value.row_id for value in selected]
    if len(row_ids) != len(set(row_ids)):
        issues.append(issue("DUPLICATE_ROW_ID", "selected RowIDs must be unique"))
    domains = sum(value.canonical_input.mapping_type == "domain" for value in selected)
    ranges = sum(value.canonical_input.mapping_type == "range" for value in selected)
    named = sum(value.canonical_input.expression is not None and value.canonical_input.expression.kind == "named" for value in selected)
    unions = sum(value.canonical_input.expression is not None and value.canonical_input.expression.kind == "union" for value in selected)
    if (domains, ranges, named, unions) != (
        ALIGNMENT_CORE_DOMAIN_COUNT,
        ALIGNMENT_CORE_RANGE_COUNT,
        ALIGNMENT_CORE_NAMED_TARGET_COUNT,
        ALIGNMENT_CORE_UNION_TARGET_COUNT,
    ):
        issues.append(
            issue(
                "PRODUCT_COMPOSITION_MISMATCH",
                f"expected domains/ranges/named/unions 15/14/26/3, got {domains}/{ranges}/{named}/{unions}",
            )
        )
    if any(value.target_category != "target_neutral" for value in selected):
        issues.append(issue("TARGET_CATEGORY_MISMATCH", "all alignment-core axioms must be target-neutral"))
    if issues:
        raise ModularProductError(issues)
    imports = release_project_imports(publication_metadata, ALIGNMENT_CORE_KEY, context) if context else ()
    serialized = _turtle_bytes(
        publication_metadata,
        metadata,
        selected,
        imports=imports,
        context=context,
    )
    graph = Graph().parse(data=serialized.decode("utf-8"), format="turtle")
    logical_count = ALIGNMENT_CORE_LOGICAL_TRIPLE_COUNT
    return ModularProductResult(
        metadata=metadata,
        selected_rows=_selected_rows(selected),
        serialized_bytes=serialized,
        governed_axiom_count=len(selected),
        logical_triple_count=logical_count,
        ontology_declaration_triple_count=1,
        metadata_annotation_count=7,
        formal_metadata_annotation_count=3 if context else 0,
        total_triple_count=len(graph),
        domain_axiom_count=domains,
        range_axiom_count=ranges,
        named_target_count=named,
        union_target_count=unions,
        subclass_axiom_count=0,
        equivalent_class_axiom_count=0,
        direct_subproperty_axiom_count=0,
        property_chain_axiom_count=0,
        intersection_expression_count=0,
        existential_restriction_count=0,
        rdf_list_count=unions,
        import_triple_count=0,
        sha256=hashlib.sha256(serialized).hexdigest(),
    )


def build_strict_bfo_mapping(
    selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
    context: FormalReleaseContext | None = None,
) -> ModularProductResult:
    selected = tuple(sorted(selected_axioms, key=lambda value: value.axiom_id))
    metadata = _product_metadata(publication_metadata, STRICT_BFO_MAPPING_KEY)
    issues: list[ModularProductValidationIssue] = []
    if len(selected) != STRICT_BFO_AXIOM_COUNT:
        issues.append(
            issue(
                "PRODUCT_AXIOM_COUNT_MISMATCH",
                f"expected {STRICT_BFO_AXIOM_COUNT} axioms, got {len(selected)}",
            )
        )
    axiom_ids = [value.axiom_id for value in selected]
    if len(axiom_ids) != len(set(axiom_ids)):
        issues.append(
            issue("DUPLICATE_AUTHORITATIVE_AXIOM", "selected axiom IDs must be unique")
        )
    row_ids = [value.row_id for value in selected]
    if len(row_ids) != len(set(row_ids)):
        issues.append(issue("DUPLICATE_ROW_ID", "selected RowIDs must be unique"))

    subclasses = sum(value.canonical_input.predicate_iri == str(RDFS.subClassOf) for value in selected)
    equivalents = sum(value.canonical_input.predicate_iri == str(OWL.equivalentClass) for value in selected)
    direct_subproperties = sum(value.canonical_input.predicate_iri == str(RDFS.subPropertyOf) for value in selected)
    property_chains = sum(value.canonical_input.mapping_type == "property_chain" for value in selected)
    domains = sum(value.canonical_input.mapping_type == "domain" for value in selected)
    ranges = sum(value.canonical_input.mapping_type == "range" for value in selected)
    unions = sum(_expression_kind_count(value.canonical_input.expression, "union") for value in selected)
    intersections = sum(
        _expression_kind_count(value.canonical_input.expression, "intersection")
        for value in selected
    )
    existentials = sum(_expression_kind_count(value.canonical_input.expression, "some") for value in selected)
    rdf_lists = unions + intersections + property_chains
    composition = (
        subclasses,
        equivalents,
        direct_subproperties,
        property_chains,
        domains,
        ranges,
        unions,
        intersections,
        existentials,
        rdf_lists,
    )
    expected_composition = (
        STRICT_BFO_SUBCLASS_COUNT,
        STRICT_BFO_EQUIVALENT_CLASS_COUNT,
        STRICT_BFO_DIRECT_SUBPROPERTY_COUNT,
        STRICT_BFO_PROPERTY_CHAIN_COUNT,
        STRICT_BFO_DOMAIN_COUNT,
        STRICT_BFO_RANGE_COUNT,
        STRICT_BFO_UNION_COUNT,
        STRICT_BFO_INTERSECTION_COUNT,
        STRICT_BFO_EXISTENTIAL_COUNT,
        STRICT_BFO_RDF_LIST_COUNT,
    )
    if composition != expected_composition:
        issues.append(
            issue(
                "PRODUCT_COMPOSITION_MISMATCH",
                f"expected {expected_composition}, got {composition}",
            )
        )
    if any(value.target_category != "bfo_bearing" for value in selected):
        issues.append(
            issue("TARGET_CATEGORY_MISMATCH", "all strict-BFO axioms must be BFO-bearing")
        )
    if issues:
        raise ModularProductError(issues)

    imports = (
        release_project_imports(publication_metadata, STRICT_BFO_MAPPING_KEY, context)
        if context
        else (ALIGNMENT_CORE_IMPORT_IRI,)
    )
    serialized = _turtle_bytes(
        publication_metadata,
        metadata,
        selected,
        imports=imports,
        prefixes=STRICT_BFO_PREFIXES,
        context=context,
    )
    graph = Graph().parse(data=serialized.decode("utf-8"), format="turtle")
    return ModularProductResult(
        metadata=metadata,
        selected_rows=_selected_rows(selected),
        serialized_bytes=serialized,
        governed_axiom_count=len(selected),
        logical_triple_count=STRICT_BFO_LOGICAL_TRIPLE_COUNT,
        ontology_declaration_triple_count=1,
        metadata_annotation_count=7,
        formal_metadata_annotation_count=3 if context else 0,
        total_triple_count=len(graph),
        domain_axiom_count=domains,
        range_axiom_count=ranges,
        named_target_count=direct_subproperties,
        union_target_count=unions,
        subclass_axiom_count=subclasses,
        equivalent_class_axiom_count=equivalents,
        direct_subproperty_axiom_count=direct_subproperties,
        property_chain_axiom_count=property_chains,
        intersection_expression_count=intersections,
        existential_restriction_count=existentials,
        rdf_list_count=rdf_lists,
        import_triple_count=1,
        sha256=hashlib.sha256(serialized).hexdigest(),
    )


def build_bfo_projection(
    selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
    context: FormalReleaseContext | None = None,
) -> ModularProductResult:
    selected = tuple(sorted(selected_axioms, key=lambda value: value.axiom_id))
    metadata = _product_metadata(publication_metadata, BFO_PROJECTION_KEY)
    if selected:
        raise ModularProductError(
            [
                issue(
                    "UNAPPROVED_PROJECTION_AXIOM",
                    f"expected zero direct projection axioms, got {len(selected)}",
                )
            ]
        )

    imports = (
        release_project_imports(publication_metadata, BFO_PROJECTION_KEY, context)
        if context
        else (STRICT_BFO_IMPORT_IRI,)
    )
    serialized = _turtle_bytes(
        publication_metadata,
        metadata,
        (),
        imports=imports,
        prefixes=BFO_PROJECTION_PREFIXES,
        context=context,
    )
    graph = Graph().parse(data=serialized.decode("utf-8"), format="turtle")
    return ModularProductResult(
        metadata=metadata,
        selected_rows=(),
        serialized_bytes=serialized,
        governed_axiom_count=0,
        logical_triple_count=0,
        ontology_declaration_triple_count=1,
        metadata_annotation_count=7,
        formal_metadata_annotation_count=3 if context else 0,
        total_triple_count=len(graph),
        domain_axiom_count=0,
        range_axiom_count=0,
        named_target_count=0,
        union_target_count=0,
        subclass_axiom_count=0,
        equivalent_class_axiom_count=0,
        direct_subproperty_axiom_count=0,
        property_chain_axiom_count=0,
        intersection_expression_count=0,
        existential_restriction_count=0,
        rdf_list_count=0,
        import_triple_count=1,
        sha256=hashlib.sha256(serialized).hexdigest(),
    )


def build_cco_extension(
    selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
    context: FormalReleaseContext | None = None,
) -> ModularProductResult:
    selected = tuple(sorted(selected_axioms, key=lambda value: value.axiom_id))
    metadata = _product_metadata(publication_metadata, CCO_EXTENSION_KEY)
    issues: list[ModularProductValidationIssue] = []
    if len(selected) != CCO_EXTENSION_AXIOM_COUNT:
        issues.append(
            issue(
                "PRODUCT_AXIOM_COUNT_MISMATCH",
                f"expected {CCO_EXTENSION_AXIOM_COUNT} axioms, got {len(selected)}",
            )
        )
    axiom_ids = [value.axiom_id for value in selected]
    if len(axiom_ids) != len(set(axiom_ids)):
        issues.append(
            issue("DUPLICATE_AUTHORITATIVE_AXIOM", "selected axiom IDs must be unique")
        )
    row_ids = [value.row_id for value in selected]
    if len(row_ids) != len(set(row_ids)):
        issues.append(issue("DUPLICATE_ROW_ID", "selected RowIDs must be unique"))

    category_counts = {
        "cco_bearing": sum(value.target_category == "cco_bearing" for value in selected),
        "mixed_bfo_cco": sum(
            value.target_category == "mixed_bfo_cco" for value in selected
        ),
    }
    expected_category_counts = {
        "cco_bearing": CCO_EXTENSION_CCO_BEARING_COUNT,
        "mixed_bfo_cco": CCO_EXTENSION_MIXED_COUNT,
    }
    if category_counts != expected_category_counts:
        issues.append(
            issue(
                "PRODUCT_CATEGORY_COUNT_MISMATCH",
                f"expected {expected_category_counts}, got {category_counts}",
            )
        )

    subclasses = sum(
        value.canonical_input.predicate_iri == str(RDFS.subClassOf)
        for value in selected
    )
    equivalents = sum(
        value.canonical_input.predicate_iri == str(OWL.equivalentClass)
        for value in selected
    )
    direct_subproperties = sum(
        value.canonical_input.predicate_iri == str(RDFS.subPropertyOf)
        for value in selected
    )
    property_chains = sum(
        value.canonical_input.mapping_type == "property_chain" for value in selected
    )
    domains = sum(value.canonical_input.mapping_type == "domain" for value in selected)
    ranges = sum(value.canonical_input.mapping_type == "range" for value in selected)
    named_targets = sum(
        value.canonical_input.target_property_iri is not None
        or (
            value.canonical_input.expression is not None
            and value.canonical_input.expression.kind == "named"
        )
        for value in selected
    )
    unions = sum(
        _expression_kind_count(value.canonical_input.expression, "union")
        for value in selected
    )
    intersections = sum(
        _expression_kind_count(value.canonical_input.expression, "intersection")
        for value in selected
    )
    existentials = sum(
        _expression_kind_count(value.canonical_input.expression, "some")
        for value in selected
    )
    rdf_lists = unions + intersections + property_chains
    composition = (
        subclasses,
        equivalents,
        direct_subproperties,
        property_chains,
        domains,
        ranges,
        named_targets,
        len(selected) - named_targets,
        unions,
        intersections,
        existentials,
        rdf_lists,
    )
    expected_composition = (
        CCO_EXTENSION_SUBCLASS_COUNT,
        CCO_EXTENSION_EQUIVALENT_CLASS_COUNT,
        CCO_EXTENSION_DIRECT_SUBPROPERTY_COUNT,
        CCO_EXTENSION_PROPERTY_CHAIN_COUNT,
        CCO_EXTENSION_DOMAIN_COUNT,
        CCO_EXTENSION_RANGE_COUNT,
        CCO_EXTENSION_NAMED_TARGET_COUNT,
        CCO_EXTENSION_COMPLEX_TARGET_COUNT,
        CCO_EXTENSION_UNION_COUNT,
        CCO_EXTENSION_INTERSECTION_COUNT,
        CCO_EXTENSION_EXISTENTIAL_COUNT,
        CCO_EXTENSION_RDF_LIST_COUNT,
    )
    if composition != expected_composition:
        issues.append(
            issue(
                "PRODUCT_COMPOSITION_MISMATCH",
                f"expected {expected_composition}, got {composition}",
            )
        )
    if issues:
        raise ModularProductError(issues)

    imports = (
        release_project_imports(publication_metadata, CCO_EXTENSION_KEY, context)
        if context
        else (STRICT_BFO_IMPORT_IRI,)
    )
    serialized = _turtle_bytes(
        publication_metadata,
        metadata,
        selected,
        imports=imports,
        prefixes=CCO_EXTENSION_PREFIXES,
        context=context,
    )
    graph = Graph().parse(data=serialized.decode("utf-8"), format="turtle")
    return ModularProductResult(
        metadata=metadata,
        selected_rows=_selected_rows(selected),
        serialized_bytes=serialized,
        governed_axiom_count=len(selected),
        logical_triple_count=CCO_EXTENSION_LOGICAL_TRIPLE_COUNT,
        ontology_declaration_triple_count=1,
        metadata_annotation_count=7,
        formal_metadata_annotation_count=3 if context else 0,
        total_triple_count=len(graph),
        domain_axiom_count=domains,
        range_axiom_count=ranges,
        named_target_count=named_targets,
        union_target_count=unions,
        subclass_axiom_count=subclasses,
        equivalent_class_axiom_count=equivalents,
        direct_subproperty_axiom_count=direct_subproperties,
        property_chain_axiom_count=property_chains,
        intersection_expression_count=intersections,
        existential_restriction_count=existentials,
        rdf_list_count=rdf_lists,
        import_triple_count=1,
        sha256=hashlib.sha256(serialized).hexdigest(),
    )


def serialize_modular_product(result: ModularProductResult) -> bytes:
    return result.serialized_bytes


def _metadata_validation_issues(
    _graph: Graph,
    serialized_bytes: bytes,
    publication_metadata: PublicationMetadata,
    product_key: str,
    expected_imports: tuple[str, ...],
    prefixes: tuple[tuple[str, str], ...],
    context: FormalReleaseContext | None = None,
) -> tuple[ModularProductValidationIssue, ...]:
    return tuple(
        issue(value.code, value.message, field=value.field)
        for value in validate_serialized_ontology_header(
            serialized_bytes,
            publication_metadata,
            product_key,
            expected_imports,
            generated_notice=GENERATED_NOTICE,
            prefixes=prefixes,
            mode="release" if context else "development",
            context=context,
        )
    )


def _canonical_graph_expression(graph: Graph, node: URIRef | BNode) -> str:
    if isinstance(node, URIRef):
        return f"<{node}>"
    union = list(graph.objects(node, OWL.unionOf))
    intersection = list(graph.objects(node, OWL.intersectionOf))
    if len(union) == 1 or len(intersection) == 1:
        predicate = OWL.unionOf if union else OWL.intersectionOf
        list_node = union[0] if union else intersection[0]
        values: set[str] = set()

        def collect(value: URIRef | BNode) -> None:
            nested = list(graph.objects(value, predicate)) if isinstance(value, BNode) else []
            if len(nested) == 1:
                for member in Collection(graph, nested[0]):
                    collect(member)
                return
            values.add(_canonical_graph_expression(graph, value))

        for value in Collection(graph, list_node):
            collect(value)
        operator = "ObjectUnionOf" if predicate == OWL.unionOf else "ObjectIntersectionOf"
        return f"{operator}({' '.join(sorted(values))})"
    properties = list(graph.objects(node, OWL.onProperty))
    fillers = list(graph.objects(node, OWL.someValuesFrom))
    if len(properties) == 1 and len(fillers) == 1 and isinstance(properties[0], URIRef):
        return f"ObjectSomeValuesFrom(<{properties[0]}> {_canonical_graph_expression(graph, fillers[0])})"
    raise ValueError(f"unsupported anonymous expression {node}")


def _canonical_graph_axioms(
    graph: Graph,
    *,
    ignore_unsupported: bool = False,
) -> dict[str, tuple[str, URIRef, URIRef | BNode]]:
    result: dict[str, tuple[str, URIRef, URIRef | BNode]] = {}
    predicates = (
        RDFS.subClassOf,
        OWL.equivalentClass,
        RDFS.subPropertyOf,
        OWL.equivalentProperty,
        OWL.propertyChainAxiom,
        RDFS.domain,
        RDFS.range,
    )
    for predicate in predicates:
        for subject, _, target in graph.triples((None, predicate, None)):
            if not isinstance(subject, URIRef):
                continue
            try:
                if predicate == RDFS.subClassOf:
                    canonical = f"SubClassOf(<{subject}> {_canonical_graph_expression(graph, target)})"
                elif predicate == OWL.equivalentClass:
                    canonical = f"EquivalentClasses(<{subject}> {_canonical_graph_expression(graph, target)})"
                elif predicate == RDFS.subPropertyOf:
                    canonical = f"SubObjectPropertyOf(<{subject}> <{target}>)"
                elif predicate == OWL.equivalentProperty:
                    canonical = f"EquivalentObjectProperties(<{subject}> <{target}>)"
                elif predicate == OWL.propertyChainAxiom:
                    members = " ".join(f"<{value}>" for value in Collection(graph, target))
                    canonical = f"SubObjectPropertyOf(ObjectPropertyChain({members}) <{subject}>)"
                elif predicate == RDFS.domain:
                    canonical = f"ObjectPropertyDomain(<{subject}> {_canonical_graph_expression(graph, target)})"
                else:
                    canonical = f"ObjectPropertyRange(<{subject}> {_canonical_graph_expression(graph, target)})"
            except (TypeError, ValueError):
                if ignore_unsupported:
                    continue
                raise
            result["sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()] = (
                canonical,
                subject,
                target,
            )
    return result


def _allowed_logical_iri(value: str) -> bool:
    return value.startswith(SOURCE_NAMESPACES) or value.startswith(STRUCTURAL_NAMESPACES)


def _reachable_bnodes(graph: Graph, root: BNode) -> set[BNode]:
    found: set[BNode] = set()
    pending = [root]
    while pending:
        current = pending.pop()
        if current in found:
            continue
        found.add(current)
        for _, _, value in graph.triples((current, None, None)):
            if isinstance(value, BNode):
                pending.append(value)
    return found


def validate_alignment_core(
    serialized_bytes: bytes,
    selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
    fixed_source_closure: Graph | None = None,
    integrated_graph: Graph | None = None,
    context: FormalReleaseContext | None = None,
) -> tuple[ModularProductValidationIssue, ...]:
    selected = tuple(sorted(selected_axioms, key=lambda value: value.axiom_id))
    metadata = _product_metadata(publication_metadata, ALIGNMENT_CORE_KEY)
    issues: list[ModularProductValidationIssue] = []
    try:
        text = serialized_bytes.decode("utf-8")
        graph = Graph().parse(data=text, format="turtle")
    except Exception as exc:
        return (issue("TURTLE_PARSE", f"cannot strictly parse UTF-8 Turtle: {exc}"),)

    expected = build_alignment_core(selected, publication_metadata, context)
    if serialized_bytes != expected.serialized_bytes:
        issues.append(issue("NONDETERMINISTIC_SERIALIZATION", "bytes differ from canonical modular-product serialization"))
    ontology_iri = URIRef(metadata.stable_ontology_iri)
    expected_imports = release_project_imports(
        publication_metadata, ALIGNMENT_CORE_KEY, context
    ) if context else ()
    issues.extend(
        _metadata_validation_issues(
            graph,
            serialized_bytes,
            publication_metadata,
            ALIGNMENT_CORE_KEY,
            expected_imports,
            PREFIXES,
            context,
        )
    )
    declarations = set(graph.subjects(RDF.type, OWL.Ontology))
    if declarations != {ontology_iri}:
        issues.append(issue("ONTOLOGY_DECLARATION_MISMATCH", f"expected only {ontology_iri}, got {sorted(map(str, declarations))}"))
    imports = list(graph.triples((None, OWL.imports, None)))
    if imports:
        issues.append(issue("PROHIBITED_IMPORT", f"expected zero owl:imports triples, got {len(imports)}"))
    expected_total = (
        ALIGNMENT_CORE_FORMAL_TOTAL_TRIPLE_COUNT if context else ALIGNMENT_CORE_TOTAL_TRIPLE_COUNT
    )
    if len(graph) != expected_total:
        issues.append(
            issue(
                "TOTAL_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_total}, got {len(graph)}",
            )
        )
    logical_graph = strip_emitted_ontology_header(
        graph,
        publication_metadata,
        ALIGNMENT_CORE_KEY,
        expected_imports,
        context,
    )
    if len(logical_graph) != ALIGNMENT_CORE_LOGICAL_TRIPLE_COUNT:
        issues.append(issue("LOGICAL_TRIPLE_COUNT_MISMATCH", f"expected 53, got {len(logical_graph)}"))

    core_axioms = _canonical_graph_axioms(graph)
    selected_by_id = {value.axiom_id: value for value in selected}
    for axiom_id in sorted(set(selected_by_id) - set(core_axioms)):
        issues.append(issue("MISSING_PRODUCT_AXIOM", "selected axiom is absent from alignment core", row_id=selected_by_id[axiom_id].row_id, axiom_id=axiom_id))
    for axiom_id in sorted(set(core_axioms) - set(selected_by_id)):
        issues.append(issue("UNEXPECTED_PRODUCT_AXIOM", "alignment core contains an ungoverned axiom", axiom_id=axiom_id))
    for axiom_id in sorted(set(core_axioms) & set(selected_by_id)):
        if core_axioms[axiom_id][0] != selected_by_id[axiom_id].identity.canonical_axiom:
            issues.append(issue("CANONICAL_EXPRESSION_MISMATCH", "core canonical expression differs", row_id=selected_by_id[axiom_id].row_id, axiom_id=axiom_id))

    for subject, predicate, target in logical_graph:
        for value in (subject, predicate, target):
            if isinstance(value, URIRef) and not _allowed_logical_iri(str(value)):
                code = "PROHIBITED_LOGICAL_VOCABULARY" if str(value).startswith((BFO_NAMESPACE, CCO_NAMESPACE, RO_NAMESPACE)) else "UNEXPECTED_LOGICAL_VOCABULARY"
                issues.append(issue(code, f"logical triple contains unapproved IRI {value}"))
    for subject, _, target in graph.triples((None, RDF.type, None)):
        if isinstance(subject, URIRef) and str(subject).startswith(SOURCE_NAMESPACES) and target in NAMED_DECLARATION_TYPES:
            issues.append(issue("COPIED_SOURCE_DECLARATION", f"named source declaration is prohibited: {subject} rdf:type {target}"))
    if any(True for _ in graph.triples((None, RDF.type, OWL.Axiom))):
        issues.append(issue("ANNOTATION_ONLY_PSEUDO_MAPPING", "owl:Axiom records are prohibited"))

    union_roots = [target for _, _, target in graph.triples((None, None, None)) if isinstance(target, BNode) and (target, OWL.unionOf, None) in graph]
    if len(set(union_roots)) != ALIGNMENT_CORE_UNION_TARGET_COUNT:
        issues.append(issue("UNION_COUNT_MISMATCH", f"expected 3 distinct union expressions, got {len(set(union_roots))}"))
    closures = [_reachable_bnodes(graph, root) for root in set(union_roots)]
    for index, first in enumerate(closures):
        for second in closures[index + 1:]:
            if first & second:
                issues.append(issue("SHARED_ANONYMOUS_EXPRESSION", "distinct governed union axioms share anonymous structure"))
    for root in set(union_roots):
        list_nodes = list(graph.objects(root, OWL.unionOf))
        if len(list_nodes) != 1 or len(list(Collection(graph, list_nodes[0]))) != 3:
            issues.append(issue("INVALID_RDF_LIST", f"union expression {root} must contain exactly three ordered members"))

    if integrated_graph is not None:
        root_axioms = _canonical_graph_axioms(integrated_graph)
        for axiom_id, value in sorted(selected_by_id.items()):
            root_value = root_axioms.get(axiom_id)
            if root_value is None:
                issues.append(issue("MISSING_INTEGRATED_AXIOM", "selected axiom is absent from integrated root", row_id=value.row_id, axiom_id=axiom_id))
            elif root_value[0] != value.identity.canonical_axiom:
                issues.append(issue("INTEGRATED_AXIOM_MISMATCH", "integrated root canonical expression differs", row_id=value.row_id, axiom_id=axiom_id))
    if fixed_source_closure is not None:
        closure_axioms = _canonical_graph_axioms(
            fixed_source_closure,
            ignore_unsupported=True,
        )
        missing_closure_axioms = set(selected_by_id) - set(closure_axioms)
        if missing_closure_axioms:
            issues.append(
                issue(
                    "SOURCE_CLOSURE_MISMATCH",
                    "fixed source closure lacks selected axioms: "
                    + ", ".join(sorted(missing_closure_axioms)),
                )
            )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def validate_strict_bfo_mapping(
    serialized_bytes: bytes,
    selected_axioms: Iterable[SelectedProductAxiom],
    alignment_core_bytes: bytes,
    alignment_core_selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
    integrated_graph: Graph | None = None,
    fixed_semantic_closure: Graph | None = None,
    context: FormalReleaseContext | None = None,
) -> tuple[ModularProductValidationIssue, ...]:
    selected = tuple(sorted(selected_axioms, key=lambda value: value.axiom_id))
    core_selected = tuple(
        sorted(alignment_core_selected_axioms, key=lambda value: value.axiom_id)
    )
    metadata = _product_metadata(publication_metadata, STRICT_BFO_MAPPING_KEY)
    issues: list[ModularProductValidationIssue] = []
    try:
        graph = Graph().parse(data=serialized_bytes.decode("utf-8"), format="turtle")
    except Exception as exc:
        return (issue("TURTLE_PARSE", f"cannot strictly parse UTF-8 Turtle: {exc}"),)

    expected = build_strict_bfo_mapping(selected, publication_metadata, context)
    if serialized_bytes != expected.serialized_bytes:
        issues.append(
            issue(
                "NONDETERMINISTIC_SERIALIZATION",
                "bytes differ from canonical strict-BFO serialization",
            )
        )
    ontology_iri = URIRef(metadata.stable_ontology_iri)
    expected_import_values = (
        release_project_imports(publication_metadata, STRICT_BFO_MAPPING_KEY, context)
        if context
        else (ALIGNMENT_CORE_IMPORT_IRI,)
    )
    expected_import = URIRef(expected_import_values[0])
    issues.extend(
        _metadata_validation_issues(
            graph,
            serialized_bytes,
            publication_metadata,
            STRICT_BFO_MAPPING_KEY,
            expected_import_values,
            STRICT_BFO_PREFIXES,
            context,
        )
    )
    declarations = set(graph.subjects(RDF.type, OWL.Ontology))
    if declarations != {ontology_iri}:
        issues.append(
            issue(
                "ONTOLOGY_DECLARATION_MISMATCH",
                f"expected only {ontology_iri}, got {sorted(map(str, declarations))}",
            )
        )
    imports = set(graph.triples((None, OWL.imports, None)))
    expected_imports = {(ontology_iri, OWL.imports, expected_import)}
    if imports != expected_imports:
        issues.append(
            issue(
                "IMPORT_POLICY_MISMATCH",
                f"expected only alignment-core import, got {sorted(map(str, imports))}",
            )
        )
    expected_total = STRICT_BFO_FORMAL_TOTAL_TRIPLE_COUNT if context else STRICT_BFO_TOTAL_TRIPLE_COUNT
    if len(graph) != expected_total:
        issues.append(
            issue(
                "TOTAL_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_total}, got {len(graph)}",
            )
        )

    logical_graph = strip_emitted_ontology_header(
        graph,
        publication_metadata,
        STRICT_BFO_MAPPING_KEY,
        expected_import_values,
        context,
    )
    if len(logical_graph) != STRICT_BFO_LOGICAL_TRIPLE_COUNT:
        issues.append(
            issue(
                "LOGICAL_TRIPLE_COUNT_MISMATCH",
                f"expected {STRICT_BFO_LOGICAL_TRIPLE_COUNT}, got {len(logical_graph)}",
            )
        )

    strict_axioms = _canonical_graph_axioms(graph)
    selected_by_id = {value.axiom_id: value for value in selected}
    for axiom_id in sorted(set(selected_by_id) - set(strict_axioms)):
        issues.append(
            issue(
                "MISSING_PRODUCT_AXIOM",
                "selected axiom is absent from strict BFO mapping",
                row_id=selected_by_id[axiom_id].row_id,
                axiom_id=axiom_id,
            )
        )
    for axiom_id in sorted(set(strict_axioms) - set(selected_by_id)):
        issues.append(
            issue(
                "UNEXPECTED_PRODUCT_AXIOM",
                "strict BFO mapping contains an ungoverned axiom",
                axiom_id=axiom_id,
            )
        )
    for axiom_id in sorted(set(strict_axioms) & set(selected_by_id)):
        if strict_axioms[axiom_id][0] != selected_by_id[axiom_id].identity.canonical_axiom:
            issues.append(
                issue(
                    "CANONICAL_EXPRESSION_MISMATCH",
                    "strict-BFO canonical expression differs",
                    row_id=selected_by_id[axiom_id].row_id,
                    axiom_id=axiom_id,
                )
            )

    for subject, predicate, target in logical_graph:
        for value in (subject, predicate, target):
            if not isinstance(value, URIRef):
                continue
            iri = str(value)
            if iri.startswith(SOURCE_NAMESPACES) or iri.startswith(STRUCTURAL_NAMESPACES):
                continue
            if iri.startswith(BFO_NAMESPACE):
                continue
            code = (
                "PROHIBITED_LOGICAL_VOCABULARY"
                if iri.startswith((CCO_NAMESPACE, RO_NAMESPACE))
                else "UNEXPECTED_LOGICAL_VOCABULARY"
            )
            issues.append(issue(code, f"logical triple contains unapproved IRI {value}"))
    for subject, _, target in graph.triples((None, RDF.type, None)):
        if not isinstance(subject, URIRef) or target not in NAMED_DECLARATION_TYPES:
            continue
        if str(subject).startswith(SOURCE_NAMESPACES):
            issues.append(
                issue(
                    "COPIED_SOURCE_DECLARATION",
                    f"named source declaration is prohibited: {subject} rdf:type {target}",
                )
            )
        if str(subject).startswith(BFO_NAMESPACE):
            issues.append(
                issue(
                    "COPIED_BFO_DECLARATION",
                    f"named BFO declaration is prohibited: {subject} rdf:type {target}",
                )
            )
    if any(True for _ in graph.triples((None, RDF.type, OWL.Axiom))):
        issues.append(
            issue("ANNOTATION_ONLY_PSEUDO_MAPPING", "owl:Axiom records are prohibited")
        )

    unions = set(graph.subjects(OWL.unionOf, None))
    intersections = set(graph.subjects(OWL.intersectionOf, None))
    restrictions = set(graph.subjects(OWL.someValuesFrom, None))
    chains = set(graph.subjects(OWL.propertyChainAxiom, None))
    list_heads = [
        value
        for predicate in (OWL.unionOf, OWL.intersectionOf, OWL.propertyChainAxiom)
        for value in graph.objects(None, predicate)
    ]
    structure = (
        len(unions),
        len(intersections),
        len(restrictions),
        len(chains),
        len(list_heads),
    )
    expected_structure = (
        STRICT_BFO_UNION_COUNT,
        STRICT_BFO_INTERSECTION_COUNT,
        STRICT_BFO_EXISTENTIAL_COUNT,
        STRICT_BFO_PROPERTY_CHAIN_COUNT,
        STRICT_BFO_RDF_LIST_COUNT,
    )
    if structure != expected_structure:
        issues.append(
            issue(
                "PRODUCT_STRUCTURE_MISMATCH",
                f"expected unions/intersections/restrictions/chains/lists "
                f"{expected_structure}, got {structure}",
            )
        )
    for chain in chains:
        heads = list(graph.objects(chain, OWL.propertyChainAxiom))
        if len(heads) != 1 or len(list(Collection(graph, heads[0]))) != 3:
            issues.append(
                issue(
                    "INVALID_RDF_LIST",
                    f"property chain {chain} must contain exactly three ordered members",
                )
            )
    if any(True for _ in logical_graph.triples((None, OWL.inverseOf, None))):
        issues.append(issue("UNEXPECTED_INVERSE_EXPRESSION", "inverse expressions are absent"))

    core_issues = validate_alignment_core(
        alignment_core_bytes,
        core_selected,
        publication_metadata,
        context=context,
    )
    issues.extend(core_issues)
    try:
        core_graph = Graph().parse(
            data=alignment_core_bytes.decode("utf-8"),
            format="turtle",
        )
    except Exception as exc:
        issues.append(issue("ALIGNMENT_CORE_PARSE", f"cannot parse alignment core: {exc}"))
        core_graph = Graph()
    core_axioms = _canonical_graph_axioms(core_graph) if len(core_graph) else {}
    core_selected_by_id = {value.axiom_id: value for value in core_selected}
    overlap = set(strict_axioms) & set(core_axioms)
    if overlap:
        issues.append(
            issue(
                "DIRECT_CORE_AXIOM_OVERLAP",
                "strict and alignment-core direct graphs overlap: "
                + ", ".join(sorted(overlap)),
            )
        )
    expected_closure_ids = set(selected_by_id) | set(core_selected_by_id)
    actual_closure_ids = set(strict_axioms) | set(core_axioms)
    if expected_closure_ids != actual_closure_ids:
        issues.append(
            issue(
                "PROJECT_CLOSURE_AXIOM_MISMATCH",
                "project-module governed axiom IDs do not reconcile",
            )
        )
    if len(actual_closure_ids) != STRICT_BFO_PROJECT_CLOSURE_AXIOM_COUNT:
        issues.append(
            issue(
                "PROJECT_CLOSURE_COUNT_MISMATCH",
                f"expected {STRICT_BFO_PROJECT_CLOSURE_AXIOM_COUNT}, "
                f"got {len(actual_closure_ids)}",
            )
        )
    project_graph = Graph()
    for triple in graph:
        project_graph.add(triple)
    for triple in core_graph:
        project_graph.add(triple)
    expected_project_count = (
        STRICT_BFO_FORMAL_PROJECT_GRAPH_TRIPLE_COUNT
        if context
        else STRICT_BFO_PROJECT_GRAPH_TRIPLE_COUNT
    )
    if len(project_graph) != expected_project_count:
        issues.append(
            issue(
                "PROJECT_GRAPH_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_project_count}, got {len(project_graph)}",
            )
        )
    for triple in list(project_graph.triples((None, OWL.imports, None))):
        project_graph.remove(triple)
    expected_local_count = (
        STRICT_BFO_FORMAL_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT
        if context
        else STRICT_BFO_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT
    )
    if len(project_graph) != expected_local_count:
        issues.append(
            issue(
                "LOCAL_PROJECT_GRAPH_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_local_count}, "
                f"got {len(project_graph)}",
            )
        )

    if integrated_graph is not None:
        root_axioms = _canonical_graph_axioms(integrated_graph)
        for axiom_id, value in sorted(
            {**core_selected_by_id, **selected_by_id}.items()
        ):
            root_value = root_axioms.get(axiom_id)
            if root_value is None:
                issues.append(
                    issue(
                        "MISSING_INTEGRATED_AXIOM",
                        "project-module axiom is absent from integrated root",
                        row_id=value.row_id,
                        axiom_id=axiom_id,
                    )
                )
            elif root_value[0] != value.identity.canonical_axiom:
                issues.append(
                    issue(
                        "INTEGRATED_AXIOM_MISMATCH",
                        "integrated root canonical expression differs",
                        row_id=value.row_id,
                        axiom_id=axiom_id,
                    )
                )

    if fixed_semantic_closure is not None:
        if any(True for _ in fixed_semantic_closure.triples((None, OWL.imports, None))):
            issues.append(
                issue("FIXED_CLOSURE_IMPORT", "fixed semantic closure retains imports")
            )
        expected_fixed_count = (
            STRICT_BFO_FORMAL_FIXED_CLOSURE_TRIPLE_COUNT
            if context
            else STRICT_BFO_FIXED_CLOSURE_TRIPLE_COUNT
        )
        if len(fixed_semantic_closure) != expected_fixed_count:
            issues.append(
                issue(
                    "FIXED_CLOSURE_COUNT_MISMATCH",
                    f"expected {expected_fixed_count}, "
                    f"got {len(fixed_semantic_closure)}",
                )
            )
        bfo_iris = {
            iri
            for value in selected
            for iri in axiom_input_from_canonical_row(
                value.identity,
                value.canonical_input,
            ).target_iris
            if iri.startswith(BFO_NAMESPACE)
        }
        unresolved = sorted(
            iri
            for iri in bfo_iris
            if not any(True for _ in fixed_semantic_closure.triples((URIRef(iri), None, None)))
        )
        if unresolved:
            issues.append(
                issue(
                    "UNRESOLVED_BFO_IRI",
                    "BFO IRIs are absent from pinned validation closure: "
                    + ", ".join(unresolved),
                )
            )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def validate_bfo_projection(
    serialized_bytes: bytes,
    disposition_reconciliation: ProductDispositionReconciliation,
    strict_bfo_bytes: bytes,
    strict_selected_axioms: Iterable[SelectedProductAxiom],
    alignment_core_bytes: bytes,
    alignment_core_selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
    integrated_graph: Graph | None = None,
    strict_reasoning_result: ModularReasoningResult | None = None,
    context: FormalReleaseContext | None = None,
) -> tuple[ModularProductValidationIssue, ...]:
    strict_selected = tuple(
        sorted(strict_selected_axioms, key=lambda value: value.axiom_id)
    )
    core_selected = tuple(
        sorted(alignment_core_selected_axioms, key=lambda value: value.axiom_id)
    )
    metadata = _product_metadata(publication_metadata, BFO_PROJECTION_KEY)
    issues: list[ModularProductValidationIssue] = []
    try:
        graph = Graph().parse(data=serialized_bytes.decode("utf-8"), format="turtle")
    except Exception as exc:
        return (issue("TURTLE_PARSE", f"cannot strictly parse UTF-8 Turtle: {exc}"),)

    expected = build_bfo_projection((), publication_metadata, context)
    if serialized_bytes != expected.serialized_bytes:
        issues.append(
            issue(
                "NONDETERMINISTIC_SERIALIZATION",
                "bytes differ from canonical BFO-projection serialization",
            )
        )

    ontology_iri = URIRef(metadata.stable_ontology_iri)
    expected_import_values = (
        release_project_imports(publication_metadata, BFO_PROJECTION_KEY, context)
        if context
        else (STRICT_BFO_IMPORT_IRI,)
    )
    expected_import = URIRef(expected_import_values[0])
    issues.extend(
        _metadata_validation_issues(
            graph,
            serialized_bytes,
            publication_metadata,
            BFO_PROJECTION_KEY,
            expected_import_values,
            BFO_PROJECTION_PREFIXES,
            context,
        )
    )
    declarations = set(graph.subjects(RDF.type, OWL.Ontology))
    if declarations != {ontology_iri}:
        issues.append(
            issue(
                "ONTOLOGY_DECLARATION_MISMATCH",
                f"expected only {ontology_iri}, got {sorted(map(str, declarations))}",
            )
        )
    imports = set(graph.triples((None, OWL.imports, None)))
    expected_imports = {(ontology_iri, OWL.imports, expected_import)}
    if imports != expected_imports:
        issues.append(
            issue(
                "IMPORT_POLICY_MISMATCH",
                f"expected only strict-BFO import, got {sorted(map(str, imports))}",
            )
        )
    expected_total = (
        BFO_PROJECTION_FORMAL_TOTAL_TRIPLE_COUNT if context else BFO_PROJECTION_TOTAL_TRIPLE_COUNT
    )
    if len(graph) != expected_total:
        issues.append(
            issue(
                "TOTAL_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_total}, got {len(graph)}",
            )
        )
    logical_graph = strip_emitted_ontology_header(
        graph,
        publication_metadata,
        BFO_PROJECTION_KEY,
        expected_import_values,
        context,
    )
    if len(logical_graph) != BFO_PROJECTION_LOGICAL_TRIPLE_COUNT:
        issues.append(
            issue(
                "LOGICAL_TRIPLE_COUNT_MISMATCH",
                f"expected zero direct logical triples, got {len(logical_graph)}",
            )
        )
    projection_axioms = _canonical_graph_axioms(graph)
    if projection_axioms:
        issues.append(
            issue(
                "UNAPPROVED_PROJECTION_AXIOM",
                "BFO projection contains direct governed or transformed axioms: "
                + ", ".join(sorted(projection_axioms)),
            )
        )
    if any(isinstance(value, BNode) for value in graph.all_nodes()):
        issues.append(issue("UNEXPECTED_BLANK_NODE", "BFO projection must not contain blank nodes"))
    if any(True for _ in graph.triples((None, RDF.first, None))) or any(
        True for _ in graph.triples((None, RDF.rest, None))
    ):
        issues.append(issue("UNEXPECTED_RDF_LIST", "BFO projection must not contain RDF lists"))
    unexpected_direct_iris = sorted(
        {
            str(value)
            for value in logical_graph.all_nodes()
            if isinstance(value, URIRef)
        }
    )
    if unexpected_direct_iris:
        issues.append(
            issue(
                "UNEXPECTED_LOGICAL_VOCABULARY",
                "projection graph contains unapproved IRIs: "
                + ", ".join(unexpected_direct_iris),
            )
        )
    declaration_triples = set(graph.triples((None, RDF.type, None)))
    if declaration_triples != {(ontology_iri, RDF.type, OWL.Ontology)}:
        issues.append(
            issue(
                "COPIED_DECLARATION",
                "projection graph contains a declaration other than its ontology declaration",
            )
        )
    if any(True for _ in graph.triples((None, RDF.type, OWL.Axiom))):
        issues.append(
            issue("ANNOTATION_ONLY_PSEUDO_MAPPING", "owl:Axiom records are prohibited")
        )

    expected_totals = tuple(
        ProductDispositionTotal(category, status, reason, count)
        for category, status, reason, count in PRODUCT_SELECTION[
            BFO_PROJECTION_KEY
        ].expected_disposition_totals
    )
    if disposition_reconciliation.product_key != BFO_PROJECTION_KEY:
        issues.append(
            issue(
                "PRODUCT_RECONCILIATION_MISMATCH",
                f"expected {BFO_PROJECTION_KEY!r}, got "
                f"{disposition_reconciliation.product_key!r}",
            )
        )
    if disposition_reconciliation.governed_axiom_count != 105:
        issues.append(
            issue(
                "PRODUCT_RECONCILIATION_MISMATCH",
                f"expected 105 governed axioms, got "
                f"{disposition_reconciliation.governed_axiom_count}",
            )
        )
    if disposition_reconciliation.selected_axioms:
        issues.append(
            issue(
                "UNAPPROVED_PROJECTION_AXIOM",
                f"expected zero selected projection axioms, got "
                f"{len(disposition_reconciliation.selected_axioms)}",
            )
        )
    if disposition_reconciliation.disposition_totals != expected_totals:
        issues.append(
            issue(
                "PRODUCT_DISPOSITION_COUNT_MISMATCH",
                f"expected {expected_totals}, got "
                f"{disposition_reconciliation.disposition_totals}",
            )
        )

    try:
        issues.extend(
            validate_strict_bfo_mapping(
                strict_bfo_bytes,
                strict_selected,
                alignment_core_bytes,
                core_selected,
                publication_metadata,
                integrated_graph=integrated_graph,
                context=context,
            )
        )
    except ModularProductError as exc:
        issues.extend(exc.issues)

    try:
        strict_graph = Graph().parse(
            data=strict_bfo_bytes.decode("utf-8"), format="turtle"
        )
    except Exception as exc:
        issues.append(issue("STRICT_BFO_PARSE", f"cannot parse strict BFO mapping: {exc}"))
        strict_graph = Graph()
    try:
        core_graph = Graph().parse(
            data=alignment_core_bytes.decode("utf-8"), format="turtle"
        )
    except Exception as exc:
        issues.append(issue("ALIGNMENT_CORE_PARSE", f"cannot parse alignment core: {exc}"))
        core_graph = Graph()

    strict_axioms = _canonical_graph_axioms(strict_graph) if len(strict_graph) else {}
    core_axioms = _canonical_graph_axioms(core_graph) if len(core_graph) else {}
    strict_selected_ids = {value.axiom_id for value in strict_selected}
    core_selected_ids = {value.axiom_id for value in core_selected}
    overlap = set(strict_axioms) & set(core_axioms)
    if overlap:
        issues.append(
            issue(
                "DIRECT_CORE_AXIOM_OVERLAP",
                "strict and alignment-core direct graphs overlap: "
                + ", ".join(sorted(overlap)),
            )
        )
    expected_closure_ids = strict_selected_ids | core_selected_ids
    actual_closure_ids = set(strict_axioms) | set(core_axioms)
    if actual_closure_ids != expected_closure_ids:
        issues.append(
            issue(
                "PROJECT_CLOSURE_AXIOM_MISMATCH",
                "projection closure does not equal the selected strict/core axiom set",
            )
        )
    if len(actual_closure_ids) != BFO_PROJECTION_PROJECT_CLOSURE_AXIOM_COUNT:
        issues.append(
            issue(
                "PROJECT_CLOSURE_COUNT_MISMATCH",
                f"expected {BFO_PROJECTION_PROJECT_CLOSURE_AXIOM_COUNT}, "
                f"got {len(actual_closure_ids)}",
            )
        )

    project_graph = Graph()
    for source_graph in (graph, strict_graph, core_graph):
        for triple in source_graph:
            project_graph.add(triple)
    expected_project_count = (
        BFO_PROJECTION_FORMAL_PROJECT_GRAPH_TRIPLE_COUNT
        if context
        else BFO_PROJECTION_PROJECT_GRAPH_TRIPLE_COUNT
    )
    if len(project_graph) != expected_project_count:
        issues.append(
            issue(
                "PROJECT_GRAPH_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_project_count}, "
                f"got {len(project_graph)}",
            )
        )
    cco_iris = sorted(
        {
            str(value)
            for value in project_graph.all_nodes()
            if isinstance(value, URIRef) and str(value).startswith(CCO_NAMESPACE)
        }
    )
    if cco_iris:
        issues.append(
            issue(
                "PROHIBITED_LOGICAL_VOCABULARY",
                "projection project closure contains CCO IRIs: " + ", ".join(cco_iris),
            )
        )
    for triple in list(project_graph.triples((None, OWL.imports, None))):
        project_graph.remove(triple)
    expected_local_count = (
        BFO_PROJECTION_FORMAL_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT
        if context
        else BFO_PROJECTION_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT
    )
    if len(project_graph) != expected_local_count:
        issues.append(
            issue(
                "LOCAL_PROJECT_GRAPH_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_local_count}, "
                f"got {len(project_graph)}",
            )
        )

    strict_sha256 = hashlib.sha256(strict_bfo_bytes).hexdigest()
    if context is not None and strict_reasoning_result is not None:
        issues.append(
            issue(
                "FORMAL_PROJECTION_REASONING_REUSE",
                "formal projection validation requires an independent projection closure result",
            )
        )
    elif context is None and strict_reasoning_result is None:
        issues.append(
            issue(
                "STRICT_REASONING_RESULT_MISSING",
                "same-transaction strict-BFO reasoning result is required",
            )
        )
    elif context is None:
        if strict_reasoning_result.source_product_key != STRICT_BFO_MAPPING_KEY:
            issues.append(
                issue(
                    "STRICT_REASONING_RESULT_MISMATCH",
                    f"unexpected reasoning source "
                    f"{strict_reasoning_result.source_product_key!r}",
                )
            )
        if strict_reasoning_result.source_product_sha256 != strict_sha256:
            issues.append(
                issue(
                    "STRICT_REASONING_RESULT_MISMATCH",
                    "strict reasoning result does not belong to supplied strict bytes",
                )
            )
        if strict_reasoning_result.closure_triple_count != STRICT_BFO_FIXED_CLOSURE_TRIPLE_COUNT:
            issues.append(
                issue(
                    "STRICT_REASONING_RESULT_MISMATCH",
                    f"expected strict closure count {STRICT_BFO_FIXED_CLOSURE_TRIPLE_COUNT}, "
                    f"got {strict_reasoning_result.closure_triple_count}",
                )
            )
        if strict_reasoning_result.return_code != 0:
            issues.append(issue("STRICT_REASONING_FAILED", "strict HermiT return code is not zero"))
        if not strict_reasoning_result.reasoned_output_produced:
            issues.append(issue("STRICT_REASONING_FAILED", "strict reasoned output was not produced"))
        if strict_reasoning_result.owl_nothing_count != 0:
            issues.append(
                issue(
                    "STRICT_REASONING_FAILED",
                    f"strict owl:Nothing-derived named-class count is "
                    f"{strict_reasoning_result.owl_nothing_count}",
                )
            )
        if strict_reasoning_result.named_unsatisfiable_count != 0:
            issues.append(
                issue(
                    "STRICT_REASONING_FAILED",
                    f"strict named-unsatisfiable count is "
                    f"{strict_reasoning_result.named_unsatisfiable_count}",
                )
            )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def validate_cco_extension(
    serialized_bytes: bytes,
    selected_axioms: Iterable[SelectedProductAxiom],
    strict_bfo_bytes: bytes,
    strict_selected_axioms: Iterable[SelectedProductAxiom],
    alignment_core_bytes: bytes,
    alignment_core_selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
    integrated_graph: Graph | None = None,
    fixed_semantic_closure: Graph | None = None,
    source_dependency_graph: Graph | None = None,
    merged_cco_bfo_dependency_graph: Graph | None = None,
    context: FormalReleaseContext | None = None,
) -> tuple[ModularProductValidationIssue, ...]:
    selected = tuple(sorted(selected_axioms, key=lambda value: value.axiom_id))
    strict_selected = tuple(
        sorted(strict_selected_axioms, key=lambda value: value.axiom_id)
    )
    core_selected = tuple(
        sorted(alignment_core_selected_axioms, key=lambda value: value.axiom_id)
    )
    metadata = _product_metadata(publication_metadata, CCO_EXTENSION_KEY)
    issues: list[ModularProductValidationIssue] = []
    try:
        graph = Graph().parse(data=serialized_bytes.decode("utf-8"), format="turtle")
    except Exception as exc:
        return (issue("TURTLE_PARSE", f"cannot strictly parse UTF-8 Turtle: {exc}"),)

    expected = build_cco_extension(selected, publication_metadata, context)
    if serialized_bytes != expected.serialized_bytes:
        issues.append(
            issue(
                "NONDETERMINISTIC_SERIALIZATION",
                "bytes differ from canonical CCO-extension serialization",
            )
        )
    ontology_iri = URIRef(metadata.stable_ontology_iri)
    expected_import_values = (
        release_project_imports(publication_metadata, CCO_EXTENSION_KEY, context)
        if context
        else (STRICT_BFO_IMPORT_IRI,)
    )
    expected_import = URIRef(expected_import_values[0])
    issues.extend(
        _metadata_validation_issues(
            graph,
            serialized_bytes,
            publication_metadata,
            CCO_EXTENSION_KEY,
            expected_import_values,
            CCO_EXTENSION_PREFIXES,
            context,
        )
    )
    declarations = set(graph.subjects(RDF.type, OWL.Ontology))
    if declarations != {ontology_iri}:
        issues.append(
            issue(
                "ONTOLOGY_DECLARATION_MISMATCH",
                f"expected only {ontology_iri}, got {sorted(map(str, declarations))}",
            )
        )
    imports = set(graph.triples((None, OWL.imports, None)))
    expected_imports = {(ontology_iri, OWL.imports, expected_import)}
    if imports != expected_imports:
        issues.append(
            issue(
                "IMPORT_POLICY_MISMATCH",
                f"expected only strict-BFO import, got {sorted(map(str, imports))}",
            )
        )
    expected_total = CCO_EXTENSION_FORMAL_TOTAL_TRIPLE_COUNT if context else CCO_EXTENSION_TOTAL_TRIPLE_COUNT
    if len(graph) != expected_total:
        issues.append(
            issue(
                "TOTAL_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_total}, got {len(graph)}",
            )
        )

    logical_graph = strip_emitted_ontology_header(
        graph,
        publication_metadata,
        CCO_EXTENSION_KEY,
        expected_import_values,
        context,
    )
    if len(logical_graph) != CCO_EXTENSION_LOGICAL_TRIPLE_COUNT:
        issues.append(
            issue(
                "LOGICAL_TRIPLE_COUNT_MISMATCH",
                f"expected {CCO_EXTENSION_LOGICAL_TRIPLE_COUNT}, got {len(logical_graph)}",
            )
        )

    cco_axioms = _canonical_graph_axioms(graph)
    selected_by_id = {value.axiom_id: value for value in selected}
    for axiom_id in sorted(set(selected_by_id) - set(cco_axioms)):
        issues.append(
            issue(
                "MISSING_PRODUCT_AXIOM",
                "selected axiom is absent from CCO extension",
                row_id=selected_by_id[axiom_id].row_id,
                axiom_id=axiom_id,
            )
        )
    for axiom_id in sorted(set(cco_axioms) - set(selected_by_id)):
        issues.append(
            issue(
                "UNEXPECTED_PRODUCT_AXIOM",
                "CCO extension contains an ungoverned axiom",
                axiom_id=axiom_id,
            )
        )
    for axiom_id in sorted(set(cco_axioms) & set(selected_by_id)):
        if cco_axioms[axiom_id][0] != selected_by_id[axiom_id].identity.canonical_axiom:
            issues.append(
                issue(
                    "CANONICAL_EXPRESSION_MISMATCH",
                    "CCO-extension canonical expression differs",
                    row_id=selected_by_id[axiom_id].row_id,
                    axiom_id=axiom_id,
                )
            )

    for subject, predicate, target in logical_graph:
        for value in (subject, predicate, target):
            if not isinstance(value, URIRef):
                continue
            iri = str(value)
            if iri.startswith(SOURCE_NAMESPACES) or iri.startswith(STRUCTURAL_NAMESPACES):
                continue
            if iri.startswith((BFO_NAMESPACE, CCO_NAMESPACE)):
                continue
            code = (
                "PROHIBITED_LOGICAL_VOCABULARY"
                if iri.startswith(RO_NAMESPACE)
                else "UNEXPECTED_LOGICAL_VOCABULARY"
            )
            issues.append(issue(code, f"logical triple contains unapproved IRI {value}"))
    for subject, _, target in graph.triples((None, RDF.type, None)):
        if not isinstance(subject, URIRef) or target not in NAMED_DECLARATION_TYPES:
            continue
        iri = str(subject)
        if iri.startswith(SOURCE_NAMESPACES):
            issues.append(
                issue(
                    "COPIED_SOURCE_DECLARATION",
                    f"named source declaration is prohibited: {subject} rdf:type {target}",
                )
            )
        if iri.startswith(BFO_NAMESPACE):
            issues.append(
                issue(
                    "COPIED_BFO_DECLARATION",
                    f"named BFO declaration is prohibited: {subject} rdf:type {target}",
                )
            )
        if iri.startswith(CCO_NAMESPACE):
            issues.append(
                issue(
                    "COPIED_CCO_DECLARATION",
                    f"named CCO declaration is prohibited: {subject} rdf:type {target}",
                )
            )
    if any(True for _ in graph.triples((None, RDF.type, OWL.Axiom))):
        issues.append(
            issue("ANNOTATION_ONLY_PSEUDO_MAPPING", "owl:Axiom records are prohibited")
        )

    unions = set(graph.subjects(OWL.unionOf, None))
    intersections = set(graph.subjects(OWL.intersectionOf, None))
    restrictions = set(graph.subjects(OWL.someValuesFrom, None))
    chains = set(graph.subjects(OWL.propertyChainAxiom, None))
    list_heads = [
        value
        for predicate in (OWL.unionOf, OWL.intersectionOf, OWL.propertyChainAxiom)
        for value in graph.objects(None, predicate)
    ]
    structure = (
        len(unions),
        len(intersections),
        len(restrictions),
        len(chains),
        len(list_heads),
    )
    expected_structure = (
        CCO_EXTENSION_UNION_COUNT,
        CCO_EXTENSION_INTERSECTION_COUNT,
        CCO_EXTENSION_EXISTENTIAL_COUNT,
        CCO_EXTENSION_PROPERTY_CHAIN_COUNT,
        CCO_EXTENSION_RDF_LIST_COUNT,
    )
    if structure != expected_structure:
        issues.append(
            issue(
                "PRODUCT_STRUCTURE_MISMATCH",
                f"expected unions/intersections/restrictions/chains/lists "
                f"{expected_structure}, got {structure}",
            )
        )
    for head in list_heads:
        try:
            if not list(Collection(graph, head)):
                raise ValueError("empty list")
        except (KeyError, ValueError) as exc:
            issues.append(issue("INVALID_RDF_LIST", f"invalid RDF list {head}: {exc}"))
    if any(True for _ in logical_graph.triples((None, OWL.inverseOf, None))):
        issues.append(issue("UNEXPECTED_INVERSE_EXPRESSION", "inverse expressions are absent"))

    strict_issues = validate_strict_bfo_mapping(
        strict_bfo_bytes,
        strict_selected,
        alignment_core_bytes,
        core_selected,
        publication_metadata,
        context=context,
    )
    issues.extend(strict_issues)
    try:
        strict_graph = Graph().parse(
            data=strict_bfo_bytes.decode("utf-8"),
            format="turtle",
        )
    except Exception as exc:
        issues.append(issue("STRICT_BFO_PARSE", f"cannot parse strict BFO mapping: {exc}"))
        strict_graph = Graph()
    try:
        core_graph = Graph().parse(
            data=alignment_core_bytes.decode("utf-8"),
            format="turtle",
        )
    except Exception as exc:
        issues.append(issue("ALIGNMENT_CORE_PARSE", f"cannot parse alignment core: {exc}"))
        core_graph = Graph()

    strict_axioms = _canonical_graph_axioms(strict_graph) if len(strict_graph) else {}
    core_axioms = _canonical_graph_axioms(core_graph) if len(core_graph) else {}
    strict_selected_by_id = {value.axiom_id: value for value in strict_selected}
    core_selected_by_id = {value.axiom_id: value for value in core_selected}
    overlaps = {
        "CCO/strict": set(cco_axioms) & set(strict_axioms),
        "CCO/core": set(cco_axioms) & set(core_axioms),
        "strict/core": set(strict_axioms) & set(core_axioms),
    }
    for label, overlap in overlaps.items():
        if overlap:
            issues.append(
                issue(
                    "DIRECT_PRODUCT_AXIOM_OVERLAP",
                    f"{label} direct graphs overlap: {', '.join(sorted(overlap))}",
                )
            )
    expected_closure_ids = (
        set(selected_by_id) | set(strict_selected_by_id) | set(core_selected_by_id)
    )
    actual_closure_ids = set(cco_axioms) | set(strict_axioms) | set(core_axioms)
    if expected_closure_ids != actual_closure_ids:
        issues.append(
            issue(
                "PROJECT_CLOSURE_AXIOM_MISMATCH",
                "project-module governed axiom IDs do not reconcile",
            )
        )
    if len(actual_closure_ids) != CCO_EXTENSION_PROJECT_CLOSURE_AXIOM_COUNT:
        issues.append(
            issue(
                "PROJECT_CLOSURE_COUNT_MISMATCH",
                f"expected {CCO_EXTENSION_PROJECT_CLOSURE_AXIOM_COUNT}, "
                f"got {len(actual_closure_ids)}",
            )
        )
    project_graph = Graph()
    for product_graph in (graph, strict_graph, core_graph):
        for triple in product_graph:
            project_graph.add(triple)
    expected_project_count = (
        CCO_EXTENSION_FORMAL_PROJECT_GRAPH_TRIPLE_COUNT
        if context
        else CCO_EXTENSION_PROJECT_GRAPH_TRIPLE_COUNT
    )
    if len(project_graph) != expected_project_count:
        issues.append(
            issue(
                "PROJECT_GRAPH_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_project_count}, "
                f"got {len(project_graph)}",
            )
        )
    for triple in list(project_graph.triples((None, OWL.imports, None))):
        project_graph.remove(triple)
    expected_local_count = (
        CCO_EXTENSION_FORMAL_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT
        if context
        else CCO_EXTENSION_LOCAL_PROJECT_GRAPH_TRIPLE_COUNT
    )
    if len(project_graph) != expected_local_count:
        issues.append(
            issue(
                "LOCAL_PROJECT_GRAPH_TRIPLE_COUNT_MISMATCH",
                f"expected {expected_local_count}, "
                f"got {len(project_graph)}",
            )
        )

    if integrated_graph is not None:
        root_axioms = _canonical_graph_axioms(integrated_graph)
        all_selected = {
            **core_selected_by_id,
            **strict_selected_by_id,
            **selected_by_id,
        }
        if set(root_axioms) != set(all_selected):
            issues.append(
                issue(
                    "INTEGRATED_AXIOM_SET_MISMATCH",
                    "project-module axiom IDs do not equal the governed root axiom IDs",
                )
            )
        for axiom_id, value in sorted(all_selected.items()):
            root_value = root_axioms.get(axiom_id)
            if root_value is None:
                issues.append(
                    issue(
                        "MISSING_INTEGRATED_AXIOM",
                        "project-module axiom is absent from integrated root",
                        row_id=value.row_id,
                        axiom_id=axiom_id,
                    )
                )
            elif root_value[0] != value.identity.canonical_axiom:
                issues.append(
                    issue(
                        "INTEGRATED_AXIOM_MISMATCH",
                        "integrated root canonical expression differs",
                        row_id=value.row_id,
                        axiom_id=axiom_id,
                    )
                )

    referenced_source_iris: set[str] = set()
    referenced_target_iris: set[str] = set()
    for value in selected:
        axiom_input = axiom_input_from_canonical_row(
            value.identity,
            value.canonical_input,
        )
        for iri in (axiom_input.subject_iri, *axiom_input.target_iris):
            if iri.startswith(SOURCE_NAMESPACES):
                referenced_source_iris.add(iri)
            elif iri.startswith((CCO_NAMESPACE, BFO_NAMESPACE)):
                referenced_target_iris.add(iri)
    source_count = len(referenced_source_iris)
    cco_count = sum(iri.startswith(CCO_NAMESPACE) for iri in referenced_target_iris)
    bfo_count = sum(iri.startswith(BFO_NAMESPACE) for iri in referenced_target_iris)
    expected_term_counts = (
        CCO_EXTENSION_SOURCE_TERM_COUNT,
        CCO_EXTENSION_CCO_TERM_COUNT,
        CCO_EXTENSION_BFO_TERM_COUNT,
    )
    if (source_count, cco_count, bfo_count) != expected_term_counts:
        issues.append(
            issue(
                "REFERENCED_TERM_COUNT_MISMATCH",
                f"expected source/CCO/BFO terms {expected_term_counts}, "
                f"got {(source_count, cco_count, bfo_count)}",
            )
        )
    if source_dependency_graph is not None:
        unresolved_source = sorted(
            iri
            for iri in referenced_source_iris
            if not any(
                True
                for _ in source_dependency_graph.triples((URIRef(iri), None, None))
            )
        )
        if unresolved_source:
            issues.append(
                issue(
                    "UNRESOLVED_SOURCE_IRI",
                    "source IRIs are absent from pinned source files: "
                    + ", ".join(unresolved_source),
                )
            )
    if merged_cco_bfo_dependency_graph is not None:
        unresolved_targets = sorted(
            iri
            for iri in referenced_target_iris
            if not any(
                True
                for _ in merged_cco_bfo_dependency_graph.triples(
                    (URIRef(iri), None, None)
                )
            )
        )
        if unresolved_targets:
            issues.append(
                issue(
                    "UNRESOLVED_TARGET_IRI",
                    "CCO/BFO IRIs are absent from pinned merged dependency: "
                    + ", ".join(unresolved_targets),
                )
            )

    if fixed_semantic_closure is not None:
        if any(True for _ in fixed_semantic_closure.triples((None, OWL.imports, None))):
            issues.append(
                issue("FIXED_CLOSURE_IMPORT", "fixed semantic closure retains imports")
            )
        expected_fixed_count = (
            CCO_EXTENSION_FORMAL_FIXED_CLOSURE_TRIPLE_COUNT
            if context
            else CCO_EXTENSION_FIXED_CLOSURE_TRIPLE_COUNT
        )
        if len(fixed_semantic_closure) != expected_fixed_count:
            issues.append(
                issue(
                    "FIXED_CLOSURE_COUNT_MISMATCH",
                    f"expected {expected_fixed_count}, "
                    f"got {len(fixed_semantic_closure)}",
                )
            )
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def build_fixed_validation_closure(
    serialized_products: Iterable[bytes],
    dependency_paths: Iterable[Path],
    cleanup_triples: Iterable[tuple[URIRef, URIRef, URIRef]] = (),
) -> Graph:
    """Build an explicit offline product/dependency closure without imports."""

    graph = Graph()
    for path in dependency_paths:
        graph.parse(path, format="turtle")
    for serialized in serialized_products:
        graph.parse(data=serialized.decode("utf-8"), format="turtle")
    for triple in list(graph.triples((None, OWL.imports, None))):
        graph.remove(triple)
    for triple in cleanup_triples:
        graph.remove(triple)
    return graph


def build_fixed_source_closure(
    serialized_bytes: bytes,
    source_paths: Iterable[Path],
) -> Graph:
    """Build an offline validation closure and remove all import edges."""

    return build_fixed_validation_closure((serialized_bytes,), source_paths)
