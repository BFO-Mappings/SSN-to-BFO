#!/usr/bin/env python3
"""Focused tests for complete independent ROBOT reconstruction validation."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import robot_reconstruction_validation as reconstruction  # noqa: E402
import validate_robot_reconstruction as combined  # noqa: E402


WORKBOOK = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"

MAINTAINED_PRODUCTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RobotReconstructionValidationTests(unittest.TestCase):
    def test_canonical_comparison_reports_each_difference_category(self) -> None:
        comparison = reconstruction.compare_canonical_axioms(
            {
                "sha256:missing": "ExpectedMissing",
                "sha256:mismatch": "ExpectedMismatch",
                "sha256:shared": "Shared",
            },
            {
                "sha256:extra": "ActualExtra",
                "sha256:mismatch": "ActualMismatch",
                "sha256:shared": "Shared",
            },
        )

        self.assertFalse(comparison.passed)
        self.assertEqual(
            comparison.missing_axiom_ids,
            ("sha256:missing",),
        )
        self.assertEqual(
            comparison.extra_axiom_ids,
            ("sha256:extra",),
        )
        self.assertEqual(
            comparison.mismatched_axiom_ids,
            ("sha256:mismatch",),
        )

    def test_governed_workbook_reconstructs_all_103_axioms(self) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }

        with tempfile.TemporaryDirectory(
            prefix="robot-reconstruction-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="robot-reconstruction-b-"
        ) as second_dir:
            first_root = Path(first_dir)
            second_root = Path(second_dir)

            first = combined.run_validation(
                WORKBOOK,
                first_root,
            )
            second = combined.run_validation(
                WORKBOOK,
                second_root,
            )

            self.assertTrue(first["passed"], first)
            self.assertTrue(second["passed"], second)

            for summary in (first, second):
                self.assertEqual(summary["governed_row_count"], 105)
                self.assertTrue(
                    summary["non_chain_reconstruction_passed"]
                )
                self.assertTrue(
                    summary["property_chain_reconstruction_passed"]
                )
                self.assertEqual(summary["non_chain_axiom_count"], 100)
                self.assertEqual(summary["property_chain_axiom_count"], 3)
                self.assertEqual(summary["expected_axiom_count"], 103)
                self.assertEqual(summary["actual_axiom_count"], 103)
                self.assertEqual(summary["overlapping_axiom_ids"], [])
                self.assertEqual(summary["missing_axiom_ids"], [])
                self.assertEqual(summary["extra_axiom_ids"], [])
                self.assertEqual(summary["mismatched_axiom_ids"], [])
                self.assertEqual(
                    summary["non_chain_robot_return_code"],
                    0,
                )
                self.assertEqual(
                    summary["property_chain_robot_return_code"],
                    0,
                )

            self.assertEqual(
                (
                    first_root
                    / "non-chain"
                    / "normalized-template.tsv"
                ).read_bytes(),
                (
                    second_root
                    / "non-chain"
                    / "normalized-template.tsv"
                ).read_bytes(),
            )
            self.assertEqual(
                (
                    first_root
                    / "non-chain"
                    / "resolver.ttl"
                ).read_bytes(),
                (
                    second_root
                    / "non-chain"
                    / "resolver.ttl"
                ).read_bytes(),
            )
            self.assertEqual(
                (
                    first_root
                    / "property-chains"
                    / "normalized-property-chains.ofn"
                ).read_bytes(),
                (
                    second_root
                    / "property-chains"
                    / "normalized-property-chains.ofn"
                ).read_bytes(),
            )

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
