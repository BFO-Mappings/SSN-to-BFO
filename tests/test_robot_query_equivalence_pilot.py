#!/usr/bin/env python3
"""Focused tests for governed RDFLib versus ROBOT query equivalence."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import robot_query_equivalence_pilot as pilot  # noqa: E402


WORKBOOK = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"

MAINTAINED_PRODUCTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RobotQueryEquivalencePilotTests(unittest.TestCase):
    def test_zero_byte_robot_csv_represents_zero_rows(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="robot-query-empty-"
        ) as temp_dir:
            path = Path(temp_dir) / "empty.csv"
            path.write_bytes(b"")

            header, rows = pilot.read_robot_csv(
                path,
                pilot.UNMAPPED_COLUMNS,
            )

            self.assertEqual(header, ())
            self.assertEqual(rows, ())

    def test_governed_queries_match_rdflib_without_product_changes(self) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }

        with tempfile.TemporaryDirectory(
            prefix="robot-query-pilot-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="robot-query-pilot-b-"
        ) as second_dir:
            first = pilot.run_pilot(WORKBOOK, Path(first_dir))
            second = pilot.run_pilot(WORKBOOK, Path(second_dir))

            self.assertTrue(first["passed"], first)
            self.assertTrue(second["passed"], second)

            for summary in (first, second):
                self.assertEqual(summary["governed_row_count"], 105)

                source_graph = summary["source_graph"]
                self.assertEqual(source_graph["triple_count"], 1157)
                self.assertEqual(
                    source_graph["round_trip_triple_count"],
                    1157,
                )
                self.assertTrue(source_graph["round_trip_isomorphic"])
                self.assertEqual(source_graph["owl_imports_count"], 4)

                coverage_graph = summary["coverage_graph"]
                self.assertEqual(coverage_graph["triple_count"], 182)
                self.assertEqual(
                    coverage_graph["round_trip_triple_count"],
                    182,
                )
                self.assertTrue(coverage_graph["round_trip_isomorphic"])

                source = summary["source_query"]
                self.assertTrue(source["passed"])
                self.assertEqual(source["robot_return_code"], 0)
                self.assertEqual(source["rdflib_row_count"], 91)
                self.assertEqual(source["robot_row_count"], 91)
                self.assertTrue(source["same_ordered_rows"])
                self.assertEqual(source["rdflib_only_rows"], [])
                self.assertEqual(source["robot_only_rows"], [])
                self.assertEqual(source["robot_header"], ["term", "kind"])
                self.assertGreater(source["robot_output_bytes"], 0)

                unmapped = summary["unmapped_query"]
                self.assertTrue(unmapped["passed"])
                self.assertEqual(unmapped["robot_return_code"], 0)
                self.assertEqual(unmapped["rdflib_row_count"], 0)
                self.assertEqual(unmapped["robot_row_count"], 0)
                self.assertTrue(unmapped["same_ordered_rows"])
                self.assertEqual(unmapped["rdflib_only_rows"], [])
                self.assertEqual(unmapped["robot_only_rows"], [])
                self.assertEqual(unmapped["robot_header"], [])
                self.assertTrue(unmapped["robot_output_exists"])
                self.assertEqual(unmapped["robot_output_bytes"], 0)

            for section in (
                "source_query",
                "unmapped_query",
            ):
                self.assertEqual(first[section], second[section])

            for section in (
                "source_graph",
                "coverage_graph",
            ):
                first_semantic = {
                    key: value
                    for key, value in first[section].items()
                    if key != "sha256"
                }
                second_semantic = {
                    key: value
                    for key, value in second[section].items()
                    if key != "sha256"
                }
                self.assertEqual(first_semantic, second_semantic)

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
