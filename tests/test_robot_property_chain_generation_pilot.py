#!/usr/bin/env python3
"""Focused tests for ROBOT property-chain generation from governed COMS rows."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph
from rdflib.compare import isomorphic


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import robot_property_chain_generation_pilot as pilot  # noqa: E402


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


class RobotPropertyChainGenerationPilotTests(unittest.TestCase):
    def test_functional_iri_validation(self) -> None:
        value = "http://example.org/property"
        self.assertEqual(
            pilot.functional_iri(value),
            "<http://example.org/property>",
        )

        for invalid in (
            "",
            "http://example.org/has space",
            "http://example.org/<invalid>",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    pilot.functional_iri(invalid)

    def test_governed_workbook_reconstructs_all_property_chains(self) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }

        with tempfile.TemporaryDirectory(
            prefix="robot-property-chain-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="robot-property-chain-b-"
        ) as second_dir:
            first_root = Path(first_dir)
            second_root = Path(second_dir)

            first = pilot.run_pilot(WORKBOOK, first_root)
            second = pilot.run_pilot(WORKBOOK, second_root)

            self.assertTrue(first["passed"], first)
            self.assertTrue(second["passed"], second)

            for summary in (first, second):
                self.assertEqual(summary["governed_row_count"], 105)
                self.assertEqual(
                    summary["attempted_property_chain_rows"],
                    3,
                )
                self.assertEqual(summary["expected_axiom_count"], 3)
                self.assertEqual(summary["actual_axiom_count"], 3)
                self.assertEqual(summary["robot_return_code"], 0)
                self.assertEqual(summary["missing_axiom_ids"], [])
                self.assertEqual(summary["extra_axiom_ids"], [])
                self.assertEqual(summary["mismatched_axiom_ids"], [])
                self.assertEqual(summary["declared_property_count"], 11)

            first_artifacts = pilot.artifact_paths(first_root)
            second_artifacts = pilot.artifact_paths(second_root)

            self.assertEqual(
                first_artifacts.functional_syntax_path.read_bytes(),
                second_artifacts.functional_syntax_path.read_bytes(),
            )

            first_graph = Graph().parse(
                first_artifacts.output_path,
                format="turtle",
            )
            second_graph = Graph().parse(
                second_artifacts.output_path,
                format="turtle",
            )
            self.assertTrue(isomorphic(first_graph, second_graph))

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
