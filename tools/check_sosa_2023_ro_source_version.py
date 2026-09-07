#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import re
import sys
import tomllib
from pathlib import Path

from rdflib import Graph, OWL, RDF, URIRef


REPO_ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = (
    REPO_ROOT
    / "config/sosa-2023-ro-source-version.toml"
)

EXPECTED_AUTHORITY = {
    "status": "approved",
    "track": "sosa-2023",
    "dependency": "relations-ontology",
    "release_tag": "v2025-12-17",
    "upstream_repository":
        "https://github.com/oborel/obo-relations",
    "upstream_commit":
        "13620e1d75465c6504c755d2fdfa706922e9b7e7",
    "local_path":
        "src/sosa-next/imports/ro-full.owl",
}


class SourceVersionError(RuntimeError):
    pass


def sha256_file(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise SourceVersionError(
            f"missing config: {CONFIG_PATH}"
        )

    with CONFIG_PATH.open("rb") as handle:
        data = tomllib.load(handle)

    if data.get("schema_version") != 1:
        raise SourceVersionError(
            "schema_version must be 1"
        )

    source = data.get("source")

    if not isinstance(source, dict):
        raise SourceVersionError(
            "missing [source] table"
        )

    return source


def validate() -> dict:
    source = load_config()

    for field, expected in (
        EXPECTED_AUTHORITY.items()
    ):
        observed = source.get(field)

        if observed != expected:
            raise SourceVersionError(
                f"{field}: expected "
                f"{expected!r}; "
                f"observed {observed!r}"
            )

    commit = source.get(
        "upstream_commit",
        "",
    )

    if not re.fullmatch(
        r"[0-9a-f]{40}",
        commit,
    ):
        raise SourceVersionError(
            "upstream_commit must be "
            "a lowercase 40-hex commit"
        )

    expected_sha = source.get(
        "sha256",
        "",
    )

    if not re.fullmatch(
        r"[0-9a-f]{64}",
        expected_sha,
    ):
        raise SourceVersionError(
            "sha256 must be a lowercase "
            "64-hex digest"
        )

    local_relative = Path(
        source["local_path"]
    )

    if (
        local_relative.is_absolute()
        or ".." in local_relative.parts
    ):
        raise SourceVersionError(
            "local_path must be a "
            "repository-relative path"
        )

    local_path = (
        REPO_ROOT
        / local_relative
    )

    if not local_path.is_file():
        raise SourceVersionError(
            f"missing pinned source: "
            f"{local_relative}"
        )

    observed_sha = sha256_file(
        local_path
    )

    if observed_sha != expected_sha:
        raise SourceVersionError(
            "pinned RO SHA-256 mismatch: "
            f"expected {expected_sha}; "
            f"observed {observed_sha}"
        )

    graph = Graph()
    graph.parse(
        local_path
    )

    expected_triples = source.get(
        "triple_count"
    )

    if (
        not isinstance(
            expected_triples,
            int,
        )
        or isinstance(
            expected_triples,
            bool,
        )
        or expected_triples < 1
    ):
        raise SourceVersionError(
            "triple_count must be a "
            "positive integer"
        )

    if len(graph) != expected_triples:
        raise SourceVersionError(
            "RO triple-count mismatch: "
            f"expected {expected_triples}; "
            f"observed {len(graph)}"
        )

    ontology_iris = sorted(
        {
            str(subject)
            for subject in graph.subjects(
                RDF.type,
                OWL.Ontology,
            )
            if isinstance(
                subject,
                URIRef,
            )
        }
    )

    expected_ontology = source.get(
        "ontology_iri",
        "",
    )

    if ontology_iris != [
        expected_ontology
    ]:
        raise SourceVersionError(
            "ontology IRI mismatch: "
            f"expected "
            f"{[expected_ontology]!r}; "
            f"observed "
            f"{ontology_iris!r}"
        )

    ontology_iri = URIRef(
        expected_ontology
    )

    version_iris = sorted(
        {
            str(value)
            for value in graph.objects(
                ontology_iri,
                OWL.versionIRI,
            )
            if isinstance(
                value,
                URIRef,
            )
        }
    )

    expected_version = source.get(
        "version_iri",
        "",
    )

    expected_versions = (
        [expected_version]
        if expected_version
        else []
    )

    if version_iris != expected_versions:
        raise SourceVersionError(
            "version IRI mismatch: "
            f"expected "
            f"{expected_versions!r}; "
            f"observed "
            f"{version_iris!r}"
        )

    imports = sorted(
        {
            str(value)
            for value in graph.objects(
                ontology_iri,
                OWL.imports,
            )
            if isinstance(
                value,
                URIRef,
            )
        }
    )

    expected_imports = source.get(
        "imports"
    )

    if not isinstance(
        expected_imports,
        list,
    ):
        raise SourceVersionError(
            "imports must be a list"
        )

    if imports != expected_imports:
        raise SourceVersionError(
            "owl:imports mismatch: "
            f"expected "
            f"{expected_imports!r}; "
            f"observed {imports!r}"
        )

    if source.get(
        "import_count"
    ) != len(imports):
        raise SourceVersionError(
            "import_count mismatch"
        )

    return {
        "source": source,
        "path": local_relative,
        "sha256": observed_sha,
        "triple_count": len(graph),
        "imports": imports,
    }


def main() -> int:
    try:
        result = validate()
    except SourceVersionError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    source = result["source"]

    print(
        "Status:",
        source["status"],
    )

    print(
        "Track:",
        source["track"],
    )

    print(
        "Dependency:",
        source["dependency"],
    )

    print(
        "Release tag:",
        source["release_tag"],
    )

    print(
        "Upstream repository:",
        source[
            "upstream_repository"
        ],
    )

    print(
        "Upstream commit:",
        source[
            "upstream_commit"
        ],
    )

    print(
        "Upstream commit date:",
        source[
            "upstream_commit_date"
        ],
    )

    print(
        "Ontology IRI:",
        source["ontology_iri"],
    )

    print(
        "Version IRI:",
        source["version_iri"]
        or "(none)",
    )

    print(
        "Pinned source:",
        result["path"],
    )

    print(
        "SHA-256:",
        result["sha256"],
    )

    print(
        "Triples:",
        result["triple_count"],
    )

    print(
        "owl:imports:",
        len(
            result["imports"]
        ),
    )

    for value in result["imports"]:
        print(
            " ",
            value,
        )

    print(
        "Summary: PASS"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
