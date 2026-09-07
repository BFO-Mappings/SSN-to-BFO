#!/usr/bin/env python3
"""Shared helpers for independent ROBOT reconstruction of governed COMS axioms."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rdflib import Graph

import generate_mapping_from_coms as coms
import modular_products as modular
from coms_row_identity import CanonicalRowInput


@dataclass(frozen=True)
class GovernedComsRows:
    processed_rows: tuple[coms.ProcessedRow, ...]
    canonical_rows: tuple[CanonicalRowInput, ...]


@dataclass(frozen=True)
class CanonicalAxiomComparison:
    expected: dict[str, str]
    actual: dict[str, str]
    missing_axiom_ids: tuple[str, ...]
    extra_axiom_ids: tuple[str, ...]
    mismatched_axiom_ids: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return (
            not self.missing_axiom_ids
            and not self.extra_axiom_ids
            and not self.mismatched_axiom_ids
        )


def load_governed_coms_rows(workbook_path: Path) -> GovernedComsRows:
    """Load and fully validate the governed COMS workbook once."""

    workbook_rows, stats = coms.read_workbook(workbook_path.resolve())
    processed_rows = tuple(
        coms.validate_and_process_rows(
            workbook_rows,
            coms.Resolver(),
            stats,
        )
    )
    canonical_rows = tuple(
        coms.canonical_input_for_processed_row(row)
        for row in processed_rows
    )
    return GovernedComsRows(
        processed_rows=processed_rows,
        canonical_rows=canonical_rows,
    )


def canonical_expected_axioms(
    processed_rows: Iterable[coms.ProcessedRow],
    mapping_types: Iterable[str],
) -> dict[str, str]:
    """Return authoritative canonical axioms for the selected mapping types."""

    selected_types = frozenset(mapping_types)
    expected: dict[str, str] = {}

    for processed in processed_rows:
        row = coms.canonical_input_for_processed_row(processed)
        if row.mapping_type not in selected_types:
            continue
        if processed.identity_audit is None:
            raise ValueError(
                f"{row.row_id}: canonical identity audit is missing"
            )

        for identity in processed.identity_audit.authoritative_axioms:
            axiom_id = (
                "sha256:"
                + hashlib.sha256(
                    identity.canonical_axiom.encode("utf-8")
                ).hexdigest()
            )
            previous = expected.get(axiom_id)
            if previous is not None and previous != identity.canonical_axiom:
                raise ValueError(
                    f"{row.row_id}: canonical axiom hash collision"
                )
            expected[axiom_id] = identity.canonical_axiom

    return expected


def canonical_axioms_from_turtle(path: Path) -> dict[str, str]:
    """Canonicalize supported OWL axioms from a ROBOT-produced Turtle graph."""

    graph = Graph().parse(path, format="turtle")
    return {
        axiom_id: value[0]
        for axiom_id, value in modular._canonical_graph_axioms(
            graph,
            ignore_unsupported=True,
        ).items()
    }


def compare_canonical_axioms(
    expected: dict[str, str],
    actual: dict[str, str],
) -> CanonicalAxiomComparison:
    """Compare exact canonical axiom identities and expressions."""

    shared = set(expected) & set(actual)
    return CanonicalAxiomComparison(
        expected=expected,
        actual=actual,
        missing_axiom_ids=tuple(sorted(set(expected) - set(actual))),
        extra_axiom_ids=tuple(sorted(set(actual) - set(expected))),
        mismatched_axiom_ids=tuple(
            sorted(
                axiom_id
                for axiom_id in shared
                if expected[axiom_id] != actual[axiom_id]
            )
        ),
    )


def resolve_robot_path(robot_path: str | None = None) -> str:
    """Return the explicit or PATH-resolved ROBOT executable."""

    resolved = robot_path or shutil.which("robot")
    if resolved is None:
        raise RuntimeError("ROBOT executable not found on PATH")
    return resolved


def combined_process_output(stdout: str, stderr: str) -> str:
    """Combine subprocess output using the repository's existing convention."""

    return "\n".join(
        part
        for part in (
            stdout.strip(),
            stderr.strip(),
        )
        if part
    )
