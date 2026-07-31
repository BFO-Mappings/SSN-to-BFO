#!/usr/bin/env python3
"""Validate the governed forthcoming-SOSA COMS workbook without publishing products."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from rdflib import BNode, Graph, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection

import generate_mapping_from_coms as coms
import robot_reconstruction_validation as robot_validation


REPO_ROOT = Path(__file__).resolve().parents[1]

WORKBOOK = REPO_ROOT / "mappings/SOSA-next-to-BFO-COMS.xlsx"
CATALOG = REPO_ROOT / "src/sosa-next/catalog-v001.xml"

SOURCE_FILES = (
    REPO_ROOT / "src/sosa-next/imports/sosa.ttl",
    REPO_ROOT / "src/sosa-next/imports/sosa-common.ttl",
    REPO_ROOT / "src/sosa-next/imports/sosa-observation.ttl",
    REPO_ROOT / "src/sosa-next/imports/sosa-actuation.ttl",
    REPO_ROOT / "src/sosa-next/imports/sosa-sampling.ttl",
    REPO_ROOT / "src/sosa-next/imports/sosa-deprecated.ttl",
    REPO_ROOT / "src/sosa-next/imports/sosa-system.ttl",
    REPO_ROOT / "src/sosa-next/imports/sample-relations.ttl",
    REPO_ROOT
    / "src/sosa-next/imports/sosa-source-declaration-overlay.ttl",
)

PINNED_SOURCE_SHA256 = {
    SOURCE_FILES[0]:
        "a1875d19988b0bd17e5cd3a61f76440b6e0f7b1e07bd30237e6fb7341c170305",
    SOURCE_FILES[1]:
        "31bb4a6fb3d4b8b7612998744f73b5a8194d34ef866184460ed22dc0f78a91aa",
    SOURCE_FILES[2]:
        "da6b3b2304a491c45a8822e70529f72c1d73606dda9a8b73b0c5360313ab30c3",
    SOURCE_FILES[3]:
        "18c840cba0a4e148048e6147cb2b5fa9b36bbf09dcb60802ce65d3ecfb3175c5",
    SOURCE_FILES[4]:
        "82e59f8354debaff6cdcb3e354397ea17318e4bc45dc7a8a005c1fa5404d2d70",
    SOURCE_FILES[5]:
        "5a99055ea8938f0e9384b81ad3ac1b3eaa13aaf50c54e308cab9551c88392987",
    SOURCE_FILES[6]:
        "1ac64f168163b7e6139bf632a07e35112837a58021ff706688d2c626e9cc1caf",
    SOURCE_FILES[7]:
        "0f9c8561626e9c75cb364d3c0f6cdb3197e9e72b6727b095309fc3fb1d605e32",
    SOURCE_FILES[8]:
        "5cee7b4c6799df0ebff5f4c503b7495fce67f940c53711a2aecfa6896f8d3af2",
}

ONTOLOGY_IRI = URIRef(
    "http://www.sks.ai/SSN2BFO/development/sosa-next/active-mappings"
)

DIRECT_IMPORTS = (
    URIRef("http://www.w3.org/ns/sosa/"),
    URIRef("http://www.w3.org/ns/sosa/systems/"),
    URIRef("http://www.w3.org/ns/sosa/sampling/"),
    URIRef(
        "http://www.sks.ai/SSN2BFO/development/"
        "sosa-next/source-declaration-overlay"
    ),
    URIRef(
        "https://www.commoncoreontologies.org/"
        "CommonCoreOntologiesMerged"
    ),
)

SOURCE_NAMESPACES = {
    "sosa": "http://www.w3.org/ns/sosa/",
    "sampling": "http://www.w3.org/ns/sosa/sampling/",
}


def sha256_file(path: Path) -> str:
    """Return a bounded-memory SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_source_pins() -> dict[str, str]:
    """Require every governed source file to match its pinned digest."""

    actual = {}

    for path, expected in PINNED_SOURCE_SHA256.items():
        if not path.is_file():
            raise RuntimeError(f"Required pinned source is missing: {path}")

        digest = sha256_file(path)
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        actual[relative_path] = digest

        if digest != expected:
            raise RuntimeError(
                f"Pinned source SHA-256 mismatch for {relative_path}: "
                f"expected {expected}, got {digest}"
            )

    return actual


def resolve_robot(robot_path: str | None) -> str:
    """Resolve an explicit ROBOT path or use the governed installer."""

    if robot_path:
        return robot_validation.resolve_robot_path(robot_path)

    installer = subprocess.run(
        [str(REPO_ROOT / "tools/install_validation_robot.sh")],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return str(Path(installer.stdout.strip()) / "robot")


def configure_coms_resolver(merged_source: Path) -> None:
    """Point the shared COMS parser at the pinned forthcoming SOSA source."""

    coms.PREFIX_FILES = {
        "bfo": Path("imports/cco.ttl"),
        "cco": Path("imports/cco.ttl"),
        "sampling": merged_source,
        "sosa": merged_source,
    }
    coms.SOURCE_IMPORTS = (merged_source,)


def build_merged_source(output_path: Path) -> Graph:
    """Merge the pinned source modules for local token resolution."""

    graph = Graph()

    for path in SOURCE_FILES:
        if not path.is_file():
            raise RuntimeError(f"Required source file is missing: {path}")
        graph.parse(path, format="turtle")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(output_path, format="turtle")
    return graph


def source_kind(
    lexical: str,
    source_graph: Graph,
) -> tuple[URIRef, str]:
    """Resolve a SOSA source CURIE, including deferred datatype properties."""

    if ":" not in lexical:
        raise RuntimeError(f"Source term is not a CURIE: {lexical!r}")

    prefix, local = lexical.split(":", 1)
    namespace = SOURCE_NAMESPACES.get(prefix)

    if namespace is None:
        raise RuntimeError(
            f"Unsupported SOSA-next source prefix in {lexical!r}"
        )

    iri = URIRef(namespace + local)
    kinds = set()

    if (
        (iri, RDF.type, OWL.Class) in source_graph
        or (iri, RDF.type, RDFS.Class) in source_graph
    ):
        kinds.add("class")

    if (iri, RDF.type, OWL.ObjectProperty) in source_graph:
        kinds.add("object_property")

    if (iri, RDF.type, OWL.DatatypeProperty) in source_graph:
        kinds.add("datatype_property")

    if not kinds:
        raise RuntimeError(
            f"Source term is not explicitly declared in the pinned "
            f"SOSA-next source or overlay: {lexical}"
        )

    if len(kinds) != 1:
        raise RuntimeError(
            f"Source term has ambiguous kinds {sorted(kinds)}: {lexical}"
        )

    return iri, next(iter(kinds))


def render_active_ontology(
    processed_rows: list[coms.ProcessedRow],
    output_path: Path,
) -> Graph:
    """Render active governed mappings as a temporary ontology."""

    graph = Graph()
    coms.bind_prefixes(graph)
    graph.bind(
        "sosa-rel",
        Namespace("http://www.w3.org/ns/sosa/sampling/"),
    )

    graph.add((ONTOLOGY_IRI, RDF.type, OWL.Ontology))

    for import_iri in DIRECT_IMPORTS:
        graph.add((ONTOLOGY_IRI, OWL.imports, import_iri))

    for item in processed_rows:
        predicate = coms.ALLOWED_PREDICATES[item.predicate]

        if item.expr is not None:
            graph.add(
                (
                    item.subject,
                    predicate,
                    coms.expr_to_rdf(graph, item.expr),
                )
            )
        elif item.target_property is not None:
            graph.add(
                (
                    item.subject,
                    predicate,
                    item.target_property,
                )
            )
        elif item.property_chain:
            chain_node = BNode()
            Collection(
                graph,
                chain_node,
                list(item.property_chain),
            )
            graph.add(
                (
                    item.subject,
                    OWL.propertyChainAxiom,
                    chain_node,
                )
            )
        else:
            raise RuntimeError(
                f"{item.row.diagnostic_id}: processed row has no target"
            )

    graph.serialize(output_path, format="turtle")
    return graph


def run_reasoner(
    robot: str,
    ontology_path: Path,
    reasoned_path: Path,
    unsat_path: Path,
) -> dict[str, object]:
    """Run governed ROBOT/HermiT over the active mapping ontology."""

    reasoned_path.unlink(missing_ok=True)
    unsat_path.unlink(missing_ok=True)

    completed = subprocess.run(
        [
            robot,
            "reason",
            "--catalog",
            str(CATALOG),
            "--input",
            str(ontology_path),
            "--reasoner",
            "HermiT",
            "--dump-unsatisfiable",
            str(unsat_path),
            "--output",
            str(reasoned_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    output = robot_validation.combined_process_output(
        completed.stdout,
        completed.stderr,
    )

    named_unsats = sorted(
        set(re.findall(r"unsatisfiable:\s+(\S+)", output))
    )

    reasoned_triples = None
    if reasoned_path.is_file():
        reasoned_triples = len(
            Graph().parse(reasoned_path, format="turtle")
        )

    passed = (
        completed.returncode == 0
        and reasoned_path.is_file()
        and not named_unsats
    )

    return {
        "return_code": completed.returncode,
        "robot_output": output,
        "reasoned_output_exists": reasoned_path.is_file(),
        "reasoned_output_triples": reasoned_triples,
        "unsatisfiable_classes": named_unsats,
        "passed": passed,
    }


def run_check(
    output_dir: Path,
    robot_path: str | None = None,
) -> dict[str, object]:
    """Validate the SOSA-next workbook and reason over all active mappings."""

    output_dir = output_dir.resolve()
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    merged_source_path = output_dir / "sosa-next-source-merged.ttl"
    active_ontology_path = output_dir / "active-mappings.ttl"
    reasoned_path = output_dir / "active-mappings-reasoned.ttl"
    unsat_path = output_dir / "active-mappings-unsatisfiable.ttl"
    summary_path = output_dir / "summary.json"

    source_hashes = validate_source_pins()
    source_graph = build_merged_source(merged_source_path)
    configure_coms_resolver(merged_source_path)

    rows, workbook_stats = coms.read_workbook(WORKBOOK)
    coms.validate_workbook_row_ids(rows, workbook_stats)

    active_rows = [
        row
        for row in rows
        if (
            row.subject_text
            and row.predicate_text
            and row.target_text
        )
    ]
    deferred_rows = [
        row
        for row in rows
        if (
            row.subject_text
            and not row.predicate_text
            and not row.target_text
            and row.reasoning_text
        )
    ]
    explicitly_unmapped_rows = [
        row
        for row in rows
        if (
            row.subject_text
            and not row.predicate_text
            and not row.target_text
            and not row.reasoning_text
        )
    ]
    malformed_rows = [
        row
        for row in rows
        if (
            row not in active_rows
            and row not in deferred_rows
            and row not in explicitly_unmapped_rows
        )
    ]

    if malformed_rows:
        descriptions = [
            (
                f"{row.diagnostic_id}: subject={row.subject_text!r}; "
                f"predicate={row.predicate_text!r}; "
                f"target={row.target_text!r}"
            )
            for row in malformed_rows
        ]
        raise RuntimeError(
            "Malformed governed workbook rows:\n"
            + "\n".join(descriptions)
        )

    deferred_evidence = []

    for row in deferred_rows:
        iri, kind = source_kind(row.subject_text, source_graph)
        deferred_evidence.append(
            {
                "location": str(row.location),
                "row_id": row.stable_row_id,
                "subject": row.subject_text,
                "subject_iri": str(iri),
                "subject_kind": kind,
                "reasoning": row.reasoning_text,
            }
        )

    explicitly_unmapped_evidence = []

    for row in explicitly_unmapped_rows:
        iri, kind = source_kind(row.subject_text, source_graph)
        explicitly_unmapped_evidence.append(
            {
                "location": str(row.location),
                "row_id": row.stable_row_id,
                "subject": row.subject_text,
                "subject_iri": str(iri),
                "subject_kind": kind,
            }
        )

    active_stats = coms.WorkbookStats(
        worksheets_read=list(workbook_stats.worksheets_read),
    )
    processed = coms.validate_and_process_rows(
        active_rows,
        coms.Resolver(),
        active_stats,
    )

    active_graph = render_active_ontology(
        processed,
        active_ontology_path,
    )

    robot = resolve_robot(robot_path)
    reasoning = run_reasoner(
        robot,
        active_ontology_path,
        reasoned_path,
        unsat_path,
    )

    authoritative_axiom_count = sum(
        len(item.identity_audit.authoritative_axioms)
        for item in processed
        if item.identity_audit is not None
    )

    passed = (
        workbook_stats.governed_row_id_count == len(rows)
        and workbook_stats.unique_row_id_count == len(rows)
        and not malformed_rows
        and (
            len(active_rows)
            + len(deferred_rows)
            + len(explicitly_unmapped_rows)
            == len(rows)
        )
        and len(processed) == len(active_rows)
        and authoritative_axiom_count == len(active_rows)
        and reasoning["passed"]
    )

    summary: dict[str, object] = {
        "workbook": str(WORKBOOK),
        "catalog": str(CATALOG),
        "robot_path": robot,
        "source_files": [str(path) for path in SOURCE_FILES],
        "source_sha256": source_hashes,
        "source_triple_count": len(source_graph),
        "governed_row_count": len(rows),
        "unique_row_id_count": workbook_stats.unique_row_id_count,
        "active_mapping_count": len(active_rows),
        "deferred_mapping_count": len(deferred_rows),
        "explicitly_unmapped_row_count": len(
            explicitly_unmapped_rows
        ),
        "malformed_row_count": len(malformed_rows),
        "canonical_authoritative_axiom_count": (
            authoritative_axiom_count
        ),
        "active_ontology_triple_count": len(active_graph),
        "deferred_mappings": deferred_evidence,
        "explicitly_unmapped_rows": explicitly_unmapped_evidence,
        "reasoning": reasoning,
        "passed": passed,
    }

    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="/tmp/sosa-next-mapping-check",
        help="Directory for temporary validation evidence.",
    )
    parser.add_argument(
        "--robot",
        help="Optional explicit ROBOT executable path.",
    )
    args = parser.parse_args(argv)

    try:
        summary = run_check(
            Path(args.output_dir),
            args.robot,
        )
    except Exception as exc:
        print(f"SOSA-next COMS validation: FAIL\n{exc}")
        return 1

    reasoning = summary["reasoning"]

    print(f"Governed rows: {summary['governed_row_count']}")
    print(f"Unique RowIDs: {summary['unique_row_id_count']}")
    print(f"Active mappings: {summary['active_mapping_count']}")
    print(f"Deferred mappings: {summary['deferred_mapping_count']}")
    print(
        "Explicitly unmapped rows: "
        f"{summary['explicitly_unmapped_row_count']}"
    )
    print(
        "Canonical authoritative axioms: "
        f"{summary['canonical_authoritative_axiom_count']}"
    )
    print(
        "Active ontology triples: "
        f"{summary['active_ontology_triple_count']}"
    )
    print(
        "Reasoned output triples: "
        f"{reasoning['reasoned_output_triples']}"
    )
    print(
        "Named unsatisfiable classes: "
        f"{len(reasoning['unsatisfiable_classes'])}"
    )

    for term in reasoning["unsatisfiable_classes"]:
        print(f"  UNSAT: {term}")

    if reasoning["robot_output"] and not reasoning["passed"]:
        print("--- ROBOT output ---")
        print(reasoning["robot_output"])

    print(f"Summary: {'PASS' if summary['passed'] else 'FAIL'}")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
