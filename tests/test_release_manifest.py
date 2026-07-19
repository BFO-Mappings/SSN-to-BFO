#!/usr/bin/env python3
"""Schema-1 release-manifest model and canonicalization regressions."""

from __future__ import annotations

import dataclasses
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import release_manifest as manifest  # noqa: E402


HASH = "1" * 64
INCLUDED_PATHS = (
    "LICENSE",
    "RELEASE-NOTES.md",
    "SSN2BFO.ttl",
    "catalog-v001.xml",
    "current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    "current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    "current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
    "current-ssn-sosa/ssn-sosa-cco-extension.ttl",
    "evidence/coms-product-dispositions.json",
    "sources/SSN2BFO-COMS.xlsx",
    "sources/publication-metadata.toml",
)


def valid_manifest() -> manifest.ReleaseManifest:
    inputs = tuple(
        manifest.ReleaseManifestInput(
            key=key,
            source_path=(
                "mappings/SSN2BFO-COMS.xlsx"
                if key == "coms_workbook"
                else "config/publication-metadata.toml"
                if key == "publication_metadata"
                else "reports/coms-product-dispositions.json"
                if key == "product_dispositions"
                else "release-notes/2099-01-02.md"
                if key == "release_notes"
                else "LICENSE"
                if key == "license"
                else "tools/" + key.removeprefix("module_") + ".py"
            ),
            package_path=(
                "sources/SSN2BFO-COMS.xlsx"
                if key == "coms_workbook"
                else "sources/publication-metadata.toml"
                if key == "publication_metadata"
                else "evidence/coms-product-dispositions.json"
                if key == "product_dispositions"
                else "RELEASE-NOTES.md"
                if key == "release_notes"
                else "LICENSE"
                if key == "license"
                else None
            ),
            sha256=HASH,
            byte_size=1,
        )
        for key in manifest.INPUT_KEY_ORDER
    )
    products = tuple(
        manifest.ReleaseManifestProduct(
            key=key,
            path="SSN2BFO.ttl" if key == "integrated" else f"current-ssn-sosa/{key}.ttl",
            stable_ontology_iri=f"http://example.org/stable/{key}",
            version_iri=f"http://example.org/releases/2099-01-02/{key}",
            imports=tuple(
                f"http://example.org/import/{key}/{index}"
                for index in range(manifest.PRODUCT_IMPORT_COUNTS[key])
            ),
            sha256=HASH,
            byte_size=1,
            ontology_declaration_count=1,
            import_count=manifest.PRODUCT_IMPORT_COUNTS[key],
            static_metadata_count=7,
            formal_metadata_count=3,
            logical_triple_count=0,
            total_triple_count=11,
            direct_governed_axiom_count=0,
            governed_closure_axiom_count=0,
            reasoning_mode="independent",
        )
        for key in manifest.PRODUCT_ORDER
    )
    dependencies = tuple(
        manifest.ReleaseManifestDependency(
            key=key,
            role="validation dependency",
            path=f"imports/{key}.ttl",
            ontology_iri=f"http://example.org/{key}",
            version_iri=None,
            sha256=HASH,
            byte_size=1,
        )
        for key in manifest.DEPENDENCY_KEY_ORDER
    )
    environment = manifest.ReleaseManifestValidationEnvironment(
        python_implementation="CPython",
        python_version="3.12.4",
        java_vendor="Oracle Corporation",
        java_version="22.0.2",
        java_vm_name="Java HotSpot(TM) 64-Bit Server VM",
        robot_artifact="https://example.org/robot.jar",
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
            manifest.ReleaseManifestHermitResult(key, "PASS", count, 0, True, 0, 0)
            for key, count in manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS
        ),
    )
    included = tuple(
        manifest.ReleaseManifestIncludedFile(path, "included file", HASH, 1)
        for path in INCLUDED_PATHS
    )
    return manifest.build_release_manifest(
        release_identifier="2099-01-02",
        release_date="2099-01-02",
        git_tag="v2099-01-02",
        source_commit="0123456789abcdef0123456789abcdef01234567",
        repository_iri="https://github.com/BFO-Mappings/SSN-to-BFO",
        inputs=inputs,
        product_order=manifest.PRODUCT_ORDER,
        products=products,
        dependencies=dependencies,
        validation_environment=environment,
        validation=validation,
        included_files=included,
    )


class ReleaseManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = valid_manifest()
        self.serialized = manifest.canonical_manifest_bytes(self.manifest)
        self.document = json.loads(self.serialized)
        self.schema = json.loads(
            (REPO_ROOT / "config/release-manifest-schema-v1.json").read_text()
        )

    def assert_python_accepts(self, document) -> None:
        self.assertEqual(manifest.validate_release_manifest_document(document), ())

    def assert_python_rejects(self, document) -> None:
        self.assertTrue(manifest.validate_release_manifest_document(document))

    def test_models_are_frozen_and_schema_version_is_one(self) -> None:
        self.assertEqual(self.manifest.schema_version, 1)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.manifest.release_identifier = "changed"  # type: ignore[misc]

    def test_json_schema_and_python_field_models_are_synchronized(self) -> None:
        self.assert_python_accepts(self.document)
        self.assertEqual(
            self.schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertEqual(self.schema["type"], "object")
        self.assertEqual(tuple(self.schema["required"]), manifest.TOP_LEVEL_FIELDS)
        self.assertEqual(tuple(self.schema["properties"]), manifest.TOP_LEVEL_FIELDS)
        self.assertFalse(self.schema["additionalProperties"])
        definitions = self.schema["$defs"]
        models = (
            ("input", manifest.INPUT_FIELDS),
            ("product", manifest.PRODUCT_FIELDS),
            ("dependency", manifest.DEPENDENCY_FIELDS),
            ("validationEnvironment", manifest.VALIDATION_ENVIRONMENT_FIELDS),
            ("validation", manifest.VALIDATION_FIELDS),
            ("hermitResult", manifest.HERMIT_FIELDS),
            ("includedFile", manifest.INCLUDED_FILE_FIELDS),
        )
        for name, fields in models:
            with self.subTest(model=name):
                self.assertEqual(tuple(definitions[name]["required"]), fields)
                self.assertEqual(set(definitions[name]["properties"]), set(fields))
                self.assertFalse(definitions[name]["additionalProperties"])
        self.assertEqual(tuple(definitions["input"]["required"]), manifest.INPUT_FIELDS)
        self.assertEqual(tuple(definitions["product"]["required"]), manifest.PRODUCT_FIELDS)
        self.assertEqual(tuple(definitions["dependency"]["required"]), manifest.DEPENDENCY_FIELDS)
        self.assertEqual(
            tuple(definitions["validationEnvironment"]["required"]),
            manifest.VALIDATION_ENVIRONMENT_FIELDS,
        )

    def test_schema_scalar_rules_match_governed_python_boundaries(self) -> None:
        definitions = self.schema["$defs"]
        properties = self.schema["properties"]
        self.assertEqual(properties["schema_version"], {"const": manifest.SCHEMA_VERSION})
        self.assertEqual(tuple(properties["product_order"]["const"]), manifest.PRODUCT_ORDER)
        self.assertEqual(
            tuple(definitions["product"]["properties"]["key"]["enum"]),
            manifest.PRODUCT_ORDER,
        )
        self.assertEqual(
            tuple(definitions["hermitResult"]["properties"]["product_key"]["enum"]),
            manifest.PRODUCT_ORDER,
        )
        self.assertEqual(
            definitions["sha256"],
            {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        )
        self.assertEqual(
            definitions["relativePath"],
            {
                "type": "string",
                "minLength": 1,
                "pattern": (
                    r"^(?!/)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*//)(?!.*\\)"
                    r"(?![A-Za-z][A-Za-z0-9+.-]*:)(?!.*[\u0000-\u001F\u007F])"
                    r"(?!.*/$).+$"
                ),
            },
        )

        hash_fields = (
            ("input", "sha256"),
            ("product", "sha256"),
            ("dependency", "sha256"),
            ("validationEnvironment", "robot_sha256"),
            ("validationEnvironment", "toolchain_sha256"),
            ("validationEnvironment", "requirements_sha256"),
            ("includedFile", "sha256"),
        )
        for model, field in hash_fields:
            with self.subTest(hash_field=f"{model}.{field}"):
                self.assertEqual(
                    definitions[model]["properties"][field],
                    {"$ref": "#/$defs/sha256"},
                )

        path_fields = (
            ("input", "source_path"),
            ("product", "path"),
            ("dependency", "path"),
            ("validationEnvironment", "toolchain_path"),
            ("validationEnvironment", "requirements_path"),
            ("includedFile", "path"),
        )
        for model, field in path_fields:
            with self.subTest(path_field=f"{model}.{field}"):
                self.assertEqual(
                    definitions[model]["properties"][field],
                    {"$ref": "#/$defs/relativePath"},
                )

        integer_fields = (
            ("input", "byte_size"),
            ("product", "byte_size"),
            ("product", "ontology_declaration_count"),
            ("product", "import_count"),
            ("product", "static_metadata_count"),
            ("product", "formal_metadata_count"),
            ("product", "logical_triple_count"),
            ("product", "total_triple_count"),
            ("product", "direct_governed_axiom_count"),
            ("product", "governed_closure_axiom_count"),
            ("dependency", "byte_size"),
            ("hermitResult", "fixed_closure_triple_count"),
            ("includedFile", "byte_size"),
        )
        for model, field in integer_fields:
            with self.subTest(integer_field=f"{model}.{field}"):
                self.assertEqual(
                    definitions[model]["properties"][field],
                    {"type": "integer", "minimum": 0},
                )

        self.assertEqual(
            definitions["product"]["properties"]["reasoning_mode"],
            {"const": "independent"},
        )
        for field in manifest.VALIDATION_FIELDS[:-1]:
            self.assertEqual(
                definitions["validation"]["properties"][field],
                {"const": True},
            )
        hermit_properties = definitions["hermitResult"]["properties"]
        self.assertEqual(hermit_properties["status"], {"const": "PASS"})
        self.assertEqual(hermit_properties["return_code"], {"const": 0})
        self.assertEqual(
            hermit_properties["reasoned_output_produced"], {"const": True}
        )
        self.assertEqual(
            hermit_properties["named_unsatisfiable_class_count"], {"const": 0}
        )
        self.assertEqual(
            hermit_properties["owl_nothing_equivalent_named_class_count"],
            {"const": 0},
        )

    def test_module_has_no_external_schema_package_dependency(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        package_name = "json" + "schema"
        self.assertNotIn(f"import {package_name}", source)
        self.assertNotIn(f"from {package_name}", source)
        self.assertNotIn(f"{package_name}.", source)

    def test_fixed_array_cardinalities_and_positional_authorities_match(self) -> None:
        arrays = (
            ("inputs", manifest.INPUT_KEY_ORDER, "key"),
            ("products", manifest.PRODUCT_ORDER, "key"),
            ("dependencies", manifest.DEPENDENCY_KEY_ORDER, "key"),
            ("included_files", manifest.INCLUDED_FILE_PATH_ORDER, "path"),
        )
        for field, expected, identity in arrays:
            with self.subTest(field=field):
                schema = self.schema["properties"][field]
                self.assertEqual(schema["minItems"], len(expected))
                self.assertEqual(schema["maxItems"], len(expected))
                self.assertFalse(schema["items"])
                self.assertEqual(len(schema["prefixItems"]), len(expected))
                observed = tuple(
                    item["allOf"][1]["properties"][identity]["const"]
                    for item in schema["prefixItems"]
                )
                self.assertEqual(observed, expected)
        hermit = self.schema["$defs"]["validation"]["properties"]["hermit_results"]
        self.assertEqual((hermit["minItems"], hermit["maxItems"]), (5, 5))
        self.assertFalse(hermit["items"])
        self.assertEqual(
            tuple(
                item["allOf"][1]["properties"]["product_key"]["const"]
                for item in hermit["prefixItems"]
            ),
            manifest.PRODUCT_ORDER,
        )
        self.assertEqual(
            tuple(
                (
                    item["allOf"][1]["properties"]["product_key"]["const"],
                    item["allOf"][1]["properties"]["fixed_closure_triple_count"]["const"],
                )
                for item in hermit["prefixItems"]
            ),
            manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS,
        )

    def test_canonical_bytes_have_schema_order_utf8_and_one_newline(self) -> None:
        document = json.loads(self.serialized)
        self.assertEqual(tuple(document), manifest.TOP_LEVEL_FIELDS)
        self.assertTrue(self.serialized.endswith(b"\n"))
        self.assertFalse(self.serialized.endswith(b"\n\n"))
        self.assertIn(b'  "schema_version": 1', self.serialized)
        self.assertNotIn(b"manifest_sha256", self.serialized)
        self.assertNotIn(b"sha256sums_sha256", self.serialized)

    def test_canonical_round_trip_is_byte_identical(self) -> None:
        loaded = manifest.load_and_validate_release_manifest(self.serialized)
        self.assertEqual(loaded, self.manifest)
        self.assertEqual(manifest.canonical_manifest_bytes(loaded), self.serialized)
        self.assertEqual(manifest.release_manifest_sha256(loaded), manifest.release_manifest_sha256(self.serialized))

    def test_reordered_collections_serialize_identically(self) -> None:
        reordered = dataclasses.replace(
            self.manifest,
            inputs=tuple(reversed(self.manifest.inputs)),
            products=tuple(reversed(self.manifest.products)),
            dependencies=tuple(reversed(self.manifest.dependencies)),
            validation=dataclasses.replace(
                self.manifest.validation,
                hermit_results=tuple(reversed(self.manifest.validation.hermit_results)),
            ),
            included_files=tuple(reversed(self.manifest.included_files)),
        )
        self.assertEqual(manifest.canonical_manifest_bytes(reordered), self.serialized)

    def test_semantically_equivalent_reordered_json_is_noncanonical(self) -> None:
        document = json.loads(self.serialized)
        document["inputs"].reverse()
        noncanonical = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode()
        with self.assertRaises(manifest.ReleaseManifestError) as raised:
            manifest.load_and_validate_release_manifest(noncanonical)
        self.assertIn("NONCANONICAL_SERIALIZATION", {value.code for value in raised.exception.issues})
        self.assertEqual(manifest.canonical_manifest_bytes(document), self.serialized)

    def test_unknown_fields_are_rejected_at_every_object_level(self) -> None:
        locations = (
            ((), self.schema),
            (("inputs", 0), self.schema["$defs"]["input"]),
            (("products", 0), self.schema["$defs"]["product"]),
            (("dependencies", 0), self.schema["$defs"]["dependency"]),
            (("validation_environment",), self.schema["$defs"]["validationEnvironment"]),
            (("validation",), self.schema["$defs"]["validation"]),
            (("validation", "hermit_results", 0), self.schema["$defs"]["hermitResult"]),
            (("included_files", 0), self.schema["$defs"]["includedFile"]),
        )
        for location, schema_model in locations:
            with self.subTest(location=location):
                self.assertFalse(schema_model["additionalProperties"])
                document = json.loads(self.serialized)
                target = document
                for component in location:
                    target = target[component]
                target["unexpected"] = True
                self.assert_python_rejects(document)

    def test_missing_nested_required_fields_are_rejected_by_both_models(self) -> None:
        locations = (
            (("inputs", 0, "sha256"), self.schema["$defs"]["input"]),
            (("products", 0, "version_iri"), self.schema["$defs"]["product"]),
            (("dependencies", 0, "path"), self.schema["$defs"]["dependency"]),
            (("validation_environment", "java_vendor"), self.schema["$defs"]["validationEnvironment"]),
            (("validation", "hermit_results"), self.schema["$defs"]["validation"]),
            (("included_files", 0, "byte_size"), self.schema["$defs"]["includedFile"]),
        )
        for location, schema_model in locations:
            with self.subTest(location=location):
                self.assertIn(location[-1], schema_model["required"])
                document = json.loads(self.serialized)
                target = document
                for component in location[:-1]:
                    target = target[component]
                del target[location[-1]]
                self.assert_python_rejects(document)

    def test_duplicate_json_field_is_rejected(self) -> None:
        duplicate = self.serialized.replace(
            b'{\n  "schema_version": 1,',
            b'{\n  "schema_version": 1,\n  "schema_version": 1,',
            1,
        )
        with self.assertRaises(manifest.ReleaseManifestError) as raised:
            manifest.load_and_validate_release_manifest(duplicate)
        self.assertEqual({value.code for value in raised.exception.issues}, {"DUPLICATE_FIELD"})

    def test_floating_point_value_is_rejected(self) -> None:
        value = self.serialized.replace(b'"byte_size": 1', b'"byte_size": 1.0', 1)
        with self.assertRaises(manifest.ReleaseManifestError) as raised:
            manifest.load_and_validate_release_manifest(value)
        self.assertEqual({item.code for item in raised.exception.issues}, {"INVALID_JSON"})

    def test_unsafe_paths_are_rejected(self) -> None:
        relative_path = self.schema["$defs"]["relativePath"]
        self.assertEqual(relative_path["type"], "string")
        self.assertEqual(relative_path["minLength"], 1)
        self.assertIn("(?!.*/$)", relative_path["pattern"])
        for value in (
            "/absolute",
            "../escape",
            "a/./b",
            "a//b",
            "a\\b",
            "file:thing",
            "sources/",
            "a\x00b",
            "a\x7fb",
        ):
            with self.subTest(value=value):
                document = json.loads(self.serialized)
                document["included_files"][0]["path"] = value
                self.assert_python_rejects(document)

    def test_nonzero_hermit_return_code_is_rejected_by_both_models(self) -> None:
        self.assertEqual(
            self.schema["$defs"]["hermitResult"]["properties"]["return_code"],
            {"const": 0},
        )
        document = json.loads(self.serialized)
        document["validation"]["hermit_results"][0]["return_code"] = 1
        python_issues = manifest.validate_release_manifest_document(document)
        self.assertIn("HERMIT_RETURN_CODE", {item.code for item in python_issues})

    def test_each_wrong_fixed_closure_count_is_rejected_by_both_models(self) -> None:
        positional = self.schema["$defs"]["validation"]["properties"][
            "hermit_results"
        ]["prefixItems"]
        for index, (product_key, _) in enumerate(
            manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS
        ):
            with self.subTest(product=product_key):
                count_rule = positional[index]["allOf"][1]["properties"][
                    "fixed_closure_triple_count"
                ]
                self.assertEqual(
                    count_rule,
                    {"const": manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS[index][1]},
                )
                document = json.loads(self.serialized)
                document["validation"]["hermit_results"][index][
                    "fixed_closure_triple_count"
                ] = 999
                python_issues = manifest.validate_release_manifest_document(document)
                self.assertIn(
                    "FIXED_CLOSURE_TRIPLE_COUNT_MISMATCH",
                    {item.code for item in python_issues},
                )

    def test_hermit_result_identity_count_and_cardinality_are_positional(self) -> None:
        hermit_schema = self.schema["$defs"]["validation"]["properties"][
            "hermit_results"
        ]
        self.assertEqual(
            (hermit_schema["minItems"], hermit_schema["maxItems"]),
            (5, 5),
        )
        self.assertFalse(hermit_schema["items"])
        self.assertEqual(len(hermit_schema["prefixItems"]), 5)
        mutations = []
        for index in range(len(manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS) - 1):
            swapped = json.loads(self.serialized)
            results = swapped["validation"]["hermit_results"]
            results[index], results[index + 1] = results[index + 1], results[index]
            mutations.append((f"swap-{index}", swapped))

        wrong_product_count = json.loads(self.serialized)
        wrong_product_count["validation"]["hermit_results"][1][
            "fixed_closure_triple_count"
        ] = manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS[0][1]
        mutations.append(("wrong-product-count", wrong_product_count))

        missing = json.loads(self.serialized)
        missing["validation"]["hermit_results"].pop()
        mutations.append(("missing", missing))

        duplicated = json.loads(self.serialized)
        duplicated["validation"]["hermit_results"][1] = dict(
            duplicated["validation"]["hermit_results"][0]
        )
        mutations.append(("duplicated", duplicated))

        sixth = json.loads(self.serialized)
        sixth["validation"]["hermit_results"].append(
            dict(sixth["validation"]["hermit_results"][0])
        )
        mutations.append(("sixth", sixth))

        for name, document in mutations:
            with self.subTest(case=name):
                self.assert_python_rejects(document)

    def test_fixed_arrays_reject_extra_missing_duplicate_and_reordered_records(self) -> None:
        mutations = []
        extra_dependency = json.loads(self.serialized)
        extra_dependency["dependencies"].append(
            {**extra_dependency["dependencies"][0], "key": "extra"}
        )
        mutations.append(("sixth dependency", extra_dependency))
        extra_product = json.loads(self.serialized)
        extra_product["products"].append(dict(extra_product["products"][0]))
        mutations.append(("sixth product", extra_product))
        extra_included = json.loads(self.serialized)
        extra_included["included_files"].append(
            {**extra_included["included_files"][0], "path": "extra.txt"}
        )
        mutations.append(("extra included", extra_included))
        duplicate_input = json.loads(self.serialized)
        duplicate_input["inputs"][1] = dict(duplicate_input["inputs"][0])
        mutations.append(("duplicate input", duplicate_input))
        reordered_dependency = json.loads(self.serialized)
        reordered_dependency["dependencies"].reverse()
        mutations.append(("dependency order", reordered_dependency))
        reordered_included = json.loads(self.serialized)
        reordered_included["included_files"].reverse()
        mutations.append(("included order", reordered_included))
        for name, document in mutations:
            with self.subTest(case=name):
                self.assert_python_rejects(document)

    def test_hash_and_integer_boundaries_match(self) -> None:
        self.assertEqual(
            self.schema["$defs"]["sha256"]["pattern"], "^[0-9a-f]{64}$"
        )
        self.assertEqual(
            self.schema["$defs"]["includedFile"]["properties"]["byte_size"],
            {"type": "integer", "minimum": 0},
        )
        self.assertEqual(
            self.schema["$defs"]["product"]["properties"]["total_triple_count"],
            {"type": "integer", "minimum": 0},
        )
        mutations = []
        malformed_hash = json.loads(self.serialized)
        malformed_hash["inputs"][0]["sha256"] = "A" * 64
        mutations.append(("hash", malformed_hash))
        negative_size = json.loads(self.serialized)
        negative_size["included_files"][0]["byte_size"] = -1
        mutations.append(("negative", negative_size))
        boolean_count = json.loads(self.serialized)
        boolean_count["products"][0]["total_triple_count"] = True
        mutations.append(("boolean", boolean_count))
        for name, document in mutations:
            with self.subTest(case=name):
                self.assert_python_rejects(document)

    def test_context_validation_is_reused(self) -> None:
        document = json.loads(self.serialized)
        document["source_commit"] = "abc"
        issues = manifest.validate_release_manifest_document(document)
        self.assertIn("SOURCE_COMMIT_FORMAT", {item.code for item in issues})

    def test_product_and_hermit_order_are_exact(self) -> None:
        self.assertEqual(
            tuple(self.schema["properties"]["product_order"]["const"]),
            manifest.PRODUCT_ORDER,
        )
        document = json.loads(self.serialized)
        document["products"].reverse()
        document["validation"]["hermit_results"].reverse()
        codes = {item.code for item in manifest.validate_release_manifest_document(document)}
        self.assertIn("PRODUCT_RECORD_ORDER", codes)
        self.assertIn("HERMIT_PRODUCT_ORDER", codes)

    def test_included_files_exclude_manifest_and_checksums(self) -> None:
        included_schema = self.schema["properties"]["included_files"]
        self.assertEqual(
            tuple(
                value["allOf"][1]["properties"]["path"]["const"]
                for value in included_schema["prefixItems"]
            ),
            manifest.INCLUDED_FILE_PATH_ORDER,
        )
        paths = {value.path for value in self.manifest.included_files}
        self.assertEqual(len(paths), 11)
        self.assertNotIn("manifest.json", paths)
        self.assertNotIn("SHA256SUMS", paths)
        document = json.loads(self.serialized)
        document["included_files"][0]["path"] = "manifest.json"
        codes = {item.code for item in manifest.validate_release_manifest_document(document)}
        self.assertIn("MANIFEST_SELF_REFERENCE", codes)


if __name__ == "__main__":
    unittest.main()
