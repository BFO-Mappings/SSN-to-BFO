#!/usr/bin/env python3
"""Canonical SOSA-2023 raw-USTAR release archive construction and validation regressions."""

from __future__ import annotations

import ast
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sosa_2023_release_archive as archive  # noqa: E402
import sosa_2023_build_release as build  # noqa: E402
from sosa_2023_build_release import PACKAGE_FILE_PATHS  # noqa: E402
from release_context import parse_formal_release_context  # noqa: E402


RELEASE_ID = "2099-01-02"
SOURCE_COMMIT = "0123456789abcdef0123456789abcdef01234567"
RECORD = archive.USTAR_RECORD_SIZE
TRACK_ID = archive.TRACK_ID
EXPECTED_MEMBERS = (
    "SOSA-2023-2099-01-02/",
    "SOSA-2023-2099-01-02/LICENSE",
    "SOSA-2023-2099-01-02/RELEASE-NOTES.md",
    "SOSA-2023-2099-01-02/SHA256SUMS",
    "SOSA-2023-2099-01-02/catalog-v001.xml",
    "SOSA-2023-2099-01-02/manifest.json",
    "SOSA-2023-2099-01-02/" + TRACK_ID + "/",
    "SOSA-2023-2099-01-02/"
    + TRACK_ID
    + "/sosa-bfo-mapping.ttl",
    "SOSA-2023-2099-01-02/"
    + TRACK_ID
    + "/sosa-cco-extension.ttl",
    "SOSA-2023-2099-01-02/"
    + TRACK_ID
    + "/sosa-integrated.ttl",
    "SOSA-2023-2099-01-02/"
    + TRACK_ID
    + "/sosa-ro-mapping.ttl",
    "SOSA-2023-2099-01-02/sources/",
    "SOSA-2023-2099-01-02/sources/SOSA-2023-to-BFO-COMS.xlsx",
    "SOSA-2023-2099-01-02/sources/SOSA-2023-to-RO-COMS.xlsx",
    "SOSA-2023-2099-01-02/sources/product-role-policy.toml",
    "SOSA-2023-2099-01-02/sources/sosa-2023-publication-metadata.toml",
    "SOSA-2023-2099-01-02/sources/sosa-2023-ro-product.toml",
    "SOSA-2023-2099-01-02/sources/sosa-2023-ro-source-version.toml",
    "SOSA-2023-2099-01-02/sources/sosa-release-scope.toml",
    "SOSA-2023-2099-01-02/sources/sosa-source-version.toml",
)


@dataclass(frozen=True)
class RawMember:
    name: str
    header_offset: int
    data_offset: int
    size: int
    padding: int
    end_offset: int


def create_package(parent: Path) -> Path:
    package = parent / RELEASE_ID
    package.mkdir(parents=True)
    for relative in PACKAGE_FILE_PATHS:
        path = package / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((f"fixture:{relative}\n").encode("utf-8"))
    return package


def raw_members(value: bytes) -> tuple[RawMember, ...]:
    result: list[RawMember] = []
    offset = 0
    while value[offset : offset + RECORD] != b"\0" * RECORD:
        header = value[offset : offset + RECORD]
        name = header[:100].split(b"\0", 1)[0].decode("ascii")
        size = int(header[124:135].decode("ascii"), 8)
        data_offset = offset + RECORD
        padding = (-size) % RECORD
        end_offset = data_offset + size + padding
        result.append(RawMember(name, offset, data_offset, size, padding, end_offset))
        offset = end_offset
    return tuple(result)


def repair_checksum(value: bytes, header_offset: int) -> bytes:
    result = bytearray(value)
    header = result[header_offset : header_offset + RECORD]
    header[148:156] = b" " * 8
    checksum = sum(header)
    header[148:156] = f"{checksum:06o}".encode("ascii") + b"\0 "
    result[header_offset : header_offset + RECORD] = header
    return bytes(result)


def mutate_header(value: bytes, member: RawMember, mutate, *, repair: bool = True) -> bytes:
    result = bytearray(value)
    header = result[member.header_offset : member.header_offset + RECORD]
    mutate(header)
    result[member.header_offset : member.header_offset + RECORD] = header
    changed = bytes(result)
    return repair_checksum(changed, member.header_offset) if repair else changed


def replace_name(header: bytearray, name: str) -> None:
    encoded = name.encode("ascii")
    header[:100] = b"\0" * 100
    header[: len(encoded)] = encoded


def write_archive_and_sidecar(test: unittest.TestCase, value: bytes) -> None:
    test.archive_path.write_bytes(value)
    test.sidecar_path.write_bytes(archive.canonical_sidecar_bytes(RELEASE_ID, value))


class ReleaseArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="release-archive-tests-")).resolve()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.package = create_package(self.root / "package-root")
        self.value = archive.canonical_archive_bytes(self.package, RELEASE_ID)
        self.archive_path = self.root / archive.archive_filename(RELEASE_ID)
        self.sidecar_path = self.root / archive.sidecar_filename(RELEASE_ID)
        write_archive_and_sidecar(self, self.value)

    def validate(self):
        with mock.patch.object(archive, "_package_validation_issues", return_value=()) as package_check, mock.patch.object(
            archive, "_manifest_commit_issue", return_value=()
        ) as commit_check:
            issues = archive.validate_release_archive(
                self.package,
                self.archive_path,
                self.sidecar_path,
                RELEASE_ID,
                SOURCE_COMMIT,
                repository_root=REPO_ROOT,
            )
        return issues, package_check, commit_check

    def assert_validation_code(self, value: bytes, code: str) -> None:
        write_archive_and_sidecar(self, value)
        issues, package_check, _ = self.validate()
        self.assertIn(code, {issue.code for issue in issues})
        package_check.assert_not_called()

    def assert_read_only_validation(self, value: bytes, expected_code: str | None = None) -> None:
        write_archive_and_sidecar(self, value)
        before = (
            self.archive_path.read_bytes(),
            self.archive_path.stat().st_mtime_ns,
            self.sidecar_path.read_bytes(),
            self.sidecar_path.stat().st_mtime_ns,
        )
        issues, _, _ = self.validate()
        if expected_code is None:
            self.assertFalse(issues)
        else:
            self.assertIn(expected_code, {issue.code for issue in issues})
        after = (
            self.archive_path.read_bytes(),
            self.archive_path.stat().st_mtime_ns,
            self.sidecar_path.read_bytes(),
            self.sidecar_path.stat().st_mtime_ns,
        )
        self.assertEqual(after, before)

    def test_member_authority_is_verbatim_and_independent_of_package_sorting(self) -> None:
        self.assertEqual(archive.ARCHIVE_MEMBER_TEMPLATES, tuple(name.replace(RELEASE_ID, "{release_id}") for name in EXPECTED_MEMBERS))
        self.assertEqual(archive.canonical_member_names(RELEASE_ID), EXPECTED_MEMBERS)
        self.assertEqual(len(EXPECTED_MEMBERS), 20)
        self.assertTrue(all(name.endswith("/") for name in (EXPECTED_MEMBERS[0], EXPECTED_MEMBERS[6], EXPECTED_MEMBERS[11])))
        self.assertEqual(archive.canonical_member_names(RELEASE_ID)[5], f"SOSA-2023-{RELEASE_ID}/manifest.json")

    def test_raw_ustar_stream_has_exact_headers_metadata_and_two_record_eof(self) -> None:
        members = raw_members(self.value)
        self.assertEqual(tuple(member.name for member in members), EXPECTED_MEMBERS)
        self.assertEqual(len(members), 20)
        self.assertEqual(len(self.value) % RECORD, 0)
        self.assertEqual(self.value[-2 * RECORD :], b"\0" * (2 * RECORD))
        self.assertNotEqual(self.value[-3 * RECORD : -2 * RECORD], b"\0" * RECORD)
        for member in members:
            with self.subTest(member=member.name):
                header = self.value[member.header_offset : member.data_offset]
                self.assertEqual(header[257:263], b"ustar\0")
                self.assertEqual(header[263:265], b"00")
                self.assertEqual(header[345:500], b"\0" * 155)
                self.assertEqual(header[500:512], b"\0" * 12)
                self.assertEqual(header[157:257], b"\0" * 100)
                self.assertEqual(header[265:329], b"\0" * 64)
                self.assertEqual(header[156:157], b"5" if member.name.endswith("/") else b"0")
                self.assertEqual(self.value[member.data_offset + member.size : member.end_offset], b"\0" * member.padding)

    def build_external_output(self, output: Path):
        with mock.patch.object(archive, "_package_validation_issues", return_value=()), mock.patch.object(
            archive, "_manifest_commit_issue", return_value=()
        ):
            return archive.build_release_archive(
                self.package,
                output,
                RELEASE_ID,
                SOURCE_COMMIT,
                repository_root=REPO_ROOT,
            )

    def test_builder_publishes_only_one_complete_no_replace_output_directory(self) -> None:
        parent = self.root / "external"
        parent.mkdir()
        output = parent / "archive-output"
        result = self.build_external_output(output)
        archive_path = output / archive.archive_filename(RELEASE_ID)
        sidecar_path = output / archive.sidecar_filename(RELEASE_ID)
        self.assertEqual(result.archive_sha256, hashlib.sha256(self.value).hexdigest())
        self.assertEqual({path.name for path in output.iterdir()}, {archive_path.name, sidecar_path.name})
        self.assertEqual(archive_path.read_bytes(), self.value)
        self.assertEqual(sidecar_path.read_bytes(), archive.canonical_sidecar_bytes(RELEASE_ID, self.value))
        self.assertFalse(any(path.name.startswith(".release-archive-output-") for path in parent.iterdir()))

    def test_external_builder_interruption_never_publishes_a_one_file_pair(self) -> None:
        parent = self.root / "external"
        parent.mkdir()
        original_write = Path.write_bytes

        def fail_only_candidate_sidecar(path: Path, value: bytes) -> int:
            if path.name == archive.sidecar_filename(RELEASE_ID) and path.parent.name.startswith(".release-archive-output-"):
                raise OSError("injected after archive construction")
            return original_write(path, value)

        scenarios = (
            ("after-archive-before-sidecar", mock.patch.object(Path, "write_bytes", new=fail_only_candidate_sidecar)),
            (
                "after-sidecar-before-validation",
                mock.patch.object(
                    archive,
                    "validate_release_archive",
                    return_value=(archive.archive_issue("ARCHIVE_BUILD_FAILED", "candidate", "injected validation boundary"),),
                ),
            ),
            ("after-validation-before-publication", mock.patch.object(archive, "atomic_rename_noreplace", side_effect=OSError("before directory publication"))),
        )
        for name, patcher in scenarios:
            with self.subTest(case=name), patcher, self.assertRaises(archive.ReleaseArchiveError):
                self.build_external_output(parent / name)
            self.assertFalse((parent / name).exists())
            self.assertFalse(any(path.name.startswith(".release-archive-output-") for path in parent.iterdir()))

    def test_directory_publication_race_and_postpublication_error_preserve_external_content(self) -> None:
        parent = self.root / "external"
        parent.mkdir()
        output = parent / "raced"
        original = archive.atomic_rename_noreplace

        def occupy_at_publication(source: Path, destination: Path) -> None:
            destination.mkdir()
            (destination / "sentinel").write_bytes(b"racing directory\n")
            original(source, destination)

        with mock.patch.object(archive, "atomic_rename_noreplace", side_effect=occupy_at_publication), self.assertRaises(
            archive.ReleaseArchiveError
        ) as raised:
            self.build_external_output(output)
        self.assertIn("OUTPUT_EXISTS", {issue.code for issue in raised.exception.issues})
        self.assertEqual((output / "sentinel").read_bytes(), b"racing directory\n")
        self.assertFalse(any(path.name.startswith(".release-archive-output-") for path in parent.iterdir()))

        published = parent / "published"

        def publish_then_raise(source: Path, destination: Path) -> None:
            original(source, destination)
            raise RuntimeError("injected after successful publication")

        with mock.patch.object(archive, "atomic_rename_noreplace", side_effect=publish_then_raise), self.assertRaises(
            archive.ReleaseArchiveError
        ) as raised:
            self.build_external_output(published)
        self.assertIn("ATOMIC_PUBLICATION_FAILED", {issue.code for issue in raised.exception.issues})
        self.assertEqual(
            {path.name for path in published.iterdir()},
            {archive.archive_filename(RELEASE_ID), archive.sidecar_filename(RELEASE_ID)},
        )
        self.assertFalse(any(path.name.startswith(".release-archive-output-") for path in parent.iterdir()))

    def test_builder_rejects_invalid_package_before_creating_any_output(self) -> None:
        parent = self.root / "invalid-parent"
        parent.mkdir()
        output = parent / "invalid-output"
        invalid = archive.archive_issue("PACKAGE_FILE_SET", "package", "injected invalid package")
        with mock.patch.object(archive, "_package_validation_issues", return_value=(invalid,)), mock.patch.object(
            archive, "_manifest_commit_issue", return_value=()
        ), self.assertRaises(archive.ReleaseArchiveError) as raised:
            archive.build_release_archive(
                self.package,
                output,
                RELEASE_ID,
                SOURCE_COMMIT,
                repository_root=REPO_ROOT,
            )
        self.assertIn("PACKAGE_FILE_SET", {issue.code for issue in raised.exception.issues})
        self.assertFalse(output.exists())
        self.assertFalse(any(parent.iterdir()))

    def test_archive_output_preflight_rejects_and_preserves_hidden_staging_siblings(self) -> None:
        parent = self.root / "external"
        parent.mkdir()
        sentinel_target = self.root / "sentinel-target"
        sentinel_target.mkdir()
        (sentinel_target / "sentinel").write_bytes(b"target\n")
        cases = (
            ("directory", lambda path: (path.mkdir(), (path / "sentinel").write_bytes(b"directory\n"))),
            ("file", lambda path: path.write_bytes(b"file\n")),
            ("symlink", lambda path: path.symlink_to(sentinel_target, target_is_directory=True)),
            ("multiple", lambda path: (path.mkdir(), (parent / ".release-archive-output-second").write_bytes(b"second\n"))),
        )
        for name, create in cases:
            with self.subTest(case=name):
                sibling = parent / ".release-archive-output-unrelated"
                create(sibling)
                before = {
                    path.name: (path.lstat().st_mode, path.readlink() if path.is_symlink() else path.read_bytes() if path.is_file() else None)
                    for path in parent.iterdir()
                }
                with self.assertRaises(archive.ReleaseArchiveError) as raised:
                    self.build_external_output(parent / f"output-{name}")
                self.assertIn("OUTPUT_EXISTS", {issue.code for issue in raised.exception.issues})
                after = {
                    path.name: (path.lstat().st_mode, path.readlink() if path.is_symlink() else path.read_bytes() if path.is_file() else None)
                    for path in parent.iterdir()
                }
                self.assertEqual(after, before)
                for path in list(parent.iterdir()):
                    if path.is_symlink() or path.is_file():
                        path.unlink()
                    else:
                        shutil.rmtree(path)

        ordinary = parent / "ordinary-sibling"
        ordinary.write_bytes(b"ordinary\n")
        output = parent / "accepted"
        self.build_external_output(output)
        self.assertEqual(ordinary.read_bytes(), b"ordinary\n")

    def test_owned_archive_staging_refuses_replacement_symlink_after_publication_error(self) -> None:
        parent = self.root / "external"
        parent.mkdir()
        output = parent / "published"
        replacement = self.root / "replacement"
        replacement.mkdir()
        (replacement / "sentinel").write_bytes(b"preserve me\n")
        original = archive.atomic_rename_noreplace

        def publish_replace_and_raise(source: Path, destination: Path) -> None:
            original(source, destination)
            shutil.rmtree(destination)
            destination.symlink_to(replacement, target_is_directory=True)
            raise RuntimeError("postpublication replacement")

        with mock.patch.object(archive, "atomic_rename_noreplace", side_effect=publish_replace_and_raise), self.assertRaises(
            archive.ReleaseArchiveError
        ) as raised:
            self.build_external_output(output)
        self.assertTrue({"ATOMIC_PUBLICATION_FAILED", "CLEANUP_FAILED"} <= {issue.code for issue in raised.exception.issues})
        self.assertTrue(output.is_symlink())
        self.assertEqual((replacement / "sentinel").read_bytes(), b"preserve me\n")

    def test_header_mutation_matrix_is_rejected_before_extraction(self) -> None:
        first = raw_members(self.value)[1]
        scenarios = (
            ("checksum", mutate_header(self.value, first, lambda header: header.__setitem__(100, ord("7")), repair=False), "ARCHIVE_METADATA_MISMATCH"),
            ("numeric", mutate_header(self.value, first, lambda header: header.__setitem__(107, ord(" "))), "ARCHIVE_METADATA_MISMATCH"),
            ("magic", mutate_header(self.value, first, lambda header: header.__setitem__(257, ord("X"))), "ARCHIVE_METADATA_MISMATCH"),
            ("version", mutate_header(self.value, first, lambda header: header.__setitem__(263, ord("9"))), "ARCHIVE_METADATA_MISMATCH"),
            ("unused", mutate_header(self.value, first, lambda header: header.__setitem__(500, 1)), "ARCHIVE_METADATA_MISMATCH"),
        )
        for name, changed, code in scenarios:
            with self.subTest(case=name):
                self.assert_validation_code(changed, code)

    def test_framing_mutation_matrix_rejects_noncanonical_eof_padding_and_concatenation(self) -> None:
        file_member = next(member for member in raw_members(self.value) if member.padding)
        padding = bytearray(self.value)
        padding[file_member.data_offset + file_member.size] = 1
        scenarios = (
            ("nonzero-padding", bytes(padding), "ARCHIVE_METADATA_MISMATCH"),
            ("missing-first-eof", self.value[:-2 * RECORD] + b"x" * RECORD + b"\0" * RECORD, "ARCHIVE_METADATA_MISMATCH"),
            ("missing-second-eof", self.value[:-RECORD], "ARCHIVE_METADATA_MISMATCH"),
            ("extra-zero-eof", self.value + b"\0" * RECORD, "ARCHIVE_METADATA_MISMATCH"),
            ("nonzero-trailing", self.value + b"x" * RECORD, "ARCHIVE_METADATA_MISMATCH"),
            ("concatenated", self.value + self.value, "ARCHIVE_METADATA_MISMATCH"),
            ("truncated-header", self.value[:-1], "ARCHIVE_PARSE_FAILED"),
        )
        final_file = raw_members(self.value)[-1]
        truncated_body = mutate_header(
            self.value,
            final_file,
            lambda header: header.__setitem__(slice(124, 136), archive._octal_field(final_file.size + 4096, 12)),
        )
        scenarios += (("truncated-body", truncated_body, "ARCHIVE_PARSE_FAILED"),)
        for name, changed, code in scenarios:
            with self.subTest(case=name):
                self.assert_validation_code(changed, code)

    def test_member_order_duplicate_type_and_unsafe_path_mutations_are_rejected(self) -> None:
        members = raw_members(self.value)
        duplicate = mutate_header(self.value, members[1], lambda header: replace_name(header, members[0].name))
        unsafe = mutate_header(self.value, members[1], lambda header: replace_name(header, "../escape"))
        first_record = self.value[members[0].header_offset : members[0].end_offset]
        second_record = self.value[members[1].header_offset : members[1].end_offset]
        reordered = second_record + first_record + self.value[members[1].end_offset :]
        extra_header = archive._canonical_header(f"SOSA-2023-{RELEASE_ID}/extra", is_directory=False, size=1)
        extra = self.value[:-2 * RECORD] + extra_header + b"x" + b"\0" * (RECORD - 1) + b"\0" * (2 * RECORD)
        scenarios = (
            ("duplicate", duplicate, "DUPLICATE_ARCHIVE_MEMBER"),
            ("unsafe", unsafe, "UNSAFE_ARCHIVE_MEMBER"),
            ("reordered", reordered, "ARCHIVE_MEMBER_ORDER"),
            ("extra", extra, "ARCHIVE_MEMBER_ORDER"),
        )
        for name, changed, code in scenarios:
            with self.subTest(case=name):
                self.assert_validation_code(changed, code)
        for type_flag in (b"1", b"2", b"3", b"4", b"6", b"7", b"g", b"x", b"L", b"K"):
            with self.subTest(type_flag=type_flag):
                special = mutate_header(
                    self.value,
                    members[1],
                    lambda header, selected=type_flag: header.__setitem__(156, selected[0]),
                )
                self.assert_validation_code(special, "ARCHIVE_MEMBER_TYPE")

    def test_content_and_metadata_mismatches_are_rejected_after_raw_validation(self) -> None:
        file_member = next(member for member in raw_members(self.value) if not member.name.endswith("/"))
        changed_content = bytearray(self.value)
        changed_content[file_member.data_offset] ^= 1
        self.assert_validation_code(bytes(changed_content), "ARCHIVE_CONTENT_MISMATCH")

        changed_mode = mutate_header(
            self.value,
            file_member,
            lambda header: header.__setitem__(slice(100, 108), archive._octal_field(0o600, 8)),
        )
        self.assert_validation_code(changed_mode, "ARCHIVE_METADATA_MISMATCH")

    def test_sidecar_grammar_matrix_is_exact(self) -> None:
        digest = hashlib.sha256(self.value).hexdigest()
        filename = archive.archive_filename(RELEASE_ID)
        values = (
            ("uppercase", f"{digest.upper()}  {filename}\n".encode("ascii")),
            ("wrong-digest", b"0" * 64 + f"  {filename}\n".encode("ascii")),
            ("wrong-filename", f"{digest}  wrong.tar\n".encode("ascii")),
            ("qualified-filename", f"{digest}  nested/{filename}\n".encode("ascii")),
            ("one-space", f"{digest} {filename}\n".encode("ascii")),
            ("three-spaces", f"{digest}   {filename}\n".encode("ascii")),
            ("tab", f"{digest}\t{filename}\n".encode("ascii")),
            ("crlf", f"{digest}  {filename}\r\n".encode("ascii")),
            ("missing-lf", f"{digest}  {filename}".encode("ascii")),
            ("two-lfs", f"{digest}  {filename}\n\n".encode("ascii")),
            ("leading-blank", b"\n" + f"{digest}  {filename}\n".encode("ascii")),
            ("trailing-blank", f"{digest}  {filename}\n\n".encode("ascii")),
            ("second-entry", f"{digest}  {filename}\n{digest}  {filename}\n".encode("ascii")),
            ("non-ascii", f"{digest}  {filename}\n".encode("ascii") + b"\xff"),
        )
        for name, value in values:
            with self.subTest(case=name):
                self.sidecar_path.write_bytes(value)
                issues, package_check, _ = self.validate()
                self.assertIn("ARCHIVE_CHECKSUM_MISMATCH", {issue.code for issue in issues})
                package_check.assert_not_called()

    def test_validator_is_read_only_for_valid_and_failure_paths(self) -> None:
        self.assert_read_only_validation(self.value)
        self.assert_read_only_validation(self.value + b"\0" * RECORD, "ARCHIVE_METADATA_MISMATCH")
        unsafe = mutate_header(self.value, raw_members(self.value)[1], lambda header: replace_name(header, "../escape"))
        self.assert_read_only_validation(unsafe, "UNSAFE_ARCHIVE_MEMBER")
        metadata = mutate_header(
            self.value,
            raw_members(self.value)[1],
            lambda header: header.__setitem__(slice(100, 108), archive._octal_field(0o600, 8)),
        )
        self.assert_read_only_validation(metadata, "ARCHIVE_METADATA_MISMATCH")
        content = bytearray(self.value)
        member = raw_members(self.value)[1]
        content[member.data_offset] ^= 1
        self.assert_read_only_validation(bytes(content), "ARCHIVE_CONTENT_MISMATCH")
        self.sidecar_path.write_bytes(b"invalid sidecar\n")
        before = (
            self.archive_path.read_bytes(),
            self.archive_path.stat().st_mtime_ns,
            self.sidecar_path.read_bytes(),
            self.sidecar_path.stat().st_mtime_ns,
        )
        issues, _, _ = self.validate()
        self.assertIn("ARCHIVE_CHECKSUM_MISMATCH", {issue.code for issue in issues})
        self.assertEqual(
            (
                self.archive_path.read_bytes(),
                self.archive_path.stat().st_mtime_ns,
                self.sidecar_path.read_bytes(),
                self.sidecar_path.stat().st_mtime_ns,
            ),
            before,
        )

    def test_validator_preserves_primary_and_extraction_cleanup_diagnostics(self) -> None:
        changed = bytearray(self.value)
        member = raw_members(self.value)[1]
        changed[member.data_offset] ^= 1
        write_archive_and_sidecar(self, bytes(changed))
        original = archive._cleanup_owned_directory

        def cleanup_with_issue(path: Path | None, field: str):
            original(path, field)
            return (archive.archive_issue("CLEANUP_FAILED", field, "injected cleanup failure"),)

        with mock.patch.object(archive, "_package_validation_issues", return_value=()), mock.patch.object(
            archive, "_manifest_commit_issue", return_value=()
        ), mock.patch.object(archive, "_cleanup_owned_directory", side_effect=cleanup_with_issue):
            issues = archive.validate_release_archive(
                self.package,
                self.archive_path,
                self.sidecar_path,
                RELEASE_ID,
                SOURCE_COMMIT,
                repository_root=REPO_ROOT,
            )
        self.assertTrue({"ARCHIVE_CONTENT_MISMATCH", "CLEANUP_FAILED"} <= {issue.code for issue in issues})

    def test_fresh_process_determinism_survives_hash_seed_locale_timezone_umask_and_source_metadata(self) -> None:
        script = '''
import os
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from sosa_2023_build_release import PACKAGE_FILE_PATHS
from sosa_2023_release_archive import canonical_archive_bytes, canonical_sidecar_bytes
root = Path(sys.argv[1])
variation = int(sys.argv[4])
package = root / "2099-01-02"
package.mkdir(parents=True)
for index, relative in enumerate(PACKAGE_FILE_PATHS):
    path = package / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("fixture:" + relative + "\\n").encode("utf-8"))
    os.chmod(path, 0o600 if (index + variation) % 2 else 0o644)
    os.utime(path, ns=(index + variation + 1, index + variation + 2))
os.umask(int(sys.argv[3], 8))
value = canonical_archive_bytes(package, "2099-01-02")
sys.stdout.buffer.write(value + canonical_sidecar_bytes("2099-01-02", value))
'''
        settings = (
            ("0", "UTC", "C", "022"),
            ("1", "America/New_York", "C.UTF-8", "077"),
            ("42", "UTC", "C", "002"),
            ("random", "America/Los_Angeles", "C.UTF-8", "027"),
        )
        outputs: list[bytes] = []
        for index, (seed, timezone, locale, mask) in enumerate(settings):
            with self.subTest(seed=seed, timezone=timezone, locale=locale, umask=mask):
                root = self.root / f"fresh-process-{index}"
                environment = os.environ.copy()
                environment.update(
                    {
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONHASHSEED": seed,
                        "TZ": timezone,
                        "LC_ALL": locale,
                        "LANG": locale,
                    }
                )
                completed = subprocess.run(
                    [sys.executable, "-B", "-c", script, str(root), str(REPO_ROOT / "tools"), mask, str(index)],
                    env=environment,
                    cwd=self.root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
                outputs.append(completed.stdout)
        self.assertEqual(len(set(outputs)), 1)

    def test_output_filename_and_sidecar_bytes_are_exact(self) -> None:
        self.assertEqual(archive.archive_filename(RELEASE_ID), "SSN2BFO-sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda-2099-01-02.tar")
        self.assertEqual(archive.sidecar_filename(RELEASE_ID), "SSN2BFO-sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda-2099-01-02.tar.sha256")
        digest = hashlib.sha256(self.value).hexdigest()
        self.assertEqual(
            archive.canonical_sidecar_bytes(RELEASE_ID, self.value),
            f"{digest}  SSN2BFO-sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda-2099-01-02.tar\n".encode("ascii"),
        )


class Sosa2023RealPackageArchiveIntegrationTests(unittest.TestCase):
    def test_real_package_build_archives_twice_exactly_and_validates_read_only(
        self,
    ) -> None:
        context = parse_formal_release_context(
            "2099-01-02",
            "2099-01-02",
            "v2099-01-02",
            "0123456789abcdef0123456789abcdef01234567",
        )

        notes = (
            REPO_ROOT
            / "release-notes/SOSA-2023-SYNTHETIC-2099-01-02.md"
        )

        development_before = (
            build.snapshot_development_outputs(
                REPO_ROOT
            )
        )

        root = Path(
            tempfile.mkdtemp(
                prefix="sosa-2023-real-archive-integration-"
            )
        ).resolve()

        self.addCleanup(
            shutil.rmtree,
            root,
            True,
        )

        package = (
            root
            / "package"
            / context.release_identifier
        )

        package.parent.mkdir()

        result = build.build_release_package(
            context,
            notes,
            package,
            REPO_ROOT,
        )

        self.assertEqual(
            result.manifest.source_commit,
            context.source_commit,
        )

        def package_state():
            return {
                file_path.relative_to(
                    package
                ).as_posix(): (
                    hashlib.sha256(
                        file_path.read_bytes()
                    ).hexdigest(),
                    file_path.stat().st_size,
                    file_path.stat().st_mtime_ns,
                )
                for file_path in package.rglob("*")
                if file_path.is_file()
            }

        baseline = package_state()

        self.assertEqual(
            set(baseline),
            set(PACKAGE_FILE_PATHS),
        )

        first_parent = root / "first"
        second_parent = root / "second"

        first_parent.mkdir()
        second_parent.mkdir()

        first = archive.build_release_archive(
            package,
            first_parent / "published",
            context.release_identifier,
            context.source_commit,
            repository_root=REPO_ROOT,
        )

        self.assertEqual(
            package_state(),
            baseline,
        )

        second = archive.build_release_archive(
            package,
            second_parent / "published",
            context.release_identifier,
            context.source_commit,
            repository_root=REPO_ROOT,
        )

        self.assertEqual(
            package_state(),
            baseline,
        )

        first_bytes = first.archive_path.read_bytes()
        second_bytes = second.archive_path.read_bytes()

        first_sidecar = first.sidecar_path.read_bytes()
        second_sidecar = second.sidecar_path.read_bytes()

        self.assertEqual(
            first_bytes,
            second_bytes,
        )

        self.assertEqual(
            first_sidecar,
            second_sidecar,
        )

        self.assertEqual(
            len(first_sidecar),
            140,
        )

        self.assertEqual(
            hashlib.sha256(
                first_bytes
            ).hexdigest(),
            first.archive_sha256,
        )

        self.assertEqual(
            second.archive_sha256,
            first.archive_sha256,
        )

        self.assertEqual(
            first.member_names,
            archive.canonical_member_names(
                context.release_identifier
            ),
        )

        self.assertEqual(
            len(first.member_names),
            20,
        )

        self.assertFalse(
            any(
                "sosa-next" in member
                for member in first.member_names
            )
        )

        self.assertTrue(
            any(
                archive.TRACK_ID in member
                for member in first.member_names
            )
        )

        self.assertEqual(
            first_sidecar,
            archive.canonical_sidecar_bytes(
                context.release_identifier,
                first_bytes,
            ),
        )

        archive_state_before = (
            first.archive_path.read_bytes(),
            first.archive_path.stat().st_size,
            first.archive_path.stat().st_mtime_ns,
            first.sidecar_path.read_bytes(),
            first.sidecar_path.stat().st_size,
            first.sidecar_path.stat().st_mtime_ns,
        )

        issues = archive.validate_release_archive(
            package,
            first.archive_path,
            first.sidecar_path,
            context.release_identifier,
            context.source_commit,
            repository_root=REPO_ROOT,
        )

        self.assertEqual(
            issues,
            (),
        )

        archive_state_after = (
            first.archive_path.read_bytes(),
            first.archive_path.stat().st_size,
            first.archive_path.stat().st_mtime_ns,
            first.sidecar_path.read_bytes(),
            first.sidecar_path.stat().st_size,
            first.sidecar_path.stat().st_mtime_ns,
        )

        self.assertEqual(
            archive_state_after,
            archive_state_before,
        )

        self.assertEqual(
            package_state(),
            baseline,
        )

        members = archive._parse_raw_archive(
            first_bytes,
            context.release_identifier,
        )

        self.assertEqual(
            len(members),
            20,
        )

        self.assertEqual(
            len(first_bytes)
            % archive.USTAR_RECORD_SIZE,
            0,
        )

        self.assertEqual(
            first_bytes[
                -2
                * archive.USTAR_RECORD_SIZE:
            ],
            b"\0"
            * (
                2
                * archive.USTAR_RECORD_SIZE
            ),
        )

        self.assertLessEqual(
            max(
                len(
                    member.encode(
                        "ascii"
                    )
                )
                for member in first.member_names
            ),
            100,
        )

        self.assertEqual(
            build.development_snapshot_issues(
                REPO_ROOT,
                development_before,
            ),
            (),
        )


class Sosa2023ArchiveAuthorityContractTests(unittest.TestCase):
    def test_archive_identity_is_track_disambiguated(self) -> None:
        self.assertEqual(
            archive.archive_filename(RELEASE_ID),
            "SSN2BFO-" + TRACK_ID + "-2099-01-02.tar",
        )
        self.assertEqual(
            archive.sidecar_filename(RELEASE_ID),
            "SSN2BFO-" + TRACK_ID + "-2099-01-02.tar.sha256",
        )
        self.assertEqual(
            archive.archive_top_level(RELEASE_ID),
            "SOSA-2023-2099-01-02",
        )
        self.assertNotEqual(
            archive.archive_filename(RELEASE_ID),
            "SSN2BFO-2099-01-02.tar",
        )

    def test_exact_archive_authority_matches_package_inventory(self) -> None:
        members = archive.canonical_member_names(
            RELEASE_ID
        )

        self.assertEqual(
            len(members),
            20,
        )

        top = archive.archive_top_level(
            RELEASE_ID
        )

        files = {
            value[len(top) + 1 :]
            for value in members
            if not value.endswith("/")
        }

        self.assertEqual(
            files,
            set(PACKAGE_FILE_PATHS),
        )

        self.assertEqual(
            archive.EXPECTED_DIRECTORIES,
            (
                TRACK_ID,
                "sources",
            ),
        )

        self.assertLessEqual(
            max(
                len(value.encode("ascii"))
                for value in members
            ),
            100,
        )

    def test_package_validation_uses_sosa_checker_without_reconstruction(
        self,
    ) -> None:
        package = Path(
            "/tmp/synthetic-sosa-2023-package"
        )

        with mock.patch.object(
            archive,
            "validate_release_package",
            return_value=(),
        ) as validator:
            issues = (
                archive
                ._package_validation_issues(
                    package,
                    REPO_ROOT,
                )
            )

        self.assertEqual(
            issues,
            (),
        )

        validator.assert_called_once_with(
            package,
            repository_root=REPO_ROOT,
            reconstruct=False,
        )

    def test_archive_module_has_no_current_track_engine_dependency(
        self,
    ) -> None:
        source = (
            REPO_ROOT
            / "tools/sosa_2023_release_archive.py"
        ).read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source
        )

        imports = []

        for node in tree.body:
            if isinstance(
                node,
                ast.Import,
            ):
                imports.extend(
                    alias.name
                    for alias in node.names
                )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):
                imports.append(
                    node.module or ""
                )

        self.assertFalse(
            {
                "build_release",
                "check_release",
                "release_manifest",
                "release_archive",
            }.intersection(
                imports
            )
        )

    def test_current_archive_and_sosa_package_authorities_remain_byte_locked(
        self,
    ) -> None:
        expected = {
            "tools/release_archive.py":
                "8928d921ac7b850f5ff52449c12013fa2c394b6d1acaff83972134b81741c974",
            "tests/test_release_archive.py":
                "f2a89e4f1a34e3bdec443de687c74fd6d5ed4c938da09d8fef2cdc0fdac927d5",
            "tools/sosa_2023_release_runtime.py":
                "c515000306cdf114f648c447305946e7c2a39f33f7c45b5d79d99255a554d939",
            "tools/sosa_2023_build_release.py":
                "0479c0ad94e5f059728a294c83a2901cec2eafddad42d6bde4a8e06f5a78e9b3",
            "tools/sosa_2023_check_release.py":
                "a41cf98cdf13dc0029f710cd1c857c03a6f5b58abd5b10e2d5dbcedcb00010e9",
            "tools/sosa_2023_release_manifest.py":
                "a3d1f1a12f88455913dd1553fff6b5cd70a189de8cec3399644c08d8646b0303",
            "config/sosa-2023-release-manifest-schema-v1.json":
                "5b75bfbd2a074b65a611f7ffcad15d5834df04319de8dca016b326fc14402482",
        }

        for relative, digest in expected.items():
            with self.subTest(
                path=relative
            ):
                self.assertEqual(
                    hashlib.sha256(
                        (
                            REPO_ROOT
                            / relative
                        ).read_bytes()
                    ).hexdigest(),
                    digest,
                )


if __name__ == "__main__":
    unittest.main()
