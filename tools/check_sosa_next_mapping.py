#!/usr/bin/env python3
"""Validate the governed forthcoming-SOSA COMS workbook without publishing products."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from rdflib import BNode, Graph, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection

import generate_mapping_from_coms as coms
import sosa_2023_mapping_status as mapping_status
import robot_reconstruction_validation as robot_validation
import sosa_source_version as source_version


REPO_ROOT = Path(__file__).resolve().parents[1]

WORKBOOK = REPO_ROOT / "mappings/SOSA-next-to-BFO-COMS.xlsx"
CATALOG = REPO_ROOT / "src/sosa-next/catalog-v001.xml"

TARGET_CCO = REPO_ROOT / "src/sosa-next/imports/cco.ttl"
TARGET_CCO_SHA256 = (
    "0daf917353420073ddd9bbd581c7fb84"
    "effdc050b934a7a4678cd34dda708f26"
)
TARGET_CCO_ONTOLOGY_IRI = (
    "https://www.commoncoreontologies.org/"
    "CommonCoreOntologiesMerged"
)
TARGET_CCO_VERSION_IRI = (
    "https://www.commoncoreontologies.org/"
    "2026-04-04/CommonCoreOntologiesMerged"
)
TARGET_CCO_UPSTREAM_REPOSITORY = (
    "https://github.com/CommonCoreOntology/"
    "CommonCoreOntologies"
)
TARGET_CCO_UPSTREAM_COMMIT = (
    "010c99847a856e2fb70eb1b1b1287d19556c9290"
)
TARGET_CCO_UPSTREAM_PATH = (
    "src/cco-iris/CommonCoreOntologiesMerged.ttl"
)


SOURCE_VERSION_AUTHORITY = (
    source_version.load_source_version_authority()
)
SOURCE_VERSION_CONFIG = source_version.CONFIG_PATH
SOURCE_IDENTITY = SOURCE_VERSION_AUTHORITY.source_identity

SOURCE_FILES = tuple(
    REPO_ROOT / item.local_path
    for item in SOURCE_VERSION_AUTHORITY.source_files
) + (
    REPO_ROOT / SOURCE_VERSION_AUTHORITY.overlay_path,
)

PINNED_SOURCE_SHA256 = {
    REPO_ROOT / item.local_path: item.sha256
    for item in SOURCE_VERSION_AUTHORITY.source_files
}
PINNED_SOURCE_SHA256[
    REPO_ROOT / SOURCE_VERSION_AUTHORITY.overlay_path
] = SOURCE_VERSION_AUTHORITY.overlay_sha256

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


def validate_source_pins() -> dict[str, str]:
    """Validate governed source bytes through the source authority."""

    return source_version.validate_source_version_files(
        SOURCE_VERSION_AUTHORITY,
        REPO_ROOT,
    )


def validate_target_cco_pin() -> str:
    """Validate the SOSA-2023-specific merged CCO/BFO target dependency."""

    if not TARGET_CCO.is_file():
        raise RuntimeError(
            f"Required SOSA-2023 CCO target is missing: {TARGET_CCO}"
        )

    digest = source_version.sha256_file(TARGET_CCO)

    if digest != TARGET_CCO_SHA256:
        raise RuntimeError(
            "SOSA-2023 CCO target SHA-256 mismatch: "
            f"expected {TARGET_CCO_SHA256}; found {digest}"
        )

    graph = Graph().parse(
        TARGET_CCO,
        format="turtle",
    )

    ontology = URIRef(
        TARGET_CCO_ONTOLOGY_IRI
    )

    if (
        ontology,
        RDF.type,
        OWL.Ontology,
    ) not in graph:
        raise RuntimeError(
            "SOSA-2023 CCO target lacks the expected ontology declaration."
        )

    version_iri = URIRef(
        TARGET_CCO_VERSION_IRI
    )

    if (
        ontology,
        OWL.versionIRI,
        version_iri,
    ) not in graph:
        raise RuntimeError(
            "SOSA-2023 CCO target lacks the expected version IRI."
        )

    sensor = URIRef(
        "https://www.commoncoreontologies.org/ont00000569"
    )

    if not any(
        graph.objects(
            sensor,
            OWL.equivalentClass,
        )
    ):
        raise RuntimeError(
            "Selected CCO target does not contain the expected "
            "cco:Sensor equivalence axiom."
        )

    return digest

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
        "bfo": Path("src/sosa-next/imports/cco.ttl"),
        "cco": Path("src/sosa-next/imports/cco.ttl"),
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
    """Resolve a governed SOSA source CURIE, including datatype properties."""

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
    target_cco_sha256 = validate_target_cco_pin()
    source_authority_sha256 = source_version.sha256_file(
        SOURCE_VERSION_CONFIG
    )
    source_graph = build_merged_source(merged_source_path)

    rows, workbook_stats = coms.read_workbook(WORKBOOK)
    coms.validate_workbook_row_ids(rows, workbook_stats)

    classification = mapping_status.classify_workbook_rows(
        rows
    )

    active_rows = list(
        classification.active
    )
    deferred_rows = list(
        classification.deferred
    )
    no_direct_mapping_rows = list(
        classification.no_direct_mapping
    )
    unreviewed_rows = list(
        classification.unreviewed
    )

    # Temporary compatibility aggregate for callers that still
    # use the pre-MappingStatus SOSA-2023 summary vocabulary.
    explicitly_unmapped_rows = [
        row
        for row in rows
        if row.mapping_status_text
        in {
            mapping_status.NO_DIRECT_MAPPING,
            mapping_status.UNREVIEWED,
        }
    ]

    malformed_rows: list[coms.WorkbookRow] = []

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

    no_direct_mapping_evidence = []

    for row in no_direct_mapping_rows:
        iri, kind = source_kind(
            row.subject_text,
            source_graph,
        )
        no_direct_mapping_evidence.append(
            {
                "location": str(row.location),
                "row_id": row.stable_row_id,
                "subject": row.subject_text,
                "subject_iri": str(iri),
                "subject_kind": kind,
                "reasoning": row.reasoning_text,
            }
        )

    unreviewed_evidence = []

    for row in unreviewed_rows:
        iri, kind = source_kind(
            row.subject_text,
            source_graph,
        )
        unreviewed_evidence.append(
            {
                "location": str(row.location),
                "row_id": row.stable_row_id,
                "subject": row.subject_text,
                "subject_iri": str(iri),
                "subject_kind": kind,
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

    previous_prefix_files = dict(coms.PREFIX_FILES)
    previous_source_imports = tuple(coms.SOURCE_IMPORTS)
    configure_coms_resolver(merged_source_path)

    try:
        processed = coms.validate_and_process_rows(
            active_rows,
            coms.Resolver(),
            active_stats,
        )
    finally:
        coms.PREFIX_FILES = previous_prefix_files
        coms.SOURCE_IMPORTS = previous_source_imports

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
        "source_identity": SOURCE_IDENTITY,
        "source_version_authority": (
            SOURCE_VERSION_CONFIG.relative_to(REPO_ROOT).as_posix()
        ),
        "source_version_authority_sha256": (
            source_authority_sha256
        ),
        "source_edition_version_iri": (
            SOURCE_VERSION_AUTHORITY.edition_version_iri
        ),
        "source_upstream_commit": (
            SOURCE_VERSION_AUTHORITY.upstream_commit
        ),
        "source_files": [str(path) for path in SOURCE_FILES],
        "source_sha256": source_hashes,
        "target_cco_path": str(TARGET_CCO.relative_to(REPO_ROOT)),
        "target_cco_sha256": target_cco_sha256,
        "target_cco_ontology_iri": TARGET_CCO_ONTOLOGY_IRI,
        "target_cco_version_iri": TARGET_CCO_VERSION_IRI,
        "target_cco_upstream_repository": TARGET_CCO_UPSTREAM_REPOSITORY,
        "target_cco_upstream_commit": TARGET_CCO_UPSTREAM_COMMIT,
        "target_cco_upstream_path": TARGET_CCO_UPSTREAM_PATH,
        "source_triple_count": len(source_graph),
        "governed_row_count": len(rows),
        "unique_row_id_count": workbook_stats.unique_row_id_count,
        "active_mapping_count": len(active_rows),
        "deferred_mapping_count": len(deferred_rows),
        "no_direct_mapping_row_count": len(
            no_direct_mapping_rows
        ),
        "unreviewed_row_count": len(unreviewed_rows),
        "explicitly_unmapped_row_count": len(
            explicitly_unmapped_rows
        ),
        "malformed_row_count": len(malformed_rows),
        "canonical_authoritative_axiom_count": (
            authoritative_axiom_count
        ),
        "active_ontology_triple_count": len(active_graph),
        "deferred_mappings": deferred_evidence,
        "no_direct_mapping_rows": no_direct_mapping_evidence,
        "unreviewed_rows": unreviewed_evidence,
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
        "No-direct-mapping decisions: "
        f"{summary['no_direct_mapping_row_count']}"
    )
    print(
        "Unreviewed rows: "
        f"{summary['unreviewed_row_count']}"
    )
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
