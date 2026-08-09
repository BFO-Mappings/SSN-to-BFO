#!/usr/bin/env python3
"""End-to-end catalog consumption tests for the SOSA-next project stack."""
from __future__ import annotations

import unittest
from pathlib import Path
from xml.etree import ElementTree

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = REPO_ROOT / "src/sosa-next/catalog-v001.xml"

CATALOG_NAMESPACE = (
    "urn:oasis:names:tc:entity:xmlns:xml:catalog"
)

INTEGRATED = (
    "http://www.sks.ai/SSN2BFO/"
    "development/sosa-next/integrated"
)
BFO_MAPPING = (
    "http://www.sks.ai/SSN2BFO/"
    "development/sosa-next/bfo-mapping"
)
CCO_EXTENSION = (
    "http://www.sks.ai/SSN2BFO/"
    "development/sosa-next/cco-extension"
)
EDITOR = (
    "http://www.sks.ai/SSN2BFO/"
    "development/sosa-next/edit"
)

PROJECT_IRIS = (
    INTEGRATED,
    BFO_MAPPING,
    CCO_EXTENSION,
    EDITOR,
)

EXPECTED_PROJECT_PATHS = {
    INTEGRATED: (
        REPO_ROOT
        / "releases/sosa-next/sosa-integrated.ttl"
    ),
    BFO_MAPPING: (
        REPO_ROOT
        / "releases/sosa-next/sosa-bfo-mapping.ttl"
    ),
    CCO_EXTENSION: (
        REPO_ROOT
        / "releases/sosa-next/sosa-cco-extension.ttl"
    ),
    EDITOR: (
        REPO_ROOT
        / "src/sosa-next/sosa-mappings-edit.ttl"
    ),
}

EXPECTED_INTEGRATED_IMPORTS = frozenset(
    {
        "http://www.w3.org/ns/sosa/",
        "http://www.w3.org/ns/sosa/systems/",
        "http://www.w3.org/ns/sosa/sampling/",
        (
            "http://www.sks.ai/SSN2BFO/"
            "development/sosa-next/"
            "source-declaration-overlay"
        ),
        (
            "https://www.commoncoreontologies.org/"
            "CommonCoreOntologiesMerged"
        ),
    }
)

EXPECTED_IMPORTS = {
    INTEGRATED: EXPECTED_INTEGRATED_IMPORTS,
    BFO_MAPPING: frozenset(),
    CCO_EXTENSION: frozenset({BFO_MAPPING}),
    EDITOR: frozenset({INTEGRATED}),
}

EXPECTED_TRIPLE_COUNTS = {
    INTEGRATED: 286,
    BFO_MAPPING: 165,
    CCO_EXTENSION: 125,
    EDITOR: 4,
}

EXPECTED_EDITOR_CLOSURE = (
    EDITOR,
    INTEGRATED,
)

EXPECTED_DEPENDENCY_IRIS = frozenset(
    {
        "http://www.w3.org/ns/sosa/",
        "http://www.w3.org/ns/sosa/common/",
        "http://www.w3.org/ns/sosa/act/",
        "http://www.w3.org/ns/sosa/dep/",
        "http://www.w3.org/ns/sosa/obs/",
        "http://www.w3.org/ns/sosa/sam/",
        "http://www.w3.org/ns/sosa/systems/",
        "http://www.w3.org/ns/sosa/sampling/",
        (
            "http://www.sks.ai/SSN2BFO/"
            "development/sosa-next/"
            "source-declaration-overlay"
        ),
        (
            "https://www.commoncoreontologies.org/"
            "CommonCoreOntologiesMerged"
        ),
    }
)


def load_catalog() -> tuple[
    tuple[tuple[str, str], ...],
    dict[str, Path],
]:
    root = ElementTree.parse(CATALOG).getroot()

    entries = tuple(
        (
            element.attrib["name"],
            element.attrib["uri"],
        )
        for element in root.findall(
            f".//{{{CATALOG_NAMESPACE}}}uri"
        )
    )

    resolved = {
        name: (CATALOG.parent / relative).resolve()
        for name, relative in entries
    }

    return entries, resolved


def load_project_graphs(
    catalog: dict[str, Path],
) -> dict[str, Graph]:
    graphs: dict[str, Graph] = {}

    for ontology_iri in PROJECT_IRIS:
        graph = Graph()
        graph.parse(
            catalog[ontology_iri],
            format="turtle",
        )
        graphs[ontology_iri] = graph

    return graphs


class SosaNextConsumerStackTests(unittest.TestCase):
    def test_catalog_entries_are_unique_local_and_parseable(
        self,
    ) -> None:
        entries, catalog = load_catalog()

        self.assertEqual(len(entries), 14)
        self.assertEqual(len(catalog), 14)

        for public_iri, target in catalog.items():
            with self.subTest(public_iri=public_iri):
                self.assertTrue(
                    target.is_file(),
                    target,
                )

                target.relative_to(
                    REPO_ROOT.resolve()
                )

                graph = Graph()
                graph.parse(
                    target,
                    format="turtle",
                )

                self.assertGreater(
                    len(graph),
                    0,
                    target,
                )

    def test_editor_resolves_exact_project_stack(
        self,
    ) -> None:
        _, catalog = load_catalog()

        self.assertEqual(
            {
                ontology_iri: catalog[ontology_iri]
                for ontology_iri in PROJECT_IRIS
            },
            {
                ontology_iri: path.resolve()
                for ontology_iri, path
                in EXPECTED_PROJECT_PATHS.items()
            },
        )

        graphs = load_project_graphs(catalog)

        for ontology_iri, graph in graphs.items():
            with self.subTest(
                ontology_iri=ontology_iri
            ):
                ontology = URIRef(ontology_iri)

                ontology_declarations = set(
                    graph.triples(
                        (
                            None,
                            RDF.type,
                            OWL.Ontology,
                        )
                    )
                )

                self.assertEqual(
                    ontology_declarations,
                    {
                        (
                            ontology,
                            RDF.type,
                            OWL.Ontology,
                        )
                    },
                )

                import_triples = set(
                    graph.triples(
                        (
                            None,
                            OWL.imports,
                            None,
                        )
                    )
                )

                self.assertEqual(
                    import_triples,
                    {
                        (
                            ontology,
                            OWL.imports,
                            URIRef(imported),
                        )
                        for imported in EXPECTED_IMPORTS[
                            ontology_iri
                        ]
                    },
                )

                self.assertEqual(
                    len(graph),
                    EXPECTED_TRIPLE_COUNTS[
                        ontology_iri
                    ],
                )

        pending = [EDITOR]
        closure: list[str] = []

        while pending:
            ontology_iri = pending.pop(0)

            if ontology_iri in closure:
                continue

            closure.append(ontology_iri)

            pending.extend(
                sorted(
                    str(imported)
                    for imported in graphs[
                        ontology_iri
                    ].objects(
                        URIRef(ontology_iri),
                        OWL.imports,
                    )
                    if str(imported) in PROJECT_IRIS
                )
            )

        self.assertEqual(
            tuple(closure),
            EXPECTED_EDITOR_CLOSURE,
        )

        combined = Graph()

        for ontology_iri in closure:
            for triple in graphs[ontology_iri]:
                combined.add(triple)

        self.assertEqual(len(combined), 290)

    def test_external_dependencies_remain_separate_inputs(
        self,
    ) -> None:
        _, catalog = load_catalog()

        self.assertEqual(
            frozenset(catalog) - frozenset(PROJECT_IRIS),
            EXPECTED_DEPENDENCY_IRIS,
        )

        graphs = load_project_graphs(catalog)

        observed_integrated_imports = frozenset(
            str(imported)
            for imported in graphs[
                INTEGRATED
            ].objects(
                URIRef(INTEGRATED),
                OWL.imports,
            )
        )

        self.assertEqual(
            observed_integrated_imports,
            EXPECTED_INTEGRATED_IMPORTS,
        )
        self.assertTrue(
            observed_integrated_imports
            <= EXPECTED_DEPENDENCY_IRIS
        )

        observed_modular_imports = frozenset(
            str(imported)
            for ontology_iri in (
                BFO_MAPPING,
                CCO_EXTENSION,
            )
            for imported in graphs[
                ontology_iri
            ].objects(
                URIRef(ontology_iri),
                OWL.imports,
            )
        )

        self.assertTrue(
            observed_modular_imports
            <= frozenset(PROJECT_IRIS)
        )
        self.assertTrue(
            observed_modular_imports
            .isdisjoint(EXPECTED_DEPENDENCY_IRIS)
        )


if __name__ == "__main__":
    unittest.main()
