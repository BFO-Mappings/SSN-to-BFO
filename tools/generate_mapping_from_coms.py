#!/usr/bin/env python3
"""Generate a parallel SSN2BFO mapping candidate from a COMS workbook."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    import openpyxl
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency guard
    raise SystemExit("Missing dependency: openpyxl is required to inspect the COMS workbook.") from exc

try:
    from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef
    from rdflib.collection import Collection
    from rdflib.namespace import XSD
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency guard
    raise SystemExit("Missing dependency: rdflib is required to generate and validate RDF.") from exc


REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_COLUMNS = (
    "sssom:subject_id",
    "sssom:predicate_id",
    "coms:Target",
    "coms:Reasoning",
)

ONTOLOGY_IRI = URIRef("http://www.sks.ai/SSN2BFO/")
DIRECT_IMPORTS = (
    URIRef("http://www.w3.org/ns/ssn/"),
    URIRef("http://www.w3.org/ns/sosa/sampling/"),
    URIRef("http://www.w3.org/ns/ssn/systems/"),
    URIRef("https://www.commoncoreontologies.org/2024-11-06/CommonCoreOntologiesMerged"),
)

SOSA = Namespace("http://www.w3.org/ns/sosa/")
SSN = Namespace("http://www.w3.org/ns/ssn/")
SSN_SYSTEM = Namespace("http://www.w3.org/ns/ssn/systems/")
SAMPLING = Namespace("http://www.w3.org/ns/sosa/sampling/")
BFO = Namespace("http://purl.obolibrary.org/obo/")
CCO = Namespace("https://www.commoncoreontologies.org/")
COMS_COVERAGE = Namespace("http://www.sks.ai/SSN2BFO/coms/coverage#")

PREFIXES = {
    "bfo": str(BFO),
    "cco": str(CCO),
    "owl": str(OWL),
    "rdf": str(RDF),
    "rdfs": str(RDFS),
    "sampling": str(SAMPLING),
    "sosa": str(SOSA),
    "ssn": str(SSN),
    "ssn-system": str(SSN_SYSTEM),
}

PREFIX_FILES = {
    "bfo": Path("imports/cco.ttl"),
    "cco": Path("imports/cco.ttl"),
    "sampling": Path("imports/sosa-sampling.ttl"),
    "sosa": Path("imports/sosa.ttl"),
    "ssn": Path("imports/ssn.ttl"),
    "ssn-system": Path("imports/ssn-systems.ttl"),
}

SOURCE_IMPORTS = (
    Path("imports/sosa.ttl"),
    Path("imports/sosa-sampling.ttl"),
    Path("imports/ssn.ttl"),
    Path("imports/ssn-systems.ttl"),
)

CANDIDATE_CLOSURE_INPUTS = (
    Path("imports/cco.ttl"),
    Path("imports/sosa.ttl"),
    Path("imports/sosa-sampling.ttl"),
    Path("imports/ssn.ttl"),
    Path("imports/ssn-systems.ttl"),
)

ALLOWED_PREDICATES = {
    "rdfs:subClassOf": RDFS.subClassOf,
    "owl:equivalentClass": OWL.equivalentClass,
    "rdfs:subPropertyOf": RDFS.subPropertyOf,
    "owl:equivalentProperty": OWL.equivalentProperty,
    "owl:propertyChainAxiom": OWL.propertyChainAxiom,
}

CLASS_PREDICATES = {"rdfs:subClassOf", "owl:equivalentClass"}
OBJECT_PROPERTY_PREDICATES = {
    "rdfs:subPropertyOf",
    "owl:equivalentProperty",
    "owl:propertyChainAxiom",
}

CLEANUP_TRIPLES = (
    (SOSA.isSampleOf, RDF.type, OWL.FunctionalProperty),
    (SOSA.hasSample, RDF.type, OWL.InverseFunctionalProperty),
)

TOKEN_RE = re.compile(
    r"\s*("
    r"\("
    r"|\)"
    r"|[A-Za-z][A-Za-z0-9_-]*:[A-Za-z_][A-Za-z0-9_-]*"
    r"|and\b"
    r"|or\b"
    r"|some\b"
    r"|o\b"
    r")",
)
UNSAT_RE = re.compile(r"unsatisfiable:\s+(\S+)")


@dataclass(frozen=True)
class WorkbookRow:
    sheet: str
    row_number: int
    subject_text: str
    predicate_text: str
    target_text: str
    reasoning_text: str

    @property
    def row_id(self) -> str:
        return f"{self.sheet}!{self.row_number}"

    @property
    def is_blank_mapping(self) -> bool:
        return bool(self.subject_text) and not self.predicate_text and not self.target_text

    @property
    def is_mapped(self) -> bool:
        return bool(self.subject_text and self.predicate_text and self.target_text)


@dataclass(frozen=True)
class Resolution:
    token: str
    iri: URIRef
    kind: str
    method: str
    label: str = ""


@dataclass
class LabelResolutionRecord:
    token: str
    iri: URIRef
    kind: str
    method: str
    label: str
    rows: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Expr:
    kind: str
    iri: URIRef | None = None
    children: tuple["Expr", ...] = ()
    prop: URIRef | None = None
    filler: "Expr | None" = None


@dataclass
class ProcessedRow:
    row: WorkbookRow
    subject: URIRef
    subject_kind: str
    predicate: str
    target: str
    expr: Expr | None = None
    target_property: URIRef | None = None
    property_chain: tuple[URIRef, ...] = ()


@dataclass
class WorkbookStats:
    worksheets_read: list[str] = field(default_factory=list)
    rows_by_sheet: Counter[str] = field(default_factory=Counter)
    populated_rows_by_sheet: Counter[str] = field(default_factory=Counter)
    mapped_rows: int = 0
    blank_mapping_rows: int = 0
    class_mapping_rows: int = 0
    object_property_mapping_rows: int = 0
    property_chain_rows: int = 0


@dataclass
class HermitResult:
    graph_path: Path
    reasoned_path: Path
    generated_triple_count: int
    closure_triple_count: int
    return_code: int | None
    reasoned_output_produced: bool
    owl_nothing_count: int | None
    unsat_classes: list[URIRef]
    robot_output: str
    robot_path: str | None

    @property
    def passed(self) -> bool:
        return (
            self.return_code == 0
            and self.reasoned_output_produced
            and self.owl_nothing_count == 0
            and not self.unsat_classes
        )


@dataclass
class CoverageResult:
    source_terms: dict[URIRef, str]
    mapped_terms: set[URIRef]
    explicit_blank_terms: set[URIRef]
    spreadsheet_missing_subjects: set[str]
    query_source_count: int
    query_unmapped_count: int

    @property
    def mapped_classes(self) -> set[URIRef]:
        return {term for term in self.mapped_terms if self.source_terms.get(term) == "class"}

    @property
    def mapped_object_properties(self) -> set[URIRef]:
        return {term for term in self.mapped_terms if self.source_terms.get(term) == "object_property"}

    @property
    def unmapped_classes(self) -> set[URIRef]:
        return {
            term
            for term, kind in self.source_terms.items()
            if kind == "class" and term not in self.mapped_terms
        }

    @property
    def unmapped_object_properties(self) -> set[URIRef]:
        return {
            term
            for term, kind in self.source_terms.items()
            if kind == "object_property" and term not in self.mapped_terms
        }

    @property
    def absent_terms(self) -> set[URIRef]:
        return set(self.source_terms) - self.mapped_terms - self.explicit_blank_terms


@dataclass
class ComparisonResult:
    both: set[tuple[str, str, str, str]]
    generated_only: set[tuple[str, str, str, str]]
    current_only: set[tuple[str, str, str, str]]
    class_expression_differences: list[str]
    object_property_differences: list[str]
    property_chain_differences: list[str]
    current_domain_range_absent: set[tuple[str, str, str]]


class GenerationError(Exception):
    pass


class ManchesterParser:
    def __init__(self, text: str, resolver: "Resolver", row_id: str):
        self.text = text
        self.resolver = resolver
        self.row_id = row_id
        self.tokens = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> list[str]:
        tokens: list[str] = []
        cursor = 0
        while cursor < len(text):
            match = TOKEN_RE.match(text, cursor)
            if not match:
                excerpt = text[cursor : cursor + 30]
                raise GenerationError(f"{self.row_id}: malformed Manchester expression near {excerpt!r}")
            tokens.append(match.group(1))
            cursor = match.end()
        return tokens

    def parse(self) -> Expr:
        if not self.tokens:
            raise GenerationError(f"{self.row_id}: blank Manchester expression")
        expr = self._parse_or()
        if self._peek() is not None:
            raise GenerationError(f"{self.row_id}: unexpected token {self._peek()!r}")
        return expr

    def _peek(self) -> str | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def _consume(self, expected: str | None = None) -> str:
        token = self._peek()
        if token is None:
            raise GenerationError(f"{self.row_id}: unexpected end of expression")
        if expected is not None and token != expected:
            raise GenerationError(f"{self.row_id}: expected {expected!r}, found {token!r}")
        self.pos += 1
        return token

    def _parse_or(self) -> Expr:
        children = [self._parse_and()]
        while self._peek() == "or":
            self._consume("or")
            children.append(self._parse_and())
        if len(children) == 1:
            return children[0]
        return Expr("union", children=tuple(children))

    def _parse_and(self) -> Expr:
        children = [self._parse_primary()]
        while self._peek() == "and":
            self._consume("and")
            children.append(self._parse_primary())
        if len(children) == 1:
            return children[0]
        return Expr("intersection", children=tuple(children))

    def _parse_primary(self) -> Expr:
        token = self._peek()
        if token == "(":
            self._consume("(")
            expr = self._parse_or()
            self._consume(")")
            return expr
        if token is None:
            raise GenerationError(f"{self.row_id}: unexpected end of expression")
        if ":" not in token:
            raise GenerationError(f"{self.row_id}: expected CURIE or parenthesized expression, found {token!r}")
        curie = self._consume()
        if self._peek() == "some":
            self._consume("some")
            prop = self.resolver.resolve(curie, "object_property", self.row_id).iri
            filler = self._parse_primary()
            return Expr("some", prop=prop, filler=filler)
        iri = self.resolver.resolve(curie, "class", self.row_id).iri
        return Expr("named", iri=iri)


class Resolver:
    def __init__(self) -> None:
        self.graphs: dict[str, Graph] = {}
        self.label_index: dict[tuple[str, str, str], set[URIRef]] = defaultdict(set)
        self.labels: dict[URIRef, str] = {}
        self.records: dict[tuple[str, str, str], LabelResolutionRecord] = {}
        self.cache: dict[tuple[str, str], Resolution] = {}
        self.source_graph = Graph()
        self._load_graphs()

    def _load_graphs(self) -> None:
        loaded_by_file: dict[Path, Graph] = {}
        for prefix, rel_path in PREFIX_FILES.items():
            graph = loaded_by_file.get(rel_path)
            if graph is None:
                graph = Graph()
                graph.parse(REPO_ROOT / rel_path, format="turtle")
                loaded_by_file[rel_path] = graph
            self.graphs[prefix] = graph

        for path in SOURCE_IMPORTS:
            self.source_graph.parse(REPO_ROOT / path, format="turtle")

        for prefix, graph in self.graphs.items():
            if prefix in {"owl", "rdf", "rdfs"}:
                continue
            for subject, _, label in graph.triples((None, RDFS.label, None)):
                if not isinstance(subject, URIRef):
                    continue
                label_text = str(label)
                self.labels.setdefault(subject, label_text)
                for kind in self.kinds(subject, graph):
                    self.label_index[(prefix, self._normalize_key(label_text), kind)].add(subject)

    def _normalize_key(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    def _label_style_key(self, local: str) -> str:
        spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", local)
        spaced = spaced.replace("_", " ").replace("-", " ")
        return self._normalize_key(spaced)

    def kinds(self, iri: URIRef, graph: Graph | None = None) -> set[str]:
        graph = graph or self.graph_for_iri(iri)
        kinds: set[str] = set()
        if (iri, RDF.type, OWL.Class) in graph or (iri, RDF.type, RDFS.Class) in graph:
            kinds.add("class")
        if (iri, RDF.type, OWL.ObjectProperty) in graph:
            kinds.add("object_property")
        return kinds

    def graph_for_iri(self, iri: URIRef) -> Graph:
        text = str(iri)
        for prefix, namespace in sorted(PREFIXES.items(), key=lambda item: len(item[1]), reverse=True):
            if prefix in self.graphs and text.startswith(namespace):
                return self.graphs[prefix]
        return self.graphs["cco"]

    def resolve(self, token: str, expected_kind: str, row_id: str) -> Resolution:
        cache_key = (token, expected_kind)
        if cache_key in self.cache:
            resolution = self.cache[cache_key]
            self._record_resolution(resolution, row_id)
            return resolution

        if ":" not in token:
            raise GenerationError(f"{row_id}: token {token!r} is not a CURIE")
        prefix, local = token.split(":", 1)
        if prefix not in PREFIXES:
            raise GenerationError(f"{row_id}: unknown prefix {prefix!r} in {token!r}")
        if prefix in {"owl", "rdf", "rdfs"}:
            iri = URIRef(PREFIXES[prefix] + local)
            resolution = Resolution(token, iri, expected_kind, "direct")
            self.cache[cache_key] = resolution
            return resolution
        graph = self.graphs.get(prefix)
        if graph is None:
            raise GenerationError(f"{row_id}: prefix {prefix!r} is not associated with a local ontology")

        direct_iri = URIRef(PREFIXES[prefix] + local)
        direct_kinds = self.kinds(direct_iri, graph)
        if expected_kind in direct_kinds:
            resolution = Resolution(token, direct_iri, expected_kind, "direct")
            self.cache[cache_key] = resolution
            return resolution
        if direct_kinds and expected_kind not in direct_kinds:
            raise GenerationError(
                f"{row_id}: {token} resolves directly to {sorted(direct_kinds)}, not {expected_kind}"
            )

        exact_matches = {
            subject
            for subject, label in graph.subject_objects(RDFS.label)
            if isinstance(subject, URIRef)
            and str(label) == local
            and expected_kind in self.kinds(subject, graph)
        }
        if len(exact_matches) == 1:
            iri = next(iter(exact_matches))
            resolution = Resolution(token, iri, expected_kind, "exact_label", self.labels.get(iri, local))
            self.cache[cache_key] = resolution
            self._record_resolution(resolution, row_id)
            return resolution
        if len(exact_matches) > 1:
            raise GenerationError(
                f"{row_id}: {token} has multiple exact label matches: "
                + ", ".join(sorted(map(str, exact_matches)))
            )

        label_key = self._label_style_key(local)
        style_matches = self.label_index.get((prefix, label_key, expected_kind), set())
        if len(style_matches) == 1:
            iri = next(iter(style_matches))
            resolution = Resolution(
                token,
                iri,
                expected_kind,
                "label_style_key",
                self.labels.get(iri, local),
            )
            self.cache[cache_key] = resolution
            self._record_resolution(resolution, row_id)
            return resolution
        if len(style_matches) > 1:
            raise GenerationError(
                f"{row_id}: {token} has multiple label-style matches: "
                + ", ".join(sorted(map(str, style_matches)))
            )

        raise GenerationError(f"{row_id}: unresolved {expected_kind} token {token!r}")

    def resolve_source_subject(self, token: str, row_id: str) -> tuple[URIRef, str]:
        if ":" not in token:
            raise GenerationError(f"{row_id}: source subject {token!r} is not a CURIE")
        prefix, _ = token.split(":", 1)
        if prefix not in {"sosa", "sampling", "ssn", "ssn-system"}:
            raise GenerationError(f"{row_id}: source subject {token!r} is not in a source ontology prefix")
        iri: URIRef | None = None
        source_kinds: set[str] = set()
        class_error: GenerationError | None = None
        try:
            iri = self.resolve(token, "class", row_id).iri
            source_kinds = self.kinds(iri, self.source_graph)
        except GenerationError as exc:
            class_error = exc
        if not source_kinds:
            try:
                iri = self.resolve(token, "object_property", row_id).iri
                source_kinds = self.kinds(iri, self.source_graph)
            except GenerationError:
                if class_error is not None:
                    raise class_error
        if len(source_kinds) != 1:
            raise GenerationError(f"{row_id}: source subject {token!r} has ambiguous or missing type {source_kinds}")
        assert iri is not None
        return iri, next(iter(source_kinds))

    def _record_resolution(self, resolution: Resolution, row_id: str) -> None:
        if resolution.method == "direct":
            return
        key = (resolution.token, str(resolution.iri), resolution.kind)
        record = self.records.get(key)
        if record is None:
            record = LabelResolutionRecord(
                token=resolution.token,
                iri=resolution.iri,
                kind=resolution.kind,
                method=resolution.method,
                label=resolution.label,
            )
            self.records[key] = record
        record.rows.add(row_id)


def normalize_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def compact_iri(value: URIRef | str) -> str:
    text = str(value)
    for prefix, namespace in sorted(PREFIXES.items(), key=lambda item: len(item[1]), reverse=True):
        if text.startswith(namespace):
            return f"{prefix}:{text[len(namespace):]}"
    return f"<{text}>"


def command_text(command: list[str]) -> str:
    return shlex.join(command)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bind_prefixes(graph: Graph) -> None:
    for prefix, namespace in PREFIXES.items():
        graph.bind(prefix, Namespace(namespace))


def read_workbook(path: Path) -> tuple[list[WorkbookRow], WorkbookStats]:
    workbook = openpyxl.load_workbook(path, data_only=True)
    rows: list[WorkbookRow] = []
    stats = WorkbookStats()
    for worksheet in workbook.worksheets:
        headers = [normalize_cell(worksheet.cell(row=1, column=col).value) for col in range(1, worksheet.max_column + 1)]
        if not all(column in headers for column in REQUIRED_COLUMNS):
            continue
        stats.worksheets_read.append(worksheet.title)
        header_index = {header: idx + 1 for idx, header in enumerate(headers)}
        for row_number in range(2, worksheet.max_row + 1):
            row = WorkbookRow(
                sheet=worksheet.title,
                row_number=row_number,
                subject_text=normalize_cell(worksheet.cell(row=row_number, column=header_index["sssom:subject_id"]).value),
                predicate_text=normalize_cell(worksheet.cell(row=row_number, column=header_index["sssom:predicate_id"]).value),
                target_text=normalize_cell(worksheet.cell(row=row_number, column=header_index["coms:Target"]).value),
                reasoning_text=normalize_cell(worksheet.cell(row=row_number, column=header_index["coms:Reasoning"]).value),
            )
            stats.rows_by_sheet[worksheet.title] += 1
            if row.subject_text or row.predicate_text or row.target_text or row.reasoning_text:
                stats.populated_rows_by_sheet[worksheet.title] += 1
                rows.append(row)
    if not stats.worksheets_read:
        raise GenerationError(f"no worksheet in {path} contains the required COMS header")
    return rows, stats


def validate_and_process_rows(rows: list[WorkbookRow], resolver: Resolver, stats: WorkbookStats) -> list[ProcessedRow]:
    processed: list[ProcessedRow] = []
    mapping_by_key: dict[tuple[str, str], str] = {}
    for row in rows:
        if not row.subject_text:
            if row.predicate_text or row.target_text:
                raise GenerationError(f"{row.row_id}: predicate/target populated without subject")
            continue

        subject, subject_kind = resolver.resolve_source_subject(row.subject_text, row.row_id)

        if row.is_blank_mapping:
            stats.blank_mapping_rows += 1
            processed.append(
                ProcessedRow(
                    row=row,
                    subject=subject,
                    subject_kind=subject_kind,
                    predicate="",
                    target="",
                )
            )
            continue

        if not row.predicate_text or not row.target_text:
            raise GenerationError(
                f"{row.row_id}: mapped rows must populate subject, predicate, and target; "
                "only subject-only rows are allowed as explicit blank mappings"
            )
        if row.predicate_text not in ALLOWED_PREDICATES:
            raise GenerationError(f"{row.row_id}: invalid predicate {row.predicate_text!r}")

        if row.predicate_text in CLASS_PREDICATES and subject_kind != "class":
            raise GenerationError(f"{row.row_id}: class predicate used with {subject_kind} subject")
        if row.predicate_text in OBJECT_PROPERTY_PREDICATES and subject_kind != "object_property":
            raise GenerationError(f"{row.row_id}: object-property predicate used with {subject_kind} subject")

        key = (str(subject), row.predicate_text)
        previous_target = mapping_by_key.get(key)
        if previous_target is not None and previous_target != row.target_text:
            raise GenerationError(
                f"{row.row_id}: duplicate mapping for {row.subject_text} {row.predicate_text} "
                f"has incompatible targets {previous_target!r} and {row.target_text!r}"
            )
        mapping_by_key[key] = row.target_text

        if row.predicate_text in CLASS_PREDICATES:
            expr = ManchesterParser(row.target_text, resolver, row.row_id).parse()
            stats.class_mapping_rows += 1
            processed.append(
                ProcessedRow(
                    row=row,
                    subject=subject,
                    subject_kind=subject_kind,
                    predicate=row.predicate_text,
                    target=row.target_text,
                    expr=expr,
                )
            )
        elif row.predicate_text == "owl:propertyChainAxiom":
            chain = parse_property_chain(row.target_text, resolver, row.row_id)
            stats.object_property_mapping_rows += 1
            stats.property_chain_rows += 1
            processed.append(
                ProcessedRow(
                    row=row,
                    subject=subject,
                    subject_kind=subject_kind,
                    predicate=row.predicate_text,
                    target=row.target_text,
                    property_chain=chain,
                )
            )
        else:
            target_property = resolver.resolve(row.target_text, "object_property", row.row_id).iri
            stats.object_property_mapping_rows += 1
            processed.append(
                ProcessedRow(
                    row=row,
                    subject=subject,
                    subject_kind=subject_kind,
                    predicate=row.predicate_text,
                    target=row.target_text,
                    target_property=target_property,
                )
            )
        stats.mapped_rows += 1
    return processed


def parse_property_chain(text: str, resolver: Resolver, row_id: str) -> tuple[URIRef, ...]:
    tokens = [token for token in re.split(r"\s+", text.strip()) if token]
    if len(tokens) < 3 or len(tokens) % 2 == 0:
        raise GenerationError(f"{row_id}: invalid property-chain syntax {text!r}")
    chain: list[URIRef] = []
    for index, token in enumerate(tokens):
        if index % 2 == 1:
            if token != "o":
                raise GenerationError(f"{row_id}: property-chain separator must be 'o', found {token!r}")
            continue
        chain.append(resolver.resolve(token, "object_property", row_id).iri)
    if len(chain) < 2:
        raise GenerationError(f"{row_id}: property chains must contain at least two properties")
    return tuple(chain)


def expr_to_rdf(graph: Graph, expr: Expr) -> URIRef | BNode:
    if expr.kind == "named":
        assert expr.iri is not None
        return expr.iri
    if expr.kind in {"intersection", "union"}:
        node = BNode()
        graph.add((node, RDF.type, OWL.Class))
        list_node = BNode()
        predicate = OWL.intersectionOf if expr.kind == "intersection" else OWL.unionOf
        graph.add((node, predicate, list_node))
        Collection(graph, list_node, [expr_to_rdf(graph, child) for child in expr.children])
        return node
    if expr.kind == "some":
        assert expr.prop is not None and expr.filler is not None
        node = BNode()
        graph.add((node, RDF.type, OWL.Restriction))
        graph.add((node, OWL.onProperty, expr.prop))
        graph.add((node, OWL.someValuesFrom, expr_to_rdf(graph, expr.filler)))
        return node
    raise GenerationError(f"unsupported expression node {expr.kind!r}")


def generate_ontology(processed_rows: list[ProcessedRow], output_path: Path) -> Graph:
    graph = Graph()
    bind_prefixes(graph)
    graph.add((ONTOLOGY_IRI, RDF.type, OWL.Ontology))
    for import_iri in DIRECT_IMPORTS:
        graph.add((ONTOLOGY_IRI, OWL.imports, import_iri))

    for item in processed_rows:
        if not item.predicate:
            continue
        predicate_iri = ALLOWED_PREDICATES[item.predicate]
        if item.expr is not None:
            graph.add((item.subject, predicate_iri, expr_to_rdf(graph, item.expr)))
        elif item.target_property is not None:
            graph.add((item.subject, predicate_iri, item.target_property))
        elif item.property_chain:
            chain_node = BNode()
            Collection(graph, chain_node, list(item.property_chain))
            graph.add((item.subject, OWL.propertyChainAxiom, chain_node))
        else:
            raise GenerationError(f"{item.row.row_id}: processed row has no target")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=output_path, format="turtle")
    return graph


def normalized_mapping_rows(processed_rows: list[ProcessedRow], graph: Graph) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for item in processed_rows:
        if not item.predicate:
            continue
        predicate_iri = ALLOWED_PREDICATES[item.predicate]
        if item.expr is not None:
            objects = list(graph.objects(item.subject, predicate_iri))
            normalized = " ; ".join(canonical_expr(graph, obj) for obj in objects)
        elif item.target_property is not None:
            normalized = compact_iri(item.target_property)
        elif item.property_chain:
            normalized = " o ".join(compact_iri(prop) for prop in item.property_chain)
        else:
            normalized = ""
        rows.append(
            (
                item.row.row_id,
                compact_iri(item.subject),
                item.predicate,
                item.target,
                normalized,
            )
        )
    return rows


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


def run_candidate_hermit(generated_path: Path, tmp_dir: Path) -> HermitResult:
    generated_graph = Graph()
    generated_graph.parse(generated_path, format="turtle")

    closure = Graph()
    bind_prefixes(closure)
    for path in CANDIDATE_CLOSURE_INPUTS:
        closure.parse(REPO_ROOT / path, format="turtle")
    closure.parse(generated_path, format="turtle")
    for triple in list(closure.triples((None, OWL.imports, None))):
        closure.remove(triple)
    for triple in CLEANUP_TRIPLES:
        closure.remove(triple)

    tmp_dir.mkdir(parents=True, exist_ok=True)
    graph_path = tmp_dir / "coms-candidate-full-closure.ttl"
    reasoned_path = tmp_dir / "coms-candidate-full-closure-reasoned.ttl"
    if reasoned_path.exists():
        reasoned_path.unlink()
    closure.serialize(destination=graph_path, format="turtle")

    robot = shutil.which("robot")
    if robot is None:
        return HermitResult(
            graph_path=graph_path,
            reasoned_path=reasoned_path,
            generated_triple_count=len(generated_graph),
            closure_triple_count=len(closure),
            return_code=None,
            reasoned_output_produced=False,
            owl_nothing_count=None,
            unsat_classes=[],
            robot_output="ROBOT executable not found on PATH.",
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
    output_unsats = {URIRef(match.group(1)) for match in UNSAT_RE.finditer(output)}
    reasoned_output_produced = reasoned_path.exists() and reasoned_path.stat().st_size > 0
    owl_nothing_count: int | None = None
    inferred_unsats: set[URIRef] = set(output_unsats)
    if reasoned_output_produced:
        reasoned_graph = Graph()
        bind_prefixes(reasoned_graph)
        reasoned_graph.parse(reasoned_path, format="turtle")
        inferred_unsats |= set(unsat_classes(reasoned_graph))
        owl_nothing_count = len(inferred_unsats)

    return HermitResult(
        graph_path=graph_path,
        reasoned_path=reasoned_path,
        generated_triple_count=len(generated_graph),
        closure_triple_count=len(closure),
        return_code=proc.returncode,
        reasoned_output_produced=reasoned_output_produced,
        owl_nothing_count=owl_nothing_count,
        unsat_classes=sorted(inferred_unsats, key=str),
        robot_output=output,
        robot_path=robot,
    )


def run_select_query(graph: Graph, query_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in graph.query((REPO_ROOT / query_path).read_text(encoding="utf-8")):
        asdict = row.asdict()
        rows.append({key: str(value) for key, value in asdict.items()})
    return rows


def build_source_graph() -> Graph:
    graph = Graph()
    bind_prefixes(graph)
    for path in SOURCE_IMPORTS:
        graph.parse(REPO_ROOT / path, format="turtle")
    return graph


def build_coverage(
    processed_rows: list[ProcessedRow],
    source_subject_errors: Iterable[str],
    coverage_report_path: Path,
) -> CoverageResult:
    source_graph = build_source_graph()
    source_query_rows = run_select_query(source_graph, Path("queries/source-classes-and-object-properties.rq"))
    source_terms = {
        URIRef(row["term"]): row["kind"]
        for row in source_query_rows
    }

    mapped_terms = {row.subject for row in processed_rows if row.predicate}
    explicit_blank_terms = {row.subject for row in processed_rows if not row.predicate}
    missing_subjects = set(source_subject_errors)

    coverage_graph = Graph()
    bind_prefixes(coverage_graph)
    coverage_graph.bind("coms", COMS_COVERAGE)
    for term, kind in sorted(source_terms.items(), key=lambda item: str(item[0])):
        coverage_graph.add((term, COMS_COVERAGE.sourceKind, Literal(kind)))
        if term in mapped_terms:
            status = "mapped"
        elif term in explicit_blank_terms:
            status = "explicitly_unmapped"
        else:
            status = "absent_from_spreadsheet"
        coverage_graph.add((term, COMS_COVERAGE.coverageStatus, Literal(status)))

    unmapped_rows = run_select_query(coverage_graph, Path("queries/unmapped-source-terms.rq"))
    result = CoverageResult(
        source_terms=source_terms,
        mapped_terms=mapped_terms,
        explicit_blank_terms=explicit_blank_terms,
        spreadsheet_missing_subjects=missing_subjects,
        query_source_count=len(source_query_rows),
        query_unmapped_count=len(unmapped_rows),
    )
    write_coverage_report(coverage_report_path, result)
    return result


def format_term_list(values: Iterable[URIRef | str]) -> list[str]:
    return [f"- `{compact_iri(value)}`" for value in sorted(values, key=str)]


def write_coverage_report(path: Path, coverage: CoverageResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# COMS Source-Term Coverage",
        "",
        "This report is generated by `tools/generate_mapping_from_coms.py`.",
        "",
        "Coverage scope is all non-deprecated named OWL classes and object properties defined by:",
        "",
        *[f"- `{path}`" for path in SOURCE_IMPORTS],
        "",
        "The source term inventory is produced by `queries/source-classes-and-object-properties.rq`. "
        "Unmapped terms are selected from the generated coverage graph by `queries/unmapped-source-terms.rq`.",
        "",
        "## Summary",
        "",
        "| Item | Count |",
        "|---|---:|",
        f"| source terms returned by SPARQL | {coverage.query_source_count} |",
        f"| mapped classes | {len(coverage.mapped_classes)} |",
        f"| unmapped classes | {len(coverage.unmapped_classes)} |",
        f"| mapped object properties | {len(coverage.mapped_object_properties)} |",
        f"| unmapped object properties | {len(coverage.unmapped_object_properties)} |",
        f"| explicitly listed blank mappings | {len(coverage.explicit_blank_terms)} |",
        f"| source terms absent from spreadsheet | {len(coverage.absent_terms)} |",
        f"| spreadsheet subjects not found in source ontologies | {len(coverage.spreadsheet_missing_subjects)} |",
        f"| unmapped rows returned by SPARQL coverage query | {coverage.query_unmapped_count} |",
        "",
        "## Mapped Classes",
        "",
        *format_term_list(coverage.mapped_classes),
        "",
        "## Unmapped Classes",
        "",
        *format_term_list(coverage.unmapped_classes),
        "",
        "## Mapped Object Properties",
        "",
        *format_term_list(coverage.mapped_object_properties),
        "",
        "## Unmapped Object Properties",
        "",
        *format_term_list(coverage.unmapped_object_properties),
        "",
        "## Explicitly Listed Blank Mappings",
        "",
        *format_term_list(coverage.explicit_blank_terms),
        "",
        "## Source Terms Absent From Spreadsheet",
        "",
        *format_term_list(coverage.absent_terms),
        "",
        "## Spreadsheet Subjects Not Found In Source Ontologies",
        "",
        *(f"- `{value}`" for value in sorted(coverage.spreadsheet_missing_subjects)),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def canonical_expr(graph: Graph, node: URIRef | BNode) -> str:
    if isinstance(node, URIRef):
        return str(node)
    if (node, OWL.intersectionOf, None) in graph:
        list_node = next(graph.objects(node, OWL.intersectionOf))
        items = sorted(canonical_expr(graph, item) for item in Collection(graph, list_node))
        return "ObjectIntersectionOf(" + " ".join(items) + ")"
    if (node, OWL.unionOf, None) in graph:
        list_node = next(graph.objects(node, OWL.unionOf))
        items = sorted(canonical_expr(graph, item) for item in Collection(graph, list_node))
        return "ObjectUnionOf(" + " ".join(items) + ")"
    if (node, OWL.onProperty, None) in graph and (node, OWL.someValuesFrom, None) in graph:
        prop = next(graph.objects(node, OWL.onProperty))
        filler = next(graph.objects(node, OWL.someValuesFrom))
        return f"ObjectSomeValuesFrom({prop} {canonical_expr(graph, filler)})"
    return f"_:{node}"


def property_chain_text(graph: Graph, list_node: BNode) -> str:
    return " o ".join(str(item) for item in Collection(graph, list_node))


def extract_mapping_axioms(graph: Graph) -> set[tuple[str, str, str, str]]:
    mappings: set[tuple[str, str, str, str]] = set()
    for predicate in (RDFS.subClassOf, OWL.equivalentClass):
        for subject, _, obj in graph.triples((None, predicate, None)):
            if isinstance(subject, URIRef):
                mappings.add(("class", str(subject), str(predicate), canonical_expr(graph, obj)))
    for predicate in (RDFS.subPropertyOf, OWL.equivalentProperty):
        for subject, _, obj in graph.triples((None, predicate, None)):
            if isinstance(subject, URIRef) and isinstance(obj, URIRef):
                mappings.add(("object_property", str(subject), str(predicate), str(obj)))
    for subject, _, obj in graph.triples((None, OWL.propertyChainAxiom, None)):
        if isinstance(subject, URIRef) and isinstance(obj, BNode):
            mappings.add(("property_chain", str(subject), str(OWL.propertyChainAxiom), property_chain_text(graph, obj)))
    return mappings


def compare_generated_to_current(generated_path: Path, report_path: Path, processed_rows: list[ProcessedRow]) -> ComparisonResult:
    generated = Graph()
    generated.parse(generated_path, format="turtle")
    current = Graph()
    current.parse(REPO_ROOT / "SSN2BFO.ttl", format="turtle")

    generated_mappings = extract_mapping_axioms(generated)
    current_mappings = extract_mapping_axioms(current)
    both = generated_mappings & current_mappings
    generated_only = generated_mappings - current_mappings
    current_only = current_mappings - generated_mappings

    class_diffs = diff_by_subject_predicate(generated_mappings, current_mappings, "class")
    object_property_diffs = diff_by_subject_predicate(generated_mappings, current_mappings, "object_property")
    property_chain_diffs = diff_by_subject_predicate(generated_mappings, current_mappings, "property_chain")

    current_domain_range = {
        (str(subject), str(predicate), str(obj))
        for predicate in (RDFS.domain, RDFS.range)
        for subject, _, obj in current.triples((None, predicate, None))
        if isinstance(subject, URIRef) and isinstance(obj, URIRef)
    }
    generated_domain_range = {
        (str(subject), str(predicate), str(obj))
        for predicate in (RDFS.domain, RDFS.range)
        for subject, _, obj in generated.triples((None, predicate, None))
        if isinstance(subject, URIRef) and isinstance(obj, URIRef)
    }
    current_domain_range_absent = current_domain_range - generated_domain_range

    result = ComparisonResult(
        both=both,
        generated_only=generated_only,
        current_only=current_only,
        class_expression_differences=class_diffs,
        object_property_differences=object_property_diffs,
        property_chain_differences=property_chain_diffs,
        current_domain_range_absent=current_domain_range_absent,
    )
    write_comparison_report(report_path, result, processed_rows)
    return result


def diff_by_subject_predicate(
    generated: set[tuple[str, str, str, str]],
    current: set[tuple[str, str, str, str]],
    kind: str,
) -> list[str]:
    gen_index = defaultdict(set)
    cur_index = defaultdict(set)
    for item in generated:
        if item[0] == kind:
            gen_index[(item[1], item[2])].add(item[3])
    for item in current:
        if item[0] == kind:
            cur_index[(item[1], item[2])].add(item[3])
    diffs: list[str] = []
    for key in sorted(set(gen_index) & set(cur_index)):
        if gen_index[key] != cur_index[key]:
            subject, predicate = key
            diffs.append(
                f"`{compact_iri(subject)}` `{compact_iri(predicate)}`: "
                f"generated={sorted(gen_index[key])}; current={sorted(cur_index[key])}"
            )
    return diffs


def format_mapping_rows(rows: Iterable[tuple[str, str, str, str]], limit: int | None = None) -> list[str]:
    formatted: list[str] = []
    sorted_rows = sorted(rows)
    if limit is not None:
        sorted_rows = sorted_rows[:limit]
    for kind, subject, predicate, target in sorted_rows:
        formatted.append(
            f"- `{kind}` `{compact_iri(subject)}` `{compact_iri(predicate)}` `{target}`"
        )
    return formatted or ["- none"]


def write_comparison_report(path: Path, result: ComparisonResult, processed_rows: list[ProcessedRow]) -> None:
    blank_rows = [row for row in processed_rows if not row.predicate]
    class_difference_lines = [f"- {value}" for value in result.class_expression_differences] or ["- none"]
    object_property_difference_lines = [f"- {value}" for value in result.object_property_differences] or ["- none"]
    property_chain_difference_lines = [f"- {value}" for value in result.property_chain_differences] or ["- none"]
    domain_range_lines = [
        f"- `{compact_iri(subject)}` `{compact_iri(predicate)}` `{compact_iri(obj)}`"
        for subject, predicate, obj in sorted(result.current_domain_range_absent)
    ] or ["- none"]
    blank_row_lines = [f"- `{item.row.subject_text}` at `{item.row.row_id}`" for item in blank_rows] or ["- none"]
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# COMS Generated vs Current Mapping Diff",
        "",
        "This report compares mapping-bearing axioms in `generated/SSN2BFO-from-COMS.ttl` against `SSN2BFO.ttl`. "
        "The candidate is not loaded together with the current ontology.",
        "",
        "## Summary",
        "",
        "| Item | Count |",
        "|---|---:|",
        f"| mappings present in both | {len(result.both)} |",
        f"| mappings only in generated candidate | {len(result.generated_only)} |",
        f"| mappings only in current validated ontology | {len(result.current_only)} |",
        f"| class-expression differences | {len(result.class_expression_differences)} |",
        f"| object-property mapping differences | {len(result.object_property_differences)} |",
        f"| property-chain differences | {len(result.property_chain_differences)} |",
        f"| current local domain/range basis axioms absent from candidate | {len(result.current_domain_range_absent)} |",
        f"| spreadsheet rows intentionally producing no mapping | {len(blank_rows)} |",
        "",
        "## Mappings Present In Both",
        "",
        *format_mapping_rows(result.both),
        "",
        "## Only In Generated Candidate",
        "",
        *format_mapping_rows(result.generated_only),
        "",
        "## Only In Current Validated Ontology",
        "",
        *format_mapping_rows(result.current_only),
        "",
        "## Class-Expression Differences",
        "",
        *class_difference_lines,
        "",
        "## Object-Property Mapping Differences",
        "",
        *object_property_difference_lines,
        "",
        "## Property-Chain Differences",
        "",
        *property_chain_difference_lines,
        "",
        "## Current Local Domain/Range Basis Axioms Absent From Candidate",
        "",
        *domain_range_lines,
        "",
        "## Spreadsheet Rows Intentionally Producing No Mapping",
        "",
        *blank_row_lines,
        "",
        "## Terms Requiring Human Review",
        "",
        "Human review should focus on generated-only mappings, current-only mappings, the absent local domain/range basis, and explicitly blank spreadsheet rows.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_generation_report(
    path: Path,
    *,
    workbook_path: Path,
    stats: WorkbookStats,
    resolver: Resolver,
    errors: list[str],
    output_path: Path,
    hermit: HermitResult | None,
    coverage: CoverageResult | None,
    comparison: ComparisonResult | None,
    normalized_rows: list[tuple[str, str, str, str, str]],
    elapsed_seconds: float,
    workbook_sha256: str,
    generator_sha256: str,
    generation_timestamp: str,
    candidate_sha256: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    error_lines = [f"- {error}" for error in errors] or ["- none"]
    lines = [
        "# COMS Mapping Generation Validation",
        "",
        "This report is generated by `tools/generate_mapping_from_coms.py`.",
        "",
        "## Source Metadata",
        "",
        "Freshness is determined from content hashes, not file timestamps.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| workbook SHA-256 | `{workbook_sha256}` |",
        f"| generator SHA-256 | `{generator_sha256}` |",
        f"| generation timestamp (UTC) | `{generation_timestamp}` |",
        f"| generated candidate SHA-256 | `{candidate_sha256}` |",
        "",
        "## Workbook",
        "",
        f"- Workbook path: `{workbook_path}`",
        f"- Worksheets read: {', '.join(f'`{name}`' for name in stats.worksheets_read) or 'none'}",
        "",
        "| Worksheet | Rows scanned | Populated rows |",
        "|---|---:|---:|",
        *[
            f"| `{sheet}` | {stats.rows_by_sheet[sheet]} | {stats.populated_rows_by_sheet[sheet]} |"
            for sheet in stats.worksheets_read
        ],
        "",
        "## Row Counts",
        "",
        "| Item | Count |",
        "|---|---:|",
        f"| mapped row count | {stats.mapped_rows} |",
        f"| blank mapping row count | {stats.blank_mapping_rows} |",
        f"| class mapping count | {stats.class_mapping_rows} |",
        f"| object-property mapping count | {stats.object_property_mapping_rows} |",
        f"| property-chain count | {stats.property_chain_rows} |",
        "",
        "## Prefixes Derived",
        "",
        *[f"- `{prefix}:` `{namespace}`" for prefix, namespace in sorted(PREFIXES.items())],
        "",
        "## Label-To-IRI Resolutions",
        "",
    ]
    records = sorted(resolver.records.values(), key=lambda record: (record.token, str(record.iri), record.kind))
    if records:
        lines.extend(["| Token | Kind | Method | Label | IRI | Rows |", "|---|---|---|---|---|---|"])
        for record in records:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{record.token}`",
                        record.kind,
                        record.method,
                        record.label.replace("|", "\\|"),
                        f"`{record.iri}`",
                        ", ".join(f"`{row}`" for row in sorted(record.rows)),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No label-to-IRI fallback resolutions were required.")

    lines.extend(
        [
            "",
            "## Malformed Or Unresolved Rows",
            "",
            *error_lines,
            "",
            "## Duplicate-Row Checks",
            "",
            "- Duplicate subject/predicate rows with incompatible targets are fatal.",
            "- No incompatible duplicate mappings were found." if not errors else "- Duplicate checks did not complete cleanly because generation errors were present.",
            "",
            "## Generated Ontology",
            "",
            f"- Path: `{output_path}`",
            f"- Generated mapping triple count: {'n/a' if hermit is None else hermit.generated_triple_count}",
            "- `coms:Reasoning` remained spreadsheet-only and was not emitted into the ontology.",
            "- `SSN2BFO.ttl` was not replaced or edited by this tool.",
            "",
            "## Candidate Closure HermiT Result",
            "",
            "| Item | Result |",
            "|---|---|",
        ]
    )
    if hermit is None:
        lines.extend(
            [
                "| ROBOT executable | n/a |",
                "| full candidate closure triple count | n/a |",
                "| HermiT return code | n/a |",
                "| reasoned output produced | no |",
                "| `owl:Nothing` count | n/a |",
                "| named unsat count | n/a |",
                "| named unsat set | n/a |",
                "| overall status | FAIL |",
            ]
        )
    else:
        lines.extend(
            [
                f"| ROBOT executable | `{hermit.robot_path or 'not found'}` |",
                "| candidate closure graph path | temporary validation artifact (`coms-candidate-full-closure.ttl`) |",
                "| reasoned output path | temporary validation artifact (`coms-candidate-full-closure-reasoned.ttl`) |",
                f"| full candidate closure triple count | {hermit.closure_triple_count} |",
                f"| HermiT return code | {'' if hermit.return_code is None else hermit.return_code} |",
                f"| reasoned output produced | {'yes' if hermit.reasoned_output_produced else 'no'} |",
                f"| `owl:Nothing` count | {'n/a' if hermit.owl_nothing_count is None else hermit.owl_nothing_count} |",
                f"| named unsat count | {len(hermit.unsat_classes)} |",
                f"| named unsat set | {', '.join(f'`{compact_iri(value)}`' for value in hermit.unsat_classes) or 'clean'} |",
                f"| overall status | {'PASS' if hermit.passed else 'FAIL'} |",
            ]
        )
        if hermit.robot_output:
            excerpt = hermit.robot_output.strip()
            if len(excerpt) > 4000:
                excerpt = excerpt[:4000] + "\n... [truncated]"
            lines.extend(
                [
                    "",
                    "### ROBOT Output",
                    "",
                    "```text",
                    excerpt,
                    "```",
                ]
            )

    lines.extend(
        [
            "",
            "## Parsed/Normalized Mapping Expressions",
            "",
            "This section records the normalized form generated from each mapped spreadsheet row, making Manchester grouping and precedence visible during review.",
            "",
        ]
    )
    if normalized_rows:
        lines.extend(["| Row | Subject | Predicate | Original target | Normalized generated form |", "|---|---|---|---|---|"])
        for row_id, subject, predicate, original, normalized in normalized_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row_id}`",
                        f"`{subject}`",
                        f"`{predicate}`",
                        original.replace("|", "\\|"),
                        normalized.replace("|", "\\|"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No mapped rows were normalized.")

    lines.extend(
        [
            "",
            "## Source-Term Coverage Summary",
            "",
            "| Item | Count |",
            "|---|---:|",
        ]
    )
    if coverage is None:
        lines.extend(
            [
                "| mapped classes | n/a |",
                "| unmapped classes | n/a |",
                "| mapped object properties | n/a |",
                "| unmapped object properties | n/a |",
            ]
        )
    else:
        lines.extend(
            [
                f"| mapped classes | {len(coverage.mapped_classes)} |",
                f"| unmapped classes | {len(coverage.unmapped_classes)} |",
                f"| mapped object properties | {len(coverage.mapped_object_properties)} |",
                f"| unmapped object properties | {len(coverage.unmapped_object_properties)} |",
                f"| explicitly listed blank mappings | {len(coverage.explicit_blank_terms)} |",
                f"| source terms absent from spreadsheet | {len(coverage.absent_terms)} |",
                f"| spreadsheet subjects not found in source ontologies | {len(coverage.spreadsheet_missing_subjects)} |",
            ]
        )

    lines.extend(
        [
            "",
            "## Generated-Versus-Current Summary",
            "",
            "| Item | Count |",
            "|---|---:|",
        ]
    )
    if comparison is None:
        lines.extend(
            [
                "| mappings present in both | n/a |",
                "| mappings only in generated candidate | n/a |",
                "| mappings only in current validated ontology | n/a |",
            ]
        )
    else:
        lines.extend(
            [
                f"| mappings present in both | {len(comparison.both)} |",
                f"| mappings only in generated candidate | {len(comparison.generated_only)} |",
                f"| mappings only in current validated ontology | {len(comparison.current_only)} |",
                f"| class-expression differences | {len(comparison.class_expression_differences)} |",
                f"| object-property mapping differences | {len(comparison.object_property_differences)} |",
                f"| property-chain differences | {len(comparison.property_chain_differences)} |",
                f"| current domain/range basis absent | {len(comparison.current_domain_range_absent)} |",
            ]
        )

    lines.extend(
        [
            "",
            "## Runtime",
            "",
            f"- Runtime seconds: {elapsed_seconds:.2f}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary_json(
    path: Path,
    *,
    workbook_path: Path,
    output_path: Path,
    workbook_sha256: str,
    generator_sha256: str,
    generation_timestamp: str,
    candidate_sha256: str,
    stats: WorkbookStats,
    hermit: HermitResult | None,
    coverage: CoverageResult | None,
    comparison: ComparisonResult | None,
    errors: list[str],
    elapsed_seconds: float,
) -> None:
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "workbook_path": str(workbook_path),
        "output_path": str(output_path),
        "workbook_sha256": workbook_sha256,
        "generator_sha256": generator_sha256,
        "generation_timestamp": generation_timestamp,
        "generated_candidate_sha256": candidate_sha256,
        "worksheets_read": stats.worksheets_read,
        "mapped_rows": stats.mapped_rows,
        "blank_mapping_rows": stats.blank_mapping_rows,
        "class_mapping_rows": stats.class_mapping_rows,
        "object_property_mapping_rows": stats.object_property_mapping_rows,
        "property_chain_rows": stats.property_chain_rows,
        "generated_ontology_triple_count": None if hermit is None else hermit.generated_triple_count,
        "candidate_closure_triple_count": None if hermit is None else hermit.closure_triple_count,
        "hermit_return_code": None if hermit is None else hermit.return_code,
        "hermit_result": "PASS" if hermit is not None and hermit.passed else "FAIL",
        "owl_nothing_count": None if hermit is None else hermit.owl_nothing_count,
        "named_unsat_count": None if hermit is None else len(hermit.unsat_classes),
        "named_unsat_set": [] if hermit is None else [str(value) for value in hermit.unsat_classes],
        "source_term_coverage": None
        if coverage is None
        else {
            "query_source_count": coverage.query_source_count,
            "query_unmapped_count": coverage.query_unmapped_count,
            "mapped_classes": len(coverage.mapped_classes),
            "unmapped_classes": len(coverage.unmapped_classes),
            "mapped_object_properties": len(coverage.mapped_object_properties),
            "unmapped_object_properties": len(coverage.unmapped_object_properties),
            "explicitly_listed_blank_mappings": len(coverage.explicit_blank_terms),
            "source_terms_absent_from_spreadsheet": len(coverage.absent_terms),
            "spreadsheet_subjects_not_found": len(coverage.spreadsheet_missing_subjects),
        },
        "generated_vs_current": None
        if comparison is None
        else {
            "mappings_present_in_both": len(comparison.both),
            "mappings_only_in_generated": len(comparison.generated_only),
            "mappings_only_in_current": len(comparison.current_only),
            "class_expression_differences": len(comparison.class_expression_differences),
            "object_property_differences": len(comparison.object_property_differences),
            "property_chain_differences": len(comparison.property_chain_differences),
        },
        "errors": errors,
        "runtime_seconds": round(elapsed_seconds, 3),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="COMS workbook input path.")
    parser.add_argument("--output", required=True, help="Generated TTL output path.")
    parser.add_argument("--report", required=True, help="Generation validation report path.")
    parser.add_argument(
        "--coverage-report",
        default="reports/coms-source-term-coverage.md",
        help="Source-term coverage report path.",
    )
    parser.add_argument(
        "--diff-report",
        default="reports/coms-generated-vs-current-mapping-diff.md",
        help="Generated-vs-current mapping diff report path.",
    )
    parser.add_argument(
        "--tmp-dir",
        default="/tmp/ssn-to-bfo-coms-generation",
        help="Temporary directory for candidate closure validation.",
    )
    parser.add_argument(
        "--report-workbook-path",
        help="Workbook path displayed in reports. Defaults to the actual --input path.",
    )
    parser.add_argument(
        "--report-output-path",
        help="Generated ontology path displayed in reports. Defaults to the actual --output path.",
    )
    parser.add_argument(
        "--summary-json",
        help="Optional machine-readable generation summary path.",
    )
    args = parser.parse_args(argv)

    started = time.perf_counter()
    input_path = REPO_ROOT / args.input if not Path(args.input).is_absolute() else Path(args.input)
    output_path = REPO_ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)
    report_path = REPO_ROOT / args.report if not Path(args.report).is_absolute() else Path(args.report)
    coverage_report_path = REPO_ROOT / args.coverage_report if not Path(args.coverage_report).is_absolute() else Path(args.coverage_report)
    diff_report_path = REPO_ROOT / args.diff_report if not Path(args.diff_report).is_absolute() else Path(args.diff_report)
    report_workbook_path = Path(args.report_workbook_path) if args.report_workbook_path else input_path
    report_output_path = Path(args.report_output_path) if args.report_output_path else output_path
    summary_json_path = None
    if args.summary_json:
        summary_json_path = REPO_ROOT / args.summary_json if not Path(args.summary_json).is_absolute() else Path(args.summary_json)
    generation_timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    workbook_sha256 = sha256_file(input_path) if input_path.is_file() else "unavailable"
    generator_sha256 = sha256_file(Path(__file__).resolve())
    candidate_sha256 = "unavailable"

    stats = WorkbookStats()
    resolver = Resolver()
    errors: list[str] = []
    hermit: HermitResult | None = None
    coverage: CoverageResult | None = None
    comparison: ComparisonResult | None = None
    normalized_rows: list[tuple[str, str, str, str, str]] = []

    try:
        rows, stats = read_workbook(input_path)
        processed = validate_and_process_rows(rows, resolver, stats)
        graph = generate_ontology(processed, output_path)
        normalized_rows = normalized_mapping_rows(processed, graph)
        coverage = build_coverage(processed, [], coverage_report_path)
        graph.parse(output_path, format="turtle")
        hermit = run_candidate_hermit(output_path, Path(args.tmp_dir))
        comparison = compare_generated_to_current(output_path, diff_report_path, processed)
        if not hermit.passed:
            errors.append("candidate full local closure is not HermiT-clean")
    except GenerationError as exc:
        errors.append(str(exc))
    except Exception as exc:  # pragma: no cover - top-level reporting guard
        errors.append(f"unexpected generation failure: {type(exc).__name__}: {exc}")

    elapsed = time.perf_counter() - started
    if output_path.is_file():
        candidate_sha256 = sha256_file(output_path)
    write_generation_report(
        report_path,
        workbook_path=report_workbook_path,
        stats=stats,
        resolver=resolver,
        errors=errors,
        output_path=report_output_path,
        hermit=hermit,
        coverage=coverage,
        comparison=comparison,
        normalized_rows=normalized_rows,
        elapsed_seconds=elapsed,
        workbook_sha256=workbook_sha256,
        generator_sha256=generator_sha256,
        generation_timestamp=generation_timestamp,
        candidate_sha256=candidate_sha256,
    )
    if summary_json_path is not None:
        write_summary_json(
            summary_json_path,
            workbook_path=report_workbook_path,
            output_path=report_output_path,
            workbook_sha256=workbook_sha256,
            generator_sha256=generator_sha256,
            generation_timestamp=generation_timestamp,
            candidate_sha256=candidate_sha256,
            stats=stats,
            hermit=hermit,
            coverage=coverage,
            comparison=comparison,
            errors=errors,
            elapsed_seconds=elapsed,
        )

    print(f"Wrote {report_path}")
    if output_path.exists():
        print(f"Wrote {output_path}")
    if coverage_report_path.exists():
        print(f"Wrote {coverage_report_path}")
    if diff_report_path.exists():
        print(f"Wrote {diff_report_path}")
    print(f"Worksheets read: {', '.join(stats.worksheets_read) or 'none'}")
    print(f"Mapped rows: {stats.mapped_rows}")
    print(f"Blank mapping rows: {stats.blank_mapping_rows}")
    print(f"Class mapping rows: {stats.class_mapping_rows}")
    print(f"Object-property mapping rows: {stats.object_property_mapping_rows}")
    print(f"Property-chain rows: {stats.property_chain_rows}")
    if hermit is not None:
        print(f"Generated triple count: {hermit.generated_triple_count}")
        print(f"Candidate closure triple count: {hermit.closure_triple_count}")
        print(f"HermiT return code: {hermit.return_code}")
        print(f"owl:Nothing count: {hermit.owl_nothing_count}")
        print(f"Named unsat count: {len(hermit.unsat_classes)}")
        print(f"HermiT summary: {'PASS' if hermit.passed else 'FAIL'}")
    if coverage is not None:
        print(f"Mapped classes: {len(coverage.mapped_classes)}")
        print(f"Unmapped classes: {len(coverage.unmapped_classes)}")
        print(f"Mapped object properties: {len(coverage.mapped_object_properties)}")
        print(f"Unmapped object properties: {len(coverage.unmapped_object_properties)}")
    if comparison is not None:
        print(f"Mappings present in both: {len(comparison.both)}")
        print(f"Generated-only mappings: {len(comparison.generated_only)}")
        print(f"Current-only mappings: {len(comparison.current_only)}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Summary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
