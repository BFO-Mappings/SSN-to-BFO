#!/usr/bin/env python3
"""Canonical identity and integrity helpers for governed COMS workbook rows."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Iterable


CANONICALIZATION_VERSION = "coms-row-expression-v1"
ROW_ID_PATTERN = re.compile(
    r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)

RDFS_SUBCLASS_OF = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
RDFS_SUBPROPERTY_OF = "http://www.w3.org/2000/01/rdf-schema#subPropertyOf"
RDFS_DOMAIN = "http://www.w3.org/2000/01/rdf-schema#domain"
RDFS_RANGE = "http://www.w3.org/2000/01/rdf-schema#range"
OWL_EQUIVALENT_CLASS = "http://www.w3.org/2002/07/owl#equivalentClass"
OWL_EQUIVALENT_PROPERTY = "http://www.w3.org/2002/07/owl#equivalentProperty"
OWL_PROPERTY_CHAIN_AXIOM = "http://www.w3.org/2002/07/owl#propertyChainAxiom"

MAPPING_TYPES = {
    "class_mapping",
    "object_property_mapping",
    "property_chain",
    "domain",
    "range",
    "explicit_blank",
}


@dataclass(frozen=True, order=True)
class RowLocation:
    worksheet: str
    row_number: int

    @property
    def text(self) -> str:
        return f"{self.worksheet}!{self.row_number}"


@dataclass(frozen=True)
class ExpressionNode:
    kind: str
    iri: str | None = None
    children: tuple["ExpressionNode", ...] = ()
    property_iri: str | None = None
    filler: "ExpressionNode | None" = None


@dataclass(frozen=True)
class RowIdentityReference:
    row_id: str
    location: RowLocation


@dataclass(frozen=True)
class CanonicalRowInput:
    row_id: str
    location: RowLocation
    subject_iri: str
    predicate_iri: str | None
    mapping_type: str
    reasoning: str = ""
    expression: ExpressionNode | None = None
    target_property_iri: str | None = None
    property_chain: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalRowExpression:
    canonicalization: str
    mapping_type: str
    predicate_iri: str | None
    subject_iri: str
    target: str | None

    def as_object(self) -> dict[str, str | None]:
        return {
            "canonicalization": self.canonicalization,
            "mapping_type": self.mapping_type,
            "predicate_iri": self.predicate_iri,
            "subject_iri": self.subject_iri,
            "target": self.target,
        }


@dataclass(frozen=True)
class AuthoritativeAxiomIdentity:
    canonical_axiom: str
    sha256: str


@dataclass(frozen=True)
class CanonicalRowAudit:
    row_id: str
    location: RowLocation
    reasoning: str
    expression: CanonicalRowExpression
    source_expression_sha256: str
    authoritative_axioms: tuple[AuthoritativeAxiomIdentity, ...]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    location: RowLocation
    row_id: str
    message: str

    @property
    def sort_key(self) -> tuple[str, int, str, str, str]:
        return (
            self.location.worksheet,
            self.location.row_number,
            self.code,
            self.row_id,
            self.message,
        )


class ComsRowIdentityError(ValueError):
    """One or more expected COMS identity or canonicalization failures."""

    def __init__(self, issues: Iterable[ValidationIssue]):
        self.issues = tuple(sorted(issues, key=lambda issue: issue.sort_key))
        super().__init__("\n".join(format_issue(issue) for issue in self.issues))


def format_issue(issue: ValidationIssue) -> str:
    row_id = f" [{issue.row_id}]" if issue.row_id else ""
    return f"ERROR [{issue.code}] {issue.location.text}{row_id}: {issue.message}"


def _issue(code: str, location: RowLocation, row_id: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, location=location, row_id=row_id, message=message)


def validate_row_id(value: object, location: RowLocation | None = None) -> str:
    """Return a canonical UUIDv4 URN or raise a structured validation error."""

    location = location or RowLocation("(unknown)", 0)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ComsRowIdentityError(
            [_issue("MISSING_ROW_ID", location, "", "coms:RowID is required for every governed row")]
        )
    if not isinstance(value, str) or not ROW_ID_PATTERN.fullmatch(value):
        raise ComsRowIdentityError(
            [
                _issue(
                    "MALFORMED_ROW_ID",
                    location,
                    value if isinstance(value, str) else repr(value),
                    "expected a lowercase canonical UUIDv4 URN",
                )
            ]
        )
    parsed = uuid.UUID(value.removeprefix("urn:uuid:"))
    if parsed.version != 4 or parsed.variant != uuid.RFC_4122 or value != f"urn:uuid:{parsed}":
        raise ComsRowIdentityError(
            [
                _issue(
                    "MALFORMED_ROW_ID",
                    location,
                    value,
                    "expected a lowercase canonical UUIDv4 URN",
                )
            ]
        )
    return value


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _iri(value: str) -> str:
    normalized = _nfc(value)
    if not normalized:
        raise ValueError("IRI must be nonempty")
    return f"<{normalized}>"


def _unsupported(row: CanonicalRowInput, message: str) -> ComsRowIdentityError:
    return ComsRowIdentityError(
        [_issue("UNSUPPORTED_CANONICAL_EXPRESSION", row.location, row.row_id, message)]
    )


def _flatten(node: ExpressionNode, kind: str) -> tuple[ExpressionNode, ...]:
    flattened: list[ExpressionNode] = []
    for child in node.children:
        if child.kind == kind:
            flattened.extend(_flatten(child, kind))
        else:
            flattened.append(child)
    return tuple(flattened)


def _canonical_expression_node(node: ExpressionNode, row: CanonicalRowInput) -> str:
    if node.kind == "named":
        if node.iri is None:
            raise _unsupported(row, "named expression lacks an IRI")
        return _iri(node.iri)
    if node.kind in {"intersection", "union"}:
        flattened = _flatten(node, node.kind)
        if not flattened:
            raise _unsupported(row, f"{node.kind} expression has no operands")
        operands = sorted({_canonical_expression_node(child, row) for child in flattened})
        if len(operands) == 1:
            return operands[0]
        operator = "ObjectIntersectionOf" if node.kind == "intersection" else "ObjectUnionOf"
        return f"{operator}({' '.join(operands)})"
    if node.kind == "some":
        if node.property_iri is None or node.filler is None:
            raise _unsupported(row, "existential restriction lacks a property or filler")
        filler = _canonical_expression_node(node.filler, row)
        return f"ObjectSomeValuesFrom({_iri(node.property_iri)} {filler})"
    raise _unsupported(row, f"unsupported expression node kind {node.kind!r}")


def canonicalize_processed_row(row: CanonicalRowInput) -> CanonicalRowExpression:
    """Canonicalize a neutral adapter built from an already-resolved generator row."""

    if row.mapping_type not in MAPPING_TYPES:
        raise _unsupported(row, f"unsupported mapping type {row.mapping_type!r}")

    target_sources = sum(
        (
            row.expression is not None,
            row.target_property_iri is not None,
            bool(row.property_chain),
        )
    )
    if row.mapping_type == "explicit_blank":
        if row.predicate_iri is not None or target_sources:
            raise _unsupported(row, "explicit blank row contains a predicate or target")
        target = None
    elif target_sources != 1:
        raise _unsupported(row, "active row must have exactly one canonical target representation")
    elif row.expression is not None:
        target = _canonical_expression_node(row.expression, row)
    elif row.target_property_iri is not None:
        target = _iri(row.target_property_iri)
    else:
        target = f"ObjectPropertyChain({' '.join(_iri(value) for value in row.property_chain)})"

    return CanonicalRowExpression(
        canonicalization=CANONICALIZATION_VERSION,
        mapping_type=_nfc(row.mapping_type),
        predicate_iri=None if row.predicate_iri is None else _nfc(row.predicate_iri),
        subject_iri=_nfc(row.subject_iri),
        target=target,
    )


def canonical_row_json(expression: CanonicalRowExpression) -> str:
    return json.dumps(
        expression.as_object(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def source_expression_sha256(expression: CanonicalRowExpression) -> str:
    payload = canonical_row_json(expression).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _axiom_identity(value: str) -> AuthoritativeAxiomIdentity:
    canonical = _nfc(value)
    return AuthoritativeAxiomIdentity(
        canonical_axiom=canonical,
        sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


def canonical_authoritative_axioms(row: CanonicalRowInput) -> tuple[AuthoritativeAxiomIdentity, ...]:
    expression = canonicalize_processed_row(row)
    subject = _iri(expression.subject_iri)
    target = expression.target
    predicate = expression.predicate_iri

    if expression.mapping_type == "explicit_blank":
        return ()
    assert target is not None
    if expression.mapping_type == "class_mapping" and predicate == RDFS_SUBCLASS_OF:
        canonical = f"SubClassOf({subject} {target})"
    elif expression.mapping_type == "class_mapping" and predicate == OWL_EQUIVALENT_CLASS:
        canonical = f"EquivalentClasses({subject} {target})"
    elif expression.mapping_type == "object_property_mapping" and predicate == RDFS_SUBPROPERTY_OF:
        canonical = f"SubObjectPropertyOf({subject} {target})"
    elif expression.mapping_type == "object_property_mapping" and predicate == OWL_EQUIVALENT_PROPERTY:
        canonical = f"EquivalentObjectProperties({subject} {target})"
    elif expression.mapping_type == "property_chain" and predicate == OWL_PROPERTY_CHAIN_AXIOM:
        canonical = f"SubObjectPropertyOf({target} {subject})"
    elif expression.mapping_type == "domain" and predicate == RDFS_DOMAIN:
        canonical = f"ObjectPropertyDomain({subject} {target})"
    elif expression.mapping_type == "range" and predicate == RDFS_RANGE:
        canonical = f"ObjectPropertyRange({subject} {target})"
    else:
        raise _unsupported(
            row,
            f"mapping type {expression.mapping_type!r} is incompatible with predicate {predicate!r}",
        )
    return (_axiom_identity(canonical),)


def build_row_audit(row: CanonicalRowInput) -> CanonicalRowAudit:
    row_id = validate_row_id(row.row_id, row.location)
    expression = canonicalize_processed_row(row)
    return CanonicalRowAudit(
        row_id=row_id,
        location=row.location,
        reasoning=row.reasoning,
        expression=expression,
        source_expression_sha256=source_expression_sha256(expression),
        authoritative_axioms=canonical_authoritative_axioms(row),
    )


def validate_unique_row_ids(rows: Iterable[RowIdentityReference]) -> tuple[ValidationIssue, ...]:
    seen: dict[str, RowIdentityReference] = {}
    issues: list[ValidationIssue] = []
    for row in sorted(rows, key=lambda item: (item.location, item.row_id)):
        previous = seen.get(row.row_id)
        if previous is None:
            seen[row.row_id] = row
            continue
        issues.append(
            _issue(
                "DUPLICATE_ROW_ID",
                row.location,
                row.row_id,
                f"duplicates RowID first used at {previous.location.text}",
            )
        )
    return tuple(sorted(issues, key=lambda issue: issue.sort_key))


def validate_unique_authoritative_axioms(
    rows: Iterable[CanonicalRowAudit],
) -> tuple[ValidationIssue, ...]:
    seen: dict[str, tuple[CanonicalRowAudit, AuthoritativeAxiomIdentity]] = {}
    issues: list[ValidationIssue] = []
    for row in sorted(rows, key=lambda item: (item.location, item.row_id)):
        for axiom in sorted(row.authoritative_axioms, key=lambda item: item.canonical_axiom):
            previous = seen.get(axiom.canonical_axiom)
            if previous is None:
                seen[axiom.canonical_axiom] = (row, axiom)
                continue
            previous_row, _ = previous
            issues.append(
                _issue(
                    "DUPLICATE_AUTHORITATIVE_AXIOM",
                    row.location,
                    row.row_id,
                    "canonical axiom duplicates "
                    f"{previous_row.row_id} at {previous_row.location.text}: {axiom.canonical_axiom}",
                )
            )
    return tuple(sorted(issues, key=lambda issue: issue.sort_key))
