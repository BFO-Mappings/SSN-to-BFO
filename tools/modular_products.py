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
)
from publication_metadata import ProductMetadata, PublicationMetadata


ALIGNMENT_CORE_KEY = "alignment_core"
ALIGNMENT_CORE_AXIOM_COUNT = 29
ALIGNMENT_CORE_DOMAIN_COUNT = 15
ALIGNMENT_CORE_RANGE_COUNT = 14
ALIGNMENT_CORE_LOGICAL_TRIPLE_COUNT = 53
ALIGNMENT_CORE_TOTAL_TRIPLE_COUNT = 54
ALIGNMENT_CORE_NAMED_TARGET_COUNT = 26
ALIGNMENT_CORE_UNION_TARGET_COUNT = 3

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
    ("owl", str(OWL)),
    ("rdf", str(RDF)),
    ("rdfs", str(RDFS)),
    ("sampling", "http://www.w3.org/ns/sosa/sampling/"),
    ("sosa", "http://www.w3.org/ns/sosa/"),
    ("ssn", "http://www.w3.org/ns/ssn/"),
    ("ssn-system", "http://www.w3.org/ns/ssn/systems/"),
)

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
class ModularProductResult:
    metadata: ModularProductMetadata
    selected_rows: tuple[SelectedProductRow, ...]
    serialized_bytes: bytes
    governed_axiom_count: int
    logical_triple_count: int
    ontology_header_triple_count: int
    total_triple_count: int
    domain_axiom_count: int
    range_axiom_count: int
    named_target_count: int
    union_target_count: int
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


def select_product_axioms(
    product_key: str,
    processed_rows: Iterable[CanonicalRowInput],
    canonical_audits: Iterable[CanonicalRowAudit],
    disposition_document: DispositionDocument,
) -> tuple[SelectedProductAxiom, ...]:
    """Reconcile governed identities and select unchanged alignment-core axioms."""

    issues: list[ModularProductValidationIssue] = []
    if product_key != ALIGNMENT_CORE_KEY:
        raise ModularProductError(
            [issue("UNSUPPORTED_PRODUCT", f"generation is not implemented for {product_key!r}")]
        )

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
            expected = (
                ProductDisposition("emitted_unchanged")
                if category == "target_neutral"
                else ProductDisposition("not_applicable", "TARGET_SPECIFIC")
            )
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
            if category != "target_neutral":
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

    if len(selected) != ALIGNMENT_CORE_AXIOM_COUNT:
        issues.append(
            issue(
                "PRODUCT_AXIOM_COUNT_MISMATCH",
                f"expected {ALIGNMENT_CORE_AXIOM_COUNT} selected axioms, got {len(selected)}",
            )
        )
    if issues:
        raise ModularProductError(issues)
    return tuple(sorted(selected, key=lambda value: value.axiom_id))


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


def _axiom_turtle(value: SelectedProductAxiom) -> list[str]:
    row = value.canonical_input
    if row.predicate_iri is None:
        raise ModularProductError([issue("MISSING_PREDICATE", "selected axiom lacks predicate", row_id=value.row_id, axiom_id=value.axiom_id)])
    predicate = PREDICATE_QNAMES.get(row.predicate_iri)
    if predicate is None:
        raise ModularProductError([issue("UNSUPPORTED_PREDICATE", f"unsupported predicate {row.predicate_iri}", row_id=value.row_id, axiom_id=value.axiom_id)])
    if row.expression is not None:
        target, structural = _expression_turtle(row.expression, value.axiom_id, "target")
        return [f"{_iri(row.subject_iri)} {predicate} {target} .", *structural]
    if row.target_property_iri is not None:
        return [f"{_iri(row.subject_iri)} {predicate} {_iri(row.target_property_iri)} ."]
    if row.property_chain:
        list_nodes = [_bnode(value.axiom_id, f"chain_list_{index}") for index in range(len(row.property_chain))]
        lines = [f"{_iri(row.subject_iri)} {predicate} {list_nodes[0]} ."]
        for index, member in enumerate(row.property_chain):
            rest = list_nodes[index + 1] if index + 1 < len(list_nodes) else "rdf:nil"
            lines.append(f"{list_nodes[index]} rdf:first {_iri(member)} .")
            lines.append(f"{list_nodes[index]} rdf:rest {rest} .")
        return lines
    raise ModularProductError([issue("MISSING_TARGET", "selected axiom lacks a structured target", row_id=value.row_id, axiom_id=value.axiom_id)])


def _turtle_bytes(metadata: ModularProductMetadata, selected: tuple[SelectedProductAxiom, ...]) -> bytes:
    lines = [GENERATED_NOTICE, ""]
    lines.extend(f"@prefix {prefix}: <{namespace}> ." for prefix, namespace in PREFIXES)
    lines.extend(["", f"<{metadata.stable_ontology_iri}> rdf:type owl:Ontology .", ""])
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


def build_alignment_core(
    selected_axioms: Iterable[SelectedProductAxiom],
    publication_metadata: PublicationMetadata,
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
    serialized = _turtle_bytes(metadata, selected)
    graph = Graph().parse(data=serialized.decode("utf-8"), format="turtle")
    logical_count = len(graph) - 1
    return ModularProductResult(
        metadata=metadata,
        selected_rows=_selected_rows(selected),
        serialized_bytes=serialized,
        governed_axiom_count=len(selected),
        logical_triple_count=logical_count,
        ontology_header_triple_count=1,
        total_triple_count=len(graph),
        domain_axiom_count=domains,
        range_axiom_count=ranges,
        named_target_count=named,
        union_target_count=unions,
        sha256=hashlib.sha256(serialized).hexdigest(),
    )


def serialize_modular_product(result: ModularProductResult) -> bytes:
    return result.serialized_bytes


def _canonical_graph_expression(graph: Graph, node: URIRef | BNode) -> str:
    if isinstance(node, URIRef):
        return f"<{node}>"
    union = list(graph.objects(node, OWL.unionOf))
    intersection = list(graph.objects(node, OWL.intersectionOf))
    if len(union) == 1 or len(intersection) == 1:
        predicate = OWL.unionOf if union else OWL.intersectionOf
        list_node = union[0] if union else intersection[0]
        values = sorted({_canonical_graph_expression(graph, value) for value in Collection(graph, list_node)})
        operator = "ObjectUnionOf" if predicate == OWL.unionOf else "ObjectIntersectionOf"
        return f"{operator}({' '.join(values)})"
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
) -> tuple[ModularProductValidationIssue, ...]:
    selected = tuple(sorted(selected_axioms, key=lambda value: value.axiom_id))
    metadata = _product_metadata(publication_metadata, ALIGNMENT_CORE_KEY)
    issues: list[ModularProductValidationIssue] = []
    try:
        text = serialized_bytes.decode("utf-8")
        graph = Graph().parse(data=text, format="turtle")
    except Exception as exc:
        return (issue("TURTLE_PARSE", f"cannot strictly parse UTF-8 Turtle: {exc}"),)

    expected = build_alignment_core(selected, publication_metadata)
    if serialized_bytes != expected.serialized_bytes:
        issues.append(issue("NONDETERMINISTIC_SERIALIZATION", "bytes differ from canonical modular-product serialization"))
    ontology_iri = URIRef(metadata.stable_ontology_iri)
    declarations = set(graph.subjects(RDF.type, OWL.Ontology))
    if declarations != {ontology_iri}:
        issues.append(issue("ONTOLOGY_DECLARATION_MISMATCH", f"expected only {ontology_iri}, got {sorted(map(str, declarations))}"))
    imports = list(graph.triples((None, OWL.imports, None)))
    if imports:
        issues.append(issue("PROHIBITED_IMPORT", f"expected zero owl:imports triples, got {len(imports)}"))
    if len(graph) != ALIGNMENT_CORE_TOTAL_TRIPLE_COUNT:
        issues.append(issue("TOTAL_TRIPLE_COUNT_MISMATCH", f"expected 54, got {len(graph)}"))
    logical_graph = Graph()
    for triple in graph:
        if triple != (ontology_iri, RDF.type, OWL.Ontology):
            logical_graph.add(triple)
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


def build_fixed_source_closure(
    serialized_bytes: bytes,
    source_paths: Iterable[Path],
) -> Graph:
    """Build an offline validation closure and remove all import edges."""

    graph = Graph()
    for path in source_paths:
        graph.parse(path, format="turtle")
    graph.parse(data=serialized_bytes.decode("utf-8"), format="turtle")
    for triple in list(graph.triples((None, OWL.imports, None))):
        graph.remove(triple)
    return graph
