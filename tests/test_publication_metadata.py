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
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_publication_metadata as checker  # noqa: E402
import publication_metadata as metadata  # noqa: E402


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
    schema_raw: str = "2",
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
        self.assertEqual(loaded.schema_version, 2)
        self.assertEqual(tuple(product.key for product in loaded.products), metadata.PRODUCT_ORDER)

    def test_minimal_complete_schema_2_document_passes(self) -> None:
        loaded = metadata.load_metadata(self.write(render_toml()))
        self.assertEqual(loaded.schema_version, 2)
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
        content = render_toml().replace("schema_version = 2\n\n", "")
        self.assert_issue(content, "MISSING_FIELD", "metadata.schema_version")

    def test_unknown_top_level_field(self) -> None:
        content = render_toml().replace(
            "schema_version = 2\n",
            "schema_version = 2\nunknown = true\n",
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

    def test_schema_1_and_unknown_schema_are_rejected(self) -> None:
        for value in ("1", "3"):
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
    def test_development_output_is_deterministic_and_reports_exact_schema_2_values(self) -> None:
        first = io.StringIO()
        second = io.StringIO()
        self.assertEqual(checker.main([], stdout=first), 0)
        self.assertEqual(checker.main([], stdout=second), 0)
        self.assertEqual(first.getvalue(), second.getvalue())

        rendered = first.getvalue()
        expected_lines = (
            "Schema version: 2",
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

    def test_valid_sequences(self) -> None:
        for value in ("2026-07-14.1", "2026-07-14.2", "2026-07-14.100"):
            with self.subTest(value=value):
                self.assertEqual(metadata.validate_release_identifier(value), value)

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
        context = metadata.validate_release_context("2026-07-14.1", "v2026-07-14.1")
        self.assertEqual(context.git_tag, "v2026-07-14.1")

    def test_missing_v(self) -> None:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.validate_release_context("2026-07-14", "2026-07-14")
        self.assertEqual(raised.exception.issues[0].code, "GIT_TAG_FORMAT")

    def test_malformed_tag(self) -> None:
        for value in ("version-2026-07-14", "v2026-02-30"):
            with self.subTest(value=value):
                with self.assertRaises(metadata.PublicationMetadataError) as raised:
                    metadata.validate_release_context("2026-07-14", value)
                self.assertEqual(raised.exception.issues[0].code, "GIT_TAG_FORMAT")

    def test_mismatched_date(self) -> None:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.validate_release_context("2026-07-14", "v2026-07-15")
        self.assertEqual(raised.exception.issues[0].code, "RELEASE_TAG_MISMATCH")

    def test_mismatched_sequence(self) -> None:
        with self.assertRaises(metadata.PublicationMetadataError) as raised:
            metadata.validate_release_context("2026-07-14.1", "v2026-07-14.2")
        self.assertEqual(raised.exception.issues[0].code, "RELEASE_TAG_MISMATCH")

    def test_release_mode_requires_release_and_tag_pair(self) -> None:
        for argv in (
            ["--mode", "release"],
            ["--mode", "release", "--release-id", "2026-07-14"],
            ["--mode", "release", "--git-tag", "v2026-07-14"],
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
        expected = {
            "integrated": f"{RELEASE_BASE}/2026-07-14/integrated",
            "alignment_core": f"{RELEASE_BASE}/2026-07-14/current-ssn-sosa/alignment-core",
            "strict_bfo_mapping": f"{RELEASE_BASE}/2026-07-14/current-ssn-sosa/bfo-mapping",
            "bfo_projection": f"{RELEASE_BASE}/2026-07-14/current-ssn-sosa/bfo-projection",
            "cco_extension": f"{RELEASE_BASE}/2026-07-14/current-ssn-sosa/cco-extension",
        }
        observed = {
            product.key: metadata.build_version_iri(product, "2026-07-14")
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
                "--git-tag",
                "v2026-07-14",
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
                "--git-tag",
                "v2026-07-15",
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
