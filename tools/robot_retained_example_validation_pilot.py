#!/usr/bin/env python3
"""Validate retained Turtle examples with read-only ROBOT conversion."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from rdflib import Graph, Literal, RDF, RDFS, OWL, XSD
from rdflib.compare import isomorphic, to_canonical_graph

import robot_reconstruction_validation as reconstruction


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = (
    REPO_ROOT
    / "src"
    / "current-ssn-sosa"
    / "examples"
)

EXPECTED_EXAMPLES = (
    "sosa-instance-data/Beer-Full-IBS-TH2.ttl",
    "sosa-instance-data/IDEAS.ttl",
    "sosa-instance-data/apartment-134.ttl",
    "sosa-instance-data/dht22-deployment.ttl",
    "sosa-instance-data/dht22.ttl",
    "sosa-instance-data/ip68.ttl",
    "sosa-instance-data/iphone_barometer-sosa.ttl",
    "sosa-instance-data/seismograph.ttl",
    "sosa-instance-data/spinning-cups.ttl",
    "sosa-instance-data/sunspots.ttl",
    "sosa-instance-data/tree-height.ttl",
)

STRUCTURAL_DECLARATION_TYPES = frozenset(
    {
        OWL.AnnotationProperty,
        OWL.Class,
        OWL.NamedIndividual,
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.Ontology,
        OWL.Restriction,
        RDFS.Datatype,
    }
)

INTEGRAL_DECIMAL_PATTERN = re.compile(r"[+-]?\d+")


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_name(relative_path: str) -> str:
    """Return the historical Makefile-compatible output name."""

    return (
        relative_path
        .replace("/", "_")
        .replace(".", "_")
        + ".ttl"
    )


def run_robot_convert(
    robot: str,
    source_path: Path,
    output_path: Path,
) -> dict[str, object]:
    """Run one read-only ROBOT conversion."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.unlink(missing_ok=True)

    completed = subprocess.run(
        [
            robot,
            "convert",
            "--input",
            str(source_path),
            "--format",
            "ttl",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return {
        "return_code": completed.returncode,
        "robot_output": reconstruction.combined_process_output(
            completed.stdout,
            completed.stderr,
        ),
        "output_exists": output_path.is_file(),
        "output_bytes": (
            output_path.stat().st_size
            if output_path.is_file()
            else 0
        ),
        "output_sha256": (
            sha256(output_path)
            if output_path.is_file()
            else ""
        ),
    }


def normalize_graph(
    graph: Graph,
) -> tuple[Graph, int, int]:
    """Normalize only proven OWLAPI conversion effects."""

    normalized = Graph()
    for prefix, namespace in graph.namespaces():
        normalized.bind(prefix, namespace)

    removed_structural_declarations = 0
    rewritten_integral_decimals = 0

    for subject, predicate, object_ in graph:
        if (
            predicate == RDF.type
            and object_ in STRUCTURAL_DECLARATION_TYPES
        ):
            removed_structural_declarations += 1
            continue

        if (
            isinstance(object_, Literal)
            and object_.datatype == XSD.decimal
            and INTEGRAL_DECIMAL_PATTERN.fullmatch(str(object_))
        ):
            object_ = Literal(
                int(str(object_)),
                datatype=XSD.integer,
            )
            rewritten_integral_decimals += 1

        normalized.add((subject, predicate, object_))

    return (
        normalized,
        removed_structural_declarations,
        rewritten_integral_decimals,
    )


def canonical_sha256(graph: Graph) -> str:
    """Return a deterministic digest of a normalized RDF graph."""

    canonical = to_canonical_graph(graph)
    lines = sorted(
        line
        for line in canonical.serialize(format="nt").splitlines()
        if line
    )
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluate_example(
    robot: str,
    source_path: Path,
    relative_path: str,
    first_dir: Path,
    second_dir: Path,
) -> dict[str, object]:
    """Convert one example twice and compare normalized semantics."""

    generated_name = output_name(relative_path)
    first_path = first_dir / generated_name
    second_path = second_dir / generated_name

    first_result = run_robot_convert(
        robot,
        source_path,
        first_path,
    )
    second_result = run_robot_convert(
        robot,
        source_path,
        second_path,
    )

    successful_conversion = (
        first_result["return_code"] == 0
        and second_result["return_code"] == 0
        and first_result["output_exists"]
        and second_result["output_exists"]
    )

    if not successful_conversion:
        return {
            "source": relative_path,
            "source_sha256": sha256(source_path),
            "first_conversion": first_result,
            "second_conversion": second_result,
            "passed": False,
        }

    source_graph = Graph().parse(
        source_path,
        format="turtle",
    )
    first_graph = Graph().parse(
        first_path,
        format="turtle",
    )
    second_graph = Graph().parse(
        second_path,
        format="turtle",
    )

    (
        normalized_source,
        source_declarations_removed,
        source_literals_rewritten,
    ) = normalize_graph(source_graph)
    (
        normalized_first,
        first_declarations_removed,
        first_literals_rewritten,
    ) = normalize_graph(first_graph)
    (
        normalized_second,
        second_declarations_removed,
        second_literals_rewritten,
    ) = normalize_graph(second_graph)

    source_canonical_sha256 = canonical_sha256(
        normalized_source,
    )
    first_canonical_sha256 = canonical_sha256(
        normalized_first,
    )
    second_canonical_sha256 = canonical_sha256(
        normalized_second,
    )

    source_output_isomorphic = isomorphic(
        normalized_source,
        normalized_first,
    )
    repeated_outputs_isomorphic = isomorphic(
        normalized_first,
        normalized_second,
    )
    canonical_hashes_equal = (
        source_canonical_sha256
        == first_canonical_sha256
        == second_canonical_sha256
    )
    raw_bytes_equal = (
        first_path.read_bytes()
        == second_path.read_bytes()
    )

    passed = (
        successful_conversion
        and source_output_isomorphic
        and repeated_outputs_isomorphic
        and canonical_hashes_equal
    )

    return {
        "source": relative_path,
        "source_sha256": sha256(source_path),
        "source_triple_count": len(source_graph),
        "first_output_triple_count": len(first_graph),
        "second_output_triple_count": len(second_graph),
        "normalized_source_triple_count": len(
            normalized_source
        ),
        "normalized_first_output_triple_count": len(
            normalized_first
        ),
        "normalized_second_output_triple_count": len(
            normalized_second
        ),
        "source_structural_declarations_removed": (
            source_declarations_removed
        ),
        "first_output_structural_declarations_removed": (
            first_declarations_removed
        ),
        "second_output_structural_declarations_removed": (
            second_declarations_removed
        ),
        "source_integral_decimals_rewritten": (
            source_literals_rewritten
        ),
        "first_output_integral_decimals_rewritten": (
            first_literals_rewritten
        ),
        "second_output_integral_decimals_rewritten": (
            second_literals_rewritten
        ),
        "source_output_isomorphic": source_output_isomorphic,
        "repeated_outputs_isomorphic": (
            repeated_outputs_isomorphic
        ),
        "raw_bytes_equal": raw_bytes_equal,
        "canonical_hashes_equal": canonical_hashes_equal,
        "normalized_canonical_sha256": (
            source_canonical_sha256
        ),
        "first_conversion": first_result,
        "second_conversion": second_result,
        "passed": passed,
    }


def evaluate_malformed_control(
    robot: str,
    output_dir: Path,
) -> dict[str, object]:
    """Prove that malformed Turtle is rejected without output."""

    source_path = output_dir / "malformed-control.ttl"
    output_path = output_dir / "malformed-control-output.ttl"

    source_path.write_text(
        "@prefix ex: <https://example.org/> .\n"
        "ex:subject ex:predicate [\n",
        encoding="utf-8",
    )

    result = run_robot_convert(
        robot,
        source_path,
        output_path,
    )

    invalid_diagnostic = (
        "INVALID ONTOLOGY FILE ERROR"
        in str(result["robot_output"])
    )
    passed = (
        result["return_code"] == 1
        and not result["output_exists"]
        and invalid_diagnostic
    )

    return {
        **result,
        "invalid_ontology_diagnostic": invalid_diagnostic,
        "passed": passed,
    }


def run_pilot(
    output_dir: Path,
    robot_path: str | None = None,
) -> dict[str, object]:
    """Run the permanent retained-example validation pilot."""

    output_dir = output_dir.resolve()
    shutil.rmtree(output_dir, ignore_errors=True)

    first_dir = output_dir / "first"
    second_dir = output_dir / "second"
    first_dir.mkdir(parents=True, exist_ok=True)
    second_dir.mkdir(parents=True, exist_ok=True)

    robot = reconstruction.resolve_robot_path(robot_path)

    source_paths = sorted(EXAMPLES_ROOT.rglob("*.ttl"))
    actual_inventory = tuple(
        path.relative_to(EXAMPLES_ROOT).as_posix()
        for path in source_paths
    )
    inventory_matches = (
        actual_inventory == EXPECTED_EXAMPLES
    )

    results = [
        evaluate_example(
            robot,
            source_path,
            relative_path,
            first_dir,
            second_dir,
        )
        for source_path, relative_path in zip(
            source_paths,
            actual_inventory,
            strict=True,
        )
    ]

    malformed_control = evaluate_malformed_control(
        robot,
        output_dir,
    )

    successful_count = sum(
        1
        for result in results
        if result["passed"]
    )
    raw_byte_reproducible_count = sum(
        1
        for result in results
        if result.get("raw_bytes_equal") is True
    )
    canonical_reproducible_count = sum(
        1
        for result in results
        if result.get("canonical_hashes_equal") is True
    )
    total_output_structural_declarations = sum(
        int(
            result.get(
                "first_output_structural_declarations_removed",
                0,
            )
        )
        for result in results
    )
    total_source_integral_decimal_rewrites = sum(
        int(
            result.get(
                "source_integral_decimals_rewritten",
                0,
            )
        )
        for result in results
    )

    passed = (
        inventory_matches
        and len(results) == len(EXPECTED_EXAMPLES)
        and successful_count == len(EXPECTED_EXAMPLES)
        and malformed_control["passed"]
    )

    summary: dict[str, object] = {
        "robot_path": robot,
        "examples_root": str(EXAMPLES_ROOT),
        "expected_example_count": len(EXPECTED_EXAMPLES),
        "actual_example_count": len(actual_inventory),
        "expected_inventory": list(EXPECTED_EXAMPLES),
        "actual_inventory": list(actual_inventory),
        "inventory_matches": inventory_matches,
        "successful_example_count": successful_count,
        "raw_byte_reproducible_count": (
            raw_byte_reproducible_count
        ),
        "canonical_reproducible_count": (
            canonical_reproducible_count
        ),
        "total_output_structural_declarations_removed": (
            total_output_structural_declarations
        ),
        "total_source_integral_decimals_rewritten": (
            total_source_integral_decimal_rewrites
        ),
        "examples": results,
        "malformed_control": malformed_control,
        "disposition": (
            "ROBOT convert is accepted as a permanent read-only "
            "retained-example parse gate; normalized graph "
            "equivalence is authoritative for this gate, while "
            "raw converted bytes are not"
        ),
        "passed": passed,
    }

    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
        Path(args.output_dir),
        args.robot,
    )

    print(
        "Retained examples: "
        f"{summary['actual_example_count']}"
    )
    print(
        "Inventory matches: "
        f"{summary['inventory_matches']}"
    )
    print(
        "Successful normalized comparisons: "
        f"{summary['successful_example_count']}"
    )
    print(
        "Raw byte reproducible outputs: "
        f"{summary['raw_byte_reproducible_count']}"
    )
    print(
        "Canonical reproducible outputs: "
        f"{summary['canonical_reproducible_count']}"
    )
    print(
        "OWLAPI structural declarations normalized: "
        f"{summary['total_output_structural_declarations_removed']}"
    )
    print(
        "Source integral decimals normalized: "
        f"{summary['total_source_integral_decimals_rewritten']}"
    )

    malformed = summary["malformed_control"]
    print(
        "Malformed control return code: "
        f"{malformed['return_code']}"
    )
    print(
        "Malformed control output produced: "
        f"{malformed['output_exists']}"
    )
    print(
        "Disposition: "
        f"{summary['disposition']}"
    )
    print(
        f"Summary: {'PASS' if summary['passed'] else 'FAIL'}"
    )

    if not summary["passed"]:
        for result in summary["examples"]:
            if not result["passed"]:
                print(
                    "Failed example: "
                    f"{result['source']}"
                )

        if not malformed["passed"]:
            print("Malformed control failed")
            if malformed["robot_output"]:
                print(malformed["robot_output"])

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
