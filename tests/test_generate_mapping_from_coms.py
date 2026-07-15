#!/usr/bin/env python3
"""Focused tests for COMS generation, coverage, and authority migration."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import openpyxl
from rdflib import BNode, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_coms_mapping as checker  # noqa: E402
import coms_row_identity as identity  # noqa: E402
import generate_mapping_from_coms as coms  # noqa: E402
import product_dispositions as dispositions  # noqa: E402
from publication_metadata import load_metadata  # noqa: E402


SUBJECT = "sosa:hasFeatureOfInterest"
SUBJECT_IRI = URIRef("http://www.w3.org/ns/sosa/hasFeatureOfInterest")
OBSERVATION = URIRef("http://www.w3.org/ns/sosa/Observation")
ACTUATION = URIRef("http://www.w3.org/ns/sosa/Actuation")
SAMPLING = URIRef("http://www.w3.org/ns/sosa/Sampling")
FEATURE_OF_INTEREST = URIRef("http://www.w3.org/ns/sosa/FeatureOfInterest")
MAPPED_PROPERTY = URIRef("http://www.w3.org/ns/sosa/actsOnProperty")
DOMAIN_ONLY_PROPERTY = SUBJECT_IRI
RANGE_ONLY_PROPERTY = URIRef("http://www.w3.org/ns/sosa/hasResult")
UNCOVERED_PROPERTY = URIRef("http://www.w3.org/ns/sosa/hosts")


class ComsDomainRangeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="coms-domain-range-test-")
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    @staticmethod
    def row_id_for(index: int) -> str:
        return f"urn:uuid:00000000-0000-4000-8000-{index:012x}"

    def synthetic_workbook(
        self,
        rows: list[tuple[str, ...]],
        *,
        row_ids: list[str] | None = None,
        headers: tuple[str, ...] = coms.REQUIRED_COLUMNS,
    ) -> Path:
        path = self.root / "synthetic-coms.xlsx"
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Synthetic"
        worksheet.append(list(headers))
        for index, row in enumerate(rows, start=1):
            subject, predicate, target = row[:3]
            reasoning = row[3] if len(row) > 3 else "synthetic test row"
            row_id = row_ids[index - 1] if row_ids is not None else self.row_id_for(index)
            values = {
                "sssom:subject_id": subject,
                "sssom:predicate_id": predicate,
                "coms:Target": target,
                "coms:Reasoning": reasoning,
                "coms:RowID": row_id,
            }
            worksheet.append([values[header] for header in headers])
        workbook.save(path)
        workbook.close()
        return path

    def process(self, rows: list[tuple[str, ...]], *, row_ids: list[str] | None = None):
        workbook_path = self.synthetic_workbook(rows, row_ids=row_ids)
        workbook_rows, stats = coms.read_workbook(workbook_path)
        processed = coms.validate_and_process_rows(workbook_rows, coms.Resolver(), stats)
        return processed, stats

    def generate(self, rows: list[tuple[str, ...]], *, row_ids: list[str] | None = None):
        processed, stats = self.process(rows, row_ids=row_ids)
        output = self.root / "candidate.ttl"
        graph = coms.generate_ontology(processed, output)
        return graph, processed, stats

    def assert_generation_error(
        self,
        rows: list[tuple[str, ...]],
        *expected_fragments: str,
        row_ids: list[str] | None = None,
    ) -> None:
        workbook_path = self.synthetic_workbook(rows, row_ids=row_ids)
        workbook_rows, stats = coms.read_workbook(workbook_path)
        with self.assertRaises(coms.GenerationError) as raised:
            coms.validate_and_process_rows(workbook_rows, coms.Resolver(), stats)
        message = str(raised.exception)
        for fragment in expected_fragments:
            self.assertIn(fragment, message)

    def run_generator(self, workbook_path: Path) -> tuple[int, Path, Path, Path]:
        output_path = self.root / "candidate-output.ttl"
        report_path = self.root / "generation-report.md"
        disposition_path = self.root / "product-dispositions.json"
        return_code = coms.main(
            [
                "--input",
                str(workbook_path),
                "--output",
                str(output_path),
                "--report",
                str(report_path),
                "--disposition-report",
                str(disposition_path),
                "--alignment-core-output",
                str(self.root / "alignment-core.ttl"),
                "--coverage-report",
                str(self.root / "coverage.md"),
                "--diff-report",
                str(self.root / "comparison.md"),
                "--tmp-dir",
                str(self.root / "reasoner"),
            ]
        )
        return return_code, output_path, report_path, disposition_path

    def assert_generator_main_failure(
        self,
        workbook_path: Path,
        *expected_fragments: str,
    ) -> None:
        before = workbook_path.read_bytes()
        return_code, output_path, report_path, disposition_path = self.run_generator(workbook_path)
        self.assertEqual(return_code, 1)
        self.assertFalse(output_path.exists())
        self.assertFalse(disposition_path.exists())
        self.assertFalse((self.root / "alignment-core.ttl").exists())
        self.assertTrue(report_path.is_file())
        report = report_path.read_text(encoding="utf-8")
        self.assertIn("| overall status | FAIL |", report)
        for fragment in expected_fragments:
            self.assertIn(fragment, report)
        self.assertEqual(workbook_path.read_bytes(), before)

    def test_disposition_failure_prevents_ontology_generation(self) -> None:
        workbook_path = self.synthetic_workbook(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")]
        )
        failure = dispositions.ProductDispositionError(
            [
                dispositions.ValidationIssue(
                    code="TARGET_CATEGORY_MISMATCH",
                    row_id=self.row_id_for(1),
                    message="synthetic disposition failure",
                )
            ]
        )
        before = workbook_path.read_bytes()
        with mock.patch.object(coms, "build_disposition_document", side_effect=failure):
            return_code, output_path, report_path, disposition_path = self.run_generator(
                workbook_path
            )
        self.assertEqual(return_code, 1)
        self.assertFalse(output_path.exists())
        self.assertFalse(disposition_path.exists())
        self.assertFalse((self.root / "alignment-core.ttl").exists())
        report = report_path.read_text(encoding="utf-8")
        self.assertIn("TARGET_CATEGORY_MISMATCH", report)
        self.assertIn("| overall status | FAIL |", report)
        self.assertEqual(workbook_path.read_bytes(), before)

    def test_disposition_generation_succeeds_without_mutating_workbook(self) -> None:
        workbook_path = self.synthetic_workbook(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")]
        )
        before = workbook_path.read_bytes()
        workbook_rows, stats = coms.read_workbook(workbook_path)
        processed = coms.validate_and_process_rows(workbook_rows, coms.Resolver(), stats)
        path = self.root / "dispositions.json"
        document, row_inputs = coms.build_and_write_disposition_report(
            processed,
            path,
            dispositions.RequiredInputHashes(*["0" * 64] * 5),
        )
        self.assertEqual(document.summary.governed_row_count, 1)
        self.assertEqual(document.summary.authoritative_axiom_count, 1)
        self.assertEqual(document.summary.target_neutral_axiom_count, 1)
        self.assertEqual(len(row_inputs), 1)
        self.assertEqual(workbook_path.read_bytes(), before)

    def governed_row(
        self,
        index: int,
        *,
        sheet: str = "Synthetic",
        row_number: int | None = None,
    ) -> coms.WorkbookRow:
        return coms.WorkbookRow(
            sheet=sheet,
            row_number=row_number if row_number is not None else index + 1,
            subject_text=SUBJECT,
            predicate_text="rdfs:domain",
            target_text="sosa:Observation",
            reasoning_text="synthetic test row",
            stable_row_id=self.row_id_for(index),
        )

    @staticmethod
    def processed_row(row: coms.WorkbookRow) -> coms.ProcessedRow:
        return coms.ProcessedRow(
            row=row,
            subject=URIRef(f"urn:test:property:{row.stable_row_id[-12:]}"),
            subject_kind="object_property",
            predicate="rdfs:domain",
            target="sosa:Observation",
            expr=coms.Expr(kind="named", iri=OBSERVATION),
        )

    def assert_completeness_error(
        self,
        governed_rows: list[coms.WorkbookRow],
        processed_rows: list[coms.ProcessedRow],
        audits: tuple[identity.CanonicalRowAudit, ...],
        *expected_fragments: str,
    ) -> str:
        with self.assertRaises(coms.GenerationError) as raised:
            coms.validate_identity_audit_completeness(
                governed_rows,
                processed_rows,
                audits,
            )
        message = str(raised.exception)
        for fragment in expected_fragments:
            self.assertIn(fragment, message)
        return message

    def test_row_id_only_governed_row_is_fatal(self) -> None:
        row_id = self.row_id_for(1)
        workbook_path = self.synthetic_workbook(
            [("", "", "", "")],
            row_ids=[row_id],
        )
        self.assert_generator_main_failure(
            workbook_path,
            "MISSING_SOURCE_SUBJECT",
            "Synthetic!2",
            row_id,
            "sssom:subject_id",
        )

    def test_row_id_and_reasoning_only_governed_row_is_fatal(self) -> None:
        row_id = self.row_id_for(1)
        workbook_path = self.synthetic_workbook(
            [("", "", "", "retained rationale")],
            row_ids=[row_id],
        )
        self.assert_generator_main_failure(
            workbook_path,
            "MISSING_SOURCE_SUBJECT",
            "Synthetic!2",
            row_id,
            "sssom:subject_id",
        )

    def test_predicate_and_target_without_subject_are_fatal(self) -> None:
        row_id = self.row_id_for(1)
        workbook_path = self.synthetic_workbook(
            [("", "rdfs:subClassOf", "bfo:MaterialEntity", "")],
            row_ids=[row_id],
        )
        self.assert_generator_main_failure(
            workbook_path,
            "MISSING_SOURCE_SUBJECT",
            "Synthetic!2",
            row_id,
            "sssom:subject_id",
        )

    def test_governed_worksheet_without_row_id_header_is_fatal(self) -> None:
        workbook_path = self.synthetic_workbook(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")],
            headers=coms.BASE_REQUIRED_COLUMNS,
        )
        self.assert_generator_main_failure(
            workbook_path,
            "Synthetic!1",
            "coms:RowID",
            "missing required header",
        )

    def test_identity_audit_completeness_mismatch_is_fatal(self) -> None:
        workbook_path = self.synthetic_workbook(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")]
        )
        with mock.patch.object(coms, "attach_canonical_identities", return_value=()):
            self.assert_generator_main_failure(
                workbook_path,
                "IDENTITY_AUDIT_INCOMPLETE",
                "processed row count 1 does not match identity-audit row count 0",
                self.row_id_for(1),
            )

    def test_equal_count_governed_processed_row_id_substitution_is_fatal(self) -> None:
        governed = [self.governed_row(1), self.governed_row(2)]
        processed = [
            self.processed_row(governed[0]),
            self.processed_row(self.governed_row(3)),
        ]
        audits = coms.attach_canonical_identities(processed)
        self.assert_completeness_error(
            governed,
            processed,
            audits,
            "GOVERNED_PROCESSED_ROWID_MISMATCH",
            f"{self.row_id_for(2)} (Synthetic!3)",
            f"{self.row_id_for(3)} (Synthetic!4)",
        )

    def test_equal_count_processed_audit_row_id_substitution_is_fatal(self) -> None:
        governed = [self.governed_row(1), self.governed_row(2)]
        processed = [self.processed_row(row) for row in governed]
        coms.attach_canonical_identities(processed)
        unexpected = self.processed_row(self.governed_row(3))
        unexpected_audit = coms.attach_canonical_identities([unexpected])[0]
        audits = (processed[0].identity_audit, unexpected_audit)
        self.assert_completeness_error(
            governed,
            processed,
            audits,
            "PROCESSED_AUDIT_ROWID_MISMATCH",
            f"{self.row_id_for(2)} (Synthetic!3)",
            f"{self.row_id_for(3)} (Synthetic!4)",
        )

    def test_governed_processed_location_mismatch_is_fatal(self) -> None:
        governed = [self.governed_row(1, sheet="Sheet1", row_number=2)]
        processed = [
            self.processed_row(self.governed_row(1, sheet="Sheet2", row_number=9))
        ]
        audits = coms.attach_canonical_identities(processed)
        self.assert_completeness_error(
            governed,
            processed,
            audits,
            "IDENTITY_AUDIT_LOCATION_MISMATCH",
            "governed-to-processed location mismatch",
            self.row_id_for(1),
            "governed Sheet1!2, processed Sheet2!9",
        )

    def test_processed_audit_location_mismatch_is_fatal(self) -> None:
        governed = [self.governed_row(1, sheet="Sheet1", row_number=2)]
        processed = [self.processed_row(governed[0])]
        coms.attach_canonical_identities(processed)
        alternate = self.processed_row(
            self.governed_row(1, sheet="Sheet2", row_number=9)
        )
        alternate_audit = coms.attach_canonical_identities([alternate])
        self.assert_completeness_error(
            governed,
            processed,
            alternate_audit,
            "IDENTITY_AUDIT_LOCATION_MISMATCH",
            "processed-to-audit location mismatch",
            self.row_id_for(1),
            "processed Sheet1!2, audit Sheet2!9",
        )

    def test_row_id_mismatch_diagnostics_are_sorted(self) -> None:
        governed = [self.governed_row(3), self.governed_row(1)]
        processed = [
            self.processed_row(self.governed_row(4)),
            self.processed_row(self.governed_row(2)),
        ]
        audits = coms.attach_canonical_identities(processed)
        message = self.assert_completeness_error(
            governed,
            processed,
            audits,
            "GOVERNED_PROCESSED_ROWID_MISMATCH",
        )
        self.assertLess(message.index(self.row_id_for(1)), message.index(self.row_id_for(3)))
        self.assertLess(message.index(self.row_id_for(2)), message.index(self.row_id_for(4)))

    def test_successful_processing_has_complete_identity_counts(self) -> None:
        processed, stats = self.process(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")]
        )
        self.assertEqual(stats.governed_row_id_count, 1)
        self.assertEqual(stats.processed_row_count, 1)
        self.assertEqual(stats.identity_audit_row_count, 1)
        self.assertTrue(stats.identity_count_reconciliation_passed)
        self.assertTrue(stats.identity_row_id_set_reconciliation_passed)
        self.assertTrue(stats.identity_location_reconciliation_passed)
        self.assertEqual(len(processed), 1)
        audit = processed[0].identity_audit
        self.assertIsNotNone(audit)
        self.assertEqual(processed[0].row.stable_row_id, audit.row_id)
        self.assertEqual(processed[0].row.location, audit.location)
        self.assertEqual(len(audit.authoritative_axioms), 1)

    def test_missing_row_id_is_rejected(self) -> None:
        self.assert_generation_error(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")],
            "MISSING_ROW_ID",
            "Synthetic!2",
            row_ids=[""],
        )

    def test_malformed_row_id_is_rejected_with_location_and_value(self) -> None:
        malformed = "urn:uuid:NOT-CANONICAL"
        self.assert_generation_error(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")],
            "MALFORMED_ROW_ID",
            "Synthetic!2",
            malformed,
            row_ids=[malformed],
        )

    def test_duplicate_row_id_is_rejected(self) -> None:
        duplicate = self.row_id_for(1)
        self.assert_generation_error(
            [
                (SUBJECT, "rdfs:domain", "sosa:Observation"),
                (SUBJECT, "rdfs:range", "sosa:FeatureOfInterest"),
            ],
            "DUPLICATE_ROW_ID",
            "Synthetic!2",
            "Synthetic!3",
            duplicate,
            row_ids=[duplicate, duplicate],
        )

    def test_duplicate_canonical_authoritative_axiom_is_rejected(self) -> None:
        self.assert_generation_error(
            [
                (
                    "sosa:Observation",
                    "rdfs:subClassOf",
                    "bfo:MaterialEntity and sosa:FeatureOfInterest",
                    "first rationale",
                ),
                (
                    "sosa:Observation",
                    "rdfs:subClassOf",
                    "sosa:FeatureOfInterest and bfo:MaterialEntity",
                    "second rationale",
                ),
            ],
            "DUPLICATE_AUTHORITATIVE_AXIOM",
            "Synthetic!2",
            "Synthetic!3",
            self.row_id_for(1),
            self.row_id_for(2),
        )

    def test_incompatible_duplicate_mapping_still_fails(self) -> None:
        self.assert_generation_error(
            [
                ("sosa:Observation", "rdfs:subClassOf", "bfo:MaterialEntity"),
                ("sosa:Observation", "rdfs:subClassOf", "sosa:FeatureOfInterest"),
            ],
            "incompatible target",
            "Synthetic!2",
            "Synthetic!3",
            self.row_id_for(1),
            self.row_id_for(2),
        )

    def test_row_id_does_not_change_generated_ontology(self) -> None:
        rows = [(SUBJECT, "rdfs:domain", "sosa:Observation")]
        first, _ = self.process(rows, row_ids=[self.row_id_for(1)])
        first_output = self.root / "first.ttl"
        coms.generate_ontology(first, first_output)
        second, _ = self.process(rows, row_ids=[self.row_id_for(2)])
        second_output = self.root / "second.ttl"
        coms.generate_ontology(second, second_output)
        self.assertEqual(first_output.read_bytes(), second_output.read_bytes())

    def test_generation_does_not_mutate_workbook(self) -> None:
        workbook_path = self.synthetic_workbook(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")]
        )
        before = workbook_path.read_bytes()
        workbook_rows, stats = coms.read_workbook(workbook_path)
        processed = coms.validate_and_process_rows(workbook_rows, coms.Resolver(), stats)
        coms.generate_ontology(processed, self.root / "nonmutating.ttl")
        self.assertEqual(before, workbook_path.read_bytes())

    def test_named_class_domain(self) -> None:
        graph, processed, stats = self.generate([(SUBJECT, "rdfs:domain", "sosa:Observation")])

        self.assertIn((SUBJECT_IRI, RDFS.domain, OBSERVATION), graph)
        self.assertEqual(stats.domain_rows, 1)
        self.assertEqual(stats.range_rows, 0)
        self.assertEqual(stats.object_property_mapping_rows, 0)
        self.assertEqual(stats.mapped_rows, 0)
        normalized = coms.normalized_axiom_rows(processed, graph)
        self.assertEqual(normalized[0].subject_kind, "object_property")
        self.assertEqual(normalized[0].predicate, "rdfs:domain")
        self.assertIn("rdfs:domain", normalized[0].rdf_owl_form)

    def test_generated_file_notice_is_nonsemantic_turtle_comment(self) -> None:
        graph, _, _ = self.generate([(SUBJECT, "rdfs:domain", "sosa:Observation")])
        output = self.root / "candidate.ttl"

        self.assertTrue(output.read_text(encoding="utf-8").startswith(coms.GENERATED_NOTICE + "\n\n"))
        reparsed = coms.Graph().parse(output, format="turtle")
        self.assertEqual(set(graph), set(reparsed))

    def test_union_domain_generates_one_union_expression(self) -> None:
        target = "(sosa:Observation or sosa:Actuation or sosa:Sampling)"
        graph, _, stats = self.generate([(SUBJECT, "rdfs:domain", target)])

        domain_objects = list(graph.objects(SUBJECT_IRI, RDFS.domain))
        self.assertEqual(len(domain_objects), 1)
        self.assertIsInstance(domain_objects[0], BNode)
        union_lists = list(graph.objects(domain_objects[0], OWL.unionOf))
        self.assertEqual(len(union_lists), 1)
        self.assertEqual(
            set(Collection(graph, union_lists[0])),
            {OBSERVATION, ACTUATION, SAMPLING},
        )
        self.assertEqual(len(list(graph.triples((None, OWL.unionOf, None)))), 1)
        self.assertEqual(stats.domain_rows, 1)

    def test_named_class_range(self) -> None:
        graph, _, stats = self.generate([(SUBJECT, "rdfs:range", "sosa:FeatureOfInterest")])

        self.assertIn((SUBJECT_IRI, RDFS.range, FEATURE_OF_INTEREST), graph)
        self.assertEqual(stats.range_rows, 1)
        self.assertEqual(stats.object_property_mapping_rows, 0)

    def test_complex_class_expression_range(self) -> None:
        target = (
            "sosa:FeatureOfInterest and "
            "(sosa:isFeatureOfInterestOf some sosa:Observation)"
        )
        graph, _, _ = self.generate([(SUBJECT, "rdfs:range", target)])

        range_objects = list(graph.objects(SUBJECT_IRI, RDFS.range))
        self.assertEqual(len(range_objects), 1)
        members = list(Collection(graph, next(graph.objects(range_objects[0], OWL.intersectionOf))))
        restrictions = [member for member in members if (member, RDF.type, OWL.Restriction) in graph]
        self.assertEqual(len(restrictions), 1)
        restriction = restrictions[0]
        self.assertIn(
            (restriction, OWL.onProperty, URIRef("http://www.w3.org/ns/sosa/isFeatureOfInterestOf")),
            graph,
        )
        self.assertIn((restriction, OWL.someValuesFrom, OBSERVATION), graph)

    def test_unresolved_subject(self) -> None:
        self.assert_generation_error(
            [("sosa:NoSuchProperty", "rdfs:domain", "sosa:Observation")],
            "Synthetic!2",
            "source subject",
            "cannot be resolved",
        )

    def test_class_subject_is_rejected(self) -> None:
        self.assert_generation_error(
            [("sosa:Observation", "rdfs:domain", "sosa:Observation")],
            "Synthetic!2",
            "rdfs:domain requires an object-property subject",
            "resolves as class",
        )

    def test_malformed_target(self) -> None:
        self.assert_generation_error(
            [(SUBJECT, "rdfs:domain", "sosa:Observation or")],
            "Synthetic!2",
            "unexpected end of expression",
        )

    def test_object_property_target_is_rejected_as_non_class(self) -> None:
        self.assert_generation_error(
            [(SUBJECT, "rdfs:range", "sosa:isFeatureOfInterestOf")],
            "Synthetic!2",
            "not class",
        )

    def test_duplicate_domain_rows_are_rejected(self) -> None:
        self.assert_generation_error(
            [
                (SUBJECT, "rdfs:domain", "sosa:Observation"),
                (SUBJECT, "rdfs:domain", "sosa:Actuation"),
            ],
            "Synthetic!3",
            "duplicate rdfs:domain row",
            "Multiple OWL domain axioms are conjunctive",
            "Manchester 'or'",
        )

    def test_duplicate_range_rows_are_rejected(self) -> None:
        self.assert_generation_error(
            [
                (SUBJECT, "rdfs:range", "sosa:FeatureOfInterest"),
                (SUBJECT, "rdfs:range", "sosa:Observation"),
            ],
            "Synthetic!3",
            "duplicate rdfs:range row",
            "Multiple OWL range axioms are conjunctive",
            "Manchester 'or'",
        )

    def test_subproperty_domain_and_range_can_coexist(self) -> None:
        graph, processed, stats = self.generate(
            [
                (SUBJECT, "rdfs:subPropertyOf", "sosa:isFeatureOfInterestOf"),
                (SUBJECT, "rdfs:domain", "sosa:Observation or sosa:Actuation"),
                (SUBJECT, "rdfs:range", "sosa:FeatureOfInterest"),
            ]
        )

        self.assertEqual(stats.mapped_rows, 1)
        self.assertEqual(stats.object_property_mapping_rows, 1)
        self.assertEqual(stats.domain_rows, 1)
        self.assertEqual(stats.range_rows, 1)
        self.assertEqual(stats.property_chain_rows, 0)
        self.assertEqual(stats.active_axiom_rows, 3)
        self.assertEqual(len(list(graph.objects(SUBJECT_IRI, RDFS.subPropertyOf))), 1)
        self.assertEqual(len(list(graph.objects(SUBJECT_IRI, RDFS.domain))), 1)
        self.assertEqual(len(list(graph.objects(SUBJECT_IRI, RDFS.range))), 1)
        coverage = coms.build_coverage(processed, [], self.root / "coexistence-coverage.md")
        self.assertIn(SUBJECT_IRI, coverage.mapped_object_properties)
        self.assertNotIn(SUBJECT_IRI, coverage.property_typing_only_terms)
        self.assertNotIn(SUBJECT_IRI, coverage.unmapped_object_properties)

    def coverage_classification_fixture(self):
        processed, _ = self.process(
            [
                ("sosa:actsOnProperty", "rdfs:subPropertyOf", "sosa:isActedOnBy"),
                (SUBJECT, "rdfs:domain", "sosa:Observation"),
                ("sosa:hasResult", "rdfs:range", "sosa:Result"),
            ]
        )
        return coms.build_coverage(processed, [], self.root / "coverage.md")

    def test_relation_mapped_property_is_mapped_and_covered(self) -> None:
        coverage = self.coverage_classification_fixture()

        self.assertIn(MAPPED_PROPERTY, coverage.mapped_object_properties)
        self.assertNotIn(MAPPED_PROPERTY, coverage.property_typing_only_terms)
        self.assertNotIn(MAPPED_PROPERTY, coverage.unmapped_object_properties)

    def test_domain_only_property_is_covered_but_not_mapped(self) -> None:
        coverage = self.coverage_classification_fixture()

        self.assertNotIn(DOMAIN_ONLY_PROPERTY, coverage.mapped_object_properties)
        self.assertIn(DOMAIN_ONLY_PROPERTY, coverage.property_typing_only_terms)
        self.assertNotIn(DOMAIN_ONLY_PROPERTY, coverage.unmapped_object_properties)

    def test_range_only_property_is_covered_but_not_mapped(self) -> None:
        coverage = self.coverage_classification_fixture()

        self.assertNotIn(RANGE_ONLY_PROPERTY, coverage.mapped_object_properties)
        self.assertIn(RANGE_ONLY_PROPERTY, coverage.property_typing_only_terms)
        self.assertNotIn(RANGE_ONLY_PROPERTY, coverage.unmapped_object_properties)

    def test_genuinely_uncovered_property_remains_unmapped(self) -> None:
        coverage = self.coverage_classification_fixture()

        self.assertNotIn(UNCOVERED_PROPERTY, coverage.mapped_object_properties)
        self.assertNotIn(UNCOVERED_PROPERTY, coverage.property_typing_only_terms)
        self.assertIn(UNCOVERED_PROPERTY, coverage.unmapped_object_properties)
        self.assertEqual(
            coverage.query_unmapped_count,
            len(coverage.unmapped_classes) + len(coverage.unmapped_object_properties),
        )


class ComsGenerationReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="coms-report-test-")
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def hermit_result(self, robot_path: str | None) -> coms.HermitResult:
        available = robot_path is not None
        return coms.HermitResult(
            graph_path=self.root / "closure.ttl",
            reasoned_path=self.root / "reasoned.ttl",
            generated_triple_count=1117,
            closure_triple_count=15905,
            return_code=0 if available else None,
            reasoned_output_produced=available,
            owl_nothing_count=0 if available else None,
            unsat_classes=[],
            robot_output="" if available else "ROBOT executable not found on PATH.",
            robot_path=robot_path,
        )

    def render_report(
        self,
        name: str,
        robot_path: str | None,
        *,
        stats: coms.WorkbookStats | None = None,
        identity_audits: list[identity.CanonicalRowAudit] | None = None,
        disposition_document: dispositions.DispositionDocument | None = None,
        alignment_core_result: object | None = None,
        alignment_core_hermit: object | None = None,
    ) -> str:
        path = self.root / f"{name}.md"
        coms.write_generation_report(
            path,
            workbook_path=Path("mappings/SSN2BFO-COMS.xlsx"),
            stats=stats or coms.WorkbookStats(),
            resolver=mock.Mock(records={}),
            errors=[] if robot_path is not None else ["candidate HermiT unavailable"],
            output_path=Path("SSN2BFO.ttl"),
            hermit=self.hermit_result(robot_path),
            coverage=None,
            comparison=None,
            normalized_rows=[],
            identity_audits=identity_audits or [],
            elapsed_seconds=1.0,
            workbook_sha256="workbook-hash",
            generator_sha256="generator-hash",
            identity_module_sha256="identity-module-hash",
            generation_timestamp="2026-01-01T00:00:00+00:00",
            candidate_sha256="candidate-hash",
            disposition_document=disposition_document,
            disposition_path=Path("reports/coms-product-dispositions.json"),
            disposition_sha256="disposition-hash",
            disposition_module_sha256="disposition-module-hash",
            publication_metadata_sha256="publication-metadata-hash",
            modular_products_module_sha256="modular-products-module-hash",
            alignment_core_result=alignment_core_result,
            alignment_core_path=Path(
                "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl"
            ),
            alignment_core_sha256="alignment-core-hash",
            alignment_core_hermit=alignment_core_hermit,
        )
        return path.read_text(encoding="utf-8")

    def test_robot_report_value_is_stable_across_paths_and_accurate_when_missing(self) -> None:
        first_path = "/opt/toolchains/robot-a/bin/robot"
        second_path = "/home/runner/work/_temp/robot-b/bin/robot"
        first_report = self.render_report("first", first_path)
        second_report = self.render_report("second", second_path)

        self.assertEqual(first_report, second_report)
        self.assertNotIn(first_path, first_report)
        self.assertNotIn(second_path, second_report)
        self.assertIn(
            "| ROBOT command | `robot` (resolved from `PATH`) |",
            first_report,
        )

        missing_report = self.render_report("missing", None)
        self.assertIn(
            "| ROBOT command | `robot` (not found on `PATH`) |",
            missing_report,
        )
        self.assertIn("ROBOT executable not found on PATH.", missing_report)

    def test_generation_report_includes_row_identity_audit(self) -> None:
        row = identity.CanonicalRowInput(
            row_id="urn:uuid:11111111-1111-4111-8111-111111111111",
            location=identity.RowLocation("Synthetic", 7),
            subject_iri=str(SUBJECT_IRI),
            predicate_iri=identity.RDFS_DOMAIN,
            mapping_type="domain",
            expression=identity.ExpressionNode(kind="named", iri=str(OBSERVATION)),
        )
        audit = identity.build_row_audit(row)
        stats = coms.WorkbookStats(
            worksheets_read=["Synthetic"],
            domain_rows=1,
            governed_row_id_count=1,
            unique_row_id_count=1,
            processed_row_count=1,
            identity_audit_row_count=1,
            identity_count_reconciliation_passed=True,
            identity_row_id_set_reconciliation_passed=True,
            identity_location_reconciliation_passed=True,
        )
        report = self.render_report(
            "identity",
            "/opt/robot",
            stats=stats,
            identity_audits=[audit],
            disposition_document=dispositions.build_disposition_document(
                [
                    dispositions.DispositionRowInput(
                        row_id=row.row_id,
                        location=row.location,
                        subject_lexical=SUBJECT,
                        predicate_lexical="rdfs:domain",
                        authoritative_target_lexical="sosa:Observation",
                        canonical_row=audit.expression,
                        source_expression_sha256=audit.source_expression_sha256,
                        mapping_type="domain",
                        reasoning="",
                        authoritative_axioms=tuple(
                            dispositions.axiom_input_from_canonical_row(axiom, row)
                            for axiom in audit.authoritative_axioms
                        ),
                    )
                ],
                load_metadata(REPO_ROOT / "config/publication-metadata.toml"),
                dispositions.RequiredInputHashes(*["0" * 64] * 5),
            ),
        )

        self.assertIn("Governed RowID header: `coms:RowID`", report)
        self.assertIn("Canonical-expression version: `coms-row-expression-v1`", report)
        self.assertIn("Processed governed row count: 1", report)
        self.assertIn("Identity-audit row count: 1", report)
        self.assertIn("Canonical authoritative axiom count: 1", report)
        self.assertIn("Count reconciliation result: PASS", report)
        self.assertIn("RowID-set reconciliation result: PASS", report)
        self.assertIn("Location reconciliation result: PASS", report)
        self.assertIn("Identity-audit completeness result: PASS", report)
        self.assertIn("Duplicate RowID result: PASS", report)
        self.assertIn("Duplicate authoritative-axiom result: PASS", report)
        self.assertIn(audit.row_id, report)
        self.assertIn(audit.source_expression_sha256, report)
        self.assertIn(audit.authoritative_axioms[0].canonical_axiom, report)
        self.assertIn("_(blank)_", report)
        self.assertIn("## Product Dispositions", report)
        self.assertIn("Target-neutral axioms: 1", report)
        self.assertIn("Disposition reconciliation and canonical serialization: PASS", report)

    def test_generation_report_includes_alignment_core_results(self) -> None:
        result = SimpleNamespace(
            metadata=SimpleNamespace(
                stable_ontology_iri=(
                    "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core"
                )
            ),
            governed_axiom_count=29,
            domain_axiom_count=15,
            range_axiom_count=14,
            named_target_count=26,
            union_target_count=3,
            logical_triple_count=53,
            ontology_header_triple_count=1,
            total_triple_count=54,
        )
        hermit = SimpleNamespace(
            return_code=0,
            reasoned_output_produced=True,
            unsat_classes=[],
            passed=True,
        )

        report = self.render_report(
            "alignment-core",
            "/opt/robot",
            alignment_core_result=result,
            alignment_core_hermit=hermit,
        )

        self.assertIn("## Alignment Core", report)
        self.assertIn(
            "maintained authoritative development artifact at the approved production path",
            report,
        )
        self.assertIn("Governed authoritative axioms: 29", report)
        self.assertIn("Domain axioms: 15", report)
        self.assertIn("Range axioms: 14", report)
        self.assertIn("Logical RDF triples: 53", report)
        self.assertIn("Total RDF triples: 54", report)
        self.assertIn("Source-closure HermiT result: PASS", report)


class ComsAuthorityMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="coms-authority-test-")
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def maintained_outputs(self) -> dict[str, Path]:
        return {
            "candidate": self.root / "SSN2BFO.ttl",
            "generation_report": self.root / "reports/coms-generation-validation.md",
            "coverage_report": self.root / "reports/coms-source-term-coverage.md",
            "diff_report": self.root / "reports/coms-vs-pre-coms-legacy-diff.md",
            "disposition_report": self.root / "reports/coms-product-dispositions.json",
            "alignment_core": self.root / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
        }

    @staticmethod
    def write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_root_ontology_is_the_maintained_output(self) -> None:
        self.assertEqual(checker.MAINTAINED_OUTPUTS["candidate"], REPO_ROOT / "SSN2BFO.ttl")
        self.assertEqual(
            checker.MAINTAINED_OUTPUTS["diff_report"],
            REPO_ROOT / "reports/coms-vs-pre-coms-legacy-diff.md",
        )
        self.assertEqual(
            checker.MAINTAINED_OUTPUTS["disposition_report"],
            REPO_ROOT / "reports/coms-product-dispositions.json",
        )
        self.assertEqual(
            checker.MAINTAINED_OUTPUTS["alignment_core"],
            REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
        )

    def test_legacy_ontology_is_the_comparison_baseline(self) -> None:
        generated_path = self.root / "generated.ttl"
        legacy_path = self.root / "legacy.ttl"
        report_path = self.root / "comparison.md"
        subject = URIRef("http://example.org/Source")
        coms_target = URIRef("http://example.org/ComsTarget")
        legacy_target = URIRef("http://example.org/LegacyTarget")
        generated = coms.Graph()
        generated.add((subject, RDFS.subClassOf, coms_target))
        generated.serialize(destination=generated_path, format="turtle")
        legacy = coms.Graph()
        legacy.add((subject, RDFS.subClassOf, legacy_target))
        legacy.serialize(destination=legacy_path, format="turtle")

        with mock.patch.object(coms, "LEGACY_ONTOLOGY", legacy_path):
            result = coms.compare_coms_to_legacy(generated_path, report_path, [])

        self.assertIn(("class", str(subject), str(RDFS.subClassOf), str(coms_target)), result.coms_only)
        self.assertIn(("class", str(subject), str(RDFS.subClassOf), str(legacy_target)), result.legacy_only)
        self.assertIn("COMS vs Pre-COMS Legacy", report_path.read_text(encoding="utf-8"))

    def test_freshness_uses_the_root_ontology_hash(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"maintained-{name}\n")
        candidate_hash = checker.sha256_file(outputs["candidate"])
        disposition_hash = checker.sha256_file(outputs["disposition_report"])
        disposition_module_hash = checker.sha256_file(checker.DISPOSITION_MODULE)
        modular_products_module_hash = checker.sha256_file(checker.MODULAR_PRODUCTS_MODULE)
        publication_metadata_hash = checker.sha256_file(checker.PUBLICATION_METADATA)
        alignment_core_hash = checker.sha256_file(outputs["alignment_core"])
        self.write(
            outputs["generation_report"],
            "\n".join(
                [
                    "| workbook SHA-256 | `workbook-hash` |",
                    "| generator SHA-256 | `generator-hash` |",
                    f"| product-disposition module SHA-256 | `{disposition_module_hash}` |",
                    f"| modular-products module SHA-256 | `{modular_products_module_hash}` |",
                    f"| publication metadata SHA-256 | `{publication_metadata_hash}` |",
                    "| generation timestamp (UTC) | `2026-01-01T00:00:00+00:00` |",
                    "| maintained ontology path | `SSN2BFO.ttl` |",
                    f"| generated ontology SHA-256 | `{candidate_hash}` |",
                    "| maintained product-disposition path | `reports/coms-product-dispositions.json` |",
                    f"| product-disposition JSON SHA-256 | `{disposition_hash}` |",
                    "| maintained alignment-core path | `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` |",
                    f"| alignment-core Turtle SHA-256 | `{alignment_core_hash}` |",
                ]
            ),
        )

        fake_disposition = SimpleNamespace(
            input_hashes=SimpleNamespace(
                workbook_sha256="workbook-hash",
                generator_sha256="generator-hash",
                row_identity_module_sha256=checker.sha256_file(checker.ROW_IDENTITY_MODULE),
                disposition_module_sha256=disposition_module_hash,
                publication_metadata_sha256=publication_metadata_hash,
            ),
            product_order=tuple(
                product.key for product in load_metadata(checker.PUBLICATION_METADATA).products
            ),
        )

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "load_disposition_document", return_value=fake_disposition),
            mock.patch.object(
                checker,
                "serialize_disposition_document",
                return_value=outputs["disposition_report"].read_bytes(),
            ),
        ):
            self.assertEqual(checker.freshness_errors("workbook-hash", "generator-hash"), [])
            self.write(outputs["candidate"], "changed root ontology\n")
            self.assertIn(
                "generated candidate hash differs from the generated report",
                checker.freshness_errors("workbook-hash", "generator-hash"),
            )

    def test_stale_alignment_core_hash_fails_check_only_without_rewriting_outputs(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"maintained-{name}\n")
        candidate_hash = checker.sha256_file(outputs["candidate"])
        disposition_hash = checker.sha256_file(outputs["disposition_report"])
        disposition_module_hash = checker.sha256_file(checker.DISPOSITION_MODULE)
        modular_products_module_hash = checker.sha256_file(checker.MODULAR_PRODUCTS_MODULE)
        publication_metadata_hash = checker.sha256_file(checker.PUBLICATION_METADATA)
        alignment_core_hash = checker.sha256_file(outputs["alignment_core"])
        self.write(
            outputs["generation_report"],
            "\n".join(
                [
                    "| workbook SHA-256 | `workbook-hash` |",
                    "| generator SHA-256 | `generator-hash` |",
                    f"| product-disposition module SHA-256 | `{disposition_module_hash}` |",
                    f"| modular-products module SHA-256 | `{modular_products_module_hash}` |",
                    f"| publication metadata SHA-256 | `{publication_metadata_hash}` |",
                    "| generation timestamp (UTC) | `2026-01-01T00:00:00+00:00` |",
                    "| maintained ontology path | `SSN2BFO.ttl` |",
                    f"| generated ontology SHA-256 | `{candidate_hash}` |",
                    "| maintained product-disposition path | `reports/coms-product-dispositions.json` |",
                    f"| product-disposition JSON SHA-256 | `{disposition_hash}` |",
                    "| maintained alignment-core path | `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` |",
                    f"| alignment-core Turtle SHA-256 | `{alignment_core_hash}` |",
                ]
            ),
        )
        fake_disposition = SimpleNamespace(
            input_hashes=SimpleNamespace(
                workbook_sha256="workbook-hash",
                generator_sha256="generator-hash",
                row_identity_module_sha256=checker.sha256_file(checker.ROW_IDENTITY_MODULE),
                disposition_module_sha256=disposition_module_hash,
                publication_metadata_sha256=publication_metadata_hash,
            ),
            product_order=tuple(
                product.key for product in load_metadata(checker.PUBLICATION_METADATA).products
            ),
        )
        cache_dir = self.root / ".cache/coms"
        run_generator = mock.Mock()

        self.write(outputs["alignment_core"], "modified maintained alignment core\n")
        expected = {path: path.read_bytes() for path in outputs.values()}

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "run_generator", run_generator),
            mock.patch.object(checker, "load_disposition_document", return_value=fake_disposition),
            mock.patch.object(
                checker,
                "serialize_disposition_document",
                return_value=outputs["disposition_report"].read_bytes(),
            ),
            mock.patch.object(checker, "write_failure_log"),
        ):
            errors = checker.freshness_errors("workbook-hash", "generator-hash")
            self.assertEqual(
                errors,
                ["alignment-core hash differs from the generated report"],
            )
            self.assertEqual(
                checker.relative(outputs["alignment_core"]),
                "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
            )
            self.assertNotIn(
                "generated candidate hash differs from the generated report",
                errors,
            )
            self.assertEqual(checker.main(["--check-only"]), 1)

        run_generator.assert_not_called()
        for path, content in expected.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(list(cache_dir.glob("run-*")), [])

    def test_first_successful_update_creates_initially_absent_alignment_core(self) -> None:
        outputs = self.maintained_outputs()
        existing = {
            name: path
            for name, path in outputs.items()
            if name != "alignment_core"
        }
        for name, path in existing.items():
            self.write(path, f"old-{name}\n")
        self.assertFalse(outputs["alignment_core"].exists())

        expected_generated = {
            name: f"new-{name}\n".encode("utf-8")
            for name in existing
        }
        alignment_core_bytes = (
            REPO_ROOT
            / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl"
        ).read_bytes()
        ontology_iri = URIRef(
            "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core"
        )
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []
        events: list[str] = []
        validation_complete = False

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            self.assertFalse(outputs["alignment_core"].exists())
            transaction_dirs.append(paths["candidate"].parents[1])
            for name, content in expected_generated.items():
                paths[name].parent.mkdir(parents=True, exist_ok=True)
                paths[name].write_bytes(content)
            paths["alignment_core"].parent.mkdir(parents=True, exist_ok=True)
            paths["alignment_core"].write_bytes(alignment_core_bytes)
            self.write(paths["summary"], "{}\n")
            events.append("generated")

        def fake_validate(paths: dict[str, Path], *_args, **_kwargs):
            nonlocal validation_complete
            self.assertFalse(outputs["alignment_core"].exists())
            graph = coms.Graph().parse(paths["alignment_core"], format="turtle")
            self.assertEqual(set(graph.subjects(RDF.type, OWL.Ontology)), {ontology_iri})
            self.assertEqual(list(graph.triples((None, OWL.imports, None))), [])
            governed_axioms = len(set(graph.triples((None, RDFS.domain, None)))) + len(
                set(graph.triples((None, RDFS.range, None)))
            )
            self.assertEqual(governed_axioms, 29)
            self.assertEqual(len(graph), 54)
            validation_complete = True
            events.append("validated")
            return {}

        production_replace = checker.replace_outputs_atomically

        def observe_replace(
            paths: dict[str, Path], transaction_dir: Path, log: list[str]
        ) -> None:
            self.assertTrue(validation_complete)
            self.assertFalse(outputs["alignment_core"].exists())
            events.append("replace-start")
            production_replace(paths, transaction_dir, log)
            self.assertTrue(outputs["alignment_core"].exists())
            events.append("replace-complete")

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=["missing alignment core"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "validate_temporary_outputs", side_effect=fake_validate),
            mock.patch.object(checker, "git_diff_check"),
            mock.patch.object(checker, "output_differences", return_value=list(outputs)),
            mock.patch.object(
                checker,
                "replace_outputs_atomically",
                side_effect=observe_replace,
            ),
            mock.patch.object(checker, "record_success"),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 0)

        self.assertEqual(
            events,
            ["generated", "validated", "replace-start", "replace-complete"],
        )
        for name, content in expected_generated.items():
            self.assertEqual(outputs[name].read_bytes(), content)
        self.assertEqual(outputs["alignment_core"].read_bytes(), alignment_core_bytes)
        final_graph = coms.Graph().parse(outputs["alignment_core"], format="turtle")
        self.assertEqual(set(final_graph.subjects(RDF.type, OWL.Ontology)), {ontology_iri})
        self.assertEqual(list(final_graph.triples((None, OWL.imports, None))), [])
        self.assertEqual(
            len(set(final_graph.triples((None, RDFS.domain, None))))
            + len(set(final_graph.triples((None, RDFS.range, None)))),
            29,
        )
        self.assertEqual(len(final_graph), 54)
        self.assertTrue(all(path.is_file() for path in outputs.values()))
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())
        self.assertEqual(list(cache_dir.glob("run-*")), [])

    def test_temporary_validation_precedes_atomic_root_replacement(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"old-{name}\n")
        cache_dir = self.root / ".cache/coms"

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            for name in outputs:
                self.write(paths[name], f"new-{name}\n")
            self.write(paths["summary"], "{}\n")

        def fake_validate(*_args, **_kwargs):
            self.assertEqual(outputs["candidate"].read_text(encoding="utf-8"), "old-candidate\n")
            return {}

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=["stale"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "validate_temporary_outputs", side_effect=fake_validate),
            mock.patch.object(checker, "git_diff_check"),
            mock.patch.object(checker, "output_differences", return_value=["candidate"]),
            mock.patch.object(checker, "record_success"),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 0)

        self.assertEqual(outputs["candidate"].read_text(encoding="utf-8"), "new-candidate\n")

    def test_check_only_preserves_all_six_outputs_and_workbook(self) -> None:
        outputs = self.maintained_outputs()
        workbook = self.root / "mappings/SSN2BFO-COMS.xlsx"
        self.write(workbook, "workbook-bytes\n")
        for name, path in outputs.items():
            self.write(path, f"maintained-{name}\n")
        protected = [workbook, *outputs.values()]
        before = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in protected
        }
        files_before = {
            path.relative_to(self.root)
            for path in self.root.rglob("*")
            if path.is_file()
        }
        cache_dir = self.root / ".cache/coms"

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            for name in outputs:
                self.write(paths[name], f"temporary-{name}\n")
            self.write(paths["summary"], "{}\n")

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "WORKBOOK", workbook),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=[]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "validate_temporary_outputs", return_value={}),
            mock.patch.object(checker, "git_diff_check"),
            mock.patch.object(checker, "output_differences", return_value=[]),
            mock.patch.object(checker, "record_success"),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main(["--check-only"]), 0)

        for path, expected in before.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), expected)
        files_after = {
            path.relative_to(self.root)
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(files_after, files_before)

    def test_rollback_removes_new_disposition_when_it_was_initially_absent(self) -> None:
        outputs = self.maintained_outputs()
        existing = {
            name: path
            for name, path in outputs.items()
            if name != "disposition_report"
        }
        for name, path in existing.items():
            self.write(path, f"old-{name}\n")
        before = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in existing.values()
        }
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            transaction_dirs.append(paths["candidate"].parents[1])
            for name in outputs:
                self.write(paths[name], f"new-{name}\n")
            self.write(paths["summary"], "{}\n")

        diff_checks = 0

        def fail_post_update(_log: list[str], _label: str) -> None:
            nonlocal diff_checks
            diff_checks += 1
            if diff_checks == 2:
                raise checker.CheckFailure("post-update failure")

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=["stale"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "validate_temporary_outputs", return_value={}),
            mock.patch.object(checker, "git_diff_check", side_effect=fail_post_update),
            mock.patch.object(checker, "output_differences", return_value=list(outputs)),
            mock.patch.object(checker, "record_success"),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 1)

        self.assertEqual(diff_checks, 2)
        for path, expected in before.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), expected)
        self.assertFalse(outputs["disposition_report"].exists())
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())

    def test_rollback_removes_new_alignment_core_when_it_was_initially_absent(self) -> None:
        outputs = self.maintained_outputs()
        existing = {
            name: path
            for name, path in outputs.items()
            if name != "alignment_core"
        }
        for name, path in existing.items():
            self.write(path, f"old-{name}\n")
        before = {path: path.read_bytes() for path in existing.values()}
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            transaction_dirs.append(paths["candidate"].parents[1])
            for name in outputs:
                self.write(paths[name], f"new-{name}\n")
            self.write(paths["summary"], "{}\n")

        diff_checks = 0

        def fail_post_update(_log: list[str], _label: str) -> None:
            nonlocal diff_checks
            diff_checks += 1
            if diff_checks == 2:
                raise checker.CheckFailure("post-update failure")

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=["stale"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "validate_temporary_outputs", return_value={}),
            mock.patch.object(checker, "git_diff_check", side_effect=fail_post_update),
            mock.patch.object(checker, "output_differences", return_value=list(outputs)),
            mock.patch.object(checker, "record_success"),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 1)

        self.assertEqual(diff_checks, 2)
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)
        self.assertFalse(outputs["alignment_core"].exists())
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())

    def test_written_malformed_disposition_fails_before_replacement(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"old-{name}\n")
        before = {path: path.read_bytes() for path in outputs.values()}
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []
        observed_candidates: list[bytes] = []

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            transaction_dirs.append(paths["candidate"].parents[1])
            for name in outputs:
                self.write(paths[name], f"temporary-{name}\n")
            self.write(
                paths["disposition_report"],
                json.dumps({"schema_version": 1}, indent=2) + "\n",
            )
            self.write(
                paths["summary"],
                json.dumps(
                    {
                        "status": "PASS",
                        "workbook_sha256": "workbook-hash",
                        "generator_sha256": "generator-hash",
                    }
                )
                + "\n",
            )

        production_loader = checker.load_disposition_document

        def observe_load(path: Path):
            observed_candidates.append(path.read_bytes())
            return production_loader(path)

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=["stale"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "load_disposition_document", side_effect=observe_load),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 1)

        self.assertEqual(len(observed_candidates), 1)
        self.assertIn(b'"schema_version": 1', observed_candidates[0])
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())

    def test_written_malformed_alignment_core_fails_before_replacement(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"old-{name}\n")
        before = {path: path.read_bytes() for path in outputs.values()}
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []
        observed_candidates: list[bytes] = []
        disposition_source = REPO_ROOT / "reports/coms-product-dispositions.json"
        disposition = checker.load_disposition_document(disposition_source)
        disposition_bytes = disposition_source.read_bytes()
        workbook_hash = disposition.input_hashes.workbook_sha256
        generator_hash = disposition.input_hashes.generator_sha256

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            transaction_dirs.append(paths["candidate"].parents[1])
            for name in outputs:
                self.write(paths[name], f"temporary-{name}\n")
            paths["disposition_report"].write_bytes(disposition_bytes)
            malformed_core = b"@prefix owl: <http://www.w3.org/2002/07/owl#> .\n[\n"
            paths["alignment_core"].write_bytes(malformed_core)
            self.write(
                paths["summary"],
                json.dumps(
                    {
                        "status": "PASS",
                        "workbook_sha256": workbook_hash,
                        "generator_sha256": generator_hash,
                        "product_disposition_report_sha256": checker.sha256_file(
                            paths["disposition_report"]
                        ),
                        "product_dispositions": {
                            field: getattr(disposition.summary, field)
                            for field in disposition.summary.__dataclass_fields__
                        },
                        "alignment_core_sha256": checker.sha256_file(
                            paths["alignment_core"]
                        ),
                        "modular_products_module_sha256": checker.sha256_file(
                            checker.MODULAR_PRODUCTS_MODULE
                        ),
                        "alignment_core": {
                            "product_key": "alignment_core",
                            "stable_ontology_iri": (
                                "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core"
                            ),
                            "governed_axiom_count": 29,
                            "logical_triple_count": 53,
                            "ontology_header_triple_count": 1,
                            "total_triple_count": 54,
                            "domain_axiom_count": 15,
                            "range_axiom_count": 14,
                            "named_target_count": 26,
                            "union_target_count": 3,
                            "hermit_return_code": 0,
                            "hermit_result": "PASS",
                            "named_unsat_count": 0,
                        },
                    }
                )
                + "\n",
            )

        original_parse = checker.Graph.parse

        def observe_parse(graph, source=None, *args, **kwargs):
            if source == checker.transaction_paths(transaction_dirs[0])["alignment_core"]:
                observed_candidates.append(Path(source).read_bytes())
            return original_parse(graph, source, *args, **kwargs)

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value=workbook_hash),
            mock.patch.object(checker, "compile_generator", return_value=generator_hash),
            mock.patch.object(checker, "freshness_errors", return_value=["stale"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker.Graph, "parse", new=observe_parse),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 1)

        self.assertEqual(len(observed_candidates), 1)
        self.assertIn(b"[", observed_candidates[0])
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())

    def test_atomic_replacement_rolls_back_root_on_post_update_failure(self) -> None:
        outputs = self.maintained_outputs()
        transaction_dir = self.root / "transaction"
        paths = checker.transaction_paths(transaction_dir)
        for name, destination in outputs.items():
            self.write(destination, f"old-{name}\n")
            self.write(paths[name], f"new-{name}\n")

        with (
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "git_diff_check", side_effect=checker.CheckFailure("post-update failure")),
            self.assertRaises(checker.CheckFailure),
        ):
            checker.replace_outputs_atomically(paths, transaction_dir, [])

        for name, destination in outputs.items():
            self.assertEqual(destination.read_text(encoding="utf-8"), f"old-{name}\n")

    def test_no_active_dependency_on_retired_generated_path(self) -> None:
        retired = str(Path("generated") / "SSN2BFO-from-COMS.ttl")
        active_files = [REPO_ROOT / "Makefile", REPO_ROOT / "README.md"]
        active_files.extend((REPO_ROOT / "tools").glob("*.py"))
        active_files.extend((REPO_ROOT / "tests").glob("*.py"))
        active_files.extend((REPO_ROOT / "src").rglob("Makefile"))
        for path in active_files:
            self.assertNotIn(retired, path.read_text(encoding="utf-8"), str(path))
        self.assertFalse((REPO_ROOT / retired).exists())


if __name__ == "__main__":
    unittest.main()
