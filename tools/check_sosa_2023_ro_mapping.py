#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from rdflib import (
    Graph,
    OWL,
    RDF,
    RDFS,
    URIRef,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(REPO_ROOT / "tools"),
)

import check_sosa_2023_ro_source_version as ro_source
import generate_sosa_2023_ro_mapping as generator


class RoProductError(
    RuntimeError
):
    pass


SOURCE_FILES = (
    "sosa.ttl",
    "sosa-common.ttl",
    "sosa-observation.ttl",
    "sosa-actuation.ttl",
    "sosa-sampling.ttl",
    "sosa-deprecated.ttl",
    "sosa-system.ttl",
    "sample-relations.ttl",
    "sosa-source-declaration-overlay.ttl",
)


def sha256_bytes(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def build_source_graph() -> Graph:
    graph = Graph()

    root = (
        REPO_ROOT
        / "src/sosa-next/imports"
    )

    for name in SOURCE_FILES:
        path = root / name

        if not path.is_file():
            raise RoProductError(
                f"missing SOSA source "
                f"input: {path}"
            )

        graph.parse(
            path
        )

    return graph


def validate_product(
    product_path: Path,
) -> dict:
    authority = ro_source.validate()

    product, active, expected = (
        generator.build()
    )

    if not product_path.is_file():
        raise RoProductError(
            f"missing RO mapping product: "
            f"{product_path}"
        )

    observed = product_path.read_bytes()

    if observed != expected:
        raise RoProductError(
            "maintained product bytes "
            "do not match governed "
            "generator output; "
            f"expected SHA-256 "
            f"{sha256_bytes(expected)}; "
            f"observed "
            f"{sha256_bytes(observed)}"
        )

    graph = Graph()
    graph.parse(
        data=observed,
        format="turtle",
    )

    expected_total = product[
        "total_triple_count"
    ]

    if len(graph) != expected_total:
        raise RoProductError(
            "product triple-count mismatch: "
            f"expected {expected_total}; "
            f"observed {len(graph)}"
        )

    ontology_iri = URIRef(
        product[
            "stable_ontology_iri"
        ]
    )

    ontology_declarations = {
        subject
        for subject in graph.subjects(
            RDF.type,
            OWL.Ontology,
        )
    }

    if ontology_declarations != {
        ontology_iri
    }:
        raise RoProductError(
            "ontology declaration differs: "
            f"{ontology_declarations!r}"
        )

    imports = set(
        graph.objects(
            ontology_iri,
            OWL.imports,
        )
    )

    if imports:
        raise RoProductError(
            "RO mapping product must be "
            "import-free; found "
            f"{sorted(map(str, imports))}"
        )

    expected_axioms = {
        (
            URIRef(
                "http://www.w3.org/ns/sosa/"
                + row.subject_text.split(
                    ":",
                    1,
                )[1]
            ),
            RDFS.subPropertyOf,
            URIRef(
                "http://purl.obolibrary.org/obo/"
                + row.target_text.replace(
                    ":",
                    "_",
                    1,
                )
            ),
        )
        for row in active
    }

    observed_axioms = {
        triple
        for triple in graph.triples(
            (
                None,
                RDFS.subPropertyOf,
                None,
            )
        )
    }

    if observed_axioms != expected_axioms:
        missing = sorted(
            expected_axioms
            - observed_axioms,
            key=lambda value:
                tuple(map(str, value)),
        )

        extra = sorted(
            observed_axioms
            - expected_axioms,
            key=lambda value:
                tuple(map(str, value)),
        )

        raise RoProductError(
            "logical mapping set differs; "
            f"missing={missing!r}; "
            f"extra={extra!r}"
        )

    if (
        len(observed_axioms)
        != product[
            "logical_triple_count"
        ]
    ):
        raise RoProductError(
            "logical triple count differs"
        )

    source_graph = (
        build_source_graph()
    )

    ro_graph = Graph()
    ro_graph.parse(
        REPO_ROOT
        / authority[
            "path"
        ]
    )

    for (
        source,
        _predicate,
        target,
    ) in sorted(
        observed_axioms,
        key=lambda value:
            tuple(map(str, value)),
    ):
        if not any(
            source_graph.triples(
                (
                    source,
                    None,
                    None,
                )
            )
        ):
            raise RoProductError(
                f"source property absent "
                f"from pinned SOSA graph: "
                f"{source}"
            )

        if not any(
            ro_graph.triples(
                (
                    target,
                    None,
                    None,
                )
            )
        ):
            raise RoProductError(
                f"target relation absent "
                f"from pinned RO graph: "
                f"{target}"
            )

    for predicate in graph.predicates():
        value = str(
            predicate
        )

        if value.startswith(
            "http://www.w3.org/"
            "2004/02/skos/core#"
        ) and value.endswith(
            (
                "Match",
                "match",
            )
        ):
            raise RoProductError(
                "SKOS mapping predicate "
                "is prohibited"
            )

    return {
        "product":
            product,
        "active":
            active,
        "bytes":
            observed,
        "graph":
            graph,
        "axioms":
            observed_axioms,
        "authority":
            authority,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the governed "
            "SOSA-2023 RO mapping product."
        )
    )

    parser.add_argument(
        "--product",
        default=(
            "releases/sosa-next/"
            "sosa-ro-mapping.ttl"
        ),
    )

    args = parser.parse_args()

    product_path = Path(
        args.product
    )

    if not product_path.is_absolute():
        product_path = (
            REPO_ROOT
            / product_path
        )

    try:
        result = validate_product(
            product_path
        )
    except (
        RoProductError,
        generator.RoGenerationError,
        ro_source.SourceVersionError,
        OSError,
        ValueError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    product = result[
        "product"
    ]

    print(
        "Product:",
        product["key"],
    )

    print(
        "Ontology IRI:",
        product[
            "stable_ontology_iri"
        ],
    )

    print(
        "Governed properties:",
        product[
            "governed_property_count"
        ],
    )

    print(
        "Active axioms:",
        len(
            result["active"]
        ),
    )

    print(
        "No direct:",
        product[
            "no_direct_mapping_count"
        ],
    )

    print(
        "Logical triples:",
        len(
            result["axioms"]
        ),
    )

    print(
        "Total triples:",
        len(
            result["graph"]
        ),
    )

    print(
        "Imports: 0"
    )

    print(
        "SKOS mappings: 0"
    )

    print(
        "SHA-256:",
        sha256_bytes(
            result["bytes"]
        ),
    )

    print(
        "RO mapping product: PASS"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
