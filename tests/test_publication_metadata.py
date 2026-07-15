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
POLICY_PRODUCTS = {
    "integrated": {
        "path": "SSN2BFO.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/",
        "release_iri_suffix": "integrated",
    },
    "alignment_core": {
        "path": "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core",
        "release_iri_suffix": "current-ssn-sosa/alignment-core",
    },
    "strict_bfo_mapping": {
        "path": "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping",
        "release_iri_suffix": "current-ssn-sosa/bfo-mapping",
    },
    "bfo_projection": {
        "path": "releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-projection",
        "release_iri_suffix": "current-ssn-sosa/bfo-projection",
    },
    "cco_extension": {
        "path": "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
        "stable_ontology_iri": "http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension",
        "release_iri_suffix": "current-ssn-sosa/cco-extension",
    },
}


def render_toml(
    *,
    product_order: tuple[str, ...] = metadata.PRODUCT_ORDER,
    omit_products: frozenset[str] = frozenset(),
    omit_fields: frozenset[tuple[str, str]] = frozenset(),
    raw_overrides: dict[tuple[str, str], str] | None = None,
    release_base_raw: str | None = None,
    schema_raw: str = "1",
) -> str:
    overrides = raw_overrides or {}
    lines = [f"schema_version = {schema_raw}", "", "[publication]"]
    lines.append(
        "release_iri_base = "
        + (release_base_raw if release_base_raw is not None else json.dumps(RELEASE_BASE))
    )
    for key in product_order:
        if key in omit_products:
            continue
        values = POLICY_PRODUCTS.get(
            key,
            {
                "path": f"releases/{key}.ttl",
                "stable_ontology_iri": f"http://example.org/{key}",
                "release_iri_suffix": key,
            },
        )
        lines.extend(["", f"[products.{key}]"])
        for field in metadata.PRODUCT_FIELDS:
            if (key, field) in omit_fields:
                continue
            raw = overrides.get((key, field), json.dumps(values[field]))
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
        self.assertEqual(loaded.schema_version, 1)
        self.assertEqual(tuple(product.key for product in loaded.products), metadata.PRODUCT_ORDER)

    def test_actual_config_is_locked_to_approved_policy_values(self) -> None:
        loaded = metadata.load_metadata(ACTUAL_CONFIG)
        self.assertEqual(loaded.release_iri_base, RELEASE_BASE)
        observed = {
            product.key: {
                "path": product.path,
                "stable_ontology_iri": product.stable_ontology_iri,
                "release_iri_suffix": product.release_iri_suffix,
            }
            for product in loaded.products
        }
        self.assertEqual(observed, POLICY_PRODUCTS)

    def test_malformed_toml(self) -> None:
        self.assert_issue("schema_version =\n", "TOML_PARSE")

    def test_missing_top_level_field(self) -> None:
        content = render_toml().replace("schema_version = 1\n\n", "")
        self.assert_issue(content, "MISSING_FIELD", "metadata.schema_version")

    def test_unknown_top_level_field(self) -> None:
        content = render_toml().replace(
            "schema_version = 1\n",
            "schema_version = 1\nunknown = true\n",
        )
        self.assert_issue(content, "UNKNOWN_FIELD", "metadata.unknown")

    def test_unknown_publication_field(self) -> None:
        content = render_toml().replace(
            "[publication]\n",
            "[publication]\nunknown = true\n",
        )
        self.assert_issue(content, "UNKNOWN_FIELD", "publication.unknown")

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

    def test_wrong_schema_version(self) -> None:
        self.assert_issue(render_toml(schema_raw="2"), "SCHEMA_VERSION", "schema_version")

    def test_reordered_product_tables_return_canonical_order(self) -> None:
        loaded = metadata.load_metadata(
            self.write(render_toml(product_order=tuple(reversed(metadata.PRODUCT_ORDER))))
        )
        self.assertEqual(tuple(product.key for product in loaded.products), metadata.PRODUCT_ORDER)


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


class DevelopmentModeTests(MetadataTestCase):
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
