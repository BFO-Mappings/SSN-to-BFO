#!/usr/bin/env python3
"""Project-local configuration and adapters for shadow COMS integration."""

from __future__ import annotations

from coms.config import HeaderBinding, WorkbookProfile
from coms.mapping_parser import EntityResolutionError
from coms.workbook_mapping import ResolvedSourceEntity

from generate_mapping_from_coms import GenerationError, Resolver


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


class SsnSourceResolverAdapter:
    """Expose the existing SSN source resolver through the COMS contract."""

    def __init__(
        self,
        resolver: Resolver,
        *,
        diagnostic_context: str = "COMS shadow integration",
    ) -> None:
        self._resolver = resolver
        self._diagnostic_context = diagnostic_context

    def resolve_source_entity(self, token: str) -> ResolvedSourceEntity:
        iri, kind = self._resolver.resolve_source_subject(
            token,
            self._diagnostic_context,
        )
        return ResolvedSourceEntity(iri=str(iri), kind=kind)


class SsnTargetResolverAdapter:
    """Expose the existing SSN target resolver through the COMS contract."""

    def __init__(
        self,
        resolver: Resolver,
        *,
        diagnostic_context: str = "COMS shadow integration",
    ) -> None:
        self._resolver = resolver
        self._diagnostic_context = diagnostic_context

    def resolve_entity(self, token: str, expected_kind: str) -> str:
        try:
            resolution = self._resolver.resolve(
                token,
                expected_kind,
                self._diagnostic_context,
            )
        except GenerationError as exc:
            raise EntityResolutionError(str(exc)) from exc
        return str(resolution.iri)
