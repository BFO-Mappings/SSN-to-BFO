#!/usr/bin/env python3
"""Focused tests for generated COMS per-product disposition evidence."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import coms_row_identity as identity  # noqa: E402
import generate_mapping_from_coms as generator  # noqa: E402
import product_dispositions as dispositions  # noqa: E402
from publication_metadata import load_metadata  # noqa: E402


ROW_A = "urn:uuid:11111111-1111-4111-8111-111111111111"
ROW_B = "urn:uuid:22222222-2222-4222-8222-222222222222"
SOSA_OBSERVATION = "http://www.w3.org/ns/sosa/Observation"
SOSA_FEATURE = "http://www.w3.org/ns/sosa/FeatureOfInterest"
SOSA_HAS_FEATURE = "http://www.w3.org/ns/sosa/hasFeatureOfInterest"
BFO_ENTITY = "http://purl.obolibrary.org/obo/BFO_0000001"
CCO_ENTITY = "https://www.commoncoreontologies.org/ont00000958"
RDFS_SUBCLASS = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
RDFS_SUBPROPERTY = "http://www.w3.org/2000/01/rdf-schema#subPropertyOf"
RDFS_DOMAIN = "http://www.w3.org/2000/01/rdf-schema#domain"
OWL_CHAIN = "http://www.w3.org/2002/07/owl#propertyChainAxiom"


def hashes(seed: str = "0") -> dispositions.RequiredInputHashes:
    return dispositions.RequiredInputHashes(*[(seed * 64)[:64]] * 5)


def named(iri: str) -> identity.ExpressionNode:
    return identity.ExpressionNode(kind="named", iri=iri)


def row_input(
    target: identity.ExpressionNode = identity.ExpressionNode(kind="named", iri=SOSA_FEATURE),
    *,
    row_id: str = ROW_A,
    location: identity.RowLocation = identity.RowLocation("Synthetic", 2),
    reasoning: str = "",
    subject: str = SOSA_OBSERVATION,
    predicate: str = RDFS_SUBCLASS,
    predicate_lexical: str = "rdfs:subClassOf",
    mapping_type: str = "class_mapping",
    target_lexical: str = "sosa:FeatureOfInterest",
) -> dispositions.DispositionRowInput:
    canonical = identity.CanonicalRowInput(
        row_id=row_id,
        location=location,
        subject_iri=subject,
        predicate_iri=predicate,
        mapping_type=mapping_type,
        reasoning=reasoning,
        expression=target,
    )
    audit = identity.build_row_audit(canonical)
    return dispositions.DispositionRowInput(
        row_id=row_id,
        location=location,
        subject_lexical="sosa:Observation",
        predicate_lexical=predicate_lexical,
        authoritative_target_lexical=target_lexical,
        canonical_row=audit.expression,
        source_expression_sha256=audit.source_expression_sha256,
        mapping_type=mapping_type,
        reasoning=reasoning,
        authoritative_axioms=tuple(
            dispositions.axiom_input_from_canonical_row(axiom, canonical)
            for axiom in audit.authoritative_axioms
        ),
    )


def zero_row() -> dispositions.DispositionRowInput:
    canonical = identity.CanonicalRowInput(
        row_id=ROW_A,
        location=identity.RowLocation("Synthetic", 2),
        subject_iri=SOSA_OBSERVATION,
        predicate_iri=None,
        mapping_type="explicit_blank",
    )
    audit = identity.build_row_audit(canonical)
    return dispositions.DispositionRowInput(
        row_id=ROW_A,
        location=canonical.location,
        subject_lexical="sosa:Observation",
        predicate_lexical=None,
        authoritative_target_lexical=None,
        canonical_row=audit.expression,
        source_expression_sha256=audit.source_expression_sha256,
        mapping_type="explicit_blank",
        reasoning="",
        authoritative_axioms=(),
    )


def object_property_row_input() -> dispositions.DispositionRowInput:
    canonical = identity.CanonicalRowInput(
        row_id=ROW_A,
        location=identity.RowLocation("Synthetic", 2),
        subject_iri=SOSA_HAS_FEATURE,
        predicate_iri=RDFS_SUBPROPERTY,
        mapping_type="object_property_mapping",
        target_property_iri="http://purl.obolibrary.org/obo/BFO_0000056",
    )
    audit = identity.build_row_audit(canonical)
    return dispositions.DispositionRowInput(
        row_id=ROW_A,
        location=canonical.location,
        subject_lexical="sosa:hasFeatureOfInterest",
        predicate_lexical="rdfs:subPropertyOf",
        authoritative_target_lexical="bfo:participates_in",
        canonical_row=audit.expression,
        source_expression_sha256=audit.source_expression_sha256,
        mapping_type="object_property_mapping",
        reasoning="",
        authoritative_axioms=tuple(
            dispositions.axiom_input_from_canonical_row(axiom, canonical)
            for axiom in audit.authoritative_axioms
        ),
    )


def domain_row_input() -> dispositions.DispositionRowInput:
    return replace(
        row_input(
            subject=SOSA_HAS_FEATURE,
            predicate=RDFS_DOMAIN,
            predicate_lexical="rdfs:domain",
            mapping_type="domain",
        ),
        subject_lexical="sosa:hasFeatureOfInterest",
    )


def multi_axiom_row_input() -> dispositions.DispositionRowInput:
    source = row_input()
    expression = (
        "SubClassOf(<http://www.w3.org/ns/sosa/Observation> "
        "<http://www.w3.org/ns/sosa/Actuation>)"
    )
    second = dispositions.DispositionAxiomInput(
        identity.AuthoritativeAxiomIdentity(
            canonical_axiom=expression,
            sha256=dispositions.sha256_text(expression),
        ),
        SOSA_OBSERVATION,
        RDFS_SUBCLASS,
        ("http://www.w3.org/ns/sosa/Actuation",),
    )
    return replace(
        source,
        authoritative_axioms=(*source.authoritative_axioms, second),
    )


class ProductDispositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        cls.product_order = tuple(product.key for product in cls.metadata.products)

    def build(self, *rows: dispositions.DispositionRowInput) -> dispositions.DispositionDocument:
        return dispositions.build_disposition_document(rows, self.metadata, hashes())

    def assert_codes(self, issues, *codes: str) -> None:
        actual = {value.code for value in issues}
        for code in codes:
            self.assertIn(code, actual)

    def assert_noncanonical_file(
        self,
        document: dispositions.DispositionDocument,
        row_inputs: list[dispositions.DispositionRowInput],
        mutate,
    ) -> None:
        raw = dispositions.disposition_document_object(document)
        mutate(raw)
        with tempfile.TemporaryDirectory(prefix="disposition-order-") as temp:
            path = Path(temp) / "dispositions.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            loaded, issues = dispositions.validate_disposition_file(
                path,
                row_inputs,
                self.metadata,
                hashes(),
            )
            self.assert_codes(issues, "NONCANONICAL_SERIALIZATION")
            self.assertEqual(
                dispositions.validate_disposition_document(
                    loaded,
                    row_inputs,
                    self.metadata,
                    hashes(),
                ),
                (),
            )
            self.assertEqual(
                dispositions.serialize_disposition_document(loaded),
                dispositions.serialize_disposition_document(document),
            )

    def current_document(self) -> dispositions.DispositionDocument:
        rows, stats = generator.read_workbook(REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx")
        processed = generator.validate_and_process_rows(rows, generator.Resolver(), stats)
        inputs = [generator.disposition_input_for_processed_row(row) for row in processed]
        return dispositions.build_disposition_document(inputs, self.metadata, hashes())

    def test_current_workbook_totals_and_product_order(self) -> None:
        document = self.current_document()
        summary = document.summary
        self.assertEqual(document.product_order, self.product_order)
        self.assertEqual(summary.governed_row_count, 105)
        self.assertEqual(summary.unique_row_id_count, 105)
        self.assertEqual(summary.authoritative_axiom_count, 105)
        self.assertEqual(summary.unique_authoritative_axiom_count, 105)
        self.assertEqual(summary.zero_axiom_row_count, 0)
        self.assertEqual(
            (
                summary.target_neutral_axiom_count,
                summary.bfo_bearing_axiom_count,
                summary.cco_bearing_axiom_count,
                summary.mixed_bfo_cco_axiom_count,
            ),
            (29, 19, 25, 32),
        )
        self.assertEqual(
            (
                summary.class_mapping_row_count,
                summary.relation_mapping_row_count,
                summary.property_chain_row_count,
                summary.property_typing_row_count,
            ),
            (44, 25, 5, 31),
        )
        self.assertTrue(all(len(row.authoritative_axioms) == 1 for row in document.rows))

    def test_exact_disposition_matrix(self) -> None:
        expected = {
            "target_neutral": (
                ("integrated", "emitted_unchanged", None),
                ("alignment_core", "emitted_unchanged", None),
                ("strict_bfo_mapping", "provided_through_import", None),
                ("bfo_projection", "provided_transitively", None),
                ("cco_extension", "provided_transitively", None),
            ),
            "bfo_bearing": (
                ("integrated", "emitted_unchanged", None),
                ("alignment_core", "not_applicable", "TARGET_SPECIFIC"),
                ("strict_bfo_mapping", "emitted_unchanged", None),
                ("bfo_projection", "provided_through_import", None),
                ("cco_extension", "provided_through_import", None),
            ),
            "cco_bearing": (
                ("integrated", "emitted_unchanged", None),
                ("alignment_core", "not_applicable", "TARGET_SPECIFIC"),
                ("strict_bfo_mapping", "deferred", "NO_APPROVED_TRANSFORMATION_RULE"),
                ("bfo_projection", "deferred", "NO_APPROVED_TRANSFORMATION_RULE"),
                ("cco_extension", "emitted_unchanged", None),
            ),
            "mixed_bfo_cco": (
                ("integrated", "emitted_unchanged", None),
                ("alignment_core", "not_applicable", "TARGET_SPECIFIC"),
                ("strict_bfo_mapping", "deferred", "NO_APPROVED_TRANSFORMATION_RULE"),
                ("bfo_projection", "deferred", "NO_APPROVED_TRANSFORMATION_RULE"),
                ("cco_extension", "emitted_unchanged", None),
            ),
        }
        for category, required in expected.items():
            with self.subTest(category=category):
                values = dispositions.derive_product_dispositions(category, self.product_order)
                self.assertEqual(
                    tuple((key, value.status, value.reason_code) for key, value in values),
                    required,
                )

    def test_target_categories_and_nested_traversal(self) -> None:
        expressions = {
            "target_neutral": identity.ExpressionNode(
                kind="union", children=(named(SOSA_OBSERVATION), named(SOSA_FEATURE))
            ),
            "bfo_bearing": named(BFO_ENTITY),
            "cco_bearing": named(CCO_ENTITY),
            "mixed_bfo_cco": identity.ExpressionNode(
                kind="intersection",
                children=(
                    named(BFO_ENTITY),
                    identity.ExpressionNode(
                        kind="some",
                        property_iri="https://www.commoncoreontologies.org/ont00001808",
                        filler=named(SOSA_FEATURE),
                    ),
                ),
            ),
        }
        for expected, expression in expressions.items():
            with self.subTest(expected=expected):
                axiom = row_input(expression).authoritative_axioms[0]
                self.assertEqual(dispositions.classify_target_category(axiom), expected)
                references = dispositions.referenced_iris(axiom)
                self.assertEqual(references, tuple(sorted(set(references))))

    def test_property_chain_member_traversal_and_coverage(self) -> None:
        canonical = identity.CanonicalRowInput(
            row_id=ROW_A,
            location=identity.RowLocation("Synthetic", 2),
            subject_iri=SOSA_HAS_FEATURE,
            predicate_iri=OWL_CHAIN,
            mapping_type="property_chain",
            property_chain=(
                "http://www.w3.org/ns/sosa/madeBySensor",
                "https://www.commoncoreontologies.org/ont00001808",
            ),
        )
        audit = identity.build_row_audit(canonical)
        axiom = dispositions.axiom_input_from_canonical_row(audit.authoritative_axioms[0], canonical)
        self.assertEqual(dispositions.classify_target_category(axiom), "cco_bearing")
        self.assertIn("https://www.commoncoreontologies.org/ont00001808", dispositions.referenced_iris(axiom))
        self.assertEqual(dispositions.coverage_classification("property_chain"), "property_chain")

    def test_coverage_classification(self) -> None:
        expected = {
            "class_mapping": "class_mapping",
            "object_property_mapping": "relation_mapping",
            "property_chain": "property_chain",
            "domain": "property_typing",
            "range": "property_typing",
            "explicit_blank": "explicitly_unmapped",
        }
        for mapping_type, coverage in expected.items():
            with self.subTest(mapping_type=mapping_type):
                self.assertEqual(dispositions.coverage_classification(mapping_type), coverage)

    def test_domain_and_range_are_property_typing(self) -> None:
        for mapping_type, predicate, lexical in (
            ("domain", RDFS_DOMAIN, "rdfs:domain"),
            ("range", "http://www.w3.org/2000/01/rdf-schema#range", "rdfs:range"),
        ):
            with self.subTest(mapping_type=mapping_type):
                document = self.build(
                    row_input(
                        subject=SOSA_HAS_FEATURE,
                        predicate=predicate,
                        predicate_lexical=lexical,
                        mapping_type=mapping_type,
                    )
                )
                self.assertEqual(document.rows[0].coverage_classification, "property_typing")

    def test_unexpected_subject_predicate_and_target_fail(self) -> None:
        cases = (
            replace(row_input(), canonical_row=replace(row_input().canonical_row, subject_iri="https://example.org/Subject")),
            replace(
                row_input(),
                authoritative_axioms=(
                    replace(row_input().authoritative_axioms[0], predicate_iri="https://example.org/predicate"),
                ),
            ),
            row_input(named("https://example.org/ThirdParty")),
        )
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(dispositions.ProductDispositionError) as caught:
                    self.build(value)
                self.assert_codes(caught.exception.issues, "UNEXPECTED_TARGET_VOCABULARY")

    def test_zero_one_and_multiple_axiom_schema_support(self) -> None:
        zero = self.build(zero_row()).rows[0]
        self.assertEqual(zero.authoritative_axioms, ())
        self.assertIsNotNone(zero.row_product_dispositions)
        self.assertTrue(
            all(
                value == dispositions.ProductDisposition(
                    "deferred", "EXPLICITLY_UNMAPPED_SOURCE_ROW"
                )
                for _, value in zero.row_product_dispositions or ()
            )
        )
        one_input = row_input()
        one = self.build(one_input).rows[0]
        second_identity = identity.AuthoritativeAxiomIdentity(
            canonical_axiom="SubClassOf(<http://www.w3.org/ns/sosa/Observation> <http://www.w3.org/ns/sosa/Actuation>)",
            sha256=dispositions.sha256_text(
                "SubClassOf(<http://www.w3.org/ns/sosa/Observation> <http://www.w3.org/ns/sosa/Actuation>)"
            ),
        )
        second = dispositions.DispositionAxiomInput(
            second_identity,
            SOSA_OBSERVATION,
            RDFS_SUBCLASS,
            ("http://www.w3.org/ns/sosa/Actuation",),
        )
        multiple = self.build(
            replace(one_input, authoritative_axioms=(*one_input.authoritative_axioms, second))
        ).rows[0]
        self.assertEqual(len(one.authoritative_axioms), 1)
        self.assertEqual(len(multiple.authoritative_axioms), 2)

    def test_incomplete_zero_axiom_row_rejected(self) -> None:
        with self.assertRaises(dispositions.ProductDispositionError) as caught:
            self.build(replace(zero_row(), predicate_lexical="rdfs:subClassOf"))
        self.assert_codes(caught.exception.issues, "INCOMPLETE_ZERO_AXIOM_ROW")

    def test_reasoning_changes_bytes_not_expression_hash(self) -> None:
        first = self.build(row_input(reasoning="first"))
        second = self.build(row_input(reasoning="second"))
        self.assertEqual(
            first.rows[0].source_expression_sha256,
            second.rows[0].source_expression_sha256,
        )
        self.assertNotEqual(
            dispositions.serialize_disposition_document(first),
            dispositions.serialize_disposition_document(second),
        )

    def test_serialization_is_deterministic_and_input_order_independent(self) -> None:
        first = row_input(row_id=ROW_A, location=identity.RowLocation("Synthetic", 2))
        second = row_input(
            named("http://www.w3.org/ns/sosa/Actuation"),
            row_id=ROW_B,
            location=identity.RowLocation("Synthetic", 3),
            target_lexical="sosa:Actuation",
        )
        forward = self.build(first, second)
        reverse = self.build(second, first)
        self.assertEqual(
            dispositions.serialize_disposition_document(forward),
            dispositions.serialize_disposition_document(reverse),
        )
        self.assertEqual(tuple(row.row_id for row in forward.rows), (ROW_A, ROW_B))

    def test_file_validation_rejects_noncanonical_collection_order(self) -> None:
        first = row_input(row_id=ROW_A, location=identity.RowLocation("Synthetic", 2))
        second = row_input(
            named("http://www.w3.org/ns/sosa/Actuation"),
            row_id=ROW_B,
            location=identity.RowLocation("Synthetic", 3),
            target_lexical="sosa:Actuation",
        )

        def reverse_rows(raw) -> None:
            raw["rows"].reverse()

        def reverse_axioms(raw) -> None:
            raw["rows"][0]["authoritative_axioms"].reverse()

        def reverse_references(raw) -> None:
            raw["rows"][0]["authoritative_axioms"][0]["referenced_iris"].reverse()

        def reverse_axiom_dispositions(raw) -> None:
            current = raw["rows"][0]["authoritative_axioms"][0]["product_dispositions"]
            raw["rows"][0]["authoritative_axioms"][0]["product_dispositions"] = dict(
                reversed(tuple(current.items()))
            )

        def reverse_row_dispositions(raw) -> None:
            current = raw["rows"][0]["row_product_dispositions"]
            raw["rows"][0]["row_product_dispositions"] = dict(
                reversed(tuple(current.items()))
            )

        cases = (
            ("rows", [first, second], reverse_rows),
            ("axioms", [multi_axiom_row_input()], reverse_axioms),
            ("references", [first], reverse_references),
            ("axiom dispositions", [first], reverse_axiom_dispositions),
            ("row dispositions", [zero_row()], reverse_row_dispositions),
        )
        for label, inputs, mutate in cases:
            with self.subTest(label=label):
                self.assert_noncanonical_file(self.build(*inputs), inputs, mutate)

    def test_worksheet_names_are_nfc_normalized(self) -> None:
        decomposed = "Cafe\u0301"
        composed = "Caf\u00e9"
        source = replace(
            row_input(),
            location=identity.RowLocation(decomposed, 7),
        )
        document = self.build(source)
        self.assertEqual(source.location.worksheet, decomposed)
        self.assertEqual(document.rows[0].location, identity.RowLocation(composed, 7))
        self.assertEqual(
            self.build(row_input()).rows[0].location.worksheet,
            "Synthetic",
        )

        def decompose_worksheet(raw) -> None:
            raw["rows"][0]["location"]["worksheet"] = decomposed

        self.assert_noncanonical_file(document, [source], decompose_worksheet)

    def test_mapping_type_must_match_canonical_expression(self) -> None:
        cases = (
            (replace(row_input(), mapping_type="domain"), "domain", "class_mapping"),
            (
                replace(object_property_row_input(), mapping_type="range"),
                "range",
                "object_property_mapping",
            ),
        )
        for source, supplied, canonical in cases:
            with self.subTest(supplied=supplied, canonical=canonical):
                with (
                    mock.patch.object(
                        dispositions,
                        "coverage_classification",
                        side_effect=AssertionError(
                            "coverage classification must not run after a mapping-type mismatch"
                        ),
                    ) as coverage,
                    self.assertRaises(dispositions.ProductDispositionError) as caught,
                ):
                    self.build(source)
                coverage.assert_not_called()
                self.assertEqual(len(caught.exception.issues), 1)
                mismatch = next(
                    value
                    for value in caught.exception.issues
                    if value.code == "ROW_EXPRESSION_MISMATCH"
                    and value.field == "mapping_type"
                )
                self.assertEqual(mismatch.row_id, ROW_A)
                self.assertIn("Synthetic!2", mismatch.message)
                self.assertIn(repr(supplied), mismatch.message)
                self.assertIn(repr(canonical), mismatch.message)

    def test_matching_mapping_types_derive_coverage(self) -> None:
        cases = (
            (row_input(), "class_mapping"),
            (domain_row_input(), "property_typing"),
        )
        for source, expected in cases:
            with (
                self.subTest(mapping_type=source.mapping_type),
                mock.patch.object(
                    dispositions,
                    "coverage_classification",
                    wraps=dispositions.coverage_classification,
                ) as coverage,
            ):
                document = self.build(source)
                coverage.assert_called_once_with(source.mapping_type)
                self.assertEqual(document.rows[0].coverage_classification, expected)

    def test_round_trip_and_noncanonical_serialization(self) -> None:
        document = self.build(row_input())
        with tempfile.TemporaryDirectory(prefix="disposition-json-") as temp:
            path = Path(temp) / "dispositions.json"
            canonical = dispositions.serialize_disposition_document(document)
            path.write_bytes(canonical)
            loaded, issues = dispositions.validate_disposition_file(
                path, [row_input()], self.metadata, hashes()
            )
            self.assertEqual(issues, ())
            self.assertEqual(dispositions.serialize_disposition_document(loaded), canonical)
            path.write_text(json.dumps(dispositions.disposition_document_object(document)), encoding="utf-8")
            _, issues = dispositions.validate_disposition_file(
                path, [row_input()], self.metadata, hashes()
            )
            self.assert_codes(issues, "NONCANONICAL_SERIALIZATION")

    def test_identity_and_row_reconciliation_failures(self) -> None:
        source = row_input()
        document = self.build(source)
        actual = document.rows[0]
        mutations = (
            (replace(document, rows=(replace(actual, row_id=ROW_B),)), "MISSING_DISPOSITION_ROW"),
            (replace(document, rows=(replace(actual, location=identity.RowLocation("Other", 99)),)), "ROW_LOCATION_MISMATCH"),
            (replace(document, rows=(replace(actual, canonical_row_expression=replace(actual.canonical_row_expression, target="<changed>")),)), "ROW_EXPRESSION_MISMATCH"),
            (replace(document, rows=(replace(actual, source_expression_sha256="f" * 64),)), "EXPRESSION_HASH_MISMATCH"),
        )
        for changed, code in mutations:
            with self.subTest(code=code):
                self.assert_codes(
                    dispositions.validate_disposition_document(changed, [source], self.metadata, hashes()),
                    code,
                )

    def test_axiom_reconciliation_category_and_references(self) -> None:
        source = row_input()
        document = self.build(source)
        row = document.rows[0]
        axiom = row.authoritative_axioms[0]
        mutations = (
            (replace(axiom, axiom_id="sha256:" + "f" * 64), "MISSING_AUTHORITATIVE_AXIOM"),
            (replace(axiom, canonical_expression=axiom.canonical_expression + " "), "AXIOM_ID_MISMATCH"),
            (replace(axiom, referenced_iris=(*axiom.referenced_iris, "https://example.org/x")), "REFERENCED_IRI_MISMATCH"),
            (replace(axiom, target_category="cco_bearing"), "TARGET_CATEGORY_MISMATCH"),
            (replace(axiom, target_category="unknown"), "UNKNOWN_TARGET_CATEGORY"),
        )
        for changed_axiom, code in mutations:
            changed = replace(document, rows=(replace(row, authoritative_axioms=(changed_axiom,)),))
            with self.subTest(code=code):
                self.assert_codes(
                    dispositions.validate_disposition_document(changed, [source], self.metadata, hashes()),
                    code,
                )

    def test_product_status_and_reason_validation(self) -> None:
        source = row_input(named(CCO_ENTITY))
        document = self.build(source)
        row = document.rows[0]
        axiom = row.authoritative_axioms[0]
        values = list(axiom.product_dispositions)
        mutations = (
            (tuple(values[:-1]), "MISSING_PRODUCT_DISPOSITION"),
            ((*values, ("extra", dispositions.ProductDisposition("deferred", "NO_APPROVED_TRANSFORMATION_RULE"))), "UNKNOWN_PRODUCT"),
            (tuple((key, dispositions.ProductDisposition("unknown")) if key == "integrated" else (key, value) for key, value in values), "UNKNOWN_DISPOSITION_STATUS"),
            (tuple((key, dispositions.ProductDisposition("deferred")) if key == "strict_bfo_mapping" else (key, value) for key, value in values), "MISSING_REASON_CODE"),
            (tuple((key, dispositions.ProductDisposition("emitted_unchanged", "TARGET_SPECIFIC")) if key == "integrated" else (key, value) for key, value in values), "PROHIBITED_REASON_CODE"),
            (tuple((key, dispositions.ProductDisposition("deferred", "TARGET_SPECIFIC")) if key == "strict_bfo_mapping" else (key, value) for key, value in values), "INVALID_REASON_CODE"),
        )
        for changed_values, code in mutations:
            changed_axiom = replace(axiom, product_dispositions=tuple(changed_values))
            changed = replace(document, rows=(replace(row, authoritative_axioms=(changed_axiom,)),))
            with self.subTest(code=code):
                self.assert_codes(
                    dispositions.validate_disposition_document(changed, [source], self.metadata, hashes()),
                    code,
                )

    def test_summary_product_order_and_stale_hashes(self) -> None:
        source = row_input()
        document = self.build(source)
        changed_summary = replace(document.summary, governed_row_count=2)
        self.assert_codes(
            dispositions.validate_disposition_document(
                replace(document, summary=changed_summary), [source], self.metadata, hashes()
            ),
            "SUMMARY_MISMATCH",
        )
        self.assert_codes(
            dispositions.validate_disposition_document(
                replace(document, product_order=tuple(reversed(document.product_order))),
                [source],
                self.metadata,
                hashes(),
            ),
            "PRODUCT_ORDER_MISMATCH",
        )
        hash_codes = (
            ("workbook_sha256", "STALE_WORKBOOK"),
            ("generator_sha256", "STALE_GENERATOR"),
            ("row_identity_module_sha256", "STALE_ROW_IDENTITY_MODULE"),
            ("disposition_module_sha256", "STALE_DISPOSITION_MODULE"),
            ("publication_metadata_sha256", "STALE_PUBLICATION_METADATA"),
        )
        for field, code in hash_codes:
            changed_hashes = replace(document.input_hashes, **{field: "f" * 64})
            with self.subTest(field=field):
                self.assert_codes(
                    dispositions.validate_disposition_document(
                        replace(document, input_hashes=changed_hashes),
                        [source],
                        self.metadata,
                        hashes(),
                    ),
                    code,
                )

    def test_future_modular_ttl_files_are_not_required(self) -> None:
        for product in self.metadata.products:
            if product.key != "integrated":
                self.assertFalse((REPO_ROOT / product.path).is_file())
        self.assertEqual(self.build(row_input()).summary.governed_row_count, 1)


if __name__ == "__main__":
    unittest.main()
