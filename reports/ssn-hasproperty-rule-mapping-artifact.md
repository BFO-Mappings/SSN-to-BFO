# `ssn:hasProperty` Conditional Rule Mapping Artifact

## Purpose

This report documents `rules/ssn-hasproperty-conditional-mapping.rq`, a SPARQL CONSTRUCT artifact for the intended conditional mapping of `ssn:hasProperty`.

The artifact keeps the conditional mapping outside `SSN2BFO.ttl`. It is intended for rule/query-based materialization in a graph that already has suitable explicit or precomputed inferred typing and, when narrower predicates should be consumed, explicit or precomputed `rdfs:subPropertyOf` hierarchy triples.

## Verified BFO Identifiers

The rule uses BFO identifiers verified locally in `imports/cco.ttl`:

| CURIE | Local label | Use in rule |
| --- | --- | --- |
| `bfo:BFO_0000004` | independent continuant | Continuant-side subject type. |
| `bfo:BFO_0000020` | specifically dependent continuant | Continuant-side object type. |
| `bfo:BFO_0000003` | occurrent | Occurrent-side subject type. |
| `bfo:BFO_0000144` | Process Profile | Occurrent-side object type. |
| `bfo:BFO_0000196` | bearer of | Constructed relation for the independent-continuant/specifically-dependent-continuant case. |
| `bfo:BFO_0000117` | has occurrent part | Constructed relation for the occurrent/process-profile case. |

The independent continuant identifier is `bfo:BFO_0000004`, not the broader `bfo:BFO_0000002` continuant class.

## Rule Semantics

The artifact encodes two conditional branches. In both branches, the relation used in the source assertion may be direct `ssn:hasProperty` or a predicate explicitly classified under `ssn:hasProperty` with `rdfs:subPropertyOf`.

1. If `?entity ?hasPropertyRelation ?property`, `?hasPropertyRelation rdfs:subPropertyOf* ssn:hasProperty`, `?entity` is typed as or classified under independent continuant, and `?property` is typed as or classified under specifically dependent continuant, construct:

   ```turtle
   ?entity bfo:BFO_0000196 ?property .
   ```

2. If `?process ?hasPropertyRelation ?profile`, `?hasPropertyRelation rdfs:subPropertyOf* ssn:hasProperty`, `?process` is typed as or classified under occurrent, and `?profile` is typed as or classified under process profile, construct:

   ```turtle
   ?process bfo:BFO_0000117 ?profile .
   ```

## Difference From An Active OWL Mapping

This is not an active OWL mapping in `SSN2BFO.ttl`.

Recent local modeling reports showed that these active OWL mappings are not ELK-clean:

```turtle
ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000196 .
ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000117 .
```

The SPARQL artifact avoids a global `rdfs:subPropertyOf` assertion from `ssn:hasProperty` to either BFO relation. Instead, it materializes BFO relations only when the source predicate is `ssn:hasProperty` or an explicit/precomputed subproperty of it, and the subject/object typing matches one of the two intended cases. That keeps the conditional intent explicit and avoids forcing all uses of `ssn:hasProperty`, including inherited SSN Systems subproperties, under one or both BFO relations.

## Assumptions

The query assumes the input graph has suitable explicit or precomputed inferred classification:

- source assertions use either direct `ssn:hasProperty` or predicates connected to `ssn:hasProperty` by explicit or precomputed `rdfs:subPropertyOf` triples;
- instances that should match the first branch are typed directly as `bfo:BFO_0000004`, or typed with a class connected to `bfo:BFO_0000004` by explicit `rdfs:subClassOf` triples;
- property instances that should match the first branch are typed directly as `bfo:BFO_0000020`, or under it through explicit `rdfs:subClassOf`;
- instances that should match the second branch are typed directly as `bfo:BFO_0000003`, or under it through explicit `rdfs:subClassOf`;
- profile instances that should match the second branch are typed directly as `bfo:BFO_0000144`, or under it through explicit `rdfs:subClassOf`.

The query uses `?hasPropertyRelation rdfs:subPropertyOf* ssn:hasProperty`, which matches direct `ssn:hasProperty` assertions because `*` includes the zero-length path. It also matches narrower SSN Systems subproperties only when the graph contains the relevant explicit or precomputed `rdfs:subPropertyOf` hierarchy.

The query also uses `rdf:type/rdfs:subClassOf*` paths. These paths are useful over explicit or materialized type/classification triples, but they do not provide complete OWL DL entailment.

## Limitations

SPARQL CONSTRUCT is a materialization/query artifact, not an ontology axiom.

Important limitations:

- The rule does not prove that an individual is an independent continuant, specifically dependent continuant, occurrent, or process profile. It only consumes available typing/classification.
- The subproperty matching depends on explicit or precomputed `rdfs:subPropertyOf` triples. If the hierarchy is absent, assertions using narrower predicates such as SSN Systems subproperties will not match.
- SPARQL property paths over `rdfs:subClassOf*` do not replace OWL reasoning over equivalence, restrictions, disjunctions, property characteristics, or imported ontology semantics.
- The query does not have SWRL-style rule semantics inside an OWL reasoner.
- Materialized triples should be treated as derived output, with provenance and validation appropriate to the graph in which the rule was run.
- The query may produce no output on data that has not been typed or preclassified enough for the branch conditions to match.

## COMS Annotation Path

Later, once the `coms:` vocabulary is ready in this repository, `SSN2BFO.ttl` or a companion mapping metadata file could reference this rule artifact with COMS annotations.

For example, COMS metadata could identify:

- the source relation: `ssn:hasProperty`;
- the rule artifact path: `rules/ssn-hasproperty-conditional-mapping.rq`;
- the generated target relations: `bfo:BFO_0000196` and `bfo:BFO_0000117`;
- the required classification assumptions;
- the rule status, provenance, and review decision.

This report does not define COMS terms and does not add COMS annotations. The recommendation is to wait until COMS is ready before annotating `SSN2BFO.ttl`.

## Validation Performed

Validation run locally:

```text
SPARQL parse with rdflib prepareQuery: passed
python -m py_compile tools/compare_mappings.py: passed
git diff --check: passed
```

The final requested file existence and git status checks were run after creating the artifacts.

## Recommendation

Keep `rules/ssn-hasproperty-conditional-mapping.rq` as a separate mapping artifact.

Do not add active OWL axioms for this mapping to `SSN2BFO.ttl` now. Do not annotate `SSN2BFO.ttl` until the COMS vocabulary and annotation pattern are ready.

This rule artifact is useful because it preserves the intended conditional semantics without reintroducing the known ELK-unsafe direct subproperty mappings.
