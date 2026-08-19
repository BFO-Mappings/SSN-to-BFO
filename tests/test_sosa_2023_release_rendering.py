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
    "integrated": 292,
    "strict_bfo_mapping": 165,
    "cco_extension": 135,
}

EXPECTED_LOGICAL_TRIPLES = {
    "integrated": 277,
    "strict_bfo_mapping": 154,
    "cco_extension": 123,
}


FORMAL_HASHES = {
    "integrated":
        "539c07541bf20e5305fa675fa34b54899fe2bd3be31cc33c865d367b3e7dbe43",
    "strict_bfo_mapping":
        "8eadb56c78b215fb7b623dede6071b6b412e2ed7eb2a85e694a372310a700125",
    "cco_extension":
        "d3b6f3324fa2b8931760c1d743e37984d1198a124abc7c7bdcf2195370428f3d",
}

FORMAL_BYTE_SIZES = {
    "integrated": 41010,
    "strict_bfo_mapping": 23664,
    "cco_extension": 18891,
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
            277,
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
                "3f502821476478252cdd9feb316b47612daa473e511597970a1351617d5cfc12",
            "strict_bfo_mapping":
                "1ae415bc96940e4007d064102f556aa544593616a0eff984534406028b846efb",
            "cco_extension":
                "53a7cc6c0f664e51bf9f7ac28e3d067fc4fdcc750e22a34fe5c12c766e51dc19",
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
