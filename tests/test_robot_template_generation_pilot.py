#!/usr/bin/env python3
"""Focused tests for normalized ROBOT Template generation from governed COMS rows."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import robot_template_generation_pilot as pilot  # noqa: E402
from coms_row_identity import ExpressionNode  # noqa: E402


WORKBOOK = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"

MAINTAINED_PRODUCTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RobotTemplateGenerationPilotTests(unittest.TestCase):
    def test_normalized_expression_uses_generated_labels(self) -> None:
        class_a = "http://example.org/ClassA"
        class_b = "http://example.org/ClassB"
        property_a = "http://example.org/propertyA"

        expression = ExpressionNode(
            kind="intersection",
            children=(
                ExpressionNode(kind="named", iri=class_a),
                ExpressionNode(
                    kind="some",
                    property_iri=property_a,
                    filler=ExpressionNode(kind="named", iri=class_b),
                ),
            ),
        )

        labels = {
            ("class", class_a): pilot.deterministic_label("class", class_a),
            ("class", class_b): pilot.deterministic_label("class", class_b),
            ("property", property_a): pilot.deterministic_label(
                "property",
                property_a,
            ),
        }

        rendered = pilot.render_manchester_expression(expression, labels)

        self.assertNotIn(class_a, rendered)
        self.assertNotIn(class_b, rendered)
        self.assertNotIn(property_a, rendered)
        self.assertIn(labels[("class", class_a)], rendered)
        self.assertIn(labels[("class", class_b)], rendered)
        self.assertIn(labels[("property", property_a)], rendered)
        self.assertIn(" and ", rendered)
        self.assertIn(" some ", rendered)

    def test_governed_workbook_reconstructs_all_non_chain_axioms(self) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }

        with tempfile.TemporaryDirectory(
            prefix="robot-template-pilot-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="robot-template-pilot-b-"
        ) as second_dir:
            first_root = Path(first_dir)
            second_root = Path(second_dir)

            first = pilot.run_pilot(WORKBOOK, first_root)
            second = pilot.run_pilot(WORKBOOK, second_root)

            self.assertTrue(first["passed"], first)
            self.assertTrue(second["passed"], second)

            for summary in (first, second):
                self.assertEqual(summary["governed_row_count"], 105)
                self.assertEqual(summary["attempted_non_chain_rows"], 100)
                self.assertEqual(summary["excluded_property_chain_rows"], 3)
                self.assertEqual(summary["expected_axiom_count"], 100)
                self.assertEqual(summary["actual_axiom_count"], 100)
                self.assertEqual(summary["robot_return_code"], 0)
                self.assertEqual(summary["missing_axiom_ids"], [])
                self.assertEqual(summary["extra_axiom_ids"], [])
                self.assertEqual(summary["mismatched_axiom_ids"], [])

            first_artifacts = pilot.artifact_paths(first_root)
            second_artifacts = pilot.artifact_paths(second_root)

            self.assertEqual(
                first_artifacts.resolver_path.read_bytes(),
                second_artifacts.resolver_path.read_bytes(),
            )
            self.assertEqual(
                first_artifacts.template_path.read_bytes(),
                second_artifacts.template_path.read_bytes(),
            )

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
