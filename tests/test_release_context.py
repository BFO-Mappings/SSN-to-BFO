#!/usr/bin/env python3
"""Focused tests for explicit immutable formal-release context inputs."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import release_context as release  # noqa: E402


SYNTHETIC_VALUES = (
    "2099-01-02",
    "2099-01-02",
    "v2099-01-02",
    "0123456789abcdef0123456789abcdef01234567",
)


class FormalReleaseContextTests(unittest.TestCase):
    @staticmethod
    def codes(error: release.FormalReleaseContextError) -> tuple[str, ...]:
        return tuple(issue.code for issue in error.issues)

    def assert_invalid_identifier(
        self,
        value: object,
        code: str = "RELEASE_ID_FORMAT",
    ) -> None:
        with self.assertRaises(release.FormalReleaseContextError) as raised:
            release.validate_release_identifier(value)
        self.assertEqual(self.codes(raised.exception), (code,))

    def test_synthetic_context_is_valid_frozen_and_exact(self) -> None:
        context = release.parse_formal_release_context(*SYNTHETIC_VALUES)
        self.assertEqual(
            (
                context.release_identifier,
                context.release_date,
                context.git_tag,
                context.source_commit,
            ),
            SYNTHETIC_VALUES,
        )
        self.assertEqual(release.validate_formal_release_context(context), context)
        with self.assertRaises(FrozenInstanceError):
            context.release_identifier = "changed"  # type: ignore[misc]

    def test_expected_git_tag_uses_only_canonical_identifier(self) -> None:
        self.assertEqual(release.expected_git_tag("2099-01-02"), "v2099-01-02")
        with self.assertRaises(release.FormalReleaseContextError):
            release.expected_git_tag("v2099-01-02")

    def test_identifier_grammar_rejects_non_date_forms(self) -> None:
        values = (
            "2099-1-02",
            "2099-01-2",
            "v2099-01-02",
            "2099-01-02.1",
            "1.0.0",
            "2099-01-02T00:00:00",
            "2099-01-02Z",
            " 2099-01-02",
            "2099-01-02 ",
            "",
        )
        for value in values:
            with self.subTest(value=value):
                self.assert_invalid_identifier(value)

    def test_identifier_requires_real_gregorian_date(self) -> None:
        for value in ("2099-02-29", "2099-04-31", "0000-01-01"):
            with self.subTest(value=value):
                self.assert_invalid_identifier(value, "RELEASE_DATE_INVALID")
        self.assertEqual(
            release.validate_release_identifier("2100-02-28"),
            "2100-02-28",
        )

    def test_release_date_has_same_canonical_grammar(self) -> None:
        with self.assertRaises(release.FormalReleaseContextError) as raised:
            release.parse_formal_release_context(
                SYNTHETIC_VALUES[0],
                "2099-01-02T00:00:00Z",
                SYNTHETIC_VALUES[2],
                SYNTHETIC_VALUES[3],
            )
        self.assertEqual(self.codes(raised.exception), ("RELEASE_DATE_FORMAT",))

    def test_release_date_must_equal_identifier(self) -> None:
        with self.assertRaises(release.FormalReleaseContextError) as raised:
            release.parse_formal_release_context(
                "2099-01-02",
                "2099-01-03",
                "v2099-01-02",
                SYNTHETIC_VALUES[3],
            )
        self.assertEqual(self.codes(raised.exception), ("RELEASE_DATE_MISMATCH",))

    def test_git_tag_requires_exact_v_identifier(self) -> None:
        for value, code in (
            ("2099-01-02", "GIT_TAG_FORMAT"),
            ("V2099-01-02", "GIT_TAG_FORMAT"),
            ("v2099-01-03", "RELEASE_TAG_MISMATCH"),
            ("v2099-01-02.1", "GIT_TAG_FORMAT"),
            (" v2099-01-02", "GIT_TAG_FORMAT"),
        ):
            with self.subTest(value=value):
                with self.assertRaises(release.FormalReleaseContextError) as raised:
                    release.parse_formal_release_context(
                        SYNTHETIC_VALUES[0],
                        SYNTHETIC_VALUES[1],
                        value,
                        SYNTHETIC_VALUES[3],
                    )
                self.assertEqual(self.codes(raised.exception), (code,))

    def test_source_commit_requires_full_lowercase_hex(self) -> None:
        values = (
            "0" * 39,
            "0" * 41,
            "A" * 40,
            "g" * 40,
            "sha:" + "0" * 40,
            " " + "0" * 40,
            "0" * 40 + " ",
            "",
        )
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(release.FormalReleaseContextError) as raised:
                    release.parse_formal_release_context(
                        *SYNTHETIC_VALUES[:3],
                        value,
                    )
                self.assertEqual(self.codes(raised.exception), ("SOURCE_COMMIT_FORMAT",))

    def test_missing_fields_are_rejected_in_deterministic_order(self) -> None:
        with self.assertRaises(release.FormalReleaseContextError) as raised:
            release.parse_formal_release_context()
        self.assertEqual(
            tuple((issue.code, issue.field) for issue in raised.exception.issues),
            (
                ("RELEASE_ID_FORMAT", "release_identifier"),
                ("RELEASE_DATE_FORMAT", "release_date"),
                ("GIT_TAG_FORMAT", "git_tag"),
                ("SOURCE_COMMIT_FORMAT", "source_commit"),
            ),
        )

    def test_accumulated_issue_order_is_repeatable(self) -> None:
        expected = release.formal_release_context_issues(None, None, None, None)
        for _ in range(10):
            self.assertEqual(
                release.formal_release_context_issues(None, None, None, None),
                expected,
            )

    def test_context_type_is_required(self) -> None:
        with self.assertRaises(release.FormalReleaseContextError) as raised:
            release.validate_formal_release_context(SYNTHETIC_VALUES)
        self.assertEqual(self.codes(raised.exception), ("RELEASE_CONTEXT_TYPE",))

    def test_validation_does_not_require_a_git_repository(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="formal-context-no-git-") as directory:
            os.chdir(directory)
            try:
                context = release.parse_formal_release_context(*SYNTHETIC_VALUES)
            finally:
                os.chdir(previous)
        self.assertEqual(context.source_commit, SYNTHETIC_VALUES[3])


if __name__ == "__main__":
    unittest.main()
