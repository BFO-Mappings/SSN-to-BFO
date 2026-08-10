#!/usr/bin/env python3
"""Focused formal-rendering contract for the immutable SOSA-2023 track."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, OWL
from rdflib.compare import isomorphic

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import generate_sosa_next_products as products  # noqa: E402
from release_context import parse_formal_release_context  # noqa: E402


TRACK_ID = (
    "sosa-2023-"
    "af425a0454ec00512a5ebfa2873fe35a077f5fda"
)

SYNTHETIC_CONTEXT = parse_formal_release_context(
    "2099-01-02",
    "2099-01-02",
    "v2099-01-02",
    "0123456789abcdef0123456789abcdef01234567",
)

EXPECTED_TOTAL_TRIPLES = {
    "integrated": 288,
    "strict_bfo_mapping": 168,
    "cco_extension": 128,
}

EXPECTED_LOGICAL_TRIPLES = {
    "integrated": 273,
    "strict_bfo_mapping": 157,
    "cco_extension": 116,
}


FORMAL_HASHES = {
    "integrated":
        "81694ddfc0a7587c2d83517f0fc69449a25dc31ae68571b0a63f48aa5ca10aae",
    "strict_bfo_mapping":
        "c88cb347742a15fc003cafe2e167f7f784cc4a70653720c11f1e6247e6a3096c",
    "cco_extension":
        "bc356b515e29a21d74865101661fe1d81f2da33f86b31bf4c497109e8f9b202b",
}

FORMAL_BYTE_SIZES = {
    "integrated": 40785,
    "strict_bfo_mapping": 24238,
    "cco_extension": 18092,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


class Sosa2023ReleaseRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(
            prefix="sosa-2023-formal-rendering-"
        )
        cls.root = Path(cls.temporary.name)

        (
            cls.processed,
            cls.counts,
            cls.source_graph,
        ) = products.process_active_rows(
            cls.root / "source"
        )

        cls.first = products.render_formal_product_set(
            cls.processed,
            SYNTHETIC_CONTEXT,
        )

        cls.second = products.render_formal_product_set(
            cls.processed,
            SYNTHETIC_CONTEXT,
            reverse_input=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_exact_formal_product_inventory(self) -> None:
        self.assertEqual(
            tuple(self.first["products"]),
            products.PRODUCT_ORDER,
        )

    def test_synthetic_formal_bytes_are_locked(self) -> None:
        observed_hashes = {
            key: self.first["products"][key]["sha256"]
            for key in products.PRODUCT_ORDER
        }

        observed_sizes = {
            key: self.first["products"][key]["byte_size"]
            for key in products.PRODUCT_ORDER
        }

        self.assertEqual(
            observed_hashes,
            FORMAL_HASHES,
        )

        self.assertEqual(
            observed_sizes,
            FORMAL_BYTE_SIZES,
        )

    def test_exact_formal_graph_partitions(self) -> None:
        for key in products.PRODUCT_ORDER:
            with self.subTest(product=key):
                result = self.first["products"][key]

                self.assertEqual(
                    result["axiom_count"],
                    products.PRODUCT_SPECS[key][
                        "axiom_count"
                    ],
                )
                self.assertEqual(
                    result["logical_triple_count"],
                    EXPECTED_LOGICAL_TRIPLES[key],
                )
                self.assertEqual(
                    result["total_triple_count"],
                    EXPECTED_TOTAL_TRIPLES[key],
                )

    def test_exact_formal_import_contract(self) -> None:
        bfo_version = (
            "http://www.sks.ai/SSN2BFO/releases/"
            f"2099-01-02/{TRACK_ID}/bfo-mapping"
        )

        expected = {
            "integrated": (
                "http://www.w3.org/ns/sosa/",
                "http://www.w3.org/ns/sosa/systems/",
                "http://www.w3.org/ns/sosa/sampling/",
                (
                    "https://www.commoncoreontologies.org/"
                    "CommonCoreOntologiesMerged"
                ),
            ),
            "strict_bfo_mapping": (),
            "cco_extension": (bfo_version,),
        }

        observed = {
            key: self.first["products"][key]["imports"]
            for key in products.PRODUCT_ORDER
        }

        self.assertEqual(observed, expected)

    def test_source_declaration_overlay_is_not_published_import(self) -> None:
        overlay = (
            "http://www.sks.ai/SSN2BFO/development/"
            "sosa-next/source-declaration-overlay"
        )

        for key in products.PRODUCT_ORDER:
            with self.subTest(product=key):
                self.assertNotIn(
                    overlay,
                    self.first["products"][key][
                        "imports"
                    ],
                )

    def test_no_temporary_development_identity_survives(self) -> None:
        for key in products.PRODUCT_ORDER:
            with self.subTest(product=key):
                serialized = self.first["products"][key][
                    "serialized_bytes"
                ]

                self.assertNotIn(
                    b"sosa-next",
                    serialized,
                )
                self.assertNotIn(
                    b"/development/",
                    serialized,
                )

    def test_stable_and_version_iris_are_exact(self) -> None:
        expected_stable = {
            "integrated":
                f"http://www.sks.ai/SSN2BFO/{TRACK_ID}/integrated",
            "strict_bfo_mapping":
                f"http://www.sks.ai/SSN2BFO/{TRACK_ID}/bfo-mapping",
            "cco_extension":
                f"http://www.sks.ai/SSN2BFO/{TRACK_ID}/cco-extension",
        }

        expected_versions = {
            "integrated":
                "http://www.sks.ai/SSN2BFO/releases/"
                f"2099-01-02/{TRACK_ID}/integrated",
            "strict_bfo_mapping":
                "http://www.sks.ai/SSN2BFO/releases/"
                f"2099-01-02/{TRACK_ID}/bfo-mapping",
            "cco_extension":
                "http://www.sks.ai/SSN2BFO/releases/"
                f"2099-01-02/{TRACK_ID}/cco-extension",
        }

        self.assertEqual(
            {
                key: self.first["products"][key][
                    "stable_ontology_iri"
                ]
                for key in products.PRODUCT_ORDER
            },
            expected_stable,
        )

        self.assertEqual(
            {
                key: self.first["products"][key][
                    "version_iri"
                ]
                for key in products.PRODUCT_ORDER
            },
            expected_versions,
        )

    def test_formal_logical_graphs_match_development_products(self) -> None:
        for key in products.PRODUCT_ORDER:
            with self.subTest(product=key):
                development = Graph().parse(
                    products.MAINTAINED_PRODUCTS[key],
                    format="turtle",
                )

                development_logical = (
                    products.logical_graph(
                        development,
                        products.PRODUCT_SPECS[key][
                            "ontology_iri"
                        ],
                    )
                )

                formal_logical = self.first["products"][
                    key
                ]["logical_graph"]

                self.assertTrue(
                    isomorphic(
                        development_logical,
                        formal_logical,
                    )
                )

    def test_formal_modular_union_is_integrated(self) -> None:
        self.assertEqual(
            self.first[
                "combined_logical_triple_count"
            ],
            273,
        )
        self.assertTrue(
            self.first["logical_union_isomorphic"]
        )

    def test_formal_import_triples_match_contract(self) -> None:
        for key in products.PRODUCT_ORDER:
            with self.subTest(product=key):
                result = self.first["products"][key]

                graph = Graph().parse(
                    data=result["serialized_bytes"],
                    format="turtle",
                )

                observed = {
                    str(value)
                    for value in graph.objects(
                        None,
                        OWL.imports,
                    )
                }

                self.assertEqual(
                    observed,
                    set(result["imports"]),
                )

    def test_independent_renders_are_byte_identical(self) -> None:
        for key in products.PRODUCT_ORDER:
            with self.subTest(product=key):
                self.assertEqual(
                    self.first["products"][key][
                        "serialized_bytes"
                    ],
                    self.second["products"][key][
                        "serialized_bytes"
                    ],
                )

                self.assertEqual(
                    self.first["products"][key][
                        "sha256"
                    ],
                    self.second["products"][key][
                        "sha256"
                    ],
                )

    def test_renderer_does_not_change_maintained_products(self) -> None:
        expected = {
            "integrated":
                "7ce45659e4d84ac089ae90c3279fa46d169d763ec487c34cb3c533eb0e6c197c",
            "strict_bfo_mapping":
                "67bb58ea543e654ace41c0d1a393b2a3f92426c693f5100f0aa3ba35f3b005d2",
            "cco_extension":
                "e65e96f15a55e19fc43be8dbda6e56351ef40bbd6e0fa9368a240e83c5d6bb69",
        }

        self.assertEqual(
            {
                key: sha256(
                    products.MAINTAINED_PRODUCTS[key]
                )
                for key in products.PRODUCT_ORDER
            },
            expected,
        )


if __name__ == "__main__":
    unittest.main()
