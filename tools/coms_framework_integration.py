#!/usr/bin/env python3
"""Project-local configuration, adapters, and temporary COMS projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

from coms.adapters.xlsx import (
    WorkbookSourceRow,
    XlsxAdapterDependencyError,
    XlsxAdapterError,
    read_xlsx_source_rows,
)
from coms.config import HeaderBinding, WorkbookProfile
from coms.mapping_expression import ExpressionNode
from coms.mapping_parser import EntityResolutionError, MappingParseError
from coms.mapping_predicates import MappingPredicateTokenError
from coms.mapping_record_builder import MappingRecordBuildError
from coms.row_identity import (
    CanonicalRowAudit as FrameworkCanonicalRowAudit,
    ComsRowIdentityError as FrameworkRowIdentityError,
)
from coms.workbook_batch import (
    AuditedWorkbookRow,
    build_governed_workbook_batch,
    validate_workbook_source_row_ids,
)
from coms.workbook_mapping import (
    ResolvedSourceEntity,
    WorkbookMappingError,
)
from rdflib import URIRef

import coms_row_identity as legacy_identity
import generate_mapping_from_coms as legacy


PRIMARY_WORKBOOK_PROFILE = WorkbookProfile(
    workbook_path="mappings/SSN2BFO-COMS.xlsx",
    sheet_selectors=("Sheet1", "Sheet2"),
    header_bindings=(
        HeaderBinding(field="source", column="sssom:subject_id"),
        HeaderBinding(field="predicate", column="sssom:predicate_id"),
        HeaderBinding(field="target", column="coms:Target"),
        HeaderBinding(field="reasoning", column="coms:Reasoning"),
        HeaderBinding(field="row_id", column="coms:RowID"),
    ),
    required_columns=(
        "sssom:subject_id",
        "sssom:predicate_id",
        "coms:Target",
        "coms:Reasoning",
        "coms:RowID",
    ),
    row_id_column="coms:RowID",
    explicit_blank_representation="blank predicate and blank target",
)

_EXPECTED_FRAMEWORK_FAILURES = (
    XlsxAdapterDependencyError,
    XlsxAdapterError,
    MappingPredicateTokenError,
    EntityResolutionError,
    MappingParseError,
    MappingRecordBuildError,
    FrameworkRowIdentityError,
    WorkbookMappingError,
)


def _diagnostic_id(row: WorkbookSourceRow) -> str:
    suffix = f" [{row.row_id_text}]" if row.row_id_text else ""
    return f"{row.location.text}{suffix}"


class SsnWorkbookResolutionContext:
    """Maintain explicit row context for one ordered COMS semantic batch."""

    def __init__(self, rows: Iterable[WorkbookSourceRow]) -> None:
        self._rows = tuple(rows)
        self._next_row_index = 0
        self._current_row: WorkbookSourceRow | None = None
        self._source_kind_by_row_id: dict[str, str] = {}

    def begin_source_resolution(self, token: str) -> str:
        """Advance to the next row after verifying its source token."""

        if self._next_row_index >= len(self._rows):
            raise legacy.GenerationError(
                "COMS source resolver received more calls than the configured workbook rows"
            )

        row = self._rows[self._next_row_index]
        diagnostic_id = _diagnostic_id(row)
        expected_token = row.subject_text.strip()
        if token != expected_token:
            raise legacy.GenerationError(
                f"{diagnostic_id}: COMS source resolver received {token!r}; "
                f"expected {expected_token!r} for the next workbook row"
            )

        self._current_row = row
        self._next_row_index += 1
        return diagnostic_id

    @property
    def current_diagnostic_id(self) -> str:
        if self._current_row is None:
            raise legacy.GenerationError(
                "COMS target resolver was called before source-row context was established"
            )
        return _diagnostic_id(self._current_row)

    def retain_source_kind(self, kind: str) -> None:
        if self._current_row is None:
            raise legacy.GenerationError(
                "COMS source kind cannot be retained before row context is established"
            )
        row_id = self._current_row.row_id_text
        if row_id in self._source_kind_by_row_id:
            raise legacy.GenerationError(
                f"{self.current_diagnostic_id}: source kind was already retained"
            )
        self._source_kind_by_row_id[row_id] = kind

    @property
    def source_kind_by_row_id(self) -> Mapping[str, str]:
        """Return a read-only snapshot of source kinds retained during resolution."""

        return MappingProxyType(dict(self._source_kind_by_row_id))

    def assert_complete(self) -> None:
        """Require exactly one completed source-resolution call for every row."""

        if self._next_row_index != len(self._rows):
            raise legacy.GenerationError(
                "COMS source resolver consumed "
                f"{self._next_row_index} of {len(self._rows)} configured workbook rows"
            )
        if len(self._source_kind_by_row_id) != len(self._rows):
            raise legacy.GenerationError(
                "COMS source resolver did not retain one source kind per workbook row"
            )


class SsnSourceResolverAdapter:
    """Expose the existing SSN source resolver through the COMS contract."""

    def __init__(
        self,
        resolver: legacy.Resolver,
        *,
        diagnostic_context: str = "COMS shadow integration",
        row_context: SsnWorkbookResolutionContext | None = None,
    ) -> None:
        self._resolver = resolver
        self._diagnostic_context = diagnostic_context
        self._row_context = row_context

    def resolve_source_entity(self, token: str) -> ResolvedSourceEntity:
        diagnostic_context = self._diagnostic_context
        if self._row_context is not None:
            diagnostic_context = self._row_context.begin_source_resolution(token)
        iri, kind = self._resolver.resolve_source_subject(
            token,
            diagnostic_context,
        )
        if self._row_context is not None:
            self._row_context.retain_source_kind(kind)
        return ResolvedSourceEntity(iri=str(iri), kind=kind)


class SsnTargetResolverAdapter:
    """Expose the existing SSN target resolver through the COMS contract."""

    def __init__(
        self,
        resolver: legacy.Resolver,
        *,
        diagnostic_context: str = "COMS shadow integration",
        row_context: SsnWorkbookResolutionContext | None = None,
    ) -> None:
        self._resolver = resolver
        self._diagnostic_context = diagnostic_context
        self._row_context = row_context

    def resolve_entity(self, token: str, expected_kind: str) -> str:
        diagnostic_context = self._diagnostic_context
        if self._row_context is not None:
            diagnostic_context = self._row_context.current_diagnostic_id
        try:
            resolution = self._resolver.resolve(
                token,
                expected_kind,
                diagnostic_context,
            )
        except legacy.GenerationError as exc:
            raise EntityResolutionError(str(exc)) from exc
        return str(resolution.iri)


def project_workbook_source_row(row: WorkbookSourceRow) -> legacy.WorkbookRow:
    """Copy a COMS source row into the temporary legacy row representation."""

    return legacy.WorkbookRow(
        sheet=row.location.worksheet,
        row_number=row.location.row_number,
        subject_text=row.subject_text,
        predicate_text=row.predicate_text,
        target_text=row.target_text,
        reasoning_text=row.reasoning_text,
        stable_row_id=row.row_id_text,
        mapping_status_text=row.status_text or "",
    )


def project_expression_node(node: ExpressionNode | None) -> legacy.Expr | None:
    """Project a resolved COMS expression without reparsing or canonicalizing it."""

    if node is None:
        return None
    return _project_expression_node(node)


def _project_expression_node(node: ExpressionNode) -> legacy.Expr:
    if node.kind == "named":
        if node.iri is None:
            raise legacy.GenerationError("COMS named expression lacks an IRI")
        return legacy.Expr(kind="named", iri=URIRef(node.iri))
    if node.kind in {"intersection", "union"}:
        return legacy.Expr(
            kind=node.kind,
            children=tuple(
                _project_expression_node(child)
                for child in node.children
            ),
        )
    if node.kind == "some":
        if node.property_iri is None or node.filler is None:
            raise legacy.GenerationError(
                "COMS existential expression lacks a property or filler"
            )
        return legacy.Expr(
            kind="some",
            prop=URIRef(node.property_iri),
            filler=_project_expression_node(node.filler),
        )
    raise legacy.GenerationError(
        f"unsupported COMS expression node kind {node.kind!r}"
    )


def project_canonical_row_audit(
    audit: FrameworkCanonicalRowAudit,
) -> legacy_identity.CanonicalRowAudit:
    """Copy COMS canonical identity values into the legacy runtime types."""

    return legacy_identity.CanonicalRowAudit(
        row_id=audit.row_id,
        location=legacy_identity.RowLocation(
            worksheet=audit.location.worksheet,
            row_number=audit.location.row_number,
        ),
        reasoning=audit.reasoning,
        expression=legacy_identity.CanonicalRowExpression(
            canonicalization=audit.expression.canonicalization,
            mapping_type=audit.expression.mapping_type,
            predicate_iri=audit.expression.predicate_iri,
            subject_iri=audit.expression.subject_iri,
            target=audit.expression.target,
        ),
        source_expression_sha256=audit.source_expression_sha256,
        authoritative_axioms=tuple(
            legacy_identity.AuthoritativeAxiomIdentity(
                canonical_axiom=axiom.canonical_axiom,
                sha256=axiom.sha256,
            )
            for axiom in audit.authoritative_axioms
        ),
    )


def project_audited_workbook_rows(
    audited_rows: Iterable[AuditedWorkbookRow],
    source_kind_by_row_id: Mapping[str, str],
) -> list[legacy.ProcessedRow]:
    """Mechanically project audited COMS rows into the legacy downstream shape."""

    projected_rows: list[legacy.ProcessedRow] = []
    for audited_row in audited_rows:
        source_row = audited_row.source_row
        record = audited_row.governed_record
        audit = audited_row.row_audit
        row_id = source_row.row_id_text
        diagnostic_id = _diagnostic_id(source_row)

        if record.row_id != row_id or audit.row_id != row_id:
            raise legacy.GenerationError(
                f"{diagnostic_id}: COMS source, semantic record, and audit RowIDs differ"
            )
        if (
            audit.location.worksheet != source_row.location.worksheet
            or audit.location.row_number != source_row.location.row_number
        ):
            raise legacy.GenerationError(
                f"{diagnostic_id}: COMS source and audit locations differ"
            )
        try:
            subject_kind = source_kind_by_row_id[row_id]
        except KeyError:
            raise legacy.GenerationError(
                f"{diagnostic_id}: source-kind sidecar entry is missing"
            ) from None

        projected_rows.append(
            legacy.ProcessedRow(
                row=project_workbook_source_row(source_row),
                subject=URIRef(record.subject_iri),
                subject_kind=subject_kind,
                predicate=source_row.predicate_text,
                target=source_row.target_text,
                expr=project_expression_node(record.expression),
                target_property=(
                    None
                    if record.target_property_iri is None
                    else URIRef(record.target_property_iri)
                ),
                property_chain=tuple(
                    URIRef(iri)
                    for iri in record.property_chain
                ),
                identity_audit=project_canonical_row_audit(audit),
            )
        )

    return projected_rows


def _validate_primary_domain_range_policy_compat(
    processed_rows: Iterable[legacy.ProcessedRow],
) -> None:
    """Temporarily mirror the inline primary SSN domain/range authoring rule.

    This project-only compatibility helper avoids changing the provenance-bearing
    generator before the authorized Commit 3 cutover. Commit 3 must consolidate
    this rule into one shared project-policy authority.
    """

    first_by_key: dict[tuple[str, str], legacy.ProcessedRow] = {}
    for item in processed_rows:
        if item.predicate not in legacy.DOMAIN_RANGE_PREDICATES:
            continue
        key = (str(item.subject), item.predicate)
        previous = first_by_key.get(key)
        if previous is None:
            first_by_key[key] = item
            continue
        axiom_name = "domain" if item.predicate == "rdfs:domain" else "range"
        raise legacy.GenerationError(
            f"{item.row.diagnostic_id}: duplicate {item.predicate} row for "
            f"{item.row.subject_text}; the first {axiom_name} row is "
            f"{previous.row.diagnostic_id}. Multiple OWL {axiom_name} axioms "
            "are conjunctive; write alternatives with Manchester 'or' in one "
            "target expression."
        )


def _framework_failure_message(error: Exception) -> str:
    parts = [f"{type(error).__name__}: {error}"]
    parts.extend(str(note) for note in getattr(error, "__notes__", ()))
    return " | ".join(parts)


def _derive_primary_workbook_stats(
    profile: WorkbookProfile,
    source_rows: tuple[WorkbookSourceRow, ...],
    audited_rows: tuple[AuditedWorkbookRow, ...],
    processed_rows: list[legacy.ProcessedRow],
) -> legacy.WorkbookStats:
    """Reproduce legacy primary-workbook statistics from COMS batch results."""

    stats = legacy.WorkbookStats()
    stats.worksheets_read = list(profile.sheet_selectors)
    seen_sheets = set(stats.worksheets_read)

    for row in source_rows:
        sheet = row.location.worksheet
        if sheet not in seen_sheets:
            stats.worksheets_read.append(sheet)
            seen_sheets.add(sheet)
        stats.rows_by_sheet[sheet] = max(
            stats.rows_by_sheet[sheet],
            row.location.row_number - 1,
        )
        stats.populated_rows_by_sheet[sheet] += 1

    mapping_types = Counter(
        item.governed_record.mapping_type
        for item in audited_rows
    )
    stats.class_mapping_rows = mapping_types["class_mapping"]
    stats.object_property_mapping_rows = mapping_types["object_property_mapping"]
    stats.property_chain_rows = mapping_types["property_chain"]
    stats.domain_rows = mapping_types["domain"]
    stats.range_rows = mapping_types["range"]
    stats.blank_mapping_rows = mapping_types["explicit_blank"]
    stats.mapped_rows = (
        stats.class_mapping_rows
        + stats.object_property_mapping_rows
        + stats.property_chain_rows
    )
    stats.governed_row_id_count = len(source_rows)
    stats.unique_row_id_count = len({row.row_id_text for row in source_rows})
    stats.processed_row_count = len(processed_rows)

    identity_audits = tuple(
        item.identity_audit
        for item in processed_rows
        if item.identity_audit is not None
    )
    stats.identity_audit_row_count = len(identity_audits)
    legacy.validate_identity_audit_completeness(
        [project_workbook_source_row(row) for row in source_rows],
        processed_rows,
        identity_audits,
    )
    stats.identity_count_reconciliation_passed = True
    stats.identity_row_id_set_reconciliation_passed = True
    stats.identity_location_reconciliation_passed = True
    return stats


def process_primary_workbook_with_coms(
    workbook_path: Path,
    resolver: legacy.Resolver,
) -> tuple[list[legacy.ProcessedRow], legacy.WorkbookStats]:
    """Process the primary SSN workbook through COMS without writing outputs."""

    profile = replace(
        PRIMARY_WORKBOOK_PROFILE,
        workbook_path=str(workbook_path),
    )
    try:
        source_rows = read_xlsx_source_rows(
            profile,
            base_directory=legacy.REPO_ROOT,
        )
        validate_workbook_source_row_ids(source_rows)

        row_context = SsnWorkbookResolutionContext(source_rows)
        audited_rows = build_governed_workbook_batch(
            source_rows,
            SsnSourceResolverAdapter(
                resolver,
                row_context=row_context,
            ),
            SsnTargetResolverAdapter(
                resolver,
                row_context=row_context,
            ),
        )
        row_context.assert_complete()
        processed_rows = project_audited_workbook_rows(
            audited_rows,
            row_context.source_kind_by_row_id,
        )
    except _EXPECTED_FRAMEWORK_FAILURES as exc:
        raise legacy.GenerationError(
            _framework_failure_message(exc)
        ) from exc

    _validate_primary_domain_range_policy_compat(processed_rows)
    legacy.validate_incompatible_duplicate_mappings(processed_rows)
    stats = _derive_primary_workbook_stats(
        profile,
        source_rows,
        audited_rows,
        processed_rows,
    )
    return processed_rows, stats
