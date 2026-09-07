#!/usr/bin/env python3
"""Focused tests for the immutable SOSA source-version authority."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_sosa_source_version as checker  # noqa: E402
import sosa_source_version as source_version  # noqa: E402


EXPECTED_COMMIT = "af425a0454ec00512a5ebfa2873fe35a077f5fda"
EXPECTED_IDENTITY = f"sosa-2023-{EXPECTED_COMMIT}"


class SosaSourceVersionTests(unittest.TestCase):
    def test_approved_identity_uses_full_upstream_commit(self) -> None:
        authority = source_version.load_source_version_authority()

        self.assertEqual(authority.schema_version, 1)
        self.assertEqual(authority.status, "approved")
        self.assertEqual(authority.source_identity, EXPECTED_IDENTITY)
        self.assertEqual(authority.development_alias, "sosa-next")
        self.assertEqual(authority.upstream_commit, EXPECTED_COMMIT)
        self.assertEqual(
            authority.upstream_repository,
            "https://github.com/w3c/sdw-sosa-ssn",
        )
        self.assertEqual(
            authority.edition_version_iri,
            "http://www.w3.org/ns/sosa/2023/",
        )
        self.assertEqual(len(authority.source_files), 8)

    def test_governed_source_bytes_and_metadata_match(self) -> None:
        summary = checker.run_check()

        self.assertTrue(summary["passed"])
        self.assertEqual(summary["source_identity"], EXPECTED_IDENTITY)
        self.assertEqual(summary["upstream_commit"], EXPECTED_COMMIT)
        self.assertEqual(summary["upstream_source_file_count"], 8)
        self.assertEqual(len(summary["source_sha256"]), 9)

    def test_abbreviated_commit_identity_is_rejected(self) -> None:
        original = source_version.CONFIG_PATH.read_text(
            encoding="utf-8"
        )
        altered = original.replace(
            EXPECTED_IDENTITY,
            "sosa-2023-af425a0",
            1,
        )
        self.assertNotEqual(original, altered)

        with tempfile.TemporaryDirectory(
            prefix="sosa-source-version-test-"
        ) as directory:
            config_path = Path(directory) / "source-version.toml"
            config_path.write_text(altered, encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "complete approved upstream commit",
            ):
                source_version.load_source_version_authority(
                    config_path
                )

    def test_wrong_source_digest_is_rejected(self) -> None:
        authority = source_version.load_source_version_authority()
        first = authority.source_files[0]

        bad_authority = source_version.SourceVersionAuthority(
            schema_version=authority.schema_version,
            status=authority.status,
            source_identity=authority.source_identity,
            development_alias=authority.development_alias,
            edition_label=authority.edition_label,
            edition_version_iri=authority.edition_version_iri,
            w3c_tr_iri=authority.w3c_tr_iri,
            upstream_repository=authority.upstream_repository,
            upstream_commit=authority.upstream_commit,
            upstream_commit_date=authority.upstream_commit_date,
            source_files=(
                source_version.SourceFile(
                    local_path=first.local_path,
                    upstream_path=first.upstream_path,
                    sha256="0" * 64,
                ),
                *authority.source_files[1:],
            ),
            overlay_path=authority.overlay_path,
            overlay_sha256=authority.overlay_sha256,
            overlay_bound_upstream_commit=(
                authority.overlay_bound_upstream_commit
            ),
            overlay_purpose=authority.overlay_purpose,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "SHA-256 mismatch",
        ):
            source_version.validate_source_version_files(
                bad_authority
            )


if __name__ == "__main__":
    unittest.main()
