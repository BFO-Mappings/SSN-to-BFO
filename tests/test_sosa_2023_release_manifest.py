#!/usr/bin/env python3
"""SOSA-2023 release-manifest evidence-model regressions."""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sosa_2023_release_manifest as manifest  # noqa: E402


HASH = "a" * 64
SYNTHETIC_DATE = "2099-01-02"
SYNTHETIC_COMMIT = "0123456789abcdef0123456789abcdef01234567"

FORMAL_HASHES = {
    "integrated":
        "e2345d7e50ac871a535bd0f1e7e2c612181729b83d8d8bd7d5cb6d3976299a19",
    "strict_bfo_mapping":
        "c4417989963590517a5636bf1d57ddc966199ab8273fee814b3d27fb159c0c96",
    "cco_extension":
        "49dec6023bfdebac6c78c4f2b6b291ab74766c1816d146598f797dfb9295bc35",
}

CURRENT_AUTHORITY_HASHES = {
    "tools/release_manifest.py":
        "89105d96dac5fb4d79128b85a5becfa3faec6ac9586507286f0c97e18f0259c5",
    "config/release-manifest-schema-v2.json":
        "b0162fb89fe2872f47b13cae9ad1a15aa2b225c6a69b4152a9c894183822191c",
    "tests/test_release_manifest.py":
        "6f25af9a9760ed644bd2b4edf36fb3110f9368eba9337ad1f310fa281499ce51",
    "tools/build_release.py":
        "3969aa59159dc5caf1c3f69b2ccef5ca9c9bd28d317b97dcb332e5a04fa2eb76",
    "tools/check_release.py":
        "3b839dbdb31142eba720a25801eb4f2f28c46a7623e60dd868024d661dfe8d6a",
    "tools/release_archive.py":
        "8928d921ac7b850f5ff52449c12013fa2c394b6d1acaff83972134b81741c974",
    "tools/rehearse_release.py":
        "737f880da62c0b33de00877404469e98b0cc6634340bbd8bab0f128676d3263d",
}


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_record(
    key: str,
    source_path: str,
    package_path: str | None,
) -> manifest.ReleaseManifestInput:
    source = REPO_ROOT / source_path
    content = source.read_bytes()

    return manifest.ReleaseManifestInput(
        key=key,
        source_path=source_path,
        package_path=package_path,
        sha256=sha256(content),
        byte_size=len(content),
    )


def valid_manifest() -> manifest.ReleaseManifest:
    inputs = []

    for key, source_path, package_path in manifest.INPUT_POLICIES:
        if key == "release_notes":
            source_path = "release-notes/SYNTHETIC-2099-01-02.md"

        assert source_path is not None

        inputs.append(
            file_record(
                key,
                source_path,
                package_path,
            )
        )

    products = tuple(
        manifest.ReleaseManifestProduct(
            key=key,
            path=manifest.PRODUCT_PACKAGE_PATHS[key],
            stable_ontology_iri=(
                manifest.PRODUCT_STABLE_ONTOLOGY_IRIS[key]
            ),
            version_iri=manifest.expected_version_iri(
                key,
                SYNTHETIC_DATE,
            ),
            imports=manifest.expected_product_imports(
                key,
                SYNTHETIC_DATE,
            ),
            sha256=FORMAL_HASHES[key],
            **manifest.PRODUCT_STATIC_EVIDENCE[key],
        )
        for key in manifest.PRODUCT_ORDER
    )

    dependencies = tuple(
        manifest.ReleaseManifestDependency(
            key=key,
            role=role,
            path=source_path,
            ontology_iri=ontology_iri,
            version_iri=None,
            sha256=sha256(
                (REPO_ROOT / source_path).read_bytes()
            ),
            byte_size=(
                REPO_ROOT / source_path
            ).stat().st_size,
        )
        for (
            key,
            role,
            source_path,
            ontology_iri,
        ) in manifest.DEPENDENCY_POLICIES
    )

    environment = manifest.ReleaseManifestValidationEnvironment(
        python_implementation="CPython",
        python_version="3.12.4",
        java_vendor="Fixture Java Vendor",
        java_version="22.0.2",
        java_vm_name="Fixture Java VM",
        robot_artifact="https://example.invalid/robot.jar",
        robot_version="1.9.7",
        robot_sha256=HASH,
        toolchain_path="config/validation-toolchain.env",
        toolchain_sha256=HASH,
        requirements_path="requirements/validation.txt",
        requirements_sha256=HASH,
    )

    validation = manifest.ReleaseManifestValidation(
        strict_turtle_parsing=True,
        formal_metadata_validation=True,
        serialized_header_validation=True,
        governed_axiom_reconciliation=True,
        import_graph_validation=True,
        catalog_validation=True,
        checksum_validation=True,
        development_artifact_nonmutation=True,
        deterministic_package_rebuild=True,
        hermit_results=tuple(
            manifest.ReleaseManifestHermitResult(
                product_key=key,
                status="PASS",
                fixed_closure_triple_count=count,
                return_code=0,
                reasoned_output_produced=True,
                named_unsatisfiable_class_count=0,
                owl_nothing_equivalent_named_class_count=0,
            )
            for key, count in (
                manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS
            )
        ),
    )

    included_files = tuple(
        manifest.ReleaseManifestIncludedFile(
            path=value,
            role="governed SOSA-2023 formal package member",
            sha256=HASH,
            byte_size=1,
        )
        for value in manifest.INCLUDED_FILE_PATH_ORDER
    )

    return manifest.build_release_manifest(
        release_identifier=SYNTHETIC_DATE,
        release_date=SYNTHETIC_DATE,
        git_tag="v" + SYNTHETIC_DATE,
        source_commit=SYNTHETIC_COMMIT,
        repository_iri=manifest.REPOSITORY_IRI,
        inputs=tuple(inputs),
        product_order=manifest.PRODUCT_ORDER,
        products=products,
        dependencies=dependencies,
        validation_environment=environment,
        validation=validation,
        included_files=included_files,
    )


class Sosa2023ReleaseManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.value = valid_manifest()
        cls.serialized = manifest.canonical_manifest_bytes(
            cls.value
        )
        cls.document = json.loads(cls.serialized)
        cls.schema = json.loads(
            (
                REPO_ROOT
                / "config/sosa-2023-release-manifest-schema-v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_exact_track_inventory_and_closure_authority(self) -> None:
        self.assertEqual(
            manifest.PRODUCT_ORDER,
            (
                "integrated",
                "strict_bfo_mapping",
                "cco_extension",
            ),
        )
        self.assertEqual(
            manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS,
            (
                ("integrated", 15234),
                ("strict_bfo_mapping", 15117),
                ("cco_extension", 15245),
            ),
        )
        self.assertEqual(
            manifest.PRODUCT_IMPORT_COUNTS,
            {
                "integrated": 4,
                "strict_bfo_mapping": 0,
                "cco_extension": 1,
            },
        )

    def test_schema_and_python_authorities_are_synchronized(self) -> None:
        self.assertEqual(manifest.SCHEMA_VERSION, 1)
        self.assertEqual(
            self.schema["properties"]["schema_version"],
            {"const": 1},
        )
        self.assertEqual(
            tuple(
                self.schema["properties"][
                    "product_order"
                ]["const"]
            ),
            manifest.PRODUCT_ORDER,
        )
        self.assertEqual(
            tuple(
                self.schema["$defs"]["product"][
                    "properties"
                ]["key"]["enum"]
            ),
            manifest.PRODUCT_ORDER,
        )
        self.assertEqual(
            tuple(
                self.schema["$defs"]["hermitResult"][
                    "properties"
                ]["product_key"]["enum"]
            ),
            manifest.PRODUCT_ORDER,
        )

        expected_arrays = (
            (
                "inputs",
                manifest.INPUT_KEY_ORDER,
                "key",
            ),
            (
                "products",
                manifest.PRODUCT_ORDER,
                "key",
            ),
            (
                "dependencies",
                manifest.DEPENDENCY_KEY_ORDER,
                "key",
            ),
            (
                "included_files",
                manifest.INCLUDED_FILE_PATH_ORDER,
                "path",
            ),
        )

        for field, expected, identity_field in expected_arrays:
            value = self.schema["properties"][field]

            with self.subTest(field=field):
                self.assertEqual(
                    (
                        value["minItems"],
                        value["maxItems"],
                    ),
                    (
                        len(expected),
                        len(expected),
                    ),
                )
                self.assertFalse(value["items"])
                self.assertEqual(
                    tuple(
                        item["allOf"][1]["properties"][
                            identity_field
                        ]["const"]
                        for item in value["prefixItems"]
                    ),
                    expected,
                )

        hermit = self.schema["$defs"]["validation"][
            "properties"
        ]["hermit_results"]

        self.assertEqual(
            (
                hermit["minItems"],
                hermit["maxItems"],
            ),
            (3, 3),
        )

        self.assertEqual(
            tuple(
                (
                    item["allOf"][1]["properties"][
                        "product_key"
                    ]["const"],
                    item["allOf"][1]["properties"][
                        "fixed_closure_triple_count"
                    ]["const"],
                )
                for item in hermit["prefixItems"]
            ),
            manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS,
        )

    def test_valid_manifest_round_trips_canonically(self) -> None:
        self.assertEqual(
            manifest.validate_release_manifest_document(
                self.document
            ),
            (),
        )
        loaded = manifest.load_and_validate_release_manifest(
            self.serialized
        )
        self.assertEqual(loaded, self.value)
        self.assertEqual(
            manifest.canonical_manifest_bytes(loaded),
            self.serialized,
        )
        self.assertTrue(
            self.serialized.endswith(b"\n")
        )
        self.assertFalse(
            self.serialized.endswith(b"\n\n")
        )

    def test_reordered_models_have_identical_canonical_bytes(self) -> None:
        reordered = replace(
            self.value,
            inputs=tuple(reversed(self.value.inputs)),
            products=tuple(reversed(self.value.products)),
            dependencies=tuple(
                reversed(self.value.dependencies)
            ),
            validation=replace(
                self.value.validation,
                hermit_results=tuple(
                    reversed(
                        self.value.validation.hermit_results
                    )
                ),
            ),
            included_files=tuple(
                reversed(self.value.included_files)
            ),
        )

        self.assertEqual(
            manifest.canonical_manifest_bytes(reordered),
            self.serialized,
        )

    def test_synthetic_formal_product_evidence_is_exact(self) -> None:
        observed = {
            value.key: value
            for value in self.value.products
        }

        for key in manifest.PRODUCT_ORDER:
            product = observed[key]

            self.assertEqual(
                product.sha256,
                FORMAL_HASHES[key],
            )
            self.assertEqual(
                product.byte_size,
                manifest.PRODUCT_STATIC_EVIDENCE[
                    key
                ]["byte_size"],
            )
            self.assertEqual(
                product.version_iri,
                manifest.expected_version_iri(
                    key,
                    SYNTHETIC_DATE,
                ),
            )
            self.assertEqual(
                product.imports,
                manifest.expected_product_imports(
                    key,
                    SYNTHETIC_DATE,
                ),
            )

            formal_text = "\n".join(
                (
                    product.path,
                    product.stable_ontology_iri,
                    product.version_iri,
                    *product.imports,
                )
            )

            self.assertNotIn(
                "sosa-next",
                formal_text,
            )
            self.assertNotIn(
                "/development/",
                formal_text,
            )

    def test_all_source_and_development_evidence_is_represented(self) -> None:
        records = {
            value.key: value
            for value in self.value.inputs
        }

        self.assertEqual(
            tuple(records),
            manifest.INPUT_KEY_ORDER,
        )

        for key, source_path, package_path in (
            manifest.INPUT_POLICIES
        ):
            record = records[key]

            if key == "release_notes":
                source_path = (
                    "release-notes/"
                    "SYNTHETIC-2099-01-02.md"
                )

            assert source_path is not None

            content = (
                REPO_ROOT / source_path
            ).read_bytes()

            self.assertEqual(
                record.source_path,
                source_path,
            )
            self.assertEqual(
                record.package_path,
                package_path,
            )
            self.assertEqual(
                record.sha256,
                sha256(content),
            )
            self.assertEqual(
                record.byte_size,
                len(content),
            )

        pinned_keys = {
            "pinned_sosa",
            "pinned_sosa_common",
            "pinned_sosa_observation",
            "pinned_sosa_actuation",
            "pinned_sosa_sampling",
            "pinned_sosa_deprecated",
            "pinned_sosa_system",
            "pinned_sample_relations",
            "source_declaration_overlay",
        }

        self.assertTrue(
            pinned_keys <= set(records)
        )

    def test_dependency_ontology_identities_match_pinned_files(self) -> None:
        from rdflib import Graph, OWL, RDF, URIRef

        for (
            key,
            _role,
            source_path,
            expected_ontology_iri,
        ) in manifest.DEPENDENCY_POLICIES:
            with self.subTest(dependency=key):
                graph = Graph().parse(
                    REPO_ROOT / source_path,
                    format="turtle",
                )

                observed = tuple(
                    sorted(
                        str(value)
                        for value in graph.subjects(
                            RDF.type,
                            OWL.Ontology,
                        )
                        if isinstance(value, URIRef)
                    )
                )

                self.assertEqual(
                    observed,
                    (expected_ontology_iri,),
                )


    def test_package_engine_modules_are_governed_inputs(self) -> None:
        records = {
            value.key: value
            for value in self.value.inputs
        }

        expected = (
            (
                "module_sosa_2023_release_runtime",
                "tools/sosa_2023_release_runtime.py",
            ),
            (
                "module_sosa_2023_build_release",
                "tools/sosa_2023_build_release.py",
            ),
            (
                "module_sosa_2023_check_release",
                "tools/sosa_2023_check_release.py",
            ),
        )

        self.assertEqual(
            len(self.value.inputs),
            31,
        )

        for key, source_path in expected:
            with self.subTest(input=key):
                record = records[key]
                content = (
                    REPO_ROOT / source_path
                ).read_bytes()

                self.assertEqual(
                    record.source_path,
                    source_path,
                )
                self.assertIsNone(
                    record.package_path,
                )
                self.assertEqual(
                    record.sha256,
                    sha256(content),
                )
                self.assertEqual(
                    record.byte_size,
                    len(content),
                )

                self.assertNotIn(
                    source_path,
                    manifest.INCLUDED_FILE_PATH_ORDER,
                )


    def test_exact_policy_mutations_are_rejected(self) -> None:
        variants = []

        wrong_input = json.loads(self.serialized)
        wrong_input["inputs"][0]["source_path"] = (
            "mappings/wrong.xlsx"
        )
        variants.append(
            (
                "wrong input",
                wrong_input,
                "INPUT_SOURCE_POLICY",
            )
        )

        wrong_product_path = json.loads(self.serialized)
        wrong_product_path["products"][0]["path"] = (
            "sosa-next/sosa-integrated.ttl"
        )
        variants.append(
            (
                "wrong product path",
                wrong_product_path,
                "PRODUCT_PATH_POLICY",
            )
        )

        wrong_stable = json.loads(self.serialized)
        wrong_stable["products"][0][
            "stable_ontology_iri"
        ] = "http://www.sks.ai/SSN2BFO/development/sosa-next/integrated"
        variants.append(
            (
                "wrong stable IRI",
                wrong_stable,
                "PRODUCT_STABLE_IRI_POLICY",
            )
        )

        wrong_version = json.loads(self.serialized)
        wrong_version["products"][1]["version_iri"] = (
            "http://www.sks.ai/SSN2BFO/releases/"
            "2099-01-02/wrong"
        )
        variants.append(
            (
                "wrong version IRI",
                wrong_version,
                "PRODUCT_VERSION_IRI_POLICY",
            )
        )

        wrong_import = json.loads(self.serialized)
        wrong_import["products"][2]["imports"] = []
        wrong_import["products"][2]["import_count"] = 0
        variants.append(
            (
                "wrong import",
                wrong_import,
                "PRODUCT_IMPORT_POLICY",
            )
        )

        wrong_count = json.loads(self.serialized)
        wrong_count["products"][0][
            "logical_triple_count"
        ] = 274
        variants.append(
            (
                "wrong evidence",
                wrong_count,
                "PRODUCT_EVIDENCE_POLICY",
            )
        )

        wrong_dependency = json.loads(self.serialized)
        wrong_dependency["dependencies"][0]["path"] = (
            "imports/wrong.ttl"
        )
        variants.append(
            (
                "wrong dependency",
                wrong_dependency,
                "DEPENDENCY_POLICY",
            )
        )

        wrong_included = json.loads(self.serialized)
        wrong_included["included_files"][2]["path"] = (
            "sosa-next/catalog-v001.xml"
        )
        variants.append(
            (
                "development package path",
                wrong_included,
                "DEVELOPMENT_IDENTITY_LEAK",
            )
        )

        for label, document, expected_code in variants:
            with self.subTest(label=label):
                codes = {
                    value.code
                    for value in (
                        manifest
                        .validate_release_manifest_document(
                            document
                        )
                    )
                }
                self.assertIn(
                    expected_code,
                    codes,
                )

    def test_reasoning_evidence_is_product_specific_and_fixed(self) -> None:
        observed = tuple(
            (
                value.product_key,
                value.fixed_closure_triple_count,
                value.return_code,
                value.reasoned_output_produced,
                value.named_unsatisfiable_class_count,
            )
            for value in self.value.validation.hermit_results
        )

        self.assertEqual(
            observed,
            (
                (
                    "integrated",
                    15234,
                    0,
                    True,
                    0,
                ),
                (
                    "strict_bfo_mapping",
                    15117,
                    0,
                    True,
                    0,
                ),
                (
                    "cco_extension",
                    15245,
                    0,
                    True,
                    0,
                ),
            ),
        )

        changed = json.loads(self.serialized)
        changed["validation"]["hermit_results"][2][
            "fixed_closure_triple_count"
        ] = 15140

        codes = {
            value.code
            for value in (
                manifest.validate_release_manifest_document(
                    changed
                )
            )
        }

        self.assertIn(
            "FIXED_CLOSURE_TRIPLE_COUNT_MISMATCH",
            codes,
        )

    def test_included_files_are_formal_only_and_anti_circular(self) -> None:
        self.assertEqual(
            tuple(sorted(manifest.INCLUDED_FILE_PATH_ORDER)),
            manifest.INCLUDED_FILE_PATH_ORDER,
        )

        self.assertNotIn(
            "manifest.json",
            manifest.INCLUDED_FILE_PATH_ORDER,
        )
        self.assertNotIn(
            "SHA256SUMS",
            manifest.INCLUDED_FILE_PATH_ORDER,
        )

        for value in manifest.INCLUDED_FILE_PATH_ORDER:
            self.assertNotIn(
                "sosa-next",
                value,
            )

    def test_current_release_authorities_remain_byte_locked(self) -> None:
        for relative, expected in CURRENT_AUTHORITY_HASHES.items():
            with self.subTest(relative=relative):
                observed = sha256(
                    (REPO_ROOT / relative).read_bytes()
                )
                self.assertEqual(
                    observed,
                    expected,
                )

    def test_module_has_no_external_json_schema_dependency(self) -> None:
        source = (
            REPO_ROOT
            / "tools/sosa_2023_release_manifest.py"
        ).read_text(encoding="utf-8")

        package_name = "json" + "schema"

        self.assertNotIn(
            f"import {package_name}",
            source,
        )
        self.assertNotIn(
            f"from {package_name}",
            source,
        )


if __name__ == "__main__":
    unittest.main()
