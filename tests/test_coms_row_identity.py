#!/usr/bin/env python3
"""Focused tests for persistent COMS RowIDs and canonical axiom identity."""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import coms_row_identity as identity  # noqa: E402
import generate_mapping_from_coms as generator  # noqa: E402


ROW_ID_A = "urn:uuid:11111111-1111-4111-8111-111111111111"
ROW_ID_B = "urn:uuid:22222222-2222-4222-8222-222222222222"
ROW_ID_C = "urn:uuid:33333333-3333-4333-8333-333333333333"
SOSA_OBSERVATION = "http://www.w3.org/ns/sosa/Observation"
SOSA_ACTUATION = "http://www.w3.org/ns/sosa/Actuation"
SOSA_FEATURE = "http://www.w3.org/ns/sosa/FeatureOfInterest"
SOSA_HAS_FEATURE = "http://www.w3.org/ns/sosa/hasFeatureOfInterest"
RDFS_SUBCLASS = identity.RDFS_SUBCLASS_OF


def named(iri: str) -> identity.ExpressionNode:
    return identity.ExpressionNode(kind="named", iri=iri)


def class_row(
    *,
    row_id: str = ROW_ID_A,
    location: identity.RowLocation = identity.RowLocation("Sheet1", 2),
    reasoning: str = "",
    subject: str = SOSA_OBSERVATION,
    expression: identity.ExpressionNode = identity.ExpressionNode(
        kind="named", iri=SOSA_FEATURE
    ),
    predicate: str = RDFS_SUBCLASS,
) -> identity.CanonicalRowInput:
    return identity.CanonicalRowInput(
        row_id=row_id,
        location=location,
        subject_iri=subject,
        predicate_iri=predicate,
        mapping_type="class_mapping",
        reasoning=reasoning,
        expression=expression,
    )


def simple_row(
    mapping_type: str,
    predicate: str,
    *,
    subject: str = SOSA_HAS_FEATURE,
    target: str = SOSA_FEATURE,
    row_id: str = ROW_ID_A,
    location: identity.RowLocation = identity.RowLocation("Sheet2", 2),
) -> identity.CanonicalRowInput:
    if mapping_type in {"class_mapping", "domain", "range"}:
        return identity.CanonicalRowInput(
            row_id=row_id,
            location=location,
            subject_iri=subject,
            predicate_iri=predicate,
            mapping_type=mapping_type,
            expression=named(target),
        )
    return identity.CanonicalRowInput(
        row_id=row_id,
        location=location,
        subject_iri=subject,
        predicate_iri=predicate,
        mapping_type=mapping_type,
        target_property_iri=target,
    )


class RowIdGrammarTests(unittest.TestCase):
    def test_valid_canonical_uuid4_urn(self) -> None:
        self.assertEqual(identity.validate_row_id(ROW_ID_A), ROW_ID_A)

    def test_missing_and_whitespace_only_are_rejected(self) -> None:
        for value in (None, "", "   "):
            with self.subTest(value=value), self.assertRaises(identity.ComsRowIdentityError) as raised:
                identity.validate_row_id(value, identity.RowLocation("Synthetic", 4))
            self.assertEqual(raised.exception.issues[0].code, "MISSING_ROW_ID")
            self.assertEqual(raised.exception.issues[0].location.text, "Synthetic!4")

    def test_noncanonical_row_ids_are_rejected(self) -> None:
        invalid = {
            "uppercase": ROW_ID_A.upper(),
            "bare": ROW_ID_A.removeprefix("urn:uuid:"),
            "non_v4": "urn:uuid:11111111-1111-5111-8111-111111111111",
            "invalid_variant": "urn:uuid:11111111-1111-4111-7111-111111111111",
            "braces": "urn:uuid:{11111111-1111-4111-8111-111111111111}",
            "surrounding_whitespace": f" {ROW_ID_A} ",
            "punctuation": "urn:uuid:11111111_1111-4111-8111-111111111111",
        }
        for label, value in invalid.items():
            with self.subTest(label=label), self.assertRaises(identity.ComsRowIdentityError) as raised:
                identity.validate_row_id(value, identity.RowLocation("Synthetic", 5))
            self.assertEqual(raised.exception.issues[0].code, "MALFORMED_ROW_ID")
            self.assertIn("Synthetic!5", str(raised.exception))


class CanonicalIdentityBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resolver = generator.Resolver()

    def generator_class_input(
        self,
        target: str,
        *,
        row_id: str = ROW_ID_A,
        worksheet: str = "Synthetic",
        row_number: int = 2,
        reasoning: str = "",
    ) -> identity.CanonicalRowInput:
        workbook_row = generator.WorkbookRow(
            sheet=worksheet,
            row_number=row_number,
            subject_text="sosa:Observation",
            predicate_text="rdfs:subClassOf",
            target_text=target,
            reasoning_text=reasoning,
            stable_row_id=row_id,
        )
        subject, kind = self.resolver.resolve_source_subject(
            workbook_row.subject_text, workbook_row.diagnostic_id
        )
        processed = generator.ProcessedRow(
            row=workbook_row,
            subject=subject,
            subject_kind=kind,
            predicate=workbook_row.predicate_text,
            target=target,
            expr=generator.ManchesterParser(
                target, self.resolver, workbook_row.diagnostic_id
            ).parse(),
        )
        return generator.canonical_input_for_processed_row(processed)

    def test_row_movement_preserves_row_id_and_expression_hash(self) -> None:
        first = class_row()
        moved = replace(first, location=identity.RowLocation("MovedSheet", 99))
        self.assertEqual(first.row_id, moved.row_id)
        self.assertEqual(
            identity.source_expression_sha256(identity.canonicalize_processed_row(first)),
            identity.source_expression_sha256(identity.canonicalize_processed_row(moved)),
        )

    def test_reasoning_only_change_preserves_expression_hash(self) -> None:
        first = class_row(reasoning="first rationale")
        revised = replace(first, reasoning="revised rationale")
        self.assertEqual(
            identity.source_expression_sha256(identity.canonicalize_processed_row(first)),
            identity.source_expression_sha256(identity.canonicalize_processed_row(revised)),
        )

    def test_logical_content_change_changes_expression_hash(self) -> None:
        first = class_row(expression=named(SOSA_FEATURE))
        revised = class_row(expression=named(SOSA_ACTUATION))
        self.assertNotEqual(
            identity.source_expression_sha256(identity.canonicalize_processed_row(first)),
            identity.source_expression_sha256(identity.canonicalize_processed_row(revised)),
        )

    def test_prefix_aliases_resolving_to_same_iri_have_same_hash(self) -> None:
        label_style = self.generator_class_input("bfo:MaterialEntity")
        literal_curie = self.generator_class_input("bfo:BFO_0000040")
        self.assertEqual(
            identity.source_expression_sha256(identity.canonicalize_processed_row(label_style)),
            identity.source_expression_sha256(identity.canonicalize_processed_row(literal_curie)),
        )

    def test_whitespace_and_harmless_parentheses_have_same_hash(self) -> None:
        first = self.generator_class_input(
            "bfo:MaterialEntity and (sosa:hosts some ssn:System)"
        )
        second = self.generator_class_input(
            "( bfo:MaterialEntity ) and ( ( sosa:hosts some ( ssn:System ) ) )"
        )
        self.assertEqual(
            identity.source_expression_sha256(identity.canonicalize_processed_row(first)),
            identity.source_expression_sha256(identity.canonicalize_processed_row(second)),
        )


class CanonicalExpressionTests(unittest.TestCase):
    def test_named_expression(self) -> None:
        expression = identity.canonicalize_processed_row(class_row())
        self.assertEqual(expression.target, f"<{SOSA_FEATURE}>")

    def test_mapping_axiom_forms(self) -> None:
        cases = [
            (
                "subclass",
                simple_row("class_mapping", identity.RDFS_SUBCLASS_OF, subject=SOSA_OBSERVATION),
                "SubClassOf(",
            ),
            (
                "equivalent_class",
                simple_row("class_mapping", identity.OWL_EQUIVALENT_CLASS, subject=SOSA_OBSERVATION),
                "EquivalentClasses(",
            ),
            (
                "subproperty",
                simple_row("object_property_mapping", identity.RDFS_SUBPROPERTY_OF),
                "SubObjectPropertyOf(",
            ),
            (
                "domain",
                simple_row("domain", identity.RDFS_DOMAIN),
                "ObjectPropertyDomain(",
            ),
            (
                "range",
                simple_row("range", identity.RDFS_RANGE),
                "ObjectPropertyRange(",
            ),
        ]
        for label, row, expected in cases:
            with self.subTest(label=label):
                axioms = identity.canonical_authoritative_axioms(row)
                self.assertEqual(len(axioms), 1)
                self.assertTrue(axioms[0].canonical_axiom.startswith(expected))

    def test_intersection_flattens_deduplicates_and_sorts(self) -> None:
        nested = identity.ExpressionNode(
            kind="intersection",
            children=(
                named("http://example.org/B"),
                identity.ExpressionNode(
                    kind="intersection",
                    children=(named("http://example.org/A"), named("http://example.org/B")),
                ),
            ),
        )
        target = identity.canonicalize_processed_row(class_row(expression=nested)).target
        self.assertEqual(
            target,
            "ObjectIntersectionOf(<http://example.org/A> <http://example.org/B>)",
        )

    def test_union_flattens_deduplicates_and_sorts(self) -> None:
        nested = identity.ExpressionNode(
            kind="union",
            children=(
                named("http://example.org/C"),
                identity.ExpressionNode(
                    kind="union",
                    children=(named("http://example.org/A"), named("http://example.org/C")),
                ),
            ),
        )
        target = identity.canonicalize_processed_row(class_row(expression=nested)).target
        self.assertEqual(
            target,
            "ObjectUnionOf(<http://example.org/A> <http://example.org/C>)",
        )

    def test_existential_nesting_preserves_roles(self) -> None:
        expression = identity.ExpressionNode(
            kind="some",
            property_iri="http://example.org/p",
            filler=identity.ExpressionNode(
                kind="some",
                property_iri="http://example.org/q",
                filler=named("http://example.org/C"),
            ),
        )
        target = identity.canonicalize_processed_row(class_row(expression=expression)).target
        self.assertEqual(
            target,
            "ObjectSomeValuesFrom(<http://example.org/p> "
            "ObjectSomeValuesFrom(<http://example.org/q> <http://example.org/C>))",
        )

    def test_property_chain_order_is_preserved_and_changes_hash(self) -> None:
        first = identity.CanonicalRowInput(
            row_id=ROW_ID_A,
            location=identity.RowLocation("Sheet2", 16),
            subject_iri="http://example.org/super",
            predicate_iri=identity.OWL_PROPERTY_CHAIN_AXIOM,
            mapping_type="property_chain",
            property_chain=("http://example.org/p", "http://example.org/q"),
        )
        reversed_row = replace(first, property_chain=tuple(reversed(first.property_chain)))
        first_expression = identity.canonicalize_processed_row(first)
        reversed_expression = identity.canonicalize_processed_row(reversed_row)
        self.assertEqual(
            first_expression.target,
            "ObjectPropertyChain(<http://example.org/p> <http://example.org/q>)",
        )
        self.assertNotEqual(
            identity.source_expression_sha256(first_expression),
            identity.source_expression_sha256(reversed_expression),
        )
        self.assertEqual(
            identity.canonical_authoritative_axioms(first)[0].canonical_axiom,
            "SubObjectPropertyOf(ObjectPropertyChain(<http://example.org/p> "
            "<http://example.org/q>) <http://example.org/super>)",
        )

    def test_unsupported_expression_fails_structurally(self) -> None:
        row = class_row(expression=identity.ExpressionNode(kind="inverse"))
        with self.assertRaises(identity.ComsRowIdentityError) as raised:
            identity.canonicalize_processed_row(row)
        self.assertEqual(raised.exception.issues[0].code, "UNSUPPORTED_CANONICAL_EXPRESSION")

    def test_canonical_json_and_hash_are_deterministic(self) -> None:
        expression = identity.canonicalize_processed_row(class_row())
        expected = (
            '{"canonicalization":"coms-row-expression-v1","mapping_type":"class_mapping",'
            '"predicate_iri":"http://www.w3.org/2000/01/rdf-schema#subClassOf",'
            '"subject_iri":"http://www.w3.org/ns/sosa/Observation",'
            '"target":"<http://www.w3.org/ns/sosa/FeatureOfInterest>"}'
        )
        self.assertEqual(identity.canonical_row_json(expression), expected)
        self.assertEqual(
            identity.source_expression_sha256(expression),
            identity.source_expression_sha256(expression),
        )


class IntegrityTests(unittest.TestCase):
    def test_duplicate_row_ids_are_reported(self) -> None:
        issues = identity.validate_unique_row_ids(
            [
                identity.RowIdentityReference(ROW_ID_A, identity.RowLocation("B", 2)),
                identity.RowIdentityReference(ROW_ID_A, identity.RowLocation("A", 3)),
            ]
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "DUPLICATE_ROW_ID")
        self.assertIn("A!3", issues[0].message)

    def test_duplicate_canonical_axioms_report_both_rows(self) -> None:
        first = identity.build_row_audit(class_row(row_id=ROW_ID_A))
        second = identity.build_row_audit(
            class_row(
                row_id=ROW_ID_B,
                location=identity.RowLocation("Sheet9", 90),
                reasoning="different rationale",
            )
        )
        issues = identity.validate_unique_authoritative_axioms([second, first])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "DUPLICATE_AUTHORITATIVE_AXIOM")
        self.assertIn(ROW_ID_A, issues[0].message)
        self.assertEqual(issues[0].row_id, ROW_ID_B)
        self.assertEqual(issues[0].location.text, "Sheet9!90")

    def test_zero_one_and_multiple_axiom_tuples_are_supported(self) -> None:
        blank = identity.CanonicalRowInput(
            row_id=ROW_ID_A,
            location=identity.RowLocation("Sheet2", 2),
            subject_iri=SOSA_HAS_FEATURE,
            predicate_iri=None,
            mapping_type="explicit_blank",
        )
        zero = identity.build_row_audit(blank)
        one = identity.build_row_audit(class_row(row_id=ROW_ID_B))
        two = replace(
            one,
            row_id=ROW_ID_C,
            location=identity.RowLocation("Future", 1),
            authoritative_axioms=(
                one.authoritative_axioms[0],
                identity.AuthoritativeAxiomIdentity("FutureAxiom()", "0" * 64),
            ),
        )
        self.assertEqual(len(zero.authoritative_axioms), 0)
        self.assertEqual(len(one.authoritative_axioms), 1)
        self.assertEqual(len(two.authoritative_axioms), 2)

    def test_issue_ordering_is_deterministic(self) -> None:
        rows = [
            identity.RowIdentityReference(ROW_ID_A, identity.RowLocation("Z", 9)),
            identity.RowIdentityReference(ROW_ID_A, identity.RowLocation("Z", 2)),
            identity.RowIdentityReference(ROW_ID_B, identity.RowLocation("A", 8)),
            identity.RowIdentityReference(ROW_ID_B, identity.RowLocation("A", 3)),
        ]
        forward = identity.validate_unique_row_ids(rows)
        reverse = identity.validate_unique_row_ids(reversed(rows))
        self.assertEqual(forward, reverse)
        self.assertEqual([issue.location.text for issue in forward], ["A!8", "Z!9"])


if __name__ == "__main__":
    unittest.main()
