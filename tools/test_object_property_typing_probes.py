#!/usr/bin/env python3
"""Run the historical pre-COMS object-property typing diagnostic.

This frozen 62-probe profile targets the legacy manual ontology and is not a
release gate for the authoritative COMS-generated ontology.
"""

from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from rdflib import BNode, Graph, Namespace, OWL, RDF, RDFS, URIRef
from rdflib.collection import Collection


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TMP_DIR = Path("/tmp/ssn-to-bfo-object-property-typing-probes")
DEFAULT_OUTPUT = Path("reports/object-property-typing-probe-check.md")

SOSA = Namespace("http://www.w3.org/ns/sosa/")
SSN = Namespace("http://www.w3.org/ns/ssn/")
SSN_SYSTEM = Namespace("http://www.w3.org/ns/ssn/systems/")
BFO = Namespace("http://purl.obolibrary.org/obo/")
CCO = Namespace("https://www.commoncoreontologies.org/")
PROBE = Namespace("http://example.org/ssn-to-bfo/object-property-typing-probe/")

GRAPH_INPUTS = (
    Path("imports/cco.ttl"),
    Path("imports/sosa.ttl"),
    Path("imports/sosa-sampling.ttl"),
    Path("imports/ssn.ttl"),
    Path("imports/ssn-systems.ttl"),
    Path("legacy/SSN2BFO-pre-COMS.ttl"),
)

CLEANUP_TRIPLES = (
    (SOSA.isSampleOf, RDF.type, OWL.FunctionalProperty),
    (SOSA.hasSample, RDF.type, OWL.InverseFunctionalProperty),
)

UNSAT_RE = re.compile(r"unsatisfiable:\s+(\S+)")


@dataclass(frozen=True)
class ProbeSpec:
    identifier: str
    property_iri: URIRef
    kind: str
    intended_class: URIRef
    workbook_row: str

    @property
    def probe_iri(self) -> URIRef:
        return URIRef(f"{PROBE}{self.identifier}")


@dataclass
class BasisCheck:
    local_domains: set[tuple[URIRef, URIRef, URIRef]]
    local_ranges: set[tuple[URIRef, URIRef, URIRef]]
    missing_retained: set[tuple[URIRef, URIRef, URIRef]]
    extra_domains: set[tuple[URIRef, URIRef, URIRef]]
    extra_ranges: set[tuple[URIRef, URIRef, URIRef]]

    @property
    def passed(self) -> bool:
        return (
            len(self.local_domains) == 22
            and len(self.local_ranges) == 0
            and not self.missing_retained
            and not self.extra_domains
            and not self.extra_ranges
        )


@dataclass
class HermitRun:
    graph_path: Path
    reasoned_path: Path
    triple_count: int
    return_code: int | None
    reasoned_output_produced: bool
    owl_nothing_count: int | None
    unsat_classes: set[URIRef]
    robot_output: str


@dataclass
class ProbeResult:
    spec: ProbeSpec
    run: HermitRun
    expected_probe_unsat: bool
    satisfiable: bool
    inconclusive: bool
    unexpected_unsats: set[URIRef]

    @property
    def passed(self) -> bool:
        return (
            self.expected_probe_unsat
            and not self.satisfiable
            and not self.inconclusive
            and not self.unexpected_unsats
        )


PROBE_SPECS: tuple[ProbeSpec, ...] = (
    ProbeSpec("p00_sosa_actsOnProperty_domain_sosa_Actuation", SOSA.actsOnProperty, "domain", SOSA.Actuation, "Common OPs row 2"),
    ProbeSpec("p01_sosa_actsOnProperty_range_sosa_ActuatableProperty", SOSA.actsOnProperty, "range", SOSA.ActuatableProperty, "Common OPs row 2"),
    ProbeSpec("p02_sosa_hasSample_domain_sosa_FeatureOfInterest", SOSA.hasSample, "domain", SOSA.FeatureOfInterest, "Common OPs row 13"),
    ProbeSpec("p03_sosa_hasSample_range_sosa_Sample", SOSA.hasSample, "range", SOSA.Sample, "Common OPs row 13"),
    ProbeSpec("p04_sosa_isActedOnBy_domain_sosa_ActuatableProperty", SOSA.isActedOnBy, "domain", SOSA.ActuatableProperty, "Common OPs row 19"),
    ProbeSpec("p05_sosa_isActedOnBy_range_sosa_Actuation", SOSA.isActedOnBy, "range", SOSA.Actuation, "Common OPs row 19"),
    ProbeSpec("p06_sosa_isObservedBy_domain_sosa_ObservableProperty", SOSA.isObservedBy, "domain", SOSA.ObservableProperty, "Common OPs row 22"),
    ProbeSpec("p07_sosa_isObservedBy_range_sosa_Sensor", SOSA.isObservedBy, "range", SOSA.Sensor, "Common OPs row 22"),
    ProbeSpec("p08_sosa_isSampleOf_domain_sosa_Sample", SOSA.isSampleOf, "domain", SOSA.Sample, "Common OPs row 26"),
    ProbeSpec("p09_sosa_isSampleOf_range_sosa_FeatureOfInterest", SOSA.isSampleOf, "range", SOSA.FeatureOfInterest, "Common OPs row 26"),
    ProbeSpec("p10_sosa_madeActuation_domain_sosa_Actuator", SOSA.madeActuation, "domain", SOSA.Actuator, "Common OPs row 27"),
    ProbeSpec("p11_sosa_madeActuation_range_sosa_Actuation", SOSA.madeActuation, "range", SOSA.Actuation, "Common OPs row 27"),
    ProbeSpec("p12_sosa_madeByActuator_domain_sosa_Actuation", SOSA.madeByActuator, "domain", SOSA.Actuation, "Common OPs row 28"),
    ProbeSpec("p13_sosa_madeByActuator_range_sosa_Actuator", SOSA.madeByActuator, "range", SOSA.Actuator, "Common OPs row 28"),
    ProbeSpec("p14_sosa_madeBySampler_domain_sosa_Sampling", SOSA.madeBySampler, "domain", SOSA.Sampling, "Common OPs row 29"),
    ProbeSpec("p15_sosa_madeBySampler_range_sosa_Sampler", SOSA.madeBySampler, "range", SOSA.Sampler, "Common OPs row 29"),
    ProbeSpec("p16_sosa_madeBySensor_domain_sosa_Observation", SOSA.madeBySensor, "domain", SOSA.Observation, "Common OPs row 30"),
    ProbeSpec("p17_sosa_madeBySensor_range_sosa_Sensor", SOSA.madeBySensor, "range", SOSA.Sensor, "Common OPs row 30"),
    ProbeSpec("p18_sosa_madeObservation_domain_sosa_Sensor", SOSA.madeObservation, "domain", SOSA.Sensor, "Common OPs row 31"),
    ProbeSpec("p19_sosa_madeObservation_range_sosa_Observation", SOSA.madeObservation, "range", SOSA.Observation, "Common OPs row 31"),
    ProbeSpec("p20_sosa_madeSampling_domain_sosa_Sampler", SOSA.madeSampling, "domain", SOSA.Sampler, "Common OPs row 32"),
    ProbeSpec("p21_sosa_madeSampling_range_sosa_Sampling", SOSA.madeSampling, "range", SOSA.Sampling, "Common OPs row 32"),
    ProbeSpec("p22_sosa_observedProperty_domain_sosa_Observation", SOSA.observedProperty, "domain", SOSA.Observation, "Common OPs row 33"),
    ProbeSpec("p23_sosa_observedProperty_range_sosa_ObservableProperty", SOSA.observedProperty, "range", SOSA.ObservableProperty, "Common OPs row 33"),
    ProbeSpec("p24_sosa_observes_domain_sosa_Sensor", SOSA.observes, "domain", SOSA.Sensor, "Common OPs row 34"),
    ProbeSpec("p25_sosa_observes_range_sosa_ObservableProperty", SOSA.observes, "range", SOSA.ObservableProperty, "Common OPs row 34"),
    ProbeSpec("p26_ssn_deployedOnPlatform_domain_ssn_Deployment", SSN.deployedOnPlatform, "domain", SSN.Deployment, "Common OPs row 3"),
    ProbeSpec("p27_ssn_deployedOnPlatform_range_sosa_Platform", SSN.deployedOnPlatform, "range", SOSA.Platform, "Common OPs row 3"),
    ProbeSpec("p28_ssn_deployedSystem_domain_ssn_Deployment", SSN.deployedSystem, "domain", SSN.Deployment, "Common OPs row 4"),
    ProbeSpec("p29_ssn_deployedSystem_range_ssn_System", SSN.deployedSystem, "range", SSN.System, "Common OPs row 4"),
    ProbeSpec("p30_ssn_detects_domain_sosa_Sensor", SSN.detects, "domain", SOSA.Sensor, "Common OPs row 5"),
    ProbeSpec("p31_ssn_detects_range_ssn_Stimulus", SSN.detects, "range", SSN.Stimulus, "Common OPs row 5"),
    ProbeSpec("p32_ssn_hasDeployment_domain_ssn_System", SSN.hasDeployment, "domain", SSN.System, "Common OPs row 7"),
    ProbeSpec("p33_ssn_hasDeployment_range_ssn_Deployment", SSN.hasDeployment, "range", SSN.Deployment, "Common OPs row 7"),
    ProbeSpec("p34_ssn_hasInput_domain_sosa_Procedure", SSN.hasInput, "domain", SOSA.Procedure, "Common OPs row 9"),
    ProbeSpec("p35_ssn_hasInput_range_ssn_Input", SSN.hasInput, "range", SSN.Input, "Common OPs row 9"),
    ProbeSpec("p36_ssn_hasOutput_domain_sosa_Procedure", SSN.hasOutput, "domain", SOSA.Procedure, "Common OPs row 10"),
    ProbeSpec("p37_ssn_hasOutput_range_ssn_Output", SSN.hasOutput, "range", SSN.Output, "Common OPs row 10"),
    ProbeSpec("p38_ssn_hasSubSystem_domain_ssn_System", SSN.hasSubSystem, "domain", SSN.System, "Common OPs row 14"),
    ProbeSpec("p39_ssn_hasSubSystem_range_ssn_System", SSN.hasSubSystem, "range", SSN.System, "Common OPs row 14"),
    ProbeSpec("p40_ssn_implementedBy_domain_sosa_Procedure", SSN.implementedBy, "domain", SOSA.Procedure, "Common OPs row 16"),
    ProbeSpec("p41_ssn_implementedBy_range_ssn_System", SSN.implementedBy, "range", SSN.System, "Common OPs row 16"),
    ProbeSpec("p42_ssn_implements_domain_ssn_System", SSN.implements, "domain", SSN.System, "Common OPs row 17"),
    ProbeSpec("p43_ssn_implements_range_sosa_Procedure", SSN.implements, "range", SOSA.Procedure, "Common OPs row 17"),
    ProbeSpec("p44_ssn_inDeployment_domain_sosa_Platform", SSN.inDeployment, "domain", SOSA.Platform, "Common OPs row 18"),
    ProbeSpec("p45_ssn_inDeployment_range_ssn_Deployment", SSN.inDeployment, "range", SSN.Deployment, "Common OPs row 18"),
    ProbeSpec("p46_ssn_isProxyFor_domain_ssn_Stimulus", SSN.isProxyFor, "domain", SSN.Stimulus, "Common OPs row 24"),
    ProbeSpec("p47_ssn_isProxyFor_range_sosa_ObservableProperty", SSN.isProxyFor, "range", SOSA.ObservableProperty, "Common OPs row 24"),
    ProbeSpec("p48_ssn_system_hasOperatingProperty_domain_ssn_system_OperatingRange", SSN_SYSTEM.hasOperatingProperty, "domain", SSN_SYSTEM.OperatingRange, "System Capability row 9"),
    ProbeSpec("p49_ssn_system_hasOperatingProperty_range_ssn_system_OperatingProperty", SSN_SYSTEM.hasOperatingProperty, "range", SSN_SYSTEM.OperatingProperty, "System Capability row 9"),
    ProbeSpec("p50_ssn_system_hasOperatingRange_domain_ssn_System", SSN_SYSTEM.hasOperatingRange, "domain", SSN.System, "System Capability row 10"),
    ProbeSpec("p51_ssn_system_hasOperatingRange_range_ssn_system_OperatingRange", SSN_SYSTEM.hasOperatingRange, "range", SSN_SYSTEM.OperatingRange, "System Capability row 10"),
    ProbeSpec("p52_ssn_system_hasSurvivalProperty_domain_ssn_system_SurvivalRange", SSN_SYSTEM.hasSurvivalProperty, "domain", SSN_SYSTEM.SurvivalRange, "System Capability row 11"),
    ProbeSpec("p53_ssn_system_hasSurvivalProperty_range_ssn_system_SurvivalProperty", SSN_SYSTEM.hasSurvivalProperty, "range", SSN_SYSTEM.SurvivalProperty, "System Capability row 11"),
    ProbeSpec("p54_ssn_system_hasSurvivalRange_domain_ssn_System", SSN_SYSTEM.hasSurvivalRange, "domain", SSN.System, "System Capability row 12"),
    ProbeSpec("p55_ssn_system_hasSurvivalRange_range_ssn_system_SurvivalRange", SSN_SYSTEM.hasSurvivalRange, "range", SSN_SYSTEM.SurvivalRange, "System Capability row 12"),
    ProbeSpec("p56_ssn_system_hasSystemCapability_domain_ssn_System", SSN_SYSTEM.hasSystemCapability, "domain", SSN.System, "System Capability row 13"),
    ProbeSpec("p57_ssn_system_hasSystemCapability_range_ssn_system_SystemCapability", SSN_SYSTEM.hasSystemCapability, "range", SSN_SYSTEM.SystemCapability, "System Capability row 13"),
    ProbeSpec("p58_ssn_system_hasSystemProperty_domain_ssn_system_SystemCapability", SSN_SYSTEM.hasSystemProperty, "domain", SSN_SYSTEM.SystemCapability, "System Capability row 14"),
    ProbeSpec("p59_ssn_system_hasSystemProperty_range_ssn_system_SystemProperty", SSN_SYSTEM.hasSystemProperty, "range", SSN_SYSTEM.SystemProperty, "System Capability row 14"),
    ProbeSpec("p60_ssn_wasOriginatedBy_domain_sosa_Observation", SSN.wasOriginatedBy, "domain", SOSA.Observation, "Common OPs row 37"),
    ProbeSpec("p61_ssn_wasOriginatedBy_range_ssn_Stimulus", SSN.wasOriginatedBy, "range", SSN.Stimulus, "Common OPs row 37"),
)

EXPECTED_RETAINED_BASIS: frozenset[tuple[URIRef, URIRef, URIRef]] = frozenset(
    {
        (SOSA.isActedOnBy, RDFS.domain, SOSA.ActuatableProperty),
        (SOSA.isObservedBy, RDFS.domain, SOSA.ObservableProperty),
        (SOSA.isSampleOf, RDFS.domain, SOSA.Sample),
        (SOSA.madeByActuator, RDFS.domain, SOSA.Actuation),
        (SOSA.madeObservation, RDFS.domain, SOSA.Sensor),
        (SOSA.madeSampling, RDFS.domain, SOSA.Sampler),
        (SOSA.observedProperty, RDFS.domain, SOSA.Observation),
        (SSN.detects, RDFS.domain, SOSA.Sensor),
        (SSN.hasDeployment, RDFS.domain, SSN.System),
        (SSN.hasInput, RDFS.domain, SOSA.Procedure),
        (SSN.hasOutput, RDFS.domain, SOSA.Procedure),
        (SSN.hasSubSystem, RDFS.domain, SSN.System),
        (SSN.implements, RDFS.domain, SSN.System),
        (SSN.inDeployment, RDFS.domain, SOSA.Platform),
        (SSN.isProxyFor, RDFS.domain, SSN.Stimulus),
        (SSN_SYSTEM.hasOperatingProperty, RDFS.domain, SSN_SYSTEM.OperatingRange),
        (SSN_SYSTEM.hasOperatingRange, RDFS.domain, SSN.System),
        (SSN_SYSTEM.hasSurvivalProperty, RDFS.domain, SSN_SYSTEM.SurvivalRange),
        (SSN_SYSTEM.hasSurvivalRange, RDFS.domain, SSN.System),
        (SSN_SYSTEM.hasSystemCapability, RDFS.domain, SSN.System),
        (SSN_SYSTEM.hasSystemProperty, RDFS.domain, SSN_SYSTEM.SystemCapability),
        (SSN.wasOriginatedBy, RDFS.domain, SOSA.Observation),
    }
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
        ("probe", str(PROBE)),
    )
    for prefix, namespace in prefixes:
        if text.startswith(namespace):
            return f"{prefix}:{text[len(namespace):]}"
    return f"<{text}>"


def command_text(command: list[str]) -> str:
    return shlex.join(command)


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|")


def bind_prefixes(graph: Graph) -> None:
    graph.bind("owl", OWL)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("sosa", SOSA)
    graph.bind("ssn", SSN)
    graph.bind("ssn-system", SSN_SYSTEM)
    graph.bind("bfo", BFO)
    graph.bind("cco", CCO)
    graph.bind("probe", PROBE)


def build_full_closure_graph() -> Graph:
    graph = Graph()
    bind_prefixes(graph)
    for path in GRAPH_INPUTS:
        graph.parse(REPO_ROOT / path, format="turtle")

    for triple in list(graph.triples((None, OWL.imports, None))):
        graph.remove(triple)
    for triple in CLEANUP_TRIPLES:
        graph.remove(triple)

    return graph


def clone_graph(source: Graph) -> Graph:
    graph = Graph()
    bind_prefixes(graph)
    for prefix, namespace in source.namespaces():
        graph.bind(prefix, namespace)
    for triple in source:
        graph.add(triple)
    return graph


def unsat_classes_from_graph(graph: Graph) -> set[URIRef]:
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
    return classes


def unsat_classes_from_robot_output(output: str) -> set[URIRef]:
    return {URIRef(match.group(1)) for match in UNSAT_RE.finditer(output)}


def verify_probe_specs() -> list[str]:
    errors: list[str] = []
    unique_specs = {(spec.property_iri, spec.kind, spec.intended_class) for spec in PROBE_SPECS}
    if len(PROBE_SPECS) != 62:
        errors.append(f"expected 62 probe specifications; found {len(PROBE_SPECS)}")
    if len(unique_specs) != len(PROBE_SPECS):
        errors.append("duplicate property/kind/class probe specifications found")
    kinds = {spec.kind for spec in PROBE_SPECS}
    if kinds != {"domain", "range"}:
        errors.append(f"unexpected probe kinds: {sorted(kinds)}")
    domain_count = sum(1 for spec in PROBE_SPECS if spec.kind == "domain")
    range_count = sum(1 for spec in PROBE_SPECS if spec.kind == "range")
    if domain_count != 31 or range_count != 31:
        errors.append(f"expected 31 domain and 31 range probes; found {domain_count}/{range_count}")

    expected_from_specs = {
        (spec.property_iri, RDFS.domain if spec.kind == "domain" else RDFS.range, spec.intended_class)
        for spec in PROBE_SPECS
    }
    if not EXPECTED_RETAINED_BASIS <= expected_from_specs:
        missing = sorted(EXPECTED_RETAINED_BASIS - expected_from_specs, key=lambda item: tuple(map(str, item)))
        errors.append(
            "retained basis includes triples absent from the frozen probe list: "
            + ", ".join(format_triple(triple) for triple in missing)
        )
    return errors


def check_retained_basis() -> BasisCheck:
    graph = Graph()
    bind_prefixes(graph)
    graph.parse(REPO_ROOT / "legacy/SSN2BFO-pre-COMS.ttl", format="turtle")
    local_domains = {(s, p, o) for s, p, o in graph.triples((None, RDFS.domain, None))}
    local_ranges = {(s, p, o) for s, p, o in graph.triples((None, RDFS.range, None))}
    missing_retained = set(EXPECTED_RETAINED_BASIS - local_domains)
    extra_domains = set(local_domains - EXPECTED_RETAINED_BASIS)
    extra_ranges = set(local_ranges)
    return BasisCheck(
        local_domains=local_domains,
        local_ranges=local_ranges,
        missing_retained=missing_retained,
        extra_domains=extra_domains,
        extra_ranges=extra_ranges,
    )


def add_probe(graph: Graph, spec: ProbeSpec) -> None:
    probe = spec.probe_iri
    graph.add((probe, RDF.type, OWL.Class))

    complement = BNode()
    graph.add((complement, OWL.complementOf, spec.intended_class))

    restriction = BNode()
    graph.add((restriction, RDF.type, OWL.Restriction))
    graph.add((restriction, OWL.onProperty, spec.property_iri))

    if spec.kind == "domain":
        some_values = BNode()
        graph.add((some_values, RDF.type, OWL.Restriction))
        graph.add((some_values, OWL.onProperty, spec.property_iri))
        graph.add((some_values, OWL.someValuesFrom, OWL.Thing))

        intersection = BNode()
        members = BNode()
        graph.add((intersection, RDF.type, OWL.Class))
        graph.add((intersection, OWL.intersectionOf, members))
        Collection(graph, members, [some_values, complement])
        graph.add((probe, OWL.equivalentClass, intersection))
    elif spec.kind == "range":
        graph.add((restriction, OWL.someValuesFrom, complement))
        graph.add((probe, OWL.equivalentClass, restriction))
    else:
        raise ValueError(f"unexpected probe kind: {spec.kind}")


def run_hermit(graph: Graph, graph_path: Path, reasoned_path: Path, robot: str | None) -> HermitRun:
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    if reasoned_path.exists():
        reasoned_path.unlink()
    graph.serialize(destination=graph_path, format="turtle")

    if robot is None:
        return HermitRun(
            graph_path=graph_path,
            reasoned_path=reasoned_path,
            triple_count=len(graph),
            return_code=None,
            reasoned_output_produced=False,
            owl_nothing_count=None,
            unsat_classes=set(),
            robot_output="ROBOT executable not found on PATH.",
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
    output_unsats = unsat_classes_from_robot_output(output)

    reasoned_output_produced = reasoned_path.exists() and reasoned_path.stat().st_size > 0
    reasoned_unsats: set[URIRef] = set()
    owl_nothing_count: int | None = None
    if reasoned_output_produced:
        reasoned_graph = Graph()
        bind_prefixes(reasoned_graph)
        reasoned_graph.parse(reasoned_path, format="turtle")
        reasoned_unsats = unsat_classes_from_graph(reasoned_graph)
        owl_nothing_count = len(reasoned_unsats)

    return HermitRun(
        graph_path=graph_path,
        reasoned_path=reasoned_path,
        triple_count=len(graph),
        return_code=proc.returncode,
        reasoned_output_produced=reasoned_output_produced,
        owl_nothing_count=owl_nothing_count,
        unsat_classes=output_unsats | reasoned_unsats,
        robot_output=output,
    )


def classify_probe_result(spec: ProbeSpec, run: HermitRun) -> ProbeResult:
    expected_probe_unsat = spec.probe_iri in run.unsat_classes
    unexpected_unsats = set(run.unsat_classes - {spec.probe_iri})
    satisfiable = run.return_code == 0 and not expected_probe_unsat
    inconclusive = (
        run.return_code is None
        or (run.return_code != 0 and not expected_probe_unsat and not unexpected_unsats)
    )
    return ProbeResult(
        spec=spec,
        run=run,
        expected_probe_unsat=expected_probe_unsat,
        satisfiable=satisfiable,
        inconclusive=inconclusive,
        unexpected_unsats=unexpected_unsats,
    )


def format_triple(triple: tuple[URIRef, URIRef, URIRef]) -> str:
    return f"{compact_iri(triple[0])} {compact_iri(triple[1])} {compact_iri(triple[2])} ."


def format_unsat(values: set[URIRef]) -> str:
    if not values:
        return "none"
    return ", ".join(f"`{compact_iri(value)}`" for value in sorted(values, key=str))


def write_report(
    path: Path,
    *,
    robot: str | None,
    spec_errors: list[str],
    basis: BasisCheck,
    baseline: HermitRun | None,
    probe_results: list[ProbeResult],
    elapsed_seconds: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    domain_probe_count = sum(1 for spec in PROBE_SPECS if spec.kind == "domain")
    range_probe_count = sum(1 for spec in PROBE_SPECS if spec.kind == "range")
    passed_probes = sum(1 for result in probe_results if result.passed)
    satisfiable_probes = [result for result in probe_results if result.satisfiable]
    inconclusive_probes = [result for result in probe_results if result.inconclusive]
    unexpected_unsats = sorted(
        {value for result in probe_results for value in result.unexpected_unsats},
        key=str,
    )
    baseline_passed = (
        baseline is not None
        and baseline.return_code == 0
        and baseline.reasoned_output_produced
        and baseline.owl_nothing_count == 0
        and not baseline.unsat_classes
    )
    overall_passed = (
        not spec_errors
        and basis.passed
        and baseline_passed
        and len(probe_results) == 62
        and passed_probes == 62
        and not satisfiable_probes
        and not inconclusive_probes
        and not unexpected_unsats
    )

    lines = [
        "# Object-Property Typing Probe Check",
        "",
        "This report is generated by `tools/test_object_property_typing_probes.py`.",
        "",
        "This non-gating historical diagnostic verifies that the frozen pre-COMS 22-triple object-property domain/range basis preserves all 62 intended typing entailments from the prior local network. It does not constrain the authoritative COMS-generated ontology.",
        "",
        "## Graph Profile",
        "",
        "The no-probe baseline and each probe load the full local SOSA closure:",
        "",
        *[f"- `{input_path}`" for input_path in GRAPH_INPUTS],
        "",
        "After loading, the check removes all `owl:imports` triples and the established sample simplicity blockers:",
        "",
        "```ttl",
        "sosa:isSampleOf rdf:type owl:FunctionalProperty .",
        "sosa:hasSample rdf:type owl:InverseFunctionalProperty .",
        "```",
        "",
        "## Retained-Basis Structural Check",
        "",
        "| Item | Result |",
        "|---|---:|",
        f"| retained local object-property domains | {len(basis.local_domains)} |",
        f"| retained local object-property ranges | {len(basis.local_ranges)} |",
        f"| expected retained domains missing | {len(basis.missing_retained)} |",
        f"| unexpected local domain triples | {len(basis.extra_domains)} |",
        f"| unexpected local range triples | {len(basis.extra_ranges)} |",
        f"| structural check | {'PASS' if basis.passed else 'FAIL'} |",
        "",
    ]
    if not basis.passed:
        lines.extend(
            [
                "### Structural Diagnostics",
                "",
                f"- Missing retained triples: {', '.join(format_triple(t) for t in sorted(basis.missing_retained, key=lambda item: tuple(map(str, item)))) or 'none'}",
                f"- Unexpected domain triples: {', '.join(format_triple(t) for t in sorted(basis.extra_domains, key=lambda item: tuple(map(str, item)))) or 'none'}",
                f"- Unexpected range triples: {', '.join(format_triple(t) for t in sorted(basis.extra_ranges, key=lambda item: tuple(map(str, item)))) or 'none'}",
                "",
            ]
        )

    lines.extend(
        [
            "## Probe Specification",
            "",
            "| Item | Result |",
            "|---|---:|",
            f"| probe specifications | {len(PROBE_SPECS)} |",
            f"| domain probes | {domain_probe_count} |",
            f"| range probes | {range_probe_count} |",
            f"| duplicate property/kind/class entries | {len(PROBE_SPECS) - len({(s.property_iri, s.kind, s.intended_class) for s in PROBE_SPECS})} |",
            f"| specification check | {'PASS' if not spec_errors else 'FAIL'} |",
            "",
        ]
    )
    if spec_errors:
        lines.extend(["Specification errors:", ""])
        lines.extend(f"- {error}" for error in spec_errors)
        lines.append("")

    lines.extend(
        [
            "## Test Method",
            "",
            "The check first confirms the no-probe full local SOSA closure is HermiT-clean. It then tests each probe independently against the same clean baseline graph. Probe classes are never batched, so one probe cannot provide entailment support for another.",
            "",
            "For a domain assertion `p rdfs:domain D`, the fresh probe class is equivalent to `p some owl:Thing` intersected with `not D`. For a range assertion `p rdfs:range R`, the fresh probe class is equivalent to `p some (not R)`. The expected result for each probe is unsatisfiability of the fresh probe class.",
            "",
            "An intentionally unsatisfiable probe may make `robot reason` return nonzero. This check treats that as a pass only when HermiT reports the expected fresh probe class as unsatisfiable and reports no unexpected ontology unsats.",
            "",
            "## Baseline Result",
            "",
            "| Item | Result |",
            "|---|---|",
            f"| ROBOT executable | `{markdown_escape(robot or 'not found')}` |",
        ]
    )
    if baseline is None:
        lines.extend(
            [
                "| baseline graph path | not run |",
                "| baseline triple count | n/a |",
                "| baseline return code | n/a |",
                "| baseline reasoned output | no |",
                "| baseline `owl:Nothing` count | n/a |",
                "| baseline unsat set | n/a |",
                "| baseline status | FAIL |",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"| baseline graph path | `{markdown_escape(str(baseline.graph_path))}` |",
                f"| baseline triple count | {baseline.triple_count} |",
                f"| baseline return code | {baseline.return_code} |",
                f"| baseline reasoned output | {'yes' if baseline.reasoned_output_produced else 'no'} |",
                f"| baseline `owl:Nothing` count | {'n/a' if baseline.owl_nothing_count is None else baseline.owl_nothing_count} |",
                f"| baseline unsat set | {format_unsat(baseline.unsat_classes)} |",
                f"| baseline status | {'PASS' if baseline_passed else 'FAIL'} |",
                "",
            ]
        )

    lines.extend(
        [
            "## Probe Summary",
            "",
            "| Item | Result |",
            "|---|---:|",
            f"| probes tested | {len(probe_results)} |",
            f"| expected-unsatisfiable probes | {passed_probes} |",
            f"| satisfiable probes | {len(satisfiable_probes)} |",
            f"| inconclusive probes | {len(inconclusive_probes)} |",
            f"| unexpected ontology unsats | {len(unexpected_unsats)} |",
            f"| runtime seconds | {elapsed_seconds:.2f} |",
            f"| overall status | {'PASS' if overall_passed else 'FAIL'} |",
            "",
            "## Probe Results",
            "",
            "| Probe | Kind | Property | Intended class | Workbook row | Graph path | Return code | Expected probe unsat | Unexpected unsats | Status |",
            "|---|---|---|---|---|---|---:|---|---|---|",
        ]
    )
    for result in probe_results:
        spec = result.spec
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{spec.identifier}`",
                    spec.kind,
                    f"`{compact_iri(spec.property_iri)}`",
                    f"`{compact_iri(spec.intended_class)}`",
                    spec.workbook_row,
                    f"`{markdown_escape(str(result.run.graph_path))}`",
                    "" if result.run.return_code is None else str(result.run.return_code),
                    "yes" if result.expected_probe_unsat else "no",
                    format_unsat(result.unexpected_unsats),
                    "PASS" if result.passed else "FAIL",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Unexpected Unsat Set",
            "",
            format_unsat(set(unexpected_unsats)),
            "",
            "## Interpretation",
            "",
        ]
    )
    if overall_passed:
        lines.extend(
            [
                "All 62 frozen typing probes were independently unsatisfiable, and the no-probe full local SOSA closure remained HermiT-clean.",
                "",
                "This confirms that the frozen pre-COMS 22-triple basis preserves the historical object-property typing entailments guarded by this diagnostic.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "The object-property typing probe check failed. Inspect the structural diagnostics, baseline result, and per-probe rows before accepting mapping changes.",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
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
    args = parser.parse_args()

    started = time.perf_counter()
    output_path = REPO_ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)
    tmp_dir = Path(args.tmp_dir)
    robot = shutil.which("robot")

    spec_errors = verify_probe_specs()
    basis = check_retained_basis()
    baseline: HermitRun | None = None
    probe_results: list[ProbeResult] = []

    if not spec_errors and basis.passed:
        base_graph = build_full_closure_graph()
        baseline = run_hermit(
            base_graph,
            tmp_dir / "baseline-full-sosa-closure.ttl",
            tmp_dir / "baseline-full-sosa-closure-reasoned.ttl",
            robot,
        )
        baseline_passed = (
            baseline.return_code == 0
            and baseline.reasoned_output_produced
            and baseline.owl_nothing_count == 0
            and not baseline.unsat_classes
        )
        if baseline_passed:
            for spec in PROBE_SPECS:
                graph = clone_graph(base_graph)
                add_probe(graph, spec)
                run = run_hermit(
                    graph,
                    tmp_dir / f"{spec.identifier}.ttl",
                    tmp_dir / f"{spec.identifier}-reasoned.ttl",
                    robot,
                )
                probe_results.append(classify_probe_result(spec, run))

    elapsed = time.perf_counter() - started
    write_report(
        output_path,
        robot=robot,
        spec_errors=spec_errors,
        basis=basis,
        baseline=baseline,
        probe_results=probe_results,
        elapsed_seconds=elapsed,
    )

    passed_probes = sum(1 for result in probe_results if result.passed)
    satisfiable = sum(1 for result in probe_results if result.satisfiable)
    inconclusive = sum(1 for result in probe_results if result.inconclusive)
    unexpected = {value for result in probe_results for value in result.unexpected_unsats}
    baseline_passed = (
        baseline is not None
        and baseline.return_code == 0
        and baseline.reasoned_output_produced
        and baseline.owl_nothing_count == 0
        and not baseline.unsat_classes
    )
    overall_passed = (
        not spec_errors
        and basis.passed
        and baseline_passed
        and len(probe_results) == 62
        and passed_probes == 62
        and satisfiable == 0
        and inconclusive == 0
        and not unexpected
    )

    print(f"Wrote {output_path}")
    print(f"Retained local domains: {len(basis.local_domains)}")
    print(f"Retained local ranges: {len(basis.local_ranges)}")
    print(f"Probes specified: {len(PROBE_SPECS)}")
    print(f"Probes tested: {len(probe_results)}")
    print(f"Expected-unsatisfiable probes: {passed_probes}")
    print(f"Satisfiable probes: {satisfiable}")
    print(f"Inconclusive probes: {inconclusive}")
    print(f"Unexpected ontology unsats: {len(unexpected)}")
    print(f"Runtime seconds: {elapsed:.2f}")
    print(f"Summary: {'PASS' if overall_passed else 'FAIL'}")

    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
