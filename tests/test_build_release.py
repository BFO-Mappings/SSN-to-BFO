#!/usr/bin/env python3
"""Deterministic release-package build and read-only validation regressions."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rdflib import Graph, OWL, RDF, URIRef


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import build_release as build  # noqa: E402
import check_release as check  # noqa: E402
import release_manifest as release_manifest  # noqa: E402
from release_context import parse_formal_release_context  # noqa: E402
from release_manifest import load_and_validate_release_manifest  # noqa: E402


SYNTHETIC_CONTEXT = parse_formal_release_context(
    "2099-01-02",
    "2099-01-02",
    "v2099-01-02",
    "0123456789abcdef0123456789abcdef01234567",
)
FORMAL_HASHES = {
    "SSN2BFO.ttl": "fa076bfd3b4b279b14e66e52642d419bafce0c861aa51854f1dba18f39a163a4",
    "current-ssn-sosa/ssn-sosa-alignment-core.ttl": "c40ec6372eeb43d37fb7fc4775535574ac4a4ee1e218fbe6e840e35b0ba20716",
    "current-ssn-sosa/ssn-sosa-bfo-mapping.ttl": "68a91fc766a7ce8ace367d63d70b22f30adfdbb88a41cf9a622d2db956a69be9",
    "current-ssn-sosa/ssn-sosa-bfo-projection.ttl": "9c995fa0b6d8e3acfabbd495515fe36ffec58c4f353249ee9f3ee195c74b9673",
    "current-ssn-sosa/ssn-sosa-cco-extension.ttl": "960160a4d422a8391c29a2e4ff6c211e6047cdb9fa11cebdbf1497d14e3311f2",
}
NOTES_PATH = REPO_ROOT / "release-notes/SYNTHETIC-2099-01-02.md"


def synthetic_notes_text(suffix: str = "") -> str:
    sections = {
        "Release identity": "Synthetic identity 2099-01-02 is a deterministic release-engineering fixture. It is not an actual release announcement, tag, GitHub release, upload, or deployment.",
        "Included products": "This fixture exercises the repository's governed formal package inputs without selecting an actual release.",
        "Product selection guidance": "Consumers must use the governed product descriptions and policy rather than this synthetic fixture as release guidance.",
        "Governed axiom and closure summary": "The package builder records governed counts from the repository inputs deterministically.",
        "Import graph": "The formal package catalog records only the governed package-relative product graph.",
        "BFO projection notice": "The package preserves the governed import-only BFO projection policy.",
        "Validation summary": "The fixture is accepted by the real deterministic package builder and checker.",
        "Known limitations": "This fixture does not announce or authorize a real publication.",
        "Deferred functionality": "Actual release selection, publication, and deployment remain outside this fixture.",
        "License scope": "Repository license information is packaged from the governed project license.",
        "Dependencies": "Validation dependencies are recorded from stable repository configuration and are not redistributed by this fixture.",
        "Reproduction": "Use committed repository inputs and the explicit synthetic identity only for deterministic release-engineering regression coverage.",
    }
    return "\n\n".join(f"# {heading}\n\n{sections[heading]}{suffix}" for heading in build.REQUIRED_RELEASE_NOTE_HEADINGS) + "\n"


def notes_bytes(suffix: str = "") -> bytes:
    return synthetic_notes_text(suffix).encode("utf-8")


def notes_fixture_state(path: Path) -> tuple[int, int, bytes, int, str]:
    status = path.lstat()
    return (
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        path.read_bytes(),
        status.st_mtime_ns,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def hashes(root: Path) -> dict[str, str]:
    return {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in build.PACKAGE_FILE_PATHS
    }


def package_file_state(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path: ((root / path).read_bytes(), (root / path).stat().st_mtime_ns)
        for path in build.PACKAGE_FILE_PATHS
    }


class ReleasePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        status = NOTES_PATH.lstat()
        if not stat.S_ISREG(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise AssertionError("the committed synthetic release notes fixture must be a regular file")
        cls.notes_fixture_before = notes_fixture_state(NOTES_PATH)
        if NOTES_PATH.read_bytes() != notes_bytes():
            raise AssertionError("the committed synthetic release notes fixture differs from its governed regression content")
        cls.root = Path(tempfile.mkdtemp(prefix="release-package-tests-"))
        cls.package = cls.root / SYNTHETIC_CONTEXT.release_identifier
        cls.result = build.build_release_package(
            SYNTHETIC_CONTEXT,
            NOTES_PATH,
            cls.package,
            REPO_ROOT,
        )
        cls.manifest = load_and_validate_release_manifest(cls.package / "manifest.json")
        cls.baseline_hashes = hashes(cls.package)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.root, ignore_errors=True)
        if notes_fixture_state(NOTES_PATH) != cls.notes_fixture_before:
            raise AssertionError("package tests mutated the committed synthetic release notes fixture")

    def copy_package(self) -> tuple[Path, Path]:
        parent = Path(tempfile.mkdtemp(prefix="release-package-copy-"))
        destination = parent / SYNTHETIC_CONTEXT.release_identifier
        shutil.copytree(self.package, destination)
        self.addCleanup(shutil.rmtree, parent, True)
        return parent, destination

    def fast_build(self, context, notes: Path, output: Path, *, repository_root: Path = REPO_ROOT):
        with mock.patch.object(build, "run_independent_reasoning", return_value=self.manifest.validation.hermit_results), mock.patch.object(
            check, "validate_release_package", return_value=()
        ):
            return build.build_release_package(context, notes, output, repository_root)

    def rewrite_manifest_and_checksums(self, package: Path, mutate) -> None:
        document = json.loads((package / "manifest.json").read_bytes())
        mutate(document)
        (package / "manifest.json").write_bytes(
            release_manifest.canonical_manifest_bytes(document)
        )
        (package / "SHA256SUMS").write_bytes(
            build.canonical_sha256sums_bytes(package)
        )

    @staticmethod
    def update_included_evidence(package: Path, document: dict, relative: str) -> None:
        content = (package / relative).read_bytes()
        record = next(value for value in document["included_files"] if value["path"] == relative)
        record["sha256"] = hashlib.sha256(content).hexdigest()
        record["byte_size"] = len(content)

    def test_exact_package_layout_hashes_and_formal_counts(self) -> None:
        observed = tuple(
            path.relative_to(self.package).as_posix()
            for path in sorted(self.package.rglob("*"), key=lambda item: item.relative_to(self.package).as_posix())
            if path.is_file()
        )
        self.assertEqual(observed, build.PACKAGE_FILE_PATHS)
        self.assertEqual({path: self.baseline_hashes[path] for path in FORMAL_HASHES}, FORMAL_HASHES)
        self.assertEqual(
            [
                (
                    value.key,
                    value.ontology_declaration_count,
                    value.import_count,
                    value.static_metadata_count,
                    value.formal_metadata_count,
                    value.logical_triple_count,
                    value.total_triple_count,
                    value.direct_governed_axiom_count,
                    value.governed_closure_axiom_count,
                )
                for value in self.manifest.products
            ],
            [
                ("integrated", 1, 4, 7, 3, 1112, 1127, 105, 105),
                ("alignment_core", 1, 0, 7, 3, 53, 64, 29, 29),
                ("strict_bfo_mapping", 1, 1, 7, 3, 125, 137, 19, 48),
                ("bfo_projection", 1, 1, 7, 3, 0, 12, 0, 48),
                ("cco_extension", 1, 1, 7, 3, 934, 946, 57, 105),
            ],
        )

    def test_catalog_version_iris_and_checksum_anti_circularity(self) -> None:
        catalog = (self.package / "catalog-v001.xml").read_bytes()
        self.assertFalse(build.validate_catalog_bytes(catalog, build.publication.load_metadata(REPO_ROOT / "config/publication-metadata.toml"), SYNTHETIC_CONTEXT))
        lines = (self.package / "SHA256SUMS").read_text(encoding="ascii").splitlines()
        paths = [line[66:] for line in lines]
        self.assertEqual(tuple(paths), build.CHECKSUM_PATHS)
        self.assertIn("manifest.json", paths)
        self.assertNotIn("SHA256SUMS", paths)
        included = {value.path for value in self.manifest.included_files}
        self.assertNotIn("manifest.json", included)
        self.assertNotIn("SHA256SUMS", included)
        self.assertNotIn("manifest_sha256", (self.package / "manifest.json").read_text())

    def test_formal_products_parse_and_projection_is_import_only(self) -> None:
        for product in self.manifest.products:
            graph = Graph().parse(self.package / product.path, format="turtle")
            self.assertEqual(len(graph), product.total_triple_count)
        projection = Graph().parse(
            self.package / build.PRODUCT_PACKAGE_PATHS["bfo_projection"], format="turtle"
        )
        self.assertEqual(
            set(projection.objects(None, OWL.imports)),
            {URIRef(self.manifest.products[3].imports[0])},
        )
        self.assertEqual(self.manifest.products[3].direct_governed_axiom_count, 0)

    def test_manifest_records_exact_inputs_dependencies_environment_and_reasoning(self) -> None:
        expected_inputs = build.collect_inputs(
            REPO_ROOT,
            NOTES_PATH.relative_to(REPO_ROOT).as_posix(),
        )
        self.assertEqual(self.manifest.inputs, expected_inputs)
        self.assertEqual(self.manifest.dependencies, build.collect_dependencies(REPO_ROOT))
        toolchain = build.resolve_validation_toolchain(REPO_ROOT)
        self.assertEqual(
            self.manifest.validation_environment,
            build.collect_validation_environment(REPO_ROOT, toolchain),
        )
        self.assertEqual(self.manifest.validation_environment.java_vendor, toolchain.java_vendor)
        self.assertEqual(self.manifest.validation_environment.java_vm_name, toolchain.java_vm_name)
        self.assertEqual(
            self.manifest.validation_environment.robot_sha256,
            hashlib.sha256(toolchain.robot_jar.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            [(value.product_key, value.fixed_closure_triple_count, value.return_code, value.named_unsatisfiable_class_count) for value in self.manifest.validation.hermit_results],
            [
                (key, count, 0, 0)
                for key, count in release_manifest.FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS
            ],
        )
        self.assertTrue(all(value.reasoned_output_produced for value in self.manifest.validation.hermit_results))

    def test_dependencies_derive_from_generator_fixed_closure_authorities(self) -> None:
        expected_paths = (*build.coms.SOURCE_IMPORTS, build.coms.BFO_VALIDATION_DEPENDENCY)
        self.assertEqual(build.canonical_dependency_paths(), expected_paths)
        records = build.collect_dependencies(REPO_ROOT)
        self.assertEqual(tuple(Path(value.path) for value in records), expected_paths)
        self.assertEqual(len({value.path for value in records}), len(expected_paths))
        self.assertEqual(records[-1].key, "merged_cco_bfo")
        self.assertEqual(records[-1].role, "pinned merged CCO/BFO validation dependency")

    def test_resolved_toolchain_and_launcher_use_exact_verified_java_and_robot_jar(self) -> None:
        toolchain = build.resolve_validation_toolchain(REPO_ROOT)
        self.assertTrue(toolchain.java_vendor)
        self.assertTrue(toolchain.java_version.startswith("22"))
        self.assertTrue(toolchain.java_vm_name)
        self.assertEqual(
            toolchain.robot_jar_sha256,
            "91890c2e83d0f092dd08731376f154b36610544cfbe8685337a1bf7244ccaa2d",
        )
        with tempfile.TemporaryDirectory(prefix="verified-robot-launcher-") as directory:
            with build.verified_robot_launcher(toolchain, Path(directory)) as launcher:
                text = launcher.read_text(encoding="utf-8")
                self.assertIn(str(toolchain.java_executable), text)
                self.assertIn(str(toolchain.robot_jar), text)
                for option in build.OFFLINE_JAVA_OPTIONS:
                    self.assertIn(option, text)
                completed = subprocess.run(
                    [str(launcher), "--version"],
                    cwd=REPO_ROOT,
                    env=build.offline_subprocess_environment(),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                self.assertIn(
                    f"ROBOT version {toolchain.robot_version}",
                    completed.stdout + completed.stderr,
                )

    def test_every_java_robot_reasoning_subprocess_is_local_import_free_and_offline(self) -> None:
        toolchain = build.resolve_validation_toolchain(REPO_ROOT)
        original_run = subprocess.run
        observed: list[tuple[str, str]] = []

        def guarded_run(command, *args, **kwargs):
            if isinstance(command, list) and "reason" in command and "--input" in command:
                launcher = Path(command[0]).resolve()
                input_path = Path(command[command.index("--input") + 1]).resolve()
                self.assertTrue(launcher.is_file())
                self.assertTrue(input_path.is_file())
                launcher_text = launcher.read_text(encoding="utf-8")
                self.assertIn(str(toolchain.java_executable), launcher_text)
                self.assertIn(str(toolchain.robot_jar), launcher_text)
                for option in build.OFFLINE_JAVA_OPTIONS:
                    self.assertIn(option, launcher_text)
                for key in ("HTTP_PROXY", "HTTPS_PROXY", "FTP_PROXY", "ALL_PROXY"):
                    self.assertEqual(os.environ[key], "http://127.0.0.1:9")
                self.assertEqual(os.environ["NO_PROXY"], "")
                graph = Graph().parse(input_path, format="turtle")
                self.assertEqual(list(graph.triples((None, OWL.imports, None))), [])
                observed.append((str(launcher), str(input_path)))
            return original_run(command, *args, **kwargs)

        with tempfile.TemporaryDirectory(prefix="robot-offline-probe-") as directory:
            with mock.patch.object(build.coms.subprocess, "run", side_effect=guarded_run):
                results = build.run_independent_reasoning(
                    self.package,
                    Path(directory),
                    toolchain,
                )
        self.assertEqual(len(observed), 5)
        self.assertTrue(all(value.status == "PASS" for value in results))

    def test_release_notes_validation_boundaries(self) -> None:
        template = (REPO_ROOT / "release-notes/TEMPLATE.md").read_bytes()
        cases = {
            "empty": b"",
            "invalid UTF-8": b"\xff",
            "missing heading": notes_bytes().replace(b"# Dependencies", b"## Dependencies"),
            "CRLF": notes_bytes().replace(b"\n", b"\r\n"),
            "no newline": notes_bytes()[:-1],
            "extra newline": notes_bytes() + b"\n",
            "control": notes_bytes().replace(b"Synthetic", b"Synthetic\x00", 1),
            "template": template,
            "placeholder": notes_bytes(b" TODO"),
        }
        for name, value in cases.items():
            with self.subTest(case=name):
                self.assertTrue(build.validate_release_notes_bytes(value, template_bytes=template))
        self.assertFalse(build.validate_release_notes_bytes(notes_bytes(), template_bytes=template))

    def test_committed_synthetic_notes_fixture_is_read_only_and_accepted(self) -> None:
        status = NOTES_PATH.lstat()
        self.assertTrue(stat.S_ISREG(status.st_mode))
        self.assertFalse(stat.S_ISLNK(status.st_mode))
        self.assertEqual(notes_fixture_state(NOTES_PATH), self.notes_fixture_before)
        self.assertFalse(
            build.validate_release_notes_bytes(
                NOTES_PATH.read_bytes(),
                template_bytes=(REPO_ROOT / "release-notes/TEMPLATE.md").read_bytes(),
            )
        )
        self.assertTrue(
            build.validate_release_notes_bytes(
                (REPO_ROOT / "release-notes/TEMPLATE.md").read_bytes(),
                template_bytes=(REPO_ROOT / "release-notes/TEMPLATE.md").read_bytes(),
            )
        )

    def test_builder_rejects_every_notes_boundary_without_residue_or_mutation(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="release-build-note-failures-"))
        self.addCleanup(shutil.rmtree, parent, True)
        fixture_repository = parent / "repository"
        (fixture_repository / "release-notes").mkdir(parents=True)
        shutil.copy2(REPO_ROOT / "release-notes/TEMPLATE.md", fixture_repository / "release-notes/TEMPLATE.md")
        invalid_path = fixture_repository / "release-notes/INVALID-PACKAGE-NOTES.md"
        before = build.snapshot_development_outputs(REPO_ROOT)
        cases = (
            ("empty", invalid_path, b""),
            ("invalid-utf8", invalid_path, b"\xff"),
            (
                "missing-heading",
                invalid_path,
                notes_bytes().replace(b"# Dependencies", b"## Dependencies"),
            ),
            ("placeholder", invalid_path, notes_bytes(b" TODO")),
            ("crlf", invalid_path, notes_bytes().replace(b"\n", b"\r\n")),
            ("bare-cr", invalid_path, notes_bytes().replace(b"\n", b"\r", 1)),
            ("missing-newline", invalid_path, notes_bytes()[:-1]),
            ("extra-final-blank", invalid_path, notes_bytes() + b"\n"),
            (
                "template",
                fixture_repository / "release-notes/TEMPLATE.md",
                None,
            ),
            ("outside-repository", parent / "outside.md", notes_bytes()),
        )
        for name, notes, value in cases:
            with self.subTest(case=name):
                if value is not None:
                    notes.write_bytes(value)
                output_parent = parent / name
                output_parent.mkdir()
                output = output_parent / SYNTHETIC_CONTEXT.release_identifier
                with self.assertRaises(Exception):
                    build.build_release_package(
                        SYNTHETIC_CONTEXT,
                        notes,
                        output,
                        fixture_repository,
                    )
                self.assertFalse(output.exists())
                self.assertFalse(
                    any(
                        path.name.startswith(build.TEMP_PREFIX)
                        for path in output_parent.iterdir()
                    )
                )
                self.assertFalse(build.development_snapshot_issues(REPO_ROOT, before))
                self.assertEqual(notes_fixture_state(NOTES_PATH), self.notes_fixture_before)

    def test_builder_rejects_invalid_output_and_notes_paths_without_residue(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="release-build-paths-"))
        self.addCleanup(shutil.rmtree, parent, True)
        outside = parent / "notes.md"
        outside.write_bytes(notes_bytes())
        cases = (
            (NOTES_PATH, parent / "wrong-name"),
            (NOTES_PATH, parent / "missing" / "2099-01-02"),
            (outside, parent / "2099-01-02"),
            (REPO_ROOT / "release-notes/TEMPLATE.md", parent / "2099-01-02"),
        )
        for notes, output in cases:
            with self.subTest(notes=notes, output=output):
                with self.assertRaises(Exception):
                    build.build_release_package(SYNTHETIC_CONTEXT, notes, output, REPO_ROOT)
                self.assertFalse(output.exists())
        existing = parent / "2099-01-02"
        existing.mkdir()
        with self.assertRaises(build.ReleasePackageError):
            build.build_release_package(SYNTHETIC_CONTEXT, NOTES_PATH, existing, REPO_ROOT)
        with self.assertRaises(Exception):
            build.build_release_package(
                dataclasses.replace(SYNTHETIC_CONTEXT, source_commit="invalid"),
                NOTES_PATH,
                parent / "invalid" / "2099-01-02",
                REPO_ROOT,
            )

    def test_build_failures_clean_temporary_material_and_preserve_development(self) -> None:
        scenarios = (
            ("render", mock.patch.object(build, "render_formal_products", side_effect=RuntimeError("render failed"))),
            ("reasoning", mock.patch.object(build, "run_independent_reasoning", side_effect=RuntimeError("reasoning failed"))),
            ("catalog", mock.patch.object(build, "validate_catalog_bytes", return_value=(build.package_issue("CATALOG", "catalog", "failed"),))),
            ("manifest", mock.patch.object(build, "load_and_validate_release_manifest", side_effect=RuntimeError("manifest failed"))),
            ("checksums", mock.patch.object(build, "validate_sha256sums_bytes", return_value=(build.package_issue("SUMS", "sums", "failed"),))),
            ("publication", mock.patch.object(build.os, "replace", side_effect=OSError("rename failed"))),
            (
                "development mutation detection",
                mock.patch.object(
                    build,
                    "development_snapshot_issues",
                    return_value=(
                        build.package_issue(
                            "DEVELOPMENT_OUTPUT_MUTATED",
                            "SSN2BFO.ttl",
                            "simulated concurrent mutation",
                        ),
                    ),
                ),
            ),
        )
        before = build.snapshot_development_outputs(REPO_ROOT)
        actual_snapshot_issues = build.development_snapshot_issues
        for name, patcher in scenarios:
            with self.subTest(case=name), tempfile.TemporaryDirectory(prefix="release-build-failure-") as directory, patcher:
                output = Path(directory) / "2099-01-02"
                with self.assertRaises(Exception):
                    build.build_release_package(SYNTHETIC_CONTEXT, NOTES_PATH, output, REPO_ROOT)
                self.assertFalse(output.exists())
                self.assertFalse(any(path.name.startswith(build.TEMP_PREFIX) for path in Path(directory).iterdir()))
                self.assertFalse(actual_snapshot_issues(REPO_ROOT, before))

    def test_builder_compares_two_complete_candidates_before_publication(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="release-build-two-candidate-"))
        self.addCleanup(shutil.rmtree, parent, True)
        output = parent / SYNTHETIC_CONTEXT.release_identifier
        with mock.patch.object(
            build,
            "run_independent_reasoning",
            return_value=self.manifest.validation.hermit_results,
        ), mock.patch.object(
            check,
            "validate_release_package",
            return_value=(),
        ), mock.patch.object(
            build,
            "assemble_release_package",
            wraps=build.assemble_release_package,
        ) as assemble:
            build.build_release_package(
                SYNTHETIC_CONTEXT,
                NOTES_PATH,
                output,
                REPO_ROOT,
            )
        self.assertEqual(assemble.call_count, 2)
        self.assertFalse(build.compare_complete_packages(output, output))

    def test_builder_rejects_complete_package_rebuild_mismatch_with_unchanged_ttls(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="release-build-nondeterministic-"))
        self.addCleanup(shutil.rmtree, parent, True)
        output = parent / SYNTHETIC_CONTEXT.release_identifier
        original_copy = build._copy_package_inputs
        calls = 0

        def nondeterministic_copy(repository_root, notes, package_dir):
            nonlocal calls
            calls += 1
            original_copy(repository_root, notes, package_dir)
            if calls == 2:
                license_path = package_dir / "LICENSE"
                license_path.write_bytes(license_path.read_bytes() + b"nondeterministic\n")

        before = build.snapshot_development_outputs(REPO_ROOT)
        with mock.patch.object(
            build,
            "run_independent_reasoning",
            return_value=self.manifest.validation.hermit_results,
        ), mock.patch.object(build, "_copy_package_inputs", side_effect=nondeterministic_copy):
            with self.assertRaises(build.ReleasePackageError) as raised:
                build.build_release_package(
                    SYNTHETIC_CONTEXT,
                    NOTES_PATH,
                    output,
                    REPO_ROOT,
                )
        self.assertIn(
            "NONDETERMINISTIC_PACKAGE_REBUILD",
            {value.code for value in raised.exception.issues},
        )
        self.assertFalse(output.exists())
        self.assertFalse(any(path.name.startswith(build.TEMP_PREFIX) for path in parent.iterdir()))
        self.assertFalse(build.development_snapshot_issues(REPO_ROOT, before))

    def test_validator_independently_reconstructs_and_compares_all_thirteen_files(self) -> None:
        parent, package = self.copy_package()
        original_copy = build._copy_package_inputs

        def changed_reconstruction(repository_root, notes, package_dir):
            original_copy(repository_root, notes, package_dir)
            license_path = package_dir / "LICENSE"
            license_path.write_bytes(license_path.read_bytes() + b"reconstruction difference\n")

        before = {path: (package / path).read_bytes() for path in build.PACKAGE_FILE_PATHS}
        with mock.patch.object(
            build,
            "run_independent_reasoning",
            return_value=self.manifest.validation.hermit_results,
        ), mock.patch.object(build, "_copy_package_inputs", side_effect=changed_reconstruction):
            issues = check.validate_release_package(package, repository_root=REPO_ROOT)
        self.assertIn("NONDETERMINISTIC_PACKAGE_REBUILD", {value.code for value in issues})
        self.assertEqual(
            {path: (package / path).read_bytes() for path in build.PACKAGE_FILE_PATHS},
            before,
        )
        self.assertFalse(any(path.name.startswith("release-package-validation-") for path in parent.iterdir()))

    def test_valid_validator_preserves_all_package_bytes_and_mtimes(self) -> None:
        before = package_file_state(self.package)
        self.assertFalse(check.validate_release_package(self.package, repository_root=REPO_ROOT))
        self.assertEqual(package_file_state(self.package), before)

    def test_fixed_context_builds_to_different_parents_are_byte_identical(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="release-build-repeat-"))
        self.addCleanup(shutil.rmtree, parent, True)
        output = parent / "2099-01-02"
        self.fast_build(SYNTHETIC_CONTEXT, NOTES_PATH, output)
        self.assertEqual(hashes(output), self.baseline_hashes)

    def test_context_and_notes_changes_have_exact_byte_effects(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="release-build-changes-"))
        self.addCleanup(shutil.rmtree, parent, True)
        commit_context = dataclasses.replace(
            SYNTHETIC_CONTEXT,
            source_commit="1123456789abcdef0123456789abcdef01234567",
        )
        commit_output = parent / "commit" / "2099-01-02"
        commit_output.parent.mkdir()
        self.fast_build(commit_context, NOTES_PATH, commit_output)
        changed = {path for path in build.PACKAGE_FILE_PATHS if (commit_output / path).read_bytes() != (self.package / path).read_bytes()}
        self.assertEqual(changed, {"manifest.json", "SHA256SUMS"})

        alternate_repository = parent / "alternate-repository"
        shutil.copytree(
            REPO_ROOT,
            alternate_repository,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "*.pyo"),
        )
        alternate_notes = alternate_repository / "release-notes/SYNTHETIC-2099-01-02-ALTERNATE.md"
        alternate_notes.write_bytes(notes_bytes(" with alternate notes"))
        notes_output = parent / "notes" / "2099-01-02"
        notes_output.parent.mkdir()
        self.fast_build(SYNTHETIC_CONTEXT, alternate_notes, notes_output, repository_root=alternate_repository)
        changed = {path for path in build.PACKAGE_FILE_PATHS if (notes_output / path).read_bytes() != (self.package / path).read_bytes()}
        self.assertEqual(changed, {"RELEASE-NOTES.md", "manifest.json", "SHA256SUMS"})

        changed_context = parse_formal_release_context(
            "2099-01-03", "2099-01-03", "v2099-01-03", SYNTHETIC_CONTEXT.source_commit
        )
        date_output = parent / "date" / "2099-01-03"
        date_output.parent.mkdir()
        self.fast_build(changed_context, NOTES_PATH, date_output)
        for path in (*FORMAL_HASHES, "catalog-v001.xml", "manifest.json", "SHA256SUMS"):
            self.assertNotEqual((date_output / path).read_bytes(), (self.package / path).read_bytes())

    def test_validator_rejects_layout_symlink_and_byte_tampering_read_only(self) -> None:
        mutations = (
            ("missing", lambda root: (root / "LICENSE").unlink()),
            ("extra file", lambda root: (root / "extra.txt").write_text("extra")),
            ("extra directory", lambda root: (root / "extra").mkdir()),
            ("product", lambda root: (root / "SSN2BFO.ttl").write_bytes(b"not turtle\n")),
            ("workbook", lambda root: (root / "sources/SSN2BFO-COMS.xlsx").write_bytes(b"changed")),
            ("metadata", lambda root: (root / "sources/publication-metadata.toml").write_bytes(b"changed")),
            ("dispositions", lambda root: (root / "evidence/coms-product-dispositions.json").write_bytes(b"{}\n")),
            ("catalog", lambda root: (root / "catalog-v001.xml").write_bytes((root / "catalog-v001.xml").read_bytes().replace(b"integrated", b"stable", 1))),
            ("checksum", lambda root: (root / "SHA256SUMS").write_bytes((root / "SHA256SUMS").read_bytes().replace(b"  LICENSE", b" LICENSE", 1))),
        )
        for name, mutate in mutations:
            with self.subTest(case=name):
                _, package = self.copy_package()
                before = {path: (package / path).read_bytes() for path in build.PACKAGE_FILE_PATHS}
                mutate(package)
                after_mutation = {path: (package / path).read_bytes() for path in build.PACKAGE_FILE_PATHS if (package / path).exists()}
                self.assertTrue(check.validate_release_package(package, repository_root=REPO_ROOT))
                self.assertEqual(
                    {path: (package / path).read_bytes() for path in after_mutation},
                    after_mutation,
                )
        _, package = self.copy_package()
        target = package / "LICENSE"
        target.unlink()
        target.symlink_to(REPO_ROOT / "LICENSE")
        self.assertIn("PACKAGE_SYMLINK", {value.code for value in check.validate_release_package(package, repository_root=REPO_ROOT)})

    def test_validator_rejects_noncanonical_and_false_manifest_evidence(self) -> None:
        variants = []
        document = json.loads((self.package / "manifest.json").read_bytes())
        unknown = json.loads(json.dumps(document))
        unknown["unknown"] = True
        variants.append(unknown)
        reordered = json.loads(json.dumps(document))
        reordered["products"].reverse()
        variants.append(reordered)
        wrong_context = json.loads(json.dumps(document))
        wrong_context["source_commit"] = "0" * 40
        variants.append(wrong_context)
        wrong_hash = json.loads(json.dumps(document))
        wrong_hash["products"][0]["sha256"] = "0" * 64
        variants.append(wrong_hash)
        wrong_dependency = json.loads(json.dumps(document))
        wrong_dependency["dependencies"][0]["sha256"] = "0" * 64
        variants.append(wrong_dependency)
        wrong_validation = json.loads(json.dumps(document))
        wrong_validation["validation"]["catalog_validation"] = False
        variants.append(wrong_validation)
        for index, variant in enumerate(variants):
            with self.subTest(index=index):
                _, package = self.copy_package()
                (package / "manifest.json").write_bytes((json.dumps(variant, ensure_ascii=False, indent=2) + "\n").encode())
                self.assertTrue(check.validate_release_package(package, repository_root=REPO_ROOT))

    def test_validator_rejects_canonically_rehashed_semantic_mutations(self) -> None:
        def manifest_mutation(change):
            def mutate(package):
                self.rewrite_manifest_and_checksums(package, change)

            return mutate

        def changed_notes(package):
            notes = package / "RELEASE-NOTES.md"
            notes.write_bytes(notes.read_bytes().replace(b"Synthetic", b"Altered", 1))

            def update(document):
                content = notes.read_bytes()
                record = next(value for value in document["inputs"] if value["key"] == "release_notes")
                record["sha256"] = hashlib.sha256(content).hexdigest()
                record["byte_size"] = len(content)
                self.update_included_evidence(package, document, "RELEASE-NOTES.md")

            self.rewrite_manifest_and_checksums(package, update)

        def changed_catalog(package, *, canonical):
            catalog = package / "catalog-v001.xml"
            document = json.loads((package / "manifest.json").read_bytes())
            if canonical:
                old = document["products"][0]["version_iri"].encode()
                new = document["products"][0]["stable_ontology_iri"].encode()
                catalog.write_bytes(catalog.read_bytes().replace(old, new, 1))
            else:
                catalog.write_bytes(catalog.read_bytes().replace(b"  <uri", b"    <uri", 1))

            def update(value):
                self.update_included_evidence(package, value, "catalog-v001.xml")

            self.rewrite_manifest_and_checksums(package, update)

        def reordered_checksums(package):
            path = package / "SHA256SUMS"
            lines = path.read_bytes().splitlines()
            path.write_bytes(b"\n".join(reversed(lines)) + b"\n")

        def missing_checksum_newline(package):
            path = package / "SHA256SUMS"
            path.write_bytes(path.read_bytes()[:-1])

        cases = (
            (
                "wrong version IRI",
                manifest_mutation(
                    lambda value: value["products"][0].__setitem__(
                        "version_iri", "http://example.org/releases/2099-01-02/wrong"
                    )
                ),
                "PRODUCT_EVIDENCE_MISMATCH",
            ),
            (
                "wrong same-release import",
                manifest_mutation(
                    lambda value: value["products"][2].__setitem__(
                        "imports", ["http://example.org/releases/2099-01-02/wrong"]
                    )
                ),
                "PRODUCT_EVIDENCE_MISMATCH",
            ),
            ("changed notes", changed_notes, "INPUT_EVIDENCE_MISMATCH"),
            (
                "stable catalog mapping",
                lambda package: changed_catalog(package, canonical=True),
                "CATALOG_ENTRIES",
            ),
            (
                "noncanonical catalog",
                lambda package: changed_catalog(package, canonical=False),
                "NONCANONICAL_CATALOG",
            ),
            ("reordered checksums", reordered_checksums, "NONCANONICAL_CHECKSUMS"),
            (
                "missing checksum newline",
                missing_checksum_newline,
                "NONCANONICAL_CHECKSUMS",
            ),
            (
                "wrong direct count",
                manifest_mutation(
                    lambda value: value["products"][0].__setitem__(
                        "direct_governed_axiom_count",
                        value["products"][0]["direct_governed_axiom_count"] + 1,
                    )
                ),
                "PRODUCT_EVIDENCE_MISMATCH",
            ),
            (
                "wrong closure count",
                manifest_mutation(
                    lambda value: value["validation"]["hermit_results"][2].__setitem__(
                        "fixed_closure_triple_count", 999
                    )
                ),
                "FIXED_CLOSURE_TRIPLE_COUNT_MISMATCH",
            ),
            (
                "wrong product hash with canonical checksums",
                manifest_mutation(
                    lambda value: value["products"][0].__setitem__("sha256", "0" * 64)
                ),
                "PRODUCT_EVIDENCE_MISMATCH",
            ),
            (
                "local absolute path",
                manifest_mutation(
                    lambda value: value["inputs"][0].__setitem__(
                        "source_path", "/tmp/local-source.xlsx"
                    )
                ),
                "UNSAFE_PATH",
            ),
            (
                "trailing slash path",
                manifest_mutation(
                    lambda value: value["dependencies"][0].__setitem__("path", "imports/")
                ),
                "UNSAFE_PATH",
            ),
            (
                "sixth dependency",
                manifest_mutation(
                    lambda value: value["dependencies"].append(
                        {**value["dependencies"][0], "key": "extra"}
                    )
                ),
                "DEPENDENCY_ORDER",
            ),
            (
                "nonzero HermiT return",
                manifest_mutation(
                    lambda value: value["validation"]["hermit_results"][0].__setitem__(
                        "return_code", 1
                    )
                ),
                "HERMIT_RETURN_CODE",
            ),
            (
                "wrong dependency hash",
                manifest_mutation(
                    lambda value: value["dependencies"][0].__setitem__("sha256", "0" * 64)
                ),
                "DEPENDENCY_EVIDENCE_MISMATCH",
            ),
            (
                "wrong validation result",
                manifest_mutation(
                    lambda value: value["validation"].__setitem__("catalog_validation", False)
                ),
                "VALIDATION_OUTCOME",
            ),
        )
        for name, mutate, expected_code in cases:
            with self.subTest(case=name):
                _, package = self.copy_package()
                mutate(package)
                before = package_file_state(package)
                with mock.patch.object(
                    build,
                    "run_independent_reasoning",
                    side_effect=AssertionError("semantic mutation should fail before reconstruction"),
                ):
                    issues = check.validate_release_package(package, repository_root=REPO_ROOT)
                self.assertIn(expected_code, {value.code for value in issues})
                self.assertEqual(package_file_state(package), before)

    def test_valid_builder_and_checker_use_no_python_network_resolution(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="release-network-blocked-"))
        self.addCleanup(shutil.rmtree, parent, True)
        output = parent / SYNTHETIC_CONTEXT.release_identifier
        with mock.patch.object(socket, "create_connection", side_effect=AssertionError("network attempted")):
            build.build_release_package(
                SYNTHETIC_CONTEXT,
                NOTES_PATH,
                output,
                REPO_ROOT,
            )
            self.assertFalse(check.validate_release_package(output, repository_root=REPO_ROOT))

    def test_fresh_process_hash_seeds_are_byte_identical(self) -> None:
        parent = Path(tempfile.mkdtemp(prefix="release-seed-builds-"))
        self.addCleanup(shutil.rmtree, parent, True)
        observed: list[dict[str, str]] = []
        for seed in ("0", "1", "42", "random"):
            output = parent / seed / "2099-01-02"
            output.parent.mkdir()
            environment = os.environ.copy()
            environment.update({"PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"})
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "tools/build_release.py",
                    "--release-id", "2099-01-02",
                    "--release-date", "2099-01-02",
                    "--source-commit", SYNTHETIC_CONTEXT.source_commit,
                    "--git-tag", "v2099-01-02",
                    "--notes", str(NOTES_PATH),
                    "--output-dir", str(output),
                ],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            self.assertIn("Manifest SHA-256", completed.stdout)
            observed.append(hashes(output))
        self.assertTrue(all(value == self.baseline_hashes for value in observed))


if __name__ == "__main__":
    unittest.main()
