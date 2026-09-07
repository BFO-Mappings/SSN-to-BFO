#!/usr/bin/env python3
"""Focused tests for the SOSA formal package-scope authority."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sosa_release_scope as scope  # noqa: E402
import sosa_source_version as source_version  # noqa: E402


class SosaReleaseScopeTests(unittest.TestCase):
    def test_scope_uses_uniform_product_role_policy(self) -> None:
        value = scope.load_release_scope()
        source = source_version.load_source_version_authority()

        self.assertEqual(value.schema_version, 2)
        self.assertEqual(value.status, "approved")
        self.assertEqual(value.source_identity, source.source_identity)
        self.assertEqual(value.publication_model, "separate_package")
        self.assertEqual(
            value.product_role_policy,
            "config/product-role-policy.toml",
        )
        self.assertEqual(
            value.formal_product_order,
            (
                "integrated",
                "strict_bfo_mapping",
                "cco_extension",
                "ro_mapping",
            ),
        )
        self.assertEqual(
            value.omitted_product_roles,
            (
                "alignment_core",
                "bfo_projection",
            ),
        )
        self.assertEqual(
            value.current_track_formal_release,
            "product_role_policy_migration_complete",
        )

    def test_old_three_product_inventory_is_rejected(self) -> None:
        original = scope.CONFIG_PATH.read_text(encoding="utf-8")
        altered = original.replace(
            'formal_product_order = ["integrated", "strict_bfo_mapping", "cco_extension", "ro_mapping"]',
            'formal_product_order = ["integrated", "strict_bfo_mapping", "cco_extension"]',
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
                "must equal product-role policy",
            ):
                scope.load_release_scope(config_path)

    def test_combined_package_remains_rejected(self) -> None:
        original = scope.CONFIG_PATH.read_text(encoding="utf-8")
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
                "separate package decision remains approved",
            ):
                scope.load_release_scope(config_path)


if __name__ == "__main__":
    unittest.main()
