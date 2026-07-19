# MadeObservation / MadeBySensor Agent Pair Full-Closure Analysis

## Scope

This report is a focused, report-only analysis of the SOSA inverse-property pair:

```text
sosa:madeObservation / sosa:madeBySensor
```

It follows the recommendation from `reports/sosa-inverse-property-pairs-full-closure-analysis.md`, which classified this pair as medium risk because it is the closest active structural analog to the mitigated `madeActuation` / `madeByActuator` actuation-agent pair.

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

`imports/sosa.ttl` asserts the inverse relation on the `madeBySensor` side:

```ttl
sosa:madeBySensor owl:inverseOf sosa:madeObservation .
```

It records source-level domain/range notes using `schema:domainIncludes` and `schema:rangeIncludes`:

| Property | SOSA source note |
|---|---|
| `sosa:madeObservation` | Sensor -> Observation |
| `sosa:madeBySensor` | Observation -> Sensor |

The materialized SOSA source file does not assert these notes as global `rdfs:domain` / `rdfs:range` axioms. Active logical source-level domain/range operationalization comes from `SSN2BFO.ttl`.

### SSN Source Restrictions

`imports/ssn.ttl` contains source restrictions that connect the pair to `sosa:Sensor` and `sosa:Observation`:

| Source class | Restriction pattern |
|---|---|
| `sosa:Sensor` | `sosa:madeObservation only sosa:Observation` |
| `sosa:Observation` | `sosa:madeBySensor only sosa:Sensor` |
| `sosa:Observation` | `sosa:madeBySensor cardinality 1` |

These restrictions are active in the full local SOSA closure baseline.

### Active Mapping Context

`SSN2BFO.ttl` currently contains:

```ttl
sosa:madeBySensor rdfs:domain sosa:Observation ;
  rdfs:range sosa:Sensor ;
  rdfs:subPropertyOf cco:ont00001833 .

sosa:madeObservation rdfs:domain sosa:Sensor ;
  rdfs:range sosa:Observation ;
  rdfs:subPropertyOf cco:ont00001787 .
```

The CCO target properties are an inverse agent pair:

```ttl
cco:ont00001787 owl:inverseOf cco:ont00001833 .
cco:ont00001787 rdfs:subPropertyOf bfo:BFO_0000056 .
cco:ont00001833 rdfs:subPropertyOf bfo:BFO_0000057 .
```

Local labels:

| CCO/BFO term | Local label / role |
|---|---|
| `cco:ont00001787` | `agent in` |
| `cco:ont00001833` | `has agent` |
| `bfo:BFO_0000056` | participates-in parent path |
| `bfo:BFO_0000057` | has-participant parent path |

### Workbook Context

The corresponding workbook rows are in `Common OPs`:

| Row | Source term | Active OWL cell summary | Rationale summary |
|---:|---|---|---|
| 30 | `sosa:madeBySensor` | domain `sosa:Observation`; range `sosa:Sensor`; subproperty of `cco:has_agent` | source-level domain/range operationalization; existing CCO has-agent mapping unchanged |
| 31 | `sosa:madeObservation` | domain `sosa:Sensor`; range `sosa:Observation`; inverse note; subproperty of `cco:ont00001787` | source-level domain/range operationalization; inverse and CCO agent-in mapping notes unchanged |

### Comparison With Actuation Pair

Similarity to the mitigated actuation pair:

- SOSA materializes an inverse relation between the two properties.
- Each side has source domain/range support.
- Source restrictions connect the source classes through the paired properties.
- The active target pattern is the CCO `agent_in` / `has_agent` inverse pair.

Important difference from the actuation pair:

- The actuation-side CCO agent mappings are currently deferred because re-adding both reproduces the full-closure `sosa:Actuation` / `sosa:Actuator` / `ssn-system:ActuationRange` failure.
- The observation/sensor CCO agent mappings are currently active and the full local SOSA closure baseline is HermiT-clean.
- No systems-side analog of `ssn-system:ActuationRange` is implicated by this observation/sensor pair in the current graph.

## Focused HermiT Variants

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-madeObservation-madeBySensor-agent-pair-full-closure-analysis
```

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| V0 | Current full closure baseline | `/tmp/ssn-to-bfo-madeObservation-madeBySensor-agent-pair-full-closure-analysis/V0.ttl` | 15769 | 0 | yes | 0 | 0 | clean |
| V1 | Remove only `sosa:madeObservation rdfs:subPropertyOf cco:ont00001787` | `/tmp/ssn-to-bfo-madeObservation-madeBySensor-agent-pair-full-closure-analysis/V1.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V2 | Remove only `sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833` | `/tmp/ssn-to-bfo-madeObservation-madeBySensor-agent-pair-full-closure-analysis/V2.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V3 | Remove both direct CCO agent mappings for the pair | `/tmp/ssn-to-bfo-madeObservation-madeBySensor-agent-pair-full-closure-analysis/V3.ttl` | 15767 | 0 | yes | 0 | 0 | clean |
| V4 | Add missing symmetric source-level domain/range axiom | skipped | n/a | n/a | n/a | n/a | n/a | No missing symmetric source-level domain/range axiom was identified. Both sides already have active source-level domain/range in `SSN2BFO.ttl`. |
| V5 | Test workbook-proposed missing CCO/BFO mapping | skipped | n/a | n/a | n/a | n/a | n/a | Both sides are already mapped to the workbook-proposed CCO/BFO target properties. |
| V6 | Remove the materialized SOSA inverse axiom `sosa:madeBySensor owl:inverseOf sosa:madeObservation` | `/tmp/ssn-to-bfo-madeObservation-madeBySensor-agent-pair-full-closure-analysis/V6.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V7 | Remove source restrictions involving `sosa:madeObservation` / `sosa:madeBySensor` | `/tmp/ssn-to-bfo-madeObservation-madeBySensor-agent-pair-full-closure-analysis/V7.ttl` | 15757 | 0 | yes | 0 | 0 | clean |

V7 removed three source restrictions:

- `sosa:Observation rdfs:subClassOf [ owl:onProperty sosa:madeBySensor ; owl:allValuesFrom sosa:Sensor ]`
- `sosa:Observation rdfs:subClassOf [ owl:onProperty sosa:madeBySensor ; owl:cardinality 1 ]`
- `sosa:Sensor rdfs:subClassOf [ owl:onProperty sosa:madeObservation ; owl:allValuesFrom sosa:Observation ]`

All focused variants were HermiT-clean.

## Inverse Reconstruction Check

The pair has the structural ingredients for inverse-side coupling:

```text
sosa:madeBySensor inverseOf sosa:madeObservation
cco:agent_in inverseOf cco:has_agent
```

So a one-sided mapping should be treated as coupled modeling context, even if only one direct subproperty assertion is present.

As a practical reasoned-output check, the V1/V2 reasoned graphs were inspected for the omitted direct subproperty triple:

| Variant | Removed direct mapping | Omitted direct subproperty materialized in reasoned output? |
|---|---|---|
| V1 | `sosa:madeObservation -> cco:agent_in` | no |
| V2 | `sosa:madeBySensor -> cco:has_agent` | no |

This materialization check is not a complete OWL entailment proof. It does show that the tested reasoned outputs did not expose a simple materialized one-side reconstruction, and none of the one-sided removal variants revealed a HermiT problem.

## Interpretation

The current active `madeObservation` / `madeBySensor` pair is HermiT-clean under the full local SOSA closure.

The pair is structurally analogous to the mitigated actuation pair because it combines:

- a materialized SOSA inverse axiom;
- source restrictions on the paired source classes;
- source-level domain/range operationalization; and
- paired CCO `agent_in` / `has_agent` target mappings.

However, the current evidence does not show that the observation/sensor pair is unsafe:

- the baseline full closure is clean;
- removing either direct CCO mapping is clean;
- removing both direct CCO mappings is clean;
- removing the materialized SOSA inverse is clean;
- removing the source restrictions is clean;
- no new unsatisfiable class appeared in any focused variant.

The best explanation for the difference from the actuation pair is that the actuation failure depended on additional actuation-specific mapped context, especially the `sosa:Actuation` / `sosa:Actuator` / `ssn-system:ActuationRange` cluster. The observation/sensor pair does not currently produce an analogous conflict in the merged full-SOSA closure profile.

This report should therefore be read as a focused safety/risk note, not as evidence that the CCO agent mapping pattern is universally safe. Future changes to `sosa:Observation`, `sosa:Sensor`, `sosa:madeObservation`, `sosa:madeBySensor`, or the CCO agent target context should still be tested under the full local SOSA closure HermiT check.

## Recommendation

Recommend exactly one next step:

```text
No mapping change for sosa:madeObservation / sosa:madeBySensor.
```

Keep the current mappings active and guarded by the full local SOSA closure HermiT validation check. This pair should remain documented as medium-risk because of its structural similarity to the mitigated actuation pair, but this focused analysis does not justify a mapping-change branch or an immediate follow-up branch for this pair.

## Validation

Validation commands:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/madeObservation-madeBySensor-agent-pair-full-closure-analysis.md

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
