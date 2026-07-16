#!/usr/bin/env python3
"""Focused tests for governed publication metadata and release identity."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from dataclasses import FrozenInstanceError
from pathlib import Path

from rdflib import Graph, Literal, RDF, RDFS, OWL, URIRef
from rdflib.compare import isomorphic


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_publication_metadata as checker  # noqa: E402
import generate_mapping_from_coms as coms  # noqa: E402
import modular_products as modular  # noqa: E402
import publication_metadata as metadata  # noqa: E402
from release_context import parse_formal_release_context  # noqa: E402


ACTUAL_CONFIG = REPO_ROOT / "config/publication-metadata.toml"
RELEASE_BASE = "http://www.sks.ai/SSN2BFO/releases"
PUBLICATION_VALUES = {
    "project_title": "SSN-to-BFO",
    "default_language": "en",
    "release_iri_base": RELEASE_BASE,
    "license_iri": "https://creativecommons.org/publicdomain/zero/1.0/",
    "repository_iri": "https://github.com/BFO-Mappings/SSN-to-BFO",
    "generated_warning": (
        "Generated from governed COMS and publication metadata; "
        "do not edit this ontology directly."
    ),
    "development_status_property_iri": "http://www.w3.org/ns/adms#status",
    "development_status_iri": (
        "http://www.sks.ai/SSN2BFO/authority-status/"
        "maintained-authoritative-development"
    ),
    "formal_release_status_iri": (
        "http://www.sks.ai/SSN2BFO/authority-status/"
        "immutable-authoritative-release"
    ),
}
POLICY_PRODUCTS = {
    "integrated": {
        "path": "SSN2BFO.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/",
        "release_iri_suffix": "integrated",
        "label": "SSN-to-BFO Integrated Mapping",
        "description": (
            "Directly asserts the complete governed COMS axiom set for the "
            "SSN/SOSA alignment with BFO and CCO."
        ),
        "product_type_iri": "http://www.sks.ai/SSN2BFO/product-type/integrated",
    },
    "alignment_core": {
        "path": "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core",
        "release_iri_suffix": "current-ssn-sosa/alignment-core",
        "label": "SSN/SOSA Alignment Core",
        "description": (
            "Directly asserts the governed target-neutral SSN/SOSA alignment axioms "
            "shared by the modular products and imports no ontology."
        ),
        "product_type_iri": "http://www.sks.ai/SSN2BFO/product-type/alignment-core",
    },
    "strict_bfo_mapping": {
        "path": "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping",
        "release_iri_suffix": "current-ssn-sosa/bfo-mapping",
        "label": "SSN/SOSA Strict BFO Mapping",
        "description": (
            "Directly asserts governed BFO-bearing axioms without weakening and "
            "imports the SSN/SOSA alignment core."
        ),
        "product_type_iri": "http://www.sks.ai/SSN2BFO/product-type/strict-bfo-mapping",
    },
    "bfo_projection": {
        "path": "releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-projection",
        "release_iri_suffix": "current-ssn-sosa/bfo-projection",
        "label": "SSN/SOSA BFO Projection",
        "description": (
            "Imports the strict BFO mapping and is the designated product for approved "
            "weaker but sound BFO consequences; no direct projection axiom is currently "
            "approved."
        ),
        "product_type_iri": "http://www.sks.ai/SSN2BFO/product-type/bfo-projection",
    },
    "cco_extension": {
        "path": "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension",
        "release_iri_suffix": "current-ssn-sosa/cco-extension",
        "label": "SSN/SOSA CCO Extension",
        "description": (
            "Directly asserts governed CCO-bearing and mixed BFO/CCO axioms unchanged "
            "and imports the strict BFO mapping."
        ),
        "product_type_iri": "http://www.sks.ai/SSN2BFO/product-type/cco-extension",
    },
}


def render_toml(
    *,
    product_order: tuple[str, ...] = metadata.PRODUCT_ORDER,
    omit_products: frozenset[str] = frozenset(),
    omit_fields: frozenset[tuple[str, str]] = frozenset(),
    omit_publication_fields: frozenset[str] = frozenset(),
    raw_overrides: dict[tuple[str, str], str] | None = None,
    publication_raw_overrides: dict[str, str] | None = None,
    release_base_raw: str | None = None,
    schema_raw: str = "3",
) -> str:
    overrides = raw_overrides or {}
    publication_overrides = publication_raw_overrides or {}
    if release_base_raw is not None:
        publication_overrides["release_iri_base"] = release_base_raw
    lines = [f"schema_version = {schema_raw}", "", "[publication]"]
    for field in metadata.PUBLICATION_FIELDS:
        if field in omit_publication_fields:
            continue
        raw = publication_overrides.get(field, json.dumps(PUBLICATION_VALUES[field], ensure_ascii=False))
        lines.append(f"{field} = {raw}")
    for key in product_order:
        if key in omit_products:
            continue
        values = POLICY_PRODUCTS.get(
            key,
            {
                "path": f"releases/{key}.ttl",
                "stable_ontology_iri": f"http://example.org/{key}",
                "release_iri_suffix": key,
                "label": f"Synthetic {key}",
                "description": f"Synthetic description for {key}.",
                "product_type_iri": f"http://example.org/product-type/{key}",
            },
        )
        lines.extend(["", f"[products.{key}]"])
        for field in metadata.PRODUCT_FIELDS:
            if (key, field) in omit_fields:
                continue
            raw = overrides.get((key, field), json.dumps(values[field], ensure_ascii=False))
            lines.append(f"{field} = {raw}")
    return "\n".join(lines) + "\n"


class MetadataTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="publication-metadata-test-")
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def write(self, content: str, name: str = "metadata.toml") -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def error_for(self, content: str) -> metadata.PublicationMetadataError:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.load_metadata(self.write(content))
        return raised.exception

    def assert_issue(self, content: str, code: str, field: str | None = None) -> None:
        error = self.error_for(content)
        matches = [issue for issue in error.issues if issue.code == code]
        self.assertTrue(matches, [issue.code for issue in error.issues])
        if field is not None:
            self.assertIn(field, [issue.field for issue in matches])


class ConfigurationTests(MetadataTestCase):
    def test_actual_repository_config_passes(self) -> None:
        loaded = metadata.load_metadata(ACTUAL_CONFIG)
        self.assertEqual(loaded.schema_version, 3)
        self.assertEqual(tuple(product.key for product in loaded.products), metadata.PRODUCT_ORDER)

    def test_minimal_complete_schema_3_document_passes(self) -> None:
        loaded = metadata.load_metadata(self.write(render_toml()))
        self.assertEqual(loaded.schema_version, 3)
        self.assertEqual(len(loaded.products), 5)

    def test_actual_config_is_locked_to_approved_policy_values(self) -> None:
        loaded = metadata.load_metadata(ACTUAL_CONFIG)
        observed_publication = {
            field: getattr(loaded.publication, field)
            for field in metadata.PUBLICATION_FIELDS
        }
        self.assertEqual(observed_publication, PUBLICATION_VALUES)
        self.assertEqual(loaded.release_iri_base, RELEASE_BASE)
        observed = {
            product.key: {
                field: getattr(product, field)
                for field in metadata.PRODUCT_FIELDS
            }
            for product in loaded.products
        }
        self.assertEqual(observed, POLICY_PRODUCTS)

    def test_actual_config_has_no_deferred_tables_or_fields(self) -> None:
        text = ACTUAL_CONFIG.read_text(encoding="utf-8")
        for prohibited in (
            "agent",
            "creator",
            "contributor",
            "dependency",
            "provenance",
            "wasDerivedFrom",
            "release_identifier",
            "release_date",
            "git_tag",
            "commit",
            "sha256",
            "versionIRI",
            "versionInfo",
            "issued",
        ):
            self.assertNotIn(prohibited, text)

    def test_malformed_toml(self) -> None:
        self.assert_issue("schema_version =\n", "TOML_PARSE")

    def test_missing_top_level_field(self) -> None:
        content = render_toml().replace("schema_version = 3\n\n", "")
        self.assert_issue(content, "MISSING_FIELD", "metadata.schema_version")

    def test_unknown_top_level_field(self) -> None:
        content = render_toml().replace(
            "schema_version = 3\n",
            "schema_version = 3\nunknown = true\n",
        )
        self.assert_issue(content, "UNKNOWN_FIELD", "metadata.unknown")

    def test_unknown_publication_field(self) -> None:
        content = render_toml().replace(
            "[publication]\n",
            "[publication]\nunknown = true\n",
        )
        self.assert_issue(content, "UNKNOWN_FIELD", "publication.unknown")

    def test_missing_publication_table(self) -> None:
        content = render_toml()
        start = content.index("[publication]\n")
        end = content.index("\n[products.integrated]")
        self.assert_issue(
            content[:start] + content[end + 1 :],
            "MISSING_FIELD",
            "metadata.publication",
        )

    def test_missing_publication_field(self) -> None:
        self.assert_issue(
            render_toml(omit_publication_fields=frozenset({"license_iri"})),
            "MISSING_FIELD",
            "publication.license_iri",
        )

    def test_missing_product(self) -> None:
        self.assert_issue(
            render_toml(omit_products=frozenset({"bfo_projection"})),
            "MISSING_FIELD",
            "products.bfo_projection",
        )

    def test_extra_product(self) -> None:
        self.assert_issue(
            render_toml(product_order=metadata.PRODUCT_ORDER + ("extra",)),
            "UNKNOWN_FIELD",
            "products.extra",
        )

    def test_unknown_product_field(self) -> None:
        content = render_toml().replace(
            '[products.integrated]\n',
            '[products.integrated]\nunknown = "value"\n',
        )
        self.assert_issue(content, "UNKNOWN_FIELD", "products.integrated.unknown")

    def test_missing_product_field(self) -> None:
        self.assert_issue(
            render_toml(omit_fields=frozenset({("integrated", "path")})),
            "MISSING_FIELD",
            "products.integrated.path",
        )

    def test_empty_string(self) -> None:
        self.assert_issue(
            render_toml(raw_overrides={("integrated", "path"): '""'}),
            "EMPTY_STRING",
            "products.integrated.path",
        )

    def test_wrong_type(self) -> None:
        self.assert_issue(
            render_toml(raw_overrides={("integrated", "path"): "17"}),
            "WRONG_TYPE",
            "products.integrated.path",
        )

    def test_boolean_schema_version_is_rejected(self) -> None:
        self.assert_issue(render_toml(schema_raw="true"), "WRONG_TYPE", "schema_version")

    def test_prior_and_unknown_schema_are_rejected(self) -> None:
        for value in ("1", "2", "4"):
            with self.subTest(value=value):
                self.assert_issue(
                    render_toml(schema_raw=value),
                    "SCHEMA_VERSION",
                    "schema_version",
                )

    def test_reordered_product_tables_are_rejected(self) -> None:
        self.assert_issue(
            render_toml(product_order=tuple(reversed(metadata.PRODUCT_ORDER))),
            "PRODUCT_ORDER",
            "products",
        )

    def test_canonical_product_order_is_deterministic(self) -> None:
        first = metadata.load_metadata(self.write(render_toml(), "first.toml"))
        second = metadata.load_metadata(self.write(render_toml(), "second.toml"))
        self.assertEqual(first, second)
        self.assertEqual(tuple(product.key for product in first.products), metadata.PRODUCT_ORDER)


class OntologyMetadataEmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loaded = metadata.load_metadata(ACTUAL_CONFIG)

    def graph_for(self, product_key: str, imports: tuple[str, ...] = ()) -> Graph:
        product = next(value for value in self.loaded.products if value.key == product_key)
        ontology = URIRef(product.stable_ontology_iri)
        graph = Graph()
        graph.add((ontology, RDF.type, OWL.Ontology))
        for imported in imports:
            graph.add((ontology, OWL.imports, URIRef(imported)))
        for triple in metadata.ontology_metadata_rdf_triples(self.loaded, product_key):
            graph.add(triple)
        return graph

    @staticmethod
    def serialization_parameters(product_key: str):
        if product_key == "integrated":
            return (
                coms.ROOT_ORDERED_IMPORTS,
                coms.GENERATED_NOTICE,
                coms.ROOT_PREFIXES,
                coms.ROOT_IMPORT_TURTLE_TERMS,
            )
        imports = {
            "alignment_core": (),
            "strict_bfo_mapping": (modular.ALIGNMENT_CORE_IMPORT_IRI,),
            "bfo_projection": (modular.STRICT_BFO_IMPORT_IRI,),
            "cco_extension": (modular.STRICT_BFO_IMPORT_IRI,),
        }[product_key]
        prefixes = {
            "alignment_core": modular.PREFIXES,
            "strict_bfo_mapping": modular.STRICT_BFO_PREFIXES,
            "bfo_projection": modular.BFO_PROJECTION_PREFIXES,
            "cco_extension": modular.CCO_EXTENSION_PREFIXES,
        }[product_key]
        return imports, modular.GENERATED_NOTICE, prefixes, None

    def serialized_issues(self, value: bytes, product_key: str):
        imports, notice, prefixes, import_terms = self.serialization_parameters(product_key)
        return metadata.validate_serialized_ontology_header(
            value,
            self.loaded,
            product_key,
            imports,
            generated_notice=notice,
            prefixes=prefixes,
            import_turtle_terms=import_terms,
        )

    def test_exact_ordered_seven_metadata_triples_for_every_product(self) -> None:
        expected_predicates = (
            str(RDFS.label),
            metadata.DCTERMS_NAMESPACE + "description",
            metadata.DCTERMS_NAMESPACE + "type",
            PUBLICATION_VALUES["development_status_property_iri"],
            metadata.DCTERMS_NAMESPACE + "license",
            str(RDFS.seeAlso),
            str(RDFS.comment),
        )
        expected_kinds = (
            metadata.LANGUAGE_LITERAL,
            metadata.LANGUAGE_LITERAL,
            metadata.IRI_OBJECT,
            metadata.IRI_OBJECT,
            metadata.IRI_OBJECT,
            metadata.IRI_OBJECT,
            metadata.LANGUAGE_LITERAL,
        )
        for product in self.loaded.products:
            with self.subTest(product=product.key):
                values = metadata.ontology_metadata_triples(self.loaded, product.key)
                self.assertIsInstance(values, tuple)
                self.assertEqual(len(values), 7)
                self.assertEqual(tuple(value.predicate_iri for value in values), expected_predicates)
                self.assertEqual(tuple(value.object_kind for value in values), expected_kinds)
                self.assertEqual({value.product_key for value in values}, {product.key})
                self.assertEqual({value.ontology_iri for value in values}, {product.stable_ontology_iri})
                self.assertEqual(values[0].value, product.label)
                self.assertEqual(values[1].value, product.description)
                self.assertEqual(values[2].value, product.product_type_iri)
                self.assertEqual(values[3].value, PUBLICATION_VALUES["development_status_iri"])
                self.assertEqual(values[4].value, PUBLICATION_VALUES["license_iri"])
                self.assertEqual(values[5].value, PUBLICATION_VALUES["repository_iri"])
                self.assertEqual(values[6].value, PUBLICATION_VALUES["generated_warning"])
                self.assertEqual(
                    tuple(value.language for value in values),
                    ("en", "en", None, None, None, None, "en"),
                )

    def test_metadata_rendering_is_deterministic_and_immutable(self) -> None:
        first = metadata.ontology_metadata_triples(self.loaded, "integrated")
        second = metadata.ontology_metadata_triples(self.loaded, "integrated")
        self.assertEqual(first, second)
        self.assertEqual(
            tuple(value.object_turtle for value in first),
            tuple(value.object_turtle for value in second),
        )
        with self.assertRaises(FrozenInstanceError):
            first[0].value = "changed"  # type: ignore[misc]

    def test_rdf_terms_preserve_exact_iri_and_language_kinds(self) -> None:
        triples = metadata.ontology_metadata_rdf_triples(self.loaded, "integrated")
        objects = tuple(value[2] for value in triples)
        for index in (0, 1, 6):
            self.assertIsInstance(objects[index], Literal)
            self.assertEqual(objects[index].language, "en")
            self.assertIsNone(objects[index].datatype)
        for index in (2, 3, 4, 5):
            self.assertIsInstance(objects[index], URIRef)

    def test_exact_metadata_validation_accepts_each_product(self) -> None:
        imports = {
            "integrated": (
                "http://www.w3.org/ns/ssn/",
                "http://www.w3.org/ns/sosa/sampling/",
                "http://www.w3.org/ns/ssn/systems/",
                "https://www.commoncoreontologies.org/2024-11-06/CommonCoreOntologiesMerged",
            ),
            "alignment_core": (),
            "strict_bfo_mapping": (
                POLICY_PRODUCTS["alignment_core"]["stable_ontology_iri"],
            ),
            "bfo_projection": (
                POLICY_PRODUCTS["strict_bfo_mapping"]["stable_ontology_iri"],
            ),
            "cco_extension": (
                POLICY_PRODUCTS["strict_bfo_mapping"]["stable_ontology_iri"],
            ),
        }
        for product_key, expected_imports in imports.items():
            with self.subTest(product=product_key):
                graph = self.graph_for(product_key, expected_imports)
                self.assertEqual(
                    metadata.validate_emitted_ontology_metadata(
                        graph, self.loaded, product_key, expected_imports
                    ),
                    (),
                )
                self.assertEqual(
                    len(
                        metadata.strip_emitted_ontology_header(
                            graph, self.loaded, product_key, expected_imports
                        )
                    ),
                    0,
                )

    def test_validation_rejects_missing_extra_wrong_duplicate_and_misplaced_metadata(self) -> None:
        product_key = "alignment_core"
        product = next(value for value in self.loaded.products if value.key == product_key)
        ontology = URIRef(product.stable_ontology_iri)
        expected = metadata.ontology_metadata_rdf_triples(self.loaded, product_key)
        mutations: dict[str, tuple[Graph, str]] = {}

        missing = self.graph_for(product_key)
        missing.remove(expected[0])
        mutations["missing"] = (missing, "ONTOLOGY_METADATA_MISMATCH")

        extra = self.graph_for(product_key)
        extra.add((ontology, URIRef("https://example.org/unapproved"), Literal("extra")))
        mutations["extra"] = (extra, "UNAPPROVED_ONTOLOGY_METADATA")

        wrong = self.graph_for(product_key)
        wrong.remove(expected[0])
        wrong.add((ontology, RDFS.label, Literal("Wrong", lang="en")))
        mutations["wrong"] = (wrong, "ONTOLOGY_METADATA_MISMATCH")

        duplicate = self.graph_for(product_key)
        duplicate.add((ontology, RDFS.label, Literal(product.label, lang="fr")))
        mutations["duplicate"] = (duplicate, "ONTOLOGY_METADATA_MISMATCH")

        misplaced = self.graph_for(product_key)
        misplaced.add((URIRef("https://example.org/other"), RDFS.label, Literal("Other", lang="en")))
        mutations["misplaced"] = (misplaced, "MISPLACED_ONTOLOGY_METADATA")

        for name, (graph, expected_code) in mutations.items():
            with self.subTest(case=name):
                issues = metadata.validate_emitted_ontology_metadata(
                    graph, self.loaded, product_key, ()
                )
                self.assertIn(expected_code, {issue.code for issue in issues})

    def test_validation_rejects_malformed_term_kinds_languages_and_release_fields(self) -> None:
        product_key = "alignment_core"
        product = next(value for value in self.loaded.products if value.key == product_key)
        ontology = URIRef(product.stable_ontology_iri)
        expected = metadata.ontology_metadata_rdf_triples(self.loaded, product_key)
        mutations: dict[str, tuple[Graph, str]] = {}

        literal_for_iri = self.graph_for(product_key)
        literal_for_iri.remove(expected[2])
        literal_for_iri.add((ontology, expected[2][1], Literal(product.product_type_iri)))
        mutations["literal_for_iri"] = (literal_for_iri, "ONTOLOGY_METADATA_MISMATCH")

        iri_for_literal = self.graph_for(product_key)
        iri_for_literal.remove(expected[0])
        iri_for_literal.add((ontology, RDFS.label, URIRef("https://example.org/label")))
        mutations["iri_for_literal"] = (iri_for_literal, "ONTOLOGY_METADATA_MISMATCH")

        missing_language = self.graph_for(product_key)
        missing_language.remove(expected[1])
        missing_language.add((ontology, expected[1][1], Literal(product.description)))
        mutations["missing_language"] = (missing_language, "ONTOLOGY_METADATA_MISMATCH")

        release_only = self.graph_for(product_key)
        release_only.add((ontology, OWL.versionIRI, URIRef("https://example.org/release")))
        mutations["release_only"] = (release_only, "RELEASE_METADATA_IN_DEVELOPMENT")

        controlled_declaration = self.graph_for(product_key)
        controlled_declaration.add((URIRef(product.product_type_iri), RDF.type, OWL.Class))
        mutations["controlled_declaration"] = (
            controlled_declaration,
            "CONTROLLED_IRI_DECLARATION",
        )

        for name, (graph, expected_code) in mutations.items():
            with self.subTest(case=name):
                issues = metadata.validate_emitted_ontology_metadata(
                    graph, self.loaded, product_key, ()
                )
                self.assertIn(expected_code, {issue.code for issue in issues})

    def test_graph_validator_rejects_complete_governed_negative_matrix(self) -> None:
        product_key = "alignment_core"
        product = next(value for value in self.loaded.products if value.key == product_key)
        ontology = URIRef(product.stable_ontology_iri)
        expected = metadata.ontology_metadata_rdf_triples(self.loaded, product_key)
        cases: dict[str, tuple[Graph, str]] = {}

        wrong_subject = self.graph_for(product_key)
        wrong_subject.remove((ontology, RDF.type, OWL.Ontology))
        wrong_subject.add((URIRef("https://example.org/wrong"), RDF.type, OWL.Ontology))
        cases["wrong ontology subject"] = (wrong_subject, "ONTOLOGY_DECLARATION_MISMATCH")

        missing_declaration = self.graph_for(product_key)
        missing_declaration.remove((ontology, RDF.type, OWL.Ontology))
        cases["missing ontology declaration"] = (
            missing_declaration,
            "ONTOLOGY_DECLARATION_MISMATCH",
        )

        wrong_values = (
            ("status", 3, URIRef("https://example.org/status")),
            ("license", 4, URIRef("https://example.org/license")),
            ("repository", 5, URIRef("https://example.org/repository")),
            ("warning", 6, Literal("Wrong generated warning", lang="en")),
        )
        for name, index, replacement in wrong_values:
            graph = self.graph_for(product_key)
            graph.remove(expected[index])
            graph.add((ontology, expected[index][1], replacement))
            cases[f"wrong {name} value"] = (graph, "ONTOLOGY_METADATA_MISMATCH")

        for name, controlled_iri in (
            ("authority status declaration", self.loaded.publication.development_status_iri),
            ("product type declaration", product.product_type_iri),
        ):
            graph = self.graph_for(product_key)
            graph.add((URIRef(controlled_iri), RDF.type, OWL.NamedIndividual))
            cases[name] = (graph, "CONTROLLED_IRI_DECLARATION")

        unapproved_values = (
            ("local filesystem path", "sourcePath", "/tmp/generated.ttl"),
            ("dependency path", "dependencyPath", "imports/cco.ttl"),
            ("hash", "sha256", "0" * 64),
            ("Git tag", "gitTag", "v2026-07-16"),
            ("commit", "commit", "deadbeef"),
            ("date", "date", "2026-07-16"),
        )
        for name, local_name, value in unapproved_values:
            graph = self.graph_for(product_key)
            graph.add((ontology, URIRef(f"https://example.org/{local_name}"), Literal(value)))
            cases[name] = (graph, "UNAPPROVED_ONTOLOGY_METADATA")

        release_values = (
            ("dcterms issued", URIRef(metadata.DCTERMS_NAMESPACE + "issued"), Literal("2026-07-16")),
            ("version IRI", OWL.versionIRI, URIRef("https://example.org/release")),
            ("version info", OWL.versionInfo, Literal("v2026-07-16")),
        )
        for name, predicate, value in release_values:
            graph = self.graph_for(product_key)
            graph.add((ontology, predicate, value))
            cases[name] = (graph, "RELEASE_METADATA_IN_DEVELOPMENT")

        for name, (graph, expected_code) in cases.items():
            with self.subTest(case=name):
                issues = metadata.validate_emitted_ontology_metadata(
                    graph, self.loaded, product_key, ()
                )
                self.assertIn(expected_code, {issue.code for issue in issues})

    def test_canonical_serialized_header_is_shared_by_all_five_products(self) -> None:
        for product in self.loaded.products:
            with self.subTest(product=product.key):
                imports, notice, prefixes, import_terms = self.serialization_parameters(product.key)
                artifact = (REPO_ROOT / product.path).read_bytes()
                expected = metadata.render_ontology_header_bytes(
                    self.loaded,
                    product.key,
                    imports,
                    generated_notice=notice,
                    prefixes=prefixes,
                    import_turtle_terms=import_terms,
                )
                self.assertTrue(artifact.startswith(expected))
                self.assertEqual(self.serialized_issues(artifact, product.key), ())

    def test_missing_final_newline_is_noncanonical_but_parseable(self) -> None:
        artifact = (REPO_ROOT / "SSN2BFO.ttl").read_bytes()
        self.assertTrue(artifact.endswith(b"\n"))
        candidate = artifact[:-1]
        self.assertTrue(
            isomorphic(
                Graph().parse(data=artifact.decode(), format="turtle"),
                Graph().parse(data=candidate.decode(), format="turtle"),
            )
        )
        self.assertIn(
            "NONCANONICAL_ONTOLOGY_HEADER",
            {issue.code for issue in self.serialized_issues(candidate, "integrated")},
        )

    def test_extra_header_logical_boundary_newline_is_noncanonical_but_parseable(self) -> None:
        product_key = "integrated"
        artifact = (REPO_ROOT / "SSN2BFO.ttl").read_bytes()
        imports, notice, prefixes, import_terms = self.serialization_parameters(product_key)
        header = metadata.render_ontology_header_bytes(
            self.loaded,
            product_key,
            imports,
            generated_notice=notice,
            prefixes=prefixes,
            import_turtle_terms=import_terms,
        )
        canonical_boundary = header + b"\n"
        self.assertTrue(artifact.startswith(canonical_boundary))
        candidate = header + b"\n\n" + artifact[len(canonical_boundary) :]
        self.assertTrue(
            isomorphic(
                Graph().parse(data=artifact.decode(), format="turtle"),
                Graph().parse(data=candidate.decode(), format="turtle"),
            )
        )
        self.assertIn(
            "NONCANONICAL_ONTOLOGY_HEADER",
            {issue.code for issue in self.serialized_issues(candidate, product_key)},
        )

    def test_semantically_equivalent_reordered_headers_are_noncanonical(self) -> None:
        for product in self.loaded.products:
            with self.subTest(product=product.key):
                artifact = (REPO_ROOT / product.path).read_bytes()
                lines = artifact.splitlines()
                label_index = next(
                    index for index, line in enumerate(lines) if line.startswith(b"    rdfs:label ")
                )
                description_index = next(
                    index
                    for index, line in enumerate(lines)
                    if line.startswith(b"    dcterms:description ")
                )
                lines[label_index], lines[description_index] = (
                    lines[description_index],
                    lines[label_index],
                )
                reordered = b"\n".join(lines) + b"\n"
                self.assertTrue(
                    isomorphic(
                        Graph().parse(data=artifact.decode(), format="turtle"),
                        Graph().parse(data=reordered.decode(), format="turtle"),
                    )
                )
                self.assertIn(
                    "NONCANONICAL_ONTOLOGY_HEADER",
                    {issue.code for issue in self.serialized_issues(reordered, product.key)},
                )

    def test_other_header_order_import_prefix_and_literal_variants_are_rejected(self) -> None:
        root = (REPO_ROOT / "SSN2BFO.ttl").read_bytes()
        header_lines = (
            b"    dcterms:description ",
            b"    dcterms:type ",
            b"    adms:status ",
            b"    dcterms:license ",
            b"    rdfs:seeAlso ",
            b"    rdfs:comment ",
        )
        for prefix in header_lines:
            with self.subTest(reordered_predicate=prefix.decode().strip()):
                lines = root.splitlines()
                index = next(i for i, line in enumerate(lines) if line.startswith(prefix))
                lines[index - 1], lines[index] = lines[index], lines[index - 1]
                candidate = b"\n".join(lines) + b"\n"
                self.assertIn(
                    "NONCANONICAL_ONTOLOGY_HEADER",
                    {issue.code for issue in self.serialized_issues(candidate, "integrated")},
                )

        reordered_imports = root.replace(b"        ssn:,\n        ssn-system:,", b"        ssn-system:,\n        ssn:,")
        self.assertIn(
            "NONCANONICAL_ONTOLOGY_HEADER",
            {issue.code for issue in self.serialized_issues(reordered_imports, "integrated")},
        )

        projection = (REPO_ROOT / POLICY_PRODUCTS["bfo_projection"]["path"]).read_bytes()
        missing_prefix = projection.replace(
            b"@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n",
            b"",
            1,
        )
        noncanonical_language = projection.replace(b'"@en', b'"@EN', 1)
        label_line = next(
            line for line in projection.splitlines() if line.startswith(b"    rdfs:label ")
        )
        literal_value = label_line.split(b"rdfs:label ", 1)[1].removesuffix(b" ;")
        noncanonical_literal = projection.replace(
            literal_value,
            b'"""' + literal_value[1:-4] + b'"""@en',
            1,
        )
        for name, candidate in (
            ("missing canonical prefix", missing_prefix),
            ("noncanonical language tag", noncanonical_language),
            ("noncanonical literal", noncanonical_literal),
        ):
            with self.subTest(case=name):
                self.assertIn(
                    "NONCANONICAL_ONTOLOGY_HEADER",
                    {issue.code for issue in self.serialized_issues(candidate, "bfo_projection")},
                )

        malformed = projection.replace(label_line, b'    rdfs:label "unterminated@en ;', 1)
        self.assertIn(
            "TURTLE_PARSE",
            {issue.code for issue in self.serialized_issues(malformed, "bfo_projection")},
        )


class IdentitySafetyTests(MetadataTestCase):
    def test_duplicate_path(self) -> None:
        duplicate = json.dumps(POLICY_PRODUCTS["integrated"]["path"])
        self.assert_issue(
            render_toml(raw_overrides={("alignment_core", "path"): duplicate}),
            "DUPLICATE_PATH",
            "products.alignment_core.path",
        )

    def test_duplicate_stable_iri(self) -> None:
        duplicate = json.dumps(POLICY_PRODUCTS["integrated"]["stable_ontology_iri"])
        self.assert_issue(
            render_toml(raw_overrides={("alignment_core", "stable_ontology_iri"): duplicate}),
            "DUPLICATE_STABLE_IRI",
            "products.alignment_core.stable_ontology_iri",
        )

    def test_duplicate_release_suffix(self) -> None:
        duplicate = json.dumps(POLICY_PRODUCTS["integrated"]["release_iri_suffix"])
        self.assert_issue(
            render_toml(raw_overrides={("alignment_core", "release_iri_suffix"): duplicate}),
            "DUPLICATE_RELEASE_SUFFIX",
            "products.alignment_core.release_iri_suffix",
        )

    def test_duplicate_product_type_iri(self) -> None:
        duplicate = json.dumps(POLICY_PRODUCTS["integrated"]["product_type_iri"])
        self.assert_issue(
            render_toml(raw_overrides={("alignment_core", "product_type_iri"): duplicate}),
            "DUPLICATE_PRODUCT_TYPE_IRI",
            "products.alignment_core.product_type_iri",
        )

    def test_absolute_path(self) -> None:
        self.assert_issue(
            render_toml(raw_overrides={("integrated", "path"): json.dumps("/tmp/output.ttl")}),
            "UNSAFE_PRODUCT_PATH",
        )

    def test_parent_traversal(self) -> None:
        self.assert_issue(
            render_toml(raw_overrides={("integrated", "path"): json.dumps("../output.ttl")}),
            "UNSAFE_PRODUCT_PATH",
        )

    def test_backslash_path(self) -> None:
        self.assert_issue(
            render_toml(raw_overrides={("integrated", "path"): json.dumps("releases\\output.ttl")}),
            "UNSAFE_PRODUCT_PATH",
        )

    def test_windows_drive_and_unc_paths(self) -> None:
        values = (
            "C:/outside.ttl",
            r"C:\outside.ttl",
            r"C:relative.ttl",
            "//server/share/file.ttl",
            r"\\server\share\file.ttl",
        )
        for value in values:
            with self.subTest(value=value):
                self.assert_issue(
                    render_toml(raw_overrides={("integrated", "path"): json.dumps(value)}),
                    "UNSAFE_PRODUCT_PATH",
                )

    def test_duplicate_slash_path(self) -> None:
        self.assert_issue(
            render_toml(raw_overrides={("integrated", "path"): json.dumps("releases//output.ttl")}),
            "UNSAFE_PRODUCT_PATH",
        )

    def test_path_query_or_fragment(self) -> None:
        for value in ("releases/output.ttl?download=1", "releases/output.ttl#section"):
            with self.subTest(value=value):
                self.assert_issue(
                    render_toml(raw_overrides={("integrated", "path"): json.dumps(value)}),
                    "UNSAFE_PRODUCT_PATH",
                )

    def test_unsafe_release_suffixes(self) -> None:
        values = ("/integrated", "integrated/", "a/../b", "a\\b", "a//b", "a?b", "a#b")
        for value in values:
            with self.subTest(value=value):
                self.assert_issue(
                    render_toml(
                        raw_overrides={("integrated", "release_iri_suffix"): json.dumps(value)}
                    ),
                    "UNSAFE_RELEASE_SUFFIX",
                )

    def test_invalid_release_bases(self) -> None:
        values = (
            "not-an-iri",
            "ftp://example.org/releases",
            "http://example.org/releases/",
            "http://example.org/releases?q=1",
            "http://example.org/releases?",
            "http://example.org/releases#",
            "http://[::1",
            "http://example.org:bad",
            "http://example.org:99999",
            r"http://example.org\path",
            "http:///path",
            "http://bad_host/path",
        )
        for value in values:
            with self.subTest(value=value):
                self.assert_issue(
                    render_toml(release_base_raw=json.dumps(value)),
                    "INVALID_RELEASE_BASE",
                )

    def test_invalid_stable_ontology_iris(self) -> None:
        values = (
            "relative",
            "ftp://example.org/product",
            "http://example.org/a b",
            "http://example.org/product#fragment",
            "http://example.org/product?",
            "http://example.org/product#",
            "http://[::1",
            "http://example.org:bad",
            "http://example.org:99999",
            r"http://example.org\path",
            "http:///path",
            "http://bad_host/path",
        )
        for value in values:
            with self.subTest(value=value):
                self.assert_issue(
                    render_toml(
                        raw_overrides={("integrated", "stable_ontology_iri"): json.dumps(value)}
                    ),
                    "INVALID_STABLE_IRI",
                )

    def test_approved_trailing_slash_iris_pass(self) -> None:
        loaded = metadata.load_metadata(self.write(render_toml()))
        self.assertTrue(loaded.publication.license_iri.endswith("/"))
        self.assertTrue(loaded.products[0].stable_ontology_iri.endswith("/"))

    def test_global_and_product_iri_fields_reject_malformed_relative_and_local_values(self) -> None:
        publication_cases = (
            ("license_iri", "relative", "INVALID_LICENSE_IRI"),
            ("repository_iri", "file:///tmp/repository", "INVALID_REPOSITORY_IRI"),
            ("development_status_property_iri", "/tmp/status", "INVALID_STATUS_PROPERTY_IRI"),
            ("development_status_iri", "C:/status", "INVALID_STATUS_IRI"),
        )
        for field, value, code in publication_cases:
            with self.subTest(field=field, value=value):
                self.assert_issue(
                    render_toml(publication_raw_overrides={field: json.dumps(value)}),
                    code,
                    f"publication.{field}",
                )
        self.assert_issue(
            render_toml(
                raw_overrides={("integrated", "product_type_iri"): '"../product-type"'}
            ),
            "INVALID_PRODUCT_TYPE_IRI",
            "products.integrated.product_type_iri",
        )

    def test_queries_and_unapproved_fragments_are_rejected(self) -> None:
        for field in ("license_iri", "repository_iri", "development_status_iri"):
            with self.subTest(field=field):
                self.assert_issue(
                    render_toml(
                        publication_raw_overrides={
                            field: json.dumps("https://example.org/value?query=1")
                        }
                    ),
                    {
                        "license_iri": "INVALID_LICENSE_IRI",
                        "repository_iri": "INVALID_REPOSITORY_IRI",
                        "development_status_iri": "INVALID_STATUS_IRI",
                    }[field],
                )
        self.assert_issue(
            render_toml(
                raw_overrides={
                    ("integrated", "product_type_iri"): '"https://example.org/type#value"'
                }
            ),
            "INVALID_PRODUCT_TYPE_IRI",
        )

    def test_blank_labels_and_descriptions_are_rejected(self) -> None:
        for field in ("label", "description"):
            with self.subTest(field=field):
                self.assert_issue(
                    render_toml(raw_overrides={("integrated", field): '"   "'}),
                    "EMPTY_STRING",
                    f"products.integrated.{field}",
                )

    def test_nfc_text_passes_and_decomposed_text_is_rejected(self) -> None:
        normalized = render_toml(
            raw_overrides={("integrated", "label"): json.dumps("Caf\u00e9", ensure_ascii=False)}
        )
        loaded = metadata.load_metadata(self.write(normalized))
        self.assertEqual(loaded.products[0].label, "Caf\u00e9")
        for field in ("label", "description"):
            with self.subTest(field=field):
                self.assert_issue(
                    render_toml(
                        raw_overrides={
                            ("integrated", field): json.dumps("Cafe\u0301", ensure_ascii=False)
                        }
                    ),
                    "NON_NFC_TEXT",
                    f"products.integrated.{field}",
                )

    def test_control_characters_and_multiline_warning_are_rejected(self) -> None:
        self.assert_issue(
            render_toml(raw_overrides={("integrated", "label"): '"bad\\u0001label"'}),
            "CONTROL_CHARACTER",
            "products.integrated.label",
        )
        self.assert_issue(
            render_toml(
                publication_raw_overrides={
                    "generated_warning": '"""Generated warning\ncontinued."""'
                }
            ),
            "CONTROL_CHARACTER",
            "publication.generated_warning",
        )

    def test_noncanonical_warning_whitespace_is_rejected(self) -> None:
        self.assert_issue(
            render_toml(
                publication_raw_overrides={
                    "generated_warning": '"Generated  warning with extra spacing."'
                }
            ),
            "NONCANONICAL_WHITESPACE",
            "publication.generated_warning",
        )

    def test_language_other_than_en_is_rejected(self) -> None:
        self.assert_issue(
            render_toml(publication_raw_overrides={"default_language": '"fr"'}),
            "UNSUPPORTED_LANGUAGE",
            "publication.default_language",
        )

    def test_deferred_tables_and_fields_are_rejected(self) -> None:
        top_level_tables = ("agents", "dependencies")
        for table in top_level_tables:
            with self.subTest(table=table):
                self.assert_issue(
                    render_toml() + f"\n[{table}]\nvalue = \"deferred\"\n",
                    "UNKNOWN_FIELD",
                    f"metadata.{table}",
                )
        deferred_publication_fields = (
            "creator",
            "contributor",
            "provenance",
            "release_identifier",
            "owl_version_iri",
            "owl_version_info",
            "dcterms_issued",
            "release_date",
            "git_tag",
            "commit",
            "artifact_sha256",
        )
        for field in deferred_publication_fields:
            with self.subTest(field=field):
                content = render_toml().replace(
                    "[publication]\n",
                    f"[publication]\n{field} = \"deferred\"\n",
                )
                self.assert_issue(content, "UNKNOWN_FIELD", f"publication.{field}")


class DevelopmentModeTests(MetadataTestCase):
    def test_development_output_is_deterministic_and_reports_exact_schema_3_values(self) -> None:
        first = io.StringIO()
        second = io.StringIO()
        self.assertEqual(checker.main([], stdout=first), 0)
        self.assertEqual(checker.main([], stdout=second), 0)
        self.assertEqual(first.getvalue(), second.getvalue())

        rendered = first.getvalue()
        expected_lines = (
            "Schema version: 3",
            f"Project title: {PUBLICATION_VALUES['project_title']}",
            f"Default language: {PUBLICATION_VALUES['default_language']}",
            f"Release IRI base: {PUBLICATION_VALUES['release_iri_base']}",
            f"License IRI: {PUBLICATION_VALUES['license_iri']}",
            f"Repository IRI: {PUBLICATION_VALUES['repository_iri']}",
            f"Generated warning: {PUBLICATION_VALUES['generated_warning']}",
            (
                "Development status property IRI: "
                f"{PUBLICATION_VALUES['development_status_property_iri']}"
            ),
            f"Development status IRI: {PUBLICATION_VALUES['development_status_iri']}",
            f"Formal release status IRI: {PUBLICATION_VALUES['formal_release_status_iri']}",
            "Canonical product count: 5",
            "Canonical product order: " + ", ".join(metadata.PRODUCT_ORDER),
        )
        for line in expected_lines:
            self.assertIn(line + "\n", rendered)
        for key, values in POLICY_PRODUCTS.items():
            self.assertIn(f"Product: {key}\n", rendered)
            self.assertIn(f"  path: {values['path']}\n", rendered)
            self.assertIn(f"  stable ontology IRI: {values['stable_ontology_iri']}\n", rendered)
            self.assertIn(f"  release suffix: {values['release_iri_suffix']}\n", rendered)
            self.assertIn(f"  label: {values['label']}\n", rendered)
            self.assertIn(f"  description: {values['description']}\n", rendered)
            self.assertIn(f"  product-type IRI: {values['product_type_iri']}\n", rendered)

    def test_default_development_validation_passes_without_version_iris(self) -> None:
        output = io.StringIO()
        self.assertEqual(checker.main([], stdout=output), 0)
        rendered = output.getvalue()
        self.assertIn("Mode: development", rendered)
        self.assertIn("Immutable release version IRI: not claimed", rendered)
        self.assertNotIn("Version IRI [", rendered)

    def test_release_only_arguments_are_rejected_in_development_mode(self) -> None:
        error = io.StringIO()
        code = checker.main(["--release-id", "2026-07-14"], stderr=error)
        self.assertEqual(code, 1)
        self.assertIn("ERROR [DEVELOPMENT_RELEASE_ARGUMENT] release_context:", error.getvalue())

    def test_future_modular_product_files_do_not_need_to_exist(self) -> None:
        config = self.write(render_toml())
        self.assertFalse((self.root / POLICY_PRODUCTS["alignment_core"]["path"]).exists())
        output = io.StringIO()
        code = checker.main(["--metadata", str(config)], stdout=output)
        self.assertEqual(code, 0)


class ReleaseIdentifierTests(unittest.TestCase):
    def assert_invalid(self, value: str, code: str = "RELEASE_ID_FORMAT") -> None:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.validate_release_identifier(value)
        self.assertEqual(raised.exception.issues[0].code, code)

    def test_valid_date(self) -> None:
        self.assertEqual(metadata.validate_release_identifier("2026-07-14"), "2026-07-14")

    def test_revision_sequences_are_rejected(self) -> None:
        for value in ("2026-07-14.1", "2026-07-14.2", "2026-07-14.100"):
            with self.subTest(value=value):
                self.assert_invalid(value)

    def test_invalid_calendar_date(self) -> None:
        self.assert_invalid("2026-02-30", "RELEASE_DATE_INVALID")

    def test_missing_zero_padding(self) -> None:
        self.assert_invalid("2026-7-14")

    def test_zero_sequence(self) -> None:
        self.assert_invalid("2026-07-14.0")

    def test_leading_zero_sequence(self) -> None:
        self.assert_invalid("2026-07-14.01")

    def test_surrounding_whitespace(self) -> None:
        self.assert_invalid(" 2026-07-14")
        self.assert_invalid("2026-07-14 ")

    def test_trailing_junk(self) -> None:
        self.assert_invalid("2026-07-14-release")


class GitTagTests(unittest.TestCase):
    def test_exact_match(self) -> None:
        context = metadata.validate_release_context(
            "2026-07-14",
            "2026-07-14",
            "v2026-07-14",
            "0123456789abcdef0123456789abcdef01234567",
        )
        self.assertEqual(context.git_tag, "v2026-07-14")

    def test_missing_v(self) -> None:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.validate_release_context(
                "2026-07-14",
                "2026-07-14",
                "2026-07-14",
                "0123456789abcdef0123456789abcdef01234567",
            )
        self.assertEqual(raised.exception.issues[0].code, "GIT_TAG_FORMAT")

    def test_malformed_tag(self) -> None:
        for value, expected_code in (
            ("version-2026-07-14", "GIT_TAG_FORMAT"),
            ("v2026-02-30", "RELEASE_TAG_MISMATCH"),
        ):
            with self.subTest(value=value):
                with self.assertRaises(metadata.PublicationMetadataError) as raised:
                    metadata.validate_release_context(
                        "2026-07-14",
                        "2026-07-14",
                        value,
                        "0123456789abcdef0123456789abcdef01234567",
                    )
                self.assertEqual(raised.exception.issues[0].code, expected_code)

    def test_mismatched_date(self) -> None:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.validate_release_context(
                "2026-07-14",
                "2026-07-14",
                "v2026-07-15",
                "0123456789abcdef0123456789abcdef01234567",
            )
        self.assertEqual(raised.exception.issues[0].code, "RELEASE_TAG_MISMATCH")

    def test_release_date_mismatch(self) -> None:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.validate_release_context(
                "2026-07-14",
                "2026-07-15",
                "v2026-07-14",
                "0123456789abcdef0123456789abcdef01234567",
            )
        self.assertEqual(raised.exception.issues[0].code, "RELEASE_DATE_MISMATCH")

    def test_release_mode_requires_release_and_tag_pair(self) -> None:
        for argv in (
            ["--mode", "release"],
            ["--mode", "release", "--release-id", "2026-07-14"],
            ["--mode", "release", "--git-tag", "v2026-07-14"],
            [
                "--mode",
                "release",
                "--release-id",
                "2026-07-14",
                "--release-date",
                "2026-07-14",
                "--git-tag",
                "v2026-07-14",
            ],
        ):
            with self.subTest(argv=argv):
                error = io.StringIO()
                self.assertEqual(checker.main(argv, stderr=error), 1)
                self.assertIn("ERROR [RELEASE_ARGUMENT_REQUIRED]", error.getvalue())


class VersionIriTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loaded = metadata.load_metadata(ACTUAL_CONFIG)

    def test_all_five_approved_version_iri_forms(self) -> None:
        context = parse_formal_release_context(
            "2026-07-14",
            "2026-07-14",
            "v2026-07-14",
            "0123456789abcdef0123456789abcdef01234567",
        )
        expected = {
            "integrated": f"{RELEASE_BASE}/2026-07-14/integrated",
            "alignment_core": f"{RELEASE_BASE}/2026-07-14/current-ssn-sosa/alignment-core",
            "strict_bfo_mapping": f"{RELEASE_BASE}/2026-07-14/current-ssn-sosa/bfo-mapping",
            "bfo_projection": f"{RELEASE_BASE}/2026-07-14/current-ssn-sosa/bfo-projection",
            "cco_extension": f"{RELEASE_BASE}/2026-07-14/current-ssn-sosa/cco-extension",
        }
        observed = {
            product.key: metadata.release_version_iri(self.loaded, product.key, context)
            for product in self.loaded.products
        }
        self.assertEqual(observed, expected)

    def assert_mismatch(self, observed: str) -> None:
        product = self.loaded.products[0]
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.validate_version_iri(product, "2026-07-14", observed)
        self.assertEqual(raised.exception.issues[0].code, "VERSION_IRI_MISMATCH")

    def test_wrong_base(self) -> None:
        self.assert_mismatch("http://example.org/releases/2026-07-14/integrated")

    def test_wrong_release_identifier_is_rejected(self) -> None:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.build_version_iri(self.loaded.products[0], "2026-7-14")
        self.assertEqual(raised.exception.issues[0].code, "RELEASE_ID_FORMAT")

    def test_wrong_suffix(self) -> None:
        self.assert_mismatch(f"{RELEASE_BASE}/2026-07-14/not-integrated")

    def test_observed_iri_mismatch(self) -> None:
        self.assert_mismatch(f"{RELEASE_BASE}/2026-07-15/integrated")


class Sha256Tests(MetadataTestCase):
    def test_valid_lowercase_digest(self) -> None:
        self.assertTrue(metadata.is_sha256("0" * 64))

    def test_invalid_digest_syntax(self) -> None:
        values = (
            "A" * 64,
            "0" * 63,
            "0" * 65,
            " 0" + "0" * 63,
            "0" * 64 + " ",
            "sha256:" + "0" * 64,
            "g" * 64,
        )
        for value in values:
            with self.subTest(value=value):
                self.assertFalse(metadata.is_sha256(value))

    def test_file_hashing_correctness(self) -> None:
        path = self.write("publication metadata\n", name="source.txt")
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(metadata.sha256_file(path), expected)


class ErrorAndCliTests(MetadataTestCase):
    def test_deterministic_issue_ordering(self) -> None:
        content = render_toml(
            raw_overrides={
                ("alignment_core", "path"): json.dumps(POLICY_PRODUCTS["integrated"]["path"]),
                ("alignment_core", "stable_ontology_iri"): json.dumps(
                    POLICY_PRODUCTS["integrated"]["stable_ontology_iri"]
                ),
                ("alignment_core", "release_iri_suffix"): json.dumps(
                    POLICY_PRODUCTS["integrated"]["release_iri_suffix"]
                ),
            }
        )
        first = self.error_for(content)
        second = self.error_for(content)
        self.assertEqual(first.issues, second.issues)
        self.assertEqual(
            [issue.code for issue in first.issues],
            ["DUPLICATE_PATH", "DUPLICATE_STABLE_IRI", "DUPLICATE_RELEASE_SUFFIX"],
        )

    def test_stable_error_code_and_field_path(self) -> None:
        error = self.error_for(
            render_toml(raw_overrides={("integrated", "path"): json.dumps("../bad.ttl")})
        )
        self.assertEqual(error.issues[0].code, "UNSAFE_PRODUCT_PATH")
        self.assertEqual(error.issues[0].field, "products.integrated.path")

    def test_expected_cli_validation_failure_has_no_traceback(self) -> None:
        config = self.write("schema_version =\n")
        error = io.StringIO()
        code = checker.main(["--metadata", str(config)], stderr=error)
        self.assertEqual(code, 1)
        self.assertIn("ERROR [TOML_PARSE]", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())

    def test_cli_unknown_field_returns_nonzero(self) -> None:
        config = self.write(
            render_toml().replace(
                "[publication]\n",
                "[publication]\ncreator = \"deferred\"\n",
            )
        )
        error = io.StringIO()
        code = checker.main(["--metadata", str(config)], stderr=error)
        self.assertEqual(code, 1)
        self.assertIn("ERROR [UNKNOWN_FIELD] publication.creator", error.getvalue())

    def test_cli_malformed_iris_are_structured(self) -> None:
        values = (
            "http://[::1",
            "http://example.org:bad",
            "http://example.org:99999",
            r"http://example.org\path",
            "http:///path",
            "http://bad_host/path",
        )
        contexts = (
            (
                "INVALID_RELEASE_BASE",
                lambda value: render_toml(release_base_raw=json.dumps(value)),
            ),
            (
                "INVALID_STABLE_IRI",
                lambda value: render_toml(
                    raw_overrides={("integrated", "stable_ontology_iri"): json.dumps(value)}
                ),
            ),
        )
        for expected_code, build_content in contexts:
            for value in values:
                with self.subTest(code=expected_code, value=value):
                    config = self.write(build_content(value))
                    error = io.StringIO()
                    code = checker.main(["--metadata", str(config)], stderr=error)
                    rendered = error.getvalue()
                    self.assertEqual(code, 1)
                    self.assertIn(f"ERROR [{expected_code}]", rendered)
                    self.assertNotIn("Traceback", rendered)
                    self.assertNotIn("ValueError", rendered)

    def test_development_cli_success_and_metadata_hash(self) -> None:
        output = io.StringIO()
        code = checker.main([], stdout=output)
        self.assertEqual(code, 0)
        self.assertIn(f"Metadata SHA-256: {metadata.sha256_file(ACTUAL_CONFIG)}", output.getvalue())
        self.assertIn("Canonical product count: 5", output.getvalue())

    def test_release_cli_success(self) -> None:
        output = io.StringIO()
        code = checker.main(
            [
                "--mode",
                "release",
                "--release-id",
                "2026-07-14",
                "--release-date",
                "2026-07-14",
                "--git-tag",
                "v2026-07-14",
                "--source-commit",
                "0123456789abcdef0123456789abcdef01234567",
            ],
            stdout=output,
        )
        self.assertEqual(code, 0)
        self.assertEqual(output.getvalue().count("Version IRI ["), 5)
        self.assertIn("Git tag existence/binding", output.getvalue())

    def test_tag_mismatch_cli_failure(self) -> None:
        error = io.StringIO()
        code = checker.main(
            [
                "--mode",
                "release",
                "--release-id",
                "2026-07-14",
                "--release-date",
                "2026-07-14",
                "--git-tag",
                "v2026-07-15",
                "--source-commit",
                "0123456789abcdef0123456789abcdef01234567",
            ],
            stderr=error,
        )
        self.assertEqual(code, 1)
        self.assertEqual(
            error.getvalue().strip(),
            "ERROR [RELEASE_TAG_MISMATCH] git_tag: expected v2026-07-14, got v2026-07-15",
        )

    def test_documented_exit_codes(self) -> None:
        error = io.StringIO()
        self.assertEqual(checker.main(["--release-id", "2026-07-14"], stderr=error), 1)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            checker.main(["--mode", "unsupported"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
