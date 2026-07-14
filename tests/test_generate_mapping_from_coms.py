#!/usr/bin/env python3
"""Focused tests for COMS generation, coverage, and authority migration."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import openpyxl
from rdflib import BNode, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_coms_mapping as checker  # noqa: E402
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
        self.write(
            outputs["generation_report"],
            "\n".join(
                [
                    "| workbook SHA-256 | `workbook-hash` |",
                    "| generator SHA-256 | `generator-hash` |",
                    "| generation timestamp (UTC) | `2026-01-01T00:00:00+00:00` |",
                    "| maintained ontology path | `SSN2BFO.ttl` |",
                    f"| generated ontology SHA-256 | `{candidate_hash}` |",
                ]
            ),
        )

        with (
            mock.patch.object(checker, "REPO_ROOT", self.root),
            mock.patch.object(checker, "MAINTAINED_OUTPUTS", outputs),
        ):
            self.assertEqual(checker.freshness_errors("workbook-hash", "generator-hash"), [])
            self.write(outputs["candidate"], "changed root ontology\n")
            self.assertIn(
                "generated candidate hash differs from the generated report",
                checker.freshness_errors("workbook-hash", "generator-hash"),
            )

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
