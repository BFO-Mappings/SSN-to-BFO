#!/usr/bin/env python3
"""Focused tests for governed read-only ROBOT verify behavior."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import robot_verify_pilot as pilot  # noqa: E402


WORKBOOK = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"

MAINTAINED_PRODUCTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RobotVerifyPilotTests(unittest.TestCase):
    def test_governed_pass_and_controlled_failure_are_exact(self) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }

        with tempfile.TemporaryDirectory(
            prefix="robot-verify-pilot-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="robot-verify-pilot-b-"
        ) as second_dir:
            first = pilot.run_pilot(WORKBOOK, Path(first_dir))
            second = pilot.run_pilot(WORKBOOK, Path(second_dir))

            self.assertTrue(first["passed"], first)
            self.assertTrue(second["passed"], second)

            for summary in (first, second):
                self.assertEqual(summary["governed_row_count"], 105)

                coverage = summary["coverage_graph"]
                self.assertEqual(coverage["triple_count"], 182)
                self.assertEqual(
                    coverage["round_trip_triple_count"],
                    182,
                )
                self.assertTrue(coverage["round_trip_isomorphic"])

                controlled = summary["controlled_violation"]
                self.assertEqual(
                    controlled["term"],
                    "http://www.w3.org/ns/sosa/ActuatableProperty",
                )
                self.assertEqual(
                    controlled["status"],
                    "absent_from_spreadsheet",
                )
                self.assertEqual(controlled["expected_row_count"], 1)
                self.assertEqual(
                    controlled["expected_rows"],
                    [[
                        "http://www.w3.org/ns/sosa/ActuatableProperty",
                        "class",
                        "absent_from_spreadsheet",
                    ]],
                )
                self.assertEqual(controlled["triple_count"], 182)
                self.assertEqual(
                    controlled["round_trip_triple_count"],
                    182,
                )
                self.assertTrue(controlled["round_trip_isomorphic"])

                passing = summary["passing_verify"]
                self.assertTrue(passing["passed"])
                self.assertEqual(passing["return_code"], 0)
                self.assertIn("PASS Rule", passing["output"])
                self.assertIn("0 violation(s)", passing["output"])
                self.assertEqual(passing["report_files"], [])

                violating = summary["violating_verify"]
                self.assertTrue(violating["passed"])
                self.assertEqual(violating["return_code"], 1)
                self.assertIn("FAIL Rule", violating["output"])
                self.assertIn("1 violation(s)", violating["output"])
                self.assertEqual(
                    violating["report_files"],
                    ["unmapped-source-terms.csv"],
                )
                self.assertEqual(
                    violating["report_name"],
                    "unmapped-source-terms.csv",
                )
                self.assertTrue(violating["report_exists"])
                self.assertEqual(violating["report_bytes"], 102)
                self.assertEqual(
                    violating["report_header"],
                    ["term", "kind", "coverageStatus"],
                )
                self.assertEqual(
                    violating["report_rows"],
                    controlled["expected_rows"],
                )

            for section in (
                "coverage_graph",
                "controlled_violation",
                "passing_verify",
                "violating_verify",
            ):
                self.assertEqual(first[section], second[section])

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
