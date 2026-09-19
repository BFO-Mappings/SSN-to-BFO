#!/usr/bin/env python3
"""Shadow-mode equivalence tests for the project-neutral COMS framework."""

from __future__ import annotations

import hashlib
import sys
import unittest
from collections import Counter
from pathlib import Path

from coms.adapters.xlsx import read_xlsx_source_rows
from coms.mapping_parser import EntityResolutionError
from coms.row_identity import canonical_row_json as framework_canonical_row_json
from coms.workbook_batch import (
    build_governed_workbook_batch,
    validate_workbook_source_row_ids,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import coms_framework_integration as integration  # noqa: E402
import coms_row_identity as legacy_identity  # noqa: E402
import generate_mapping_from_coms as legacy  # noqa: E402


WORKBOOK_PATH = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"
WORKBOOK_SHA256 = "e32c6b5691bf4aa00b4ec564731e0364edc2567658bb21c46f83c1e3f0d9a4f6"
ARTIFACT_SHA256 = {
    REPO_ROOT / "SSN2BFO.ttl": "c31997d7e7b8c5e0bffd3f23a4597ab4be80786978462fefe800c4c7a5dc0c11",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl": (
        "17695ef17379924449153b2c92ffaed6b57d497a1b2d1e854f584614cebec770"
    ),
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl": (
        "676b31620df10db5c26c46bcc44b2dfd5939d606b16e0fa8a910926e8497c3af"
    ),
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl": (
        "2908f89648d42dc928f7225056216f1cbf3bcdc79de1bcf770b40a017a5e9bf5"
    ),
    REPO_ROOT / "reports/coms-product-dispositions.json": (
        "8976b914a8ef4d4291a2af190f4e01970c4c6a4b073ef7544babd67647509e75"
    ),
}
EXPECTED_MAPPING_TYPES = {
    "class_mapping": 44,
    "object_property_mapping": 25,
    "property_chain": 3,
    "domain": 16,
    "range": 15,
    "explicit_blank": 2,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_key(row_id: str, worksheet: str, row_number: int) -> tuple[str, str, int]:
    return row_id, worksheet, row_number


class ComsFrameworkShadowIntegrationTests(unittest.TestCase):
    def test_primary_workbook_semantic_identity_equivalence(self) -> None:
        workbook_hash_before = sha256_file(WORKBOOK_PATH)
        workbook_mtime_before = WORKBOOK_PATH.stat().st_mtime_ns
        artifact_hashes_before = {
            path: sha256_file(path)
            for path in ARTIFACT_SHA256
        }

        source_rows = read_xlsx_source_rows(
            integration.PRIMARY_WORKBOOK_PROFILE,
            base_directory=REPO_ROOT,
        )
        self.assertEqual(len(source_rows), 105)
        validate_workbook_source_row_ids(source_rows)
        self.assertEqual(len({row.row_id_text for row in source_rows}), 105)

        legacy_rows, legacy_stats = legacy.read_workbook(WORKBOOK_PATH)
        legacy_processed = legacy.validate_and_process_rows(
            legacy_rows,
            legacy.Resolver(),
            legacy_stats,
        )

        resolver = legacy.Resolver()
        audited_rows = build_governed_workbook_batch(
            source_rows,
            integration.SsnSourceResolverAdapter(resolver),
            integration.SsnTargetResolverAdapter(resolver),
        )
        self.assertEqual(len(audited_rows), 105)

        source_keys = [
            audit_key(
                row.row_id_text,
                row.location.worksheet,
                row.location.row_number,
            )
            for row in source_rows
        ]
        legacy_keys = [
            audit_key(
                row.stable_row_id,
                row.sheet,
                row.row_number,
            )
            for row in legacy_rows
        ]
        self.assertEqual(source_keys, legacy_keys)
        self.assertEqual(
            [
                (
                    row.subject_text,
                    row.predicate_text,
                    row.target_text,
                    row.reasoning_text,
                    row.status_text,
                )
                for row in source_rows
            ],
            [
                (
                    row.subject_text,
                    row.predicate_text,
                    row.target_text,
                    row.reasoning_text,
                    None,
                )
                for row in legacy_rows
            ],
        )

        legacy_by_key = {
            audit_key(
                item.row.stable_row_id,
                item.row.sheet,
                item.row.row_number,
            ): item
            for item in legacy_processed
        }
        framework_by_key = {
            audit_key(
                item.source_row.row_id_text,
                item.source_row.location.worksheet,
                item.source_row.location.row_number,
            ): item
            for item in audited_rows
        }
        self.assertEqual(list(framework_by_key), source_keys)
        self.assertEqual(set(framework_by_key), set(legacy_by_key))

        canonical_row_matches = 0
        expression_hash_matches = 0
        authoritative_axiom_matches = 0
        axiom_hash_matches = 0

        for key in source_keys:
            framework_audit = framework_by_key[key].row_audit
            legacy_audit = legacy_by_key[key].identity_audit
            self.assertIsNotNone(legacy_audit)
            assert legacy_audit is not None

            framework_payload = framework_canonical_row_json(
                framework_audit.expression
            )
            legacy_payload = legacy_identity.canonical_row_json(
                legacy_audit.expression
            )
            if framework_payload == legacy_payload:
                canonical_row_matches += 1
            if (
                framework_audit.source_expression_sha256
                == legacy_audit.source_expression_sha256
            ):
                expression_hash_matches += 1

            framework_axioms = tuple(
                axiom.canonical_axiom
                for axiom in framework_audit.authoritative_axioms
            )
            legacy_axioms = tuple(
                axiom.canonical_axiom
                for axiom in legacy_audit.authoritative_axioms
            )
            if framework_axioms == legacy_axioms:
                authoritative_axiom_matches += 1

            framework_axiom_hashes = tuple(
                axiom.sha256
                for axiom in framework_audit.authoritative_axioms
            )
            legacy_axiom_hashes = tuple(
                axiom.sha256
                for axiom in legacy_audit.authoritative_axioms
            )
            if framework_axiom_hashes == legacy_axiom_hashes:
                axiom_hash_matches += 1

        self.assertEqual(canonical_row_matches, 105)
        self.assertEqual(expression_hash_matches, 105)
        self.assertEqual(authoritative_axiom_matches, 105)
        self.assertEqual(axiom_hash_matches, 105)

        mapping_types = Counter(
            item.governed_record.mapping_type
            for item in audited_rows
        )
        self.assertEqual(dict(mapping_types), EXPECTED_MAPPING_TYPES)
        self.assertEqual(
            sum(len(item.row_audit.authoritative_axioms) for item in audited_rows),
            103,
        )
        explicit_blank_rows = [
            item
            for item in audited_rows
            if item.governed_record.mapping_type == "explicit_blank"
        ]
        self.assertEqual(len(explicit_blank_rows), 2)
        for item in explicit_blank_rows:
            key = audit_key(
                item.source_row.row_id_text,
                item.source_row.location.worksheet,
                item.source_row.location.row_number,
            )
            self.assertEqual(item.row_audit.authoritative_axioms, ())
            legacy_audit = legacy_by_key[key].identity_audit
            self.assertIsNotNone(legacy_audit)
            assert legacy_audit is not None
            self.assertEqual(legacy_audit.authoritative_axioms, ())

        self.assertEqual(workbook_hash_before, WORKBOOK_SHA256)
        self.assertEqual(sha256_file(WORKBOOK_PATH), WORKBOOK_SHA256)
        self.assertEqual(WORKBOOK_PATH.stat().st_mtime_ns, workbook_mtime_before)
        self.assertEqual(artifact_hashes_before, ARTIFACT_SHA256)
        self.assertEqual(
            {path: sha256_file(path) for path in ARTIFACT_SHA256},
            ARTIFACT_SHA256,
        )

    def test_target_adapter_translates_legacy_resolution_failure(self) -> None:
        class FailingResolver:
            def resolve(self, token: str, expected_kind: str, row_id: str) -> None:
                raise legacy.GenerationError(
                    f"{row_id}: unresolved {expected_kind} token {token!r}"
                )

        adapter = integration.SsnTargetResolverAdapter(FailingResolver())  # type: ignore[arg-type]
        with self.assertRaises(EntityResolutionError) as raised:
            adapter.resolve_entity("bfo:Missing", "class")
        self.assertIn("COMS shadow integration", str(raised.exception))
