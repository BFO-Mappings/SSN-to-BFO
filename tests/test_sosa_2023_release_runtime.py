#!/usr/bin/env python3
"""Regression contract for the independent SOSA-2023 release runtime."""

from __future__ import annotations

import dataclasses
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import build_release as current  # noqa: E402
import sosa_2023_release_runtime as runtime  # noqa: E402


CURRENT_BUILD_HASH = (
    "3969aa59159dc5caf1c3f69b2ccef5ca9c9bd28d317b97dcb332e5a04fa2eb76"
)


def issue_signature(values):
    return tuple(
        (
            value.code,
            value.field,
            value.message,
        )
        for value in values
    )


class Sosa2023ReleaseRuntimeTests(unittest.TestCase):
    def test_release_note_policy_is_exactly_preserved(self) -> None:
        template = (
            REPO_ROOT
            / "release-notes/TEMPLATE.md"
        ).read_bytes()

        valid = (
            REPO_ROOT
            / "release-notes/SYNTHETIC-2099-01-02.md"
        ).read_bytes()

        cases = (
            valid,
            b"",
            b"\xff",
            valid.replace(b"\n", b"\r\n"),
            valid[:-1],
            valid + b"\n",
            valid.replace(b"Synthetic", b"Synthetic\x00", 1),
            template,
            valid.replace(b"Synthetic", b"Synthetic TODO", 1),
            valid.replace(b"# Dependencies", b"## Dependencies"),
        )

        for index, value in enumerate(cases):
            with self.subTest(index=index):
                self.assertEqual(
                    issue_signature(
                        runtime.validate_release_notes_bytes(
                            value,
                            template_bytes=template,
                        )
                    ),
                    issue_signature(
                        current.validate_release_notes_bytes(
                            value,
                            template_bytes=template,
                        )
                    ),
                )

    def test_required_release_note_headings_are_identical(self) -> None:
        self.assertEqual(
            runtime.REQUIRED_RELEASE_NOTE_HEADINGS,
            current.REQUIRED_RELEASE_NOTE_HEADINGS,
        )

    def test_offline_environment_is_identical(self) -> None:
        fixture = {
            "PATH": "/fixture/bin",
            "HTTP_PROXY": "http://example.invalid:1",
            "https_proxy": "http://example.invalid:2",
            "NO_PROXY": "localhost",
            "OTHER": "value",
        }

        self.assertEqual(
            runtime.offline_subprocess_environment(
                fixture
            ),
            current.offline_subprocess_environment(
                fixture
            ),
        )

    def test_resolved_toolchain_contract_matches_current_reference(self) -> None:
        expected = current.resolve_validation_toolchain(
            REPO_ROOT
        )
        observed = runtime.resolve_validation_toolchain(
            REPO_ROOT
        )

        expected_fields = {
            field.name
            for field in dataclasses.fields(expected)
        }

        observed_fields = {
            field.name
            for field in dataclasses.fields(observed)
        }

        self.assertEqual(
            observed_fields,
            expected_fields,
        )

        for field in sorted(expected_fields):
            with self.subTest(field=field):
                self.assertEqual(
                    getattr(observed, field),
                    getattr(expected, field),
                )

        self.assertEqual(
            observed.java_robot_command(),
            expected.java_robot_command(),
        )

    def test_verified_launcher_uses_same_governed_runtime(self) -> None:
        toolchain = runtime.resolve_validation_toolchain(
            REPO_ROOT
        )

        with tempfile.TemporaryDirectory(
            prefix="sosa-2023-release-runtime-"
        ) as directory:
            root = Path(directory)

            with runtime.verified_robot_launcher(
                toolchain,
                root,
            ) as launcher:
                text = launcher.read_text(
                    encoding="utf-8"
                )

                self.assertIn(
                    str(toolchain.java_executable),
                    text,
                )
                self.assertIn(
                    str(toolchain.robot_jar),
                    text,
                )

                for option in runtime.OFFLINE_JAVA_OPTIONS:
                    self.assertIn(
                        option,
                        text,
                    )

                completed = subprocess.run(
                    [
                        str(launcher),
                        "--version",
                    ],
                    cwd=REPO_ROOT,
                    env=runtime.offline_subprocess_environment(),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )

                self.assertIn(
                    f"ROBOT version {toolchain.robot_version}",
                    completed.stdout + completed.stderr,
                )

    def test_runtime_has_no_current_builder_or_manifest_dependency(self) -> None:
        text = (
            REPO_ROOT
            / "tools/sosa_2023_release_runtime.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn(
            "import build_release",
            text,
        )
        self.assertNotIn(
            "from build_release",
            text,
        )
        self.assertNotIn(
            "release_manifest",
            text,
        )

    def test_current_builder_remains_byte_locked(self) -> None:
        observed = hashlib.sha256(
            (
                REPO_ROOT
                / "tools/build_release.py"
            ).read_bytes()
        ).hexdigest()

        self.assertEqual(
            observed,
            CURRENT_BUILD_HASH,
        )


if __name__ == "__main__":
    unittest.main()
