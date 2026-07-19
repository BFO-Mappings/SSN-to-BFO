#!/usr/bin/env python3
"""Run a full local SOSA closure HermiT consistency check."""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph, Namespace, OWL, RDF, RDFS, URIRef


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TMP_DIR = Path("/tmp/ssn-to-bfo-full-sosa-closure-hermit-check")
DEFAULT_OUTPUT = Path("reports/full-sosa-closure-hermit-check.md")

SOSA = Namespace("http://www.w3.org/ns/sosa/")
SSN = Namespace("http://www.w3.org/ns/ssn/")
SSN_SYSTEM = Namespace("http://www.w3.org/ns/ssn/systems/")
BFO = Namespace("http://purl.obolibrary.org/obo/")
CCO = Namespace("https://www.commoncoreontologies.org/")

GRAPH_INPUTS = (
    Path("imports/cco.ttl"),
    Path("imports/sosa.ttl"),
    Path("imports/sosa-sampling.ttl"),
    Path("imports/ssn.ttl"),
    Path("imports/ssn-systems.ttl"),
    Path("SSN2BFO.ttl"),
)

CLEANUP_TRIPLES = (
    (SOSA.isSampleOf, RDF.type, OWL.FunctionalProperty),
    (SOSA.hasSample, RDF.type, OWL.InverseFunctionalProperty),
)


@dataclass
class HermitResult:
    graph_path: Path
    reasoned_path: Path
    triple_count: int
    return_code: int | None
    reasoned_output_produced: bool
    owl_nothing_count: int | None
    unsat_classes: list[URIRef]
    robot_output: str
    sample_blockers_present: bool
    robot_path: str | None

    @property
    def passed(self) -> bool:
        return (
            self.return_code == 0
            and self.reasoned_output_produced
            and self.owl_nothing_count == 0
            and not self.unsat_classes
        )


def compact_iri(value: URIRef | str) -> str:
    text = str(value)
    prefixes = (
        ("owl", str(OWL)),
        ("rdf", str(RDF)),
        ("rdfs", str(RDFS)),
        ("sosa", str(SOSA)),
        ("ssn-system", str(SSN_SYSTEM)),
        ("ssn", str(SSN)),
        ("bfo", str(BFO)),
        ("cco", str(CCO)),
    )
    for prefix, namespace in prefixes:
        if text.startswith(namespace):
            return f"{prefix}:{text[len(namespace):]}"
    return f"<{text}>"


def command_text(command: list[str]) -> str:
    return shlex.join(command)


def bind_prefixes(graph: Graph) -> None:
    graph.bind("owl", OWL)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("sosa", SOSA)
    graph.bind("ssn", SSN)
    graph.bind("ssn-system", SSN_SYSTEM)
    graph.bind("bfo", BFO)
    graph.bind("cco", CCO)


def build_graph() -> Graph:
    graph = Graph()
    bind_prefixes(graph)
    for path in GRAPH_INPUTS:
        graph.parse(REPO_ROOT / path, format="turtle")

    for triple in list(graph.triples((None, OWL.imports, None))):
        graph.remove(triple)
    for triple in CLEANUP_TRIPLES:
        graph.remove(triple)

    return graph


def sample_blockers_present(graph: Graph) -> bool:
    return any(triple in graph for triple in CLEANUP_TRIPLES)


def unsat_classes(graph: Graph) -> list[URIRef]:
    classes: set[URIRef] = set()
    for subject in graph.subjects(RDFS.subClassOf, OWL.Nothing):
        if isinstance(subject, URIRef) and subject != OWL.Nothing:
            classes.add(subject)
    for subject in graph.subjects(OWL.equivalentClass, OWL.Nothing):
        if isinstance(subject, URIRef) and subject != OWL.Nothing:
            classes.add(subject)
    for obj in graph.objects(OWL.Nothing, OWL.equivalentClass):
        if isinstance(obj, URIRef) and obj != OWL.Nothing:
            classes.add(obj)
    return sorted(classes, key=str)


def run_hermit(graph: Graph, tmp_dir: Path, robot: str | None) -> HermitResult:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    graph_path = tmp_dir / "full-sosa-closure-hermit.ttl"
    reasoned_path = tmp_dir / "full-sosa-closure-hermit-reasoned.ttl"
    graph.serialize(destination=graph_path, format="turtle")

    if robot is None:
        return HermitResult(
            graph_path=graph_path,
            reasoned_path=reasoned_path,
            triple_count=len(graph),
            return_code=None,
            reasoned_output_produced=False,
            owl_nothing_count=None,
            unsat_classes=[],
            robot_output="ROBOT executable not found on PATH.",
            sample_blockers_present=sample_blockers_present(graph),
            robot_path=None,
        )

    command = [
        robot,
        "reason",
        "--reasoner",
        "HermiT",
        "--input",
        str(graph_path),
        "--output",
        str(reasoned_path),
    ]
    proc = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = "\n".join(part for part in (proc.stdout.strip(), proc.stderr.strip()) if part)

    reasoned_output_produced = reasoned_path.exists() and reasoned_path.stat().st_size > 0
    owl_nothing_count: int | None = None
    inferred_unsats: list[URIRef] = []
    if reasoned_output_produced:
        reasoned_graph = Graph()
        bind_prefixes(reasoned_graph)
        reasoned_graph.parse(reasoned_path, format="turtle")
        inferred_unsats = unsat_classes(reasoned_graph)
        owl_nothing_count = len(inferred_unsats)

    return HermitResult(
        graph_path=graph_path,
        reasoned_path=reasoned_path,
        triple_count=len(graph),
        return_code=proc.returncode,
        reasoned_output_produced=reasoned_output_produced,
        owl_nothing_count=owl_nothing_count,
        unsat_classes=inferred_unsats,
        robot_output=output,
        sample_blockers_present=sample_blockers_present(graph),
        robot_path=robot,
    )


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|")


def write_report(path: Path, result: HermitResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    command = "robot reason --reasoner HermiT --input <temporary-full-closure.ttl> --output <temporary-reasoned.ttl>"
    unsat_set = ", ".join(f"`{compact_iri(value)}`" for value in result.unsat_classes) or "clean"
    lines = [
        "# Full Local SOSA Closure HermiT Check",
        "",
        "This report is generated by `tools/test_full_sosa_closure_hermit.py`.",
        "",
        "## Scope",
        "",
        "This check protects the full local SOSA closure HermiT baseline. It loads:",
        "",
        *[f"- `{path}`" for path in GRAPH_INPUTS],
        "",
        "After loading those files, it removes all `owl:imports` triples and the established sample simplicity blockers:",
        "",
        "```ttl",
        "sosa:isSampleOf rdf:type owl:FunctionalProperty .",
        "sosa:hasSample rdf:type owl:InverseFunctionalProperty .",
        "```",
        "",
        "It then runs:",
        "",
        "```bash",
        command,
        "```",
        "",
        "## Result",
        "",
        "| Item | Result |",
        "|---|---|",
        f"| ROBOT executable | `{markdown_escape(result.robot_path or 'not found')}` |",
        f"| graph path | `{markdown_escape(str(result.graph_path))}` |",
        f"| reasoned output path | `{markdown_escape(str(result.reasoned_path))}` |",
        f"| triple count before reasoning | {result.triple_count} |",
        f"| return code | {'' if result.return_code is None else result.return_code} |",
        f"| reasoned output produced | {'yes' if result.reasoned_output_produced else 'no'} |",
        f"| `owl:Nothing` count | {'n/a' if result.owl_nothing_count is None else result.owl_nothing_count} |",
        f"| unsat count | {len(result.unsat_classes)} |",
        f"| unsat set | {unsat_set} |",
        f"| sample simplicity blocker reappeared | {'yes' if result.sample_blockers_present else 'no'} |",
        f"| overall status | {'PASS' if result.passed else 'FAIL'} |",
        "",
        "## Interpretation",
        "",
    ]
    if result.passed:
        lines.extend(
            [
                "The full local SOSA closure graph is HermiT-clean under the established cleanup conditions.",
                "",
                "This confirms the current baseline after the paired actuation-agent mapping deferral.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "The full local SOSA closure graph is not HermiT-clean under the established cleanup conditions.",
                "",
                "Investigate the unsatisfiable classes or ROBOT/HermiT failure before merging mapping changes.",
                "",
            ]
        )

    if result.robot_output:
        excerpt = result.robot_output.strip()
        if len(excerpt) > 4000:
            excerpt = excerpt[:4000] + "\n... [truncated]"
        lines.extend(
            [
                "## ROBOT Output",
                "",
                "```text",
                excerpt,
                "```",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Markdown report path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--tmp-dir",
        default=str(DEFAULT_TMP_DIR),
        help=f"Temporary graph directory. Default: {DEFAULT_TMP_DIR}",
    )
    parser.add_argument(
        "--robot",
        default=None,
        help="Path to ROBOT executable. Defaults to the first `robot` on PATH.",
    )
    args = parser.parse_args(argv)

    graph = build_graph()
    robot = args.robot or shutil.which("robot")
    result = run_hermit(graph, Path(args.tmp_dir), robot)
    write_report(REPO_ROOT / args.output, result)

    print(f"Wrote {args.output}")
    print(f"Triple count: {result.triple_count}")
    print(f"HermiT return code: {result.return_code}")
    print(f"Reasoned output produced: {'yes' if result.reasoned_output_produced else 'no'}")
    print(f"owl:Nothing count: {result.owl_nothing_count}")
    print(f"Unsat count: {len(result.unsat_classes)}")
    print(f"Unsat set: {', '.join(compact_iri(value) for value in result.unsat_classes) or 'clean'}")
    print(f"Summary: {'PASS' if result.passed else 'FAIL'}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
