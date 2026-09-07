#!/usr/bin/env python3
"""Focused tests for governed ROBOT diff incompatibility evidence."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import robot_diff_pilot as pilot  # noqa: E402


MAINTAINED_PRODUCTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def governed_invariants(
    result: dict[str, object],
) -> dict[str, object]:
    return {
        key: value
        for key, value in result.items()
        if key not in {
            "artifact_text",
            "process_output",
            "catalog_sha256",
        }
    }


class RobotDiffPilotTests(unittest.TestCase):
    def test_control_passes_and_governed_self_diffs_are_false_positives(
        self,
    ) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }

        with tempfile.TemporaryDirectory(
            prefix="robot-diff-pilot-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="robot-diff-pilot-b-"
        ) as second_dir:
            first = pilot.run_pilot(Path(first_dir))
            second = pilot.run_pilot(Path(second_dir))

            self.assertTrue(first["passed"], first)
            self.assertTrue(second["passed"], second)

            for summary in (first, second):
                self.assertEqual(
                    summary["disposition"],
                    (
                        "robot diff is suitable for OWLAPI-compatible "
                        "controls but rejected as an authoritative "
                        "semantic-diff mechanism for the current "
                        "governed products"
                    ),
                )

                control = summary["control"]
                self.assertTrue(control["passed"])
                self.assertEqual(control["return_code"], 0)
                self.assertEqual(control["parser_warning_count"], 0)
                self.assertTrue(control["artifact_exists"])
                self.assertEqual(control["artifact_bytes"], 25)
                self.assertEqual(
                    control["artifact_text"],
                    "Ontologies are identical\n",
                )
                self.assertTrue(control["reports_identical"])
                self.assertIsNone(control["left_only_axiom_count"])
                self.assertIsNone(control["right_only_axiom_count"])

                alignment = summary["alignment_core_self_diff"]
                self.assertTrue(alignment["false_positive_proven"])
                self.assertEqual(alignment["return_code"], 0)
                self.assertEqual(alignment["parser_warning_count"], 2)
                self.assertTrue(alignment["artifact_exists"])
                self.assertFalse(alignment["reports_identical"])
                self.assertEqual(alignment["left_only_axiom_count"], 1)
                self.assertEqual(alignment["right_only_axiom_count"], 1)
                self.assertEqual(
                    alignment["expected_property_iri"],
                    pilot.IN_CONDITION_IRI,
                )
                self.assertTrue(
                    alignment["contains_expected_property"]
                )
                self.assertTrue(
                    alignment["contains_annotation_property_domain"]
                )
                self.assertTrue(
                    alignment["contains_generated_blank_node"]
                )
                self.assertIn(
                    "owl#unionOf",
                    alignment["process_output"],
                )

                strict = summary["strict_bfo_self_diff"]
                self.assertTrue(strict["false_positive_proven"])
                self.assertEqual(strict["return_code"], 0)
                self.assertEqual(strict["parser_warning_count"], 2)
                self.assertTrue(strict["artifact_exists"])
                self.assertFalse(strict["reports_identical"])
                self.assertEqual(strict["left_only_axiom_count"], 1)
                self.assertEqual(strict["right_only_axiom_count"], 1)
                self.assertEqual(
                    strict["expected_property_iri"],
                    pilot.IS_PROPERTY_OF_IRI,
                )
                self.assertTrue(strict["contains_expected_property"])
                self.assertTrue(
                    strict["contains_annotation_property_domain"]
                )
                self.assertTrue(
                    strict["contains_generated_blank_node"]
                )
                self.assertIn(
                    "owl#unionOf",
                    strict["process_output"],
                )

            self.assertEqual(first["control"], second["control"])
            self.assertEqual(
                governed_invariants(
                    first["alignment_core_self_diff"]
                ),
                governed_invariants(
                    second["alignment_core_self_diff"]
                ),
            )
            self.assertEqual(
                governed_invariants(
                    first["strict_bfo_self_diff"]
                ),
                governed_invariants(
                    second["strict_bfo_self_diff"]
                ),
            )

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
