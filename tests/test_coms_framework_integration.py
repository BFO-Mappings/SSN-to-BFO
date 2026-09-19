#!/usr/bin/env python3
"""Shadow-mode equivalence tests for the project-neutral COMS framework."""

from __future__ import annotations

import builtins
import hashlib
import inspect
import sys
import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import coms.mapping_parser as framework_parser
import coms.mapping_predicates as framework_predicates
import coms.mapping_record_builder as framework_record_builder
import coms.row_identity as framework_identity
import coms.workbook_batch as framework_batch
import coms.workbook_mapping as framework_workbook_mapping
from coms.adapters.xlsx import (
    WorkbookSourceRow,
    XlsxAdapterDependencyError,
    XlsxAdapterError,
    read_xlsx_source_rows,
)
from coms.mapping_expression import ExpressionNode
from coms.mapping_record import GovernedMappingRecord
from coms.mapping_parser import EntityResolutionError
from coms.row_identity import (
    AuthoritativeAxiomIdentity as FrameworkAuthoritativeAxiomIdentity,
    CanonicalRowAudit as FrameworkCanonicalRowAudit,
    CanonicalRowExpression as FrameworkCanonicalRowExpression,
    RowLocation as FrameworkRowLocation,
    canonical_row_json as framework_canonical_row_json,
)
from coms.workbook_batch import (
    AuditedWorkbookRow,
    build_governed_workbook_batch,
    validate_workbook_source_row_ids,
)
from rdflib import URIRef


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import coms_framework_integration as integration  # noqa: E402
import coms_row_identity as legacy_identity  # noqa: E402
import generate_mapping_from_coms as legacy  # noqa: E402


WORKBOOK_PATH = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"
WORKBOOK_SHA256 = "e32c6b5691bf4aa00b4ec564731e0364edc2567658bb21c46f83c1e3f0d9a4f6"
GENERATOR_SHA256 = "047dce7ffc77bbffdd4a5a8e5549b0ed161c5b15f5ffd8ad8a36a59f7b5001c5"
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


def _expression_kinds(expression: legacy.Expr | None) -> set[str]:
    if expression is None:
        return set()
    kinds = {expression.kind}
    for child in expression.children:
        kinds.update(_expression_kinds(child))
    kinds.update(_expression_kinds(expression.filler))
    return kinds


SYNTHETIC_HEADERS = (
    "sssom:subject_id",
    "sssom:predicate_id",
    "coms:Target",
    "coms:Reasoning",
    "coms:RowID",
)


def _test_row_id(number: int) -> str:
    return f"urn:uuid:00000000-0000-4000-8000-{number:012d}"


def _write_test_workbook(
    path: Path,
    sheet1_rows: tuple[tuple[str, str, str, str, str], ...],
    sheet2_rows: tuple[tuple[str, str, str, str, str], ...] = (),
) -> None:
    workbook = legacy.openpyxl.Workbook()
    sheet1 = workbook.active
    sheet1.title = "Sheet1"
    sheet1.append(SYNTHETIC_HEADERS)
    for row in sheet1_rows:
        sheet1.append(row)
    sheet2 = workbook.create_sheet("Sheet2")
    sheet2.append(SYNTHETIC_HEADERS)
    for row in sheet2_rows:
        sheet2.append(row)
    workbook.save(path)
    workbook.close()


class CountingResolver(legacy.Resolver):
    def __init__(self) -> None:
        self.source_resolution_calls = 0
        self.entity_resolution_calls = 0
        super().__init__()

    def resolve_source_subject(self, token: str, row_id: str) -> tuple[URIRef, str]:
        self.source_resolution_calls += 1
        return super().resolve_source_subject(token, row_id)

    def resolve(self, token: str, expected_kind: str, row_id: str) -> legacy.Resolution:
        self.entity_resolution_calls += 1
        return super().resolve(token, expected_kind, row_id)


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


class ComsCompatibilityProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_rows = read_xlsx_source_rows(
            integration.PRIMARY_WORKBOOK_PROFILE,
            base_directory=REPO_ROOT,
        )

        legacy_rows, legacy_stats = legacy.read_workbook(WORKBOOK_PATH)
        cls.legacy_resolver = legacy.Resolver()
        cls.legacy_processed = legacy.validate_and_process_rows(
            legacy_rows,
            cls.legacy_resolver,
            legacy_stats,
        )

        cls.framework_resolver = legacy.Resolver()
        cls.row_context = integration.SsnWorkbookResolutionContext(cls.source_rows)
        cls.audited_rows = build_governed_workbook_batch(
            cls.source_rows,
            integration.SsnSourceResolverAdapter(
                cls.framework_resolver,
                row_context=cls.row_context,
            ),
            integration.SsnTargetResolverAdapter(
                cls.framework_resolver,
                row_context=cls.row_context,
            ),
        )
        cls.row_context.assert_complete()
        cls.projected_rows = integration.project_audited_workbook_rows(
            cls.audited_rows,
            cls.row_context.source_kind_by_row_id,
        )

    def test_row_aware_adapters_preserve_context_and_source_kinds(self) -> None:
        rows = (
            WorkbookSourceRow(
                location=FrameworkRowLocation("Mappings", 2),
                row_id_text="urn:uuid:00000000-0000-4000-8000-000000000001",
                subject_text="  sosa:Observation  ",
                predicate_text="rdfs:subClassOf",
                target_text="bfo:Entity",
                reasoning_text="",
                status_text=None,
            ),
            WorkbookSourceRow(
                location=FrameworkRowLocation("Mappings", 3),
                row_id_text="urn:uuid:00000000-0000-4000-8000-000000000002",
                subject_text="sosa:hasFeatureOfInterest",
                predicate_text="",
                target_text="",
                reasoning_text="unmapped",
                status_text=None,
            ),
        )

        class RecordingResolver:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str, str, str]] = []

            def resolve_source_subject(self, token: str, row_id: str) -> tuple[URIRef, str]:
                self.calls.append(("source", token, "", row_id))
                kind = "class" if token == "sosa:Observation" else "object_property"
                return URIRef(f"http://example.org/{token.split(':', 1)[1]}"), kind

            def resolve(self, token: str, expected_kind: str, row_id: str) -> legacy.Resolution:
                self.calls.append(("target", token, expected_kind, row_id))
                if token == "bfo:Missing":
                    raise legacy.GenerationError(
                        f"{row_id}: unresolved {expected_kind} token {token!r}"
                    )
                return legacy.Resolution(
                    token=token,
                    iri=URIRef("http://example.org/Entity"),
                    kind=expected_kind,
                    method="direct",
                )

        resolver = RecordingResolver()
        context = integration.SsnWorkbookResolutionContext(rows)
        source_adapter = integration.SsnSourceResolverAdapter(  # type: ignore[arg-type]
            resolver,
            row_context=context,
        )
        target_adapter = integration.SsnTargetResolverAdapter(  # type: ignore[arg-type]
            resolver,
            row_context=context,
        )

        with self.assertRaises(legacy.GenerationError):
            target_adapter.resolve_entity("bfo:Entity", "class")
        with self.assertRaises(legacy.GenerationError):
            source_adapter.resolve_source_entity("sosa:Wrong")
        self.assertEqual(resolver.calls, [])

        first_diagnostic = f"Mappings!2 [{rows[0].row_id_text}]"
        source_adapter.resolve_source_entity("sosa:Observation")
        with self.assertRaises(EntityResolutionError) as raised:
            target_adapter.resolve_entity("bfo:Missing", "class")
        self.assertIn(first_diagnostic, str(raised.exception))
        target_adapter.resolve_entity("bfo:Entity", "class")
        source_adapter.resolve_source_entity("sosa:hasFeatureOfInterest")
        context.assert_complete()

        second_diagnostic = f"Mappings!3 [{rows[1].row_id_text}]"
        self.assertEqual(
            resolver.calls,
            [
                ("source", "sosa:Observation", "", first_diagnostic),
                ("target", "bfo:Missing", "class", first_diagnostic),
                ("target", "bfo:Entity", "class", first_diagnostic),
                ("source", "sosa:hasFeatureOfInterest", "", second_diagnostic),
            ],
        )
        self.assertEqual(
            dict(context.source_kind_by_row_id),
            {
                rows[0].row_id_text: "class",
                rows[1].row_id_text: "object_property",
            },
        )
        with self.assertRaises(legacy.GenerationError):
            source_adapter.resolve_source_entity("sosa:Observation")

    def test_expression_projection_preserves_supported_shapes_and_order(self) -> None:
        expression = ExpressionNode(
            kind="intersection",
            children=(
                ExpressionNode(kind="named", iri="http://example.org/Z"),
                ExpressionNode(
                    kind="union",
                    children=(
                        ExpressionNode(kind="named", iri="http://example.org/B"),
                        ExpressionNode(kind="named", iri="http://example.org/A"),
                    ),
                ),
                ExpressionNode(
                    kind="some",
                    property_iri="http://example.org/p",
                    filler=ExpressionNode(
                        kind="intersection",
                        children=(
                            ExpressionNode(kind="named", iri="http://example.org/D"),
                            ExpressionNode(kind="named", iri="http://example.org/C"),
                        ),
                    ),
                ),
            ),
        )
        expected = legacy.Expr(
            kind="intersection",
            children=(
                legacy.Expr(kind="named", iri=URIRef("http://example.org/Z")),
                legacy.Expr(
                    kind="union",
                    children=(
                        legacy.Expr(kind="named", iri=URIRef("http://example.org/B")),
                        legacy.Expr(kind="named", iri=URIRef("http://example.org/A")),
                    ),
                ),
                legacy.Expr(
                    kind="some",
                    prop=URIRef("http://example.org/p"),
                    filler=legacy.Expr(
                        kind="intersection",
                        children=(
                            legacy.Expr(kind="named", iri=URIRef("http://example.org/D")),
                            legacy.Expr(kind="named", iri=URIRef("http://example.org/C")),
                        ),
                    ),
                ),
            ),
        )
        self.assertEqual(integration.project_expression_node(expression), expected)
        self.assertIsNone(integration.project_expression_node(None))

    def test_row_and_audit_projection_are_verbatim_legacy_values(self) -> None:
        source_row = WorkbookSourceRow(
            location=FrameworkRowLocation("Mappings", 7),
            row_id_text="sentinel-row-id-that-must-not-be-revalidated",
            subject_text=" sosa:Observation ",
            predicate_text=" rdfs:subClassOf ",
            target_text=" bfo:Entity ",
            reasoning_text=" preserve lexical text ",
            status_text=" reviewed ",
        )
        self.assertEqual(
            integration.project_workbook_source_row(source_row),
            legacy.WorkbookRow(
                sheet="Mappings",
                row_number=7,
                subject_text=" sosa:Observation ",
                predicate_text=" rdfs:subClassOf ",
                target_text=" bfo:Entity ",
                reasoning_text=" preserve lexical text ",
                stable_row_id=source_row.row_id_text,
                mapping_status_text=" reviewed ",
            ),
        )

        framework_audit = FrameworkCanonicalRowAudit(
            row_id=source_row.row_id_text,
            location=source_row.location,
            reasoning=" sentinel audit reasoning ",
            expression=FrameworkCanonicalRowExpression(
                canonicalization="sentinel-canonicalization",
                mapping_type="sentinel-mapping-type",
                predicate_iri="sentinel-predicate-iri",
                subject_iri="sentinel-subject-iri",
                target="sentinel-canonical-target",
            ),
            source_expression_sha256="sentinel-source-expression-hash",
            authoritative_axioms=(
                FrameworkAuthoritativeAxiomIdentity(
                    canonical_axiom="sentinel-authoritative-axiom",
                    sha256="sentinel-authoritative-axiom-hash",
                ),
            ),
        )
        audited_row = AuditedWorkbookRow(
            source_row=source_row,
            governed_record=GovernedMappingRecord(
                row_id=source_row.row_id_text,
                subject_iri="http://example.org/subject",
                predicate_iri="http://www.w3.org/2000/01/rdf-schema#subClassOf",
                mapping_type="class_mapping",
                reasoning=source_row.reasoning_text,
                expression=ExpressionNode(
                    kind="named",
                    iri="http://example.org/target",
                ),
            ),
            row_audit=framework_audit,
        )
        projected_row = integration.project_audited_workbook_rows(
            (audited_row,),
            {source_row.row_id_text: "class"},
        )[0]
        projected_audit = projected_row.identity_audit
        self.assertIsInstance(projected_audit, legacy_identity.CanonicalRowAudit)
        assert projected_audit is not None
        self.assertIsInstance(projected_audit.location, legacy_identity.RowLocation)
        self.assertIsInstance(
            projected_audit.expression,
            legacy_identity.CanonicalRowExpression,
        )
        for axiom in projected_audit.authoritative_axioms:
            self.assertIsInstance(
                axiom,
                legacy_identity.AuthoritativeAxiomIdentity,
            )
        self.assertEqual(
            projected_audit,
            legacy_identity.CanonicalRowAudit(
                row_id=source_row.row_id_text,
                location=legacy_identity.RowLocation("Mappings", 7),
                reasoning=" sentinel audit reasoning ",
                expression=legacy_identity.CanonicalRowExpression(
                    canonicalization="sentinel-canonicalization",
                    mapping_type="sentinel-mapping-type",
                    predicate_iri="sentinel-predicate-iri",
                    subject_iri="sentinel-subject-iri",
                    target="sentinel-canonical-target",
                ),
                source_expression_sha256="sentinel-source-expression-hash",
                authoritative_axioms=(
                    legacy_identity.AuthoritativeAxiomIdentity(
                        canonical_axiom="sentinel-authoritative-axiom",
                        sha256="sentinel-authoritative-axiom-hash",
                    ),
                ),
            ),
        )

    def test_primary_workbook_projection_is_structurally_identical(self) -> None:
        self.assertEqual(len(self.projected_rows), 105)
        self.assertEqual(len(self.legacy_processed), 105)

        projected_order = [
            (item.row.stable_row_id, item.row.sheet, item.row.row_number)
            for item in self.projected_rows
        ]
        legacy_order = [
            (item.row.stable_row_id, item.row.sheet, item.row.row_number)
            for item in self.legacy_processed
        ]
        self.assertEqual(projected_order, legacy_order)

        mismatches = Counter()
        for projected, expected in zip(self.projected_rows, self.legacy_processed):
            mismatches["row_id_location"] += (
                projected.row.stable_row_id,
                projected.row.sheet,
                projected.row.row_number,
            ) != (
                expected.row.stable_row_id,
                expected.row.sheet,
                expected.row.row_number,
            )
            mismatches["workbook_row_lexical"] += (
                projected.row.subject_text,
                projected.row.predicate_text,
                projected.row.target_text,
                projected.row.reasoning_text,
                projected.row.mapping_status_text,
            ) != (
                expected.row.subject_text,
                expected.row.predicate_text,
                expected.row.target_text,
                expected.row.reasoning_text,
                expected.row.mapping_status_text,
            )
            mismatches["subject"] += projected.subject != expected.subject
            mismatches["source_kind"] += projected.subject_kind != expected.subject_kind
            mismatches["predicate"] += projected.predicate != expected.predicate
            mismatches["target_lexical"] += projected.target != expected.target
            mismatches["expression_tree"] += projected.expr != expected.expr
            mismatches["target_property"] += projected.target_property != expected.target_property
            mismatches["property_chain"] += projected.property_chain != expected.property_chain
            mismatches["identity_audit"] += projected.identity_audit != expected.identity_audit
        self.assertEqual(
            dict(mismatches),
            {
                "row_id_location": 0,
                "workbook_row_lexical": 0,
                "subject": 0,
                "source_kind": 0,
                "predicate": 0,
                "target_lexical": 0,
                "expression_tree": 0,
                "target_property": 0,
                "property_chain": 0,
                "identity_audit": 0,
            },
        )
        self.assertEqual(self.projected_rows, self.legacy_processed)

        projected_by_location = {
            (item.row.sheet, item.row.row_number): item
            for item in self.projected_rows
        }
        legacy_by_location = {
            (item.row.sheet, item.row.row_number): item
            for item in self.legacy_processed
        }
        representative_locations = (
            ("Sheet1", 2),   # named class
            ("Sheet1", 5),   # intersection
            ("Sheet1", 4),   # union
            ("Sheet1", 13),  # nested existential
            ("Sheet2", 2),   # direct object-property target
            ("Sheet2", 18),  # ordered property chain
            ("Sheet2", 6),   # domain
            ("Sheet2", 7),   # range
            ("Sheet2", 16),  # explicit blank
        )
        for location in representative_locations:
            self.assertEqual(
                projected_by_location[location],
                legacy_by_location[location],
            )

        self.assertEqual(projected_by_location[("Sheet1", 2)].expr.kind, "named")
        self.assertEqual(projected_by_location[("Sheet1", 5)].expr.kind, "intersection")
        self.assertEqual(projected_by_location[("Sheet1", 4)].expr.kind, "union")
        self.assertIn(
            "some",
            _expression_kinds(projected_by_location[("Sheet1", 13)].expr),
        )
        self.assertIsNotNone(projected_by_location[("Sheet2", 2)].target_property)
        self.assertGreater(len(projected_by_location[("Sheet2", 18)].property_chain), 1)
        self.assertEqual(projected_by_location[("Sheet2", 6)].predicate, "rdfs:domain")
        self.assertEqual(projected_by_location[("Sheet2", 7)].predicate, "rdfs:range")

    def test_resolution_report_matches_legacy_row_attribution(self) -> None:
        self.assertGreater(len(self.legacy_resolver.records), 0)
        self.assertEqual(
            self.framework_resolver.records,
            self.legacy_resolver.records,
        )
        for record in self.framework_resolver.records.values():
            self.assertNotIn("COMS shadow integration", record.rows)

    def test_both_explicit_blank_rows_project_without_targets(self) -> None:
        blank_rows = [item for item in self.projected_rows if not item.predicate]
        self.assertEqual(
            {(item.row.sheet, item.row.row_number, item.row.stable_row_id) for item in blank_rows},
            {
                (
                    "Sheet2",
                    16,
                    "urn:uuid:2ae25d88-9551-45e7-a2b9-7735575e4d8f",
                ),
                (
                    "Sheet2",
                    17,
                    "urn:uuid:637399a9-a264-49f7-bab8-33f2128646ab",
                ),
            },
        )
        legacy_by_row_id = {
            item.row.stable_row_id: item
            for item in self.legacy_processed
        }
        for item in blank_rows:
            self.assertEqual(item, legacy_by_row_id[item.row.stable_row_id])
            self.assertEqual(item.subject_kind, "object_property")
            self.assertEqual(item.predicate, "")
            self.assertEqual(item.target, "")
            self.assertIsNone(item.expr)
            self.assertIsNone(item.target_property)
            self.assertEqual(item.property_chain, ())
            self.assertIsNotNone(item.identity_audit)
            assert item.identity_audit is not None
            self.assertEqual(item.identity_audit.authoritative_axioms, ())

    def test_projection_invokes_no_legacy_semantic_authority(self) -> None:
        forbidden = AssertionError("projection invoked a legacy semantic authority")
        with (
            mock.patch.object(legacy, "ManchesterParser", side_effect=forbidden),
            mock.patch.object(legacy, "parse_property_chain", side_effect=forbidden),
            mock.patch.object(legacy.Resolver, "resolve_source_subject", side_effect=forbidden),
            mock.patch.object(legacy.Resolver, "resolve", side_effect=forbidden),
            mock.patch.object(legacy, "validate_workbook_row_ids", side_effect=forbidden),
            mock.patch.object(legacy, "build_row_audit", side_effect=forbidden),
            mock.patch.object(legacy_identity, "build_row_audit", side_effect=forbidden),
            mock.patch.object(legacy, "attach_canonical_identities", side_effect=forbidden),
            mock.patch.object(framework_parser, "parse_class_expression", side_effect=forbidden),
            mock.patch.object(framework_parser, "parse_property_chain", side_effect=forbidden),
            mock.patch.object(
                framework_identity,
                "canonical_input_for_mapping_record",
                side_effect=forbidden,
            ),
            mock.patch.object(framework_identity, "build_row_audit", side_effect=forbidden),
            mock.patch.object(
                framework_batch,
                "canonical_input_for_mapping_record",
                side_effect=forbidden,
            ),
            mock.patch.object(framework_batch, "build_row_audit", side_effect=forbidden),
            mock.patch.object(
                framework_batch,
                "validate_workbook_source_row_ids",
                side_effect=forbidden,
            ),
        ):
            projected = integration.project_audited_workbook_rows(
                self.audited_rows,
                self.row_context.source_kind_by_row_id,
            )
        self.assertEqual(projected, self.legacy_processed)

        with self.assertRaisesRegex(
            legacy.GenerationError,
            "source-kind sidecar entry is missing",
        ):
            integration.project_audited_workbook_rows(self.audited_rows, {})


class ComsPrimaryWorkbookWrapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        legacy_rows, cls.legacy_stats = legacy.read_workbook(WORKBOOK_PATH)
        cls.legacy_resolver = CountingResolver()
        cls.legacy_processed = legacy.validate_and_process_rows(
            legacy_rows,
            cls.legacy_resolver,
            cls.legacy_stats,
        )

        cls.framework_resolver = CountingResolver()
        (
            cls.framework_processed,
            cls.framework_stats,
        ) = integration.process_primary_workbook_with_coms(
            WORKBOOK_PATH,
            cls.framework_resolver,
        )

    @staticmethod
    def _legacy_process(path: Path) -> tuple[list[legacy.ProcessedRow], legacy.WorkbookStats]:
        rows, stats = legacy.read_workbook(path)
        processed = legacy.validate_and_process_rows(rows, legacy.Resolver(), stats)
        return processed, stats

    def test_primary_wrapper_matches_legacy_rows_stats_and_resolution_state(self) -> None:
        self.assertEqual(len(self.framework_processed), 105)
        self.assertEqual(self.framework_processed, self.legacy_processed)
        self.assertEqual(self.framework_stats, self.legacy_stats)
        self.assertEqual(
            self.framework_resolver.records,
            self.legacy_resolver.records,
        )
        self.assertEqual(len(self.framework_resolver.records), 60)
        self.assertEqual(
            sum(
                len(record.rows)
                for record in self.framework_resolver.records.values()
            ),
            265,
        )
        self.assertEqual(self.legacy_resolver.source_resolution_calls, 105)
        self.assertEqual(self.framework_resolver.source_resolution_calls, 105)
        self.assertEqual(self.legacy_resolver.entity_resolution_calls, 499)
        self.assertEqual(self.framework_resolver.entity_resolution_calls, 499)
        self.assertEqual(self.framework_stats.rows_by_sheet["Sheet1"], 44)
        self.assertEqual(self.framework_stats.rows_by_sheet["Sheet2"], 61)
        self.assertEqual(self.framework_stats.mapped_rows, 72)
        self.assertEqual(self.framework_stats.blank_mapping_rows, 2)
        self.assertEqual(self.framework_stats.active_axiom_rows, 103)

    def test_wrapper_uses_no_legacy_generic_front_half_authorities(self) -> None:
        resolver = legacy.Resolver()
        forbidden = AssertionError("COMS wrapper invoked a legacy front-half authority")
        with (
            mock.patch.object(legacy, "read_workbook", side_effect=forbidden),
            mock.patch.object(legacy, "validate_and_process_rows", side_effect=forbidden),
            mock.patch.object(legacy, "ManchesterParser", side_effect=forbidden),
            mock.patch.object(legacy, "parse_property_chain", side_effect=forbidden),
            mock.patch.object(legacy, "validate_workbook_row_ids", side_effect=forbidden),
            mock.patch.object(legacy, "attach_canonical_identities", side_effect=forbidden),
            mock.patch.object(legacy, "build_row_audit", side_effect=forbidden),
            mock.patch.object(legacy_identity, "build_row_audit", side_effect=forbidden),
            mock.patch.object(legacy, "Resolver", side_effect=forbidden),
            mock.patch.object(
                integration,
                "_validate_primary_domain_range_policy_compat",
                wraps=integration._validate_primary_domain_range_policy_compat,
            ) as domain_policy,
            mock.patch.object(
                legacy,
                "validate_incompatible_duplicate_mappings",
                wraps=legacy.validate_incompatible_duplicate_mappings,
            ) as incompatible_policy,
        ):
            processed, stats = integration.process_primary_workbook_with_coms(
                WORKBOOK_PATH,
                resolver,
            )
        self.assertEqual(len(processed), 105)
        self.assertEqual(stats, self.legacy_stats)
        domain_policy.assert_called_once_with(processed)
        incompatible_policy.assert_called_once_with(processed)

    def test_rowid_preflight_fails_before_batch_or_resolution(self) -> None:
        with TemporaryDirectory() as directory:
            workbook_path = Path(directory) / "invalid-row-id.xlsx"
            malformed_row_id = "not-a-canonical-row-id"
            _write_test_workbook(
                workbook_path,
                ((
                    "sosa:Observation",
                    "rdfs:subClassOf",
                    "cco:InformationContentEntity",
                    "",
                    malformed_row_id,
                ),),
            )
            resolver = mock.Mock(spec=legacy.Resolver)
            with (
                mock.patch.object(
                    integration,
                    "validate_workbook_source_row_ids",
                    wraps=integration.validate_workbook_source_row_ids,
                ) as preflight,
                mock.patch.object(
                    integration,
                    "build_governed_workbook_batch",
                    side_effect=AssertionError("semantic batch must not run"),
                ),
                self.assertRaises(legacy.GenerationError) as raised,
            ):
                integration.process_primary_workbook_with_coms(
                    workbook_path,
                    resolver,
                )

        preflight.assert_called_once()
        resolver.resolve_source_subject.assert_not_called()
        resolver.resolve.assert_not_called()
        self.assertIsInstance(
            raised.exception.__cause__,
            framework_identity.ComsRowIdentityError,
        )
        self.assertIn("MALFORMED_ROW_ID", str(raised.exception))
        self.assertIn("Sheet1!2", str(raised.exception))
        self.assertIn(malformed_row_id, str(raised.exception))

    def test_unresolved_source_preserves_project_generation_error(self) -> None:
        row_id = _test_row_id(1)
        with TemporaryDirectory() as directory:
            workbook_path = Path(directory) / "unresolved-source.xlsx"
            _write_test_workbook(
                workbook_path,
                ((
                    "sosa:DefinitelyMissingSource",
                    "rdfs:subClassOf",
                    "cco:InformationContentEntity",
                    "",
                    row_id,
                ),),
            )
            with self.assertRaises(legacy.GenerationError) as legacy_raised:
                self._legacy_process(workbook_path)
            with self.assertRaises(legacy.GenerationError) as framework_raised:
                integration.process_primary_workbook_with_coms(
                    workbook_path,
                    legacy.Resolver(),
                )

        self.assertEqual(
            str(framework_raised.exception),
            str(legacy_raised.exception),
        )
        self.assertIn(f"Sheet1!2 [{row_id}]", str(framework_raised.exception))
        self.assertIn("sosa:DefinitelyMissingSource", str(framework_raised.exception))
        self.assertIn("cannot be resolved", str(framework_raised.exception))

    def test_expected_coms_row_failures_translate_with_notes(self) -> None:
        row_id = _test_row_id(2)
        cases = (
            (
                "target",
                "sosa:Observation",
                "rdfs:subClassOf",
                "bfo:DefinitelyMissingTarget",
                framework_parser.EntityResolutionError,
                "unresolved class token",
            ),
            (
                "parse",
                "sosa:Observation",
                "rdfs:subClassOf",
                "(",
                framework_parser.MappingParseError,
                "unexpected end of expression",
            ),
            (
                "build",
                "sosa:Observation",
                "rdfs:subPropertyOf",
                "cco:is_about",
                framework_record_builder.MappingRecordBuildError,
                "requires subject kind 'object_property'",
            ),
            (
                "predicate",
                "sosa:Observation",
                "owl:notSupported",
                "cco:InformationContentEntity",
                framework_predicates.MappingPredicateTokenError,
                "unsupported mapping predicate token",
            ),
            (
                "blank-source",
                "",
                "rdfs:subClassOf",
                "cco:InformationContentEntity",
                framework_workbook_mapping.WorkbookMappingError,
                "requires nonblank subject text",
            ),
        )
        for (
            name,
            subject,
            predicate,
            target,
            expected_cause,
            expected_fragment,
        ) in cases:
            with self.subTest(name=name), TemporaryDirectory() as directory:
                workbook_path = Path(directory) / f"{name}.xlsx"
                _write_test_workbook(
                    workbook_path,
                    ((subject, predicate, target, "", row_id),),
                )
                with self.assertRaises(legacy.GenerationError) as raised:
                    integration.process_primary_workbook_with_coms(
                        workbook_path,
                        legacy.Resolver(),
                    )

                self.assertIsInstance(raised.exception.__cause__, expected_cause)
                message = str(raised.exception)
                self.assertIn(expected_cause.__name__, message)
                self.assertIn(expected_fragment, message)
                self.assertIn(f"Workbook source row: Sheet1!2 [{row_id}]", message)
                if name == "target":
                    self.assertIn(target, message)
                    self.assertIsInstance(
                        raised.exception.__cause__.__cause__,
                        legacy.GenerationError,
                    )
                if name == "predicate":
                    self.assertIn(predicate, message)

    def test_duplicate_authoritative_axiom_is_coms_owned(self) -> None:
        first_row_id = _test_row_id(3)
        second_row_id = _test_row_id(4)
        with TemporaryDirectory() as directory:
            workbook_path = Path(directory) / "duplicate-axiom.xlsx"
            _write_test_workbook(
                workbook_path,
                (
                    (
                        "sosa:FeatureOfInterest",
                        "rdfs:subClassOf",
                        "bfo:MaterialEntity or bfo:Process",
                        "",
                        first_row_id,
                    ),
                    (
                        "sosa:FeatureOfInterest",
                        "rdfs:subClassOf",
                        "bfo:Process or bfo:MaterialEntity",
                        "",
                        second_row_id,
                    ),
                ),
            )
            forbidden = AssertionError("project authoring policy ran too early")
            with (
                mock.patch.object(
                    integration,
                    "_validate_primary_domain_range_policy_compat",
                    side_effect=forbidden,
                ),
                mock.patch.object(
                    legacy,
                    "validate_incompatible_duplicate_mappings",
                    side_effect=forbidden,
                ),
                self.assertRaises(legacy.GenerationError) as raised,
            ):
                integration.process_primary_workbook_with_coms(
                    workbook_path,
                    legacy.Resolver(),
                )

        self.assertIsInstance(
            raised.exception.__cause__,
            framework_identity.ComsRowIdentityError,
        )
        message = str(raised.exception)
        self.assertIn("DUPLICATE_AUTHORITATIVE_AXIOM", message)
        self.assertIn(first_row_id, message)
        self.assertIn(second_row_id, message)
        self.assertIn("Sheet1!2", message)
        self.assertIn("Sheet1!3", message)

    def test_temporary_domain_range_policy_matches_legacy(self) -> None:
        duplicate_cases = (
            (
                "domain",
                "rdfs:domain",
                "sosa:Observation",
                "sosa:Actuation",
            ),
            (
                "range",
                "rdfs:range",
                "sosa:FeatureOfInterest",
                "sosa:Platform",
            ),
        )
        for name, predicate, first_target, second_target in duplicate_cases:
            with self.subTest(name=name), TemporaryDirectory() as directory:
                workbook_path = Path(directory) / f"duplicate-{name}.xlsx"
                _write_test_workbook(
                    workbook_path,
                    (
                        (
                            "sosa:hasFeatureOfInterest",
                            predicate,
                            first_target,
                            "",
                            _test_row_id(5),
                        ),
                        (
                            "sosa:hasFeatureOfInterest",
                            predicate,
                            second_target,
                            "",
                            _test_row_id(6),
                        ),
                    ),
                )
                with self.assertRaises(legacy.GenerationError) as legacy_raised:
                    self._legacy_process(workbook_path)
                with self.assertRaises(legacy.GenerationError) as framework_raised:
                    integration.process_primary_workbook_with_coms(
                        workbook_path,
                        legacy.Resolver(),
                    )
                self.assertEqual(
                    str(framework_raised.exception),
                    str(legacy_raised.exception),
                )

        with TemporaryDirectory() as directory:
            workbook_path = Path(directory) / "domain-and-range.xlsx"
            _write_test_workbook(
                workbook_path,
                (
                    (
                        "sosa:hasFeatureOfInterest",
                        "rdfs:domain",
                        "sosa:Observation",
                        "",
                        _test_row_id(7),
                    ),
                    (
                        "sosa:hasFeatureOfInterest",
                        "rdfs:range",
                        "sosa:FeatureOfInterest",
                        "",
                        _test_row_id(8),
                    ),
                ),
            )
            legacy_processed, legacy_stats = self._legacy_process(workbook_path)
            framework_processed, framework_stats = (
                integration.process_primary_workbook_with_coms(
                    workbook_path,
                    legacy.Resolver(),
                )
            )
        self.assertEqual(framework_processed, legacy_processed)
        self.assertEqual(framework_stats, legacy_stats)
        self.assertNotIn(
            self.framework_processed[0].predicate,
            legacy.DOMAIN_RANGE_PREDICATES,
        )
        integration._validate_primary_domain_range_policy_compat(
            [self.framework_processed[0], self.framework_processed[0]]
        )

    def test_existing_incompatible_mapping_policy_is_retained(self) -> None:
        with TemporaryDirectory() as directory:
            workbook_path = Path(directory) / "incompatible-mapping.xlsx"
            _write_test_workbook(
                workbook_path,
                (
                    (
                        "sosa:FeatureOfInterest",
                        "rdfs:subClassOf",
                        "bfo:MaterialEntity",
                        "",
                        _test_row_id(9),
                    ),
                    (
                        "sosa:FeatureOfInterest",
                        "rdfs:subClassOf",
                        "bfo:Process",
                        "",
                        _test_row_id(10),
                    ),
                ),
            )
            with self.assertRaises(legacy.GenerationError) as legacy_raised:
                self._legacy_process(workbook_path)
            with self.assertRaises(legacy.GenerationError) as framework_raised:
                integration.process_primary_workbook_with_coms(
                    workbook_path,
                    legacy.Resolver(),
                )
        self.assertEqual(
            str(framework_raised.exception),
            str(legacy_raised.exception),
        )
        self.assertIn("incompatible target", str(framework_raised.exception))

    def test_extraction_errors_translate_and_unexpected_failures_propagate(self) -> None:
        resolver = mock.Mock(spec=legacy.Resolver)
        extraction_failures = (
            XlsxAdapterError("synthetic extraction failure"),
            XlsxAdapterDependencyError("synthetic dependency failure"),
        )
        for failure in extraction_failures:
            with (
                self.subTest(error_type=type(failure).__name__),
                mock.patch.object(
                    integration,
                    "read_xlsx_source_rows",
                    side_effect=failure,
                ),
                self.assertRaises(legacy.GenerationError) as translated,
            ):
                integration.process_primary_workbook_with_coms(
                    WORKBOOK_PATH,
                    resolver,
                )
            self.assertIs(translated.exception.__cause__, failure)
            self.assertIn(type(failure).__name__, str(translated.exception))
            self.assertIn(str(failure), str(translated.exception))

        unexpected = RuntimeError("synthetic programming failure")
        with (
            mock.patch.object(
                integration,
                "read_xlsx_source_rows",
                side_effect=unexpected,
            ),
            self.assertRaises(RuntimeError) as propagated,
        ):
            integration.process_primary_workbook_with_coms(
                WORKBOOK_PATH,
                resolver,
            )
        self.assertIs(propagated.exception, unexpected)

    def test_wrapper_is_read_only_and_production_main_is_legacy(self) -> None:
        locked_paths = (WORKBOOK_PATH, *ARTIFACT_SHA256)
        hashes_before = {
            path: sha256_file(path)
            for path in locked_paths
        }
        workbook_mtime_before = WORKBOOK_PATH.stat().st_mtime_ns
        resolver = legacy.Resolver()
        forbidden = AssertionError("wrapper attempted a file write")

        original_builtin_open = builtins.open
        original_path_open = Path.open

        def guarded_builtin_open(
            file: object,
            mode: str = "r",
            *args: object,
            **kwargs: object,
        ) -> object:
            if any(flag in mode for flag in ("w", "a", "x", "+")):
                raise forbidden
            return original_builtin_open(file, mode, *args, **kwargs)

        def guarded_path_open(
            path: Path,
            mode: str = "r",
            *args: object,
            **kwargs: object,
        ) -> object:
            if any(flag in mode for flag in ("w", "a", "x", "+")):
                raise forbidden
            return original_path_open(path, mode, *args, **kwargs)

        with (
            mock.patch.object(builtins, "open", new=guarded_builtin_open),
            mock.patch.object(Path, "open", new=guarded_path_open),
            mock.patch.object(Path, "write_text", side_effect=forbidden),
            mock.patch.object(Path, "write_bytes", side_effect=forbidden),
            mock.patch.object(
                legacy.openpyxl.Workbook,
                "save",
                side_effect=forbidden,
            ),
        ):
            processed, stats = integration.process_primary_workbook_with_coms(
                WORKBOOK_PATH,
                resolver,
            )
        self.assertEqual(len(processed), 105)
        self.assertEqual(stats, self.legacy_stats)
        self.assertEqual(
            {path: sha256_file(path) for path in locked_paths},
            hashes_before,
        )
        self.assertEqual(WORKBOOK_PATH.stat().st_mtime_ns, workbook_mtime_before)

        main_source = inspect.getsource(legacy.main)
        read_index = main_source.index("rows, stats = read_workbook(input_path)")
        process_index = main_source.index(
            "processed = validate_and_process_rows(rows, resolver, stats)"
        )
        self.assertLess(read_index, process_index)
        self.assertNotIn("process_primary_workbook_with_coms", main_source)
        self.assertEqual(
            sha256_file(Path(legacy.__file__).resolve()),
            GENERATOR_SHA256,
        )
