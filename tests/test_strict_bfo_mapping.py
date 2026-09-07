#!/usr/bin/env python3
"""Focused tests for the maintained strict BFO mapping product."""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import BNode, Graph, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection


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


EXPECTED_ROW_IDS = frozenset(
    "urn:uuid:" + value
    for value in (
        "02294d3c-f88d-4d3d-921e-8d6c00457476",
        "06782965-88c5-4345-ab99-ea027513ec86",
        "158c0cce-2c1d-4baf-90b5-243d7cdce34d",
        "17528e16-1f22-4c6e-9e29-e3b3c6699804",
        "1b7c27d4-1b0e-461f-8a77-7a81631ab342",
        "2abe4468-736d-4db8-99d7-1670730a6710",
        "37576663-68e9-4298-8652-a3c614c34ae3",
        "3af8734c-ac86-46b0-8c0c-27a19525bc1e",
        "43ad1a14-e8a4-48d5-ae2b-3b5a5b28f8d3",
        "66010702-8134-4e08-a972-f0767ec8dead",
        "6c58598b-8de6-4559-82fa-53a6efc6a3c4",
        "99b22791-b2d1-4667-901e-861a44f2b8a2",
        "af48aae7-263f-436d-a76a-4e7232c609c5",
        "b1421726-3675-4b2a-9824-150e108157e4",
        "b4508c03-1b79-4f53-b525-d5db6d80c7cb",
        "c0a94c70-33c7-41ac-8906-49ad2efe48b5",
        "d8f45381-cd95-4251-ae69-803a033a8f49",
        "e866de80-683d-4138-a713-be9646d37148",
        "f0fbd0af-655a-46c8-bda9-1c2adb24a10a",
    )
)

EXPECTED_AXIOM_IDS = frozenset(
    "sha256:" + value
    for value in (
        "0caeec31770247fe2efeb443e85fefe9b4e1648a7d9569adc35d2972b77682b1",
        "ebc5a554a5a02d96a177a4905b1f58369c2a1b3cb0c5e952b40208fd3d70f720",
        "a967fdeccb6b435f0f84de94b976dec27307580651a7d16a08b900be0daa4dd1",
        "cb03fd4e0013c6cb36cdae6f435a71662e5ace11c4b60fd6121e30a58cfddbaf",
        "f0ed25535d9f911882545913dac2c83339346e2ca16a5e939b2a2e27cd5f1c4e",
        "39946148848f627dc9bd67601c5d0d1184960c34054c876541a77fa9d42e3d6b",
        "4ee0a31d0d7abc626e19715ee1f31b610823136f2ea133155491a644f72db22a",
        "90d2b3a965084a150dcd254003bbdd2e5d706d8dd1b7a941c44e44ee2ea1737e",
        "6dfa77b04dfaea343d0a8767e6467c603eafddf10395ff40ac7416f52c7fd4d4",
        "0db60d0e9764151246aa7f88574dbc9fb112eecb2191d00822192f51ec298678",
        "205b4f09b9778256d60879903b8e03e20a284c0ce6d3dd085b87d5c2e3b44cad",
        "5606980322dc337a4e5d0eb2daef2e5acbba7ee42a782247375fcf3f39d12e00",
        "20d91e47601ba6ee027a45b1292383a93db5223addd66a57f6b0ce832054b0d6",
        "e97401fddd65d2c240938d965cb3ecb82f52b396f7fbdc7ccee0de7edf3ff74b",
        "480ce3257f6b1baaaacee7b06ce730cdf63a7dd14c16b4a1bedc09597a5d96ef",
        "3e6d4c8e6ae7f32b3fde12f2e976c4c91ea66a0893e45ae7a3bb7ddf974dafba",
        "9df2ac96dda81289facb4e871c73c208fa2ae4fc7f33cfd9bc293c8e50b0439c",
        "47859e2cfd5df437d1f55c83560793ab22f035de9b829ccdedcc4d3118cc4f3e",
        "b87f9b4fe09c1df974c9c698e4501efaab8762b8a376aa207f83810b6f2ae7dd",
    )
)


class StrictBfoMappingTests(unittest.TestCase):
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
        cls.strict_selected = modular.select_product_axioms(
            "strict_bfo_mapping",
            cls.canonical_rows,
            cls.audits,
            cls.disposition,
        )
        cls.core_selected = modular.select_product_axioms(
            "alignment_core",
            cls.canonical_rows,
            cls.audits,
            cls.disposition,
        )
        cls.strict_result = modular.build_strict_bfo_mapping(
            cls.strict_selected, cls.metadata
        )
        cls.core_result = modular.build_alignment_core(cls.core_selected, cls.metadata)
        cls.root_graph = Graph().parse(REPO_ROOT / "SSN2BFO.ttl", format="turtle")

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

    def validate_bytes(self, data: bytes, *, closure: Graph | None = None) -> set[str]:
        return {
            value.code
            for value in modular.validate_strict_bfo_mapping(
                data,
                self.strict_selected,
                self.core_result.serialized_bytes,
                self.core_selected,
                self.metadata,
                integrated_graph=self.root_graph,
                fixed_semantic_closure=closure,
            )
        }

    def test_exact_selection_identity_lock_and_distribution(self) -> None:
        self.assertEqual({value.row_id for value in self.strict_selected}, EXPECTED_ROW_IDS)
        self.assertEqual({value.axiom_id for value in self.strict_selected}, EXPECTED_AXIOM_IDS)
        predicates = [value.canonical_input.predicate_iri for value in self.strict_selected]
        self.assertEqual(predicates.count(str(RDFS.subClassOf)), 3)
        self.assertEqual(predicates.count(str(OWL.equivalentClass)), 3)
        self.assertEqual(predicates.count(str(RDFS.subPropertyOf)), 9)
        self.assertEqual(
            sum(value.canonical_input.mapping_type == "property_chain" for value in self.strict_selected),
            2,
        )
        self.assertEqual(sum(value.canonical_input.mapping_type == "domain" for value in self.strict_selected), 1)
        self.assertEqual(sum(value.canonical_input.mapping_type == "range" for value in self.strict_selected), 1)

    def test_nonselected_product_policy_is_reconciled(self) -> None:
        counts = {"provided_through_import": 0, "deferred": 0, "emitted_unchanged": 0}
        zero_axiom_rows = 0
        for row in self.disposition.rows:
            if not row.authoritative_axioms:
                zero_axiom_rows += 1
                continue
            disposition = dict(row.authoritative_axioms[0].product_dispositions)[
                "strict_bfo_mapping"
            ]
            counts[disposition.status] += 1
        self.assertEqual(zero_axiom_rows, 2)
        self.assertEqual(
            counts,
            {
                "provided_through_import": 29,
                "deferred": 55,
                "emitted_unchanged": 19,
            },
        )

    def test_wrong_disposition_category_and_prohibited_direct_selection_fail(self) -> None:
        cases = []
        strict_row = next(row for row in self.disposition.rows if row.row_id in EXPECTED_ROW_IDS)
        strict_axiom = strict_row.authoritative_axioms[0]
        wrong_strict = tuple(
            (key, ProductDisposition("provided_through_import"))
            if key == "strict_bfo_mapping"
            else (key, value)
            for key, value in strict_axiom.product_dispositions
        )
        cases.append(
            dataclasses.replace(
                strict_row,
                authoritative_axioms=(dataclasses.replace(strict_axiom, product_dispositions=wrong_strict),),
            )
        )
        cases.append(
            dataclasses.replace(
                strict_row,
                authoritative_axioms=(dataclasses.replace(strict_axiom, target_category="target_neutral"),),
            )
        )
        for category in ("target_neutral", "cco_bearing", "mixed_bfo_cco"):
            row = next(
                row
                for row in self.disposition.rows
                if row.authoritative_axioms[0].target_category == category
            )
            axiom = row.authoritative_axioms[0]
            changed_dispositions = tuple(
                (key, ProductDisposition("emitted_unchanged"))
                if key == "strict_bfo_mapping"
                else (key, value)
                for key, value in axiom.product_dispositions
            )
            cases.append(
                dataclasses.replace(
                    row,
                    authoritative_axioms=(dataclasses.replace(axiom, product_dispositions=changed_dispositions),),
                )
            )
        for changed in cases:
            with self.subTest(row_id=changed.row_id):
                with self.assertRaises(modular.ModularProductError) as raised:
                    modular.select_product_axioms(
                        "strict_bfo_mapping",
                        self.canonical_rows,
                        self.audits,
                        self.replace_disposition_row(changed.row_id, changed),
                    )
                self.assertTrue(
                    self.codes(raised.exception)
                    & {"WRONG_PRODUCT_DISPOSITION", "TARGET_CATEGORY_MISMATCH"}
                )

    def test_missing_extra_duplicate_and_substituted_row_ids_fail(self) -> None:
        replacement = dataclasses.replace(
            self.canonical_rows[0],
            row_id="urn:uuid:ffffffff-ffff-4fff-8fff-ffffffffffff",
        )
        duplicate = (*self.canonical_rows, self.canonical_rows[0])
        for rows in (
            self.canonical_rows[1:],
            (*self.canonical_rows, replacement),
            (replacement, *self.canonical_rows[1:]),
            duplicate,
        ):
            with self.subTest(count=len(rows)):
                with self.assertRaises(modular.ModularProductError):
                    modular.select_product_axioms(
                        "strict_bfo_mapping", rows, self.audits, self.disposition
                    )

    def test_axiom_identity_location_hash_and_expression_mismatches_fail(self) -> None:
        selected_row = next(row for row in self.disposition.rows if row.row_id in EXPECTED_ROW_IDS)
        axiom = selected_row.authoritative_axioms[0]
        changed_rows = (
            dataclasses.replace(selected_row, authoritative_axioms=()),
            dataclasses.replace(
                selected_row,
                authoritative_axioms=(dataclasses.replace(axiom, axiom_id="sha256:" + "0" * 64),),
            ),
            dataclasses.replace(selected_row, authoritative_axioms=(axiom, axiom)),
        )
        for changed in changed_rows:
            with self.assertRaises(modular.ModularProductError):
                modular.select_product_axioms(
                    "strict_bfo_mapping",
                    self.canonical_rows,
                    self.audits,
                    self.replace_disposition_row(selected_row.row_id, changed),
                )
        row = self.canonical_rows[0]
        moved = dataclasses.replace(row, location=RowLocation("Other", row.location.row_number))
        with self.assertRaises(modular.ModularProductError) as raised:
            modular.select_product_axioms(
                "strict_bfo_mapping", (moved, *self.canonical_rows[1:]), self.audits, self.disposition
            )
        self.assertIn("ROW_LOCATION_MISMATCH", self.codes(raised.exception))
        for changed in (
            dataclasses.replace(self.audits[0], source_expression_sha256="0" * 64),
            dataclasses.replace(
                self.audits[0],
                expression=dataclasses.replace(
                    self.audits[0].expression,
                    target="<http://example.org/Changed>",
                ),
            ),
        ):
            with self.assertRaises(modular.ModularProductError):
                modular.select_product_axioms(
                    "strict_bfo_mapping",
                    self.canonical_rows,
                    (changed, *self.audits[1:]),
                    self.disposition,
                )

    def test_duplicate_axiom_and_wrong_count_fail_build(self) -> None:
        for selected in (
            (*self.strict_selected, self.strict_selected[0]),
            self.strict_selected[:-1],
        ):
            with self.assertRaises(modular.ModularProductError):
                modular.build_strict_bfo_mapping(selected, self.metadata)

    def test_direct_graph_identity_import_counts_and_structures(self) -> None:
        graph = Graph().parse(data=self.strict_result.serialized_bytes.decode(), format="turtle")
        ontology = URIRef("http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping")
        core = URIRef("http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core")
        self.assertEqual(set(graph.subjects(RDF.type, OWL.Ontology)), {ontology})
        self.assertEqual(set(graph.triples((None, OWL.imports, None))), {(ontology, OWL.imports, core)})
        self.assertEqual(self.strict_result.logical_triple_count, 125)
        self.assertEqual(self.strict_result.ontology_declaration_triple_count, 1)
        self.assertEqual(self.strict_result.import_triple_count, 1)
        self.assertEqual(self.strict_result.metadata_annotation_count, 7)
        self.assertEqual(len(graph), 134)
        self.assertEqual(
            set(ontology_metadata_rdf_triples(self.metadata, "strict_bfo_mapping")),
            set(graph.triples((ontology, None, None)))
            - {
                (ontology, RDF.type, OWL.Ontology),
                (ontology, OWL.imports, core),
            },
        )
        self.assertEqual(
            validate_emitted_ontology_metadata(
                graph,
                self.metadata,
                "strict_bfo_mapping",
                (str(core),),
            ),
            (),
        )
        self.assertEqual(
            len(
                strip_emitted_ontology_header(
                    graph,
                    self.metadata,
                    "strict_bfo_mapping",
                    (str(core),),
                )
            ),
            125,
        )
        self.assertEqual(len(set(graph.subjects(OWL.unionOf, None))), 6)
        self.assertEqual(len(set(graph.subjects(OWL.intersectionOf, None))), 6)
        self.assertEqual(len(set(graph.subjects(OWL.someValuesFrom, None))), 6)
        chains = set(graph.subjects(OWL.propertyChainAxiom, None))
        self.assertEqual(len(chains), 2)
        self.assertTrue(
            all(len(list(Collection(graph, next(graph.objects(chain, OWL.propertyChainAxiom))))) == 3 for chain in chains)
        )
        self.assertEqual(self.strict_result.rdf_list_count, 14)
        self.assertFalse(any(True for _ in graph.triples((None, OWL.inverseOf, None))))

    def test_import_vocabulary_and_copied_declarations_are_rejected(self) -> None:
        graph = Graph().parse(data=self.strict_result.serialized_bytes.decode(), format="turtle")
        ontology = URIRef(self.strict_result.metadata.stable_ontology_iri)
        graph.add((ontology, OWL.imports, URIRef("http://example.org/external")))
        graph.add((URIRef("http://www.w3.org/ns/sosa/Sensor"), RDF.type, OWL.Class))
        graph.add((URIRef("http://purl.obolibrary.org/obo/BFO_0000001"), RDF.type, OWL.Class))
        graph.add((BNode("annotation"), RDF.type, OWL.Axiom))
        data = graph.serialize(format="turtle").encode()
        codes = self.validate_bytes(data)
        self.assertIn("IMPORT_POLICY_MISMATCH", codes)
        self.assertIn("COPIED_SOURCE_DECLARATION", codes)
        self.assertIn("COPIED_BFO_DECLARATION", codes)
        self.assertIn("ANNOTATION_ONLY_PSEUDO_MAPPING", codes)
        for original, replacement in (
            (b"http://purl.obolibrary.org/obo/BFO_0000001", b"https://www.commoncoreontologies.org/Artifact"),
            (b"http://purl.obolibrary.org/obo/BFO_0000001", b"http://purl.obolibrary.org/obo/RO_0000052"),
            (b"http://purl.obolibrary.org/obo/BFO_0000001", b"http://example.org/Unexpected"),
        ):
            if original in self.strict_result.serialized_bytes:
                self.assertTrue(
                    self.validate_bytes(self.strict_result.serialized_bytes.replace(original, replacement, 1))
                    & {"PROHIBITED_LOGICAL_VOCABULARY", "UNEXPECTED_LOGICAL_VOCABULARY"}
                )

    def test_deterministic_serialization_and_alignment_core_preservation(self) -> None:
        reversed_result = modular.build_strict_bfo_mapping(
            tuple(reversed(self.strict_selected)), self.metadata
        )
        self.assertEqual(reversed_result.serialized_bytes, self.strict_result.serialized_bytes)
        self.assertTrue(self.strict_result.serialized_bytes.endswith(b"\n"))
        self.assertFalse(self.strict_result.serialized_bytes.endswith(b"\n\n"))
        self.assertEqual(
            hashlib.sha256(self.core_result.serialized_bytes).hexdigest(),
            "17695ef17379924449153b2c92ffaed6b57d497a1b2d1e854f584614cebec770",
        )

    def test_reordered_canonical_header_is_rejected_by_product_validator(self) -> None:
        lines = self.strict_result.serialized_bytes.splitlines()
        label = next(i for i, line in enumerate(lines) if line.startswith(b"    rdfs:label "))
        description = next(
            i for i, line in enumerate(lines) if line.startswith(b"    dcterms:description ")
        )
        lines[label], lines[description] = lines[description], lines[label]
        self.assertIn(
            "NONCANONICAL_ONTOLOGY_HEADER",
            self.validate_bytes(b"\n".join(lines) + b"\n"),
        )

    def test_processed_row_and_audit_order_do_not_affect_strict_bfo_output(self) -> None:
        baseline_selected = modular.select_product_axioms(
            "strict_bfo_mapping",
            self.canonical_rows,
            self.audits,
            self.disposition,
        )
        baseline_result = modular.build_strict_bfo_mapping(
            baseline_selected,
            self.metadata,
        )
        reordered_selected = modular.select_product_axioms(
            "strict_bfo_mapping",
            tuple(reversed(self.canonical_rows)),
            tuple(reversed(self.audits)),
            self.disposition,
        )
        reordered_result = modular.build_strict_bfo_mapping(
            reordered_selected,
            self.metadata,
        )

        self.assertEqual(len(reordered_selected), 19)
        self.assertEqual(
            {value.row_id for value in reordered_selected},
            {value.row_id for value in baseline_selected},
        )
        self.assertEqual(
            {value.axiom_id for value in reordered_selected},
            {value.axiom_id for value in baseline_selected},
        )
        baseline_bytes = modular.serialize_modular_product(baseline_result)
        reordered_bytes = modular.serialize_modular_product(reordered_result)
        self.assertEqual(reordered_bytes, baseline_bytes)
        self.assertEqual(
            hashlib.sha256(reordered_bytes).hexdigest(),
            "676b31620df10db5c26c46bcc44b2dfd5939d606b16e0fa8a910926e8497c3af",
        )

    def test_fresh_process_generation_is_byte_deterministic(self) -> None:
        code = (
            "from pathlib import Path; import hashlib; "
            "import generate_mapping_from_coms as g; "
            "from product_dispositions import load_disposition_document; "
            "from publication_metadata import load_metadata; "
            "from modular_products import select_product_axioms,build_strict_bfo_mapping; "
            "r,s=g.read_workbook(Path('mappings/SSN2BFO-COMS.xlsx')); "
            "p=g.validate_and_process_rows(r,g.Resolver(),s); "
            "c=[g.canonical_input_for_processed_row(x) for x in p]; "
            "a=[x.identity_audit for x in p]; "
            "d=load_disposition_document('reports/coms-product-dispositions.json'); "
            "m=load_metadata('config/publication-metadata.toml'); "
            "x=build_strict_bfo_mapping(select_product_axioms('strict_bfo_mapping',c,a,d),m); "
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
        self.assertEqual(values, [self.strict_result.sha256, self.strict_result.sha256])

    def test_root_and_project_module_reconciliation(self) -> None:
        self.assertEqual(
            modular.validate_strict_bfo_mapping(
                self.strict_result.serialized_bytes,
                self.strict_selected,
                self.core_result.serialized_bytes,
                self.core_selected,
                self.metadata,
                integrated_graph=self.root_graph,
            ),
            (),
        )
        strict_ids = {value.axiom_id for value in self.strict_selected}
        core_ids = {value.axiom_id for value in self.core_selected}
        self.assertFalse(strict_ids & core_ids)
        self.assertEqual(len(strict_ids | core_ids), 48)
        graph = Graph().parse(data=self.strict_result.serialized_bytes.decode(), format="turtle")
        graph.parse(data=self.core_result.serialized_bytes.decode(), format="turtle")
        self.assertEqual(len(graph), 195)
        for triple in list(graph.triples((None, OWL.imports, None))):
            graph.remove(triple)
        self.assertEqual(len(graph), 194)

    def test_fixed_pinned_merged_cco_bfo_closure(self) -> None:
        dependencies = (
            REPO_ROOT / "imports/cco.ttl",
            REPO_ROOT / "imports/sosa.ttl",
            REPO_ROOT / "imports/sosa-sampling.ttl",
            REPO_ROOT / "imports/ssn.ttl",
            REPO_ROOT / "imports/ssn-systems.ttl",
        )
        self.assertTrue(all(path.is_file() for path in dependencies))
        closure = modular.build_fixed_validation_closure(
            (self.strict_result.serialized_bytes, self.core_result.serialized_bytes),
            dependencies,
        )
        self.assertEqual(len(closure), 14988)
        self.assertTrue(
            all(
                triple in closure
                for triple in coms.SAMPLE_PROPERTY_SOURCE_DECLARATIONS
            )
        )
        self.assertFalse(any(True for _ in closure.triples((None, OWL.imports, None))))
        bfo_iris = {
            iri
            for selected in self.strict_selected
            for iri in modular.axiom_input_from_canonical_row(
                selected.identity,
                selected.canonical_input,
            ).target_iris
            if iri.startswith(modular.BFO_NAMESPACE)
        }
        self.assertEqual(len(bfo_iris), 14)
        cco = Graph().parse(REPO_ROOT / "imports/cco.ttl", format="turtle")
        self.assertTrue(all(any(True for _ in cco.triples((URIRef(iri), None, None))) for iri in bfo_iris))
        self.assertEqual(self.validate_bytes(self.strict_result.serialized_bytes, closure=closure), set())

    def test_pinned_closure_hermit_is_clean(self) -> None:
        with tempfile.TemporaryDirectory(prefix="strict-bfo-hermit-") as temp:
            root = Path(temp)
            strict_path = root / "strict.ttl"
            core_path = root / "core.ttl"
            strict_path.write_bytes(self.strict_result.serialized_bytes)
            core_path.write_bytes(self.core_result.serialized_bytes)
            result = coms.run_strict_bfo_hermit(strict_path, core_path, root / "reasoner")
        self.assertTrue(result.passed, result.robot_output)
        self.assertEqual(result.return_code, 0)
        self.assertTrue(result.reasoned_output_produced)
        self.assertEqual(result.closure_triple_count, 14988)
        self.assertTrue(result.profile_checked)
        self.assertEqual(result.profile_triple_count, 14992)
        self.assertEqual(result.profile_declaration_completion_count, 4)
        self.assertEqual(result.profile_return_code, 0)
        self.assertTrue(result.source_sample_declarations_retained)
        self.assertEqual(result.unsat_classes, [])


if __name__ == "__main__":
    unittest.main()
