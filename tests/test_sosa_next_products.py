#!/usr/bin/env python3
"""Focused tests for maintained SOSA-next products."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_sosa_next_products as checker  # noqa: E402
import generate_mapping_from_coms as coms  # noqa: E402
import generate_sosa_next_products as products  # noqa: E402


PROTECTED_PATHS = (
    products.WORKBOOK,
    products.METADATA_PATH,
    *products.CURRENT_SOSA_PRODUCTS.values(),
    *products.MAINTAINED_PRODUCTS.values(),
    checker.products.mapping_checker.SOURCE_VERSION_CONFIG,
    *checker.products.mapping_checker.SOURCE_FILES,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


class SosaNextProductTests(unittest.TestCase):
    def test_maintained_products_are_exact(self) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): (
                sha256(path)
            )
            for path in PROTECTED_PATHS
        }

        original_prefix_files = dict(
            coms.PREFIX_FILES
        )
        original_source_imports = tuple(
            coms.SOURCE_IMPORTS
        )

        robot = os.environ.get(
            "SOSA_NEXT_TEST_ROBOT"
        )

        with tempfile.TemporaryDirectory(
            prefix="sosa-next-products-check-"
        ) as directory:
            root = Path(directory)

            summary = checker.run_check(
                root,
                robot,
            )

            self.assertTrue(
                summary["passed"],
                summary,
            )
            self.assertTrue(
                summary[
                    "maintained_products_fresh"
                ]
            )
            self.assertTrue(
                summary[
                    "independent_builds_byte_identical"
                ]
            )
            self.assertTrue(
                summary[
                    "logical_union_isomorphic"
                ]
            )
            self.assertTrue(
                summary[
                    "current_sosa_products_unchanged"
                ]
            )
            self.assertTrue(
                summary["resolver_state_restored"]
            )

            self.assertEqual(
                summary["governed_row_count"],
                119,
            )
            self.assertEqual(
                summary["unique_row_id_count"],
                119,
            )
            self.assertEqual(
                summary["active_mapping_count"],
                46,
            )
            self.assertEqual(
                summary["deferred_mapping_count"],
                17,
            )
            self.assertEqual(
                summary[
                    "explicitly_unmapped_row_count"
                ],
                56,
            )
            self.assertEqual(
                summary[
                    "canonical_authoritative_axiom_count"
                ],
                46,
            )
            self.assertEqual(
                summary["category_counts"],
                {
                    "bfo_bearing": 21,
                    "cco_bearing": 24,
                    "mixed_bfo_cco": 1,
                },
            )
            self.assertEqual(
                summary[
                    "combined_logical_triple_count"
                ],
                268,
            )
            self.assertEqual(
                summary[
                    "integrated_reference_logical_triple_count"
                ],
                268,
            )

            self.assertEqual(
                tuple(products.PRODUCT_ORDER),
                (
                    "integrated",
                    "strict_bfo_mapping",
                    "cco_extension",
                ),
            )

            expected = {
                "integrated": {
                    "axiom_count": 46,
                    "logical_triple_count": 268,
                    "total_triple_count": 281,
                    "sha256": (
                        "fec0e53270b4b527798db6ff078371c1"
                        "050eb8afb441440db09fbc17cf840520"
                    ),
                },
                "strict_bfo_mapping": {
                    "axiom_count": 21,
                    "logical_triple_count": 151,
                    "total_triple_count": 159,
                    "sha256": (
                        "e28dcdc2a261793b091f5c8d2e92b04"
                        "a5e7c819659840e5c9ed622c444b22ad3"
                    ),
                },
                "cco_extension": {
                    "axiom_count": 25,
                    "logical_triple_count": 117,
                    "total_triple_count": 126,
                    "sha256": (
                        "c61b07fae4aee044d7e627e7eaee94a"
                        "bca6503f0da96e8fe8bd8820c8e31d09a"
                    ),
                },
            }

            expected_closures = {
                "integrated": 15231,
                "strict_bfo_mapping": 15114,
                "cco_extension": 15239,
            }

            for product_key, values in (
                expected.items()
            ):
                observed = summary["products"][
                    product_key
                ]

                for key, value in values.items():
                    self.assertEqual(
                        observed[key],
                        value,
                        (
                            product_key,
                            key,
                            observed,
                        ),
                    )

                reasoning = summary["reasoning"][
                    product_key
                ]

                self.assertTrue(
                    reasoning["passed"],
                    reasoning,
                )
                self.assertEqual(
                    reasoning["return_code"],
                    0,
                )
                self.assertTrue(
                    reasoning[
                        "reasoned_output_exists"
                    ]
                )
                self.assertEqual(
                    reasoning[
                        "unsatisfiable_classes"
                    ],
                    [],
                )
                self.assertEqual(
                    reasoning[
                        "closure_triple_count"
                    ],
                    expected_closures[product_key],
                )

            self.assertFalse(
                any(
                    path.exists()
                    for path in (
                        products
                        .RETIRED_MAINTAINED_PRODUCTS
                    )
                )
            )

            stored = json.loads(
                (
                    root / "check-summary.json"
                ).read_text(encoding="utf-8")
            )

            self.assertEqual(stored, summary)

        self.assertEqual(
            dict(coms.PREFIX_FILES),
            original_prefix_files,
        )
        self.assertEqual(
            tuple(coms.SOURCE_IMPORTS),
            original_source_imports,
        )

        after = {
            path.relative_to(REPO_ROOT).as_posix(): (
                sha256(path)
            )
            for path in PROTECTED_PATHS
        }

        self.assertEqual(before, after)

    def test_atomic_failure_restores_outputs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="sosa-next-rollback-"
        ) as directory:
            root = Path(directory)
            candidates = root / "candidates"
            destinations_root = (
                root / "destinations"
            )
            transaction = root / "transaction"

            candidates.mkdir()
            destinations_root.mkdir()

            candidate_paths = {}
            destinations = {}
            original_bytes = {}

            for index, product_key in enumerate(
                products.PRODUCT_ORDER,
                start=1,
            ):
                candidate = (
                    candidates / product_key
                )
                destination = (
                    destinations_root / product_key
                )

                candidate.write_bytes(
                    f"new-{index}\n".encode()
                )
                destination.write_bytes(
                    f"old-{index}\n".encode()
                )

                candidate_paths[
                    product_key
                ] = candidate
                destinations[
                    product_key
                ] = destination
                original_bytes[
                    product_key
                ] = destination.read_bytes()

            def fail_after_replacement() -> None:
                raise RuntimeError(
                    "synthetic post-replacement failure"
                )

            with self.assertRaisesRegex(
                RuntimeError,
                "synthetic post-replacement failure",
            ):
                products.replace_outputs_atomically(
                    candidate_paths,
                    destinations,
                    transaction_dir=transaction,
                    post_replace=(
                        fail_after_replacement
                    ),
                )

            for product_key in (
                products.PRODUCT_ORDER
            ):
                self.assertEqual(
                    destinations[
                        product_key
                    ].read_bytes(),
                    original_bytes[product_key],
                )


if __name__ == "__main__":
    unittest.main()
