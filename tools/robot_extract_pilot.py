#!/usr/bin/env python3
"""Evaluate governed ROBOT STAR extraction without changing production dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rdflib import Graph, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDF

import generate_mapping_from_coms as coms
import modular_products as modular
import robot_reconstruction_validation as reconstruction


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"
DEPENDENCY = REPO_ROOT / coms.BFO_VALIDATION_DEPENDENCY

BFO_PREFIX = "http://purl.obolibrary.org/obo/BFO_"
CCO_PREFIX = "https://www.commoncoreontologies.org/"
MODULE_IRI = "http://www.sks.ai/SSN2BFO/pilots/robot-extract-star"

CONTROLLED_INCONSISTENCY_TERM = URIRef(
    "http://purl.obolibrary.org/obo/BFO_0000002"
)

DECLARATION_TYPES = (
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
)

BUILTIN_PREFIXES = (
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "http://www.w3.org/2000/01/rdf-schema#",
    "http://www.w3.org/2001/XMLSchema#",
    "http://www.w3.org/2002/07/owl#",
)

IRI_RE = re.compile(r"<([^>]+)>")
ERROR_IRI_RE = re.compile(
    r"http://org\.semanticweb\.owlapi/error#Error\d+"
)


@dataclass(frozen=True)
class PilotArtifacts:
    seed_path: Path
    strict_output_path: Path
    first_module_path: Path
    second_module_path: Path
    summary_path: Path


@dataclass(frozen=True)
class ExtractionResult:
    return_code: int
    output: str
    output_exists: bool
    output_bytes: int


def artifact_paths(output_dir: Path) -> PilotArtifacts:
    return PilotArtifacts(
        seed_path=output_dir / "governed-bfo-cco-seeds.txt",
        strict_output_path=output_dir / "strict-star-module.ttl",
        first_module_path=output_dir / "star-module-a.ttl",
        second_module_path=output_dir / "star-module-b.ttl",
        summary_path=output_dir / "summary.json",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_expression_iris(
    expression,
    values: set[str],
) -> None:
    if expression.kind == "named":
        if expression.iri is not None:
            values.add(expression.iri)
        return

    if expression.kind in {"intersection", "union"}:
        for child in expression.children:
            collect_expression_iris(child, values)
        return

    if expression.kind == "some":
        if expression.property_iri is not None:
            values.add(expression.property_iri)
        if expression.filler is not None:
            collect_expression_iris(expression.filler, values)
        return

    raise ValueError(
        f"Unsupported expression kind: {expression.kind}"
    )


def governed_target_iris(
    canonical_rows: Iterable,
) -> set[str]:
    targets: set[str] = set()

    for row in canonical_rows:
        targets.add(row.subject_iri)

        if row.expression is not None:
            collect_expression_iris(
                row.expression,
                targets,
            )

        if row.target_property_iri is not None:
            targets.add(row.target_property_iri)

    return targets


def governed_seed_terms(
    canonical_rows: Iterable,
) -> tuple[str, ...]:
    targets = governed_target_iris(canonical_rows)
    return tuple(
        sorted(
            iri
            for iri in targets
            if iri.startswith((BFO_PREFIX, CCO_PREFIX))
        )
    )


def governed_signature(
    canonical_rows: Iterable,
) -> set[str]:
    signature = governed_target_iris(canonical_rows)

    source_graph = coms.build_source_graph()
    for row in coms.run_select_query(
        source_graph,
        Path("queries/source-classes-and-object-properties.rq"),
    ):
        signature.add(row["term"])

    return signature


def write_seed_file(
    seeds: tuple[str, ...],
    path: Path,
) -> None:
    path.write_text(
        "".join(f"{iri}\n" for iri in seeds),
        encoding="utf-8",
    )


def run_extract(
    robot: str,
    seed_path: Path,
    output_path: Path,
    *,
    strict: bool,
) -> ExtractionResult:
    output_path.unlink(missing_ok=True)

    command = [
        robot,
        "extract",
    ]

    if strict:
        command.append("--strict")

    command.extend(
        [
            "--input",
            str(DEPENDENCY),
            "--method",
            "star",
            "--term-file",
            str(seed_path),
            "--imports",
            "exclude",
            "--output-iri",
            MODULE_IRI,
            "--output",
            str(output_path),
        ]
    )

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    output_exists = output_path.is_file()

    return ExtractionResult(
        return_code=completed.returncode,
        output=reconstruction.combined_process_output(
            completed.stdout,
            completed.stderr,
        ),
        output_exists=output_exists,
        output_bytes=(
            output_path.stat().st_size
            if output_exists
            else 0
        ),
    )


def canonical_axioms(graph: Graph) -> dict[str, str]:
    return {
        axiom_id: value[0]
        for axiom_id, value in modular._canonical_graph_axioms(
            graph,
            ignore_unsupported=True,
        ).items()
    }


def missing_seed_declarations(
    graph: Graph,
    seeds: Iterable[str],
) -> list[str]:
    return [
        iri
        for iri in seeds
        if not any(
            (
                URIRef(iri),
                RDF.type,
                declaration_type,
            )
            in graph
            for declaration_type in DECLARATION_TYPES
        )
    ]


def synthetic_error_iris(graph: Graph) -> list[str]:
    return sorted(
        {
            str(term)
            for triple in graph
            for term in triple
            if isinstance(term, URIRef)
            and str(term).startswith(
                "http://org.semanticweb.owlapi/error#"
            )
        }
    )


def governed_axioms(
    path: Path,
    signature: set[str],
) -> dict[str, str]:
    graph = Graph().parse(path, format="turtle")
    selected: dict[str, str] = {}

    for axiom_id, expression in canonical_axioms(graph).items():
        named_iris = {
            iri
            for iri in IRI_RE.findall(expression)
            if not iri.startswith(BUILTIN_PREFIXES)
        }

        if named_iris and named_iris.issubset(signature):
            selected[axiom_id] = expression

    return selected


def axiom_comparison(
    expected: dict[str, str],
    actual: dict[str, str],
) -> dict[str, object]:
    expected_ids = set(expected)
    actual_ids = set(actual)
    shared = expected_ids & actual_ids

    missing = sorted(expected_ids - actual_ids)
    extra = sorted(actual_ids - expected_ids)
    mismatched = sorted(
        axiom_id
        for axiom_id in shared
        if expected[axiom_id] != actual[axiom_id]
    )

    return {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing_axiom_ids": missing,
        "extra_axiom_ids": extra,
        "mismatched_axiom_ids": mismatched,
        "passed": not missing and not extra and not mismatched,
    }


def hermit_result_summary(result) -> dict[str, object]:
    return {
        "return_code": result.return_code,
        "reasoned_output_produced": (
            result.reasoned_output_produced
        ),
        "unsat_count": len(result.unsat_classes),
        "unsat_classes": [
            str(value)
            for value in result.unsat_classes
        ],
        "passed": result.passed,
        "robot_output": result.robot_output,
    }


def reasoning_comparison(
    *,
    name: str,
    generated_path: Path,
    product_paths: tuple[Path, ...],
    profile,
    module_path: Path,
    signature: set[str],
    output_dir: Path,
) -> dict[str, object]:
    serialized_products = tuple(
        path.read_bytes()
        for path in product_paths
    )
    source_dependencies = tuple(
        REPO_ROOT / path
        for path in coms.SOURCE_IMPORTS
    )

    baseline_closure = modular.build_fixed_validation_closure(
        serialized_products,
        (
            DEPENDENCY,
            *source_dependencies,
        ),
        coms.CLEANUP_TRIPLES,
    )
    module_closure = modular.build_fixed_validation_closure(
        serialized_products,
        (
            module_path,
            *source_dependencies,
        ),
        coms.CLEANUP_TRIPLES,
    )

    baseline = coms._run_hermit_closure(
        generated_path,
        baseline_closure,
        output_dir / f"{name}-baseline",
        profile,
        validate_profile=False,
    )
    module = coms._run_hermit_closure(
        generated_path,
        module_closure,
        output_dir / f"{name}-module",
        profile,
        validate_profile=False,
    )

    baseline_axioms = (
        governed_axioms(
            baseline.reasoned_path,
            signature,
        )
        if baseline.reasoned_output_produced
        else {}
    )
    module_axioms = (
        governed_axioms(
            module.reasoned_path,
            signature,
        )
        if module.reasoned_output_produced
        else {}
    )
    comparison = axiom_comparison(
        baseline_axioms,
        module_axioms,
    )

    passed = (
        baseline.passed
        and module.passed
        and baseline.return_code == 0
        and module.return_code == 0
        and baseline.reasoned_output_produced
        and module.reasoned_output_produced
        and len(baseline.unsat_classes) == 0
        and len(module.unsat_classes) == 0
        and len(module_closure) < len(baseline_closure)
        and comparison["passed"]
    )

    return {
        "passed": passed,
        "baseline_closure_triples": len(
            baseline_closure
        ),
        "module_closure_triples": len(module_closure),
        "closure_triple_reduction": (
            len(baseline_closure)
            - len(module_closure)
        ),
        "baseline": hermit_result_summary(baseline),
        "module": hermit_result_summary(module),
        "governed_axiom_comparison": comparison,
    }


def controlled_inconsistency_comparison(
    module_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    strict_path = (
        REPO_ROOT
        / "releases/current-ssn-sosa/"
        "ssn-sosa-bfo-mapping.ttl"
    )
    alignment_path = (
        REPO_ROOT
        / "releases/current-ssn-sosa/"
        "ssn-sosa-alignment-core.ttl"
    )

    products = (
        strict_path.read_bytes(),
        alignment_path.read_bytes(),
    )
    source_dependencies = tuple(
        REPO_ROOT / path
        for path in coms.SOURCE_IMPORTS
    )

    baseline_closure = modular.build_fixed_validation_closure(
        products,
        (
            DEPENDENCY,
            *source_dependencies,
        ),
        coms.CLEANUP_TRIPLES,
    )
    module_closure = modular.build_fixed_validation_closure(
        products,
        (
            module_path,
            *source_dependencies,
        ),
        coms.CLEANUP_TRIPLES,
    )

    controlled_axiom = (
        CONTROLLED_INCONSISTENCY_TERM,
        OWL.disjointWith,
        CONTROLLED_INCONSISTENCY_TERM,
    )
    baseline_closure.add(controlled_axiom)
    module_closure.add(controlled_axiom)

    baseline = coms._run_hermit_closure(
        strict_path,
        baseline_closure,
        output_dir / "inconsistent-baseline",
        coms.STRICT_BFO_HERMIT_PROFILE,
        validate_profile=False,
    )
    module = coms._run_hermit_closure(
        strict_path,
        module_closure,
        output_dir / "inconsistent-module",
        coms.STRICT_BFO_HERMIT_PROFILE,
        validate_profile=False,
    )

    diagnostic = "The ontology is inconsistent"

    passed = (
        baseline.return_code == 1
        and module.return_code == 1
        and not baseline.reasoned_output_produced
        and not module.reasoned_output_produced
        and diagnostic in baseline.robot_output
        and diagnostic in module.robot_output
    )

    return {
        "passed": passed,
        "controlled_term": str(
            CONTROLLED_INCONSISTENCY_TERM
        ),
        "baseline": hermit_result_summary(baseline),
        "module": hermit_result_summary(module),
        "same_inconsistency_diagnostic": (
            diagnostic in baseline.robot_output
            and diagnostic in module.robot_output
        ),
    }


def run_pilot(
    output_dir: Path,
    robot_path: str | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = artifact_paths(output_dir)
    robot = reconstruction.resolve_robot_path(robot_path)

    governed = reconstruction.load_governed_coms_rows(
        WORKBOOK,
    )
    seeds = governed_seed_terms(
        governed.canonical_rows,
    )
    signature = governed_signature(
        governed.canonical_rows,
    )
    write_seed_file(
        seeds,
        artifacts.seed_path,
    )

    strict_result = run_extract(
        robot,
        artifacts.seed_path,
        artifacts.strict_output_path,
        strict=True,
    )
    first_result = run_extract(
        robot,
        artifacts.seed_path,
        artifacts.first_module_path,
        strict=False,
    )
    second_result = run_extract(
        robot,
        artifacts.seed_path,
        artifacts.second_module_path,
        strict=False,
    )

    strict_error_iris = sorted(
        set(ERROR_IRI_RE.findall(strict_result.output))
    )
    strict_rejection_proven = (
        strict_result.return_code == 1
        and not strict_result.output_exists
        and len(strict_error_iris) == 4
        and strict_result.output.count(
            "Entity not properly recognized"
        )
        == 4
        and "INVALID ONTOLOGY FILE ERROR"
        in strict_result.output
    )

    first_graph = Graph().parse(
        artifacts.first_module_path,
        format="turtle",
    )
    second_graph = Graph().parse(
        artifacts.second_module_path,
        format="turtle",
    )
    source_graph = Graph().parse(
        DEPENDENCY,
        format="turtle",
    )

    first_axioms = canonical_axioms(first_graph)
    second_axioms = canonical_axioms(second_graph)
    source_axioms = canonical_axioms(source_graph)

    module_only_axioms = sorted(
        set(first_axioms) - set(source_axioms)
    )
    shared_mismatched_axioms = sorted(
        axiom_id
        for axiom_id in (
            set(first_axioms) & set(source_axioms)
        )
        if first_axioms[axiom_id]
        != source_axioms[axiom_id]
    )

    missing_seeds = missing_seed_declarations(
        first_graph,
        seeds,
    )
    module_imports = sorted(
        str(value)
        for value in first_graph.objects(
            None,
            OWL.imports,
        )
    )
    error_iris = synthetic_error_iris(first_graph)

    reproducible = (
        first_result.return_code == 0
        and second_result.return_code == 0
        and first_result.output_exists
        and second_result.output_exists
        and first_result.output == ""
        and second_result.output == ""
        and isomorphic(first_graph, second_graph)
        and first_axioms == second_axioms
        and artifacts.first_module_path.read_bytes()
        == artifacts.second_module_path.read_bytes()
    )

    module_structure_passed = (
        len(seeds) == 59
        and len(first_graph) == 3090
        and not missing_seeds
        and not module_imports
        and not error_iris
        and len(first_axioms) == 194
        and not module_only_axioms
        and not shared_mismatched_axioms
    )

    reasoning_specs = (
        (
            "strict_bfo",
            REPO_ROOT
            / "releases/current-ssn-sosa/"
            "ssn-sosa-bfo-mapping.ttl",
            (
                REPO_ROOT
                / "releases/current-ssn-sosa/"
                "ssn-sosa-bfo-mapping.ttl",
                REPO_ROOT
                / "releases/current-ssn-sosa/"
                "ssn-sosa-alignment-core.ttl",
            ),
            coms.STRICT_BFO_HERMIT_PROFILE,
        ),
        (
            "cco_extension",
            REPO_ROOT
            / "releases/current-ssn-sosa/"
            "ssn-sosa-cco-extension.ttl",
            (
                REPO_ROOT
                / "releases/current-ssn-sosa/"
                "ssn-sosa-cco-extension.ttl",
                REPO_ROOT
                / "releases/current-ssn-sosa/"
                "ssn-sosa-bfo-mapping.ttl",
                REPO_ROOT
                / "releases/current-ssn-sosa/"
                "ssn-sosa-alignment-core.ttl",
            ),
            coms.CCO_EXTENSION_HERMIT_PROFILE,
        ),
    )

    reasoning: dict[str, object] = {}
    for (
        name,
        generated_path,
        product_paths,
        profile,
    ) in reasoning_specs:
        reasoning[name] = reasoning_comparison(
            name=name,
            generated_path=generated_path,
            product_paths=product_paths,
            profile=profile,
            module_path=artifacts.first_module_path,
            signature=signature,
            output_dir=output_dir / "reasoning",
        )

    inconsistency = controlled_inconsistency_comparison(
        artifacts.first_module_path,
        output_dir / "reasoning",
    )

    reasoning_passed = all(
        result["passed"]
        for result in reasoning.values()
    )

    summary: dict[str, object] = {
        "passed": (
            strict_rejection_proven
            and reproducible
            and module_structure_passed
            and reasoning_passed
            and inconsistency["passed"]
        ),
        "robot_path": robot,
        "workbook": str(WORKBOOK),
        "dependency": str(DEPENDENCY),
        "governed_row_count": len(
            governed.canonical_rows
        ),
        "governed_signature_term_count": len(
            signature
        ),
        "seed_inventory": {
            "seed_count": len(seeds),
            "bfo_seed_count": sum(
                iri.startswith(BFO_PREFIX)
                for iri in seeds
            ),
            "cco_seed_count": sum(
                iri.startswith(CCO_PREFIX)
                for iri in seeds
            ),
            "seed_file_bytes": (
                artifacts.seed_path.stat().st_size
            ),
            "first_seed": seeds[0],
            "last_seed": seeds[-1],
        },
        "strict_extraction": {
            "rejection_proven": (
                strict_rejection_proven
            ),
            "return_code": strict_result.return_code,
            "output_exists": (
                strict_result.output_exists
            ),
            "output_bytes": strict_result.output_bytes,
            "entity_recognition_error_count": (
                strict_result.output.count(
                    "Entity not properly recognized"
                )
            ),
            "synthetic_error_iris": (
                strict_error_iris
            ),
            "robot_output": strict_result.output,
        },
        "module": {
            "passed": module_structure_passed,
            "source_triple_count": len(source_graph),
            "module_triple_count": len(first_graph),
            "source_supported_axiom_count": len(
                source_axioms
            ),
            "module_supported_axiom_count": len(
                first_axioms
            ),
            "module_only_axiom_ids": (
                module_only_axioms
            ),
            "shared_mismatched_axiom_ids": (
                shared_mismatched_axioms
            ),
            "missing_seed_declarations": (
                missing_seeds
            ),
            "owl_imports": module_imports,
            "synthetic_error_iris": error_iris,
            "sha256": sha256(
                artifacts.first_module_path
            ),
            "output_bytes": (
                artifacts.first_module_path.stat().st_size
            ),
        },
        "reproducibility": {
            "passed": reproducible,
            "first_return_code": (
                first_result.return_code
            ),
            "second_return_code": (
                second_result.return_code
            ),
            "first_robot_output": first_result.output,
            "second_robot_output": second_result.output,
            "graphs_isomorphic": isomorphic(
                first_graph,
                second_graph,
            ),
            "canonical_axioms_equal": (
                first_axioms == second_axioms
            ),
            "bytes_equal": (
                artifacts.first_module_path.read_bytes()
                == artifacts.second_module_path.read_bytes()
            ),
            "first_sha256": sha256(
                artifacts.first_module_path
            ),
            "second_sha256": sha256(
                artifacts.second_module_path
            ),
        },
        "reasoning": reasoning,
        "controlled_inconsistency": inconsistency,
        "disposition": (
            "non-strict ROBOT STAR extraction is "
            "equivalent for the current governed "
            "validation signature and may be retained "
            "as a read-only candidate; strict extraction "
            "remains incompatible and production "
            "substitution is not approved"
        ),
    }

    artifacts.summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True)
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

    strict = summary["strict_extraction"]
    module = summary["module"]
    reproducibility = summary["reproducibility"]

    print(
        "Strict extraction return code: "
        f"{strict['return_code']}"
    )
    print(
        "Strict extraction error entities: "
        f"{len(strict['synthetic_error_iris'])}"
    )
    print(
        "Governed seed terms: "
        f"{summary['seed_inventory']['seed_count']}"
    )
    print(
        "Module triples: "
        f"{module['module_triple_count']}"
    )
    print(
        "Module supported axioms: "
        f"{module['module_supported_axiom_count']}"
    )
    print(
        "Module byte reproducible: "
        f"{reproducibility['bytes_equal']}"
    )

    for name, result in summary["reasoning"].items():
        comparison = result[
            "governed_axiom_comparison"
        ]
        print(
            f"{name}: "
            f"{result['baseline_closure_triples']} -> "
            f"{result['module_closure_triples']} triples; "
            f"{comparison['expected_count']}/"
            f"{comparison['actual_count']} governed axioms; "
            f"{'PASS' if result['passed'] else 'FAIL'}"
        )

    print(
        "Controlled inconsistency equivalent: "
        f"{summary['controlled_inconsistency']['passed']}"
    )
    print(f"Disposition: {summary['disposition']}")
    print(
        "Summary: PASS"
        if summary["passed"]
        else "Summary: FAIL"
    )

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
