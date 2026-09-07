#!/usr/bin/env python3
"""Formal-release rendering, validation, determinism, and reasoning regressions."""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import locale
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import BNode, Graph, OWL
from rdflib.compare import isomorphic


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import generate_mapping_from_coms as coms  # noqa: E402
import modular_products as modular  # noqa: E402
import publication_metadata as metadata  # noqa: E402
from product_dispositions import load_disposition_document  # noqa: E402
from release_context import parse_formal_release_context  # noqa: E402


SYNTHETIC_CONTEXT = parse_formal_release_context(
    "2099-01-02",
    "2099-01-02",
    "v2099-01-02",
    "0123456789abcdef0123456789abcdef01234567",
)
FORMAL_HASHES = {
    "integrated": "1e933f8bcf80a3479dc5eba88ccc0f3dfefd3b83c248ddfffd8222d2b5a57954",
    "alignment_core": "c40ec6372eeb43d37fb7fc4775535574ac4a4ee1e218fbe6e840e35b0ba20716",
    "strict_bfo_mapping": "68a91fc766a7ce8ace367d63d70b22f30adfdbb88a41cf9a622d2db956a69be9",
    "cco_extension": "b8645db9d6c8cf49f8b223ce0bd37c65bffed9aac8bf6d41f53d37b51a38d300",
}
DEVELOPMENT_HASHES = {
    "integrated": "c31997d7e7b8c5e0bffd3f23a4597ab4be80786978462fefe800c4c7a5dc0c11",
    "alignment_core": "17695ef17379924449153b2c92ffaed6b57d497a1b2d1e854f584614cebec770",
    "strict_bfo_mapping": "676b31620df10db5c26c46bcc44b2dfd5939d606b16e0fa8a910926e8497c3af",
    "cco_extension": "2908f89648d42dc928f7225056216f1cbf3bcdc79de1bcf770b40a017a5e9bf5",
}
PRODUCT_PATHS = {
    "integrated": REPO_ROOT / "SSN2BFO.ttl",
    "alignment_core": REPO_ROOT
    / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    "strict_bfo_mapping": REPO_ROOT
    / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    "cco_extension": REPO_ROOT
    / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
}


def build_formal_products(context=SYNTHETIC_CONTEXT):
    rows, stats = coms.read_workbook(REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx")
    processed = coms.validate_and_process_rows(rows, coms.Resolver(), stats)
    audits = tuple(row.identity_audit for row in processed)
    disposition = load_disposition_document(
        REPO_ROOT / "reports/coms-product-dispositions.json"
    )
    publication = metadata.load_metadata(
        REPO_ROOT / "config/publication-metadata.toml"
    )
    rendered = coms.render_formal_product_set(
        processed,
        audits,
        disposition,
        publication,
        context,
    )
    return processed, audits, disposition, publication, rendered


def artifact_bytes(product_set) -> dict[str, bytes]:
    return {
        "integrated": product_set.integrated.serialized_bytes,
        "alignment_core": product_set.alignment_core.serialized_bytes,
        "strict_bfo_mapping": product_set.strict_bfo_mapping.serialized_bytes,
        "cco_extension": product_set.cco_extension.serialized_bytes,
    }


def render_synthetic_hashes() -> dict[str, str]:
    products = build_formal_products()[-1]
    return {
        key: hashlib.sha256(value).hexdigest()
        for key, value in artifact_bytes(products).items()
    }


class FormalReleaseRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (
            cls.processed,
            cls.audits,
            cls.disposition,
            cls.publication,
            cls.products,
        ) = build_formal_products()
        cls.bytes = artifact_bytes(cls.products)
        cls.reconciliations = {
            value.product_key: value for value in cls.products.reconciliations
        }

    def header_parameters(self, product_key: str):
        imports = metadata.release_project_imports(
            self.publication,
            product_key,
            SYNTHETIC_CONTEXT,
        )
        if product_key == "integrated":
            return (
                imports,
                coms.GENERATED_NOTICE,
                coms.ROOT_PREFIXES,
                coms.ROOT_IMPORT_TURTLE_TERMS,
            )
        prefixes = {
            "alignment_core": modular.PREFIXES,
            "strict_bfo_mapping": modular.STRICT_BFO_PREFIXES,
            "cco_extension": modular.CCO_EXTENSION_PREFIXES,
        }[product_key]
        return imports, modular.GENERATED_NOTICE, prefixes, None

    def serialized_issue_codes(self, product_key: str, value: bytes) -> set[str]:
        imports, notice, prefixes, import_terms = self.header_parameters(product_key)
        return {
            issue.code
            for issue in metadata.validate_serialized_ontology_header(
                value,
                self.publication,
                product_key,
                imports,
                generated_notice=notice,
                prefixes=prefixes,
                import_turtle_terms=import_terms,
                mode="release",
                context=SYNTHETIC_CONTEXT,
            )
        }

    def test_synthetic_complete_artifact_hashes_are_locked(self) -> None:
        observed = {
            key: hashlib.sha256(value).hexdigest()
            for key, value in self.bytes.items()
        }
        self.assertEqual(observed, FORMAL_HASHES)

    def test_exact_direct_graph_partitions(self) -> None:
        expected = {
            "integrated": (1, 4, 7, 3, 1102, 1117, 103),
            "alignment_core": (1, 0, 7, 3, 53, 64, 29),
            "strict_bfo_mapping": (1, 1, 7, 3, 125, 137, 19),
            "cco_extension": (1, 1, 7, 3, 924, 936, 55),
        }
        results = {
            "integrated": self.products.integrated,
            "alignment_core": self.products.alignment_core,
            "strict_bfo_mapping": self.products.strict_bfo_mapping,
            "cco_extension": self.products.cco_extension,
        }
        for key, result in results.items():
            with self.subTest(product=key):
                self.assertEqual(
                    (
                        result.ontology_declaration_triple_count,
                        result.import_triple_count,
                        result.metadata_annotation_count,
                        result.formal_metadata_annotation_count,
                        result.logical_triple_count,
                        result.total_triple_count,
                        result.governed_axiom_count,
                    ),
                    expected[key],
                )
                self.assertEqual(len(Graph().parse(data=self.bytes[key], format="turtle")), expected[key][5])

    def test_formal_metadata_is_exact_and_uses_stable_ontology_subject(self) -> None:
        expected_predicates = (
            str(metadata.RDFS.label),
            metadata.DCTERMS_NAMESPACE + "description",
            metadata.DCTERMS_NAMESPACE + "type",
            self.publication.publication.development_status_property_iri,
            metadata.DCTERMS_NAMESPACE + "license",
            str(metadata.RDFS.seeAlso),
            str(metadata.RDFS.comment),
            str(OWL.versionIRI),
            str(OWL.versionInfo),
            metadata.DCTERMS_NAMESPACE + "issued",
        )
        for product in self.publication.products:
            with self.subTest(product=product.key):
                values = metadata.ontology_metadata_triples(
                    self.publication,
                    product.key,
                    SYNTHETIC_CONTEXT,
                )
                self.assertEqual(len(values), 10)
                self.assertEqual(tuple(value.predicate_iri for value in values), expected_predicates)
                self.assertEqual({value.ontology_iri for value in values}, {product.stable_ontology_iri})
                self.assertEqual(
                    values[3].value,
                    self.publication.publication.formal_release_status_iri,
                )
                self.assertNotEqual(
                    values[3].value,
                    self.publication.publication.development_status_iri,
                )
                self.assertEqual(values[7].object_kind, metadata.IRI_OBJECT)
                self.assertEqual(
                    values[7].value,
                    metadata.release_version_iri(
                        self.publication,
                        product.key,
                        SYNTHETIC_CONTEXT,
                    ),
                )
                self.assertEqual(
                    (values[8].object_kind, values[8].value, values[8].language),
                    (metadata.PLAIN_LITERAL, "2099-01-02", None),
                )
                self.assertEqual(
                    (values[9].object_kind, values[9].value, values[9].datatype_iri),
                    (
                        metadata.TYPED_LITERAL,
                        "2099-01-02",
                        metadata.XSD_NAMESPACE + "date",
                    ),
                )

    def test_formal_headers_have_exact_prefix_and_predicate_order(self) -> None:
        predicates = (
            " a owl:Ontology ;",
            "    rdfs:label ",
            "    dcterms:description ",
            "    dcterms:type ",
            "    adms:status ",
            "    dcterms:license ",
            "    rdfs:seeAlso ",
            "    rdfs:comment ",
            "    owl:versionIRI ",
            "    owl:versionInfo ",
            "    dcterms:issued ",
        )
        for key, value in self.bytes.items():
            with self.subTest(product=key):
                text = value.decode("utf-8")
                positions = [text.index(predicate) for predicate in predicates]
                self.assertEqual(positions, sorted(positions))
                lines = text.splitlines()
                rdfs_index = next(
                    index for index, line in enumerate(lines) if line.startswith("@prefix rdfs:")
                )
                self.assertEqual(
                    lines[rdfs_index + 1],
                    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
                )
                self.assertEqual(sum(line.startswith("@prefix xsd:") for line in lines), 1)
                self.assertTrue(value.endswith(b"\n"))
                self.assertFalse(value.endswith(b"\n\n"))

    def test_version_iris_and_same_release_imports_are_exact(self) -> None:
        expected_versions = {
            "integrated": "http://www.sks.ai/SSN2BFO/releases/2099-01-02/integrated",
            "alignment_core": "http://www.sks.ai/SSN2BFO/releases/2099-01-02/current-ssn-sosa/alignment-core",
            "strict_bfo_mapping": "http://www.sks.ai/SSN2BFO/releases/2099-01-02/current-ssn-sosa/bfo-mapping",
            "cco_extension": "http://www.sks.ai/SSN2BFO/releases/2099-01-02/current-ssn-sosa/cco-extension",
        }
        expected_imports = {
            "integrated": coms.ROOT_ORDERED_IMPORTS,
            "alignment_core": (),
            "strict_bfo_mapping": (expected_versions["alignment_core"],),
            "cco_extension": (expected_versions["strict_bfo_mapping"],),
        }
        for key, expected in expected_versions.items():
            with self.subTest(product=key):
                self.assertEqual(
                    metadata.release_version_iri(
                        self.publication,
                        key,
                        SYNTHETIC_CONTEXT,
                    ),
                    expected,
                )
                self.assertEqual(
                    metadata.release_project_imports(
                        self.publication,
                        key,
                        SYNTHETIC_CONTEXT,
                    ),
                    expected_imports[key],
                )
                graph = Graph().parse(data=self.bytes[key], format="turtle")
                observed = tuple(sorted(str(value) for value in graph.objects(None, OWL.imports)))
                self.assertEqual(observed, tuple(sorted(expected_imports[key])))

    def test_production_validators_accept_all_formal_products(self) -> None:
        root = Graph().parse(data=self.bytes["integrated"], format="turtle")
        core = self.reconciliations["alignment_core"].selected_axioms
        strict = self.reconciliations["strict_bfo_mapping"].selected_axioms
        cco = self.reconciliations["cco_extension"].selected_axioms
        root_imports, notice, prefixes, import_terms = self.header_parameters("integrated")
        self.assertEqual(
            metadata.validate_serialized_ontology_header(
                self.bytes["integrated"],
                self.publication,
                "integrated",
                root_imports,
                generated_notice=notice,
                prefixes=prefixes,
                import_turtle_terms=import_terms,
                mode="release",
                context=SYNTHETIC_CONTEXT,
            ),
            (),
        )
        self.assertEqual(
            modular.validate_alignment_core(
                self.bytes["alignment_core"],
                core,
                self.publication,
                integrated_graph=root,
                context=SYNTHETIC_CONTEXT,
            ),
            (),
        )
        self.assertEqual(
            modular.validate_strict_bfo_mapping(
                self.bytes["strict_bfo_mapping"],
                strict,
                self.bytes["alignment_core"],
                core,
                self.publication,
                integrated_graph=root,
                context=SYNTHETIC_CONTEXT,
            ),
            (),
        )
        self.assertEqual(
            modular.validate_cco_extension(
                self.bytes["cco_extension"],
                cco,
                self.bytes["strict_bfo_mapping"],
                strict,
                self.bytes["alignment_core"],
                core,
                self.publication,
                integrated_graph=root,
                context=SYNTHETIC_CONTEXT,
            ),
            (),
        )

    def test_logical_graphs_are_isomorphic_to_development_products(self) -> None:
        development_imports = {
            "integrated": coms.ROOT_ORDERED_IMPORTS,
            "alignment_core": (),
            "strict_bfo_mapping": (modular.ALIGNMENT_CORE_IMPORT_IRI,),
            "cco_extension": (modular.STRICT_BFO_IMPORT_IRI,),
        }
        for key in PRODUCT_PATHS:
            with self.subTest(product=key):
                development = Graph().parse(PRODUCT_PATHS[key], format="turtle")
                formal = Graph().parse(data=self.bytes[key], format="turtle")
                development_logical = metadata.strip_emitted_ontology_header(
                    development,
                    self.publication,
                    key,
                    development_imports[key],
                )
                formal_logical = metadata.strip_emitted_ontology_header(
                    formal,
                    self.publication,
                    key,
                    metadata.release_project_imports(
                        self.publication,
                        key,
                        SYNTHETIC_CONTEXT,
                    ),
                    SYNTHETIC_CONTEXT,
                )
                self.assertTrue(isomorphic(formal_logical, development_logical))

    def test_row_and_axiom_identity_sets_are_preserved(self) -> None:
        expected_counts = {
            "alignment_core": 29,
            "strict_bfo_mapping": 19,
            "bfo_projection": 0,
            "cco_extension": 55,
        }
        governed_row_ids: set[str] = set()
        governed_axiom_ids: set[str] = set()
        for key, count in expected_counts.items():
            reconciliation = self.reconciliations[key]
            selected = reconciliation.selected_axioms
            self.assertEqual(len(selected), count)
            self.assertEqual(len({value.row_id for value in selected}), count)
            self.assertEqual(len({value.axiom_id for value in selected}), count)
            governed_row_ids.update(value.row_id for value in selected)
            governed_axiom_ids.update(value.axiom_id for value in selected)
        zero_axiom_row_ids = {
            row.row_id
            for row in self.disposition.rows
            if not row.authoritative_axioms
        }
        self.assertEqual(len(zero_axiom_row_ids), 2)
        self.assertEqual(len(governed_row_ids), 103)
        self.assertEqual(len(governed_axiom_ids), 103)
        self.assertFalse(governed_row_ids & zero_axiom_row_ids)
        self.assertEqual(
            governed_row_ids | zero_axiom_row_ids,
            {row.row_id for row in self.disposition.rows},
        )
        self.assertEqual(
            governed_axiom_ids,
            {
                axiom.axiom_id
                for row in self.disposition.rows
                for axiom in row.authoritative_axioms
            },
        )

    def test_formal_project_and_fixed_closure_counts(self) -> None:
        cco_project = Graph()
        for key in ("cco_extension", "strict_bfo_mapping", "alignment_core"):
            cco_project.parse(data=self.bytes[key], format="turtle")
        self.assertEqual(len(cco_project), 1137)
        for triple in list(cco_project.triples((None, OWL.imports, None))):
            cco_project.remove(triple)
        self.assertEqual(len(cco_project), 1135)

        dependency_paths = tuple(REPO_ROOT / path for path in coms.SOURCE_IMPORTS)
        merged_dependencies = (REPO_ROOT / coms.BFO_VALIDATION_DEPENDENCY, *dependency_paths)
        closures = {
            "alignment_core": modular.build_fixed_validation_closure(
                (self.bytes["alignment_core"],),
                dependency_paths,
            ),
            "strict_bfo_mapping": modular.build_fixed_validation_closure(
                (
                    self.bytes["strict_bfo_mapping"],
                    self.bytes["alignment_core"],
                ),
                merged_dependencies,
            ),
            "cco_extension": modular.build_fixed_validation_closure(
                (
                    self.bytes["cco_extension"],
                    self.bytes["strict_bfo_mapping"],
                    self.bytes["alignment_core"],
                ),
                merged_dependencies,
            ),
            "integrated": modular.build_fixed_validation_closure(
                (self.bytes["integrated"],),
                merged_dependencies,
            ),
        }
        self.assertEqual(
            {key: len(value) for key, value in closures.items()},
            {
                "alignment_core": 1217,
                "strict_bfo_mapping": 14994,
                "cco_extension": 15929,
                "integrated": 15907,
            },
        )
        for closure in closures.values():
            self.assertTrue(
                all(
                    triple in closure
                    for triple in coms.SAMPLE_PROPERTY_SOURCE_DECLARATIONS
                )
            )
            self.assertFalse(any(closure.triples((None, OWL.imports, None))))

    def test_bfo_projection_role_is_reconciled_but_not_rendered(self) -> None:
        reconciliation = self.reconciliations[
            "bfo_projection"
        ]

        self.assertEqual(
            reconciliation.product_key,
            "bfo_projection",
        )
        self.assertEqual(
            reconciliation.governed_axiom_count,
            103,
        )
        self.assertEqual(
            reconciliation.selected_axioms,
            (),
        )
        self.assertNotIn(
            "bfo_projection",
            self.bytes,
        )
        self.assertFalse(
            hasattr(
                self.products,
                "bfo_projection",
            )
        )

    def test_repeated_reordered_and_path_independent_rendering_is_identical(self) -> None:
        repeated = coms.render_formal_product_set(
            self.processed,
            self.audits,
            self.disposition,
            self.publication,
            SYNTHETIC_CONTEXT,
        )
        reordered = coms.render_formal_product_set(
            list(reversed(self.processed)),
            tuple(reversed(self.audits)),
            self.disposition,
            self.publication,
            SYNTHETIC_CONTEXT,
        )
        self.assertEqual(artifact_bytes(repeated), self.bytes)
        self.assertEqual(artifact_bytes(reordered), self.bytes)
        self.assertNotIn("output", inspect.signature(coms.render_formal_product_set).parameters)
        previous = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="formal-render-cwd-") as directory:
            os.chdir(directory)
            try:
                alternate_cwd = coms.render_formal_product_set(
                    self.processed,
                    self.audits,
                    self.disposition,
                    self.publication,
                    SYNTHETIC_CONTEXT,
                )
            finally:
                os.chdir(previous)
        self.assertEqual(artifact_bytes(alternate_cwd), self.bytes)

    def test_source_commit_is_validated_but_not_emitted(self) -> None:
        changed_context = dataclasses.replace(
            SYNTHETIC_CONTEXT,
            source_commit="fedcba9876543210fedcba9876543210fedcba98",
        )
        changed = coms.render_formal_product_set(
            self.processed,
            self.audits,
            self.disposition,
            self.publication,
            changed_context,
        )
        self.assertEqual(artifact_bytes(changed), self.bytes)
        for value in self.bytes.values():
            self.assertNotIn(SYNTHETIC_CONTEXT.source_commit.encode("ascii"), value)
            self.assertNotIn(SYNTHETIC_CONTEXT.git_tag.encode("ascii"), value)

    def test_release_identity_change_changes_all_formal_artifacts(self) -> None:
        changed_context = parse_formal_release_context(
            "2099-01-03",
            "2099-01-03",
            "v2099-01-03",
            SYNTHETIC_CONTEXT.source_commit,
        )
        changed = artifact_bytes(
            coms.render_formal_product_set(
                self.processed,
                self.audits,
                self.disposition,
                self.publication,
                changed_context,
            )
        )
        for key in self.bytes:
            with self.subTest(product=key):
                self.assertNotEqual(changed[key], self.bytes[key])
                self.assertIn(b'owl:versionInfo "2099-01-03"', changed[key])
                self.assertIn(b'dcterms:issued "2099-01-03"^^xsd:date', changed[key])

    def test_formal_metadata_semantic_mutations_are_rejected(self) -> None:
        original = self.bytes["cco_extension"]
        text = original.decode("utf-8")
        formal_status = self.publication.publication.formal_release_status_iri
        development_status = self.publication.publication.development_status_iri
        version_iri = metadata.release_version_iri(
            self.publication,
            "cco_extension",
            SYNTHETIC_CONTEXT,
        )
        status_line = f"    adms:status <{formal_status}> ;"
        version_line = f"    owl:versionIRI <{version_iri}> ;"
        version_info_line = '    owl:versionInfo "2099-01-02" ;'
        issued_line = '    dcterms:issued "2099-01-02"^^xsd:date ;'
        mutations = (
            ("development status", text.replace(status_line, f"    adms:status <{development_status}> ;"), "FORMAL_STATUS_MISMATCH"),
            ("both statuses", text.replace(status_line, f"    adms:status <{development_status}> ;\n{status_line}"), "FORMAL_STATUS_MISMATCH"),
            ("missing status", text.replace(status_line + "\n", ""), "FORMAL_STATUS_MISMATCH"),
            ("wrong status", text.replace(status_line, "    adms:status <http://example.org/status> ;"), "FORMAL_STATUS_MISMATCH"),
            ("missing version IRI", text.replace(version_line + "\n", ""), "VERSION_IRI_MISMATCH"),
            ("wrong version IRI", text.replace(version_iri, version_iri + "-wrong"), "VERSION_IRI_MISMATCH"),
            (
                "stable version IRI",
                text.replace(
                    f"<{version_iri}>",
                    "<http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension>",
                ),
                "VERSION_IRI_MISMATCH",
            ),
            ("literal version IRI", text.replace(f"<{version_iri}>", json.dumps(version_iri)), "VERSION_IRI_MISMATCH"),
            (
                "duplicate version IRI",
                text.replace(version_line, version_line + "\n" + version_line),
                "NONCANONICAL_ONTOLOGY_HEADER",
            ),
            ("missing version info", text.replace(version_info_line + "\n", ""), "VERSION_INFO_MISMATCH"),
            (
                "wrong version info",
                text.replace(
                    version_info_line,
                    '    owl:versionInfo "2099-01-03" ;',
                ),
                "VERSION_INFO_MISMATCH",
            ),
            ("language version info", text.replace(version_info_line, '    owl:versionInfo "2099-01-02"@en ;'), "VERSION_INFO_MISMATCH"),
            ("typed version info", text.replace(version_info_line, '    owl:versionInfo "2099-01-02"^^xsd:string ;'), "VERSION_INFO_MISMATCH"),
            ("missing issued", text.replace(issued_line + "\n", ""), "ISSUED_DATE_MISMATCH"),
            ("wrong issued", text.replace(issued_line, '    dcterms:issued "2099-01-03"^^xsd:date ;'), "ISSUED_DATE_MISMATCH"),
            ("untyped issued", text.replace(issued_line, '    dcterms:issued "2099-01-02" ;'), "ISSUED_DATE_MISMATCH"),
            ("wrong issued datatype", text.replace("^^xsd:date", "^^xsd:dateTime"), "ISSUED_DATE_MISMATCH"),
        )
        for label, mutated, expected_code in mutations:
            with self.subTest(case=label):
                codes = self.serialized_issue_codes(
                    "cco_extension",
                    mutated.encode("utf-8"),
                )
                self.assertIn(expected_code, codes)
                self.assertIn("NONCANONICAL_ONTOLOGY_HEADER", codes)

    def test_unapproved_formal_annotations_are_rejected(self) -> None:
        original = self.bytes["cco_extension"].decode("utf-8")
        import_line = "    owl:imports "
        annotations = (
            '    dcterms:creator <https://example.org/creator> ;',
            '    dcterms:contributor <https://example.org/contributor> ;',
            '    <http://www.w3.org/ns/prov#wasDerivedFrom> <https://example.org/source> ;',
            '    dcterms:identifier "v2099-01-02" ;',
            '    dcterms:identifier "0123456789abcdef0123456789abcdef01234567" ;',
            '    dcterms:identifier "sha256:0000" ;',
            '    dcterms:hasPart <https://example.org/manifest> ;',
        )
        for annotation in annotations:
            with self.subTest(annotation=annotation):
                mutated = original.replace(import_line, annotation + "\n" + import_line, 1)
                codes = self.serialized_issue_codes(
                    "cco_extension",
                    mutated.encode("utf-8"),
                )
                self.assertIn("UNAPPROVED_ONTOLOGY_METADATA", codes)
                self.assertIn("NONCANONICAL_ONTOLOGY_HEADER", codes)

    def test_formal_import_mutations_are_rejected(self) -> None:
        strict = self.bytes["strict_bfo_mapping"].decode("utf-8")
        expected = metadata.release_project_imports(
            self.publication,
            "strict_bfo_mapping",
            SYNTHETIC_CONTEXT,
        )[0]
        wrong_imports = (
            modular.ALIGNMENT_CORE_IMPORT_IRI,
            expected.replace("2099-01-02", "2099-01-03"),
            metadata.release_version_iri(
                self.publication,
                "strict_bfo_mapping",
                SYNTHETIC_CONTEXT,
            ),
            "http://example.org/unapproved",
        )
        for wrong in wrong_imports:
            with self.subTest(import_iri=wrong):
                mutated = strict.replace(expected, wrong, 1).encode("utf-8")
                codes = self.serialized_issue_codes("strict_bfo_mapping", mutated)
                self.assertIn("IMPORT_POLICY_MISMATCH", codes)
                self.assertIn("NONCANONICAL_ONTOLOGY_HEADER", codes)

        import_line = f"    owl:imports <{expected}> ."
        duplicate = strict.replace(
            import_line,
            f"    owl:imports <{expected}>,\n        <{expected}> .",
        ).encode("utf-8")
        self.assertIn(
            "NONCANONICAL_ONTOLOGY_HEADER",
            self.serialized_issue_codes("strict_bfo_mapping", duplicate),
        )

        root = self.bytes["integrated"].decode("utf-8")
        first, second = coms.ROOT_IMPORT_TURTLE_TERMS[:2]
        reordered = root.replace(first, "__FIRST__", 1).replace(second, first, 1).replace("__FIRST__", second, 1)
        self.assertIn(
            "NONCANONICAL_ONTOLOGY_HEADER",
            self.serialized_issue_codes("integrated", reordered.encode("utf-8")),
        )
        changed = root.replace(coms.ROOT_ORDERED_IMPORTS[0], "http://example.org/changed", 1)
        self.assertIn(
            "IMPORT_POLICY_MISMATCH",
            self.serialized_issue_codes("integrated", changed.encode("utf-8")),
        )

    def test_noncanonical_formal_serialization_is_rejected(self) -> None:
        original = self.bytes["alignment_core"].decode("utf-8")
        lines = original.splitlines()
        rdfs = next(index for index, line in enumerate(lines) if line.startswith("@prefix rdfs:"))
        xsd = rdfs + 1
        swapped_prefixes = list(lines)
        swapped_prefixes[rdfs], swapped_prefixes[xsd] = swapped_prefixes[xsd], swapped_prefixes[rdfs]
        label = next(index for index, line in enumerate(lines) if line.startswith("    rdfs:label"))
        description = label + 1
        swapped_predicates = list(lines)
        swapped_predicates[label], swapped_predicates[description] = (
            swapped_predicates[description],
            swapped_predicates[label],
        )
        mutations = (
            ("missing xsd prefix", "\n".join(line for line in lines if not line.startswith("@prefix xsd:")) + "\n", "TURTLE_PARSE"),
            ("wrong xsd binding", original.replace(metadata.XSD_NAMESPACE, "http://example.org/xsd#", 1), "ISSUED_DATE_MISMATCH"),
            ("prefix order", "\n".join(swapped_prefixes) + "\n", "NONCANONICAL_ONTOLOGY_HEADER"),
            ("predicate order", "\n".join(swapped_predicates) + "\n", "NONCANONICAL_ONTOLOGY_HEADER"),
            ("wrong escaping", original.replace('"SSN/SOSA Alignment Core"@en', '"SSN/SOSA \\q Core"@en'), "TURTLE_PARSE"),
            ("missing final newline", original.rstrip("\n"), "NONCANONICAL_ONTOLOGY_HEADER"),
            ("extra final newline", original + "\n", "NONCANONICAL_ONTOLOGY_HEADER"),
            ("extra boundary newline", original.replace("^^xsd:date .\n\n", "^^xsd:date .\n\n\n", 1), "NONCANONICAL_ONTOLOGY_HEADER"),
        )
        for label, mutated, expected in mutations:
            with self.subTest(case=label):
                self.assertIn(
                    expected,
                    self.serialized_issue_codes(
                        "alignment_core",
                        mutated.encode("utf-8"),
                    ),
                )

    def test_fresh_process_hash_seed_and_supported_locale_determinism(self) -> None:
        script = (
            "import json; "
            "from test_release_rendering import render_synthetic_hashes; "
            "print(json.dumps(render_synthetic_hashes(), sort_keys=True))"
        )
        available = subprocess.run(
            ["locale", "-a"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.splitlines()
        locales = ["C"]
        utf8_locale = next(
            (
                value
                for value in available
                if "utf" in value.lower() and value != locale.setlocale(locale.LC_ALL, None)
            ),
            None,
        )
        if utf8_locale is not None:
            locales.append(utf8_locale)
        for seed in ("0", "1", "42", "random"):
            for locale_name in locales:
                with self.subTest(seed=seed, locale=locale_name):
                    environment = os.environ.copy()
                    environment["PYTHONHASHSEED"] = seed
                    environment["LC_ALL"] = locale_name
                    environment["PYTHONPATH"] = os.pathsep.join(
                        (str(REPO_ROOT / "tools"), str(REPO_ROOT / "tests"))
                    )
                    completed = subprocess.run(
                        [sys.executable, "-c", script],
                        cwd=REPO_ROOT,
                        env=environment,
                        check=True,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    self.assertEqual(json.loads(completed.stdout), FORMAL_HASHES)

    def test_all_four_formal_products_pass_independent_hermit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="formal-release-hermit-") as directory:
            root = Path(directory)
            paths: dict[str, Path] = {}
            for key, value in self.bytes.items():
                path = root / f"{key}.ttl"
                path.write_bytes(value)
                paths[key] = path
            results = {
                "integrated": coms.run_candidate_hermit(paths["integrated"], root / "root"),
                "alignment_core": coms.run_alignment_core_hermit(
                    paths["alignment_core"], root / "core"
                ),
                "strict_bfo_mapping": coms.run_strict_bfo_hermit(
                    paths["strict_bfo_mapping"],
                    paths["alignment_core"],
                    root / "strict",
                ),
                "cco_extension": coms.run_cco_extension_hermit(
                    paths["cco_extension"],
                    paths["strict_bfo_mapping"],
                    paths["alignment_core"],
                    root / "cco",
                ),
            }
            expected_closures = {
                "integrated": 15907,
                "alignment_core": 1217,
                "strict_bfo_mapping": 14994,
                "cco_extension": 15929,
            }
            for key, result in results.items():
                with self.subTest(product=key):
                    self.assertEqual(result.closure_triple_count, expected_closures[key])
                    self.assertTrue(result.profile_checked)
                    self.assertEqual(
                        result.profile_triple_count,
                        expected_closures[key] + 4,
                    )
                    self.assertEqual(
                        result.profile_declaration_completion_count,
                        4,
                    )
                    self.assertEqual(
                        result.profile_return_code,
                        0,
                        result.profile_output,
                    )
                    self.assertTrue(result.source_sample_declarations_retained)
                    self.assertEqual(result.return_code, 0, result.robot_output)
                    self.assertTrue(result.reasoned_output_produced)
                    self.assertEqual(result.owl_nothing_count, 0)
                    self.assertEqual(result.unsat_classes, [])

    def test_development_artifacts_remain_byte_identical(self) -> None:
        observed = {
            key: hashlib.sha256(path.read_bytes()).hexdigest()
            for key, path in PRODUCT_PATHS.items()
        }
        self.assertEqual(observed, DEVELOPMENT_HASHES)

    def test_rendering_creates_no_release_directory_or_artifact(self) -> None:
        self.assertFalse((REPO_ROOT / "releases/2099-01-02").exists())
        for value in self.bytes.values():
            self.assertNotIn(str(REPO_ROOT).encode("utf-8"), value)
            self.assertNotIn(b"2099-01-02/manifest", value)


if __name__ == "__main__":
    if "--render-hashes" in sys.argv:
        print(json.dumps(render_synthetic_hashes(), sort_keys=True))
    else:
        unittest.main()
