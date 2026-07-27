#!/usr/bin/env python3
"""Prove ROBOT diff control behavior and governed self-diff incompatibility."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import robot_reconstruction_validation as reconstruction


REPO_ROOT = Path(__file__).resolve().parents[1]

ALIGNMENT_CORE = (
    REPO_ROOT
    / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl"
)
STRICT_BFO_MAPPING = (
    REPO_ROOT
    / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl"
)

ALIGNMENT_CORE_IRI = (
    "http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core"
)

IN_CONDITION_IRI = "http://www.w3.org/ns/ssn/systems/inCondition"
IS_PROPERTY_OF_IRI = "http://www.w3.org/ns/ssn/isPropertyOf"

CONTROL_ONTOLOGY = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://example.org/control> a owl:Ontology .

<http://example.org/A> a owl:Class ;
    rdfs:subClassOf <http://example.org/B> .

<http://example.org/B> a owl:Class .
"""


@dataclass(frozen=True)
class PilotArtifacts:
    control_path: Path
    catalog_path: Path
    control_diff_path: Path
    alignment_diff_path: Path
    strict_diff_path: Path
    summary_path: Path


@dataclass(frozen=True)
class DiffResult:
    return_code: int
    output: str
    artifact_exists: bool
    artifact_bytes: int
    artifact_text: str


def artifact_paths(output_dir: Path) -> PilotArtifacts:
    return PilotArtifacts(
        control_path=output_dir / "control.ttl",
        catalog_path=output_dir / "catalog.xml",
        control_diff_path=output_dir / "control-self-diff.txt",
        alignment_diff_path=output_dir / "alignment-core-self-diff.txt",
        strict_diff_path=output_dir / "strict-bfo-self-diff.txt",
        summary_path=output_dir / "summary.json",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_control_ontology(path: Path) -> None:
    path.write_text(CONTROL_ONTOLOGY, encoding="utf-8")


def write_catalog(path: Path) -> None:
    alignment_uri = ALIGNMENT_CORE.resolve().as_uri()
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<catalog prefer="public"
         xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="{ALIGNMENT_CORE_IRI}"
       uri="{alignment_uri}"/>
</catalog>
""",
        encoding="utf-8",
    )


def run_robot_diff(
    robot: str,
    left: Path,
    right: Path,
    output_path: Path,
    *,
    left_catalog: Path | None = None,
    right_catalog: Path | None = None,
) -> DiffResult:
    output_path.unlink(missing_ok=True)

    command = [
        robot,
        "diff",
        "--left",
        str(left),
        "--right",
        str(right),
    ]

    if left_catalog is not None:
        command.extend(["--left-catalog", str(left_catalog)])
    if right_catalog is not None:
        command.extend(["--right-catalog", str(right_catalog)])

    command.extend(["--output", str(output_path)])

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    artifact_exists = output_path.is_file()
    artifact_text = (
        output_path.read_text(encoding="utf-8")
        if artifact_exists
        else ""
    )

    return DiffResult(
        return_code=completed.returncode,
        output=reconstruction.combined_process_output(
            completed.stdout,
            completed.stderr,
        ),
        artifact_exists=artifact_exists,
        artifact_bytes=(
            output_path.stat().st_size
            if artifact_exists
            else 0
        ),
        artifact_text=artifact_text,
    )


def parser_warning_count(output: str) -> int:
    return output.count(
        "Input ontology contains 1 triple(s) that could not be parsed"
    )


def diff_side_counts(text: str) -> tuple[int | None, int | None]:
    left_match = re.search(
        r"(\d+) axioms in left ontology but not in right ontology:",
        text,
    )
    right_match = re.search(
        r"(\d+) axioms in right ontology but not in left ontology:",
        text,
    )

    return (
        int(left_match.group(1)) if left_match else None,
        int(right_match.group(1)) if right_match else None,
    )


def summarize_diff(
    result: DiffResult,
    *,
    expected_property_iri: str | None = None,
) -> dict[str, object]:
    left_count, right_count = diff_side_counts(
        result.artifact_text,
    )

    summary: dict[str, object] = {
        "return_code": result.return_code,
        "process_output": result.output,
        "parser_warning_count": parser_warning_count(
            result.output,
        ),
        "artifact_exists": result.artifact_exists,
        "artifact_bytes": result.artifact_bytes,
        "artifact_text": result.artifact_text,
        "left_only_axiom_count": left_count,
        "right_only_axiom_count": right_count,
        "reports_identical": (
            result.artifact_text.strip()
            == "Ontologies are identical"
        ),
    }

    if expected_property_iri is not None:
        summary.update(
            {
                "expected_property_iri": expected_property_iri,
                "contains_expected_property": (
                    expected_property_iri
                    in result.artifact_text
                ),
                "contains_annotation_property_domain": (
                    "AnnotationPropertyDomain("
                    in result.artifact_text
                ),
                "contains_generated_blank_node": (
                    "_:genid-" in result.artifact_text
                ),
            }
        )

    return summary


def governed_false_positive_passed(
    summary: dict[str, object],
) -> bool:
    return (
        summary["return_code"] == 0
        and summary["parser_warning_count"] == 2
        and summary["artifact_exists"] is True
        and summary["reports_identical"] is False
        and summary["left_only_axiom_count"] == 1
        and summary["right_only_axiom_count"] == 1
        and summary["contains_expected_property"] is True
        and summary["contains_annotation_property_domain"] is True
        and summary["contains_generated_blank_node"] is True
    )


def run_pilot(
    output_dir: Path,
    robot_path: str | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = artifact_paths(output_dir)
    robot = reconstruction.resolve_robot_path(robot_path)

    write_control_ontology(artifacts.control_path)
    write_catalog(artifacts.catalog_path)

    control_result = run_robot_diff(
        robot,
        artifacts.control_path,
        artifacts.control_path,
        artifacts.control_diff_path,
    )
    alignment_result = run_robot_diff(
        robot,
        ALIGNMENT_CORE,
        ALIGNMENT_CORE,
        artifacts.alignment_diff_path,
    )
    strict_result = run_robot_diff(
        robot,
        STRICT_BFO_MAPPING,
        STRICT_BFO_MAPPING,
        artifacts.strict_diff_path,
        left_catalog=artifacts.catalog_path,
        right_catalog=artifacts.catalog_path,
    )

    control = summarize_diff(control_result)
    alignment = summarize_diff(
        alignment_result,
        expected_property_iri=IN_CONDITION_IRI,
    )
    strict = summarize_diff(
        strict_result,
        expected_property_iri=IS_PROPERTY_OF_IRI,
    )

    control_passed = (
        control["return_code"] == 0
        and control["parser_warning_count"] == 0
        and control["artifact_exists"] is True
        and control["reports_identical"] is True
        and control["left_only_axiom_count"] is None
        and control["right_only_axiom_count"] is None
    )
    alignment_false_positive_proven = (
        governed_false_positive_passed(alignment)
    )
    strict_false_positive_proven = (
        governed_false_positive_passed(strict)
    )

    summary: dict[str, object] = {
        "passed": (
            control_passed
            and alignment_false_positive_proven
            and strict_false_positive_proven
        ),
        "robot_path": robot,
        "control": {
            **control,
            "passed": control_passed,
            "ontology_sha256": sha256(
                artifacts.control_path,
            ),
        },
        "alignment_core_self_diff": {
            **alignment,
            "false_positive_proven": (
                alignment_false_positive_proven
            ),
            "ontology": str(ALIGNMENT_CORE),
            "ontology_sha256": sha256(ALIGNMENT_CORE),
        },
        "strict_bfo_self_diff": {
            **strict,
            "false_positive_proven": (
                strict_false_positive_proven
            ),
            "ontology": str(STRICT_BFO_MAPPING),
            "ontology_sha256": sha256(
                STRICT_BFO_MAPPING,
            ),
            "catalog_sha256": sha256(
                artifacts.catalog_path,
            ),
        },
        "disposition": (
            "robot diff is suitable for OWLAPI-compatible controls "
            "but rejected as an authoritative semantic-diff mechanism "
            "for the current governed products"
        ),
    }

    artifacts.summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
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

    control = summary["control"]
    alignment = summary["alignment_core_self_diff"]
    strict = summary["strict_bfo_self_diff"]

    print(
        "Control reports identical: "
        f"{control['reports_identical']}"
    )
    print(
        "Alignment parser warnings: "
        f"{alignment['parser_warning_count']}"
    )
    print(
        "Alignment false self-diff axioms: "
        f"{alignment['left_only_axiom_count']}/"
        f"{alignment['right_only_axiom_count']}"
    )
    print(
        "Strict-BFO parser warnings: "
        f"{strict['parser_warning_count']}"
    )
    print(
        "Strict-BFO false self-diff axioms: "
        f"{strict['left_only_axiom_count']}/"
        f"{strict['right_only_axiom_count']}"
    )
    print(f"Disposition: {summary['disposition']}")
    print("Summary: PASS" if summary["passed"] else "Summary: FAIL")

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
