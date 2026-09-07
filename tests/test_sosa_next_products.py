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
import check_sosa_2023_ro_mapping as ro_checker  # noqa: E402
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
                55,
            )
            self.assertEqual(
                summary["deferred_mapping_count"],
                0,
            )
            self.assertEqual(
                summary[
                    "explicitly_unmapped_row_count"
                ],
                64,
            )
            self.assertEqual(
                summary[
                    "canonical_authoritative_axiom_count"
                ],
                55,
            )
            self.assertEqual(
                summary["category_counts"],
                {
                    "bfo_bearing": 24,
                    "cco_bearing": 30,
                    "mixed_bfo_cco": 1,
                },
            )
            self.assertEqual(
                summary[
                    "combined_logical_triple_count"
                ],
                277,
            )
            self.assertEqual(
                summary[
                    "integrated_reference_logical_triple_count"
                ],
                277,
            )

            self.assertEqual(
                tuple(products.PRODUCT_ORDER),
                (
                    "integrated",
                    "strict_bfo_mapping",
                    "cco_extension",
                ),
            )

            self.assertEqual(
                tuple(
                    products
                    .DEVELOPMENT_PRODUCT_ORDER
                ),
                (
                    "integrated",
                    "strict_bfo_mapping",
                    "cco_extension",
                    "ro_mapping",
                ),
            )

            self.assertEqual(
                tuple(
                    products
                    .MAINTAINED_PRODUCTS
                ),
                products
                .DEVELOPMENT_PRODUCT_ORDER,
            )

            self.assertEqual(
                set(
                    summary[
                        "products"
                    ]
                ),
                set(
                    products
                    .DEVELOPMENT_PRODUCT_ORDER
                ),
            )

            self.assertEqual(
                set(
                    summary[
                        "reasoning"
                    ]
                ),
                set(
                    products.PRODUCT_ORDER
                ),
            )

            expected = {
                "integrated": {
                    "axiom_count": 55,
                    "logical_triple_count": 277,
                    "total_triple_count": 290,
                    "sha256": (
                        "3f502821476478252cdd9feb316b47612"
                        "daa473e511597970a1351617d5cfc12"
                    ),
                },
                "strict_bfo_mapping": {
                    "axiom_count": 24,
                    "logical_triple_count": 154,
                    "total_triple_count": 162,
                    "sha256": (
                        "1ae415bc96940e4007d064102f556aa5"
                        "44593616a0eff984534406028b846efb"
                    ),
                },
                "cco_extension": {
                    "axiom_count": 31,
                    "logical_triple_count": 123,
                    "total_triple_count": 132,
                    "sha256": (
                        "53a7cc6c0f664e51bf9f7ac28e3d067f"
                        "c4fdcc750e22a34fe5c12c766e51dc19"
                    ),
                },
            }

            ro_observed = summary[
                "products"
            ][
                "ro_mapping"
            ]

            expected_ro = {
                "axiom_count": 16,
                "governed_row_count": 82,
                "no_direct_mapping_count": 66,
                "skos_mapping_count": 0,
                "logical_triple_count": 16,
                "total_triple_count": 18,
                "sha256": (
                    "1747563c4bba01a0c6b34bd61660a1f0"
                    "c9026c266cc147991e74bc1d314ac388"
                ),
            }

            for key, value in (
                expected_ro.items()
            ):
                self.assertEqual(
                    ro_observed[key],
                    value,
                    (
                        "ro_mapping",
                        key,
                        ro_observed,
                    ),
                )

            validated_ro = (
                ro_checker.validate_product(
                    products
                    .MAINTAINED_PRODUCTS[
                        "ro_mapping"
                    ]
                )
            )

            self.assertEqual(
                len(
                    validated_ro[
                        "axioms"
                    ]
                ),
                16,
            )

            self.assertEqual(
                validated_ro[
                    "product"
                ][
                    "governed_property_count"
                ],
                82,
            )

            expected_closures = {
                "integrated": 15240,
                "strict_bfo_mapping": 15117,
                "cco_extension": 15248,
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
                products.DEVELOPMENT_PRODUCT_ORDER,
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
                products.DEVELOPMENT_PRODUCT_ORDER
            ):
                self.assertEqual(
                    destinations[
                        product_key
                    ].read_bytes(),
                    original_bytes[product_key],
                )


if __name__ == "__main__":
    unittest.main()
