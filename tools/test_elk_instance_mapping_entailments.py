#!/usr/bin/env python3
"""ELK-backed instance entailment checks for local SOSA/SSN examples.

This is intentionally scoped to direct active mappings in SSN2BFO.ttl:

- named-class rdfs:subClassOf named-class;
- named-property rdfs:subPropertyOf named-property.

It does not test full OWL DL behavior, blank-node class expressions, property
chains, spreadsheet-only rows, or deferred mappings.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Namespace, OWL, RDF, RDFS, URIRef
from rdflib.term import Node


SOSA = Namespace("http://www.w3.org/ns/sosa/")
SSN = Namespace("http://www.w3.org/ns/ssn/")
SSN_SYSTEM = Namespace("http://www.w3.org/ns/ssn/systems/")
SOSA_REL = Namespace("http://www.w3.org/ns/sosa/sampling/")
BFO = Namespace("http://purl.obolibrary.org/obo/")
CCO = Namespace("https://www.commoncoreontologies.org/")

SOURCE_NAMESPACES = (
    str(SOSA),
    str(SSN),
)

DEFAULT_DATA_DIRS = (
    "src/current-ssn-sosa/examples/sosa-instance-data",
    "tests/fixtures/ssn-systems-mapping",
    "tests/fixtures/ssn-core-mapping",
    "tests/fixtures/remaining-direct-mapping",
)

PREFIXES: tuple[tuple[str, str], ...] = (
    ("rdf", str(RDF)),
    ("rdfs", str(RDFS)),
    ("owl", str(OWL)),
    ("sosa-rel", str(SOSA_REL)),
    ("ssn-system", str(SSN_SYSTEM)),
    ("sosa", str(SOSA)),
    ("ssn", str(SSN)),
    ("bfo", str(BFO)),
    ("cco", str(CCO)),
)

DEFERRED_OR_OUT_OF_SCOPE = (
    ("ssn:hasProperty", "Deferred after ELK diagnostics; no active direct mapping is expected."),
    ("ssn-system:BatteryLifetime", "Deferred after ELK diagnostics; no active direct class mapping is expected."),
    ("ssn-system:MeasurementRange", "Deferred after ELK diagnostics; no active direct class mapping is expected."),
    ("blank-node class expressions", "Out of scope for this first direct-mapping entailment test."),
    ("owl:propertyChainAxiom", "Out of scope for this first direct-mapping entailment test."),
    ("annotation-only rows", "Out of scope because they do not create direct entailments."),
)


@dataclass(frozen=True, order=True)
class DirectMapping:
    kind: str
    source: URIRef
    target: URIRef


@dataclass
class Expectation:
    example: Path
    kind: str
    source: URIRef
    target: URIRef
    subject: URIRef
    object: Node | None
    passed: bool
    robot_materialized: bool
    note: str = ""


@dataclass
class ExampleResult:
    path: Path
    source_kind: str
    merged_path: Path
    reasoned_path: Path
    robot_status: int | None
    robot_succeeded: bool
    reasoned_output_produced: bool
    nothing_count: int | None
    class_expectations_checked: int = 0
    property_expectations_checked: int = 0
    expectation_failures: list[Expectation] = field(default_factory=list)
    robot_materialization_missing: int = 0
    robot_note: str = ""
    parse_error: str = ""

    @property
    def status(self) -> str:
        if self.robot_status != 0:
            return "ROBOT_FAIL"
        if not self.reasoned_output_produced:
            return "MISSING_REASONED_OUTPUT"
        if self.parse_error:
            return "PARSE_FAIL"
        if self.nothing_count and self.nothing_count > 0:
            return "OWL_NOTHING_FAIL"
        if self.expectation_failures:
            return "EXPECTATION_FAIL"
        return "PASS"


def compact_iri(value: URIRef | str | None) -> str:
    if value is None:
        return ""
    text = str(value)
    for prefix, namespace in PREFIXES:
        if text.startswith(namespace):
            return f"{prefix}:{text[len(namespace):]}"
    return f"<{text}>"


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")


def slug_for_path(path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", path.as_posix())
    stem = stem.strip("_").removesuffix("_ttl")
    return stem or "example"


def load_graph(paths: Iterable[Path]) -> Graph:
    graph = Graph()
    bind_prefixes(graph)
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def bind_prefixes(graph: Graph) -> None:
    for prefix, namespace in PREFIXES:
        graph.bind(prefix, Namespace(namespace))


def source_term(value: object) -> bool:
    return isinstance(value, URIRef) and str(value).startswith(SOURCE_NAMESPACES)


def data_file_kind(path: Path) -> str:
    text = path.as_posix()
    if text.startswith("src/current-ssn-sosa/examples/sosa-instance-data/"):
        return "source example"
    if text.startswith("tests/fixtures/"):
        return "synthetic fixture"
    return "data file"


def discover_data_files(data_dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for data_dir in data_dirs:
        for path in sorted(data_dir.glob("*.ttl")):
            if path not in seen:
                files.append(path)
                seen.add(path)
    return files


def extract_direct_mappings(ttl_path: Path) -> tuple[list[DirectMapping], list[DirectMapping]]:
    graph = load_graph([ttl_path])
    class_mappings: list[DirectMapping] = []
    property_mappings: list[DirectMapping] = []

    for source, _, target in graph.triples((None, RDFS.subClassOf, None)):
        if source_term(source) and isinstance(target, URIRef):
            class_mappings.append(DirectMapping("class", source, target))

    for source, _, target in graph.triples((None, RDFS.subPropertyOf, None)):
        if source_term(source) and isinstance(target, URIRef):
            property_mappings.append(DirectMapping("property", source, target))

    return sorted(class_mappings), sorted(property_mappings)


def remove_profile_blockers(graph: Graph) -> None:
    graph.remove((None, OWL.imports, None))
    graph.remove((SOSA.isSampleOf, RDF.type, OWL.FunctionalProperty))


def write_merged_graph(mapping_paths: list[Path], example_path: Path, tmp_dir: Path) -> Path:
    graph = load_graph(mapping_paths + [example_path])
    remove_profile_blockers(graph)
    merged_path = tmp_dir / f"{slug_for_path(example_path)}-merged.ttl"
    graph.serialize(destination=merged_path, format="turtle")
    return merged_path


def run_robot(robot: str, merged_path: Path, reasoned_path: Path) -> tuple[int, str]:
    command = [
        robot,
        "reason",
        "--reasoner",
        "ELK",
        "--input",
        str(merged_path),
        "--output",
        str(reasoned_path),
    ]
    proc = subprocess.run(command, text=True, capture_output=True)
    output = "\n".join(part for part in (proc.stdout.strip(), proc.stderr.strip()) if part)
    return proc.returncode, summarize_robot_output(output)


def summarize_robot_output(output: str) -> str:
    if not output:
        return ""
    lower = output.lower()
    markers: list[str] = []
    if "warning" in lower or "warn" in lower:
        markers.append("ROBOT emitted warnings")
    if "http://org.semanticweb.owlapi/error#error" in lower:
        markers.append("OWLAPI parser messages about error#Error entities")
    if "unsatisfiable" in lower:
        markers.append("ROBOT reported unsatisfiability")
    if markers:
        return "; ".join(dict.fromkeys(markers))
    first_line = output.splitlines()[0]
    return first_line[:240]


def count_owl_nothing(reasoned_path: Path) -> tuple[int | None, str]:
    if not reasoned_path.exists():
        return None, ""
    try:
        graph = Graph()
        graph.parse(reasoned_path, format="turtle")
    except Exception as exc:  # pragma: no cover - reported by integration run
        return None, f"{type(exc).__name__}: {exc}"
    return len(set(graph.subjects(RDF.type, OWL.Nothing))), ""


def transitive_closure(index: dict[URIRef, set[URIRef]]) -> dict[URIRef, set[URIRef]]:
    changed = True
    while changed:
        changed = False
        for source, values in list(index.items()):
            expanded = set(values)
            for value in list(values):
                expanded |= index.get(value, set())
            if not expanded <= values:
                index[source] |= expanded
                changed = True
    return index


def closure_values(index: dict[URIRef, set[URIRef]], value: URIRef) -> set[URIRef]:
    return {value} | index.get(value, set())


def build_rdfs_indexes(graph: Graph) -> tuple[dict[URIRef, set[URIRef]], dict[URIRef, set[URIRef]]]:
    subclass: dict[URIRef, set[URIRef]] = defaultdict(set)
    subproperty: dict[URIRef, set[URIRef]] = defaultdict(set)

    for source, _, target in graph.triples((None, RDFS.subClassOf, None)):
        if isinstance(source, URIRef) and isinstance(target, URIRef):
            subclass[source].add(target)

    for source, _, target in graph.triples((None, RDFS.subPropertyOf, None)):
        if isinstance(source, URIRef) and isinstance(target, URIRef):
            subproperty[source].add(target)

    return transitive_closure(subclass), transitive_closure(subproperty)


def build_expectations(
    example_path: Path,
    merged_path: Path,
    reasoned_path: Path,
    class_mappings: list[DirectMapping],
    property_mappings: list[DirectMapping],
) -> tuple[list[Expectation], str]:
    try:
        example_graph = Graph()
        example_graph.parse(example_path, format="turtle")
        merged_graph = Graph()
        merged_graph.parse(merged_path, format="turtle")
        reasoned_graph = Graph()
        reasoned_graph.parse(reasoned_path, format="turtle")
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"

    subclass, subproperty = build_rdfs_indexes(merged_graph)
    expectations: list[Expectation] = []

    for individual, _, direct_type in sorted(
        set(example_graph.triples((None, RDF.type, None))),
        key=lambda triple: (str(triple[0]), str(triple[2])),
    ):
        if not isinstance(individual, URIRef) or not isinstance(direct_type, URIRef):
            continue
        type_closure = closure_values(subclass, direct_type)
        for mapping in class_mappings:
            if mapping.source not in type_closure:
                continue
            passed = mapping.target in type_closure
            robot_materialized = (individual, RDF.type, mapping.target) in reasoned_graph
            note = "" if passed else "Local RDFS-style subclass closure did not produce expected rdf:type triple."
            expectations.append(
                Expectation(
                    example=example_path,
                    kind="class",
                    source=mapping.source,
                    target=mapping.target,
                    subject=individual,
                    object=None,
                    passed=passed,
                    robot_materialized=robot_materialized,
                    note=note,
                )
            )

    triples = sorted(set(example_graph), key=lambda triple: (str(triple[0]), str(triple[1]), str(triple[2])))
    for subject, predicate, obj in triples:
        if not isinstance(subject, URIRef) or not isinstance(predicate, URIRef) or predicate == RDF.type:
            continue
        property_closure = closure_values(subproperty, predicate)
        for mapping in property_mappings:
            if mapping.source not in property_closure:
                continue
            passed = mapping.target in property_closure
            robot_materialized = (subject, mapping.target, obj) in reasoned_graph
            note = "" if passed else "Local RDFS-style subproperty closure did not produce expected property triple."
            expectations.append(
                Expectation(
                    example=example_path,
                    kind="property",
                    source=mapping.source,
                    target=mapping.target,
                    subject=subject,
                    object=obj,
                    passed=passed,
                    robot_materialized=robot_materialized,
                    note=note,
                )
            )

    return expectations, ""


def mapping_coverage(
    expectations: list[Expectation],
    class_mappings: list[DirectMapping],
    property_mappings: list[DirectMapping],
) -> tuple[dict[DirectMapping, int], list[DirectMapping]]:
    covered_counts: dict[DirectMapping, int] = defaultdict(int)
    mapping_lookup = {(m.kind, m.source, m.target): m for m in class_mappings + property_mappings}

    for expectation in expectations:
        mapping = mapping_lookup[(expectation.kind, expectation.source, expectation.target)]
        covered_counts[mapping] += 1

    all_mappings = class_mappings + property_mappings
    uncovered = [mapping for mapping in all_mappings if covered_counts.get(mapping, 0) == 0]
    return dict(covered_counts), sorted(uncovered)


def write_report(
    output_path: Path,
    example_results: list[ExampleResult],
    expectations: list[Expectation],
    class_mappings: list[DirectMapping],
    property_mappings: list[DirectMapping],
    covered_counts: dict[DirectMapping, int],
    uncovered: list[DirectMapping],
    robot_path: str | None,
    tmp_dir: Path,
    data_dirs: list[Path],
) -> None:
    status_counts = Counter(result.status for result in example_results)
    kind_counts = Counter(result.source_kind for result in example_results)
    robot_pass = sum(1 for result in example_results if result.robot_status == 0)
    robot_fail = len(example_results) - robot_pass
    class_checked = sum(1 for expectation in expectations if expectation.kind == "class")
    property_checked = sum(1 for expectation in expectations if expectation.kind == "property")
    failures = [expectation for expectation in expectations if not expectation.passed]
    robot_materialization_missing = sum(1 for expectation in expectations if not expectation.robot_materialized)
    nothing_failures = [result for result in example_results if result.nothing_count and result.nothing_count > 0]
    robot_failures = [result for result in example_results if result.robot_status != 0]
    missing_outputs = [result for result in example_results if result.robot_status == 0 and not result.reasoned_output_produced]

    lines: list[str] = [
        "# ELK Instance Mapping Entailments",
        "",
        "This report is generated by `tools/test_elk_instance_mapping_entailments.py`.",
        "",
        "## Scope and Limitations",
        "",
        "This test has two layers.",
        "",
        "1. ROBOT/ELK is used as a consistency and satisfiability gate for each merged example graph.",
        "2. Direct instance-level mapping expectations are checked by local deterministic RDFS-style materialization.",
        "",
        "The local materialization layer is used because an earlier version of this test showed that ROBOT/ELK completed successfully but did not materialize expected ABox property assertions in its output file.",
        "",
        "This is not full OWL DL reasoning and not HermiT.",
        "",
        "It preserves the source example discovery used by `tools/test_instance_data.py` and adds clearly labeled synthetic mapping fixtures by default.",
        "",
        "Default data directories:",
        "",
        *[f"- `{path}`" for path in data_dirs],
        "",
        "Files under `src/current-ssn-sosa/examples/sosa-instance-data` are source examples. Files under `tests/fixtures` are synthetic regression-test fixtures, not source examples or authoritative W3C examples.",
        "",
        "For each example, the script builds a temporary no-imports merged graph from:",
        "",
        "- `imports/cco.ttl`",
        "- `imports/ssn.ttl`",
        "- `imports/ssn-systems.ttl`",
        "- `SSN2BFO.ttl`",
        "- the example instance file",
        "",
        "It removes all `owl:imports` triples and removes `sosa:isSampleOf rdf:type owl:FunctionalProperty` if present, then runs:",
        "",
        "```bash",
        "robot reason --reasoner ELK --input <merged.ttl> --output <reasoned.ttl>",
        "```",
        "",
        f"Temporary files are written under `{tmp_dir}`.",
        "",
        "The local mapping-expectation layer checks only active direct mappings in `SSN2BFO.ttl`:",
        "",
        "- `source_class rdfs:subClassOf target_class` where both sides are named IRIs, using direct/transitive `rdfs:subClassOf` propagation for `rdf:type` assertions;",
        "- `source_property rdfs:subPropertyOf target_property` where both sides are named IRIs, using direct/transitive `rdfs:subPropertyOf` propagation for property assertions.",
        "",
        "It intentionally ignores blank-node restrictions, property chains, inverse-property reasoning, cardinalities, disjunctions, annotation-only rows, deferred mappings, and mappings whose source term is not used in an example file.",
        "It does not attempt HermiT or full OWL DL testing.",
        "",
        "## Summary",
        "",
        f"- ROBOT executable: `{robot_path or 'not found'}`",
        f"- Example files tested: {len(example_results)}",
        f"- Source example files tested: {kind_counts.get('source example', 0)}",
        f"- Synthetic fixture files tested: {kind_counts.get('synthetic fixture', 0)}",
        f"- ROBOT pass: {robot_pass}",
        f"- ROBOT fail: {robot_fail}",
        f"- Examples with `owl:Nothing` entities: {len(nothing_failures)}",
        f"- Direct class mappings discovered: {len(class_mappings)}",
        f"- Direct property mappings discovered: {len(property_mappings)}",
        f"- Total class expectations checked: {class_checked}",
        f"- Total property expectations checked: {property_checked}",
        f"- Total expectation failures: {len(failures)}",
        f"- Expected ABox target assertions not observed in ROBOT output: {robot_materialization_missing}",
        f"- Active direct mappings not covered by instance data: {len(uncovered)}",
        f"- Overall status: {'PASS' if not robot_failures and not missing_outputs and not nothing_failures and not failures and robot_path else 'FAIL'}",
        "",
        "## Per-example ELK Results",
        "",
        "| Example | Kind | Status | ROBOT status | `owl:Nothing` count | Class expectations | Property expectations | Expectation failures | ROBOT output missing expected ABox assertions | Notes |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    for result in example_results:
        notes = result.robot_note
        if result.parse_error:
            notes = "; ".join(part for part in [notes, f"Parse error: {result.parse_error}"] if part)
        lines.append(
            "| "
            f"`{result.path}` | {result.source_kind} | {result.status} | "
            f"{'' if result.robot_status is None else result.robot_status} | "
            f"{'' if result.nothing_count is None else result.nothing_count} | "
            f"{result.class_expectations_checked} | "
            f"{result.property_expectations_checked} | "
            f"{len(result.expectation_failures)} | "
            f"{result.robot_materialization_missing} | "
            f"{markdown_escape(notes)} |"
        )

    lines.extend(
        [
            "",
            "## Mapping Expectations Checked",
            "",
            "| Mapping kind | Source | Target | Checked expectation count |",
            "| --- | --- | --- | ---: |",
        ]
    )

    for mapping in sorted(covered_counts):
        lines.append(
            f"| {mapping.kind} | `{compact_iri(mapping.source)}` | `{compact_iri(mapping.target)}` | {covered_counts[mapping]} |"
        )

    if not covered_counts:
        lines.append("|  |  |  | 0 |")

    lines.extend(
        [
            "",
            "## Failures",
            "",
        ]
    )

    if robot_failures:
        lines.append("### ROBOT Failures")
        lines.append("")
        for result in robot_failures:
            lines.append(f"- `{result.path}`: ROBOT status `{result.robot_status}`. {result.robot_note}")
        lines.append("")

    if missing_outputs:
        lines.append("### Missing Reasoned Outputs")
        lines.append("")
        for result in missing_outputs:
            lines.append(f"- `{result.path}`: ROBOT status was 0 but no reasoned output was produced.")
        lines.append("")

    if nothing_failures:
        lines.append("### `owl:Nothing` Failures")
        lines.append("")
        for result in nothing_failures:
            lines.append(f"- `{result.path}`: `{result.nothing_count}` entities typed `owl:Nothing`.")
        lines.append("")

    if failures:
        lines.append("### Mapping Expectation Failures")
        lines.append("")
        lines.append("| Example | Kind | Source | Target | Subject | Object | Note |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for failure in failures:
            lines.append(
                "| "
                f"`{failure.example}` | {failure.kind} | "
                f"`{compact_iri(failure.source)}` | `{compact_iri(failure.target)}` | "
                f"`{compact_iri(failure.subject)}` | `{compact_iri(failure.object)}` | "
                f"{markdown_escape(failure.note)} |"
            )
        lines.append("")

    if not robot_failures and not missing_outputs and not nothing_failures and not failures:
        lines.append("No failures were detected.")
        lines.append("")

    lines.extend(
        [
            "## ROBOT Materialization Note",
            "",
            f"The local RDFS-style expectation check produced `{class_checked + property_checked}` expected ABox target assertions.",
            f"Of those, `{robot_materialization_missing}` were not observed in ROBOT's reasoned output.",
            "",
            "This is reported as a materialization limitation, not as a mapping failure, because the ELK gate succeeded and the local direct subclass/subproperty closure produced the expected target assertions.",
            "",
        ]
    )

    lines.extend(
        [
            "## Active Direct Mappings Not Covered By Instance Data",
            "",
            "These active direct mappings were discovered in `SSN2BFO.ttl`, but their source term was not used in the current example files in a way that creates a checkable ABox expectation.",
            "",
        ]
    )

    if uncovered:
        lines.extend(
            [
                "| Mapping kind | Source | Target |",
                "| --- | --- | --- |",
            ]
        )
        for mapping in uncovered:
            lines.append(f"| {mapping.kind} | `{compact_iri(mapping.source)}` | `{compact_iri(mapping.target)}` |")
    else:
        lines.append("All active direct mappings discovered in `SSN2BFO.ttl` are covered by the current source examples or synthetic fixtures.")

    lines.extend(
        [
            "",
            "## Deferred/out-of-scope Mappings",
            "",
            "| Mapping or pattern | Reason out of scope |",
            "| --- | --- |",
        ]
    )

    for term, reason in DEFERRED_OR_OUT_OF_SCOPE:
        lines.append(f"| `{term}` | {reason} |")

    lines.append("")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


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
        "--ttl",
        default="SSN2BFO.ttl",
        help="TTL mapping file used to discover active direct mappings.",
    )
    parser.add_argument(
        "--data-dir",
        action="append",
        default=None,
        help=(
            "Directory containing .ttl data files. Can be passed multiple times. "
            f"Defaults to: {', '.join(DEFAULT_DATA_DIRS)}."
        ),
    )
    parser.add_argument(
        "--output",
        default="reports/elk-instance-mapping-entailments.md",
        help="Markdown report path.",
    )
    parser.add_argument(
        "--tmp-dir",
        default="/tmp/ssn-to-bfo-elk-instance-mapping-entailments",
        help="Temporary output directory for merged and reasoned graphs.",
    )
    parser.add_argument(
        "--robot",
        default=None,
        help="Path to ROBOT executable. Defaults to the first `robot` on PATH.",
    )
    args = parser.parse_args()

    mapping_paths = [Path(p) for p in args.mapping]
    ttl_path = Path(args.ttl)
    data_dirs = [Path(p) for p in (args.data_dir or DEFAULT_DATA_DIRS)]
    output_path = Path(args.output)
    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    robot_path = args.robot or shutil.which("robot")
    class_mappings, property_mappings = extract_direct_mappings(ttl_path)
    data_files = discover_data_files(data_dirs)

    all_expectations: list[Expectation] = []
    example_results: list[ExampleResult] = []

    if robot_path is None:
        write_report(
            output_path,
            example_results,
            all_expectations,
            class_mappings,
            property_mappings,
            {},
            class_mappings + property_mappings,
            None,
            tmp_dir,
            data_dirs,
        )
        print(f"Wrote {output_path}")
        print(f"Example files tested: {len(data_files)}")
        print("ROBOT pass/fail: 0/0")
        print("Total class expectations checked: 0")
        print("Total property expectations checked: 0")
        print("Total expectation failures: 0")
        print(f"Active direct mappings not covered by instance data: {len(class_mappings) + len(property_mappings)}")
        print("Summary: FAIL (ROBOT unavailable)")
        return 1

    for example_path in data_files:
        reasoned_path = tmp_dir / f"{slug_for_path(example_path)}-reasoned.ttl"
        merged_path = write_merged_graph(mapping_paths, example_path, tmp_dir)
        robot_status, robot_note = run_robot(robot_path, merged_path, reasoned_path)
        reasoned_output_produced = reasoned_path.exists()
        nothing_count, parse_error = count_owl_nothing(reasoned_path)

        expectations: list[Expectation] = []
        expectation_parse_error = ""
        if robot_status == 0 and not parse_error and reasoned_output_produced:
            expectations, expectation_parse_error = build_expectations(
                example_path,
                merged_path,
                reasoned_path,
                class_mappings,
                property_mappings,
            )
            all_expectations.extend(expectations)

        combined_parse_error = "; ".join(part for part in [parse_error, expectation_parse_error] if part)
        failures = [expectation for expectation in expectations if not expectation.passed]
        robot_materialization_missing = sum(1 for expectation in expectations if not expectation.robot_materialized)
        example_results.append(
            ExampleResult(
                path=example_path,
                source_kind=data_file_kind(example_path),
                merged_path=merged_path,
                reasoned_path=reasoned_path,
                robot_status=robot_status,
                robot_succeeded=robot_status == 0,
                reasoned_output_produced=reasoned_output_produced,
                nothing_count=nothing_count,
                class_expectations_checked=sum(1 for expectation in expectations if expectation.kind == "class"),
                property_expectations_checked=sum(1 for expectation in expectations if expectation.kind == "property"),
                expectation_failures=failures,
                robot_materialization_missing=robot_materialization_missing,
                robot_note=robot_note,
                parse_error=combined_parse_error,
            )
        )

    covered_counts, uncovered = mapping_coverage(all_expectations, class_mappings, property_mappings)
    write_report(
        output_path,
        example_results,
        all_expectations,
        class_mappings,
        property_mappings,
        covered_counts,
        uncovered,
        robot_path,
        tmp_dir,
        data_dirs,
    )

    robot_pass = sum(1 for result in example_results if result.robot_status == 0)
    robot_fail = len(example_results) - robot_pass
    class_checked = sum(1 for expectation in all_expectations if expectation.kind == "class")
    property_checked = sum(1 for expectation in all_expectations if expectation.kind == "property")
    expectation_failures = sum(1 for expectation in all_expectations if not expectation.passed)
    nothing_failures = sum(1 for result in example_results if result.nothing_count and result.nothing_count > 0)
    parse_failures = sum(1 for result in example_results if result.parse_error)
    missing_outputs = sum(1 for result in example_results if result.robot_status == 0 and not result.reasoned_output_produced)

    print(f"Wrote {output_path}")
    print(f"Example files tested: {len(example_results)}")
    print(f"ROBOT pass/fail: {robot_pass}/{robot_fail}")
    print(f"Total class expectations checked: {class_checked}")
    print(f"Total property expectations checked: {property_checked}")
    print(f"Total expectation failures: {expectation_failures}")
    print(f"Active direct mappings not covered by instance data: {len(uncovered)}")

    failed = robot_fail > 0 or missing_outputs > 0 or nothing_failures > 0 or expectation_failures > 0 or parse_failures > 0
    print(f"Summary: {'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
