#!/usr/bin/env python3
"""Validate governed COMS property chains through ROBOT and OWL Functional Syntax."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import robot_reconstruction_validation as reconstruction
from coms_row_identity import CanonicalRowInput


REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_ONTOLOGY_IRI = (
    "http://www.sks.ai/SSN2BFO/pilots/robot-property-chain-normalized"
)


@dataclass(frozen=True)
class PilotArtifacts:
    functional_syntax_path: Path
    output_path: Path
    summary_path: Path


def functional_iri(value: str) -> str:
    """Render one already-resolved IRI for OWL Functional Syntax."""

    if (
        not value
        or any(character.isspace() for character in value)
        or any(character in value for character in '<>"{}|^`\\')
    ):
        raise ValueError(f"cannot render Functional Syntax IRI {value!r}")
    return f"<{value}>"


def select_property_chain_rows(
    rows: Iterable[CanonicalRowInput],
) -> tuple[CanonicalRowInput, ...]:
    selected = tuple(
        sorted(
            (
                row
                for row in rows
                if row.mapping_type == "property_chain"
            ),
            key=lambda row: row.row_id,
        )
    )

    for row in selected:
        if not row.property_chain:
            raise ValueError(
                f"{row.row_id}: property-chain row has no members"
            )
        if len(row.property_chain) < 2:
            raise ValueError(
                f"{row.row_id}: property chain must contain at least two members"
            )

    return selected


def write_functional_syntax(
    rows: Iterable[CanonicalRowInput],
    path: Path,
) -> tuple[CanonicalRowInput, ...]:
    selected = select_property_chain_rows(rows)

    declared_properties = sorted(
        {
            row.subject_iri
            for row in selected
        }
        | {
            member
            for row in selected
            for member in row.property_chain
        }
    )

    lines = [
        f"Ontology({functional_iri(PILOT_ONTOLOGY_IRI)}",
    ]

    for property_iri in declared_properties:
        lines.append(
            "  Declaration("
            f"ObjectProperty({functional_iri(property_iri)})"
            ")"
        )

    if declared_properties and selected:
        lines.append("")

    for index, row in enumerate(selected):
        members = " ".join(
            functional_iri(member)
            for member in row.property_chain
        )
        lines.extend(
            [
                "  SubObjectPropertyOf(",
                f"    ObjectPropertyChain({members})",
                f"    {functional_iri(row.subject_iri)}",
                "  )",
            ]
        )
        if index + 1 < len(selected):
            lines.append("")

    lines.append(")")
    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return selected


def artifact_paths(output_dir: Path) -> PilotArtifacts:
    return PilotArtifacts(
        functional_syntax_path=output_dir / "normalized-property-chains.ofn",
        output_path=output_dir / "robot-property-chains.ttl",
        summary_path=output_dir / "summary.json",
    )


def run_pilot(
    workbook_path: Path,
    output_dir: Path,
    robot_path: str | None = None,
) -> dict[str, object]:
    workbook_path = workbook_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = artifact_paths(output_dir)

    governed = reconstruction.load_governed_coms_rows(
        workbook_path,
    )
    processed = governed.processed_rows
    canonical_rows = governed.canonical_rows

    selected = write_functional_syntax(
        canonical_rows,
        artifacts.functional_syntax_path,
    )

    artifacts.output_path.unlink(missing_ok=True)

    robot = reconstruction.resolve_robot_path(robot_path)

    completed = subprocess.run(
        [
            robot,
            "convert",
            "--strict",
            "--input",
            str(artifacts.functional_syntax_path),
            "--format",
            "ttl",
            "--output",
            str(artifacts.output_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    expected = reconstruction.canonical_expected_axioms(
        processed,
        {"property_chain"},
    )
    actual: dict[str, str] = {}

    if artifacts.output_path.exists():
        actual = reconstruction.canonical_axioms_from_turtle(
            artifacts.output_path,
        )

    comparison = reconstruction.compare_canonical_axioms(
        expected,
        actual,
    )
    missing = list(comparison.missing_axiom_ids)
    extra = list(comparison.extra_axiom_ids)
    mismatched = list(comparison.mismatched_axiom_ids)

    passed = (
        completed.returncode == 0
        and len(selected) == 5
        and len(expected) == 5
        and len(actual) == 5
        and comparison.passed
    )

    summary: dict[str, object] = {
        "passed": passed,
        "robot_path": robot,
        "robot_return_code": completed.returncode,
        "robot_output": reconstruction.combined_process_output(
            completed.stdout,
            completed.stderr,
        ),
        "workbook": str(workbook_path),
        "governed_row_count": len(processed),
        "attempted_property_chain_rows": len(selected),
        "expected_axiom_count": len(expected),
        "actual_axiom_count": len(actual),
        "missing_axiom_ids": missing,
        "extra_axiom_ids": extra,
        "mismatched_axiom_ids": mismatched,
        "declared_property_count": len(
            {
                row.subject_iri
                for row in selected
            }
            | {
                member
                for row in selected
                for member in row.property_chain
            }
        ),
        "functional_syntax_sha256": hashlib.sha256(
            artifacts.functional_syntax_path.read_bytes()
        ).hexdigest(),
    }

    artifacts.summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"),
        help="Governed COMS workbook.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for temporary pilot artifacts.",
    )
    parser.add_argument(
        "--robot",
        help="Optional explicit ROBOT executable path.",
    )
    args = parser.parse_args(argv)

    summary = run_pilot(
        Path(args.input),
        Path(args.output_dir),
        args.robot,
    )

    print(f"Governed rows: {summary['governed_row_count']}")
    print(
        "Attempted property-chain rows: "
        f"{summary['attempted_property_chain_rows']}"
    )
    print(f"Expected canonical axioms: {summary['expected_axiom_count']}")
    print(f"ROBOT canonical axioms: {summary['actual_axiom_count']}")
    print(f"ROBOT return code: {summary['robot_return_code']}")
    print(f"Missing axioms: {len(summary['missing_axiom_ids'])}")
    print(f"Extra axioms: {len(summary['extra_axiom_ids'])}")
    print(f"Mismatched axioms: {len(summary['mismatched_axiom_ids'])}")
    print("Summary: PASS" if summary["passed"] else "Summary: FAIL")

    if summary["robot_output"]:
        print(summary["robot_output"])

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
