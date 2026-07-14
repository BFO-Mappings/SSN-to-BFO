#!/usr/bin/env python3
"""Focused tests for COMS domain/range spreadsheet rows."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import openpyxl
from rdflib import BNode, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import generate_mapping_from_coms as coms  # noqa: E402


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

    def synthetic_workbook(self, rows: list[tuple[str, str, str]]) -> Path:
        path = self.root / "synthetic-coms.xlsx"
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Synthetic"
        worksheet.append(list(coms.REQUIRED_COLUMNS))
        for subject, predicate, target in rows:
            worksheet.append([subject, predicate, target, "synthetic test row"])
        workbook.save(path)
        workbook.close()
        return path

    def process(self, rows: list[tuple[str, str, str]]):
        workbook_path = self.synthetic_workbook(rows)
        workbook_rows, stats = coms.read_workbook(workbook_path)
        processed = coms.validate_and_process_rows(workbook_rows, coms.Resolver(), stats)
        return processed, stats

    def generate(self, rows: list[tuple[str, str, str]]):
        processed, stats = self.process(rows)
        output = self.root / "candidate.ttl"
        graph = coms.generate_ontology(processed, output)
        return graph, processed, stats

    def assert_generation_error(
        self,
        rows: list[tuple[str, str, str]],
        *expected_fragments: str,
    ) -> None:
        workbook_path = self.synthetic_workbook(rows)
        workbook_rows, stats = coms.read_workbook(workbook_path)
        with self.assertRaises(coms.GenerationError) as raised:
            coms.validate_and_process_rows(workbook_rows, coms.Resolver(), stats)
        message = str(raised.exception)
        for fragment in expected_fragments:
            self.assertIn(fragment, message)

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


if __name__ == "__main__":
    unittest.main()
