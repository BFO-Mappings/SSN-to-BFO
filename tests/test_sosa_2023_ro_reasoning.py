#!/usr/bin/env python3

from __future__ import annotations

import inspect
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import (
    Graph,
    OWL,
    RDF,
    RDFS,
    URIRef,
)
from rdflib.compare import isomorphic


REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(REPO_ROOT / "tools"),
)

import generate_mapping_from_coms as coms
import modular_products as modular


PRODUCT = (
    REPO_ROOT
    / "releases/sosa-next/sosa-ro-mapping.ttl"
)

RO_SOURCE = (
    REPO_ROOT
    / "src/sosa-next/imports/ro-full.owl"
)

SOSA_2023_SOURCE_PATHS = (
    REPO_ROOT
    / "src/sosa-next/imports/sosa.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sosa-common.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sosa-observation.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sosa-actuation.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sosa-sampling.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sosa-deprecated.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sosa-system.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sample-relations.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sosa-source-declaration-overlay.ttl",
)


def annotation(
    iri: str,
):
    return (
        URIRef(iri),
        RDF.type,
        OWL.AnnotationProperty,
    )


def owl_class(
    iri: str,
):
    return (
        URIRef(iri),
        RDF.type,
        OWL.Class,
    )


# Declarations required only for ROBOT's transient OWL 2 DL
# profile-validation graph. They are not part of SOSA, RO,
# the maintained mapping product, or the exact HermiT closure.
SOSA_2023_PROFILE_DECLARATIONS = (
    annotation(
        "http://schema.org/domainIncludes"
    ),
    annotation(
        "http://schema.org/rangeIncludes"
    ),
    annotation(
        "http://www.w3.org/2004/02/skos/core#altLabel"
    ),
    annotation(
        "http://www.w3.org/2004/02/skos/core#definition"
    ),
    annotation(
        "http://www.w3.org/2004/02/skos/core#example"
    ),
    annotation(
        "http://www.w3.org/2004/02/skos/core#note"
    ),
    annotation(
        "http://www.w3.org/2004/02/skos/core#scopeNote"
    ),
    annotation(
        "http://www.w3.org/2004/02/skos/core#editorialNote"
    ),
    annotation(
        "http://www.w3.org/2004/02/skos/core#prefLabel"
    ),
    annotation(
        "http://xmlns.com/foaf/0.1/name"
    ),
    annotation(
        "http://purl.org/dc/terms/modified"
    ),
    annotation(
        "http://purl.org/dc/terms/rights"
    ),
    annotation(
        "http://purl.org/vocab/vann/preferredNamespacePrefix"
    ),
    annotation(
        "http://purl.org/vocab/vann/preferredNamespaceUri"
    ),
    owl_class(
        "http://purl.org/vocommons/voaf#Vocabulary"
    ),
    owl_class(
        "http://xmlns.com/foaf/0.1/Agent"
    ),
)


class Sosa2023RoReasoningTest(
    unittest.TestCase
):
    def test_shared_defaults_preserve_existing_contract(
        self,
    ) -> None:
        signature = inspect.signature(
            coms._run_hermit_closure
        )

        required_default = (
            signature.parameters[
                "required_source_declarations"
            ].default
        )

        additional_default = (
            signature.parameters[
                "additional_profile_declarations"
            ].default
        )

        self.assertEqual(
            required_default,
            coms.SAMPLE_PROPERTY_SOURCE_DECLARATIONS,
        )

        self.assertEqual(
            additional_default,
            (),
        )

        self.assertEqual(
            len(
                coms.DL_PROFILE_DECLARATION_COMPLETION
            ),
            4,
        )

    def test_pinned_sosa_2023_ro_closure_is_hermit_clean(
        self,
    ) -> None:
        self.assertEqual(
            len(
                SOSA_2023_PROFILE_DECLARATIONS
            ),
            16,
        )

        for path in (
            PRODUCT,
            RO_SOURCE,
            *SOSA_2023_SOURCE_PATHS,
        ):
            self.assertTrue(
                path.is_file(),
                msg=f"missing input: {path}",
            )

        with tempfile.TemporaryDirectory(
            prefix="sosa-2023-ro-hermit-"
        ) as root:
            temp = Path(root)

            ro_ttl = (
                temp
                / "ro-full.ttl"
            )

            pinned_ro = Graph()
            pinned_ro.parse(
                RO_SOURCE
            )

            self.assertEqual(
                len(pinned_ro),
                11640,
            )

            pinned_ro.serialize(
                ro_ttl,
                format="turtle",
            )

            transient_ro = Graph()
            transient_ro.parse(
                ro_ttl,
                format="turtle",
            )

            self.assertEqual(
                len(transient_ro),
                11640,
            )

            self.assertTrue(
                isomorphic(
                    pinned_ro,
                    transient_ro,
                )
            )

            closure = (
                modular.build_fixed_validation_closure(
                    (
                        PRODUCT.read_bytes(),
                    ),
                    (
                        ro_ttl,
                        *SOSA_2023_SOURCE_PATHS,
                    ),
                )
            )

            self.assertEqual(
                len(closure),
                12855,
            )

            self.assertEqual(
                set(
                    closure.triples(
                        (
                            None,
                            OWL.imports,
                            None,
                        )
                    )
                ),
                set(),
            )

            product_graph = Graph()
            product_graph.parse(
                PRODUCT,
                format="turtle",
            )

            product_axioms = set(
                product_graph.triples(
                    (
                        None,
                        RDFS.subPropertyOf,
                        None,
                    )
                )
            )

            self.assertEqual(
                len(product_axioms),
                16,
            )

            closure_axioms = set(
                closure.triples(
                    (
                        None,
                        RDFS.subPropertyOf,
                        None,
                    )
                )
            )

            self.assertTrue(
                product_axioms.issubset(
                    closure_axioms
                )
            )

            profile = coms.HermitRunProfile(
                graph_filename=(
                    "sosa-2023-ro-fixed-closure.ttl"
                ),
                reasoned_filename=(
                    "sosa-2023-ro-fixed-closure-reasoned.ttl"
                ),
            )

            result = (
                coms._run_hermit_closure(
                    PRODUCT,
                    closure,
                    temp,
                    profile,
                    required_source_declarations=(),
                    additional_profile_declarations=(
                        SOSA_2023_PROFILE_DECLARATIONS
                    ),
                )
            )

            self.assertEqual(
                result.generated_triple_count,
                18,
            )

            self.assertEqual(
                result.closure_triple_count,
                12855,
            )

            self.assertTrue(
                result.profile_checked
            )

            self.assertIs(
                result.source_sample_declarations_retained,
                True,
            )

            self.assertEqual(
                result.profile_return_code,
                0,
                msg=result.profile_output,
            )

            self.assertEqual(
                result.profile_triple_count,
                12875,
            )

            self.assertEqual(
                result.profile_declaration_completion_count,
                20,
            )

            self.assertEqual(
                result.return_code,
                0,
                msg=result.robot_output,
            )

            self.assertTrue(
                result.reasoned_output_produced
            )

            self.assertEqual(
                result.owl_nothing_count,
                0,
            )

            self.assertEqual(
                result.unsat_classes,
                [],
            )

            self.assertTrue(
                result.passed
            )

            reasoned = Graph()
            reasoned.parse(
                result.reasoned_path,
                format="turtle",
            )

            self.assertEqual(
                coms.unsat_classes(
                    reasoned
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
