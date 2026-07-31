#!/usr/bin/env python3
"""Regression gates for retired current placeholders and development catalogs."""

from __future__ import annotations

import hashlib
import stat
import subprocess
import sys
import unittest
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

from rdflib import Graph, OWL, RDFS


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import build_release  # noqa: E402
import publication_metadata  # noqa: E402
import release_archive  # noqa: E402
import release_context  # noqa: E402


CATALOG_NAMESPACE = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
REMOVED_PATHS = (
    "imports/catalog-v001.xml",
    "releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl",
    "releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl",
    "src/current-ssn-sosa/catalog-v001.xml",
    "src/current-ssn-sosa/ssn-sosa-mappings-edit.ttl",
    "src/current-ssn-sosa/sparql/artifact-metadata.rq",
    "src/current-ssn-sosa/sparql/construct/README.md",
    "src/current-ssn-sosa/sparql/construct/derive-bfo-from-cco.rq",
    "src/current-ssn-sosa/sparql/report/unprojectable-cco-targets.rq",
)
RETIRED_IGNORED_OUTPUTS = (
    "src/current-ssn-sosa/build/artifacts/current-ssn-sosa-bfo-only-generated.ttl",
    "src/current-ssn-sosa/build/artifacts/current-ssn-sosa-bfo-only-skipped-cco-targets.csv",
    "src/current-ssn-sosa/build/artifacts/current-ssn-sosa-projection-catalog.xml",
)
RETIRED_PLACEHOLDER_HASHES = frozenset(
    {
        "397fc7a1566afddc271fee066dc55311f9b61c4be887212be84d6ae9462df3e8",
        "33e616a74bd959fec6128779dddee7fb52e2faca8f5669d9ff5faab079a408f1",
    }
)
RETIRED_REFERENCE_TERMS = (
    *REMOVED_PATHS,
    "ssn-sosa-bfo-directmappings.ttl",
    "ssn-sosa-cco-directmappings.ttl",
    "ssn-sosa-mappings-edit.ttl",
    "artifact-metadata.rq",
    "derive-bfo-from-cco",
    "unprojectable-cco-targets",
    "current-ssn-sosa-bfo-only-generated.ttl",
    "current-ssn-sosa-bfo-only-skipped-cco-targets.csv",
    "current-ssn-sosa-projection-catalog.xml",
    "https://w3id.org/ssn-sosa-bfo-cco-mapping/current-ssn-sosa/bfo",
    "https://w3id.org/ssn-sosa-bfo-cco-mapping/current-ssn-sosa/cco",
    "https://w3id.org/ssn-sosa-bfo-cco-mapping/current-ssn-sosa/edit",
)
HISTORICAL_REFERENCE_ALLOWLIST = frozenset(
    {
        "reports/current-ssn-sosa-release-readiness-audit.md",
        "reports/prov-functional-parity-audit.md",
        "reports/sosa-import-closure-fidelity-audit.md",
    }
)
NEGATIVE_GUARD_PATHS = frozenset(
    {
        "tests/test_placeholder_catalog_migration.py",
        "tools/workflow_check.py",
    }
)

SOSA_NEXT_HASHES = {
    "releases/sosa-next/sosa-bfo-directmappings.ttl":
        "0e814b9e9bdb03cca73bb15e307b2d0ca13424f0c19775aa0feaf440c2879a18",
    "releases/sosa-next/sosa-cco-directmappings.ttl":
        "1bf9de31bf344c9b90c673cf3bab05467a7bb1026f8cb36d27e25cb9fabcfd2b",
    "src/sosa-next/sosa-mappings-edit.ttl":
        "7a27a32b8e76af2d57bf8ded5fe8b7e61ad67792c36ba3e3917d1279f8cd63d3",
}
DEPENDENCY_HASHES = {
    "imports/cco.ttl": "3ad8f098ecb3d7ca27464a1edf2795b90c69573843447d51f090e6f1b30694f4",
    "imports/sosa.ttl": "0dad03b30c7fdd085e2629dfc0ebd10bb1dacbda73b2c375fb295ab6861ffb33",
    "imports/sosa-sampling.ttl": "f6e1d9451732bb132fa4ba567ca58fba752dcfbb43e66c5d4b660963bd0f7c1a",
    "imports/ssn.ttl": "434b50fecb32e14b30aac28310a76935a33fdc397e70fce887fd653069a59383",
    "imports/ssn-systems.ttl": "156870689643840c861aaead206458bcdfc9cded5f7107598dbf87e015861105",
}
MAINTAINED_PRODUCT_HASHES = {
    "SSN2BFO.ttl": "25b5828424e48396db546b2c3732befec2defcd3159c2a132a2f73343d1f17e0",
    "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl":
        "17695ef17379924449153b2c92ffaed6b57d497a1b2d1e854f584614cebec770",
    "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl":
        "676b31620df10db5c26c46bcc44b2dfd5939d606b16e0fa8a910926e8497c3af",
    "releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl":
        "b5c1163eb6ab24c2e111e9e76c7b97acb20d897c9d1abc3daa555628206da5b0",
    "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl":
        "fc98e6fafa1a3a5c8612fd9b8e4e571e9a382faa3f9ca9801e64533b91f00aaf",
}
SOSA_NEXT_CATALOG_MAPPINGS = (
    (
        "http://www.w3.org/ns/sosa/",
        "imports/sosa.ttl",
    ),
    (
        "http://www.w3.org/ns/sosa/common/",
        "imports/sosa-common.ttl",
    ),
    (
        "http://www.w3.org/ns/sosa/act/",
        "imports/sosa-actuation.ttl",
    ),
    (
        "http://www.w3.org/ns/sosa/dep/",
        "imports/sosa-deprecated.ttl",
    ),
    (
        "http://www.w3.org/ns/sosa/obs/",
        "imports/sosa-observation.ttl",
    ),
    (
        "http://www.w3.org/ns/sosa/sam/",
        "imports/sosa-sampling.ttl",
    ),
    (
        "http://www.w3.org/ns/sosa/systems/",
        "imports/sosa-system.ttl",
    ),
    (
        "http://www.w3.org/ns/sosa/sampling/",
        "imports/sample-relations.ttl",
    ),
    (
        "http://www.sks.ai/SSN2BFO/development/"
        "sosa-next/source-declaration-overlay",
        "imports/sosa-source-declaration-overlay.ttl",
    ),
    (
        "https://www.commoncoreontologies.org/"
        "CommonCoreOntologiesMerged",
        "../../imports/cco.ttl",
    ),
    (
        "https://w3id.org/ssn-sosa-bfo-cco-mapping/sosa-next/bfo",
        "../../releases/sosa-next/sosa-bfo-directmappings.ttl",
    ),
    (
        "https://w3id.org/ssn-sosa-bfo-cco-mapping/sosa-next/cco",
        "../../releases/sosa-next/sosa-cco-directmappings.ttl",
    ),
    (
        "https://w3id.org/ssn-sosa-bfo-cco-mapping/sosa-next/edit",
        "sosa-mappings-edit.ttl",
    ),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tracked_paths(pattern: str | None = None) -> tuple[str, ...]:
    command = ["git", "ls-files", "-z"]
    if pattern is not None:
        command.extend(["--", pattern])
    output = subprocess.check_output(command, cwd=REPO_ROOT)
    return tuple(item.decode("utf-8") for item in output.split(b"\0") if item)


class PlaceholderCatalogMigrationTests(unittest.TestCase):
    def test_retired_current_paths_and_ignored_outputs_are_absent(self) -> None:
        for relative in (*REMOVED_PATHS, *RETIRED_IGNORED_OUTPUTS):
            with self.subTest(path=relative):
                path = REPO_ROOT / relative
                self.assertFalse(path.exists())
                self.assertFalse(path.is_symlink())

    def test_retired_placeholder_bytes_do_not_survive_as_tracked_regular_files(self) -> None:
        matches: list[str] = []
        for relative in tracked_paths():
            path = REPO_ROOT / relative
            try:
                mode = path.lstat().st_mode
            except FileNotFoundError:
                continue
            if stat.S_ISREG(mode) and sha256(path) in RETIRED_PLACEHOLDER_HASHES:
                matches.append(relative)
        self.assertEqual(matches, [])

    def test_retired_references_occur_only_in_enumerated_historical_reports(self) -> None:
        occurrences: dict[str, list[str]] = {}
        for relative in tracked_paths():
            if relative in NEGATIVE_GUARD_PATHS:
                continue
            path = REPO_ROOT / relative
            try:
                if not stat.S_ISREG(path.lstat().st_mode):
                    continue
                text = path.read_text(encoding="utf-8")
            except (FileNotFoundError, UnicodeDecodeError):
                continue
            matched = sorted(term for term in RETIRED_REFERENCE_TERMS if term in text)
            if matched:
                occurrences[relative] = matched
        self.assertEqual(set(occurrences), set(HISTORICAL_REFERENCE_ALLOWLIST), occurrences)

    def test_sosa_next_scaffold_ttl_is_byte_preserved_and_parseable(self) -> None:
        for relative, expected_hash in SOSA_NEXT_HASHES.items():
            with self.subTest(path=relative):
                path = REPO_ROOT / relative
                self.assertTrue(stat.S_ISREG(path.lstat().st_mode))
                self.assertEqual(sha256(path), expected_hash)
                self.assertGreater(
                    len(Graph().parse(path, format="turtle")),
                    0,
                )

    def test_pinned_dependencies_are_preserved_parseable_and_logically_nonempty(self) -> None:
        parsed: dict[str, Graph] = {}
        for relative, expected_hash in DEPENDENCY_HASHES.items():
            with self.subTest(path=relative):
                path = REPO_ROOT / relative
                self.assertTrue(stat.S_ISREG(path.lstat().st_mode))
                self.assertEqual(sha256(path), expected_hash)
                parsed[relative] = Graph().parse(path, format="turtle")
                self.assertGreater(len(parsed[relative]), 0)
        cco_path = REPO_ROOT / "imports/cco.ttl"
        self.assertGreater(cco_path.stat().st_size, 1_000_000)
        logical_predicates = {RDFS.subClassOf, RDFS.subPropertyOf, OWL.equivalentClass}
        self.assertTrue(any(predicate in logical_predicates for _, predicate, _ in parsed["imports/cco.ttl"]))

    def test_remaining_tracked_catalog_is_safe_and_has_exact_sosa_next_mappings(self) -> None:
        catalogs = tuple(
            relative
            for relative in tracked_paths("*catalog*.xml")
            if (REPO_ROOT / relative).is_file()
        )
        self.assertEqual(catalogs, ("src/sosa-next/catalog-v001.xml",))
        catalog_path = REPO_ROOT / catalogs[0]
        root = ElementTree.parse(catalog_path).getroot()
        self.assertEqual(root.tag, f"{{{CATALOG_NAMESPACE}}}catalog")
        entries = tuple(
            (child.attrib["name"], child.attrib["uri"])
            for child in root.findall(
                f".//{{{CATALOG_NAMESPACE}}}uri"
            )
        )

        self.assertEqual(
            len(entries),
            len(SOSA_NEXT_CATALOG_MAPPINGS),
        )
        self.assertEqual(
            len({name for name, _ in entries}),
            len(entries),
        )
        self.assertEqual(
            dict(entries),
            dict(SOSA_NEXT_CATALOG_MAPPINGS),
        )

        for name, target in entries:
            with self.subTest(name=name, target=target):
                self.assertTrue(name)
                self.assertFalse(PurePosixPath(target).is_absolute())
                self.assertNotIn("\\", target)
                self.assertNotIn("/Users/", target)

                resolved = (catalog_path.parent / target).resolve()
                self.assertTrue(resolved.is_file())
                self.assertTrue(
                    resolved.is_relative_to(REPO_ROOT.resolve())
                )

    def test_formal_package_catalog_uses_production_generator_and_governed_order(self) -> None:
        metadata = publication_metadata.load_metadata(REPO_ROOT / "config/publication-metadata.toml")
        context = release_context.parse_formal_release_context(
            "2099-01-02",
            "2099-01-02",
            "v2099-01-02",
            "0123456789abcdef0123456789abcdef01234567",
        )
        value = build_release.canonical_catalog_bytes(metadata, context)
        self.assertEqual(build_release.validate_catalog_bytes(value, metadata, context), ())
        root = ElementTree.fromstring(value)
        entries = tuple(
            (child.attrib["name"], child.attrib["uri"])
            for child in root.findall(f"{{{CATALOG_NAMESPACE}}}uri")
        )
        expected = tuple(
            (
                publication_metadata.release_version_iri(metadata, key, context),
                build_release.PRODUCT_PACKAGE_PATHS[key],
            )
            for key in publication_metadata.PRODUCT_ORDER
        )
        self.assertEqual(entries, expected)
        self.assertEqual(len(entries), 5)
        for _, target in entries:
            self.assertFalse(PurePosixPath(target).is_absolute())
            self.assertNotIn("\\", target)

    def test_maintained_product_bytes_are_unchanged(self) -> None:
        for relative, expected_hash in MAINTAINED_PRODUCT_HASHES.items():
            with self.subTest(path=relative):
                self.assertEqual(sha256(REPO_ROOT / relative), expected_hash)

    def test_package_and_archive_layout_authorities_remain_13_and_17_members(self) -> None:
        self.assertEqual(len(build_release.PACKAGE_FILE_PATHS), 13)
        self.assertEqual(len(release_archive.ARCHIVE_MEMBER_TEMPLATES), 17)
        self.assertEqual(
            release_archive.canonical_member_names("2099-01-02"),
            tuple(
                template.format(release_id="2099-01-02")
                for template in release_archive.ARCHIVE_MEMBER_TEMPLATES
            ),
        )


if __name__ == "__main__":
    unittest.main()
