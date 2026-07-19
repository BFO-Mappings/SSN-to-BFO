#!/usr/bin/env python3
"""Focused tests for generated modular ontology products."""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

from rdflib import BNode, Graph, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import generate_mapping_from_coms as coms  # noqa: E402
import modular_products as modular  # noqa: E402
from coms_row_identity import ExpressionNode, RowLocation  # noqa: E402
from product_dispositions import ProductDisposition, load_disposition_document  # noqa: E402
from publication_metadata import (  # noqa: E402
    load_metadata,
    ontology_metadata_rdf_triples,
    strip_emitted_ontology_header,
    validate_emitted_ontology_metadata,
)


EXPECTED_ROW_IDS = frozenset(
    {
        "urn:uuid:b16f1d3a-3d10-4b75-9f12-2331e6c46d74",
        "urn:uuid:01b1aff2-a12b-430b-9775-b43241c3a7cf",
        "urn:uuid:b5a532fc-5dea-4a47-9323-0a78a849c078",
        "urn:uuid:e15cfee1-3c8e-4519-bce0-ec62729fd2fd",
        "urn:uuid:79e12baa-9467-4494-bdf3-b6906f5a81a7",
        "urn:uuid:d5712b64-a526-4112-ba23-520ec8dc5066",
        "urn:uuid:37fac05e-0d70-420d-a0c0-78bc1d87cd63",
        "urn:uuid:61fc3404-f33a-4c4c-a25c-412d9972016c",
        "urn:uuid:5ce06556-de99-44be-922d-a3d092a00dbb",
        "urn:uuid:01085646-1b07-4c69-a39a-0c5c8ab53d33",
        "urn:uuid:0f9d6fa9-00b9-4602-b31d-9e205f53e67d",
        "urn:uuid:675bb221-ad63-4033-9f22-5190d0b6d545",
        "urn:uuid:ac95c1e2-0d93-48de-be9d-4defbe6525f0",
        "urn:uuid:434602eb-cfc3-4bca-9fb3-92154e87c6bc",
        "urn:uuid:99f8aba6-abaa-49de-a126-da1573f24c39",
        "urn:uuid:839fa73d-6601-4b17-9331-062846ba0f3e",
        "urn:uuid:e2d7f509-a5ee-477a-9660-f608b518ea3f",
        "urn:uuid:265137eb-a279-4f9a-b1b9-e85d7ecb02a7",
        "urn:uuid:8b87dd5b-298e-4ae7-8724-3778c0a67234",
        "urn:uuid:82ce9316-b7a7-4655-9c98-e16c314a0244",
        "urn:uuid:bd5a2014-f338-49b8-b7ef-27f5b933d93b",
        "urn:uuid:5f25dce9-54a0-442e-a9de-f18cd21aab1d",
        "urn:uuid:1e9432ec-0bfb-4c05-8a16-c4295d545f81",
        "urn:uuid:ac30440d-7146-4db0-a8d0-8a5bf549b607",
        "urn:uuid:ab19659f-7e70-4f35-87f1-46b59ae80884",
        "urn:uuid:27ab2a4a-15a3-4585-885a-bbac1fe0a5bb",
        "urn:uuid:766c2e20-d125-448b-bc37-642daebaf088",
        "urn:uuid:ebf4115f-fe96-4959-89a4-98c3a6031cff",
        "urn:uuid:b7873da3-fc78-4a2a-92e1-ef83efb6d600",
    }
)

EXPECTED_AXIOM_IDS = frozenset(
    {
        "sha256:2d8f0bb889aed23463bdc12f71eb087cf980f269d7283687d266c012c25c4f52",
        "sha256:9922788e81b846ae627e86d59ed8a00a0ea0c82441995dff3268e55339cbeaba",
        "sha256:5da19db0676db0eb0397d4708cf751f9c90a3a732165b769534e0d9300777cc6",
        "sha256:046c9120e36b99488082b91da7f607659195e4d0af549e456e88766fe7643f9a",
        "sha256:1149dc67a0411aa63c8ac06b3be6ecee8eaf03d62268b48079df3ca3c134dc62",
        "sha256:574e85973353c07195e8e6ae6dc3a813c8baecb2b0a19a268084ff8e404f606c",
        "sha256:1f37a84e9d8ba4775e3ff0dd1f730f21cd573dba406d80512ce84a4edb70c456",
        "sha256:96693821f15cd413fae70f98804b76a37e4b549eb952782af48daab19adc0c43",
        "sha256:5c980e110913e59c68de989465bb1ecc8b07e55d4ef9801e8e46783cb89cf1b1",
        "sha256:d26c043966cd9ac909de23299f25178e558bdf2b31d0c4cdceef63feca9f1367",
        "sha256:41080a7afb8263845cbd910a2a4c6d5bfec9b2b21126a5acd1c037b7e404b797",
        "sha256:6e391f29bd41a8d9690da48c2132f58a553fc72e2df3f7f2f4c116b0d574f189",
        "sha256:ebc7ad7b88f4da2f7a42cc794943cbdbc4a2420c9a58378764be6964603cf30b",
        "sha256:c8842712d9b51ad420a00450debb0f4fa62a2487b085a0ee6e722b1787bb676b",
        "sha256:d695dd55dbcac9a40574027e8ef1396186bccd79631492fba6403bd67e16f44c",
        "sha256:157aece9de6259bc9ad10c9023b8e620c03f9f88bc688cceb058f1e68c7d39b2",
        "sha256:dca940a9ecdfa31a693dffaa7b880ac797fb94b80580f7dc3b292f1220960009",
        "sha256:c039b2a88fe82d34a443e1753f23414ba037f6b6b5d20093323ed6efdce90540",
        "sha256:e780a611c30f9c3cf0e4dbe0bb60f281891360af5bb0c7c443caf882dd5fc33f",
        "sha256:0a66d02476e30d96f3c00a905a1cce9a4e5ff745c4a3745a238efc8291a4f691",
        "sha256:332f337d02fa3315c8d21c1ff70a9a182696adf032799e50a6f2bd623ecda746",
        "sha256:7bed0226c2da616898792bcdfc1f0ca3319d07f1934781cfec1282ebe747fe80",
        "sha256:a1b8c592a4cf6791fb11952b7c19ff54de44725f94537d874e93b3ea320232ab",
        "sha256:733a2295af690d2d2b86dfcd47dfd33214e84ed16606930d2b4246bfeab98d8b",
        "sha256:0db509d9fc575ddc50b0183e97de46b32b5ba4383954670e5ea59d60474aeb59",
        "sha256:f9e3e9bae942c365fd53f52ede02164deff53aa65f5d20a1efa91cd54df7724f",
        "sha256:390c9b5de75302a30d93d73ac3f3706f09cf39aa164a11314f85cb40fb518a56",
        "sha256:f67fc6019bda0c4d47e8eb2a71f56bc92fc3d5eb49c9e2b4a82b38615046ae91",
        "sha256:09ba32215644cf2d55cfe5855539839e3bd68f014c110cd1f562426ee660134b",
    }
)


class ModularProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows, stats = coms.read_workbook(REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx")
        cls.processed = coms.validate_and_process_rows(rows, coms.Resolver(), stats)
        cls.canonical_rows = tuple(coms.canonical_input_for_processed_row(row) for row in cls.processed)
        cls.audits = tuple(row.identity_audit for row in cls.processed)
        cls.disposition = load_disposition_document(
            REPO_ROOT / "reports/coms-product-dispositions.json"
        )
        cls.metadata = load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        cls.selected = modular.select_product_axioms(
            "alignment_core",
            cls.canonical_rows,
            cls.audits,
            cls.disposition,
        )
        cls.result = modular.build_alignment_core(cls.selected, cls.metadata)
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

    def validate_bytes(self, data: bytes, *, integrated: Graph | None = None) -> set[str]:
        return {
            value.code
            for value in modular.validate_alignment_core(
                data,
                self.selected,
                self.metadata,
                integrated_graph=integrated,
            )
        }

    def test_exact_selection_identity_lock_and_distribution(self) -> None:
        self.assertEqual({value.row_id for value in self.selected}, EXPECTED_ROW_IDS)
        self.assertEqual({value.axiom_id for value in self.selected}, EXPECTED_AXIOM_IDS)
        self.assertEqual(sum(value.canonical_input.mapping_type == "domain" for value in self.selected), 15)
        self.assertEqual(sum(value.canonical_input.mapping_type == "range" for value in self.selected), 14)
        self.assertTrue(all(value.target_category == "target_neutral" for value in self.selected))

    def test_wrong_disposition_and_wrong_category_fail(self) -> None:
        row = next(row for row in self.disposition.rows if row.row_id in EXPECTED_ROW_IDS)
        axiom = row.authoritative_axioms[0]
        dispositions = tuple(
            (name, ProductDisposition("not_applicable", "TARGET_SPECIFIC"))
            if name == "alignment_core"
            else (name, value)
            for name, value in axiom.product_dispositions
        )
        for changed_axiom in (
            dataclasses.replace(axiom, product_dispositions=dispositions),
            dataclasses.replace(axiom, target_category="bfo_bearing"),
        ):
            changed = dataclasses.replace(row, authoritative_axioms=(changed_axiom,))
            with self.subTest(changed=changed_axiom):
                with self.assertRaises(modular.ModularProductError) as raised:
                    modular.select_product_axioms(
                        "alignment_core",
                        self.canonical_rows,
                        self.audits,
                        self.replace_disposition_row(row.row_id, changed),
                    )
                self.assertTrue(
                    self.codes(raised.exception)
                    & {"WRONG_PRODUCT_DISPOSITION", "TARGET_CATEGORY_MISMATCH"}
                )

    def test_missing_extra_and_equal_count_rowid_substitution_fail(self) -> None:
        missing = self.canonical_rows[1:]
        replacement = dataclasses.replace(
            self.canonical_rows[0],
            row_id="urn:uuid:ffffffff-ffff-4fff-8fff-ffffffffffff",
        )
        substituted = (replacement, *self.canonical_rows[1:])
        for rows in (missing, (*self.canonical_rows, replacement), substituted):
            with self.subTest(count=len(rows)):
                with self.assertRaises(modular.ModularProductError) as raised:
                    modular.select_product_axioms(
                        "alignment_core", rows, self.audits, self.disposition
                    )
                self.assertTrue(
                    self.codes(raised.exception)
                    & {"MISSING_DISPOSITION_ROW", "UNEXPECTED_CANONICAL_AUDIT", "MISSING_CANONICAL_AUDIT"}
                )

    def test_location_hash_and_canonical_expression_mismatches_fail(self) -> None:
        row = self.canonical_rows[0]
        audit = self.audits[0]
        changed_rows = (
            dataclasses.replace(row, location=RowLocation("Elsewhere", row.location.row_number)),
        )
        changed_audits = (
            dataclasses.replace(audit, source_expression_sha256="0" * 64),
            dataclasses.replace(
                audit,
                expression=dataclasses.replace(audit.expression, target="<http://example.org/Changed>"),
            ),
        )
        for changed in changed_rows:
            with self.assertRaises(modular.ModularProductError) as raised:
                modular.select_product_axioms(
                    "alignment_core",
                    (changed, *self.canonical_rows[1:]),
                    self.audits,
                    self.disposition,
                )
            self.assertIn("ROW_LOCATION_MISMATCH", self.codes(raised.exception))
        for changed in changed_audits:
            with self.assertRaises(modular.ModularProductError) as raised:
                modular.select_product_axioms(
                    "alignment_core",
                    self.canonical_rows,
                    (changed, *self.audits[1:]),
                    self.disposition,
                )
            self.assertTrue(
                self.codes(raised.exception)
                & {"EXPRESSION_HASH_MISMATCH", "CANONICAL_EXPRESSION_MISMATCH"}
            )

    def test_missing_extra_and_equal_count_axiom_substitution_fail(self) -> None:
        row = next(row for row in self.disposition.rows if row.row_id in EXPECTED_ROW_IDS)
        axiom = row.authoritative_axioms[0]
        missing = dataclasses.replace(row, authoritative_axioms=())
        substituted = dataclasses.replace(
            row,
            authoritative_axioms=(dataclasses.replace(axiom, axiom_id="sha256:" + "0" * 64),),
        )
        extra = dataclasses.replace(row, authoritative_axioms=(axiom, axiom))
        for changed in (missing, substituted, extra):
            with self.subTest(changed=changed):
                with self.assertRaises(modular.ModularProductError) as raised:
                    modular.select_product_axioms(
                        "alignment_core",
                        self.canonical_rows,
                        self.audits,
                        self.replace_disposition_row(row.row_id, changed),
                    )
                self.assertTrue(
                    self.codes(raised.exception)
                    & {"AUTHORITATIVE_AXIOM_RECONCILIATION", "DUPLICATE_AUTHORITATIVE_AXIOM"}
                )

    def test_duplicate_selected_axiom_and_wrong_product_count_fail(self) -> None:
        with self.assertRaises(modular.ModularProductError) as raised:
            modular.build_alignment_core((*self.selected, self.selected[0]), self.metadata)
        self.assertIn("DUPLICATE_AUTHORITATIVE_AXIOM", self.codes(raised.exception))
        with self.assertRaises(modular.ModularProductError) as raised:
            modular.build_alignment_core(self.selected[:-1], self.metadata)
        self.assertIn("PRODUCT_AXIOM_COUNT_MISMATCH", self.codes(raised.exception))

    def test_graph_identity_import_counts_and_strict_parse(self) -> None:
        graph = Graph().parse(data=self.result.serialized_bytes.decode(), format="turtle")
        ontology = URIRef(
            "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core"
        )
        self.assertEqual(set(graph.subjects(RDF.type, OWL.Ontology)), {ontology})
        self.assertEqual(list(graph.triples((None, OWL.imports, None))), [])
        self.assertEqual(self.result.governed_axiom_count, 29)
        self.assertEqual(self.result.logical_triple_count, 53)
        self.assertEqual(self.result.ontology_declaration_triple_count, 1)
        self.assertEqual(self.result.import_triple_count, 0)
        self.assertEqual(self.result.metadata_annotation_count, 7)
        self.assertEqual(len(graph), 61)
        self.assertEqual(
            set(ontology_metadata_rdf_triples(self.metadata, "alignment_core")),
            set(graph.triples((ontology, None, None)))
            - {(ontology, RDF.type, OWL.Ontology)},
        )
        self.assertEqual(
            validate_emitted_ontology_metadata(
                graph, self.metadata, "alignment_core", ()
            ),
            (),
        )
        logical = strip_emitted_ontology_header(
            graph, self.metadata, "alignment_core", ()
        )
        self.assertEqual(len(logical), 53)
        self.assertEqual(len(list(graph.triples((None, RDFS.domain, None)))), 15)
        self.assertEqual(len(list(graph.triples((None, RDFS.range, None)))), 14)

    def test_three_union_expressions_have_distinct_three_member_lists(self) -> None:
        graph = Graph().parse(data=self.result.serialized_bytes.decode(), format="turtle")
        roots = list(graph.subjects(OWL.unionOf, None))
        self.assertEqual(len(roots), 3)
        closures = []
        for root in roots:
            head = next(graph.objects(root, OWL.unionOf))
            self.assertEqual(len(list(Collection(graph, head))), 3)
            closures.append(modular._reachable_bnodes(graph, root))
        for index, first in enumerate(closures):
            for second in closures[index + 1:]:
                self.assertFalse(first & second)

    def test_vocabulary_leakage_is_rejected(self) -> None:
        original = b"http://www.w3.org/ns/sosa/FeatureOfInterest"
        replacements = (
            b"http://purl.obolibrary.org/obo/BFO_0000001",
            b"https://www.commoncoreontologies.org/Artifact",
            b"http://purl.obolibrary.org/obo/RO_0000052",
            b"http://example.org/Unexpected",
        )
        for replacement in replacements:
            with self.subTest(replacement=replacement):
                codes = self.validate_bytes(
                    self.result.serialized_bytes.replace(original, replacement, 1)
                )
                self.assertTrue(
                    codes & {"PROHIBITED_LOGICAL_VOCABULARY", "UNEXPECTED_LOGICAL_VOCABULARY"}
                )

    def test_import_declaration_and_annotation_pseudo_mapping_are_rejected(self) -> None:
        graph = Graph().parse(data=self.result.serialized_bytes.decode(), format="turtle")
        ontology = URIRef(self.result.metadata.stable_ontology_iri)
        graph.add((ontology, OWL.imports, URIRef("http://example.org/import")))
        graph.add((BNode("annotation"), RDF.type, OWL.Axiom))
        data = graph.serialize(format="turtle").encode()
        codes = self.validate_bytes(data)
        self.assertIn("PROHIBITED_IMPORT", codes)
        self.assertIn("ANNOTATION_ONLY_PSEUDO_MAPPING", codes)

    def test_copied_named_source_declaration_is_rejected(self) -> None:
        graph = Graph().parse(data=self.result.serialized_bytes.decode(), format="turtle")
        graph.add((URIRef("http://www.w3.org/ns/sosa/Sensor"), RDF.type, OWL.Class))
        self.assertIn(
            "COPIED_SOURCE_DECLARATION",
            self.validate_bytes(graph.serialize(format="turtle").encode()),
        )

    def test_wrong_or_multiple_ontology_declarations_are_rejected(self) -> None:
        graph = Graph().parse(data=self.result.serialized_bytes.decode(), format="turtle")
        ontology = URIRef(self.result.metadata.stable_ontology_iri)
        graph.remove((ontology, RDF.type, OWL.Ontology))
        graph.add((URIRef("http://example.org/Wrong"), RDF.type, OWL.Ontology))
        self.assertIn(
            "ONTOLOGY_DECLARATION_MISMATCH",
            self.validate_bytes(graph.serialize(format="turtle").encode()),
        )
        graph.add((ontology, RDF.type, OWL.Ontology))
        self.assertIn(
            "ONTOLOGY_DECLARATION_MISMATCH",
            self.validate_bytes(graph.serialize(format="turtle").encode()),
        )

    def test_deterministic_serialization_ignores_selected_input_order(self) -> None:
        reverse = modular.build_alignment_core(tuple(reversed(self.selected)), self.metadata)
        self.assertEqual(reverse.serialized_bytes, self.result.serialized_bytes)
        self.assertEqual(modular.serialize_modular_product(reverse), self.result.serialized_bytes)
        self.assertTrue(self.result.serialized_bytes.endswith(b"\n"))
        self.assertFalse(self.result.serialized_bytes.endswith(b"\n\n"))

    def test_reordered_canonical_header_is_rejected_by_product_validator(self) -> None:
        lines = self.result.serialized_bytes.splitlines()
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
            "from modular_products import select_product_axioms,build_alignment_core; "
            "r,s=g.read_workbook(Path('mappings/SSN2BFO-COMS.xlsx')); "
            "p=g.validate_and_process_rows(r,g.Resolver(),s); "
            "c=[g.canonical_input_for_processed_row(x) for x in p]; "
            "a=[x.identity_audit for x in p]; "
            "d=load_disposition_document('reports/coms-product-dispositions.json'); "
            "m=load_metadata('config/publication-metadata.toml'); "
            "x=build_alignment_core(select_product_axioms('alignment_core',c,a,d),m); "
            "print(hashlib.sha256(x.serialized_bytes).hexdigest())"
        )
        hashes = []
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
            hashes.append(proc.stdout.strip())
        self.assertEqual(hashes, [self.result.sha256, self.result.sha256])

    def test_integrated_root_semantic_reconciliation(self) -> None:
        issues = modular.validate_alignment_core(
            self.result.serialized_bytes,
            self.selected,
            self.metadata,
            integrated_graph=self.root_graph,
        )
        self.assertEqual(issues, ())

        changed_root = Graph()
        for triple in self.root_graph:
            changed_root.add(triple)
        named = next(
            value
            for value in self.selected
            if value.canonical_input.expression is not None
            and value.canonical_input.expression.kind == "named"
        )
        subject = URIRef(named.canonical_input.subject_iri)
        predicate = URIRef(named.canonical_input.predicate_iri)
        changed_root.remove((subject, predicate, None))
        codes = {
            value.code
            for value in modular.validate_alignment_core(
                self.result.serialized_bytes,
                self.selected,
                self.metadata,
                integrated_graph=changed_root,
            )
        }
        self.assertIn("MISSING_INTEGRATED_AXIOM", codes)

    def test_fixed_local_source_closure_is_offline_and_import_free(self) -> None:
        paths = tuple(REPO_ROOT / path for path in coms.SOURCE_IMPORTS)
        self.assertEqual(
            tuple(path.relative_to(REPO_ROOT).as_posix() for path in paths),
            (
                "imports/sosa.ttl",
                "imports/sosa-sampling.ttl",
                "imports/ssn.ttl",
                "imports/ssn-systems.ttl",
            ),
        )
        closure = modular.build_fixed_source_closure(self.result.serialized_bytes, paths)
        self.assertEqual(list(closure.triples((None, OWL.imports, None))), [])
        for triple in coms.CLEANUP_TRIPLES:
            closure.remove(triple)
        self.assertEqual(len(closure), 1212)
        self.assertEqual(
            modular.validate_alignment_core(
                self.result.serialized_bytes,
                self.selected,
                self.metadata,
                fixed_source_closure=closure,
                integrated_graph=self.root_graph,
            ),
            (),
        )

    def test_malformed_turtle_is_rejected(self) -> None:
        issues = modular.validate_alignment_core(
            b"not turtle [",
            self.selected,
            self.metadata,
        )
        self.assertEqual({value.code for value in issues}, {"TURTLE_PARSE"})


if __name__ == "__main__":
    unittest.main()
