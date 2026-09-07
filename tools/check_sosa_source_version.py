#!/usr/bin/env python3
"""Validate the approved immutable SOSA source-version authority."""

from __future__ import annotations

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF

import sosa_source_version as source_version


ROOT_SOSA_ONTOLOGY = URIRef("http://www.w3.org/ns/sosa/")


def run_check() -> dict[str, object]:
    authority = source_version.load_source_version_authority()
    source_hashes = source_version.validate_source_version_files(authority)

    root_entries = [
        item
        for item in authority.source_files
        if item.local_path == "src/sosa-next/imports/sosa.ttl"
    ]
    if len(root_entries) != 1:
        raise RuntimeError(
            "Source authority must contain exactly one root sosa.ttl entry"
        )

    root_graph = Graph()
    root_graph.parse(
        source_version.REPO_ROOT / root_entries[0].local_path,
        format="turtle",
    )

    ontology_declarations = set(
        root_graph.triples((None, RDF.type, OWL.Ontology))
    )
    if ontology_declarations != {
        (ROOT_SOSA_ONTOLOGY, RDF.type, OWL.Ontology)
    }:
        raise RuntimeError(
            "Pinned root SOSA file has unexpected ontology declaration"
        )

    version_iris = {
        str(value)
        for value in root_graph.objects(
            ROOT_SOSA_ONTOLOGY,
            OWL.versionIRI,
        )
    }
    if version_iris != {authority.edition_version_iri}:
        raise RuntimeError(
            "Pinned root SOSA versionIRI does not match source authority: "
            f"{sorted(version_iris)}"
        )

    overlay_graph = Graph()
    overlay_graph.parse(
        source_version.REPO_ROOT / authority.overlay_path,
        format="turtle",
    )
    overlay_version_info = {
        str(value)
        for value in overlay_graph.objects(None, OWL.versionInfo)
    }
    expected_overlay_text = (
        f"Upstream commit {authority.upstream_commit}"
    )
    if expected_overlay_text not in overlay_version_info:
        raise RuntimeError(
            "Local source-declaration overlay does not record the approved "
            "upstream commit"
        )

    return {
        "schema_version": authority.schema_version,
        "status": authority.status,
        "source_identity": authority.source_identity,
        "development_alias": authority.development_alias,
        "edition_label": authority.edition_label,
        "edition_version_iri": authority.edition_version_iri,
        "upstream_repository": authority.upstream_repository,
        "upstream_commit": authority.upstream_commit,
        "upstream_commit_date": authority.upstream_commit_date,
        "upstream_source_file_count": len(authority.source_files),
        "local_overlay_path": authority.overlay_path,
        "source_sha256": source_hashes,
        "passed": True,
    }


def main() -> int:
    try:
        summary = run_check()
    except Exception as exc:
        print(f"SOSA source-version authority: FAIL\n{exc}")
        return 1

    print(f"Status: {summary['status']}")
    print(f"Source identity: {summary['source_identity']}")
    print(f"Development alias: {summary['development_alias']}")
    print(f"Edition: {summary['edition_label']}")
    print(f"Edition version IRI: {summary['edition_version_iri']}")
    print(f"Upstream repository: {summary['upstream_repository']}")
    print(f"Upstream commit: {summary['upstream_commit']}")
    print(f"Upstream commit date: {summary['upstream_commit_date']}")
    print(
        "Upstream source files: "
        f"{summary['upstream_source_file_count']}"
    )
    print(f"Local overlay: {summary['local_overlay_path']}")

    for file_path, digest in sorted(
        summary["source_sha256"].items()
    ):
        print(f"  {digest}  {file_path}")

    print("Summary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
