#!/usr/bin/env python3
"""Compare governed RDFLib SELECT results with read-only ROBOT query results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL

import generate_mapping_from_coms as coms
import robot_reconstruction_validation as reconstruction


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_QUERY = REPO_ROOT / "queries/source-classes-and-object-properties.rq"
UNMAPPED_QUERY = REPO_ROOT / "queries/unmapped-source-terms.rq"

SOURCE_COLUMNS = ("term", "kind")
UNMAPPED_COLUMNS = ("term", "kind", "coverageStatus")


@dataclass(frozen=True)
class PilotArtifacts:
    source_graph_path: Path
    coverage_graph_path: Path
    rdflib_source_csv_path: Path
    robot_source_csv_path: Path
    rdflib_unmapped_csv_path: Path
    robot_unmapped_csv_path: Path
    summary_path: Path


@dataclass(frozen=True)
class RobotQueryResult:
    return_code: int
    output: str
    output_exists: bool
    output_bytes: int
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def artifact_paths(output_dir: Path) -> PilotArtifacts:
    return PilotArtifacts(
        source_graph_path=output_dir / "source-graph.ttl",
        coverage_graph_path=output_dir / "coverage-graph.ttl",
        rdflib_source_csv_path=output_dir / "rdflib-source-terms.csv",
        robot_source_csv_path=output_dir / "robot-source-terms.csv",
        rdflib_unmapped_csv_path=output_dir / "rdflib-unmapped-terms.csv",
        robot_unmapped_csv_path=output_dir / "robot-unmapped-terms.csv",
        summary_path=output_dir / "summary.json",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordered_rows(
    rows: Iterable[dict[str, str]],
    columns: tuple[str, ...],
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(row[column] for column in columns)
        for row in rows
    )


def write_csv_rows(
    path: Path,
    columns: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def read_robot_csv(
    path: Path,
    columns: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    if not path.is_file() or path.stat().st_size == 0:
        return (), ()

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = tuple(
            tuple((row.get(column) or "") for column in columns)
            for row in reader
        )
    return header, rows


def run_robot_query(
    robot: str,
    input_path: Path,
    query_path: Path,
    output_path: Path,
) -> RobotQueryResult:
    output_path.unlink(missing_ok=True)

    completed = subprocess.run(
        [
            robot,
            "query",
            "--input",
            str(input_path),
            "--query",
            str(query_path),
            str(output_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    header, rows = read_robot_csv(
        output_path,
        SOURCE_COLUMNS if query_path == SOURCE_QUERY else UNMAPPED_COLUMNS,
    )
    output_exists = output_path.is_file()

    return RobotQueryResult(
        return_code=completed.returncode,
        output=reconstruction.combined_process_output(
            completed.stdout,
            completed.stderr,
        ),
        output_exists=output_exists,
        output_bytes=output_path.stat().st_size if output_exists else 0,
        header=header,
        rows=rows,
    )


def build_coverage_graph(
    processed_rows: Iterable[coms.ProcessedRow],
    source_rows: Iterable[dict[str, str]],
) -> Graph:
    processed = tuple(processed_rows)
    source_terms = {
        URIRef(row["term"]): row["kind"]
        for row in source_rows
    }

    mapped_terms = {
        row.subject
        for row in processed
        if row.predicate in coms.MAPPING_PREDICATES
    }
    property_typing_terms = {
        row.subject
        for row in processed
        if row.predicate in coms.DOMAIN_RANGE_PREDICATES
    }
    explicit_blank_terms = {
        row.subject
        for row in processed
        if not row.predicate
    }

    graph = Graph()
    coms.bind_prefixes(graph)
    graph.bind("coms", coms.COMS_COVERAGE)

    for term, kind in sorted(source_terms.items(), key=lambda item: str(item[0])):
        graph.add(
            (term, coms.COMS_COVERAGE.sourceKind, Literal(kind))
        )
        if term in mapped_terms:
            status = "mapped"
        elif term in property_typing_terms:
            status = "covered_by_property_typing"
        elif term in explicit_blank_terms:
            status = "explicitly_unmapped"
        else:
            status = "absent_from_spreadsheet"
        graph.add(
            (term, coms.COMS_COVERAGE.coverageStatus, Literal(status))
        )

    return graph


def row_differences(
    expected: tuple[tuple[str, ...], ...],
    actual: tuple[tuple[str, ...], ...],
) -> tuple[list[list[str]], list[list[str]]]:
    expected_set = set(expected)
    actual_set = set(actual)
    return (
        [list(row) for row in sorted(expected_set - actual_set)],
        [list(row) for row in sorted(actual_set - expected_set)],
    )


def query_passed(
    expected_rows: tuple[tuple[str, ...], ...],
    robot_result: RobotQueryResult,
    expected_columns: tuple[str, ...],
) -> bool:
    header_is_valid = (
        robot_result.header == expected_columns
        or (
            not expected_rows
            and not robot_result.rows
            and robot_result.header == ()
        )
    )
    return (
        robot_result.return_code == 0
        and robot_result.output_exists
        and header_is_valid
        and robot_result.rows == expected_rows
    )


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

    source_graph = coms.build_source_graph()
    source_rdflib_dicts = coms.run_select_query(source_graph, SOURCE_QUERY)
    source_rdflib_rows = ordered_rows(
        source_rdflib_dicts,
        SOURCE_COLUMNS,
    )
    source_graph.serialize(artifacts.source_graph_path, format="turtle")
    write_csv_rows(
        artifacts.rdflib_source_csv_path,
        SOURCE_COLUMNS,
        source_rdflib_rows,
    )

    source_round_trip = Graph().parse(
        artifacts.source_graph_path,
        format="turtle",
    )
    source_robot = run_robot_query(
        robot,
        artifacts.source_graph_path,
        SOURCE_QUERY,
        artifacts.robot_source_csv_path,
    )

    coverage_graph = build_coverage_graph(
        governed.processed_rows,
        source_rdflib_dicts,
    )
    coverage_rdflib_dicts = coms.run_select_query(
        coverage_graph,
        UNMAPPED_QUERY,
    )
    coverage_rdflib_rows = ordered_rows(
        coverage_rdflib_dicts,
        UNMAPPED_COLUMNS,
    )
    coverage_graph.serialize(
        artifacts.coverage_graph_path,
        format="turtle",
    )
    write_csv_rows(
        artifacts.rdflib_unmapped_csv_path,
        UNMAPPED_COLUMNS,
        coverage_rdflib_rows,
    )

    coverage_round_trip = Graph().parse(
        artifacts.coverage_graph_path,
        format="turtle",
    )
    coverage_robot = run_robot_query(
        robot,
        artifacts.coverage_graph_path,
        UNMAPPED_QUERY,
        artifacts.robot_unmapped_csv_path,
    )

    source_rdflib_only, source_robot_only = row_differences(
        source_rdflib_rows,
        source_robot.rows,
    )
    coverage_rdflib_only, coverage_robot_only = row_differences(
        coverage_rdflib_rows,
        coverage_robot.rows,
    )

    source_query_ok = query_passed(
        source_rdflib_rows,
        source_robot,
        SOURCE_COLUMNS,
    )
    coverage_query_ok = query_passed(
        coverage_rdflib_rows,
        coverage_robot,
        UNMAPPED_COLUMNS,
    )
    source_round_trip_ok = isomorphic(source_graph, source_round_trip)
    coverage_round_trip_ok = isomorphic(
        coverage_graph,
        coverage_round_trip,
    )

    summary: dict[str, object] = {
        "passed": (
            source_query_ok
            and coverage_query_ok
            and source_round_trip_ok
            and coverage_round_trip_ok
        ),
        "robot_path": robot,
        "workbook": str(workbook_path),
        "governed_row_count": len(governed.processed_rows),
        "source_graph": {
            "triple_count": len(source_graph),
            "round_trip_triple_count": len(source_round_trip),
            "round_trip_isomorphic": source_round_trip_ok,
            "owl_imports_count": len(
                list(source_graph.triples((None, OWL.imports, None)))
            ),
            "sha256": sha256(artifacts.source_graph_path),
        },
        "coverage_graph": {
            "triple_count": len(coverage_graph),
            "round_trip_triple_count": len(coverage_round_trip),
            "round_trip_isomorphic": coverage_round_trip_ok,
            "sha256": sha256(artifacts.coverage_graph_path),
        },
        "source_query": {
            "passed": source_query_ok,
            "query": str(SOURCE_QUERY),
            "rdflib_row_count": len(source_rdflib_rows),
            "robot_row_count": len(source_robot.rows),
            "same_ordered_rows": source_rdflib_rows == source_robot.rows,
            "rdflib_only_rows": source_rdflib_only,
            "robot_only_rows": source_robot_only,
            "robot_return_code": source_robot.return_code,
            "robot_output": source_robot.output,
            "robot_output_exists": source_robot.output_exists,
            "robot_output_bytes": source_robot.output_bytes,
            "robot_header": list(source_robot.header),
        },
        "unmapped_query": {
            "passed": coverage_query_ok,
            "query": str(UNMAPPED_QUERY),
            "rdflib_row_count": len(coverage_rdflib_rows),
            "robot_row_count": len(coverage_robot.rows),
            "same_ordered_rows": coverage_rdflib_rows == coverage_robot.rows,
            "rdflib_only_rows": coverage_rdflib_only,
            "robot_only_rows": coverage_robot_only,
            "robot_return_code": coverage_robot.return_code,
            "robot_output": coverage_robot.output,
            "robot_output_exists": coverage_robot.output_exists,
            "robot_output_bytes": coverage_robot.output_bytes,
            "robot_header": list(coverage_robot.header),
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

    source = summary["source_query"]
    unmapped = summary["unmapped_query"]

    print(f"Governed rows: {summary['governed_row_count']}")
    print(f"Source graph triples: {summary['source_graph']['triple_count']}")
    print(f"Source RDFLib rows: {source['rdflib_row_count']}")
    print(f"Source ROBOT rows: {source['robot_row_count']}")
    print(f"Unmapped RDFLib rows: {unmapped['rdflib_row_count']}")
    print(f"Unmapped ROBOT rows: {unmapped['robot_row_count']}")
    print(
        "ROBOT empty-result bytes: "
        f"{unmapped['robot_output_bytes']}"
    )
    print("Summary: PASS" if summary["passed"] else "Summary: FAIL")

    for query_summary in (source, unmapped):
        if query_summary["robot_output"]:
            print(query_summary["robot_output"])

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
