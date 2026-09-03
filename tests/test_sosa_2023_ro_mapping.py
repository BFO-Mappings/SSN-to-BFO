#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from rdflib import (
    Graph,
    OWL,
    RDF,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

CONFIG = (
    REPO_ROOT
    / "config/sosa-2023-ro-product.toml"
)

GENERATOR = (
    REPO_ROOT
    / "tools/generate_sosa_2023_ro_mapping.py"
)

CHECKER = (
    REPO_ROOT
    / "tools/check_sosa_2023_ro_mapping.py"
)

PRODUCT = (
    REPO_ROOT
    / "releases/sosa-next/sosa-ro-mapping.ttl"
)


class Sosa2023RoMappingTest(
    unittest.TestCase
):
    def test_product_contract(
        self,
    ) -> None:
        with CONFIG.open(
            "rb"
        ) as handle:
            data = tomllib.load(
                handle
            )

        product = data[
            "product"
        ]

        self.assertEqual(
            product["key"],
            "ro_mapping",
        )

        self.assertEqual(
            product[
                "governed_property_count"
            ],
            82,
        )

        self.assertEqual(
            product[
                "active_axiom_count"
            ],
            16,
        )

        self.assertEqual(
            product[
                "no_direct_mapping_count"
            ],
            66,
        )

        self.assertEqual(
            product[
                "import_count"
            ],
            0,
        )

        self.assertEqual(
            product[
                "total_triple_count"
            ],
            18,
        )

    def test_generator_is_reproducible(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as root:
            output = (
                Path(root)
                / "ro.ttl"
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(GENERATOR),
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=(
                    result.stdout
                    + result.stderr
                ),
            )

            self.assertEqual(
                output.read_bytes(),
                PRODUCT.read_bytes(),
            )

    def test_checker_passes(
        self,
    ) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(CHECKER),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=(
                result.stdout
                + result.stderr
            ),
        )

        self.assertIn(
            "RO mapping product: PASS",
            result.stdout,
        )

    def test_product_is_import_free(
        self,
    ) -> None:
        graph = Graph()
        graph.parse(
            PRODUCT
        )

        ontology_iris = list(
            graph.subjects(
                RDF.type,
                OWL.Ontology,
            )
        )

        self.assertEqual(
            len(
                set(
                    ontology_iris
                )
            ),
            1,
        )

        ontology = (
            ontology_iris[0]
        )

        self.assertEqual(
            list(
                graph.objects(
                    ontology,
                    OWL.imports,
                )
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
