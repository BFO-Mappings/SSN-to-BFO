#!/usr/bin/env python3
"""Focused tests for the maintained CCO-extension product."""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import BNode, Graph, RDF, RDFS, OWL, URIRef


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import generate_mapping_from_coms as coms  # noqa: E402
import modular_products as modular  # noqa: E402
from coms_row_identity import RowLocation  # noqa: E402
from product_dispositions import ProductDisposition, load_disposition_document  # noqa: E402
from publication_metadata import (  # noqa: E402
    load_metadata,
    ontology_metadata_rdf_triples,
    strip_emitted_ontology_header,
    validate_emitted_ontology_metadata,
)


EXPECTED_INVENTORY = tuple(
    ("urn:uuid:" + row_id, "sha256:" + axiom_id)
    for row_id, axiom_id in (
        ("124e6b06-906a-47be-a459-92babef3992e", "d0be6196d522ed9650cdfebad33b965d523868a68682405423324b28c54f1e82"),
        ("1a25c5c5-795c-444c-ba3b-e0578f9e715b", "3457b3a3df2aa6fa0356c77e1cfd6ff95dbb450c7e9965c5bf1beb987488a3a1"),
        ("1c52d7ee-ee3d-4eb7-ae42-4df1912ee8eb", "7b6dc290ded8df4f46f20ce28efdc86479348dd0c0746fd31c883e97724b0361"),
        ("2018c5db-cb41-4a54-aa97-df5df82f0286", "8d7dc6c8f9ecc7fc94c23b7a9c5e8603e3013f8dcef2453f4c45f3d4ee8f0f93"),
        ("206e2eaa-765b-491b-ad9c-73f144f048a1", "3f12e123ab52f767626a55a1d07c7d5d85a955e538890927ea02090db15411ab"),
        ("23915904-0174-4f2f-b6cf-6a8671b92d7e", "3c8142551309a66a37dc13ff25eb6fd6b31e7089a776f7391316bacb3705cf1e"),
        ("282b2a18-f710-4eac-a5c8-43894a242f23", "3904c25cf0f62fae33bad65d4d752ae170f94b3678274b151bd6fdd007c4d120"),
        ("287f1392-ca8f-4dc2-9d42-b60b3962adfc", "ac90bbff84f27289fdc5c5fb492323384ea75b344016bb5eb7a4d34a540a8f91"),
        ("2902e2b3-44f8-4f81-8ca9-2def4b68befd", "f1380a66f7734f9b3e29c3e53388eabffa1e5fb296f1e0a192ada48d796a6c2b"),
        ("2a4f78b4-92cb-4095-9a6b-2ae03e00be4a", "c65595bd49e621675a797ec88f0bed32696c176393221adaae8b1a9192cdd842"),
        ("2befdb79-d016-45f8-8c35-69ee93fa731f", "7bcd034eadbf0577e59b123707dd31bbd105681183ea0b8e5cf98914676d3a59"),
        ("304f62a7-9160-4857-9c39-04a7215b1bb0", "6c917d0118060a0a5c8175a486c2880f4948c998bfc384d1494925e0e9e26390"),
        ("326ad20d-f954-44e0-b94f-dccf0fd76ebb", "787e892cd89062b21176fd6a4732cccaba3bd65cddaae2d9c8580e3072b140b9"),
        ("335606ce-18b3-43d9-b13e-7301015c9d26", "2d3f18260f6d804a9e949bda85aca7dcfe2d170b01199991ee8797423dd99a61"),
        ("3734c3b6-e62e-4ae5-be42-8fef0b10d2f4", "72d1a5d3f112c4b7c8d7eb32b1196babbd912b1213beba3c5d2967fbf7221ba0"),
        ("377fa547-ff5c-4ffa-af6f-40d291ab2ab9", "87e268563c3100731545a500259535d0784a692b94e3d42d25ef938a1b5019af"),
        ("3ac135c9-bfd7-49cf-9c51-4d6e9ed56d87", "851caee27c77385ceed70a2deb1a071a3e708361318649f6f62e6b37813791a9"),
        ("3ddcc935-040b-450b-8ffa-8b0972e33c3b", "3638f72bc407bf83119efc46ddbf7364798b8e5afa31a906bc1d736b62d980b1"),
        ("4afaf231-5478-4a50-9a12-0cbf59d78d7e", "14fa695165c7036e41a38bca759038d8c35e8b0b6362c6940d3359cf0143fac1"),
        ("51c8556f-9b82-4113-a9d7-c733e70cf8cd", "66b0f4f770429025a37f6fe8844978ab9e46dc963d0a33ad2a0a55839199cdd1"),
        ("5ec3234d-bd10-4f5b-89f9-f2abb75764ec", "bfcbd5b2f93ee1e69874a2c6918895e693d5f41d44568d2dff24404d9bc519f1"),
        ("6142726b-21b1-4dba-b5ec-a7d6dca4afab", "392dd07207293b5643eb67b0770ba70c84452967e49f1986ccb747ebe8424d6d"),
        ("624eaef2-892a-4b9d-8ed6-08c79571710f", "f7079e239ac89c931c0bf767439ded105c7d1760b7b6e0346551ef3c46d3f759"),
        ("6335c13d-fb23-49fd-9662-fd682c79f172", "fbdef9082a1ce45abecc3ed037f0fb12bb6c376dea196c3912566ee664f50370"),
        ("69e972da-23ad-4e50-822b-e41198c95795", "7b38f4108fd76423fec54f3d4d34f07cc4b4540d5b773f2fd8f52413c6f78f93"),
        ("7b3f908b-b717-4336-9968-8b1083f847d3", "e69a0d20905384f1a3b3e5f9df6b82987f1a1da4e90db05becbc99d980b39168"),
        ("7caa02f4-26a1-4e81-b709-5c2116636f65", "04f2e1c545b6c6f252d9cf377e1e1f325bafa846d37c6b75a975a692ea059963"),
        ("823bbbdf-b4f1-4e45-8b0a-5597306e6b69", "7bfe203db92e7e2b6f107641f3edbbcc111a4b9879471d70e1928b2817c0b853"),
        ("86e97aa4-dc26-4d62-bef6-52cf36869bc8", "25eb572d7c35d5e480c606eddf558b7b5e986136f82f7da5657c857653b81705"),
        ("8897fadf-b70f-4d81-a08c-a072f873f82b", "0aae335885ecdd46575658fe71c7cf073d4dcdda299250671a41f4ab3447536c"),
        ("89f70432-c87d-41dd-bff2-e6120c02b5a4", "c77542ac30e2120d22aefdad6fd59cd22a77690848d2279060e2b545b97e177d"),
        ("8c9662e8-a69c-4ce1-9d17-381ec3cdc162", "cec49555cfb61f5cf5707fd755d31d71059b3b3ead5956a01ebfb820d1ee4eb5"),
        ("98b1044d-6bfe-41d2-89aa-cdc87e524e4c", "a80712efe3f50de428bfde449a3ebdf23c87750872d13a182cf065db7d0b9ae8"),
        ("9c14f13e-16c8-4afd-bcee-8b4bb9d3f0ca", "9210e36acd33fe0b2b119b7f01500e5e0b31c5a0a88808f7002efbcd8f0509b7"),
        ("9ea02b02-c86b-4a0b-a56b-47c1dea0bfa4", "69c3b2b4c146ceb3fddb1d600e12d656e8fe35fcf169d0c4fafa9dff68822b1e"),
        ("a63a89a9-d9e6-4e7d-ba06-96ff17833866", "7e4bf7f39c62e83876b0be229a205fc4bc9f52a846d5b86e049d16adc1f5c1be"),
        ("ad8cba71-f987-4e6a-b9c0-7660d5cbc8a7", "30d80749b62ad19d41ee9ffc6b0176426ab98d2d0b773aad7d4fdf16ee823ac0"),
        ("afc3498b-5446-4c8b-928f-822a8e148b63", "c8c01d3cea6d9185b6c07763b28bec3b25a8e467d2abeeba7dda4edadb99ad61"),
        ("b05ab84c-eeff-45d1-a95d-39cf2d9f084f", "4de8c53cc012a2f7e0322696f11d796ad9db81474e35fcb142b297bb3b714bde"),
        ("b15038bf-7e69-4e62-9cdd-50edb029d88b", "3555605bb2df608876e70c42ec20fa13f80abde4df1a61953beef445621384e2"),
        ("b4fc5247-7d44-4619-9d0b-8466f45218bf", "68c7f27ba59dc05cef448bf3a158a51385a53a955f45a16d5b5de3025fd50149"),
        ("b891bb2b-0093-49ff-aa86-2a68a732686d", "d7147bf65fde2651641479cec361657f97e01137ad2b760e37061eae25cbe368"),
        ("bc709fe5-c239-494c-9b88-c14e5a8fc79e", "7a526678ca98bd78c27db8abd67cc309ea9841c11fa1b6845fe62ade62f3556c"),
        ("c15208c5-847f-4de3-a456-4037142ca542", "e941d1a04c368c1f5129efef4a5d369aae978e8850e6eecfab01bc9244eca46a"),
        ("c912bc86-4ac6-4200-8606-7fda6005542f", "765b6d8892fe2096feba40fd405da8b82eb8e3ea275470c3970146781ba79ecc"),
        ("cbbba7df-22ee-4393-b4fd-46019697192a", "ea0c502c7fe789b98b0bbe26002ac0b18790b13a24580a0e31e06a9891f717ec"),
        ("d180e765-d4d1-4578-a33a-6e96308e01db", "89dc07e0f0e0a2117964d686c2a88b7da77cb761bba5c3cb74b6b6521502cf11"),
        ("d88535da-ab7c-409c-b928-a9b0760b4607", "d0db111747f3564ec1005c04b04a804ebaf5476f273ae2675826b889dfeda719"),
        ("d8b4d0f0-d8d4-4f22-ae7c-2bbdebcdd51f", "dcf3f04234e744a132f942e4d0ce6fe2bb71420cf0c3de60b8163d8b6d9ffe4a"),
        ("d973063c-f3a7-4a0b-ab0f-e0ee1fb9eeaa", "6f6ff88affdc1afbc57c833c7eae38117a3ec8d54b7ac28931e83474e938c6c5"),
        ("dbdcee3f-bbdf-4a35-b92e-a14dd26e6239", "a7156d6ebbd83de2547dbd7e11a2c103e9fd8cc8be71a59c57656e86df5a715f"),
        ("ee7f2f05-bc8e-4477-bb58-0f40e6da81d0", "21d7cb7ddce4687296139d1e503435b53404810ecba690267188a7a6082659b0"),
        ("f293250d-b1e8-4467-8b7d-a94fb2b9b705", "a5469930af6f93dca4bf66f337827b214ff9f4fb940d04f569b4142b69a68154"),
        ("f475ef3c-12f0-4925-ad21-419ebd96406b", "3c778acf36c7687a0a2d38929a849455d40ab77d001b6aa8b8c4586e890d7997"),
        ("f7b8b133-2846-4627-9f8d-1ba39c13b9d1", "3319996395ff5c961d89ef64b955bd227c90bbd762a5184a40e39ef307ea54a8"),
    )
)
EXPECTED_ROW_IDS = frozenset(row_id for row_id, _ in EXPECTED_INVENTORY)
EXPECTED_AXIOM_IDS = frozenset(axiom_id for _, axiom_id in EXPECTED_INVENTORY)
EXPECTED_INVENTORY_SHA256 = "c5587418a9fa0a16b1309609da0eddc8e34e2c2b8ea421069e2f46dd576ac590"


class CcoExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows, stats = coms.read_workbook(REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx")
        cls.processed = coms.validate_and_process_rows(rows, coms.Resolver(), stats)
        cls.canonical_rows = tuple(
            coms.canonical_input_for_processed_row(row) for row in cls.processed
        )
        cls.audits = tuple(row.identity_audit for row in cls.processed)
        cls.disposition = load_disposition_document(
            REPO_ROOT / "reports/coms-product-dispositions.json"
        )
        cls.metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        cls.cco_selected = modular.select_product_axioms(
            "cco_extension", cls.canonical_rows, cls.audits, cls.disposition
        )
        cls.strict_selected = modular.select_product_axioms(
            "strict_bfo_mapping", cls.canonical_rows, cls.audits, cls.disposition
        )
        cls.core_selected = modular.select_product_axioms(
            "alignment_core", cls.canonical_rows, cls.audits, cls.disposition
        )
        cls.cco_result = modular.build_cco_extension(cls.cco_selected, cls.metadata)
        cls.strict_result = modular.build_strict_bfo_mapping(
            cls.strict_selected, cls.metadata
        )
        cls.core_result = modular.build_alignment_core(cls.core_selected, cls.metadata)
        cls.root_graph = Graph().parse(REPO_ROOT / "SSN2BFO.ttl", format="turtle")
        cls.source_graph = Graph()
        for path in coms.SOURCE_IMPORTS:
            cls.source_graph.parse(REPO_ROOT / path, format="turtle")
        cls.merged_dependency = Graph().parse(
            REPO_ROOT / "imports/cco.ttl", format="turtle"
        )
        cls.fixed_closure = modular.build_fixed_validation_closure(
            (
                cls.cco_result.serialized_bytes,
                cls.strict_result.serialized_bytes,
                cls.core_result.serialized_bytes,
            ),
            (
                REPO_ROOT / "imports/cco.ttl",
                *(REPO_ROOT / path for path in coms.SOURCE_IMPORTS),
            ),
        )

    @staticmethod
    def codes(error: modular.ModularProductError) -> set[str]:
        return {value.code for value in error.issues}

    def replace_disposition_row(self, row_id: str, replacement) -> object:
        return dataclasses.replace(
            self.disposition,
            rows=tuple(
                replacement if row.row_id == row_id else row
                for row in self.disposition.rows
            ),
        )

    def validate_bytes(self, data: bytes) -> set[str]:
        return {
            value.code
            for value in modular.validate_cco_extension(
                data,
                self.cco_selected,
                self.strict_result.serialized_bytes,
                self.strict_selected,
                self.core_result.serialized_bytes,
                self.core_selected,
                self.metadata,
                integrated_graph=self.root_graph,
                fixed_semantic_closure=self.fixed_closure,
                source_dependency_graph=self.source_graph,
                merged_cco_bfo_dependency_graph=self.merged_dependency,
            )
        }

    def test_exact_identity_inventory_digest_categories_and_distribution(self) -> None:
        self.assertEqual({value.row_id for value in self.cco_selected}, EXPECTED_ROW_IDS)
        self.assertEqual({value.axiom_id for value in self.cco_selected}, EXPECTED_AXIOM_IDS)
        payload = "\n".join(
            f"{value.row_id}|{value.axiom_id}|{value.identity.canonical_axiom}"
            for value in sorted(
                self.cco_selected, key=lambda item: (item.row_id, item.axiom_id)
            )
        )
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), EXPECTED_INVENTORY_SHA256)
        categories = [value.target_category for value in self.cco_selected]
        self.assertEqual(categories.count("cco_bearing"), 25)
        self.assertEqual(categories.count("mixed_bfo_cco"), 30)
        predicates = [value.canonical_input.predicate_iri for value in self.cco_selected]
        self.assertEqual(predicates.count(str(RDFS.subClassOf)), 31)
        self.assertEqual(predicates.count(str(OWL.equivalentClass)), 7)
        self.assertEqual(predicates.count(str(RDFS.subPropertyOf)), 16)
        self.assertEqual(
            sum(value.canonical_input.mapping_type == "property_chain" for value in self.cco_selected),
            1,
        )

    def test_nonselected_product_policy_is_reconciled(self) -> None:
        counts: dict[str, int] = {}
        zero_axiom_rows = 0
        for row in self.disposition.rows:
            if not row.authoritative_axioms:
                zero_axiom_rows += 1
                continue
            disposition = dict(row.authoritative_axioms[0].product_dispositions)[
                "cco_extension"
            ]
            counts[disposition.status] = counts.get(disposition.status, 0) + 1
        self.assertEqual(zero_axiom_rows, 2)
        self.assertEqual(
            counts,
            {"emitted_unchanged": 55, "provided_through_import": 19, "provided_transitively": 29},
        )

    def test_wrong_disposition_category_and_imported_direct_selection_fail(self) -> None:
        selected_row = next(row for row in self.disposition.rows if row.row_id in EXPECTED_ROW_IDS)
        selected_axiom = selected_row.authoritative_axioms[0]
        wrong = tuple(
            (key, ProductDisposition("provided_through_import"))
            if key == "cco_extension"
            else (key, value)
            for key, value in selected_axiom.product_dispositions
        )
        cases = [
            dataclasses.replace(
                selected_row,
                authoritative_axioms=(dataclasses.replace(selected_axiom, product_dispositions=wrong),),
            ),
            dataclasses.replace(
                selected_row,
                authoritative_axioms=(dataclasses.replace(selected_axiom, target_category="bfo_bearing"),),
            ),
        ]
        for category in ("target_neutral", "bfo_bearing"):
            row = next(
                row
                for row in self.disposition.rows
                if row.authoritative_axioms[0].target_category == category
            )
            axiom = row.authoritative_axioms[0]
            changed = tuple(
                (key, ProductDisposition("emitted_unchanged"))
                if key == "cco_extension"
                else (key, value)
                for key, value in axiom.product_dispositions
            )
            cases.append(
                dataclasses.replace(
                    row,
                    authoritative_axioms=(dataclasses.replace(axiom, product_dispositions=changed),),
                )
            )
        for changed in cases:
            with self.subTest(row_id=changed.row_id):
                with self.assertRaises(modular.ModularProductError):
                    modular.select_product_axioms(
                        "cco_extension",
                        self.canonical_rows,
                        self.audits,
                        self.replace_disposition_row(changed.row_id, changed),
                    )

    def test_missing_extra_duplicate_substituted_and_mismatched_identities_fail(self) -> None:
        replacement = dataclasses.replace(
            self.canonical_rows[0],
            row_id="urn:uuid:ffffffff-ffff-4fff-8fff-ffffffffffff",
        )
        for rows in (
            self.canonical_rows[1:],
            (*self.canonical_rows, replacement),
            (replacement, *self.canonical_rows[1:]),
            (*self.canonical_rows, self.canonical_rows[0]),
        ):
            with self.assertRaises(modular.ModularProductError):
                modular.select_product_axioms(
                    "cco_extension", rows, self.audits, self.disposition
                )

        selected_row = next(row for row in self.disposition.rows if row.row_id in EXPECTED_ROW_IDS)
        axiom = selected_row.authoritative_axioms[0]
        for changed in (
            dataclasses.replace(selected_row, authoritative_axioms=()),
            dataclasses.replace(
                selected_row,
                authoritative_axioms=(dataclasses.replace(axiom, axiom_id="sha256:" + "0" * 64),),
            ),
            dataclasses.replace(selected_row, authoritative_axioms=(axiom, axiom)),
            dataclasses.replace(
                selected_row,
                authoritative_axioms=(dataclasses.replace(axiom, canonical_expression="Changed"),),
            ),
        ):
            with self.assertRaises(modular.ModularProductError):
                modular.select_product_axioms(
                    "cco_extension",
                    self.canonical_rows,
                    self.audits,
                    self.replace_disposition_row(selected_row.row_id, changed),
                )

        row = self.canonical_rows[0]
        moved = dataclasses.replace(row, location=RowLocation("Other", row.location.row_number))
        changed_audits = (
            dataclasses.replace(self.audits[0], source_expression_sha256="0" * 64),
            dataclasses.replace(
                self.audits[0],
                expression=dataclasses.replace(
                    self.audits[0].expression,
                    target="<http://example.org/Changed>",
                ),
            ),
        )
        with self.assertRaises(modular.ModularProductError):
            modular.select_product_axioms(
                "cco_extension", (moved, *self.canonical_rows[1:]), self.audits, self.disposition
            )
        for changed in changed_audits:
            with self.assertRaises(modular.ModularProductError):
                modular.select_product_axioms(
                    "cco_extension",
                    self.canonical_rows,
                    (changed, *self.audits[1:]),
                    self.disposition,
                )

    def test_direct_graph_identity_import_counts_and_structures(self) -> None:
        graph = Graph().parse(data=self.cco_result.serialized_bytes.decode(), format="turtle")
        ontology = URIRef("http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension")
        strict = URIRef("http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping")
        self.assertEqual(set(graph.subjects(RDF.type, OWL.Ontology)), {ontology})
        self.assertEqual(set(graph.triples((None, OWL.imports, None))), {(ontology, OWL.imports, strict)})
        self.assertEqual(self.cco_result.logical_triple_count, 924)
        self.assertEqual(self.cco_result.ontology_declaration_triple_count, 1)
        self.assertEqual(self.cco_result.import_triple_count, 1)
        self.assertEqual(self.cco_result.metadata_annotation_count, 7)
        self.assertEqual(len(graph), 933)
        self.assertEqual(
            set(ontology_metadata_rdf_triples(self.metadata, "cco_extension")),
            set(graph.triples((ontology, None, None)))
            - {
                (ontology, RDF.type, OWL.Ontology),
                (ontology, OWL.imports, strict),
            },
        )
        self.assertEqual(
            validate_emitted_ontology_metadata(
                graph,
                self.metadata,
                "cco_extension",
                (str(strict),),
            ),
            (),
        )
        self.assertEqual(
            len(
                strip_emitted_ontology_header(
                    graph,
                    self.metadata,
                    "cco_extension",
                    (str(strict),),
                )
            ),
            924,
        )
        self.assertEqual(len(set(graph.subjects(OWL.unionOf, None))), 7)
        self.assertEqual(len(set(graph.subjects(OWL.intersectionOf, None))), 86)
        self.assertEqual(len(set(graph.subjects(OWL.someValuesFrom, None))), 95)
        self.assertEqual(len(set(graph.subjects(OWL.propertyChainAxiom, None))), 1)
        self.assertEqual(self.cco_result.rdf_list_count, 94)
        self.assertFalse(any(True for _ in graph.triples((None, OWL.inverseOf, None))))
        self.assertEqual(self.validate_bytes(self.cco_result.serialized_bytes), set())

    def test_import_vocabulary_and_copied_declarations_are_rejected(self) -> None:
        graph = Graph().parse(data=self.cco_result.serialized_bytes.decode(), format="turtle")
        ontology = URIRef(self.cco_result.metadata.stable_ontology_iri)
        graph.add((ontology, OWL.imports, URIRef("http://example.org/external")))
        graph.add((URIRef("http://www.w3.org/ns/sosa/Sensor"), RDF.type, OWL.Class))
        graph.add((URIRef("http://purl.obolibrary.org/obo/BFO_0000001"), RDF.type, OWL.Class))
        graph.add((URIRef("https://www.commoncoreontologies.org/ont00000001"), RDF.type, OWL.Class))
        graph.add((BNode("annotation"), RDF.type, OWL.Axiom))
        codes = self.validate_bytes(graph.serialize(format="turtle").encode())
        self.assertIn("IMPORT_POLICY_MISMATCH", codes)
        self.assertIn("COPIED_SOURCE_DECLARATION", codes)
        self.assertIn("COPIED_BFO_DECLARATION", codes)
        self.assertIn("COPIED_CCO_DECLARATION", codes)
        self.assertIn("ANNOTATION_ONLY_PSEUDO_MAPPING", codes)
        original = b"https://www.commoncoreontologies.org/ont00001986"
        for replacement in (
            b"http://purl.obolibrary.org/obo/RO_0000052",
            b"http://example.org/UnexpectedVocabulary",
        ):
            codes = self.validate_bytes(
                self.cco_result.serialized_bytes.replace(original, replacement, 1)
            )
            self.assertTrue(
                codes & {"PROHIBITED_LOGICAL_VOCABULARY", "UNEXPECTED_LOGICAL_VOCABULARY"}
            )

    def test_determinism_reordered_inputs_and_existing_product_preservation(self) -> None:
        reordered_selected = modular.select_product_axioms(
            "cco_extension",
            tuple(reversed(self.canonical_rows)),
            tuple(reversed(self.audits)),
            self.disposition,
        )
        reordered = modular.build_cco_extension(
            tuple(reversed(reordered_selected)), self.metadata
        )
        self.assertEqual(reordered.serialized_bytes, self.cco_result.serialized_bytes)
        self.assertTrue(self.cco_result.serialized_bytes.endswith(b"\n"))
        self.assertFalse(self.cco_result.serialized_bytes.endswith(b"\n\n"))
        self.assertEqual(
            self.cco_result.sha256,
            "2908f89648d42dc928f7225056216f1cbf3bcdc79de1bcf770b40a017a5e9bf5",
        )
        self.assertEqual(
            hashlib.sha256(self.core_result.serialized_bytes).hexdigest(),
            "17695ef17379924449153b2c92ffaed6b57d497a1b2d1e854f584614cebec770",
        )
        self.assertEqual(
            hashlib.sha256(self.strict_result.serialized_bytes).hexdigest(),
            "676b31620df10db5c26c46bcc44b2dfd5939d606b16e0fa8a910926e8497c3af",
        )

    def test_reordered_canonical_header_is_rejected_by_product_validator(self) -> None:
        lines = self.cco_result.serialized_bytes.splitlines()
        label = next(i for i, line in enumerate(lines) if line.startswith(b"    rdfs:label "))
        description = next(
            i for i, line in enumerate(lines) if line.startswith(b"    dcterms:description ")
        )
        lines[label], lines[description] = lines[description], lines[label]
        self.assertIn(
            "NONCANONICAL_ONTOLOGY_HEADER",
            self.validate_bytes(b"\n".join(lines) + b"\n"),
        )

    def test_fresh_process_generation_is_byte_deterministic(self) -> None:
        code = (
            "from pathlib import Path; import hashlib; "
            "import generate_mapping_from_coms as g; "
            "from product_dispositions import load_disposition_document; "
            "from publication_metadata import load_metadata; "
            "from modular_products import select_product_axioms,build_cco_extension; "
            "r,s=g.read_workbook(Path('mappings/SSN2BFO-COMS.xlsx')); "
            "p=g.validate_and_process_rows(r,g.Resolver(),s); "
            "c=[g.canonical_input_for_processed_row(x) for x in p]; "
            "a=[x.identity_audit for x in p]; "
            "d=load_disposition_document('reports/coms-product-dispositions.json'); "
            "m=load_metadata('config/publication-metadata.toml'); "
            "x=build_cco_extension(select_product_axioms('cco_extension',c,a,d),m); "
            "print(hashlib.sha256(x.serialized_bytes).hexdigest())"
        )
        values = []
        for _ in range(2):
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=REPO_ROOT,
                env={"PYTHONPATH": str(REPO_ROOT / "tools")},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            values.append(proc.stdout.strip())
        self.assertEqual(values, [self.cco_result.sha256, self.cco_result.sha256])

    def test_root_project_closure_and_fixed_term_resolution(self) -> None:
        self.assertEqual(self.validate_bytes(self.cco_result.serialized_bytes), set())
        cco_ids = {value.axiom_id for value in self.cco_selected}
        strict_ids = {value.axiom_id for value in self.strict_selected}
        core_ids = {value.axiom_id for value in self.core_selected}
        self.assertFalse(cco_ids & strict_ids)
        self.assertFalse(cco_ids & core_ids)
        self.assertFalse(strict_ids & core_ids)
        self.assertEqual(len(cco_ids | strict_ids | core_ids), 103)
        graph = Graph().parse(data=self.cco_result.serialized_bytes.decode(), format="turtle")
        graph.parse(data=self.strict_result.serialized_bytes.decode(), format="turtle")
        graph.parse(data=self.core_result.serialized_bytes.decode(), format="turtle")
        self.assertEqual(len(graph), 1128)
        for triple in list(graph.triples((None, OWL.imports, None))):
            graph.remove(triple)
        self.assertEqual(len(graph), 1126)
        self.assertEqual(len(self.fixed_closure), 15920)
        self.assertTrue(
            all(
                triple in self.fixed_closure
                for triple in coms.SAMPLE_PROPERTY_SOURCE_DECLARATIONS
            )
        )
        self.assertFalse(any(True for _ in self.fixed_closure.triples((None, OWL.imports, None))))

    def test_pinned_closure_hermit_is_clean(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cco-extension-hermit-") as temp:
            root = Path(temp)
            cco_path = root / "cco.ttl"
            strict_path = root / "strict.ttl"
            core_path = root / "core.ttl"
            cco_path.write_bytes(self.cco_result.serialized_bytes)
            strict_path.write_bytes(self.strict_result.serialized_bytes)
            core_path.write_bytes(self.core_result.serialized_bytes)
            result = coms.run_cco_extension_hermit(
                cco_path, strict_path, core_path, root / "reasoner"
            )
        self.assertTrue(result.passed, result.robot_output)
        self.assertEqual(result.return_code, 0)
        self.assertTrue(result.reasoned_output_produced)
        self.assertEqual(result.closure_triple_count, 15920)
        self.assertTrue(result.profile_checked)
        self.assertEqual(result.profile_triple_count, 15924)
        self.assertEqual(result.profile_declaration_completion_count, 4)
        self.assertEqual(result.profile_return_code, 0)
        self.assertTrue(result.source_sample_declarations_retained)
        self.assertEqual(result.unsat_classes, [])


if __name__ == "__main__":
    unittest.main()
