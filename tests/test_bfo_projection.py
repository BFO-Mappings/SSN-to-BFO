#!/usr/bin/env python3
"""Focused governance tests for the non-materialized BFO Projection role."""

from __future__ import annotations

import dataclasses
import hashlib
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import generate_mapping_from_coms as coms  # noqa: E402
import modular_products as modular  # noqa: E402
from coms_row_identity import RowLocation  # noqa: E402
from product_dispositions import (  # noqa: E402
    ProductDisposition,
    load_disposition_document,
)
from publication_metadata import load_metadata  # noqa: E402


class BfoProjectionRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows, stats = coms.read_workbook(
            REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"
        )
        cls.processed = coms.validate_and_process_rows(
            rows,
            coms.Resolver(),
            stats,
        )
        cls.canonical_rows = tuple(
            coms.canonical_input_for_processed_row(row)
            for row in cls.processed
        )
        cls.audits = tuple(
            row.identity_audit
            for row in cls.processed
        )
        cls.disposition = load_disposition_document(
            REPO_ROOT / "reports/coms-product-dispositions.json"
        )
        cls.metadata = load_metadata(
            REPO_ROOT / "config/publication-metadata.toml"
        )
        cls.reconciliation = modular.reconcile_product_axioms(
            modular.BFO_PROJECTION_KEY,
            cls.canonical_rows,
            cls.audits,
            cls.disposition,
        )

        core_selected = modular.select_product_axioms(
            "alignment_core",
            cls.canonical_rows,
            cls.audits,
            cls.disposition,
        )
        strict_selected = modular.select_product_axioms(
            "strict_bfo_mapping",
            cls.canonical_rows,
            cls.audits,
            cls.disposition,
        )
        cco_selected = modular.select_product_axioms(
            "cco_extension",
            cls.canonical_rows,
            cls.audits,
            cls.disposition,
        )

        cls.core_result = modular.build_alignment_core(
            core_selected,
            cls.metadata,
        )
        cls.strict_result = modular.build_strict_bfo_mapping(
            strict_selected,
            cls.metadata,
        )
        cls.cco_result = modular.build_cco_extension(
            cco_selected,
            cls.metadata,
        )

    @staticmethod
    def error_codes(
        error: modular.ModularProductError,
    ) -> set[str]:
        return {
            value.code
            for value in error.issues
        }

    def replace_disposition_row(
        self,
        replacement,
    ):
        return dataclasses.replace(
            self.disposition,
            rows=tuple(
                replacement
                if row.row_id == replacement.row_id
                else row
                for row in self.disposition.rows
            ),
        )

    def test_exact_disposition_reconciliation_selects_no_direct_axioms(
        self,
    ) -> None:
        self.assertEqual(
            self.reconciliation.product_key,
            "bfo_projection",
        )
        self.assertEqual(
            self.reconciliation.governed_axiom_count,
            103,
        )
        self.assertEqual(
            self.reconciliation.selected_axioms,
            (),
        )
        self.assertEqual(
            tuple(
                (
                    value.target_category,
                    value.status,
                    value.reason_code,
                    value.count,
                )
                for value in self.reconciliation.disposition_totals
            ),
            (
                ("target_neutral", "provided_transitively", None, 29),
                ("bfo_bearing", "provided_through_import", None, 19),
                (
                    "cco_bearing",
                    "deferred",
                    "NO_APPROVED_TRANSFORMATION_RULE",
                    25,
                ),
                (
                    "mixed_bfo_cco",
                    "deferred",
                    "NO_APPROVED_TRANSFORMATION_RULE",
                    30,
                ),
            ),
        )

    def test_reordered_processed_rows_and_audits_are_stable(
        self,
    ) -> None:
        reordered = modular.reconcile_product_axioms(
            "bfo_projection",
            reversed(self.canonical_rows),
            reversed(self.audits),
            self.disposition,
        )
        self.assertEqual(
            reordered,
            self.reconciliation,
        )

    def test_identity_reconciliation_rejects_row_and_axiom_substitutions(
        self,
    ) -> None:
        replacement = dataclasses.replace(
            self.canonical_rows[0],
            row_id="urn:uuid:ffffffff-ffff-4fff-8fff-ffffffffffff",
        )

        row_cases = (
            self.canonical_rows[1:],
            (*self.canonical_rows, self.canonical_rows[0]),
            (replacement, *self.canonical_rows[1:]),
        )

        for values in row_cases:
            with self.subTest(
                row_count=len(values),
            ):
                with self.assertRaises(
                    modular.ModularProductError
                ):
                    modular.reconcile_product_axioms(
                        "bfo_projection",
                        values,
                        self.audits,
                        self.disposition,
                    )

        source = self.disposition.rows[0]
        source_axiom = source.authoritative_axioms[0]

        axiom_cases = (
            dataclasses.replace(
                source,
                authoritative_axioms=(),
            ),
            dataclasses.replace(
                source,
                authoritative_axioms=(
                    dataclasses.replace(
                        source_axiom,
                        axiom_id="sha256:" + "0" * 64,
                    ),
                ),
            ),
            dataclasses.replace(
                source,
                authoritative_axioms=(
                    source_axiom,
                    source_axiom,
                ),
            ),
        )

        for replacement_row in axiom_cases:
            with self.subTest(
                axiom_count=len(
                    replacement_row.authoritative_axioms
                ),
            ):
                with self.assertRaises(
                    modular.ModularProductError
                ):
                    modular.reconcile_product_axioms(
                        "bfo_projection",
                        self.canonical_rows,
                        self.audits,
                        self.replace_disposition_row(
                            replacement_row
                        ),
                    )

    def test_location_hash_row_and_axiom_mismatches_are_fatal(
        self,
    ) -> None:
        row = self.canonical_rows[0]

        moved = dataclasses.replace(
            row,
            location=RowLocation(
                "Other",
                row.location.row_number,
            ),
        )

        audit_cases = (
            (
                moved,
                self.audits[0],
            ),
            (
                row,
                dataclasses.replace(
                    self.audits[0],
                    source_expression_sha256="0" * 64,
                ),
            ),
            (
                row,
                dataclasses.replace(
                    self.audits[0],
                    expression=dataclasses.replace(
                        self.audits[0].expression,
                        target=(
                            self.audits[0].expression.target
                            or ""
                        )
                        + " changed",
                    ),
                ),
            ),
        )

        for changed_row, changed_audit in audit_cases:
            with self.subTest(
                location=changed_row.location.text,
            ):
                with self.assertRaises(
                    modular.ModularProductError
                ):
                    modular.reconcile_product_axioms(
                        "bfo_projection",
                        (
                            changed_row,
                            *self.canonical_rows[1:],
                        ),
                        (
                            changed_audit,
                            *self.audits[1:],
                        ),
                        self.disposition,
                    )

        disposition_row = self.disposition.rows[0]
        axiom = disposition_row.authoritative_axioms[0]

        changed = dataclasses.replace(
            disposition_row,
            authoritative_axioms=(
                dataclasses.replace(
                    axiom,
                    canonical_expression=(
                        axiom.canonical_expression
                        + " changed"
                    ),
                ),
            ),
        )

        with self.assertRaises(
            modular.ModularProductError
        ) as raised:
            modular.reconcile_product_axioms(
                "bfo_projection",
                self.canonical_rows,
                self.audits,
                self.replace_disposition_row(
                    changed
                ),
            )

        self.assertIn(
            "CANONICAL_EXPRESSION_MISMATCH",
            self.error_codes(
                raised.exception
            ),
        )

    def test_wrong_status_reason_or_category_is_fatal(
        self,
    ) -> None:
        cases = []

        for row in self.disposition.rows[:3]:
            axiom = row.authoritative_axioms[0]

            changed_dispositions = tuple(
                (
                    key,
                    ProductDisposition(
                        "emitted_unchanged"
                    ),
                )
                if key == "bfo_projection"
                else (
                    key,
                    value,
                )
                for key, value in axiom.product_dispositions
            )

            cases.append(
                dataclasses.replace(
                    row,
                    authoritative_axioms=(
                        dataclasses.replace(
                            axiom,
                            product_dispositions=(
                                changed_dispositions
                            ),
                        ),
                    ),
                )
            )

        deferred_row = next(
            row
            for row in self.disposition.rows
            if dict(
                row.authoritative_axioms[
                    0
                ].product_dispositions
            )["bfo_projection"].status
            == "deferred"
        )

        deferred_axiom = (
            deferred_row.authoritative_axioms[0]
        )

        changed_reason = tuple(
            (
                key,
                ProductDisposition(
                    "deferred",
                    "TARGET_SPECIFIC",
                ),
            )
            if key == "bfo_projection"
            else (
                key,
                value,
            )
            for key, value in deferred_axiom.product_dispositions
        )

        cases.append(
            dataclasses.replace(
                deferred_row,
                authoritative_axioms=(
                    dataclasses.replace(
                        deferred_axiom,
                        product_dispositions=(
                            changed_reason
                        ),
                    ),
                ),
            )
        )

        cases.append(
            dataclasses.replace(
                deferred_row,
                authoritative_axioms=(
                    dataclasses.replace(
                        deferred_axiom,
                        target_category="target_neutral",
                    ),
                ),
            )
        )

        for changed in cases:
            with self.subTest(
                row_id=changed.row_id,
            ):
                with self.assertRaises(
                    modular.ModularProductError
                ) as raised:
                    modular.reconcile_product_axioms(
                        "bfo_projection",
                        self.canonical_rows,
                        self.audits,
                        self.replace_disposition_row(
                            changed
                        ),
                    )

                self.assertTrue(
                    self.error_codes(
                        raised.exception
                    )
                    & {
                        "WRONG_PRODUCT_DISPOSITION",
                        "TARGET_CATEGORY_MISMATCH",
                    }
                )

    def test_existing_materialized_module_bytes_remain_protected(
        self,
    ) -> None:
        self.assertEqual(
            hashlib.sha256(
                self.core_result.serialized_bytes
            ).hexdigest(),
            "17695ef17379924449153b2c92ffaed6b57d497a1b2d1e854f584614cebec770",
        )
        self.assertEqual(
            hashlib.sha256(
                self.strict_result.serialized_bytes
            ).hexdigest(),
            "676b31620df10db5c26c46bcc44b2dfd5939d606b16e0fa8a910926e8497c3af",
        )
        self.assertEqual(
            self.cco_result.sha256,
            "2908f89648d42dc928f7225056216f1cbf3bcdc79de1bcf770b40a017a5e9bf5",
        )

    def test_projection_role_policy_is_zero_axiom_and_not_published(
        self,
    ) -> None:
        self.assertEqual(
            modular.BFO_PROJECTION_KEY,
            "bfo_projection",
        )
        self.assertEqual(
            modular.BFO_PROJECTION_AXIOM_COUNT,
            0,
        )
        self.assertNotIn(
            "bfo_projection",
            tuple(
                product.key
                for product in self.metadata.products
            ),
        )


if __name__ == "__main__":
    unittest.main()
