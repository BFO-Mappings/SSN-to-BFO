#!/usr/bin/env python3
"""Focused tests for the uniform ontology product-role policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import product_role_policy as policy  # noqa: E402
import sosa_source_version as source_version  # noqa: E402


class ProductRolePolicyTests(unittest.TestCase):
    def test_uniform_six_role_taxonomy(self) -> None:
        value = policy.load_product_role_policy()

        self.assertEqual(
            value.role_order,
            (
                "integrated",
                "alignment_core",
                "strict_bfo_mapping",
                "bfo_projection",
                "cco_extension",
                "ro_mapping",
            ),
        )
        self.assertFalse(value.empty_role_boundary_is_sufficient)

    def test_current_track_target_inventory(self) -> None:
        value = policy.load_product_role_policy()
        track = value.track("current-ssn-sosa")

        self.assertEqual(
            track.formal_product_order,
            (
                "integrated",
                "alignment_core",
                "strict_bfo_mapping",
                "cco_extension",
            ),
        )
        self.assertEqual(
            track.omitted_product_roles,
            (
                "bfo_projection",
                "ro_mapping",
            ),
        )

    def test_sosa_source_version_target_inventory(self) -> None:
        value = policy.load_product_role_policy()
        source = source_version.load_source_version_authority()
        track = value.track(source.source_identity)

        self.assertEqual(
            track.formal_product_order,
            (
                "integrated",
                "strict_bfo_mapping",
                "cco_extension",
                "ro_mapping",
            ),
        )
        self.assertEqual(
            track.omitted_product_roles,
            (
                "alignment_core",
                "bfo_projection",
            ),
        )

    def test_empty_boundary_cannot_be_approved(self) -> None:
        original = policy.CONFIG_PATH.read_text(encoding="utf-8")
        altered = original.replace(
            "empty_role_boundary_is_sufficient = false",
            "empty_role_boundary_is_sufficient = true",
            1,
        )
        self.assertNotEqual(original, altered)

        with tempfile.TemporaryDirectory(
            prefix="product-role-policy-test-"
        ) as directory:
            config_path = Path(directory) / "policy.toml"
            config_path.write_text(altered, encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "empty role boundaries",
            ):
                policy.load_product_role_policy(config_path)

    def test_materialized_order_must_follow_role_status(self) -> None:
        original = policy.CONFIG_PATH.read_text(encoding="utf-8")
        altered = original.replace(
            'formal_product_order = ["integrated", "strict_bfo_mapping", "cco_extension", "ro_mapping"]',
            'formal_product_order = ["integrated", "alignment_core", "strict_bfo_mapping", "cco_extension", "ro_mapping"]',
            1,
        )
        self.assertNotEqual(original, altered)

        with tempfile.TemporaryDirectory(
            prefix="product-role-policy-test-"
        ) as directory:
            config_path = Path(directory) / "policy.toml"
            config_path.write_text(altered, encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "does not match materialization statuses",
            ):
                policy.load_product_role_policy(config_path)


if __name__ == "__main__":
    unittest.main()
