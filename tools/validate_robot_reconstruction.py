#!/usr/bin/env python3
"""Validate exact ROBOT reconstruction of all governed COMS axioms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import robot_property_chain_generation_pilot as property_chains
import robot_reconstruction_validation as reconstruction
import robot_template_generation_pilot as template


REPO_ROOT = Path(__file__).resolve().parents[1]

GOVERNED_AXIOM_MAPPING_TYPES = frozenset(
    {
        "class_mapping",
        "object_property_mapping",
        "domain",
        "range",
        "property_chain",
    }
)


def run_validation(
    workbook_path: Path,
    output_dir: Path,
    robot_path: str | None = None,
) -> dict[str, object]:
    workbook_path = workbook_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    template_dir = output_dir / "non-chain"
    property_chain_dir = output_dir / "property-chains"

    template_summary = template.run_pilot(
        workbook_path,
        template_dir,
        robot_path,
    )
    property_chain_summary = property_chains.run_pilot(
        workbook_path,
        property_chain_dir,
        robot_path,
    )

    governed = reconstruction.load_governed_coms_rows(
        workbook_path,
    )
    expected = reconstruction.canonical_expected_axioms(
        governed.processed_rows,
        GOVERNED_AXIOM_MAPPING_TYPES,
    )

    template_actual = reconstruction.canonical_axioms_from_turtle(
        template.artifact_paths(template_dir).output_path,
    )
    property_chain_actual = reconstruction.canonical_axioms_from_turtle(
        property_chains.artifact_paths(property_chain_dir).output_path,
    )

    overlap = tuple(
        sorted(
            set(template_actual)
            & set(property_chain_actual)
        )
    )

    actual = dict(template_actual)
    for axiom_id, canonical in property_chain_actual.items():
        previous = actual.get(axiom_id)
        if previous is not None and previous != canonical:
            raise ValueError(
                f"ROBOT reconstruction axiom collision for {axiom_id}"
            )
        actual[axiom_id] = canonical

    comparison = reconstruction.compare_canonical_axioms(
        expected,
        actual,
    )

    passed = (
        bool(template_summary["passed"])
        and bool(property_chain_summary["passed"])
        and len(governed.processed_rows) == 105
        and len(template_actual) == 100
        and len(property_chain_actual) == 5
        and len(expected) == 105
        and len(actual) == 105
        and not overlap
        and comparison.passed
    )

    summary: dict[str, object] = {
        "passed": passed,
        "workbook": str(workbook_path),
        "governed_row_count": len(governed.processed_rows),
        "non_chain_reconstruction_passed": bool(
            template_summary["passed"]
        ),
        "property_chain_reconstruction_passed": bool(
            property_chain_summary["passed"]
        ),
        "non_chain_axiom_count": len(template_actual),
        "property_chain_axiom_count": len(property_chain_actual),
        "expected_axiom_count": len(expected),
        "actual_axiom_count": len(actual),
        "overlapping_axiom_ids": list(overlap),
        "missing_axiom_ids": list(
            comparison.missing_axiom_ids
        ),
        "extra_axiom_ids": list(
            comparison.extra_axiom_ids
        ),
        "mismatched_axiom_ids": list(
            comparison.mismatched_axiom_ids
        ),
        "robot_path": template_summary["robot_path"],
        "non_chain_robot_return_code": template_summary[
            "robot_return_code"
        ],
        "property_chain_robot_return_code": property_chain_summary[
            "robot_return_code"
        ],
    }

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(
            REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"
        ),
        help="Governed COMS workbook.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for temporary validation artifacts.",
    )
    parser.add_argument(
        "--robot",
        help="Optional explicit ROBOT executable path.",
    )
    args = parser.parse_args(argv)

    summary = run_validation(
        Path(args.input),
        Path(args.output_dir),
        args.robot,
    )

    print(f"Governed rows: {summary['governed_row_count']}")
    print(
        "Non-chain ROBOT axioms: "
        f"{summary['non_chain_axiom_count']}"
    )
    print(
        "Property-chain ROBOT axioms: "
        f"{summary['property_chain_axiom_count']}"
    )
    print(
        "Expected canonical axioms: "
        f"{summary['expected_axiom_count']}"
    )
    print(
        "Combined ROBOT canonical axioms: "
        f"{summary['actual_axiom_count']}"
    )
    print(
        "Overlapping backend axioms: "
        f"{len(summary['overlapping_axiom_ids'])}"
    )
    print(
        f"Missing axioms: {len(summary['missing_axiom_ids'])}"
    )
    print(
        f"Extra axioms: {len(summary['extra_axiom_ids'])}"
    )
    print(
        "Mismatched axioms: "
        f"{len(summary['mismatched_axiom_ids'])}"
    )
    print(
        "Summary: PASS"
        if summary["passed"]
        else "Summary: FAIL"
    )

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
