#!/usr/bin/env python3
"""Generate and validate a normalized ROBOT Template view of governed COMS rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rdflib import Literal, URIRef

import robot_reconstruction_validation as reconstruction
from coms_row_identity import (
    CanonicalRowInput,
    ExpressionNode,
    OWL_EQUIVALENT_CLASS,
    OWL_EQUIVALENT_PROPERTY,
    RDFS_DOMAIN,
    RDFS_RANGE,
    RDFS_SUBCLASS_OF,
    RDFS_SUBPROPERTY_OF,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_ONTOLOGY_IRI = "http://www.sks.ai/SSN2BFO/pilots/robot-template-normalized"

TEMPLATE_HEADER = (
    "ID",
    "Type",
    "SubClassOf",
    "EquivalentClass",
    "SubPropertyOf",
    "EquivalentProperty",
    "Domain",
    "Range",
)

TEMPLATE_DIRECTIVES = (
    "ID",
    "TYPE",
    "SC %",
    "EC %",
    "SP %",
    "EP %",
    "DOMAIN",
    "RANGE",
)

SUPPORTED_MAPPING_TYPES = frozenset(
    {
        "class_mapping",
        "object_property_mapping",
        "domain",
        "range",
    }
)


@dataclass(frozen=True)
class PilotArtifacts:
    resolver_path: Path
    template_path: Path
    output_path: Path
    errors_path: Path
    summary_path: Path


def deterministic_label(kind: str, iri: str) -> str:
    if kind not in {"class", "property"}:
        raise ValueError(f"unsupported ROBOT label kind: {kind}")
    digest = hashlib.sha256(iri.encode("utf-8")).hexdigest()
    return f"__robot_{kind}_{digest}"


def _flatten_expression(
    expression: ExpressionNode,
    kind: str,
) -> tuple[ExpressionNode, ...]:
    flattened: list[ExpressionNode] = []
    for child in expression.children:
        if child.kind == kind:
            flattened.extend(_flatten_expression(child, kind))
        else:
            flattened.append(child)
    return tuple(flattened)


def collect_expression_entities(
    expression: ExpressionNode,
    classes: set[str],
    properties: set[str],
) -> None:
    if expression.kind == "named":
        if expression.iri is None:
            raise ValueError("named expression lacks an IRI")
        classes.add(expression.iri)
        return

    if expression.kind in {"intersection", "union"}:
        if not expression.children:
            raise ValueError(f"{expression.kind} expression has no operands")
        for child in expression.children:
            collect_expression_entities(child, classes, properties)
        return

    if expression.kind == "some":
        if expression.property_iri is None or expression.filler is None:
            raise ValueError("existential restriction is incomplete")
        properties.add(expression.property_iri)
        collect_expression_entities(expression.filler, classes, properties)
        return

    raise ValueError(f"unsupported expression kind: {expression.kind}")


def build_entity_labels(
    rows: Iterable[CanonicalRowInput],
) -> dict[tuple[str, str], str]:
    classes: set[str] = set()
    properties: set[str] = set()

    for row in rows:
        if row.expression is not None:
            collect_expression_entities(row.expression, classes, properties)
        if row.target_property_iri is not None:
            properties.add(row.target_property_iri)

    labels: dict[tuple[str, str], str] = {}
    for iri in sorted(classes):
        labels[("class", iri)] = deterministic_label("class", iri)
    for iri in sorted(properties):
        labels[("property", iri)] = deterministic_label("property", iri)
    return labels


def _quoted_label(kind: str, iri: str, labels: dict[tuple[str, str], str]) -> str:
    try:
        label = labels[(kind, iri)]
    except KeyError as exc:
        raise ValueError(f"missing generated {kind} label for {iri}") from exc
    return f"'{label}'"


def render_manchester_expression(
    expression: ExpressionNode,
    labels: dict[tuple[str, str], str],
) -> str:
    if expression.kind == "named":
        if expression.iri is None:
            raise ValueError("named expression lacks an IRI")
        return _quoted_label("class", expression.iri, labels)

    if expression.kind in {"intersection", "union"}:
        flattened = _flatten_expression(expression, expression.kind)
        rendered = sorted(
            {
                render_manchester_expression(child, labels)
                for child in flattened
            }
        )
        if not rendered:
            raise ValueError(f"{expression.kind} expression has no operands")
        if len(rendered) == 1:
            return rendered[0]
        operator = " and " if expression.kind == "intersection" else " or "
        return f"({operator.join(rendered)})"

    if expression.kind == "some":
        if expression.property_iri is None or expression.filler is None:
            raise ValueError("existential restriction is incomplete")
        property_label = _quoted_label(
            "property",
            expression.property_iri,
            labels,
        )
        filler = render_manchester_expression(expression.filler, labels)
        return f"({property_label} some {filler})"

    raise ValueError(f"unsupported expression kind: {expression.kind}")


def _template_row(
    row: CanonicalRowInput,
    labels: dict[tuple[str, str], str],
) -> tuple[str, ...]:
    values = [""] * len(TEMPLATE_HEADER)
    values[0] = row.subject_iri

    if row.mapping_type == "class_mapping":
        values[1] = "owl:Class"
        if row.expression is None:
            raise ValueError(f"{row.row_id}: class mapping lacks expression")
        target = render_manchester_expression(row.expression, labels)
        if row.predicate_iri == RDFS_SUBCLASS_OF:
            values[2] = target
        elif row.predicate_iri == OWL_EQUIVALENT_CLASS:
            values[3] = target
        else:
            raise ValueError(
                f"{row.row_id}: unsupported class predicate {row.predicate_iri}"
            )

    elif row.mapping_type == "object_property_mapping":
        values[1] = "owl:ObjectProperty"
        if row.target_property_iri is None:
            raise ValueError(
                f"{row.row_id}: object-property mapping lacks target property"
            )
        target = _quoted_label(
            "property",
            row.target_property_iri,
            labels,
        )
        if row.predicate_iri == RDFS_SUBPROPERTY_OF:
            values[4] = target
        elif row.predicate_iri == OWL_EQUIVALENT_PROPERTY:
            values[5] = target
        else:
            raise ValueError(
                f"{row.row_id}: unsupported property predicate {row.predicate_iri}"
            )

    elif row.mapping_type in {"domain", "range"}:
        values[1] = "owl:ObjectProperty"
        if row.expression is None:
            raise ValueError(f"{row.row_id}: {row.mapping_type} lacks expression")
        target = render_manchester_expression(row.expression, labels)
        expected_predicate = RDFS_DOMAIN if row.mapping_type == "domain" else RDFS_RANGE
        if row.predicate_iri != expected_predicate:
            raise ValueError(
                f"{row.row_id}: {row.mapping_type} predicate mismatch"
            )
        values[6 if row.mapping_type == "domain" else 7] = target

    else:
        raise ValueError(
            f"{row.row_id}: unsupported pilot mapping type {row.mapping_type}"
        )

    return tuple(values)


def write_resolver_ontology(
    labels: dict[tuple[str, str], str],
    path: Path,
) -> None:
    lines = [
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        f"<{PILOT_ONTOLOGY_IRI}/resolver> a owl:Ontology .",
    ]

    for (kind, iri), label in sorted(labels.items()):
        owl_type = "owl:Class" if kind == "class" else "owl:ObjectProperty"
        lines.extend(
            [
                "",
                f"{URIRef(iri).n3()} a {owl_type} ;",
                f"    rdfs:label {Literal(label).n3()} .",
            ]
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_template(
    rows: Iterable[CanonicalRowInput],
    labels: dict[tuple[str, str], str],
    path: Path,
) -> tuple[CanonicalRowInput, ...]:
    selected = tuple(
        sorted(
            (
                row
                for row in rows
                if row.mapping_type in SUPPORTED_MAPPING_TYPES
            ),
            key=lambda row: row.row_id,
        )
    )

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(
            handle,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writerow(TEMPLATE_HEADER)
        writer.writerow(TEMPLATE_DIRECTIVES)
        for row in selected:
            writer.writerow(_template_row(row, labels))

    return selected


def artifact_paths(output_dir: Path) -> PilotArtifacts:
    return PilotArtifacts(
        resolver_path=output_dir / "resolver.ttl",
        template_path=output_dir / "normalized-template.tsv",
        output_path=output_dir / "robot-output.ttl",
        errors_path=output_dir / "robot-errors.tsv",
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

    labels = build_entity_labels(canonical_rows)
    selected = write_template(
        canonical_rows,
        labels,
        artifacts.template_path,
    )
    write_resolver_ontology(labels, artifacts.resolver_path)

    artifacts.output_path.unlink(missing_ok=True)
    artifacts.errors_path.unlink(missing_ok=True)

    robot = reconstruction.resolve_robot_path(robot_path)

    completed = subprocess.run(
        [
            robot,
            "template",
            "--input",
            str(artifacts.resolver_path),
            "--template",
            str(artifacts.template_path),
            "--ontology-iri",
            PILOT_ONTOLOGY_IRI,
            "--errors",
            str(artifacts.errors_path),
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
        SUPPORTED_MAPPING_TYPES,
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
        and len(selected) == 100
        and len(expected) == 100
        and len(actual) == 100
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
        "attempted_non_chain_rows": len(selected),
        "excluded_property_chain_rows": sum(
            row.mapping_type == "property_chain"
            for row in canonical_rows
        ),
        "expected_axiom_count": len(expected),
        "actual_axiom_count": len(actual),
        "missing_axiom_ids": missing,
        "extra_axiom_ids": extra,
        "mismatched_axiom_ids": mismatched,
        "resolver_entity_count": len(labels),
        "resolver_sha256": hashlib.sha256(
            artifacts.resolver_path.read_bytes()
        ).hexdigest(),
        "template_sha256": hashlib.sha256(
            artifacts.template_path.read_bytes()
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
    print(f"Attempted non-chain rows: {summary['attempted_non_chain_rows']}")
    print(f"Excluded property-chain rows: {summary['excluded_property_chain_rows']}")
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
