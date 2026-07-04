#!/usr/bin/env python3
"""Smoke-test SSN/SOSA instance data against the current BFO/CCO mapping file.

This is intentionally lightweight:
- parses imports, mappings, and example instance data;
- performs simple RDFS subclass/subproperty closure;
- checks whether the provisional Sample Relationship mappings support instance data;
- writes a Markdown report.

It is not a full OWL DL reasoner or SHACL validation pass.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef


SOSA = Namespace("http://www.w3.org/ns/sosa/")
SSN = Namespace("http://www.w3.org/ns/ssn/")
SAMPLING = Namespace("http://www.w3.org/ns/sosa/sampling/")
CCO_ICE = URIRef("https://www.commoncoreontologies.org/ont00000958")

SOURCE_NS = (
    "http://www.w3.org/ns/sosa/",
    "http://www.w3.org/ns/ssn/",
)


@dataclass
class FileResult:
    path: Path
    status: str
    triples: int = 0
    observations: int = 0
    sensors: int = 0
    samples: int = 0
    sample_relationships: int = 0
    relationship_natures: int = 0
    directly_mapped_property_uses: int = 0
    property_chain_mapped_uses: int = 0
    unmapped_source_properties: tuple[str, ...] = ()
    sample_relationship_problems: tuple[str, ...] = ()
    error: str = ""


def load_graph(paths: Iterable[Path]) -> Graph:
    g = Graph()
    for path in paths:
        g.parse(path, format="turtle")
    return g


def transitive_closure(index: dict[URIRef, set[URIRef]]) -> dict[URIRef, set[URIRef]]:
    changed = True
    while changed:
        changed = False
        for k, vals in list(index.items()):
            expanded = set(vals)
            for v in list(vals):
                expanded |= index.get(v, set())
            if not expanded <= vals:
                index[k] |= expanded
                changed = True
    return index


def build_reasoning_indexes(g: Graph):
    subclass = defaultdict(set)
    subproperty = defaultdict(set)
    property_chains = set()

    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            subclass[s].add(o)

    for s, _, o in g.triples((None, OWL.equivalentClass, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            subclass[s].add(o)
            subclass[o].add(s)

    for s, _, o in g.triples((None, RDFS.subPropertyOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            subproperty[s].add(o)

    for s, _, o in g.triples((None, OWL.equivalentProperty, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            subproperty[s].add(o)
            subproperty[o].add(s)

    for s, _, _ in g.triples((None, OWL.propertyChainAxiom, None)):
        if isinstance(s, URIRef):
            property_chains.add(s)

    return transitive_closure(subclass), transitive_closure(subproperty), property_chains


def inferred_types(g: Graph, subclass: dict[URIRef, set[URIRef]], x) -> set[URIRef]:
    direct = {o for o in g.objects(x, RDF.type) if isinstance(o, URIRef)}
    all_types = set(direct)
    for t in list(direct):
        all_types |= subclass.get(t, set())
    return all_types


def source_property(p) -> bool:
    return isinstance(p, URIRef) and str(p).startswith(SOURCE_NS)


def analyze_graph(path: Path, g: Graph, subclass, subproperty, property_chains) -> FileResult:
    observations = set(g.subjects(RDF.type, SOSA.Observation))
    sensors = set(g.subjects(RDF.type, SOSA.Sensor))
    samples = set(g.subjects(RDF.type, SOSA.Sample))
    sample_relationships = set(g.subjects(RDF.type, SAMPLING.SampleRelationship))
    relationship_natures = set(g.subjects(RDF.type, SAMPLING.RelationshipNature))

    used_source_properties = {p for _, p, _ in g if source_property(p)}
    directly_mapped = {p for p in used_source_properties if subproperty.get(p)}
    property_chain_mapped = {p for p in used_source_properties if p in property_chains}
    mapped = directly_mapped | property_chain_mapped
    unmapped = sorted(str(p) for p in used_source_properties - mapped)

    problems: list[str] = []

    for rel in sorted(sample_relationships, key=str):
        rel_types = inferred_types(g, subclass, rel)
        if CCO_ICE not in rel_types:
            problems.append(f"{rel} does not infer to CCO Information Content Entity")

        related = list(g.objects(rel, SAMPLING.relatedSample))
        natures = list(g.objects(rel, SAMPLING.natureOfRelationship))

        if not related:
            problems.append(f"{rel} missing sampling:relatedSample")
        if not natures:
            problems.append(f"{rel} missing sampling:natureOfRelationship")

        for sample in related:
            if SOSA.Sample not in inferred_types(g, subclass, sample):
                problems.append(f"{rel} relatedSample object is not typed/inferred sosa:Sample: {sample}")

        for nature in natures:
            if SAMPLING.RelationshipNature not in inferred_types(g, subclass, nature):
                problems.append(
                    f"{rel} natureOfRelationship object is not typed/inferred sampling:RelationshipNature: {nature}"
                )

    status = "PASS" if not problems else "CHECK"

    return FileResult(
        path=path,
        status=status,
        triples=len(g),
        observations=len(observations),
        sensors=len(sensors),
        samples=len(samples),
        sample_relationships=len(sample_relationships),
        relationship_natures=len(relationship_natures),
        directly_mapped_property_uses=len(directly_mapped),
        property_chain_mapped_uses=len(property_chain_mapped),
        unmapped_source_properties=tuple(unmapped),
        sample_relationship_problems=tuple(problems),
    )


def add_sample_relationship_fixture(g: Graph) -> None:
    ex = Namespace("http://example.org/sample-test/")

    g.add((ex["sample-1"], RDF.type, SOSA.Sample))
    g.add((ex["sample-2"], RDF.type, SOSA.Sample))
    g.add((ex["derived-from"], RDF.type, SAMPLING.RelationshipNature))
    g.add((ex["sample-relationship-1"], RDF.type, SAMPLING.SampleRelationship))
    g.add((ex["sample-relationship-1"], SAMPLING.relatedSample, ex["sample-2"]))
    g.add((ex["sample-relationship-1"], SAMPLING.natureOfRelationship, ex["derived-from"]))


def write_report(path: Path, results: list[FileResult], fixture: FileResult) -> None:
    status_counts = Counter(r.status for r in results)

    lines = [
        "# Instance Data Smoke Test",
        "",
        "This report is generated by `tools/test_instance_data.py`.",
        "",
        "This is a lightweight parse/RDFS-closure smoke test, not a full OWL DL or SHACL validation.",
        "",
        "## Summary",
        "",
        f"- Example files tested: {len(results)}",
        f"- PASS: {status_counts.get('PASS', 0)}",
        f"- CHECK: {status_counts.get('CHECK', 0)}",
        f"- PARSE_FAIL: {status_counts.get('PARSE_FAIL', 0)}",
        "",
        "## Example File Results",
        "",
        "| File | Status | Triples | Observations | Sensors | Samples | SampleRelationships | RelationshipNatures | Directly mapped properties | Property-chain mapped properties | Unmapped source properties |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for r in results:
        lines.append(
            f"| `{r.path}` | {r.status} | {r.triples} | {r.observations} | {r.sensors} | "
            f"{r.samples} | {r.sample_relationships} | {r.relationship_natures} | "
            f"{r.directly_mapped_property_uses} | {r.property_chain_mapped_uses} | {len(r.unmapped_source_properties)} |"
        )

    lines.extend(
        [
            "",
            "## Provisional Sample Relationship Fixture",
            "",
            f"- Status: {fixture.status}",
            f"- Triples: {fixture.triples}",
            f"- SampleRelationship instances: {fixture.sample_relationships}",
            f"- RelationshipNature instances: {fixture.relationship_natures}",
            "",
        ]
    )

    if fixture.sample_relationship_problems:
        lines.append("### Fixture problems")
        lines.append("")
        for problem in fixture.sample_relationship_problems:
            lines.append(f"- {problem}")
        lines.append("")
    else:
        lines.append("The synthetic Sample Relationship fixture passed the provisional mapping checks.")
        lines.append("")

    all_unmapped = Counter()
    for r in results:
        for p in r.unmapped_source_properties:
            all_unmapped[p] += 1

    lines.extend([
        "## Unmapped SOSA/SSN Property Uses",
        "",
        "This section is an informational coverage review queue, not a failure condition. "
        "A property may appear here because it is intentionally structural, datatype-oriented, "
        "outside the current mapping scope, or awaiting a separate mapping decision.",
        "",
    ])

    if all_unmapped:
        lines.append("| Property | Files using it |")
        lines.append("| --- | ---: |")
        for prop, count in sorted(all_unmapped.items()):
            lines.append(f"| `{prop}` | {count} |")
    else:
        lines.append("No unmapped SOSA/SSN property uses found by the lightweight subproperty check.")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mapping",
        action="append",
        default=[
            "imports/cco.ttl",
            "imports/ssn.ttl",
            "imports/ssn-systems.ttl",
            "SSN2BFO.ttl",
        ],
        help="Mapping/import TTL file. Can be passed multiple times.",
    )
    parser.add_argument(
        "--data-dir",
        default="src/current-ssn-sosa/examples/sosa-instance-data",
        help="Directory containing example .ttl files.",
    )
    parser.add_argument(
        "--output",
        default="reports/instance-data-smoke-test.md",
        help="Markdown report path.",
    )
    args = parser.parse_args()

    mapping_paths = [Path(p) for p in args.mapping]
    data_files = sorted(Path(args.data_dir).glob("*.ttl"))

    results: list[FileResult] = []

    for data_file in data_files:
        try:
            g = load_graph(mapping_paths + [data_file])
            subclass, subproperty, property_chains = build_reasoning_indexes(g)
            results.append(analyze_graph(data_file, g, subclass, subproperty, property_chains))
        except Exception as e:
            results.append(FileResult(path=data_file, status="PARSE_FAIL", error=f"{type(e).__name__}: {e}"))

    fixture_graph = load_graph(mapping_paths)
    add_sample_relationship_fixture(fixture_graph)
    subclass, subproperty, property_chains = build_reasoning_indexes(fixture_graph)
    fixture = analyze_graph(Path("synthetic:sample-relationship-fixture"), fixture_graph, subclass, subproperty, property_chains)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_report(output, results, fixture)

    print(f"Wrote {output}")
    print(f"Example files tested: {len(results)}")
    print(Counter(r.status for r in results))
    print(f"Fixture status: {fixture.status}")

    if any(r.status == "PARSE_FAIL" for r in results) or fixture.status != "PASS":
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
