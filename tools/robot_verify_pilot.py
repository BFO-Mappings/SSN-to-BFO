#!/usr/bin/env python3
"""Validate governed zero- and one-violation behavior with read-only ROBOT verify."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph, Literal
from rdflib.compare import isomorphic

import generate_mapping_from_coms as coms
import robot_query_equivalence_pilot as query_pilot
import robot_reconstruction_validation as reconstruction


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VIOLATION_STATUS = "absent_from_spreadsheet"
EXPECTED_REPORT_NAME = "unmapped-source-terms.csv"


@dataclass(frozen=True)
class PilotArtifacts:
    passing_graph_path: Path
    violating_graph_path: Path
    passing_report_dir: Path
    violating_report_dir: Path
    summary_path: Path


@dataclass(frozen=True)
class VerifyResult:
    return_code: int
    output: str
    report_files: tuple[Path, ...]


def artifact_paths(output_dir: Path) -> PilotArtifacts:
    return PilotArtifacts(
        passing_graph_path=output_dir / "coverage-graph-pass.ttl",
        violating_graph_path=output_dir / "coverage-graph-one-violation.ttl",
        passing_report_dir=output_dir / "pass-reports",
        violating_report_dir=output_dir / "fail-reports",
        summary_path=output_dir / "summary.json",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_robot_verify(
    robot: str,
    input_path: Path,
    report_dir: Path,
) -> VerifyResult:
    shutil.rmtree(report_dir, ignore_errors=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [
            robot,
            "verify",
            "--input",
            str(input_path),
            "--queries",
            str(query_pilot.UNMAPPED_QUERY),
            "--output-dir",
            str(report_dir),
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    report_files = tuple(
        sorted(
            (
                path
                for path in report_dir.iterdir()
                if path.is_file()
            ),
            key=lambda path: path.name,
        )
    )

    return VerifyResult(
        return_code=completed.returncode,
        output=reconstruction.combined_process_output(
            completed.stdout,
            completed.stderr,
        ),
        report_files=report_files,
    )


def build_governed_coverage_graph(
    processed_rows: tuple[coms.ProcessedRow, ...],
) -> Graph:
    source_graph = coms.build_source_graph()
    source_rows = coms.run_select_query(
        source_graph,
        query_pilot.SOURCE_QUERY,
    )
    return query_pilot.build_coverage_graph(
        processed_rows,
        source_rows,
    )


def build_controlled_violation(
    coverage_graph: Graph,
) -> tuple[Graph, str]:
    candidates = sorted(
        subject
        for subject, _, _ in coverage_graph.triples(
            (
                None,
                coms.COMS_COVERAGE.coverageStatus,
                Literal("mapped"),
            )
        )
    )
    if not candidates:
        raise RuntimeError(
            "No mapped coverage term is available for a controlled violation"
        )

    selected = candidates[0]

    violating_graph = Graph()
    coms.bind_prefixes(violating_graph)
    violating_graph.bind("coms", coms.COMS_COVERAGE)

    for triple in coverage_graph:
        violating_graph.add(triple)

    violating_graph.remove(
        (
            selected,
            coms.COMS_COVERAGE.coverageStatus,
            Literal("mapped"),
        )
    )
    violating_graph.add(
        (
            selected,
            coms.COMS_COVERAGE.coverageStatus,
            Literal(EXPECTED_VIOLATION_STATUS),
        )
    )

    return violating_graph, str(selected)


def read_report_rows(
    path: Path,
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    if not path.is_file() or path.stat().st_size == 0:
        return (), ()

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = tuple(
            tuple(
                (row.get(column) or "")
                for column in query_pilot.UNMAPPED_COLUMNS
            )
            for row in reader
        )

    return header, rows


def run_pilot(
    workbook_path: Path,
    output_dir: Path,
    robot_path: str | None = None,
) -> dict[str, object]:
    workbook_path = workbook_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = artifact_paths(output_dir)
    robot = reconstruction.resolve_robot_path(robot_path)

    governed = reconstruction.load_governed_coms_rows(workbook_path)
    coverage_graph = build_governed_coverage_graph(
        governed.processed_rows,
    )

    passing_rows = query_pilot.ordered_rows(
        coms.run_select_query(
            coverage_graph,
            query_pilot.UNMAPPED_QUERY,
        ),
        query_pilot.UNMAPPED_COLUMNS,
    )
    if passing_rows:
        raise RuntimeError(
            "Governed coverage graph unexpectedly contains violations"
        )

    coverage_graph.serialize(
        artifacts.passing_graph_path,
        format="turtle",
    )
    passing_round_trip = Graph().parse(
        artifacts.passing_graph_path,
        format="turtle",
    )

    violating_graph, controlled_term = build_controlled_violation(
        coverage_graph,
    )
    expected_violation_rows = query_pilot.ordered_rows(
        coms.run_select_query(
            violating_graph,
            query_pilot.UNMAPPED_QUERY,
        ),
        query_pilot.UNMAPPED_COLUMNS,
    )
    if len(expected_violation_rows) != 1:
        raise RuntimeError(
            "Controlled violation did not produce exactly one RDFLib row"
        )

    violating_graph.serialize(
        artifacts.violating_graph_path,
        format="turtle",
    )
    violating_round_trip = Graph().parse(
        artifacts.violating_graph_path,
        format="turtle",
    )

    passing_result = run_robot_verify(
        robot,
        artifacts.passing_graph_path,
        artifacts.passing_report_dir,
    )
    violating_result = run_robot_verify(
        robot,
        artifacts.violating_graph_path,
        artifacts.violating_report_dir,
    )

    failing_report_path = (
        artifacts.violating_report_dir / EXPECTED_REPORT_NAME
    )
    report_header, report_rows = read_report_rows(
        failing_report_path,
    )

    passing_round_trip_ok = isomorphic(
        coverage_graph,
        passing_round_trip,
    )
    violating_round_trip_ok = isomorphic(
        violating_graph,
        violating_round_trip,
    )

    passing_ok = (
        passing_result.return_code == 0
        and "PASS Rule" in passing_result.output
        and "0 violation(s)" in passing_result.output
        and not passing_result.report_files
    )

    violating_ok = (
        violating_result.return_code == 1
        and "FAIL Rule" in violating_result.output
        and "1 violation(s)" in violating_result.output
        and tuple(path.name for path in violating_result.report_files)
        == (EXPECTED_REPORT_NAME,)
        and report_header == query_pilot.UNMAPPED_COLUMNS
        and report_rows == expected_violation_rows
    )

    summary: dict[str, object] = {
        "passed": (
            passing_ok
            and violating_ok
            and passing_round_trip_ok
            and violating_round_trip_ok
        ),
        "robot_path": robot,
        "workbook": str(workbook_path),
        "governed_row_count": len(governed.processed_rows),
        "coverage_graph": {
            "triple_count": len(coverage_graph),
            "round_trip_triple_count": len(passing_round_trip),
            "round_trip_isomorphic": passing_round_trip_ok,
            "sha256": sha256(artifacts.passing_graph_path),
        },
        "controlled_violation": {
            "term": controlled_term,
            "status": EXPECTED_VIOLATION_STATUS,
            "expected_row_count": len(expected_violation_rows),
            "expected_rows": [
                list(row)
                for row in expected_violation_rows
            ],
            "triple_count": len(violating_graph),
            "round_trip_triple_count": len(violating_round_trip),
            "round_trip_isomorphic": violating_round_trip_ok,
            "sha256": sha256(artifacts.violating_graph_path),
        },
        "passing_verify": {
            "passed": passing_ok,
            "return_code": passing_result.return_code,
            "output": passing_result.output,
            "report_files": [
                path.name
                for path in passing_result.report_files
            ],
        },
        "violating_verify": {
            "passed": violating_ok,
            "return_code": violating_result.return_code,
            "output": violating_result.output,
            "report_files": [
                path.name
                for path in violating_result.report_files
            ],
            "report_name": EXPECTED_REPORT_NAME,
            "report_exists": failing_report_path.is_file(),
            "report_bytes": (
                failing_report_path.stat().st_size
                if failing_report_path.is_file()
                else 0
            ),
            "report_header": list(report_header),
            "report_rows": [
                list(row)
                for row in report_rows
            ],
        },
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

    passing = summary["passing_verify"]
    violating = summary["violating_verify"]
    controlled = summary["controlled_violation"]

    print(f"Governed rows: {summary['governed_row_count']}")
    print(
        "Coverage graph triples: "
        f"{summary['coverage_graph']['triple_count']}"
    )
    print(f"Controlled violation term: {controlled['term']}")
    print(
        "Controlled violation rows: "
        f"{controlled['expected_row_count']}"
    )
    print(
        "Passing verify return code: "
        f"{passing['return_code']}"
    )
    print(
        "Passing verify reports: "
        f"{len(passing['report_files'])}"
    )
    print(
        "Violating verify return code: "
        f"{violating['return_code']}"
    )
    print(
        "Violating verify report rows: "
        f"{len(violating['report_rows'])}"
    )
    print("Summary: PASS" if summary["passed"] else "Summary: FAIL")

    for verify_summary in (passing, violating):
        if verify_summary["output"]:
            print(verify_summary["output"])

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
