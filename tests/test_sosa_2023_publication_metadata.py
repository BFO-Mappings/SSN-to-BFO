#!/usr/bin/env python3
"""Publication-metadata contract for the immutable SOSA-2023 track."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import publication_metadata as metadata  # noqa: E402
from release_context import parse_formal_release_context  # noqa: E402


TRACK_ID = "sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda"

PRODUCT_ORDER = (
    "integrated",
    "strict_bfo_mapping",
    "cco_extension",
    "ro_mapping",
)

CONFIG = (
    REPO_ROOT
    / "config/sosa-2023-publication-metadata.toml"
)

CURRENT_CONFIG = REPO_ROOT / "config/publication-metadata.toml"

CURRENT_CONFIG_SHA256 = (
    "bb818ab88d2dbcfd8a11eddcfc846c81609c4e9a9c6819def44f950da423e8f9"
)

SYNTHETIC_CONTEXT = parse_formal_release_context(
    "2099-01-02",
    "2099-01-02",
    "v2099-01-02",
    "0123456789abcdef0123456789abcdef01234567",
)


class Sosa2023PublicationMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.value = metadata.load_metadata(
            CONFIG,
            product_order=PRODUCT_ORDER,
        )
        cls.by_key = {
            product.key: product
            for product in cls.value.products
        }

    def test_exact_product_inventory(self) -> None:
        self.assertEqual(
            tuple(product.key for product in self.value.products),
            PRODUCT_ORDER,
        )
        self.assertEqual(self.value.schema_version, 4)

    def test_exact_product_paths(self) -> None:
        self.assertEqual(
            {
                key: self.by_key[key].path
                for key in PRODUCT_ORDER
            },
            {
                "integrated":
                    "releases/sosa-next/sosa-integrated.ttl",
                "strict_bfo_mapping":
                    "releases/sosa-next/sosa-bfo-mapping.ttl",
                "cco_extension":
                    "releases/sosa-next/sosa-cco-extension.ttl",
                "ro_mapping":
                    "releases/sosa-next/sosa-ro-mapping.ttl",
            },
        )

    def test_stable_ontology_iris_use_immutable_source_identity(self) -> None:
        expected = {
            "integrated":
                f"http://www.sks.ai/SSN2BFO/{TRACK_ID}/integrated",
            "strict_bfo_mapping":
                f"http://www.sks.ai/SSN2BFO/{TRACK_ID}/bfo-mapping",
            "cco_extension":
                f"http://www.sks.ai/SSN2BFO/{TRACK_ID}/cco-extension",
            "ro_mapping":
                f"http://www.sks.ai/SSN2BFO/{TRACK_ID}/ro-mapping",
        }

        observed = {
            key: self.by_key[key].stable_ontology_iri
            for key in PRODUCT_ORDER
        }

        self.assertEqual(observed, expected)

        for value in observed.values():
            self.assertNotIn("sosa-next", value)
            self.assertNotIn("/development/", value)

    def test_release_suffixes_use_immutable_source_identity(self) -> None:
        expected = {
            "integrated":
                f"{TRACK_ID}/integrated",
            "strict_bfo_mapping":
                f"{TRACK_ID}/bfo-mapping",
            "cco_extension":
                f"{TRACK_ID}/cco-extension",
            "ro_mapping":
                f"{TRACK_ID}/ro-mapping",
        }

        self.assertEqual(
            {
                key: self.by_key[key].release_iri_suffix
                for key in PRODUCT_ORDER
            },
            expected,
        )

    def test_synthetic_version_iris_are_exact(self) -> None:
        expected = {
            "integrated":
                "http://www.sks.ai/SSN2BFO/releases/"
                f"2099-01-02/{TRACK_ID}/integrated",
            "strict_bfo_mapping":
                "http://www.sks.ai/SSN2BFO/releases/"
                f"2099-01-02/{TRACK_ID}/bfo-mapping",
            "cco_extension":
                "http://www.sks.ai/SSN2BFO/releases/"
                f"2099-01-02/{TRACK_ID}/cco-extension",
            "ro_mapping":
                "http://www.sks.ai/SSN2BFO/releases/"
                f"2099-01-02/{TRACK_ID}/ro-mapping",
        }

        self.assertEqual(
            {
                key: metadata.release_version_iri(
                    self.value,
                    key,
                    SYNTHETIC_CONTEXT,
                )
                for key in PRODUCT_ORDER
            },
            expected,
        )

    def test_product_types_are_shared_role_iris(self) -> None:
        self.assertEqual(
            {
                key: self.by_key[key].product_type_iri
                for key in PRODUCT_ORDER
            },
            {
                "integrated":
                    "http://www.sks.ai/SSN2BFO/product-type/integrated",
                "strict_bfo_mapping":
                    "http://www.sks.ai/SSN2BFO/product-type/strict-bfo-mapping",
                "cco_extension":
                    "http://www.sks.ai/SSN2BFO/product-type/cco-extension",
                "ro_mapping":
                    "http://www.sks.ai/SSN2BFO/product-type/ro-mapping",
            },
        )

    def test_formal_generated_warning_avoids_development_alias(self) -> None:
        warning = self.value.publication.generated_warning
        self.assertNotIn("sosa-next", warning)
        self.assertIn("SOSA-2023", warning)

    def test_explicit_product_order_is_required_for_second_track(self) -> None:
        with self.assertRaises(metadata.PublicationMetadataError):
            metadata.load_metadata(CONFIG)

    def test_current_default_product_order_is_unchanged(self) -> None:
        current = metadata.load_metadata(CURRENT_CONFIG)

        self.assertEqual(
            tuple(product.key for product in current.products),
            metadata.PRODUCT_ORDER,
        )

    def test_current_publication_metadata_bytes_are_unchanged(self) -> None:
        observed = hashlib.sha256(
            CURRENT_CONFIG.read_bytes()
        ).hexdigest()

        self.assertEqual(
            observed,
            CURRENT_CONFIG_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
