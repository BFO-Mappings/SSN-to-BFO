#!/usr/bin/env python3
"""Focused regressions for the separate SOSA-2023 release rehearsal."""

from __future__ import annotations

import ast
import hashlib
import inspect
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import rehearse_release as current  # noqa: E402
import sosa_2023_build_release as build  # noqa: E402
import sosa_2023_check_release as check  # noqa: E402
import sosa_2023_release_archive as archive  # noqa: E402
import sosa_2023_release_runtime as runtime  # noqa: E402
import sosa_2023_rehearse_release as rehearsal  # noqa: E402


RELEASE_ID = "2099-01-02"
NOTES = "release-notes/SOSA-2023-SYNTHETIC-2099-01-02.md"


def run_git(
    repository: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            *arguments,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if completed.returncode:
        raise AssertionError(
            completed.stderr.decode(
                "utf-8",
                errors="replace",
            )
        )

    return completed


class Sosa2023ReleaseRehearsalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(
            tempfile.mkdtemp(
                prefix="sosa-2023-rehearsal-tests-"
            )
        ).resolve()

        self.addCleanup(
            shutil.rmtree,
            self.root,
            True,
        )

        self.repository = (
            self.root
            / "repository"
        )
        self.repository.mkdir()

        notes = (
            self.repository
            / NOTES
        )
        notes.parent.mkdir(
            parents=True
        )
        notes.write_bytes(
            (
                REPO_ROOT
                / NOTES
            ).read_bytes()
        )

        (
            self.repository
            / "tracked.txt"
        ).write_text(
            "tracked\n",
            encoding="utf-8",
        )

        run_git(
            self.repository,
            "init",
            "-q",
        )
        run_git(
            self.repository,
            "add",
            ".",
        )

        environment = os.environ.copy()
        environment.update(
            {
                "GIT_AUTHOR_NAME": "Rehearsal Test",
                "GIT_AUTHOR_EMAIL": "rehearsal@example.invalid",
                "GIT_COMMITTER_NAME": "Rehearsal Test",
                "GIT_COMMITTER_EMAIL": "rehearsal@example.invalid",
                "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
                "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            }
        )

        subprocess.run(
            [
                "git",
                "-C",
                str(self.repository),
                "commit",
                "-q",
                "-m",
                "fixture",
            ],
            env=environment,
            check=True,
        )

        self.commit = (
            run_git(
                self.repository,
                "rev-parse",
                "HEAD",
            )
            .stdout
            .decode()
            .strip()
        )

    def fake_builder(
        self,
        observed: list[Path],
        *,
        change_second_archive: bool = False,
    ):
        def build_candidate(
            candidate_root,
            invoking_repository,
            source_commit,
            release_identifier,
            release_date,
            git_tag,
            notes_relative,
            expected_notes,
            guard_directory,
            verified_toolchain,
        ):
            observed.append(
                candidate_root
            )

            checkout = (
                candidate_root
                / "checkout"
            )
            checkout.mkdir()

            package = (
                candidate_root
                / "package"
                / release_identifier
            )
            package.mkdir(
                parents=True
            )

            artifacts = (
                candidate_root
                / "artifacts"
            )
            artifacts.mkdir()

            archive_bytes = b"same archive\n"

            if (
                change_second_archive
                and candidate_root.name == "candidate-b"
            ):
                archive_bytes = b"different archive\n"

            archive_path = (
                artifacts
                / archive.archive_filename(
                    release_identifier
                )
            )

            sidecar_path = (
                artifacts
                / archive.sidecar_filename(
                    release_identifier
                )
            )

            archive_path.write_bytes(
                archive_bytes
            )
            sidecar_path.write_bytes(
                b"same sidecar\n"
            )

            return rehearsal.CandidateResult(
                checkout=checkout,
                environment={},
                package_dir=package,
                archive_path=archive_path,
                sidecar_path=sidecar_path,
                manifest=types.SimpleNamespace(
                    source_commit=source_commit
                ),
                archive_sha256=hashlib.sha256(
                    archive_bytes
                ).hexdigest(),
            )

        return build_candidate

    def rehearse_with_fakes(
        self,
        *,
        command: str = "verify",
        output: Path | None = None,
        change_second_archive: bool = False,
        package_issues=(),
        stage_output=None,
    ):
        observed: list[Path] = []

        patches = [
            mock.patch.object(
                rehearsal,
                "_preflight_validation_toolchain",
                return_value=types.SimpleNamespace(),
            ),
            mock.patch.object(
                rehearsal,
                "_build_candidate",
                side_effect=self.fake_builder(
                    observed,
                    change_second_archive=change_second_archive,
                ),
            ),
            mock.patch.object(
                rehearsal,
                "compare_complete_packages",
                return_value=package_issues,
            ),
        ]

        if stage_output is not None:
            patches.append(
                mock.patch.object(
                    rehearsal,
                    "_stage_output",
                    side_effect=stage_output,
                )
            )

        for patcher in patches:
            patcher.start()

        try:
            result = rehearsal.rehearse_release(
                command,
                RELEASE_ID,
                RELEASE_ID,
                "v" + RELEASE_ID,
                self.commit,
                NOTES,
                output_dir=output,
                repository_root=self.repository,
            )
        finally:
            for patcher in reversed(patches):
                patcher.stop()

        return result, observed

    def test_current_rehearsal_authorities_remain_byte_locked(self) -> None:
        expected = {
            "tools/rehearse_release.py":
                "737f880da62c0b33de00877404469e98b0cc6634340bbd8bab0f128676d3263d",
            "tests/test_release_rehearsal.py":
                "f8c21ceabd0043e882f1cb217e8debf91e5c24b431d9ca0db55070cfc8e488fb",
        }

        for relative, digest in expected.items():
            with self.subTest(path=relative):
                self.assertEqual(
                    hashlib.sha256(
                        (
                            REPO_ROOT
                            / relative
                        ).read_bytes()
                    ).hexdigest(),
                    digest,
                )

    def test_all_nonbinding_definitions_match_current_rehearsal(self) -> None:
        intentionally_different = {
            "_build_candidate",
            "_validate_staged_output",
            "main",
        }

        current_source = inspect.getsource(current)
        current_tree = ast.parse(
            current_source
        )

        names = [
            node.name
            for node in current_tree.body
            if isinstance(
                node,
                (
                    ast.ClassDef,
                    ast.FunctionDef,
                ),
            )
        ]

        compared = 0

        for name in names:
            if name in intentionally_different:
                continue

            with self.subTest(definition=name):
                self.assertEqual(
                    inspect.getsource(
                        getattr(
                            rehearsal,
                            name,
                        )
                    ),
                    inspect.getsource(
                        getattr(
                            current,
                            name,
                        )
                    ),
                )
                compared += 1

        self.assertGreater(
            compared,
            30,
        )

    def test_track_bindings_are_exact_and_current_imports_are_absent(self) -> None:
        self.assertEqual(
            rehearsal.PACKAGE_FILE_PATHS,
            build.PACKAGE_FILE_PATHS,
        )

        self.assertEqual(
            rehearsal.EXPECTED_DIRECTORIES,
            check._expected_directories(),
        )

        self.assertEqual(
            len(rehearsal.PACKAGE_FILE_PATHS),
            13,
        )

        self.assertEqual(
            len(
                archive.canonical_member_names(
                    RELEASE_ID
                )
            ),
            16,
        )

        self.assertIs(
            rehearsal.resolve_validation_toolchain,
            runtime.resolve_validation_toolchain,
        )

        source = (
            REPO_ROOT
            / "tools/sosa_2023_rehearse_release.py"
        ).read_text(
            encoding="utf-8"
        )

        tree = ast.parse(source)

        imports = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                imports.extend(
                    alias.name
                    for alias in node.names
                )

            elif isinstance(node, ast.ImportFrom):
                imports.append(
                    node.module or ""
                )

        self.assertFalse(
            {
                "build_release",
                "check_release",
                "release_archive",
                "release_manifest",
                "rehearse_release",
            }.intersection(imports)
        )

    def test_candidate_and_staged_commands_use_only_sosa_tools(self) -> None:
        source = (
            inspect.getsource(
                rehearsal._build_candidate
            )
            + inspect.getsource(
                rehearsal._validate_staged_output
            )
        )

        self.assertIn(
            "tools/sosa_2023_build_release.py",
            source,
        )
        self.assertIn(
            "tools/sosa_2023_check_release.py",
            source,
        )
        self.assertIn(
            "tools/sosa_2023_release_archive.py",
            source,
        )

        self.assertNotIn(
            "tools/build_release.py",
            source,
        )
        self.assertNotIn(
            "tools/check_release.py",
            source,
        )
        self.assertNotIn(
            "tools/release_archive.py",
            source,
        )

        self.assertNotIn(
            '"tools/sosa_2023_check_release.py", "validate"',
            source,
        )

    def test_verify_uses_two_candidates_and_retains_no_output(self) -> None:
        result, observed = (
            self.rehearse_with_fakes()
        )

        self.assertEqual(
            result.source_commit,
            self.commit,
        )
        self.assertEqual(
            result.package_file_count,
            13,
        )
        self.assertEqual(
            result.archive_member_count,
            16,
        )
        self.assertIsNone(
            result.output_dir
        )

        self.assertEqual(
            {
                path.name
                for path in observed
            },
            {
                "candidate-a",
                "candidate-b",
            },
        )

        self.assertTrue(
            all(
                not path.exists()
                for path in observed
            )
        )

    def test_package_nondeterminism_blocks_rehearsal(self) -> None:
        issue = types.SimpleNamespace(
            code="NONDETERMINISTIC_PACKAGE_REBUILD",
            field="package",
            message="injected mismatch",
        )

        with self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse_with_fakes(
                package_issues=(
                    issue,
                )
            )

        self.assertIn(
            "NONDETERMINISTIC_PACKAGE_REBUILD",
            {
                value.code
                for value in raised.exception.issues
            },
        )

    def test_archive_nondeterminism_blocks_rehearsal(self) -> None:
        with self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            self.rehearse_with_fakes(
                change_second_archive=True
            )

        self.assertIn(
            "NONDETERMINISTIC_ARCHIVE_REBUILD",
            {
                value.code
                for value in raised.exception.issues
            },
        )

    def test_dirty_invoking_checkout_is_rejected_before_candidates(self) -> None:
        (
            self.repository
            / "untracked.txt"
        ).write_text(
            "dirty\n",
            encoding="utf-8",
        )

        observed: list[Path] = []

        with mock.patch.object(
            rehearsal,
            "_preflight_validation_toolchain",
            return_value=types.SimpleNamespace(),
        ), mock.patch.object(
            rehearsal,
            "_build_candidate",
            side_effect=self.fake_builder(
                observed
            ),
        ), self.assertRaises(
            rehearsal.ReleaseRehearsalError
        ) as raised:
            rehearsal.rehearse_release(
                "verify",
                RELEASE_ID,
                RELEASE_ID,
                "v" + RELEASE_ID,
                self.commit,
                NOTES,
                repository_root=self.repository,
            )

        self.assertIn(
            "DIRTY_INVOKING_CHECKOUT",
            {
                value.code
                for value in raised.exception.issues
            },
        )

        self.assertEqual(
            observed,
            [],
        )

    def test_build_publishes_only_after_candidate_equivalence(self) -> None:
        output = (
            self.root
            / "external-result"
        )

        def stage_output(
            candidate,
            output_dir,
            release_identifier,
            source_commit,
        ):
            staging = (
                output_dir.parent
                / ".release-rehearsal-output-fixture"
            )
            staging.mkdir()

            (
                staging
                / "sentinel.txt"
            ).write_text(
                "verified\n",
                encoding="utf-8",
            )

            return rehearsal._capture_owned_directory(
                staging,
                "staged_output",
            )

        result, observed = (
            self.rehearse_with_fakes(
                command="build",
                output=output,
                stage_output=stage_output,
            )
        )

        self.assertEqual(
            result.output_dir,
            output,
        )

        self.assertEqual(
            (
                output
                / "sentinel.txt"
            ).read_text(
                encoding="utf-8"
            ),
            "verified\n",
        )

        self.assertEqual(
            len(observed),
            2,
        )

        self.assertFalse(
            (
                self.root
                / ".release-rehearsal-output-fixture"
            ).exists()
        )

    def test_sitecustomize_network_guard_is_preserved_exactly(self) -> None:
        self.assertEqual(
            rehearsal.SITE_CUSTOMIZE,
            current.SITE_CUSTOMIZE,
        )

        self.assertIn(
            "socket.create_connection = _offline",
            rehearsal.SITE_CUSTOMIZE,
        )
        self.assertIn(
            "socket.getaddrinfo = _offline",
            rehearsal.SITE_CUSTOMIZE,
        )


if __name__ == "__main__":
    unittest.main()
