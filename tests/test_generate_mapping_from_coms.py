#!/usr/bin/env python3
"""Focused tests for COMS generation, coverage, and authority migration."""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import openpyxl
from rdflib import BNode, Graph, Literal, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection
from rdflib.compare import isomorphic


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_coms_mapping as checker  # noqa: E402
import coms_row_identity as identity  # noqa: E402
import generate_mapping_from_coms as coms  # noqa: E402
import modular_products as modular  # noqa: E402
import product_dispositions as dispositions  # noqa: E402
from publication_metadata import (  # noqa: E402
    load_metadata,
    ontology_metadata_rdf_triples,
    strip_emitted_ontology_header,
    validate_emitted_ontology_metadata,
)


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
        self.metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")

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
        graph = coms.generate_ontology(processed, output, self.metadata)
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
                "--strict-bfo-output",
                str(self.root / "strict-bfo.ttl"),
                "--cco-extension-output",
                str(self.root / "cco-extension.ttl"),
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
        self.assertFalse((self.root / "strict-bfo.ttl").exists())
        self.assertFalse((self.root / "cco-extension.ttl").exists())
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
        self.assertFalse((self.root / "strict-bfo.ttl").exists())
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
            self.metadata,
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

    def test_explicit_blank_row_has_complete_zero_axiom_identity_audit(self) -> None:
        processed, stats = self.process(
            [
                (
                    SUBJECT,
                    "",
                    "",
                    "Mapping deliberately deferred.",
                )
            ]
        )

        self.assertEqual(stats.governed_row_id_count, 1)
        self.assertEqual(stats.processed_row_count, 1)
        self.assertEqual(stats.identity_audit_row_count, 1)
        self.assertEqual(stats.blank_mapping_rows, 1)
        self.assertTrue(stats.identity_count_reconciliation_passed)
        self.assertTrue(
            stats.identity_row_id_set_reconciliation_passed
        )
        self.assertTrue(stats.identity_location_reconciliation_passed)

        item = processed[0]
        self.assertEqual(item.predicate, "")
        self.assertEqual(item.target, "")

        audit = item.identity_audit
        self.assertIsNotNone(audit)
        self.assertEqual(
            audit.expression.mapping_type,
            "explicit_blank",
        )
        self.assertIsNone(audit.expression.predicate_iri)
        self.assertIsNone(audit.expression.target)
        self.assertEqual(audit.authoritative_axioms, ())

        disposition = coms.disposition_input_for_processed_row(item)
        self.assertEqual(disposition.mapping_type, "explicit_blank")
        self.assertEqual(disposition.authoritative_axioms, ())

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
        coms.generate_ontology(first, first_output, self.metadata)
        second, _ = self.process(rows, row_ids=[self.row_id_for(2)])
        second_output = self.root / "second.ttl"
        coms.generate_ontology(second, second_output, self.metadata)
        self.assertEqual(first_output.read_bytes(), second_output.read_bytes())

    def test_generation_does_not_mutate_workbook(self) -> None:
        workbook_path = self.synthetic_workbook(
            [(SUBJECT, "rdfs:domain", "sosa:Observation")]
        )
        before = workbook_path.read_bytes()
        workbook_rows, stats = coms.read_workbook(workbook_path)
        processed = coms.validate_and_process_rows(workbook_rows, coms.Resolver(), stats)
        coms.generate_ontology(
            processed, self.root / "nonmutating.ttl", self.metadata
        )
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
            generated_triple_count=1114,
            closure_triple_count=15904,
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
        strict_bfo_result: object | None = None,
        strict_bfo_hermit: object | None = None,
        cco_extension_result: object | None = None,
        cco_extension_hermit: object | None = None,
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
            strict_bfo_result=strict_bfo_result,
            strict_bfo_path=Path(
                "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl"
            ),
            strict_bfo_sha256="strict-bfo-hash",
            strict_bfo_hermit=strict_bfo_hermit,
            cco_extension_result=cco_extension_result,
            cco_extension_path=Path(
                "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl"
            ),
            cco_extension_sha256="cco-extension-hash",
            cco_extension_hermit=cco_extension_hermit,
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
            ontology_declaration_triple_count=1,
            import_triple_count=0,
            metadata_annotation_count=7,
            total_triple_count=61,
        )
        hermit = SimpleNamespace(
            closure_triple_count=1214,
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
        self.assertIn("Ontology declaration triples: 1", report)
        self.assertIn("Import triples: 0", report)
        self.assertIn("Descriptive metadata annotations: 7", report)
        self.assertIn("Total RDF triples: 61", report)
        self.assertIn("Source-closure triple count: 1214", report)
        self.assertIn("Source-closure HermiT result: PASS", report)

    def test_generation_report_includes_strict_bfo_results(self) -> None:
        result = SimpleNamespace(
            metadata=SimpleNamespace(
                stable_ontology_iri=(
                    "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping"
                )
            ),
            governed_axiom_count=19,
            subclass_axiom_count=3,
            equivalent_class_axiom_count=3,
            direct_subproperty_axiom_count=9,
            property_chain_axiom_count=2,
            domain_axiom_count=1,
            range_axiom_count=1,
            logical_triple_count=125,
            ontology_declaration_triple_count=1,
            import_triple_count=1,
            metadata_annotation_count=7,
            total_triple_count=134,
        )
        hermit = SimpleNamespace(
            closure_triple_count=14988,
            return_code=0,
            reasoned_output_produced=True,
            unsat_classes=[],
            passed=True,
        )
        report = self.render_report(
            "strict-bfo",
            "/opt/robot",
            strict_bfo_result=result,
            strict_bfo_hermit=hermit,
        )
        self.assertIn("## Strict BFO Mapping", report)
        self.assertIn("Direct governed authoritative axioms: 19", report)
        self.assertIn("Project-module closure governed axioms: 48", report)
        self.assertIn("Descriptive metadata annotations: 7", report)
        self.assertIn("Total RDF triples: 134", report)
        self.assertIn("Pinned closure triple count: 14988", report)
        self.assertIn("HermiT result: PASS", report)

    def test_generation_report_includes_cco_extension_results(self) -> None:
        selected = tuple(
            SimpleNamespace(target_category="cco_bearing") for _ in range(25)
        ) + tuple(
            SimpleNamespace(target_category="mixed_bfo_cco") for _ in range(30)
        )
        result = SimpleNamespace(
            metadata=SimpleNamespace(
                stable_ontology_iri=(
                    "http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension"
                )
            ),
            selected_rows=(SimpleNamespace(axioms=selected),),
            governed_axiom_count=55,
            subclass_axiom_count=31,
            equivalent_class_axiom_count=7,
            direct_subproperty_axiom_count=16,
            property_chain_axiom_count=1,
            logical_triple_count=924,
            ontology_declaration_triple_count=1,
            import_triple_count=1,
            metadata_annotation_count=7,
            total_triple_count=933,
        )
        hermit = SimpleNamespace(
            closure_triple_count=15920,
            return_code=0,
            reasoned_output_produced=True,
            unsat_classes=[],
            passed=True,
        )
        report = self.render_report(
            "cco-extension",
            "/opt/robot",
            cco_extension_result=result,
            cco_extension_hermit=hermit,
        )
        self.assertIn("## CCO Extension", report)
        self.assertIn("Direct governed authoritative axioms: 55", report)
        self.assertIn("CCO-bearing axioms: 25", report)
        self.assertIn("Mixed BFO/CCO axioms: 30", report)
        self.assertIn("Project-module closure governed axioms: 103", report)
        self.assertIn("Descriptive metadata annotations: 7", report)
        self.assertIn("Total RDF triples: 933", report)
        self.assertIn("Pinned closure triple count: 15920", report)



class ComsCheckerBytecodeIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="coms-bytecode-test-")
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def assert_owned_descriptors_closed(
        self,
        owned: checker.OwnedCompilationRoot,
        directory_fd: int,
        marker_fd: int,
    ) -> None:
        self.assertEqual(owned.directory_fd, -1)
        self.assertEqual(owned.marker_fd, -1)
        with self.assertRaises(OSError):
            os.fstat(directory_fd)
        with self.assertRaises(OSError):
            os.fstat(marker_fd)

    @staticmethod
    def bytecode_paths(repository: Path) -> set[str]:
        return {
            path.relative_to(repository).as_posix()
            for path in repository.rglob("*")
            if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}
        }

    @staticmethod
    def path_state(path: Path) -> tuple[int, int, bytes, int, int, int, int]:
        info = os.lstat(path)
        return (
            stat.S_IFMT(info.st_mode),
            stat.S_IMODE(info.st_mode),
            path.read_bytes(),
            info.st_size,
            info.st_mtime_ns,
            info.st_dev,
            info.st_ino,
        )

    def compile_fixture(self) -> tuple[Path, dict[str, Path]]:
        repository = self.root / "compile-repository"
        tools = repository / "tools"
        tools.mkdir(parents=True)
        paths = {
            "GENERATOR": tools / "generate_mapping_from_coms.py",
            "ROW_IDENTITY_MODULE": tools / "coms_row_identity.py",
            "DISPOSITION_MODULE": tools / "product_dispositions.py",
            "MODULAR_PRODUCTS_MODULE": tools / "modular_products.py",
            "PUBLICATION_METADATA_MODULE": tools / "publication_metadata.py",
        }
        for index, path in enumerate(paths.values()):
            path.write_text(f"VALUE = {index}\n", encoding="utf-8")
        return repository, paths

    def checker_patch(self, repository: Path, paths: dict[str, Path]):
        return mock.patch.multiple(checker, REPO_ROOT=repository, **paths)

    def create_sentinels(self, repository: Path) -> dict[Path, tuple[int, int, bytes, int, int, int, int]]:
        sentinels = {
            repository / "tools/__pycache__/preexisting.pyc": b"preexisting-pyc\x00sentinel\n",
            repository / "tests/__pycache__/preexisting.pyo": b"preexisting-pyo\x00sentinel\n",
        }
        for index, (path, content) in enumerate(sentinels.items()):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o640)
            timestamp = 1_700_000_000_000_000_000 + index
            os.utime(path, ns=(timestamp, timestamp))
        return {path: self.path_state(path) for path in sentinels}

    def test_direct_check_only_preserves_repository_bytecode_and_outputs(self) -> None:
        repository = self.root / "direct-repository"
        shutil.copytree(
            REPO_ROOT,
            repository,
            ignore=shutil.ignore_patterns(".git", ".cache", "__pycache__", "*.pyc", "*.pyo"),
        )
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=repository,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        before_sentinels = self.create_sentinels(repository)
        before_bytecode = self.bytecode_paths(repository)
        output_relatives = tuple(
            path.relative_to(REPO_ROOT) for path in checker.MAINTAINED_OUTPUTS.values()
        )
        before_outputs = {
            relative: (repository / relative).read_bytes() for relative in output_relatives
        }
        external_temp = self.root / "direct-external-temp"
        external_temp.mkdir()
        environment = os.environ.copy()
        environment.pop("PYTHONPYCACHEPREFIX", None)
        environment.update(
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "TMPDIR": str(external_temp),
            }
        )

        completed = subprocess.run(
            [sys.executable, "-B", "tools/check_coms_mapping.py", "--check-only"],
            cwd=repository,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Check-only mode: maintained outputs are fresh", completed.stdout)
        self.assertEqual(self.bytecode_paths(repository), before_bytecode)
        for path, state in before_sentinels.items():
            self.assertEqual(self.path_state(path), state)
            self.assertTrue(path.parent.is_dir())
        self.assertEqual(
            {relative: (repository / relative).read_bytes() for relative in output_relatives},
            before_outputs,
        )
        self.assertFalse(
            any(external_temp.glob("ssn-to-bfo-coms-compile-*"))
        )

    def test_compile_generator_uses_only_explicit_external_cfiles_and_restores_process_state(self) -> None:
        repository, paths = self.compile_fixture()
        observed: list[tuple[Path, Path, bool, bool]] = []

        def record_compile(source, *, cfile, doraise):
            destination = Path(cfile)
            observed.append(
                (Path(source), destination, doraise, sys.dont_write_bytecode)
            )
            destination.write_bytes(b"external compiled bytecode\n")
            return str(destination)

        original = sys.dont_write_bytecode
        try:
            for initial in (False, True):
                with self.subTest(initial=initial), self.checker_patch(repository, paths), mock.patch.object(
                    checker.py_compile, "compile", side_effect=record_compile
                ):
                    sys.dont_write_bytecode = initial
                    self.assertEqual(
                        checker.compile_generator([]),
                        checker.sha256_file(paths["GENERATOR"]),
                    )
                    self.assertEqual(sys.dont_write_bytecode, initial)
        finally:
            sys.dont_write_bytecode = original

        self.assertEqual(len(observed), 10)
        for source, destination, doraise, suppressed in observed:
            self.assertIn(source, paths.values())
            self.assertTrue(destination.is_absolute())
            self.assertFalse(destination.is_relative_to(repository))
            self.assertTrue(doraise)
            self.assertTrue(suppressed)
            self.assertFalse(destination.parent.exists())
        self.assertEqual(self.bytecode_paths(repository), set())

    def test_compile_failure_cleans_external_root_and_preserves_preexisting_bytecode(self) -> None:
        repository, paths = self.compile_fixture()
        paths["GENERATOR"].write_text("def invalid(:\n", encoding="utf-8")
        sentinels = self.create_sentinels(repository)
        before_bytecode = self.bytecode_paths(repository)
        roots: list[checker.OwnedCompilationRoot] = []
        original_create = checker.create_compilation_root

        def record_root():
            owned = original_create()
            roots.append(owned)
            return owned

        original_state = sys.dont_write_bytecode
        with self.checker_patch(repository, paths), mock.patch.object(
            checker, "create_compilation_root", side_effect=record_root
        ), self.assertRaises(checker.CheckFailure) as raised:
            checker.compile_generator([])
        self.assertIn("generator compile failed", str(raised.exception))
        self.assertEqual(sys.dont_write_bytecode, original_state)
        self.assertTrue(roots)
        self.assertTrue(all(not owned.path.exists() for owned in roots))
        self.assertEqual(self.bytecode_paths(repository), before_bytecode)
        for path, state in sentinels.items():
            self.assertEqual(self.path_state(path), state)

    def test_compilation_cleanup_refuses_replacement_directory(self) -> None:
        owned = checker.create_compilation_root()
        directory_fd = owned.directory_fd
        marker_fd = owned.marker_fd
        pinned = os.fstat(directory_fd)
        self.assertEqual((pinned.st_dev, pinned.st_ino), (owned.device, owned.inode))
        self.assertTrue(stat.S_ISDIR(pinned.st_mode))
        shutil.rmtree(owned.path)
        owned.path.mkdir()
        sentinel = owned.path / "sentinel.bin"
        sentinel.write_bytes(b"unrelated replacement directory\n")
        self.addCleanup(shutil.rmtree, owned.path, True)

        still_pinned = os.fstat(owned.directory_fd)
        self.assertEqual((still_pinned.st_dev, still_pinned.st_ino), (owned.device, owned.inode))
        self.assertTrue(stat.S_ISDIR(still_pinned.st_mode))
        self.assertTrue(owned.path.is_dir())
        self.assertEqual(sentinel.read_bytes(), b"unrelated replacement directory\n")

        errors = checker.cleanup_compilation_root(owned)

        self.assertEqual(
            errors,
            ("CLEANUP_FAILED COMS compilation root: owned path identity changed",),
        )
        self.assertEqual(sentinel.read_bytes(), b"unrelated replacement directory\n")
        self.assertTrue(owned.path.is_dir())
        self.assert_owned_descriptors_closed(owned, directory_fd, marker_fd)
        self.assertEqual(
            checker.cleanup_compilation_root(owned),
            (checker.COMPILATION_ROOT_IDENTITY_ERROR,),
        )
        self.assertEqual(sentinel.read_bytes(), b"unrelated replacement directory\n")
        self.assertTrue(owned.path.is_dir())

    def test_compilation_cleanup_refuses_replacement_symlink(self) -> None:
        owned = checker.create_compilation_root()
        directory_fd = owned.directory_fd
        marker_fd = owned.marker_fd
        shutil.rmtree(owned.path)
        target = self.root / "unrelated-target"
        target.mkdir()
        sentinel = target / "sentinel.bin"
        sentinel.write_bytes(b"unrelated symlink target\n")
        owned.path.symlink_to(target, target_is_directory=True)
        self.addCleanup(owned.path.unlink, missing_ok=True)

        errors = checker.cleanup_compilation_root(owned)

        self.assertEqual(
            errors,
            ("CLEANUP_FAILED COMS compilation root: owned path identity changed",),
        )
        self.assertTrue(owned.path.is_symlink())
        self.assertEqual(sentinel.read_bytes(), b"unrelated symlink target\n")
        self.assert_owned_descriptors_closed(owned, directory_fd, marker_fd)
        self.assertEqual(
            checker.cleanup_compilation_root(owned),
            (checker.COMPILATION_ROOT_IDENTITY_ERROR,),
        )
        self.assertTrue(owned.path.is_symlink())
        self.assertEqual(sentinel.read_bytes(), b"unrelated symlink target\n")

    def test_compilation_cleanup_rejects_matching_superficial_path_metadata(self) -> None:
        owned = checker.create_compilation_root()
        directory_fd = owned.directory_fd
        marker_fd = owned.marker_fd
        original_lstat = checker.os.lstat
        shutil.rmtree(owned.path)
        owned.path.mkdir()
        sentinel = owned.path / "sentinel.bin"
        sentinel.write_bytes(b"matching superficial metadata replacement\n")
        self.addCleanup(shutil.rmtree, owned.path, True)
        matching_metadata = SimpleNamespace(
            st_dev=owned.device,
            st_ino=owned.inode,
            st_mode=owned.file_type | 0o700,
        )

        def superficial_lstat(path):
            if Path(path) == owned.path:
                return matching_metadata
            return original_lstat(path)

        with mock.patch.object(checker.os, "lstat", side_effect=superficial_lstat):
            errors = checker.cleanup_compilation_root(owned)

        self.assertEqual(errors, (checker.COMPILATION_ROOT_IDENTITY_ERROR,))
        self.assertEqual(sentinel.read_bytes(), b"matching superficial metadata replacement\n")
        self.assertTrue(owned.path.is_dir())
        self.assert_owned_descriptors_closed(owned, directory_fd, marker_fd)
        self.assertEqual(
            checker.cleanup_compilation_root(owned),
            (checker.COMPILATION_ROOT_IDENTITY_ERROR,),
        )
        self.assertEqual(sentinel.read_bytes(), b"matching superficial metadata replacement\n")

    def test_compilation_marker_mutations_fail_closed(self) -> None:
        for case in (
            "missing",
            "directory",
            "symlink",
            "bytes",
            "identity",
            "type",
            "mode",
            "token",
        ):
            with self.subTest(case=case):
                owned = checker.create_compilation_root()
                cleanup_owned = owned
                directory_fd = owned.directory_fd
                marker_fd = owned.marker_fd
                marker = owned.path / owned.marker_name
                original_token = owned.marker_token
                sentinel = owned.path / "sentinel.bin"
                sentinel.write_bytes((case + " marker mutation\n").encode("ascii"))
                symlink_target: Path | None = None
                changed_marker_bytes = b"changed marker bytes\n"

                if case == "missing":
                    marker.unlink()
                elif case == "directory":
                    marker.unlink()
                    marker.mkdir()
                    (marker / "sentinel.bin").write_bytes(b"replacement marker directory\n")
                elif case == "symlink":
                    marker.unlink()
                    symlink_target = self.root / "replacement-marker-target"
                    symlink_target.write_bytes(b"replacement marker symlink target\n")
                    marker.symlink_to(symlink_target)
                elif case == "bytes":
                    marker.write_bytes(changed_marker_bytes)
                    marker.chmod(0o600)
                elif case == "identity":
                    cleanup_owned = replace(owned, marker_inode=owned.marker_inode + 1)
                elif case == "type":
                    cleanup_owned = replace(owned, marker_file_type=stat.S_IFDIR)
                elif case == "mode":
                    marker.chmod(0o640)
                elif case == "token":
                    cleanup_owned = replace(
                        owned,
                        marker_token=bytes(value ^ 0xFF for value in owned.marker_token),
                    )

                def assert_preserved() -> None:
                    self.assertTrue(owned.path.is_dir())
                    self.assertEqual(
                        sentinel.read_bytes(),
                        (case + " marker mutation\n").encode("ascii"),
                    )
                    if case == "missing":
                        self.assertFalse(os.path.lexists(marker))
                    elif case == "directory":
                        self.assertEqual(
                            (marker / "sentinel.bin").read_bytes(),
                            b"replacement marker directory\n",
                        )
                    elif symlink_target is not None:
                        self.assertTrue(marker.is_symlink())
                        self.assertEqual(
                            symlink_target.read_bytes(),
                            b"replacement marker symlink target\n",
                        )
                    elif case == "bytes":
                        self.assertEqual(marker.read_bytes(), changed_marker_bytes)
                    elif case == "mode":
                        self.assertEqual(stat.S_IMODE(os.lstat(marker).st_mode), 0o640)
                    else:
                        self.assertEqual(marker.read_bytes(), original_token)

                errors = checker.cleanup_compilation_root(cleanup_owned)
                self.assertEqual(errors, (checker.COMPILATION_ROOT_IDENTITY_ERROR,))
                assert_preserved()
                self.assert_owned_descriptors_closed(cleanup_owned, directory_fd, marker_fd)
                self.assertEqual(
                    checker.cleanup_compilation_root(cleanup_owned),
                    (checker.COMPILATION_ROOT_IDENTITY_ERROR,),
                )
                assert_preserved()
                shutil.rmtree(owned.path)

    def test_compilation_cleanup_removes_valid_owned_root_and_closes_descriptors(self) -> None:
        owned = checker.create_compilation_root()
        directory_fd = owned.directory_fd
        marker_fd = owned.marker_fd
        marker = owned.path / owned.marker_name
        compiled = owned.path / "compiled.pyc"
        compiled.write_bytes(b"compiled bytecode\n")
        marker_info = os.lstat(marker)
        self.assertEqual(
            owned.marker_name,
            ".ssn-to-bfo-owned-coms-compilation-root",
        )
        self.assertTrue(stat.S_ISREG(marker_info.st_mode))
        self.assertEqual(stat.S_IMODE(marker_info.st_mode), 0o600)
        self.assertEqual(len(owned.marker_token), 32)
        self.assertEqual(marker.read_bytes(), owned.marker_token)
        self.assertFalse(os.get_inheritable(directory_fd))
        self.assertFalse(os.get_inheritable(marker_fd))

        self.assertEqual(checker.cleanup_compilation_root(owned), ())

        self.assertFalse(owned.path.exists())
        self.assertFalse(marker.exists())
        self.assertFalse(compiled.exists())
        self.assert_owned_descriptors_closed(owned, directory_fd, marker_fd)
        self.assertEqual(checker.cleanup_compilation_root(owned), ())

    def test_compilation_descriptors_are_not_inherited_by_children(self) -> None:
        owned = checker.create_compilation_root()
        directory_fd = owned.directory_fd
        marker_fd = owned.marker_fd
        script = (
            "import os, sys\n"
            "for value in sys.argv[1:]:\n"
            "    try:\n"
            "        os.fstat(int(value))\n"
            "    except OSError:\n"
            "        continue\n"
            "    raise SystemExit(7)\n"
        )
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"

        child = subprocess.run(
            [sys.executable, "-B", "-c", script, str(directory_fd), str(marker_fd)],
            cwd=REPO_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
        self.assertFalse(os.get_inheritable(directory_fd))
        self.assertFalse(os.get_inheritable(marker_fd))
        self.assertEqual(checker.cleanup_compilation_root(owned), ())
        self.assert_owned_descriptors_closed(owned, directory_fd, marker_fd)

    def test_compile_and_cleanup_failures_remain_observable_and_restore_process_state(self) -> None:
        def cleanup_failure(owned):
            marker = owned.path / owned.marker_name
            marker.unlink()
            sentinel = owned.path / "cleanup-failure-sentinel.bin"
            sentinel.write_bytes(b"preserve after cleanup refusal\n")

        repository, paths = self.compile_fixture()
        original_state = sys.dont_write_bytecode
        for compile_fails in (False, True):
            roots: list[checker.OwnedCompilationRoot] = []
            descriptor_pairs: list[tuple[int, int]] = []
            corrupted = False
            original_create = checker.create_compilation_root

            def record_root():
                owned = original_create()
                roots.append(owned)
                descriptor_pairs.append((owned.directory_fd, owned.marker_fd))
                return owned

            def compile_result(source, *, cfile, doraise):
                nonlocal corrupted
                if not corrupted:
                    cleanup_failure(roots[-1])
                    corrupted = True
                if compile_fails:
                    raise OSError("injected compile failure")
                Path(cfile).write_bytes(b"compiled\n")
                return cfile

            with self.subTest(compile_fails=compile_fails), self.checker_patch(
                repository, paths
            ), mock.patch.object(
                checker, "create_compilation_root", side_effect=record_root
            ), mock.patch.object(
                checker.py_compile, "compile", side_effect=compile_result
            ), self.assertRaises(checker.CheckFailure) as raised:
                checker.compile_generator([])
            message = str(raised.exception)
            self.assertIn(checker.COMPILATION_ROOT_IDENTITY_ERROR, message)
            if compile_fails:
                self.assertIn("generator compile failed", message)
            self.assertEqual(sys.dont_write_bytecode, original_state)
            self.assertEqual(len(roots), 1)
            self.assertEqual(len(descriptor_pairs), 1)
            owned = roots[0]
            self.assertTrue(owned.path.is_dir())
            self.assertEqual(
                (owned.path / "cleanup-failure-sentinel.bin").read_bytes(),
                b"preserve after cleanup refusal\n",
            )
            self.assert_owned_descriptors_closed(owned, *descriptor_pairs[0])
            self.assertEqual(
                checker.cleanup_compilation_root(owned),
                (checker.COMPILATION_ROOT_IDENTITY_ERROR,),
            )
            shutil.rmtree(owned.path)


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
            "strict_bfo_mapping": self.root / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
            "cco_extension": self.root / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
        }

    @staticmethod
    def write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def generated_product_bytes(product_key: str) -> bytes:
        rows, stats = coms.read_workbook(REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx")
        processed = coms.validate_and_process_rows(rows, coms.Resolver(), stats)
        canonical_rows = tuple(
            coms.canonical_input_for_processed_row(row) for row in processed
        )
        audits = tuple(row.identity_audit for row in processed)
        disposition = checker.load_disposition_document(
            REPO_ROOT / "reports/coms-product-dispositions.json"
        )
        metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        selected = modular.select_product_axioms(
            product_key, canonical_rows, audits, disposition
        )
        builders = {
            "alignment_core": modular.build_alignment_core,
            "strict_bfo_mapping": modular.build_strict_bfo_mapping,
            "cco_extension": modular.build_cco_extension,
        }
        return builders[product_key](selected, metadata).serialized_bytes

    @classmethod
    def generated_cco_extension_bytes(cls) -> bytes:
        return cls.generated_product_bytes("cco_extension")

    @staticmethod

    @staticmethod
    def reordered_root_import_bytes(canonical: bytes) -> bytes:
        canonical_imports = (
            b"    owl:imports sampling:,\n"
            b"        ssn:,\n"
        )
        reordered_imports = (
            b"    owl:imports ssn:,\n"
            b"        sampling:,\n"
        )
        if canonical.count(canonical_imports) != 1:
            raise AssertionError("canonical integrated-root import block is missing or duplicated")
        return canonical.replace(canonical_imports, reordered_imports, 1)

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
        self.assertEqual(
            checker.MAINTAINED_OUTPUTS["strict_bfo_mapping"],
            REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
        )
        self.assertEqual(
            checker.MAINTAINED_OUTPUTS["cco_extension"],
            REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
        )

    def test_maintained_root_has_exact_metadata_and_logical_partition(self) -> None:
        maintained_path = REPO_ROOT / "SSN2BFO.ttl"
        metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        maintained_graph = Graph().parse(maintained_path, format="turtle")

        self.assertEqual(
            validate_emitted_ontology_metadata(
                maintained_graph,
                metadata,
                "integrated",
                checker.ROOT_ORDERED_IMPORTS,
            ),
            (),
        )
        self.assertEqual(len(maintained_graph), 1114)
        logical_graph = strip_emitted_ontology_header(
            maintained_graph,
            metadata,
            "integrated",
            checker.ROOT_ORDERED_IMPORTS,
        )
        self.assertEqual(len(logical_graph), 1102)
        self.assertNotEqual(
            hashlib.sha256(maintained_path.read_bytes()).hexdigest(),
            "fd6eadf1bcbd4bfc6dc06df58915116d8f909bc8c3238592b1f13509cec47d16",
        )

        rows, stats = coms.read_workbook(REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx")
        processed = coms.validate_and_process_rows(rows, coms.Resolver(), stats)
        regenerated_path = self.root / "regenerated-root.ttl"
        regenerated_graph = coms.generate_ontology(
            processed,
            regenerated_path,
            metadata,
            require_current_counts=True,
        )
        self.assertEqual(len(regenerated_graph), 1114)
        self.assertEqual(regenerated_path.read_bytes(), maintained_path.read_bytes())
        self.assertEqual(
            hashlib.sha256(maintained_path.read_bytes()).hexdigest(),
            "c31997d7e7b8c5e0bffd3f23a4597ab4be80786978462fefe800c4c7a5dc0c11",
        )
        governed_axiom_ids = {
            f"sha256:{axiom.sha256}"
            for item in processed
            for axiom in item.identity_audit.authoritative_axioms
        }
        self.assertEqual(set(modular._canonical_graph_axioms(regenerated_graph)), governed_axiom_ids)
        self.assertEqual(len(governed_axiom_ids), 103)

    def test_integrated_root_bytes_are_explicit_and_repeatable_without_rdflib_serialization(self) -> None:
        rows, stats = coms.read_workbook(REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx")
        processed = coms.validate_and_process_rows(rows, coms.Resolver(), stats)
        publication_metadata = load_metadata(
            REPO_ROOT / "config/publication-metadata.toml"
        )
        first = self.root / "root-first.ttl"
        second = self.root / "nested/root-second.ttl"
        with mock.patch.object(
            coms.Graph,
            "serialize",
            side_effect=AssertionError("RDFLib serialization must not determine maintained bytes"),
        ) as serializer:
            coms.generate_ontology(
                processed, first, publication_metadata, require_current_counts=True
            )
            coms.generate_ontology(
                processed, second, publication_metadata, require_current_counts=True
            )
        serializer.assert_not_called()
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(
            hashlib.sha256(first.read_bytes()).hexdigest(),
            "c31997d7e7b8c5e0bffd3f23a4597ab4be80786978462fefe800c4c7a5dc0c11",
        )
        self.assertNotIn(".serialize(", inspect.getsource(coms._root_turtle_bytes))
        self.assertNotIn(".serialize(", inspect.getsource(coms.generate_ontology))

    def test_integrated_root_is_fresh_process_stable_across_hash_seeds_and_paths(self) -> None:
        code = (
            "from pathlib import Path; import hashlib,sys; "
            "import generate_mapping_from_coms as g; "
            "from publication_metadata import load_metadata; "
            "rows,stats=g.read_workbook(Path('mappings/SSN2BFO-COMS.xlsx')); "
            "processed=g.validate_and_process_rows(rows,g.Resolver(),stats); "
            "output=Path(sys.argv[1]); "
            "g.generate_ontology(processed,output,load_metadata(Path('config/publication-metadata.toml')),require_current_counts=True); "
            "print(hashlib.sha256(output.read_bytes()).hexdigest())"
        )
        expected = "c31997d7e7b8c5e0bffd3f23a4597ab4be80786978462fefe800c4c7a5dc0c11"
        observed: dict[str, str] = {}
        for seed in ("0", "1", "42", "random"):
            with tempfile.TemporaryDirectory(prefix=f"root-seed-{seed}-") as directory:
                output = Path(directory) / "different/path/SSN2BFO.ttl"
                environment = dict(os.environ)
                environment.update(
                    {
                        "PYTHONPATH": str(REPO_ROOT / "tools"),
                        "PYTHONHASHSEED": seed,
                        "LC_ALL": "C",
                        "LANG": "C",
                    }
                )
                process = subprocess.run(
                    [sys.executable, "-c", code, str(output)],
                    cwd=REPO_ROOT,
                    env=environment,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                observed[seed] = process.stdout.strip()
        self.assertEqual(observed, {seed: expected for seed in observed})

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
        strict_bfo_hash = checker.sha256_file(outputs["strict_bfo_mapping"])
        cco_extension_hash = checker.sha256_file(outputs["cco_extension"])
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
                    "| maintained strict-BFO path | `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` |",
                    f"| strict-BFO Turtle SHA-256 | `{strict_bfo_hash}` |",
                    "| maintained CCO-extension path | `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` |",
                    f"| CCO-extension Turtle SHA-256 | `{cco_extension_hash}` |",
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
            product_order=checker.PRODUCT_ROLE_ORDER,
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
        strict_bfo_hash = checker.sha256_file(outputs["strict_bfo_mapping"])
        cco_extension_hash = checker.sha256_file(outputs["cco_extension"])
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
                    "| maintained strict-BFO path | `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` |",
                    f"| strict-BFO Turtle SHA-256 | `{strict_bfo_hash}` |",
                    "| maintained CCO-extension path | `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` |",
                    f"| CCO-extension Turtle SHA-256 | `{cco_extension_hash}` |",
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
            product_order=checker.PRODUCT_ROLE_ORDER,
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

    def test_stale_strict_bfo_hash_fails_check_only_without_rewriting_outputs(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"maintained-{name}\n")
        hashes = {name: checker.sha256_file(path) for name, path in outputs.items()}
        disposition_module_hash = checker.sha256_file(checker.DISPOSITION_MODULE)
        modular_products_module_hash = checker.sha256_file(checker.MODULAR_PRODUCTS_MODULE)
        publication_metadata_hash = checker.sha256_file(checker.PUBLICATION_METADATA)
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
                    f"| generated ontology SHA-256 | `{hashes['candidate']}` |",
                    "| maintained product-disposition path | `reports/coms-product-dispositions.json` |",
                    f"| product-disposition JSON SHA-256 | `{hashes['disposition_report']}` |",
                    "| maintained alignment-core path | `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` |",
                    f"| alignment-core Turtle SHA-256 | `{hashes['alignment_core']}` |",
                    "| maintained strict-BFO path | `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` |",
                    f"| strict-BFO Turtle SHA-256 | `{hashes['strict_bfo_mapping']}` |",
                    "| maintained CCO-extension path | `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` |",
                    f"| CCO-extension Turtle SHA-256 | `{hashes['cco_extension']}` |",
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
            product_order=checker.PRODUCT_ROLE_ORDER,
        )
        cache_dir = self.root / ".cache/coms"
        run_generator = mock.Mock()
        self.write(outputs["strict_bfo_mapping"], "modified maintained strict BFO mapping\n")
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
            self.assertEqual(errors, ["strict-BFO hash differs from the generated report"])
            self.assertNotIn("generated candidate hash differs from the generated report", errors)
            self.assertEqual(checker.main(["--check-only"]), 1)
        run_generator.assert_not_called()
        for path, content in expected.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(list(cache_dir.glob("run-*")), [])

    def test_stale_cco_extension_hash_fails_check_only_without_rewriting_outputs(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"maintained-{name}\n")
        hashes = {name: checker.sha256_file(path) for name, path in outputs.items()}
        disposition_module_hash = checker.sha256_file(checker.DISPOSITION_MODULE)
        modular_products_module_hash = checker.sha256_file(checker.MODULAR_PRODUCTS_MODULE)
        publication_metadata_hash = checker.sha256_file(checker.PUBLICATION_METADATA)
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
                    f"| generated ontology SHA-256 | `{hashes['candidate']}` |",
                    "| maintained product-disposition path | `reports/coms-product-dispositions.json` |",
                    f"| product-disposition JSON SHA-256 | `{hashes['disposition_report']}` |",
                    "| maintained alignment-core path | `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` |",
                    f"| alignment-core Turtle SHA-256 | `{hashes['alignment_core']}` |",
                    "| maintained strict-BFO path | `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` |",
                    f"| strict-BFO Turtle SHA-256 | `{hashes['strict_bfo_mapping']}` |",
                    "| maintained CCO-extension path | `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` |",
                    f"| CCO-extension Turtle SHA-256 | `{hashes['cco_extension']}` |",
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
            product_order=checker.PRODUCT_ROLE_ORDER,
        )
        self.write(outputs["cco_extension"], "modified maintained CCO extension\n")
        expected = {path: path.read_bytes() for path in outputs.values()}
        cache_dir = self.root / ".cache/coms"
        run_generator = mock.Mock()
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
            self.assertEqual(errors, ["CCO-extension hash differs from the generated report"])
            self.assertNotIn("generated candidate hash differs from the generated report", errors)
            self.assertEqual(checker.main(["--check-only"]), 1)
        run_generator.assert_not_called()
        for path, content in expected.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(list(cache_dir.glob("run-*")), [])


    def test_publication_metadata_source_hash_participates_in_freshness(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            source = checker.MAINTAINED_OUTPUTS[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(source.read_bytes())
        before = {path: path.read_bytes() for path in outputs.values()}
        changed_metadata = self.root / "config/publication-metadata.toml"
        changed_metadata.parent.mkdir(parents=True, exist_ok=True)
        changed_metadata.write_text(
            checker.PUBLICATION_METADATA.read_text(encoding="utf-8").replace(
                'project_title = "SSN-to-BFO"',
                'project_title = "SSN-to-BFO metadata freshness probe"',
                1,
            ),
            encoding="utf-8",
        )
        workbook_hash = checker.sha256_file(checker.WORKBOOK)
        generator_hash = checker.sha256_file(checker.GENERATOR)
        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "PUBLICATION_METADATA", changed_metadata),
        ):
            errors = checker.freshness_errors(workbook_hash, generator_hash)
        self.assertIn("publication metadata hash differs from the generated report", errors)
        self.assertIn("product-disposition publication_metadata_sha256 is stale", errors)
        self.assertEqual({path: path.read_bytes() for path in outputs.values()}, before)

    def test_first_successful_metadata_migration_replaces_all_four_ttls_together(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"pre-metadata-{name}\n")
        before = {path: path.read_bytes() for path in outputs.values()}
        generated_ttls = {
            "candidate": (REPO_ROOT / "SSN2BFO.ttl").read_bytes(),
            "alignment_core": self.generated_product_bytes("alignment_core"),
            "strict_bfo_mapping": self.generated_product_bytes("strict_bfo_mapping"),
            "cco_extension": self.generated_cco_extension_bytes(),
        }
        metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        expected_imports = {
            "candidate": checker.ROOT_ORDERED_IMPORTS,
            "alignment_core": (),
            "strict_bfo_mapping": (
                "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core",
            ),
            "cco_extension": (
                "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping",
            ),
        }
        product_keys = {
            "candidate": "integrated",
            "alignment_core": "alignment_core",
            "strict_bfo_mapping": "strict_bfo_mapping",
            "cco_extension": "cco_extension",
        }
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []
        validated = False

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            transaction_dirs.append(paths["candidate"].parents[1])
            for name in outputs:
                paths[name].parent.mkdir(parents=True, exist_ok=True)
                paths[name].write_bytes(
                    generated_ttls.get(name, f"generated-{name}\n".encode("utf-8"))
                )
            self.write(paths["summary"], "{}\n")

        def validate_metadata(paths: dict[str, Path], *_args, **_kwargs):
            nonlocal validated
            for name, product_key in product_keys.items():
                graph = Graph().parse(paths[name], format="turtle")
                checker.validate_product_metadata(
                    graph,
                    metadata,
                    product_key,
                    expected_imports[name],
                )
            validated = True
            return {}

        production_replace = checker.replace_outputs_atomically

        def observe_replace(paths: dict[str, Path], transaction_dir: Path, log: list[str]) -> None:
            self.assertTrue(validated)
            self.assertEqual(
                {path: path.read_bytes() for path in outputs.values()}, before
            )
            production_replace(paths, transaction_dir, log)

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=["metadata migration"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "validate_temporary_outputs", side_effect=validate_metadata),
            mock.patch.object(checker, "git_diff_check"),
            mock.patch.object(checker, "output_differences", return_value=list(outputs)),
            mock.patch.object(checker, "replace_outputs_atomically", side_effect=observe_replace),
            mock.patch.object(checker, "record_success"),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 0)
        for name, content in generated_ttls.items():
            self.assertEqual(outputs[name].read_bytes(), content)
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())

    def test_checker_rejects_noncanonical_headers_for_all_four_candidates(self) -> None:
        metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        canonical = {
            "candidate": (REPO_ROOT / "SSN2BFO.ttl").read_bytes(),
            "alignment_core": self.generated_product_bytes("alignment_core"),
            "strict_bfo_mapping": self.generated_product_bytes("strict_bfo_mapping"),
            "cco_extension": self.generated_cco_extension_bytes(),
        }
        product_keys = {
            output_name: product_key
            for output_name, product_key, *_rest in checker.SERIALIZED_HEADER_PRODUCTS
        }
        paths = {
            name: self.root / "serialized-header-candidates" / f"{name}.ttl"
            for name in canonical
        }

        for mutated_name in canonical:
            with self.subTest(product=product_keys[mutated_name]):
                for name, content in canonical.items():
                    paths[name].parent.mkdir(parents=True, exist_ok=True)
                    paths[name].write_bytes(content)
                lines = canonical[mutated_name].splitlines()
                label_index = next(
                    index
                    for index, line in enumerate(lines)
                    if line.startswith(b"    rdfs:label ")
                )
                description_index = next(
                    index
                    for index, line in enumerate(lines)
                    if line.startswith(b"    dcterms:description ")
                )
                lines[label_index], lines[description_index] = (
                    lines[description_index],
                    lines[label_index],
                )
                mutated = b"\n".join(lines) + b"\n"
                paths[mutated_name].write_bytes(mutated)
                self.assertTrue(
                    isomorphic(
                        Graph().parse(data=canonical[mutated_name].decode(), format="turtle"),
                        Graph().parse(data=mutated.decode(), format="turtle"),
                    )
                )
                with self.assertRaises(checker.CheckFailure) as raised:
                    checker.validate_candidate_serialized_headers(paths, metadata)
                self.assertIn("NONCANONICAL_ONTOLOGY_HEADER", str(raised.exception))
                self.assertIn(product_keys[mutated_name], str(raised.exception))

    def test_checker_uses_generator_root_import_order_with_matching_turtle_terms(self) -> None:
        expected_imports = (
            "http://www.w3.org/ns/sosa/sampling/",
            "http://www.w3.org/ns/ssn/",
            "http://www.w3.org/ns/ssn/systems/",
            "https://www.commoncoreontologies.org/2024-11-06/CommonCoreOntologiesMerged",
        )
        self.assertIs(checker.ROOT_ORDERED_IMPORTS, coms.ROOT_ORDERED_IMPORTS)
        self.assertFalse(hasattr(checker, "ROOT_IMPORTS"))
        self.assertEqual(coms.ROOT_ORDERED_IMPORTS, expected_imports)
        self.assertEqual(len(coms.ROOT_ORDERED_IMPORTS), 4)
        self.assertEqual(len(coms.ROOT_IMPORT_TURTLE_TERMS), 4)

        integrated = next(
            value
            for value in checker.SERIALIZED_HEADER_PRODUCTS
            if value[1] == "integrated"
        )
        self.assertIs(integrated[2], coms.ROOT_ORDERED_IMPORTS)
        self.assertIs(integrated[5], coms.ROOT_IMPORT_TURTLE_TERMS)

        prefix_block = "\n".join(
            f"@prefix {prefix}: <{namespace}> ."
            for prefix, namespace in coms.ROOT_PREFIXES
        )
        for expected_iri, turtle_term in zip(
            coms.ROOT_ORDERED_IMPORTS,
            coms.ROOT_IMPORT_TURTLE_TERMS,
            strict=True,
        ):
            with self.subTest(turtle_term=turtle_term):
                graph = Graph().parse(
                    data=(
                        f"{prefix_block}\n"
                        f"<urn:test:ontology> owl:imports {turtle_term} .\n"
                    ),
                    format="turtle",
                )
                self.assertEqual(
                    tuple(str(value) for value in graph.objects(None, OWL.imports)),
                    (expected_iri,),
                )

    def test_checker_rejects_reordered_integrated_root_imports(self) -> None:
        metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        canonical = {
            "candidate": (REPO_ROOT / "SSN2BFO.ttl").read_bytes(),
            "alignment_core": self.generated_product_bytes("alignment_core"),
            "strict_bfo_mapping": self.generated_product_bytes("strict_bfo_mapping"),
            "cco_extension": self.generated_cco_extension_bytes(),
        }
        paths = {
            name: self.root / "reordered-root-imports" / f"{name}.ttl"
            for name in canonical
        }
        for name, content in canonical.items():
            paths[name].parent.mkdir(parents=True, exist_ok=True)
            paths[name].write_bytes(content)

        reordered = self.reordered_root_import_bytes(canonical["candidate"])
        paths["candidate"].write_bytes(reordered)
        self.assertTrue(
            isomorphic(
                Graph().parse(data=canonical["candidate"].decode(), format="turtle"),
                Graph().parse(data=reordered.decode(), format="turtle"),
            )
        )
        with self.assertRaises(checker.CheckFailure) as raised:
            checker.validate_candidate_serialized_headers(paths, metadata)
        self.assertIn("NONCANONICAL_ONTOLOGY_HEADER", str(raised.exception))
        self.assertIn("integrated", str(raised.exception))

    def test_reordered_integrated_root_imports_block_all_nine_outputs(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(checker.MAINTAINED_OUTPUTS[name].read_bytes())
        before = {path: path.read_bytes() for path in outputs.values()}
        before_mtimes = {path: path.stat().st_mtime_ns for path in outputs.values()}
        cache_dir = self.root / ".cache/coms-reordered-root-imports"
        transaction_dirs: list[Path] = []
        production_run_generator = checker.run_generator
        production_validate = checker.validate_temporary_outputs
        workbook_hash = checker.sha256_file(checker.WORKBOOK)
        generator_hash = checker.sha256_file(checker.GENERATOR)

        def generate_then_reorder_imports(
            paths: dict[str, Path], log: list[str]
        ) -> None:
            production_run_generator(paths, log)
            transaction_dirs.append(paths["candidate"].parents[1])
            canonical = paths["candidate"].read_bytes()
            reordered = self.reordered_root_import_bytes(canonical)
            self.assertTrue(
                isomorphic(
                    Graph().parse(data=canonical.decode(), format="turtle"),
                    Graph().parse(data=reordered.decode(), format="turtle"),
                )
            )
            old_hash = hashlib.sha256(canonical).hexdigest()
            new_hash = hashlib.sha256(reordered).hexdigest()
            paths["candidate"].write_bytes(reordered)
            summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
            summary["generated_candidate_sha256"] = new_hash
            paths["summary"].write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            report = paths["generation_report"].read_text(encoding="utf-8")
            self.assertIn(old_hash, report)
            paths["generation_report"].write_text(
                report.replace(old_hash, new_hash),
                encoding="utf-8",
            )

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value=workbook_hash),
            mock.patch.object(checker, "compile_generator", return_value=generator_hash),
            mock.patch.object(checker, "freshness_errors", return_value=["metadata migration"]),
            mock.patch.object(
                checker, "run_generator", side_effect=generate_then_reorder_imports
            ),
            mock.patch.object(checker, "replace_outputs_atomically") as replace,
        ):
            self.assertIs(checker.validate_temporary_outputs, production_validate)
            self.assertEqual(checker.main([]), 1)
        replace.assert_not_called()
        self.assertEqual(
            {path: path.read_bytes() for path in outputs.values()},
            before,
        )
        self.assertEqual(
            {path: path.stat().st_mtime_ns for path in outputs.values()},
            before_mtimes,
        )
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())
        self.assertEqual(list(cache_dir.glob("run-*")), [])
        failure_log = (cache_dir / "last-failure.log").read_text(encoding="utf-8")
        self.assertIn("NONCANONICAL_ONTOLOGY_HEADER", failure_log)

    def test_reordered_header_blocks_all_nine_outputs_via_production_validation(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(checker.MAINTAINED_OUTPUTS[name].read_bytes())
        before = {path: path.read_bytes() for path in outputs.values()}
        before_mtimes = {path: path.stat().st_mtime_ns for path in outputs.values()}
        cache_dir = self.root / ".cache/coms-noncanonical-header"
        transaction_dirs: list[Path] = []
        production_run_generator = checker.run_generator
        production_validate = checker.validate_temporary_outputs
        workbook_hash = checker.sha256_file(checker.WORKBOOK)
        generator_hash = checker.sha256_file(checker.GENERATOR)

        def generate_then_reorder_header(
            paths: dict[str, Path], log: list[str]
        ) -> None:
            production_run_generator(paths, log)
            transaction_dirs.append(paths["candidate"].parents[1])
            canonical = paths["alignment_core"].read_bytes()
            lines = canonical.splitlines()
            label_index = next(
                index
                for index, line in enumerate(lines)
                if line.startswith(b"    rdfs:label ")
            )
            description_index = next(
                index
                for index, line in enumerate(lines)
                if line.startswith(b"    dcterms:description ")
            )
            lines[label_index], lines[description_index] = (
                lines[description_index],
                lines[label_index],
            )
            reordered = b"\n".join(lines) + b"\n"
            self.assertTrue(
                isomorphic(
                    Graph().parse(data=canonical.decode(), format="turtle"),
                    Graph().parse(data=reordered.decode(), format="turtle"),
                )
            )
            old_hash = hashlib.sha256(canonical).hexdigest()
            new_hash = hashlib.sha256(reordered).hexdigest()
            paths["alignment_core"].write_bytes(reordered)
            summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
            summary["alignment_core_sha256"] = new_hash
            paths["summary"].write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            report = paths["generation_report"].read_text(encoding="utf-8")
            self.assertIn(old_hash, report)
            paths["generation_report"].write_text(
                report.replace(old_hash, new_hash),
                encoding="utf-8",
            )

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value=workbook_hash),
            mock.patch.object(checker, "compile_generator", return_value=generator_hash),
            mock.patch.object(checker, "freshness_errors", return_value=["metadata migration"]),
            mock.patch.object(
                checker, "run_generator", side_effect=generate_then_reorder_header
            ),
            mock.patch.object(checker, "replace_outputs_atomically") as replace,
        ):
            self.assertIs(checker.validate_temporary_outputs, production_validate)
            self.assertEqual(checker.main([]), 1)
        replace.assert_not_called()
        self.assertEqual(
            {path: path.read_bytes() for path in outputs.values()},
            before,
        )
        self.assertEqual(
            {path: path.stat().st_mtime_ns for path in outputs.values()},
            before_mtimes,
        )
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())
        self.assertEqual(list(cache_dir.glob("run-*")), [])
        failure_log = (cache_dir / "last-failure.log").read_text(encoding="utf-8")
        self.assertIn("NONCANONICAL_ONTOLOGY_HEADER", failure_log)


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
        alignment_core_bytes = self.generated_product_bytes("alignment_core")
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
            self.assertEqual(len(graph), 61)
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
        self.assertEqual(len(final_graph), 61)
        self.assertTrue(all(path.is_file() for path in outputs.values()))
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())
        self.assertEqual(list(cache_dir.glob("run-*")), [])

    def test_first_successful_update_creates_initially_absent_strict_bfo_mapping(self) -> None:
        outputs = self.maintained_outputs()
        existing = {
            name: path for name, path in outputs.items() if name != "strict_bfo_mapping"
        }
        for name, path in existing.items():
            self.write(path, f"old-{name}\n")
        self.assertFalse(outputs["strict_bfo_mapping"].exists())
        expected_generated = {
            name: f"new-{name}\n".encode("utf-8") for name in existing
        }
        strict_bytes = self.generated_product_bytes("strict_bfo_mapping")
        ontology_iri = URIRef(
            "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping"
        )
        alignment_iri = URIRef(
            "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core"
        )
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []
        validation_complete = False

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            self.assertFalse(outputs["strict_bfo_mapping"].exists())
            transaction_dirs.append(paths["candidate"].parents[1])
            for name, content in expected_generated.items():
                paths[name].parent.mkdir(parents=True, exist_ok=True)
                paths[name].write_bytes(content)
            paths["strict_bfo_mapping"].parent.mkdir(parents=True, exist_ok=True)
            paths["strict_bfo_mapping"].write_bytes(strict_bytes)
            self.write(paths["summary"], "{}\n")

        def fake_validate(paths: dict[str, Path], *_args, **_kwargs):
            nonlocal validation_complete
            self.assertFalse(outputs["strict_bfo_mapping"].exists())
            graph = coms.Graph().parse(paths["strict_bfo_mapping"], format="turtle")
            self.assertEqual(set(graph.subjects(RDF.type, OWL.Ontology)), {ontology_iri})
            self.assertEqual(
                set(graph.triples((None, OWL.imports, None))),
                {(ontology_iri, OWL.imports, alignment_iri)},
            )
            self.assertEqual(len(graph), 134)
            validation_complete = True
            return {}

        production_replace = checker.replace_outputs_atomically

        def observe_replace(paths: dict[str, Path], transaction_dir: Path, log: list[str]) -> None:
            self.assertTrue(validation_complete)
            self.assertFalse(outputs["strict_bfo_mapping"].exists())
            production_replace(paths, transaction_dir, log)
            self.assertTrue(outputs["strict_bfo_mapping"].exists())

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=["missing strict BFO mapping"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "validate_temporary_outputs", side_effect=fake_validate),
            mock.patch.object(checker, "git_diff_check"),
            mock.patch.object(checker, "output_differences", return_value=list(outputs)),
            mock.patch.object(checker, "replace_outputs_atomically", side_effect=observe_replace),
            mock.patch.object(checker, "record_success"),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 0)
        for name, content in expected_generated.items():
            self.assertEqual(outputs[name].read_bytes(), content)
        self.assertEqual(outputs["strict_bfo_mapping"].read_bytes(), strict_bytes)
        self.assertTrue(all(path.is_file() for path in outputs.values()))
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())
        self.assertEqual(list(cache_dir.glob("run-*")), [])

    def test_first_successful_update_creates_initially_absent_cco_extension(self) -> None:
        outputs = self.maintained_outputs()
        existing = {name: path for name, path in outputs.items() if name != "cco_extension"}
        for name, path in existing.items():
            self.write(path, f"old-{name}\n")
        self.assertFalse(outputs["cco_extension"].exists())
        expected_generated = {
            name: f"new-{name}\n".encode("utf-8") for name in existing
        }
        cco_bytes = self.generated_cco_extension_bytes()
        ontology_iri = URIRef(
            "http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension"
        )
        strict_iri = URIRef(
            "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping"
        )
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []
        validation_complete = False

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            self.assertFalse(outputs["cco_extension"].exists())
            transaction_dirs.append(paths["candidate"].parents[1])
            for name, content in expected_generated.items():
                paths[name].parent.mkdir(parents=True, exist_ok=True)
                paths[name].write_bytes(content)
            paths["cco_extension"].parent.mkdir(parents=True, exist_ok=True)
            paths["cco_extension"].write_bytes(cco_bytes)
            self.write(paths["summary"], "{}\n")

        def fake_validate(paths: dict[str, Path], *_args, **_kwargs):
            nonlocal validation_complete
            self.assertFalse(outputs["cco_extension"].exists())
            graph = coms.Graph().parse(paths["cco_extension"], format="turtle")
            self.assertEqual(set(graph.subjects(RDF.type, OWL.Ontology)), {ontology_iri})
            self.assertEqual(
                set(graph.triples((None, OWL.imports, None))),
                {(ontology_iri, OWL.imports, strict_iri)},
            )
            self.assertEqual(len(graph), 933)
            validation_complete = True
            return {}

        production_replace = checker.replace_outputs_atomically

        def observe_replace(paths: dict[str, Path], transaction_dir: Path, log: list[str]) -> None:
            self.assertTrue(validation_complete)
            self.assertFalse(outputs["cco_extension"].exists())
            production_replace(paths, transaction_dir, log)
            self.assertTrue(outputs["cco_extension"].exists())

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "CACHE_DIR", cache_dir),
            mock.patch.object(checker, "LAST_SUCCESS", cache_dir / "last-success.json"),
            mock.patch.object(checker, "LAST_FAILURE", cache_dir / "last-failure.log"),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
            mock.patch.object(checker, "verify_workbook", return_value="workbook-hash"),
            mock.patch.object(checker, "compile_generator", return_value="generator-hash"),
            mock.patch.object(checker, "freshness_errors", return_value=["missing CCO extension"]),
            mock.patch.object(checker, "run_generator", side_effect=fake_run_generator),
            mock.patch.object(checker, "validate_temporary_outputs", side_effect=fake_validate),
            mock.patch.object(checker, "git_diff_check"),
            mock.patch.object(checker, "output_differences", return_value=list(outputs)),
            mock.patch.object(checker, "replace_outputs_atomically", side_effect=observe_replace),
            mock.patch.object(checker, "record_success"),
            mock.patch.object(checker, "write_failure_log"),
        ):
            self.assertEqual(checker.main([]), 0)
        for name, content in expected_generated.items():
            self.assertEqual(outputs[name].read_bytes(), content)
        self.assertEqual(outputs["cco_extension"].read_bytes(), cco_bytes)
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

    def test_check_only_preserves_all_nine_outputs_and_workbook(self) -> None:
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

    def test_rollback_removes_new_strict_bfo_when_it_was_initially_absent(self) -> None:
        outputs = self.maintained_outputs()
        existing = {
            name: path for name, path in outputs.items() if name != "strict_bfo_mapping"
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
        self.assertFalse(outputs["strict_bfo_mapping"].exists())
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())


    def test_rollback_removes_new_cco_extension_when_it_was_initially_absent(self) -> None:
        outputs = self.maintained_outputs()
        existing = {name: path for name, path in outputs.items() if name != "cco_extension"}
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
        self.assertFalse(outputs["cco_extension"].exists())
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
        failures: list[str] = []
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
            observed_candidates.append(paths["alignment_core"].read_bytes())
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
                            "ontology_declaration_triple_count": 1,
                            "import_triple_count": 0,
                            "metadata_annotation_count": 7,
                            "total_triple_count": 61,
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
            mock.patch.object(
                checker,
                "write_failure_log",
                side_effect=lambda _mode, _log, exc: failures.append(str(exc)),
            ),
        ):
            self.assertEqual(checker.main([]), 1)

        self.assertEqual(len(observed_candidates), 1)
        self.assertIn(b"[", observed_candidates[0])
        self.assertIn("TURTLE_PARSE", failures[0])
        self.assertIn("products.alignment_core.serialized_ontology", failures[0])
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())

    def test_written_malformed_strict_bfo_fails_before_replacement(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"old-{name}\n")
        before = {path: path.read_bytes() for path in outputs.values()}
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []
        observed_candidates: list[bytes] = []
        failures: list[str] = []
        disposition_source = REPO_ROOT / "reports/coms-product-dispositions.json"
        disposition = checker.load_disposition_document(disposition_source)
        disposition_bytes = disposition_source.read_bytes()
        alignment_bytes = self.generated_product_bytes("alignment_core")
        workbook_hash = disposition.input_hashes.workbook_sha256
        generator_hash = disposition.input_hashes.generator_sha256

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            transaction_dirs.append(paths["candidate"].parents[1])
            for name in outputs:
                self.write(paths[name], f"temporary-{name}\n")
            paths["disposition_report"].write_bytes(disposition_bytes)
            paths["alignment_core"].write_bytes(alignment_bytes)
            malformed_strict = b"@prefix owl: <http://www.w3.org/2002/07/owl#> .\n[\n"
            paths["strict_bfo_mapping"].write_bytes(malformed_strict)
            observed_candidates.append(paths["strict_bfo_mapping"].read_bytes())
            self.write(
                paths["summary"],
                json.dumps(
                    {
                        "status": "PASS",
                        "workbook_sha256": workbook_hash,
                        "generator_sha256": generator_hash,
                        "product_disposition_report_sha256": checker.sha256_file(paths["disposition_report"]),
                        "product_dispositions": {
                            field: getattr(disposition.summary, field)
                            for field in disposition.summary.__dataclass_fields__
                        },
                        "alignment_core_sha256": checker.sha256_file(paths["alignment_core"]),
                        "modular_products_module_sha256": checker.sha256_file(checker.MODULAR_PRODUCTS_MODULE),
                        "alignment_core": {
                            "product_key": "alignment_core",
                            "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core",
                            "governed_axiom_count": 29,
                            "logical_triple_count": 53,
                            "ontology_declaration_triple_count": 1,
                            "import_triple_count": 0,
                            "metadata_annotation_count": 7,
                            "total_triple_count": 61,
                            "domain_axiom_count": 15,
                            "range_axiom_count": 14,
                            "named_target_count": 26,
                            "union_target_count": 3,
                            "hermit_return_code": 0,
                            "hermit_result": "PASS",
                            "named_unsat_count": 0,
                        },
                        "strict_bfo_mapping_sha256": checker.sha256_file(paths["strict_bfo_mapping"]),
                        "strict_bfo_mapping": {
                            "product_key": "strict_bfo_mapping",
                            "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping",
                            "governed_axiom_count": 19,
                            "logical_triple_count": 125,
                            "ontology_declaration_triple_count": 1,
                            "import_triple_count": 1,
                            "metadata_annotation_count": 7,
                            "total_triple_count": 134,
                            "subclass_axiom_count": 3,
                            "equivalent_class_axiom_count": 3,
                            "direct_subproperty_axiom_count": 9,
                            "property_chain_axiom_count": 2,
                            "domain_axiom_count": 1,
                            "range_axiom_count": 1,
                            "union_expression_count": 6,
                            "intersection_expression_count": 6,
                            "existential_restriction_count": 6,
                            "rdf_list_count": 14,
                            "project_closure_governed_axiom_count": 48,
                            "project_graph_triple_count": 195,
                            "local_project_graph_triple_count": 194,
                            "hermit_return_code": 0,
                            "hermit_result": "PASS",
                            "closure_triple_count": 14988,
                            "named_unsat_count": 0,
                        },
                    }
                )
                + "\n",
            )

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
            mock.patch.object(
                checker,
                "write_failure_log",
                side_effect=lambda _mode, _log, exc: failures.append(str(exc)),
            ),
        ):
            self.assertEqual(checker.main([]), 1)
        self.assertEqual(len(observed_candidates), 1)
        self.assertIn(b"[", observed_candidates[0])
        self.assertIn("TURTLE_PARSE", failures[0])
        self.assertIn("products.strict_bfo_mapping.serialized_ontology", failures[0])
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(len(transaction_dirs), 1)
        self.assertFalse(transaction_dirs[0].exists())


    def test_written_malformed_cco_extension_fails_before_replacement(self) -> None:
        outputs = self.maintained_outputs()
        for name, path in outputs.items():
            self.write(path, f"old-{name}\n")
        before = {path: path.read_bytes() for path in outputs.values()}
        cache_dir = self.root / ".cache/coms"
        transaction_dirs: list[Path] = []
        observed_candidates: list[bytes] = []
        failures: list[str] = []
        disposition_source = REPO_ROOT / "reports/coms-product-dispositions.json"
        disposition = checker.load_disposition_document(disposition_source)
        disposition_bytes = disposition_source.read_bytes()
        alignment_bytes = self.generated_product_bytes("alignment_core")
        strict_bytes = self.generated_product_bytes("strict_bfo_mapping")
        workbook_hash = disposition.input_hashes.workbook_sha256
        generator_hash = disposition.input_hashes.generator_sha256

        def fake_run_generator(paths: dict[str, Path], _log: list[str]) -> None:
            transaction_dirs.append(paths["candidate"].parents[1])
            for name in outputs:
                self.write(paths[name], f"temporary-{name}\n")
            paths["disposition_report"].write_bytes(disposition_bytes)
            paths["alignment_core"].write_bytes(alignment_bytes)
            paths["strict_bfo_mapping"].write_bytes(strict_bytes)
            malformed_cco = b"@prefix owl: <http://www.w3.org/2002/07/owl#> .\n[\n"
            paths["cco_extension"].write_bytes(malformed_cco)
            observed_candidates.append(paths["cco_extension"].read_bytes())
            summary = {
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
                "alignment_core_sha256": checker.sha256_file(paths["alignment_core"]),
                "modular_products_module_sha256": checker.sha256_file(
                    checker.MODULAR_PRODUCTS_MODULE
                ),
                "alignment_core": {
                    "product_key": "alignment_core",
                    "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core",
                    "governed_axiom_count": 29,
                    "logical_triple_count": 53,
                    "ontology_declaration_triple_count": 1,
                    "import_triple_count": 0,
                    "metadata_annotation_count": 7,
                    "total_triple_count": 61,
                    "domain_axiom_count": 15,
                    "range_axiom_count": 14,
                    "named_target_count": 26,
                    "union_target_count": 3,
                    "hermit_return_code": 0,
                    "hermit_result": "PASS",
                    "named_unsat_count": 0,
                },
                "strict_bfo_mapping_sha256": checker.sha256_file(
                    paths["strict_bfo_mapping"]
                ),
                "strict_bfo_mapping": {
                    "product_key": "strict_bfo_mapping",
                    "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping",
                    "governed_axiom_count": 19,
                    "logical_triple_count": 125,
                    "ontology_declaration_triple_count": 1,
                    "import_triple_count": 1,
                    "metadata_annotation_count": 7,
                    "total_triple_count": 134,
                    "subclass_axiom_count": 3,
                    "equivalent_class_axiom_count": 3,
                    "direct_subproperty_axiom_count": 9,
                    "property_chain_axiom_count": 2,
                    "domain_axiom_count": 1,
                    "range_axiom_count": 1,
                    "union_expression_count": 6,
                    "intersection_expression_count": 6,
                    "existential_restriction_count": 6,
                    "rdf_list_count": 14,
                    "project_closure_governed_axiom_count": 48,
                    "project_graph_triple_count": 195,
                    "local_project_graph_triple_count": 194,
                    "hermit_return_code": 0,
                    "hermit_result": "PASS",
                    "closure_triple_count": 14988,
                    "named_unsat_count": 0,
                },
                "cco_extension_sha256": checker.sha256_file(paths["cco_extension"]),
                "cco_extension": {
                    "product_key": "cco_extension",
                    "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension",
                    "governed_axiom_count": 55,
                    "cco_bearing_axiom_count": 25,
                    "mixed_bfo_cco_axiom_count": 30,
                    "logical_triple_count": 924,
                    "ontology_declaration_triple_count": 1,
                    "import_triple_count": 1,
                    "metadata_annotation_count": 7,
                    "total_triple_count": 933,
                    "subclass_axiom_count": 31,
                    "equivalent_class_axiom_count": 7,
                    "direct_subproperty_axiom_count": 16,
                    "property_chain_axiom_count": 1,
                    "union_expression_count": 7,
                    "intersection_expression_count": 86,
                    "existential_restriction_count": 95,
                    "rdf_list_count": 94,
                    "project_closure_governed_axiom_count": 103,
                    "project_graph_triple_count": 1128,
                    "local_project_graph_triple_count": 1126,
                    "hermit_return_code": 0,
                    "hermit_result": "PASS",
                    "closure_triple_count": 15920,
                    "named_unsat_count": 0,
                },
            }
            self.write(paths["summary"], json.dumps(summary) + "\n")

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
            mock.patch.object(
                checker,
                "write_failure_log",
                side_effect=lambda _mode, _log, exc: failures.append(str(exc)),
            ),
        ):
            self.assertEqual(checker.main([]), 1)
        self.assertEqual(len(observed_candidates), 1)
        self.assertIn(b"[", observed_candidates[0])
        self.assertIn("TURTLE_PARSE", failures[0])
        self.assertIn("products.cco_extension.serialized_ontology", failures[0])
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
