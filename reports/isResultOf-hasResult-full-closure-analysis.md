# IsResultOf / HasResult Full-Closure Analysis

## Scope

This report is a focused, report-only analysis of the SOSA inverse-property pair:

```text
sosa:isResultOf / sosa:hasResult
```

It follows `reports/sosa-inverse-property-pairs-full-closure-analysis.md`, which classified this pair as medium risk. The pair is worth checking because it touches result/output modeling, inverse-property propagation, and the previously rejected `ssn:hasOutput -> cco:has_output` mapping.

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

## Full-Closure Method

All HermiT runs use the current full local SOSA closure graph built from:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

After loading, each graph removes:

```ttl
owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty .
sosa:hasSample rdf:type owl:InverseFunctionalProperty .
```

HermiT command pattern:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

## Baseline Confirmation

Command:

```bash
python tools/test_full_sosa_closure_hermit.py --output /tmp/full-sosa-current.md
```

Result:

| Item | Result |
|---|---:|
| triple count | 15769 |
| HermiT return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |

The current active full local SOSA closure is HermiT-clean.

## Pair Inventory

### SOSA Source Context

`imports/sosa.ttl` asserts the inverse relation on the `hasResult` side:

```ttl
sosa:hasResult owl:inverseOf sosa:isResultOf .
```

It records source-level domain/range notes using `schema:domainIncludes` and `schema:rangeIncludes`:

| Property | SOSA source note |
|---|---|
| `sosa:hasResult` | Actuation / Observation / Sampling -> Result / Sample |
| `sosa:isResultOf` | Result / Sample -> Actuation / Observation / Sampling |

The materialized SOSA source file does not assert these notes as global `rdfs:domain` / `rdfs:range` axioms. Active direct CCO/BFO mappings come from `SSN2BFO.ttl`.

### SSN Source Restrictions

`imports/ssn.ttl` contains source restrictions that connect `hasResult` and `isResultOf` to result-producing events:

| Source class | Restriction pattern |
|---|---|
| `sosa:Actuation` | `sosa:hasResult only sosa:Result`; `sosa:hasResult minCardinality 1` |
| `sosa:Observation` | `sosa:hasResult only sosa:Result`; `sosa:hasResult minCardinality 1` |
| `sosa:Sampling` | `sosa:hasResult only sosa:Sample`; `sosa:hasResult minCardinality 1` |
| `sosa:Result` | `sosa:isResultOf only (Actuation or Observation or Sampling)` |
| `sosa:Sample` | `sosa:isResultOf only Sampling`; `sosa:isResultOf minCardinality 1` |

These restrictions are active in the full local SOSA closure baseline.

### Active Mapping Context

`SSN2BFO.ttl` currently contains:

```ttl
sosa:hasResult rdfs:subPropertyOf cco:ont00001986 .
sosa:isResultOf rdfs:subPropertyOf cco:ont00001816 .
```

The CCO target properties are an inverse output pair:

```ttl
cco:ont00001816 owl:inverseOf cco:ont00001986 .
cco:ont00001816 rdfs:subPropertyOf bfo:BFO_0000056 .
cco:ont00001986 rdfs:subPropertyOf bfo:BFO_0000057 .
```

Local labels and target constraints:

| CCO/BFO term | Local label / role |
|---|---|
| `cco:ont00001816` | `is output of`; domain `bfo:Continuant`; range `bfo:Process`; subproperty of `bfo:participates_in` |
| `cco:ont00001986` | `has output`; domain `bfo:Process`; range `bfo:Continuant`; subproperty of `bfo:has_participant` |
| `bfo:BFO_0000056` | participates-in parent path |
| `bfo:BFO_0000057` | has-participant parent path |

### Related Class Mappings

The active local mapping for `sosa:Result` is:

```text
sosa:Result equivalentTo
  (cco:InformationContentEntity or bfo:MaterialEntity)
  and (cco:is_output_of some (sosa:Actuation or sosa:Observation or sosa:Sampling))
```

The active local event mappings include:

| Class | Active local mapping shape |
|---|---|
| `sosa:Observation` | subclass of `cco:PlannedAct` with observation/measurement process-part structure |
| `sosa:Actuation` | equivalent to `cco:PlannedAct and (sosa:actsOnProperty some sosa:ActuatableProperty)` |
| `sosa:Sampling` | equivalent to `cco:PlannedAct and (cco:prescribed_by some sosa:Procedure) and (cco:has_output some sosa:Sample)` |

This context is why the pair deserves focused review: the property mappings, the `sosa:Result` class mapping, and the event mappings all use CCO output/process structure.

### Workbook Context

The corresponding workbook rows are in `Common OPs`:

| Row | Source term | Active OWL cell summary | Rationale summary |
|---:|---|---|---|
| 12 | `sosa:hasResult` | subproperty of `cco:has_output` | results are defined as outputs of observations, actuations, or samplings |
| 25 | `sosa:isResultOf` | inverse of `sosa:hasResult`; subproperty of `cco:ont00001816` | inverse of `sosa:hasResult`; see `sosa:hasResult` row |

Relevant rejected input/output row:

| Row | Source term | Current state |
|---:|---|---|
| 10 | `ssn:hasOutput` | source-level domain/range typing only; prior direct CCO mapping to `cco:has_output` remains removed/rejected |

### Comparison Cases

Similarity to the mitigated actuation agent pair:

- SOSA materializes an inverse relation between the two properties.
- Both sides map to inverse CCO/BFO target properties.
- Both target properties sit on BFO participant parent paths.
- The pair touches actuation context through `sosa:Actuation`.

Difference from the mitigated actuation agent pair:

- The target relations are output relations, not agent relations.
- The active mappings do not involve `sosa:Actuator` or the `ssn-system:ActuationRange` cluster.
- The current active pair is full-closure HermiT-clean.

Comparison to clean `madeObservation` / `madeBySensor`, `madeSampling` / `madeBySampler`, and `isActedOnBy` / `actsOnProperty`:

- Like those pairs, this pair is active and full-closure clean.
- Unlike the agent pairs, this pair maps to CCO output relations rather than agent relations.
- Unlike `actsOnProperty` / `isActedOnBy`, this pair has a documented nearby rejected mapping: `ssn:hasOutput -> cco:has_output`.

## Focused HermiT Variants

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis
```

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| V0 | Current full closure baseline | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V0.ttl` | 15769 | 0 | yes | 0 | 0 | clean |
| V1 | Remove only `sosa:hasResult rdfs:subPropertyOf cco:ont00001986` | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V1.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V2 | Remove only `sosa:isResultOf rdfs:subPropertyOf cco:ont00001816` | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V2.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V3 | Remove both active CCO/BFO mappings for the pair | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V3.ttl` | 15767 | 0 | yes | 0 | 0 | clean |
| V4 | Temporarily re-add documented/rejected `ssn:hasOutput rdfs:subPropertyOf cco:ont00001986` | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V4.ttl` | 15770 | 1 | no | n/a | 1 | `ssn:Output` |
| V5 | Add source-supported symmetric domain/range union axioms for `hasResult` / `isResultOf` | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V5.ttl` | 15787 | 0 | yes | 0 | 0 | clean |
| V6 | Remove materialized SOSA inverse axiom `sosa:hasResult owl:inverseOf sosa:isResultOf` | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V6.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V7 | Remove source class restrictions involving `sosa:isResultOf` / `sosa:hasResult` | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V7.ttl` | 15733 | 0 | yes | 0 | 0 | clean |
| V8 | Remove active `sosa:Result` class-expression mapping only | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V8.ttl` | 15745 | 0 | yes | 0 | 0 | clean |
| V9a | Remove active `sosa:Observation` class-expression mapping only | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V9a.ttl` | 15753 | 0 | yes | 0 | 0 | clean |
| V9b | Remove active `sosa:Actuation` class-expression mapping only | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V9b.ttl` | 15759 | 0 | yes | 0 | 0 | clean |
| V9c | Remove active `sosa:Sampling` class-expression mapping only | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V9c.ttl` | 15754 | 0 | yes | 0 | 0 | clean |
| V9d | Remove active `Observation` / `Actuation` / `Sampling` class-expression mappings together | `/tmp/ssn-to-bfo-isResultOf-hasResult-full-closure-analysis/V9d.ttl` | 15728 | 0 | yes | 0 | 0 | clean |

V5 added four temporary source-supported union axioms:

- `sosa:hasResult rdfs:domain (sosa:Actuation or sosa:Observation or sosa:Sampling)`
- `sosa:hasResult rdfs:range (sosa:Result or sosa:Sample)`
- `sosa:isResultOf rdfs:domain (sosa:Result or sosa:Sample)`
- `sosa:isResultOf rdfs:range (sosa:Actuation or sosa:Observation or sosa:Sampling)`

V7 removed direct source restrictions involving the pair from `sosa:Actuation`, `sosa:Observation`, `sosa:Sampling`, `sosa:Result`, and `sosa:Sample`.

All focused variants were HermiT-clean except V4. V4 intentionally reintroduced a previously rejected mapping and reproduced `ssn:Output` unsatisfiability.

## Inverse Reconstruction Check

The pair has the structural ingredients for inverse-side coupling:

```text
sosa:hasResult inverseOf sosa:isResultOf
cco:has_output inverseOf cco:is_output_of
```

So a one-sided mapping should be treated as coupled modeling context, even if only one direct subproperty assertion is present.

As a practical reasoned-output check, the V1/V2 reasoned graphs were inspected for the omitted direct subproperty triple:

| Variant | Removed direct mapping | Omitted direct subproperty materialized in reasoned output? |
|---|---|---|
| V1 | `sosa:hasResult -> cco:has_output` | no |
| V2 | `sosa:isResultOf -> cco:is_output_of` | no |

This materialization check is not a complete OWL entailment proof. It does show that the tested reasoned outputs did not expose a simple materialized one-side reconstruction, and none of the one-sided removal variants revealed a HermiT problem.

## Interpretation

The current active `isResultOf` / `hasResult` pair is HermiT-clean under the full local SOSA closure.

The pair is structurally analogous to other inverse-property pairs because it combines:

- a materialized SOSA inverse axiom;
- source restrictions on result-producing event classes and result classes;
- paired CCO `has_output` / `is_output_of` target mappings; and
- BFO participant parent paths.

It is not strongly analogous to the mitigated actuation agent failure:

- the target semantics are output relations rather than agent relations;
- the tested pair does not involve `sosa:Actuator` or `ssn-system:ActuationRange`;
- removing either side, both sides, the inverse axiom, the source restrictions, `sosa:Result`, or the result-producing event mappings did not reveal a HermiT issue.

Result/output modeling does add a nearby risk: V4 confirms that the old direct `ssn:hasOutput -> cco:has_output` mapping remains unsafe under the current full closure, reintroducing `ssn:Output`. This is consistent with the prior Input/Output diagnostics and does not implicate the active `sosa:hasResult` mapping itself.

The source-supported union domain/range test in V5 was HermiT-clean. That is only a temporary diagnostic result; this report does not recommend adding those axioms because the branch is focused on inverse-pair safety, not source-domain/range expansion.

## Recommendation

Recommend exactly one next step:

```text
No mapping change for sosa:isResultOf / sosa:hasResult.
```

Keep the current mappings active and guarded by the full local SOSA closure HermiT validation check. Keep the previously rejected `ssn:hasOutput -> cco:has_output` mapping inactive. This pair should remain documented as medium-risk because it is an inverse output pair near prior input/output failures, but this focused analysis does not justify a mapping-change branch or an immediate follow-up branch for this pair.

## Validation

Validation commands:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/isResultOf-hasResult-full-closure-analysis.md

git diff --check
```

Final result:

- `workflow_check.py --mode report-only`: PASS
- validation suite: PASS
- mapping audit: PASS with the two expected `sosa:Sensor` version-alignment issues only
- ELK direct property expectations: 75
- full local SOSA closure HermiT check: PASS (`15769` triples, return code `0`, `owl:Nothing` count `0`, unsat count `0`)
- Python compile check: PASS
- `git diff --check`: PASS
