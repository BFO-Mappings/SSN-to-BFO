#!/usr/bin/env python3
"""Explicit-input regressions for SOSA-2023 RO formal rendering."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

sys.path.insert(
    0,
    str(REPO_ROOT / "tools"),
)

import generate_sosa_2023_ro_mapping as ro  # noqa: E402
import generate_sosa_next_products as products  # noqa: E402


class Sosa2023RoExplicitPathTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.config = (
            REPO_ROOT
            / "config/"
              "sosa-2023-ro-product.toml"
        )

        self.workbook = (
            REPO_ROOT
            / "mappings/"
              "SOSA-next-to-RO-COMS.xlsx"
        )

    def test_explicit_config_and_workbook_are_authoritative(
        self,
    ) -> None:
        canonical_product, canonical_active, canonical_rendered = (
            ro.build()
        )

        with tempfile.TemporaryDirectory(
            prefix="sosa-2023-ro-explicit-"
        ) as directory:
            root = Path(directory)

            config = (
                root
                / "ro-product.toml"
            )

            workbook = (
                root
                / "ro-coms.xlsx"
            )

            workbook.write_bytes(
                self.workbook.read_bytes()
            )

            altered = (
                self.config
                .read_text(
                    encoding="utf-8"
                )
                .replace(
                    'workbook_path = '
                    '"mappings/'
                    'SOSA-next-to-RO-COMS.xlsx"',
                    'workbook_path = '
                    '"INTENTIONALLY-ABSENT.xlsx"',
                    1,
                )
                .replace(
                    'output_path = '
                    '"releases/sosa-next/'
                    'sosa-ro-mapping.ttl"',
                    'output_path = '
                    '"sentinel/'
                    'explicit-path.ttl"',
                    1,
                )
            )

            config.write_text(
                altered,
                encoding="utf-8",
            )

            self.assertIn(
                "INTENTIONALLY-ABSENT.xlsx",
                altered,
            )

            self.assertIn(
                "sentinel/explicit-path.ttl",
                altered,
            )

            with mock.patch.object(
                ro,
                "CONFIG_PATH",
                root
                / "DEFAULT-CONFIG-MUST-NOT-BE-READ.toml",
            ):
                product, active, rendered = (
                    ro.build(
                        config_path=config,
                        workbook_path=workbook,
                    )
                )

                body = (
                    products
                    .formal_ro_body_bytes(
                        ro_product_config_path=(
                            config
                        ),
                        ro_workbook_path=(
                            workbook
                        ),
                    )
                )

            self.assertEqual(
                product["output_path"],
                "sentinel/explicit-path.ttl",
            )

            self.assertEqual(
                product["key"],
                canonical_product["key"],
            )

            self.assertEqual(
                len(active),
                len(canonical_active),
            )

            self.assertEqual(
                len(active),
                16,
            )

            self.assertEqual(
                rendered,
                canonical_rendered,
            )

            self.assertEqual(
                body,
                products
                .formal_ro_body_bytes(),
            )

    def test_default_development_api_is_preserved(
        self,
    ) -> None:
        product, active, rendered = (
            ro.build()
        )

        self.assertEqual(
            product["key"],
            "ro_mapping",
        )

        self.assertEqual(
            len(active),
            16,
        )

        self.assertTrue(
            rendered
        )


if __name__ == "__main__":
    unittest.main()
