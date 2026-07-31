#!/usr/bin/env python3
"""Focused tests for the governed SOSA-next COMS checker."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_sosa_next_mapping as checker  # noqa: E402


GOVERNED_INPUTS = (
    REPO_ROOT / "mappings/SOSA-next-to-BFO-COMS.xlsx",
    REPO_ROOT / "src/sosa-next/catalog-v001.xml",
    *checker.SOURCE_FILES,
)

CURRENT_PRODUCTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)

DATATYPE_DEFERRAL = (
    "Datatype-property mapping deferred pending repository-wide COMS "
    "support for datatype-property source terms. This capability must be "
    "implemented consistently for both the current SOSA mapping and the "
    "forthcoming SOSA mapping."
)

EXPECTED_DATATYPE_TERMS = {
    "sosa:endTime",
    "sosa:hasSimpleResult",
    "sosa:resultTime",
    "sosa:startTime",
}

EXPECTED_CLASS_DEFERRALS = {
    "sosa:ActuatableProperty",
    "sosa:Asset",
    "sosa:ObservableProperty",
    "sosa:Result",
    "sosa:Sensor",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CheckSosaNextMappingTests(unittest.TestCase):
    def test_governed_workbook_and_reasoning_are_exact(self) -> None:
        protected_paths = (*GOVERNED_INPUTS, *CURRENT_PRODUCTS)

        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in protected_paths
        }

        with tempfile.TemporaryDirectory(
            prefix="sosa-next-check-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="sosa-next-check-b-"
        ) as second_dir:
            first = checker.run_check(Path(first_dir))
            second = checker.run_check(Path(second_dir))

            for summary in (first, second):
                self.assertTrue(summary["passed"], summary)
                self.assertEqual(summary["source_triple_count"], 1207)
                self.assertEqual(
                    summary["source_sha256"],
                    {
                        path.relative_to(REPO_ROOT).as_posix(): digest
                        for path, digest
                        in checker.PINNED_SOURCE_SHA256.items()
                    },
                )
                self.assertEqual(summary["governed_row_count"], 119)
                self.assertEqual(summary["unique_row_id_count"], 119)
                self.assertEqual(summary["active_mapping_count"], 61)
                self.assertEqual(summary["deferred_mapping_count"], 9)
                self.assertEqual(
                    summary["explicitly_unmapped_row_count"],
                    49,
                )
                self.assertEqual(summary["malformed_row_count"], 0)
                self.assertEqual(
                    summary["canonical_authoritative_axiom_count"],
                    61,
                )
                self.assertEqual(
                    summary["active_ontology_triple_count"],
                    425,
                )

                reasoning = summary["reasoning"]
                self.assertTrue(reasoning["passed"])
                self.assertEqual(reasoning["return_code"], 0)
                self.assertTrue(reasoning["reasoned_output_exists"])
                self.assertEqual(
                    reasoning["reasoned_output_triples"],
                    1899,
                )
                self.assertEqual(
                    reasoning["unsatisfiable_classes"],
                    [],
                )
                self.assertEqual(reasoning["robot_output"], "")

                deferred = {
                    item["subject"]: item
                    for item in summary["deferred_mappings"]
                }
                self.assertEqual(len(deferred), 9)
                self.assertEqual(
                    len(deferred),
                    len(summary["deferred_mappings"]),
                )
                self.assertTrue(
                    all(
                        item["reasoning"]
                        for item in summary["deferred_mappings"]
                    )
                )

                class_terms = {
                    subject
                    for subject, item in deferred.items()
                    if item["subject_kind"] == "class"
                }
                self.assertEqual(
                    class_terms,
                    EXPECTED_CLASS_DEFERRALS,
                )

                sensor = deferred["sosa:Sensor"]
                self.assertEqual(sensor["subject_kind"], "class")
                self.assertIn(
                    "next CCO release",
                    sensor["reasoning"],
                )
                self.assertIn(
                    "forthcoming SOSA 2023 Edition",
                    sensor["reasoning"],
                )

                datatype_terms = {
                    subject
                    for subject, item in deferred.items()
                    if item["subject_kind"] == "datatype_property"
                }
                self.assertEqual(
                    datatype_terms,
                    EXPECTED_DATATYPE_TERMS,
                )

                for subject in EXPECTED_DATATYPE_TERMS:
                    self.assertEqual(
                        deferred[subject]["reasoning"],
                        DATATYPE_DEFERRAL,
                    )

                explicitly_unmapped = {
                    item["subject"]: item
                    for item in summary["explicitly_unmapped_rows"]
                }
                self.assertEqual(len(explicitly_unmapped), 49)
                self.assertEqual(
                    len(explicitly_unmapped),
                    len(summary["explicitly_unmapped_rows"]),
                )
                self.assertIn(
                    "sosa:hasSample",
                    explicitly_unmapped,
                )
                self.assertIn(
                    "sosa:isSampleOf",
                    explicitly_unmapped,
                )

            stable_sections = (
                "source_sha256",
                "source_triple_count",
                "governed_row_count",
                "unique_row_id_count",
                "active_mapping_count",
                "deferred_mapping_count",
                "explicitly_unmapped_row_count",
                "malformed_row_count",
                "canonical_authoritative_axiom_count",
                "active_ontology_triple_count",
                "deferred_mappings",
                "explicitly_unmapped_rows",
                "reasoning",
            )

            for section in stable_sections:
                self.assertEqual(
                    first[section],
                    second[section],
                )

            for directory, summary in (
                (Path(first_dir), first),
                (Path(second_dir), second),
            ):
                summary_path = directory / "summary.json"
                self.assertTrue(summary_path.is_file())
                self.assertEqual(
                    json.loads(
                        summary_path.read_text(encoding="utf-8")
                    ),
                    summary,
                )

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in protected_paths
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
