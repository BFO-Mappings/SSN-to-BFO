#!/usr/bin/env python3
"""Focused tests for SOSA-2023 COMS MappingStatus governance."""

from __future__ import annotations

from dataclasses import dataclass
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(
    0,
    str(REPO_ROOT / "tools"),
)

import generate_mapping_from_coms as coms  # noqa: E402
import sosa_2023_mapping_status as status  # noqa: E402


@dataclass(frozen=True)
class SyntheticRow:
    subject_text: str = "sosa:Example"
    predicate_text: str = ""
    target_text: str = ""
    reasoning_text: str = ""
    mapping_status_text: str = ""
    diagnostic_id: str = "Synthetic!2 [urn:uuid:test]"


class MappingStatusUnitTests(unittest.TestCase):
    def test_all_four_statuses_are_classified(self) -> None:
        rows = (
            SyntheticRow(
                predicate_text="rdfs:subClassOf",
                target_text="bfo:Entity",
                mapping_status_text="active",
            ),
            SyntheticRow(
                reasoning_text="decision remains open",
                mapping_status_text="deferred",
            ),
            SyntheticRow(
                reasoning_text="reviewed; no direct mapping adopted",
                mapping_status_text="no_direct_mapping",
            ),
            SyntheticRow(
                mapping_status_text="unreviewed",
            ),
        )

        result = status.classify_workbook_rows(
            rows
        )

        self.assertEqual(
            len(result.active),
            1,
        )
        self.assertEqual(
            len(result.deferred),
            1,
        )
        self.assertEqual(
            len(result.no_direct_mapping),
            1,
        )
        self.assertEqual(
            len(result.unreviewed),
            1,
        )
        self.assertEqual(
            result.governed_row_count,
            4,
        )

    def assert_invalid(
        self,
        row: SyntheticRow,
        fragment: str,
    ) -> None:
        with self.assertRaises(
            status.MappingStatusError
        ) as caught:
            status.classify_workbook_rows(
                (row,)
            )

        self.assertIn(
            fragment,
            str(caught.exception),
        )

    def test_missing_status_is_rejected(self) -> None:
        self.assert_invalid(
            SyntheticRow(),
            "MappingStatus is required",
        )

    def test_unknown_status_is_rejected(self) -> None:
        self.assert_invalid(
            SyntheticRow(
                mapping_status_text="unknown",
            ),
            "unknown coms:MappingStatus",
        )

    def test_active_requires_mapping(self) -> None:
        self.assert_invalid(
            SyntheticRow(
                mapping_status_text="active",
            ),
            "active status requires",
        )

    def test_nonactive_status_prohibits_mapping(self) -> None:
        self.assert_invalid(
            SyntheticRow(
                predicate_text="rdfs:subClassOf",
                target_text="bfo:Entity",
                reasoning_text="later",
                mapping_status_text="deferred",
            ),
            "requires blank predicate and target",
        )

    def test_deferred_requires_reasoning(self) -> None:
        self.assert_invalid(
            SyntheticRow(
                mapping_status_text="deferred",
            ),
            "deferred status requires",
        )

    def test_no_direct_mapping_requires_reasoning(self) -> None:
        self.assert_invalid(
            SyntheticRow(
                mapping_status_text="no_direct_mapping",
            ),
            "no_direct_mapping status requires",
        )

    def test_unreviewed_prohibits_reasoning(self) -> None:
        self.assert_invalid(
            SyntheticRow(
                reasoning_text="already reviewed",
                mapping_status_text="unreviewed",
            ),
            "unreviewed status requires blank",
        )


class CurrentWorkbookTests(unittest.TestCase):
    def test_sosa_2023_current_status_distribution(self) -> None:
        rows, stats = coms.read_workbook(
            REPO_ROOT
            / "mappings/SOSA-next-to-BFO-COMS.xlsx"
        )

        coms.validate_workbook_row_ids(
            rows,
            stats,
        )

        result = status.classify_workbook_rows(
            rows
        )

        self.assertEqual(
            stats.unique_row_id_count,
            119,
        )

        self.assertEqual(
            (
                len(result.active),
                len(result.deferred),
                len(result.no_direct_mapping),
                len(result.unreviewed),
            ),
            (
                55,
                4,
                60,
                0,
            ),
        )


if __name__ == "__main__":
    unittest.main()
