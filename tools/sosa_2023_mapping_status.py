#!/usr/bin/env python3
"""Authoritative SOSA-2023 COMS mapping-status classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, Sequence, TypeVar


ACTIVE = "active"
DEFERRED = "deferred"
NO_DIRECT_MAPPING = "no_direct_mapping"
UNREVIEWED = "unreviewed"

ALLOWED_MAPPING_STATUSES = frozenset(
    {
        ACTIVE,
        DEFERRED,
        NO_DIRECT_MAPPING,
        UNREVIEWED,
    }
)


class GovernedMappingStatusRow(Protocol):
    subject_text: str
    predicate_text: str
    target_text: str
    reasoning_text: str
    mapping_status_text: str

    @property
    def diagnostic_id(self) -> str:
        ...


RowT = TypeVar(
    "RowT",
    bound=GovernedMappingStatusRow,
)


class MappingStatusError(ValueError):
    """Raised when a governed row violates MappingStatus semantics."""


@dataclass(frozen=True)
class MappingStatusClassification(Generic[RowT]):
    active: tuple[RowT, ...]
    deferred: tuple[RowT, ...]
    no_direct_mapping: tuple[RowT, ...]
    unreviewed: tuple[RowT, ...]

    @property
    def governed_row_count(self) -> int:
        return (
            len(self.active)
            + len(self.deferred)
            + len(self.no_direct_mapping)
            + len(self.unreviewed)
        )

    @property
    def legacy_explicitly_unmapped(self) -> tuple[RowT, ...]:
        """Compatibility view for pre-MappingStatus SOSA-2023 callers."""

        by_identity = {
            id(row)
            for row in (
                *self.no_direct_mapping,
                *self.unreviewed,
            )
        }

        return tuple(
            row
            for group in (
                self.no_direct_mapping,
                self.unreviewed,
            )
            for row in group
            if id(row) in by_identity
        )


def _error(
    row: GovernedMappingStatusRow,
    message: str,
) -> MappingStatusError:
    return MappingStatusError(
        f"{row.diagnostic_id}: {message}"
    )


def classify_workbook_rows(
    rows: Sequence[RowT],
) -> MappingStatusClassification[RowT]:
    """Classify rows solely from explicit coms:MappingStatus values."""

    active: list[RowT] = []
    deferred: list[RowT] = []
    no_direct_mapping: list[RowT] = []
    unreviewed: list[RowT] = []

    for row in rows:
        if not row.subject_text:
            raise _error(
                row,
                "governed row requires a source subject",
            )

        status = row.mapping_status_text

        if not status:
            raise _error(
                row,
                "coms:MappingStatus is required for every "
                "SOSA-2023 governed row",
            )

        if status not in ALLOWED_MAPPING_STATUSES:
            raise _error(
                row,
                "unknown coms:MappingStatus "
                f"{status!r}; expected one of "
                f"{sorted(ALLOWED_MAPPING_STATUSES)!r}",
            )

        has_predicate = bool(
            row.predicate_text
        )

        has_target = bool(
            row.target_text
        )

        if has_predicate != has_target:
            raise _error(
                row,
                "predicate and target must either both be populated "
                "or both be blank",
            )

        if status == ACTIVE:
            if not has_predicate:
                raise _error(
                    row,
                    "active status requires a populated predicate "
                    "and target",
                )

            active.append(row)
            continue

        if has_predicate:
            raise _error(
                row,
                f"{status} status requires blank predicate and target",
            )

        if status == DEFERRED:
            if not row.reasoning_text:
                raise _error(
                    row,
                    "deferred status requires coms:Reasoning "
                    "explaining the unresolved decision",
                )

            deferred.append(row)
            continue

        if status == NO_DIRECT_MAPPING:
            if not row.reasoning_text:
                raise _error(
                    row,
                    "no_direct_mapping status requires "
                    "coms:Reasoning documenting the final decision",
                )

            no_direct_mapping.append(row)
            continue

        if row.reasoning_text:
            raise _error(
                row,
                "unreviewed status requires blank coms:Reasoning; "
                "reviewed zero-axiom rows must be deferred or "
                "no_direct_mapping",
            )

        unreviewed.append(row)

    result = MappingStatusClassification(
        active=tuple(active),
        deferred=tuple(deferred),
        no_direct_mapping=tuple(
            no_direct_mapping
        ),
        unreviewed=tuple(unreviewed),
    )

    if result.governed_row_count != len(rows):
        raise RuntimeError(
            "SOSA-2023 MappingStatus classification "
            "did not reconcile all governed rows"
        )

    return result
