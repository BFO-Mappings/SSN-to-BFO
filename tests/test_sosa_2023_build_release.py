#!/usr/bin/env python3
"""Regression coverage for deterministic SOSA-2023 release packaging."""

from __future__ import annotations

import hashlib
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import publication_metadata as publication  # noqa: E402
from release_context import parse_formal_release_context  # noqa: E402
import sosa_2023_build_release as build  # noqa: E402
import sosa_2023_check_release as check  # noqa: E402
import sosa_2023_release_manifest as manifest  # noqa: E402
import sosa_2023_release_runtime as runtime  # noqa: E402


SYNTHETIC_CONTEXT = parse_formal_release_context(
    "2099-01-02",
    "2099-01-02",
    "v2099-01-02",
    "0123456789abcdef0123456789abcdef01234567",
)

NOTES_PATH = (
    REPO_ROOT
    / "release-notes/SOSA-2023-SYNTHETIC-2099-01-02.md"
)

FORMAL_HASHES = {
    "integrated":
        "539c07541bf20e5305fa675fa34b54899fe2bd3be31cc33c865d367b3e7dbe43",
    "strict_bfo_mapping":
        "8eadb56c78b215fb7b623dede6071b6b412e2ed7eb2a85e694a372310a700125",
    "cco_extension":
        "d3b6f3324fa2b8931760c1d743e37984d1198a124abc7c7bdcf2195370428f3d",
    "ro_mapping":
        "faba756dc6480c2088cc6ad3e514524736130f90365f1ab7e40c3d909877ca69",
}

EXPECTED_CLOSURES = (
    ("integrated", 15243),
    ("strict_bfo_mapping", 15120),
    ("cco_extension", 15254),
    ("ro_mapping", 12864),
)

PACKAGE_ENGINE_INPUTS = (
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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def package_state(
    root: Path,
) -> dict[str, tuple[str, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            sha256_bytes(path.read_bytes()),
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in root.rglob("*")
        if path.is_file()
    }


def package_hashes(
    root: Path,
) -> dict[str, str]:
    return {
        relative: sha256_bytes(
            (root / relative).read_bytes()
        )
        for relative in build.PACKAGE_FILE_PATHS
    }


class Sosa2023ReleasePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        status = NOTES_PATH.lstat()

        if (
            not stat.S_ISREG(status.st_mode)
            or stat.S_ISLNK(status.st_mode)
        ):
            raise AssertionError(
                "synthetic SOSA-2023 notes fixture "
                "must be a regular file"
            )

        note_issues = runtime.validate_release_notes_bytes(
            NOTES_PATH.read_bytes(),
            template_bytes=(
                REPO_ROOT
                / "release-notes/TEMPLATE.md"
            ).read_bytes(),
        )

        if note_issues:
            raise AssertionError(
                "\n".join(
                    runtime.format_issue(issue)
                    for issue in note_issues
                )
            )

        cls.development_before = (
            build.snapshot_development_outputs(
                REPO_ROOT
            )
        )

        cls.root = Path(
            tempfile.mkdtemp(
                prefix="sosa-2023-release-package-tests-"
            )
        )

        cls.package = (
            cls.root
            / SYNTHETIC_CONTEXT.release_identifier
        )

        cls.result = build.build_release_package(
            SYNTHETIC_CONTEXT,
            NOTES_PATH,
            cls.package,
            REPO_ROOT,
        )

        cls.manifest = (
            manifest.load_and_validate_release_manifest(
                cls.package / "manifest.json"
            )
        )

        cls.baseline_state = package_state(
            cls.package
        )

        cls.baseline_hashes = package_hashes(
            cls.package
        )

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            issues = build.development_snapshot_issues(
                REPO_ROOT,
                cls.development_before,
            )

            if issues:
                raise AssertionError(
                    "\n".join(
                        runtime.format_issue(issue)
                        for issue in issues
                    )
                )
        finally:
            shutil.rmtree(
                cls.root,
                ignore_errors=True,
            )

    def copy_package(self) -> tuple[Path, Path]:
        parent = Path(
            tempfile.mkdtemp(
                prefix="sosa-2023-package-copy-"
            )
        )

        destination = (
            parent
            / SYNTHETIC_CONTEXT.release_identifier
        )

        shutil.copytree(
            self.package,
            destination,
        )

        self.addCleanup(
            shutil.rmtree,
            parent,
            True,
        )

        return parent, destination

    def fast_build(
        self,
        output: Path,
    ):
        with mock.patch.object(
            build,
            "run_independent_reasoning",
            return_value=(
                self.manifest.validation.hermit_results
            ),
        ), mock.patch.object(
            check,
            "validate_release_package",
            return_value=(),
        ):
            return build.build_release_package(
                SYNTHETIC_CONTEXT,
                NOTES_PATH,
                output,
                REPO_ROOT,
            )

    def test_exact_package_layout_and_authority_counts(
        self,
    ) -> None:
        observed = tuple(
            path.relative_to(
                self.package
            ).as_posix()
            for path in sorted(
                self.package.rglob("*"),
                key=lambda value: (
                    value.relative_to(
                        self.package
                    ).as_posix()
                ),
            )
            if path.is_file()
        )

        self.assertEqual(
            observed,
            build.PACKAGE_FILE_PATHS,
        )

        self.assertEqual(
            len(observed),
            17,
        )

        self.assertEqual(
            len(build.CHECKSUM_PATHS),
            16,
        )

        self.assertEqual(
            len(self.manifest.inputs),
            37,
        )

        self.assertEqual(
            len(self.manifest.dependencies),
            5,
        )

        self.assertEqual(
            len(self.manifest.included_files),
            15,
        )

        self.assertEqual(
            self.manifest.product_order,
            build.PRODUCT_ORDER,
        )

    def test_exact_formal_products_and_reasoning_evidence(
        self,
    ) -> None:
        self.assertEqual(
            {
                value.key: value.sha256
                for value in self.manifest.products
            },
            FORMAL_HASHES,
        )

        self.assertEqual(
            tuple(
                (
                    value.product_key,
                    value.fixed_closure_triple_count,
                )
                for value in (
                    self.manifest
                    .validation
                    .hermit_results
                )
            ),
            EXPECTED_CLOSURES,
        )

        for result in (
            self.manifest
            .validation
            .hermit_results
        ):
            with self.subTest(
                product=result.product_key
            ):
                self.assertEqual(
                    result.status,
                    "PASS",
                )

                self.assertEqual(
                    result.return_code,
                    0,
                )

                self.assertTrue(
                    result.reasoned_output_produced
                )

                self.assertEqual(
                    result.named_unsatisfiable_class_count,
                    0,
                )

                self.assertEqual(
                    result.owl_nothing_equivalent_named_class_count,
                    0,
                )

    def test_package_engine_modules_are_evidenced_not_packaged(
        self,
    ) -> None:
        records = {
            value.key: value
            for value in self.manifest.inputs
        }

        for key, source_path in PACKAGE_ENGINE_INPUTS:
            with self.subTest(input=key):
                record = records[key]

                self.assertEqual(
                    record.source_path,
                    source_path,
                )

                self.assertIsNone(
                    record.package_path,
                )

                content = (
                    REPO_ROOT
                    / source_path
                ).read_bytes()

                self.assertEqual(
                    record.sha256,
                    sha256_bytes(content),
                )

                self.assertEqual(
                    record.byte_size,
                    len(content),
                )

                self.assertNotIn(
                    source_path,
                    build.PACKAGE_FILE_PATHS,
                )

                self.assertNotIn(
                    source_path,
                    manifest.INCLUDED_FILE_PATH_ORDER,
                )

    def test_sampling_dependency_identity_is_distinct_from_formal_import(
        self,
    ) -> None:
        dependency = next(
            value
            for value in self.manifest.dependencies
            if value.key == "sosa_sampling"
        )

        integrated = next(
            value
            for value in self.manifest.products
            if value.key == "integrated"
        )

        self.assertEqual(
            dependency.ontology_iri,
            "http://www.w3.org/ns/sosa/sam/",
        )

        self.assertIn(
            "http://www.w3.org/ns/sosa/sampling/",
            integrated.imports,
        )

        self.assertNotIn(
            "http://www.w3.org/ns/sosa/sam/",
            integrated.imports,
        )

    def test_catalog_is_exact_and_formal_only(
        self,
    ) -> None:
        metadata = publication.load_metadata(
            (
                self.package
                / (
                    "sources/"
                    "sosa-2023-publication-metadata.toml"
                )
            ),
            product_order=build.PRODUCT_ORDER,
        )

        value = (
            self.package
            / "catalog-v001.xml"
        ).read_bytes()

        self.assertEqual(
            build.validate_catalog_bytes(
                value,
                metadata,
                SYNTHETIC_CONTEXT,
            ),
            (),
        )

        self.assertEqual(
            value,
            build.canonical_catalog_bytes(
                metadata,
                SYNTHETIC_CONTEXT,
            ),
        )

        self.assertEqual(
            value.count(b"<uri "),
            4,
        )

        self.assertNotIn(
            b"sosa-next",
            value,
        )

        self.assertNotIn(
            b"/development/",
            value,
        )

    def test_checksum_and_manifest_anti_circularity(
        self,
    ) -> None:
        lines = (
            self.package
            / "SHA256SUMS"
        ).read_text(
            encoding="ascii"
        ).splitlines()

        paths = tuple(
            line[66:]
            for line in lines
        )

        self.assertEqual(
            paths,
            build.CHECKSUM_PATHS,
        )

        self.assertEqual(
            len(paths),
            16,
        )

        self.assertIn(
            "manifest.json",
            paths,
        )

        self.assertNotIn(
            "SHA256SUMS",
            paths,
        )

        included = {
            value.path
            for value in self.manifest.included_files
        }

        self.assertNotIn(
            "manifest.json",
            included,
        )

        self.assertNotIn(
            "SHA256SUMS",
            included,
        )

        self.assertEqual(
            build.validate_sha256sums_bytes(
                self.package,
                (
                    self.package
                    / "SHA256SUMS"
                ).read_bytes(),
            ),
            (),
        )

    def test_checker_is_read_only_without_reconstruction(
        self,
    ) -> None:
        before = package_state(
            self.package
        )

        issues = check.validate_release_package(
            self.package,
            repository_root=REPO_ROOT,
            reconstruct=False,
        )

        self.assertEqual(
            issues,
            (),
        )

        self.assertEqual(
            package_state(
                self.package
            ),
            before,
        )

    def test_full_reconstruction_is_exact_and_read_only(
        self,
    ) -> None:
        before = package_state(
            self.package
        )

        issues = check.validate_release_package(
            self.package,
            repository_root=REPO_ROOT,
            reconstruct=True,
        )

        self.assertEqual(
            issues,
            (),
        )

        self.assertEqual(
            package_state(
                self.package
            ),
            before,
        )

    def test_fixed_context_rebuild_is_byte_identical(
        self,
    ) -> None:
        parent = Path(
            tempfile.mkdtemp(
                prefix="sosa-2023-repeat-build-"
            )
        )

        self.addCleanup(
            shutil.rmtree,
            parent,
            True,
        )

        output = (
            parent
            / SYNTHETIC_CONTEXT.release_identifier
        )

        self.fast_build(
            output
        )

        self.assertEqual(
            package_hashes(
                output
            ),
            self.baseline_hashes,
        )

    def test_checker_rejects_tampering_read_only(
        self,
    ) -> None:
        cases = (
            (
                "license",
                lambda root: (
                    root / "LICENSE"
                ).write_bytes(
                    (
                        root / "LICENSE"
                    ).read_bytes()
                    + b"tampered\n"
                ),
            ),
            (
                "catalog",
                lambda root: (
                    root / "catalog-v001.xml"
                ).write_bytes(
                    (
                        root / "catalog-v001.xml"
                    ).read_bytes().replace(
                        b"<uri ",
                        b"<uri  ",
                        1,
                    )
                ),
            ),
            (
                "workbook",
                lambda root: (
                    root
                    / (
                        "sources/"
                        "SOSA-2023-to-BFO-COMS.xlsx"
                    )
                ).write_bytes(
                    b"not an xlsx file"
                ),
            ),
            (
                "formal product",
                lambda root: (
                    root
                    / build.PRODUCT_PACKAGE_PATHS[
                        "integrated"
                    ]
                ).write_bytes(
                    b"not turtle\n"
                ),
            ),
            (
                "checksums",
                lambda root: (
                    root / "SHA256SUMS"
                ).write_bytes(
                    (
                        root / "SHA256SUMS"
                    ).read_bytes().replace(
                        b"  LICENSE",
                        b" LICENSE",
                        1,
                    )
                ),
            ),
        )

        for name, mutate in cases:
            with self.subTest(case=name):
                _, package = self.copy_package()

                mutate(
                    package
                )

                after_mutation = package_state(
                    package
                )

                issues = check.validate_release_package(
                    package,
                    repository_root=REPO_ROOT,
                    reconstruct=False,
                )

                self.assertTrue(
                    issues
                )

                self.assertEqual(
                    package_state(
                        package
                    ),
                    after_mutation,
                )

    def test_checker_rejects_package_symlink(
        self,
    ) -> None:
        _, package = self.copy_package()

        target = (
            package
            / "LICENSE"
        )

        target.unlink()

        target.symlink_to(
            REPO_ROOT / "LICENSE"
        )

        issues = check.validate_release_package(
            package,
            repository_root=REPO_ROOT,
            reconstruct=False,
        )

        self.assertIn(
            "PACKAGE_SYMLINK",
            {
                value.code
                for value in issues
            },
        )

    def test_builder_rejects_invalid_release_notes_without_residue(
        self,
    ) -> None:
        parent = Path(
            tempfile.mkdtemp(
                prefix="sosa-2023-invalid-notes-"
            )
        )

        self.addCleanup(
            shutil.rmtree,
            parent,
            True,
        )

        repository = (
            parent
            / "repository"
        )

        shutil.copytree(
            REPO_ROOT,
            repository,
            ignore=shutil.ignore_patterns(
                ".git",
                "__pycache__",
                "*.pyc",
                "*.pyo",
            ),
        )

        notes = (
            repository
            / "release-notes/INVALID.md"
        )

        notes.write_bytes(
            b"invalid\n"
        )

        output_parent = (
            parent
            / "output"
        )

        output_parent.mkdir()

        output = (
            output_parent
            / SYNTHETIC_CONTEXT.release_identifier
        )

        with self.assertRaises(
            runtime.ReleasePackageError
        ):
            build.build_release_package(
                SYNTHETIC_CONTEXT,
                notes,
                output,
                repository,
            )

        self.assertFalse(
            output.exists()
        )

        self.assertFalse(
            any(
                path.name.startswith(
                    build.TEMP_PREFIX
                )
                for path in output_parent.iterdir()
            )
        )

    def test_formal_package_identity_has_no_development_alias(
        self,
    ) -> None:
        rendered = "\n".join(
            text
            for product in self.manifest.products
            for text in (
                product.path,
                product.stable_ontology_iri,
                product.version_iri,
                *product.imports,
            )
        )

        self.assertNotIn(
            "sosa-next",
            rendered,
        )

        self.assertNotIn(
            "/development/",
            rendered,
        )

    def test_sosa_2023_package_engine_is_separate_from_current_engine(
        self,
    ) -> None:
        for relative in (
            "tools/sosa_2023_release_runtime.py",
            "tools/sosa_2023_build_release.py",
            "tools/sosa_2023_check_release.py",
        ):
            with self.subTest(module=relative):
                text = (
                    REPO_ROOT
                    / relative
                ).read_text(
                    encoding="utf-8"
                )

                self.assertNotIn(
                    "import build_release",
                    text,
                )

                self.assertNotIn(
                    "from build_release",
                    text,
                )

                self.assertNotIn(
                    "import check_release",
                    text,
                )

                self.assertNotIn(
                    "from check_release",
                    text,
                )

                self.assertNotIn(
                    "import release_manifest",
                    text,
                )

                self.assertNotIn(
                    "from release_manifest",
                    text,
                )


if __name__ == "__main__":
    unittest.main()
