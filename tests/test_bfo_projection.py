#!/usr/bin/env python3
"""Focused tests for the maintained import-only BFO projection product."""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

from rdflib import BNode, Graph, RDF, OWL, URIRef


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import generate_mapping_from_coms as coms  # noqa: E402
import modular_products as modular  # noqa: E402
from coms_row_identity import RowLocation  # noqa: E402
from product_dispositions import ProductDisposition, load_disposition_document  # noqa: E402
from publication_metadata import load_metadata  # noqa: E402


EXPECTED_SHA256 = "7914e0afb6212df20e02686e1b11b71d109e0b81095ddf33ff120b01768cc71c"
PROJECTION_IRI = URIRef(
    "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-projection"
)
STRICT_IRI = URIRef("http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping")


class BfoProjectionTests(unittest.TestCase):
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
        cls.reconciliation = modular.reconcile_product_axioms(
            modular.BFO_PROJECTION_KEY,
            cls.canonical_rows,
            cls.audits,
            cls.disposition,
        )
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
        cls.strict_bytes = (
            REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl"
        ).read_bytes()
        cls.core_bytes = (
            REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl"
        ).read_bytes()
        cls.root_graph = Graph().parse(REPO_ROOT / "SSN2BFO.ttl", format="turtle")
        cls.reasoning = modular.ModularReasoningResult(
            source_product_key="strict_bfo_mapping",
            source_product_sha256=hashlib.sha256(cls.strict_bytes).hexdigest(),
            closure_triple_count=14972,
            return_code=0,
            reasoned_output_produced=True,
            owl_nothing_count=0,
            named_unsatisfiable_count=0,
        )
        cls.result = modular.build_bfo_projection(
            cls.reconciliation.selected_axioms,
            cls.metadata,
        )

    @staticmethod
    def error_codes(error: modular.ModularProductError) -> set[str]:
        return {value.code for value in error.issues}

    @staticmethod
    def issue_codes(issues) -> set[str]:
        return {value.code for value in issues}

    def replace_disposition_row(self, replacement):
        return dataclasses.replace(
            self.disposition,
            rows=tuple(
                replacement if row.row_id == replacement.row_id else row
                for row in self.disposition.rows
            ),
        )

    def validate(self, data: bytes, *, reconciliation=None, reasoning=None):
        return modular.validate_bfo_projection(
            data,
            reconciliation or self.reconciliation,
            self.strict_bytes,
            self.strict_selected,
            self.core_bytes,
            self.core_selected,
            self.metadata,
            integrated_graph=self.root_graph,
            strict_reasoning_result=self.reasoning if reasoning is None else reasoning,
        )

    def test_exact_disposition_reconciliation_selects_no_direct_axioms(self) -> None:
        self.assertEqual(self.reconciliation.product_key, "bfo_projection")
        self.assertEqual(self.reconciliation.governed_axiom_count, 105)
        self.assertEqual(self.reconciliation.selected_axioms, ())
        self.assertEqual(
            tuple(
                (value.target_category, value.status, value.reason_code, value.count)
                for value in self.reconciliation.disposition_totals
            ),
            (
                ("target_neutral", "provided_transitively", None, 29),
                ("bfo_bearing", "provided_through_import", None, 19),
                ("cco_bearing", "deferred", "NO_APPROVED_TRANSFORMATION_RULE", 25),
                ("mixed_bfo_cco", "deferred", "NO_APPROVED_TRANSFORMATION_RULE", 32),
            ),
        )

    def test_reordered_processed_rows_and_audits_are_stable(self) -> None:
        reordered = modular.reconcile_product_axioms(
            "bfo_projection",
            reversed(self.canonical_rows),
            reversed(self.audits),
            self.disposition,
        )
        reordered_result = modular.build_bfo_projection(
            reordered.selected_axioms,
            self.metadata,
        )
        self.assertEqual(reordered, self.reconciliation)
        self.assertEqual(reordered_result.serialized_bytes, self.result.serialized_bytes)

    def test_identity_reconciliation_rejects_row_and_axiom_substitutions(self) -> None:
        replacement = dataclasses.replace(
            self.canonical_rows[0],
            row_id="urn:uuid:ffffffff-ffff-4fff-8fff-ffffffffffff",
        )
        row_cases = (
            self.canonical_rows[1:],
            (*self.canonical_rows, self.canonical_rows[0]),
            (replacement, *self.canonical_rows[1:]),
        )
        for values in row_cases:
            with self.subTest(row_count=len(values)):
                with self.assertRaises(modular.ModularProductError):
                    modular.reconcile_product_axioms(
                        "bfo_projection", values, self.audits, self.disposition
                    )

        source = self.disposition.rows[0]
        source_axiom = source.authoritative_axioms[0]
        axiom_cases = (
            dataclasses.replace(source, authoritative_axioms=()),
            dataclasses.replace(
                source,
                authoritative_axioms=(
                    dataclasses.replace(
                        source_axiom,
                        axiom_id="sha256:" + "0" * 64,
                    ),
                ),
            ),
            dataclasses.replace(
                source,
                authoritative_axioms=(source_axiom, source_axiom),
            ),
        )
        for replacement_row in axiom_cases:
            with self.subTest(axiom_count=len(replacement_row.authoritative_axioms)):
                with self.assertRaises(modular.ModularProductError):
                    modular.reconcile_product_axioms(
                        "bfo_projection",
                        self.canonical_rows,
                        self.audits,
                        self.replace_disposition_row(replacement_row),
                    )

    def test_location_hash_row_and_axiom_mismatches_are_fatal(self) -> None:
        row = self.canonical_rows[0]
        moved = dataclasses.replace(
            row,
            location=RowLocation("Other", row.location.row_number),
        )
        audit_cases = (
            (moved, self.audits[0]),
            (
                row,
                dataclasses.replace(
                    self.audits[0], source_expression_sha256="0" * 64
                ),
            ),
            (
                row,
                dataclasses.replace(
                    self.audits[0],
                    expression=dataclasses.replace(
                        self.audits[0].expression,
                        target=(self.audits[0].expression.target or "") + " changed",
                    ),
                ),
            ),
        )
        for changed_row, changed_audit in audit_cases:
            with self.subTest(location=changed_row.location.text):
                with self.assertRaises(modular.ModularProductError):
                    modular.reconcile_product_axioms(
                        "bfo_projection",
                        (changed_row, *self.canonical_rows[1:]),
                        (changed_audit, *self.audits[1:]),
                        self.disposition,
                    )

        disposition_row = self.disposition.rows[0]
        axiom = disposition_row.authoritative_axioms[0]
        changed = dataclasses.replace(
            disposition_row,
            authoritative_axioms=(
                dataclasses.replace(
                    axiom,
                    canonical_expression=axiom.canonical_expression + " changed",
                ),
            ),
        )
        with self.assertRaises(modular.ModularProductError) as raised:
            modular.reconcile_product_axioms(
                "bfo_projection",
                self.canonical_rows,
                self.audits,
                self.replace_disposition_row(changed),
            )
        self.assertIn("CANONICAL_EXPRESSION_MISMATCH", self.error_codes(raised.exception))

    def test_wrong_status_reason_or_category_is_fatal(self) -> None:
        cases = []
        for row in self.disposition.rows[:3]:
            axiom = row.authoritative_axioms[0]
            changed_dispositions = tuple(
                (key, ProductDisposition("emitted_unchanged"))
                if key == "bfo_projection"
                else (key, value)
                for key, value in axiom.product_dispositions
            )
            cases.append(
                dataclasses.replace(
                    row,
                    authoritative_axioms=(
                        dataclasses.replace(
                            axiom,
                            product_dispositions=changed_dispositions,
                        ),
                    ),
                )
            )
        deferred_row = next(
            row
            for row in self.disposition.rows
            if dict(row.authoritative_axioms[0].product_dispositions)[
                "bfo_projection"
            ].status
            == "deferred"
        )
        deferred_axiom = deferred_row.authoritative_axioms[0]
        changed_reason = tuple(
            (key, ProductDisposition("deferred", "TARGET_SPECIFIC"))
            if key == "bfo_projection"
            else (key, value)
            for key, value in deferred_axiom.product_dispositions
        )
        cases.append(
            dataclasses.replace(
                deferred_row,
                authoritative_axioms=(
                    dataclasses.replace(
                        deferred_axiom,
                        product_dispositions=changed_reason,
                    ),
                ),
            )
        )
        cases.append(
            dataclasses.replace(
                deferred_row,
                authoritative_axioms=(
                    dataclasses.replace(
                        deferred_axiom,
                        target_category="target_neutral",
                    ),
                ),
            )
        )
        for changed in cases:
            with self.subTest(row_id=changed.row_id):
                with self.assertRaises(modular.ModularProductError) as raised:
                    modular.reconcile_product_axioms(
                        "bfo_projection",
                        self.canonical_rows,
                        self.audits,
                        self.replace_disposition_row(changed),
                    )
                self.assertTrue(
                    self.error_codes(raised.exception)
                    & {"WRONG_PRODUCT_DISPOSITION", "TARGET_CATEGORY_MISMATCH"}
                )

    def test_builder_rejects_any_direct_axiom(self) -> None:
        with self.assertRaises(modular.ModularProductError) as raised:
            modular.build_bfo_projection((self.strict_selected[0],), self.metadata)
        self.assertEqual(self.error_codes(raised.exception), {"UNAPPROVED_PROJECTION_AXIOM"})

    def test_direct_graph_has_only_the_governed_header_and_import(self) -> None:
        graph = Graph().parse(
            data=self.result.serialized_bytes.decode("utf-8"), format="turtle"
        )
        self.assertEqual(len(graph), 2)
        self.assertEqual(self.result.governed_axiom_count, 0)
        self.assertEqual(self.result.logical_triple_count, 0)
        self.assertEqual(self.result.import_triple_count, 1)
        self.assertEqual(
            set(graph),
            {
                (PROJECTION_IRI, RDF.type, OWL.Ontology),
                (PROJECTION_IRI, OWL.imports, STRICT_IRI),
            },
        )
        self.assertFalse(any(isinstance(value, BNode) for value in graph.all_nodes()))
        text = self.result.serialized_bytes.decode("utf-8")
        for prohibited in (
            "http://www.w3.org/ns/sosa/",
            "http://www.w3.org/ns/ssn/",
            "http://purl.obolibrary.org/obo/BFO_",
            "https://www.commoncoreontologies.org/",
            "http://purl.obolibrary.org/obo/RO_",
            "owl:Axiom",
            "rdf:first",
            "rdf:rest",
        ):
            self.assertNotIn(prohibited, text)
        self.assertEqual(self.validate(self.result.serialized_bytes), ())

    def test_wrong_import_and_unexpected_direct_content_are_rejected(self) -> None:
        text = self.result.serialized_bytes.decode("utf-8")
        cases = (
            text.replace(
                str(STRICT_IRI),
                "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core",
            ).encode("utf-8"),
            (
                text
                + "<http://www.w3.org/ns/sosa/Observation> "
                "<http://www.w3.org/2000/01/rdf-schema#subClassOf> "
                "<http://purl.obolibrary.org/obo/BFO_0000001> .\n"
            ).encode("utf-8"),
            (
                text
                + "<http://www.w3.org/ns/sosa/Observation> "
                "<http://www.w3.org/2000/01/rdf-schema#subClassOf> "
                "<https://www.commoncoreontologies.org/Artifact> .\n"
            ).encode("utf-8"),
            (
                text
                + "<http://www.w3.org/ns/sosa/Observation> "
                "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
                "<http://www.w3.org/2002/07/owl#Class> .\n"
            ).encode("utf-8"),
        )
        for data in cases:
            with self.subTest(size=len(data)):
                codes = self.issue_codes(self.validate(data))
                self.assertTrue(
                    codes
                    & {
                        "IMPORT_POLICY_MISMATCH",
                        "UNAPPROVED_PROJECTION_AXIOM",
                        "COPIED_DECLARATION",
                        "UNEXPECTED_LOGICAL_VOCABULARY",
                    }
                )

    def test_project_closure_is_exact_strict_core_set_and_has_no_cco(self) -> None:
        strict_graph = Graph().parse(data=self.strict_bytes.decode(), format="turtle")
        core_graph = Graph().parse(data=self.core_bytes.decode(), format="turtle")
        project = Graph()
        for source in (
            Graph().parse(data=self.result.serialized_bytes.decode(), format="turtle"),
            strict_graph,
            core_graph,
        ):
            for triple in source:
                project.add(triple)
        self.assertEqual(len(self.strict_selected), 19)
        self.assertEqual(len(self.core_selected), 29)
        self.assertEqual(
            {value.axiom_id for value in self.strict_selected}
            & {value.axiom_id for value in self.core_selected},
            set(),
        )
        self.assertEqual(len(project), 183)
        self.assertEqual(len(list(project.triples((None, OWL.imports, None)))), 2)
        for triple in list(project.triples((None, OWL.imports, None))):
            project.remove(triple)
        self.assertEqual(len(project), 181)
        self.assertFalse(
            any(
                isinstance(value, URIRef)
                and str(value).startswith("https://www.commoncoreontologies.org/")
                for value in project.all_nodes()
            )
        )
        self.assertEqual(self.validate(self.result.serialized_bytes), ())

    def test_strict_reasoning_reuse_is_required_and_bound_to_strict_bytes(self) -> None:
        self.assertIn(
            "STRICT_REASONING_RESULT_MISSING",
            self.issue_codes(
                modular.validate_bfo_projection(
                    self.result.serialized_bytes,
                    self.reconciliation,
                    self.strict_bytes,
                    self.strict_selected,
                    self.core_bytes,
                    self.core_selected,
                    self.metadata,
                    integrated_graph=self.root_graph,
                    strict_reasoning_result=None,
                )
            ),
        )
        for changed in (
            dataclasses.replace(self.reasoning, source_product_sha256="0" * 64),
            dataclasses.replace(self.reasoning, return_code=1),
            dataclasses.replace(self.reasoning, named_unsatisfiable_count=1),
        ):
            with self.subTest(return_code=changed.return_code):
                self.assertTrue(self.issue_codes(self.validate(self.result.serialized_bytes, reasoning=changed)))

    def test_serialization_is_deterministic_and_fresh_process_stable(self) -> None:
        repeated = modular.build_bfo_projection((), self.metadata).serialized_bytes
        self.assertEqual(repeated, self.result.serialized_bytes)
        self.assertTrue(repeated.endswith(b"\n"))
        self.assertFalse(repeated.endswith(b"\n\n"))
        self.assertEqual(hashlib.sha256(repeated).hexdigest(), EXPECTED_SHA256)
        script = """
import hashlib, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'tools'))
from modular_products import build_bfo_projection
from publication_metadata import load_metadata
data = build_bfo_projection((), load_metadata(root / 'config/publication-metadata.toml')).serialized_bytes
print(hashlib.sha256(data).hexdigest())
"""
        completed = subprocess.run(
            [sys.executable, "-c", script, str(REPO_ROOT)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(completed.stdout.strip(), EXPECTED_SHA256)

    def test_existing_module_bytes_remain_protected(self) -> None:
        self.assertEqual(
            hashlib.sha256(self.core_bytes).hexdigest(),
            "95f71184b90224906b0ba703d0ea60fd2f8b993b3853b803c66b88b91ba0b01c",
        )
        self.assertEqual(
            hashlib.sha256(self.strict_bytes).hexdigest(),
            "15f080145c6803d174a00cf9e13c971925b40485049744dba6e0847093016ea7",
        )
        self.assertEqual(
            hashlib.sha256(
                (
                    REPO_ROOT
                    / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl"
                ).read_bytes()
            ).hexdigest(),
            "fe6986d79ec2f5f67553fbee1364fa98ebd7ba3205196f0368ac246646fcdf7c",
        )


if __name__ == "__main__":
    unittest.main()
