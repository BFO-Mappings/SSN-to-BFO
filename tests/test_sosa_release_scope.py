#!/usr/bin/env python3
"""Focused tests for the SOSA formal-package scope authority."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_sosa_release_scope as checker  # noqa: E402
import sosa_release_scope as release_scope  # noqa: E402
import sosa_source_version as source_version  # noqa: E402


class SosaReleaseScopeTests(unittest.TestCase):
    def test_approved_scope_is_separate_three_product_package(
        self,
    ) -> None:
        scope = release_scope.load_release_scope()
        source = source_version.load_source_version_authority()

        self.assertEqual(scope.schema_version, 1)
        self.assertEqual(scope.status, "approved")
        self.assertEqual(
            scope.source_identity,
            source.source_identity,
        )
        self.assertEqual(
            scope.development_alias,
            "sosa-next",
        )
        self.assertEqual(
            scope.publication_model,
            "separate_package",
        )
        self.assertEqual(
            scope.formal_track_component,
            source.source_identity,
        )
        self.assertEqual(
            scope.product_order,
            (
                "alignment_core",
                "strict_bfo_mapping",
                "cco_extension",
            ),
        )
        self.assertFalse(scope.integrated_product)
        self.assertFalse(scope.bfo_projection_product)
        self.assertEqual(
            scope.current_track_formal_release,
            "unchanged",
        )

    def test_checker_reports_approved_scope(self) -> None:
        summary = checker.run_check()

        self.assertTrue(summary["passed"])
        self.assertEqual(
            summary["publication_model"],
            "separate_package",
        )
        self.assertEqual(
            summary["product_order"],
            (
                "alignment_core",
                "strict_bfo_mapping",
                "cco_extension",
            ),
        )

    def test_combined_package_is_rejected(self) -> None:
        original = release_scope.CONFIG_PATH.read_text(
            encoding="utf-8"
        )
        altered = original.replace(
            'publication_model = "separate_package"',
            'publication_model = "combined_package"',
            1,
        )
        self.assertNotEqual(original, altered)

        with tempfile.TemporaryDirectory(
            prefix="sosa-release-scope-test-"
        ) as directory:
            config_path = Path(directory) / "scope.toml"
            config_path.write_text(altered, encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "approved model",
            ):
                release_scope.load_release_scope(config_path)

    def test_public_label_key_is_rejected(self) -> None:
        original = release_scope.CONFIG_PATH.read_text(
            encoding="utf-8"
        )
        altered = original.replace(
            '"strict_bfo_mapping"',
            '"bfo_mapping"',
            1,
        )
        self.assertNotEqual(original, altered)

        with tempfile.TemporaryDirectory(
            prefix="sosa-release-scope-test-"
        ) as directory:
            config_path = Path(directory) / "scope.toml"
            config_path.write_text(altered, encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "approved order",
            ):
                release_scope.load_release_scope(config_path)

    def test_extra_formal_product_is_rejected(self) -> None:
        original = release_scope.CONFIG_PATH.read_text(
            encoding="utf-8"
        )
        altered = original.replace(
            'product_order = ["alignment_core", "strict_bfo_mapping", "cco_extension"]',
            'product_order = ["alignment_core", "strict_bfo_mapping", "cco_extension", "integrated"]',
            1,
        )
        self.assertNotEqual(original, altered)

        with tempfile.TemporaryDirectory(
            prefix="sosa-release-scope-test-"
        ) as directory:
            config_path = Path(directory) / "scope.toml"
            config_path.write_text(altered, encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "approved order",
            ):
                release_scope.load_release_scope(config_path)

    def test_source_identity_mismatch_is_rejected(self) -> None:
        original = release_scope.CONFIG_PATH.read_text(
            encoding="utf-8"
        )
        altered = original.replace(
            'source_identity = "sosa-2023-',
            'source_identity = "wrong-',
            1,
        )
        self.assertNotEqual(original, altered)

        with tempfile.TemporaryDirectory(
            prefix="sosa-release-scope-test-"
        ) as directory:
            config_path = Path(directory) / "scope.toml"
            config_path.write_text(altered, encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "must equal the approved SOSA source-version identity",
            ):
                release_scope.load_release_scope(config_path)


if __name__ == "__main__":
    unittest.main()
