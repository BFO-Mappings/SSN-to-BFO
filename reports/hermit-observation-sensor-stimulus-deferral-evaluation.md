# HermiT Observation / Sensor / Stimulus Deferral Evaluation

## Scope

This is a diagnostic-only candidate-deferral evaluation for the final remaining core SOSA/SSN HermiT cluster:

```text
sosa:Observation
sosa:Sensor
ssn:Stimulus
```

No ontology mappings, spreadsheets, imports, source examples, generated artifacts, release artifacts, or existing reports were edited. Temporary HermiT files were written only under:

```text
/tmp/ssn-to-bfo-hermit-observation-sensor-stimulus-deferral-evaluation
```

This report compares candidate temporary deferrals in temporary graphs only. It does not claim that any mapping is semantically wrong.

## Prior Context

The preceding report, `reports/hermit-observation-sensor-stimulus-evaluation.md`, found that the current full M2 HermiT baseline has exactly:

```text
sosa:Observation
sosa:Sensor
ssn:Stimulus
```

It also found that this trio behaves as a mixed interaction cluster. Several one-subject removals cleared the trio in temporary graphs, especially:

- `sosa:Sensor`
- `sosa:hosts`
- `sosa:madeBySensor`
- `sosa:observedProperty`

The goal here is to compare those candidate deferrals and identify the best next temporary fix-evaluation branch, while leaving repo ontology and spreadsheet files untouched.

## Method

For every full-graph HermiT variant, a temporary M2 graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Then these cleanup steps were applied:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

Every HermiT run used this command shape:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

ROBOT version:

```text
ROBOT version 1.9.7
```

Clean variants produced reasoned output and had `owl:Nothing` count 0. Unsatisfiable variants returned nonzero and did not produce reasoned output. The sample simplicity blocker did not reappear in any reported variant.

## Current Baseline

Variant A reproduced the current full M2 baseline:

| Variant | Triples | Return code | Reasoned output | Unsat count | Unsat set |
| --- | ---: | ---: | --- | ---: | --- |
| A full M2 | 15475 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| B source/import-only | 14485 | 0 | yes | 0 | clean |

The source/import-only control was HermiT-clean, so the trio is not present without `SSN2BFO.ttl`.

## Candidate Mapping Inventory

The candidate inventory was extracted from `SSN2BFO.ttl` before running deferral variants.

| Source subject | Mapping classification | Active logical content | Candidate impact if deferred |
| --- | --- | --- | --- |
| `sosa:Sensor` | class/restriction-style mapping | `rdf:type owl:Class`; `rdfs:subClassOf` blank-node expression | removes one restriction/expression mapping; clears trio |
| `sosa:Observation` | class/restriction-style mapping | `rdf:type owl:Class`; `rdfs:subClassOf` blank-node expression | removes one restriction/expression mapping; does not clear trio |
| `sosa:hosts` | property-chain mapping | `rdf:type owl:ObjectProperty`; `owl:propertyChainAxiom` blank-node list | removes one property-chain mapping; clears trio |
| `sosa:isHostedBy` | property-chain mapping | `rdf:type owl:ObjectProperty`; `owl:propertyChainAxiom` blank-node list | removes one property-chain mapping; does not clear trio |
| `sosa:madeBySensor` | direct property mapping | `rdfs:subPropertyOf cco:ont00001833` | removes one direct property mapping; clears trio |
| `sosa:madeObservation` | direct property mapping | `rdfs:subPropertyOf cco:ont00001787` | removes one direct property mapping; does not clear trio |
| `sosa:observedProperty` | direct property mapping | `rdfs:subPropertyOf cco:ont00001921` | removes one direct property mapping; clears trio |
| `sosa:observes` | direct property mapping | `rdfs:subPropertyOf ssn:forProperty` | removes one direct property mapping; does not clear trio |
| `ssn:detects` | direct property mapping | `rdfs:subPropertyOf cco:ont00001886` | removes one direct property mapping; does not clear trio |
| `ssn:Stimulus` | class/restriction-style mapping | `rdf:type owl:Class`; `owl:equivalentClass` blank-node expression | removes one restriction/expression mapping; clears `ssn:Stimulus` only |

Relevant local target labels from `imports/cco.ttl`:

| Identifier | Local label |
| --- | --- |
| `bfo:BFO_0000017` | realizable entity |
| `bfo:BFO_0000040` | material entity |
| `bfo:BFO_0000054` | has realization |
| `bfo:BFO_0000055` | realizes |
| `bfo:BFO_0000056` | participates in |
| `bfo:BFO_0000057` | has participant |
| `bfo:BFO_0000196` | bearer of |
| `bfo:BFO_0000197` | inheres in |
| `cco:ont00000037` | Act of Observation |
| `cco:ont00000228` | Planned Act |
| `cco:ont00000345` | Act of Measuring |
| `cco:ont00000978` | Cause |
| `cco:ont00001777` | has process part |
| `cco:ont00001787` | agent in |
| `cco:ont00001803` | is cause of |
| `cco:ont00001833` | has agent |
| `cco:ont00001886` | is affected by |
| `cco:ont00001921` | has input |

## Variant Summary Table

| Group | Variant | Temporary edit | Triples | Unsat count | Result |
| --- | --- | --- | ---: | ---: | --- |
| A | `A_full_m2` | current full M2 graph | 15475 | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| B | `B_source_import_only` | source/import-only, no `SSN2BFO.ttl` | 14485 | 0 | clean |
| C | `C_remove_sosa_Sensor` | remove `sosa:Sensor` mapping block | 15450 | 0 | clean |
| C | `C_remove_sosa_Observation` | remove `sosa:Observation` mapping block | 15458 | 3 | unchanged |
| C | `C_remove_sosa_hosts` | remove `sosa:hosts` mapping block | 15467 | 0 | clean |
| C | `C_remove_sosa_isHostedBy` | remove `sosa:isHostedBy` mapping block | 15467 | 3 | unchanged |
| C | `C_remove_sosa_madeBySensor` | remove `sosa:madeBySensor` mapping block | 15474 | 0 | clean |
| C | `C_remove_sosa_madeObservation` | remove `sosa:madeObservation` mapping block | 15474 | 3 | unchanged |
| C | `C_remove_sosa_observedProperty` | remove `sosa:observedProperty` mapping block | 15474 | 0 | clean |
| C | `C_remove_sosa_observes` | remove `sosa:observes` mapping block | 15474 | 3 | unchanged |
| C | `C_remove_ssn_detects` | remove `ssn:detects` mapping block | 15474 | 3 | unchanged |
| C | `C_remove_ssn_Stimulus` | remove `ssn:Stimulus` mapping block | 15464 | 2 | leaves `sosa:Observation`, `sosa:Sensor` |
| D | `D1_hosts_isHostedBy` | remove `sosa:hosts` + `sosa:isHostedBy` | 15459 | 0 | clean |
| D | `D2_madeBySensor_madeObservation` | remove `sosa:madeBySensor` + `sosa:madeObservation` | 15473 | 0 | clean |
| D | `D3_observedProperty_observes` | remove `sosa:observedProperty` + `sosa:observes` | 15473 | 0 | clean |
| D | `D4_hosts_madeBySensor_observedProperty` | remove three individually clearing subjects | 15465 | 0 | clean |
| D | `D5_all_direct_property_sensor_obs_stimulus` | remove all direct/property-chain mapping subjects involving the trio | 15454 | 0 | clean |
| D | `D6_all_property_chains_sensor_obs` | remove all property-chain mappings involving Sensor/Observation | 15459 | 0 | clean |
| D | `D7_all_individually_clearing_subjects` | remove all one-at-a-time clearing subjects | 15440 | 0 | clean |
| D | `D8_Sensor_Observation` | remove `sosa:Sensor` + `sosa:Observation` | 15433 | 0 | clean |
| F | `F1_Sensor_type_only` | remove only `sosa:Sensor rdf:type owl:Class` | 15474 | 3 | unchanged |
| F | `F2_Sensor_subClass_expression_only` | remove `sosa:Sensor` subclass expression only | 15451 | 0 | clean |
| F | `F3_Sensor_bearer_realization_part` | remove approximate Sensor bearer/realization subpart | 15451 | 0 | clean |
| F | `F4_Sensor_agent_in_part` | remove approximate Sensor `cco:agent_in` subpart | 15451 | 0 | clean |
| F | `F5_hosts_type_only` | remove only `sosa:hosts rdf:type owl:ObjectProperty` | 15474 | 3 | unchanged |
| F | `F6_hosts_property_chain_only` | remove only `sosa:hosts owl:propertyChainAxiom` | 15468 | 0 | clean |
| F | `F7_isHostedBy_property_chain_only` | remove only `sosa:isHostedBy owl:propertyChainAxiom` | 15468 | 3 | unchanged |
| F | `F8_madeBySensor_assertion_only` | remove only `sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833` | 15474 | 0 | clean |
| F | `F9_observedProperty_assertion_only` | remove only `sosa:observedProperty rdfs:subPropertyOf cco:ont00001921` | 15474 | 0 | clean |
| F | `F10_Stimulus_type_only` | remove only `ssn:Stimulus rdf:type owl:Class` | 15474 | 3 | unchanged |
| F | `F11_Stimulus_equivalentClass_only` | remove only `ssn:Stimulus equivalentClass` expression | 15465 | 2 | leaves `sosa:Observation`, `sosa:Sensor` |
| G | `G1_source_plus_Sensor` | source/import-only + `sosa:Sensor` mapping block | 14510 | 0 | clean |
| G | `G2_source_plus_hosts` | source/import-only + `sosa:hosts` mapping block | 14493 | 0 | clean |
| G | `G3_source_plus_madeBySensor` | source/import-only + `sosa:madeBySensor` mapping block | 14486 | 0 | clean |
| G | `G4_source_plus_observedProperty` | source/import-only + `sosa:observedProperty` mapping block | 14486 | 0 | clean |
| G | `G5_source_plus_top_candidates` | source/import-only + all top individually clearing blocks | 14520 | 0 | clean |
| G | `G6_source_plus_top_candidates_System_PropertyContext` | top candidates + `ssn:System` and property context | 14563 | 0 | clean |
| G | `G7_source_plus_cluster_base` | source/import-only + sensor/observation cluster mapping base | 14556 | 0 | clean |
| G | `G8_source_plus_cluster_base_System_PropertyContext` | cluster base + `ssn:System` and property context | 14599 | 3 | reproduces trio |
| G | `G_core_except_sosa_Sensor` | all core SOSA/SSN mappings except `sosa:Sensor` | 14834 | 0 | clean |
| G | `G_core_except_sosa_hosts` | all core SOSA/SSN mappings except `sosa:hosts` | 14851 | 0 | clean |
| G | `G_core_except_sosa_madeBySensor` | all core SOSA/SSN mappings except `sosa:madeBySensor` | 14858 | 0 | clean |
| G | `G_core_except_sosa_observedProperty` | all core SOSA/SSN mappings except `sosa:observedProperty` | 14858 | 0 | clean |
| G | `G_core_except_all_top_candidates` | all core mappings except all top candidates | 14824 | 0 | clean |

## One-At-A-Time Candidate Results

The one-at-a-time clearing candidates were:

| Candidate | Mapping type | Scope | HermiT effect |
| --- | --- | --- | --- |
| `sosa:Sensor` | class/restriction-style mapping | broad, 25-triple class-expression block | clears trio |
| `sosa:hosts` | property-chain mapping | one property-chain mapping block | clears trio |
| `sosa:madeBySensor` | direct property mapping | one `rdfs:subPropertyOf` assertion | clears trio |
| `sosa:observedProperty` | direct property mapping | one `rdfs:subPropertyOf` assertion | clears trio |

The non-clearing one-at-a-time candidates were:

```text
sosa:Observation
sosa:isHostedBy
sosa:madeObservation
sosa:observes
ssn:detects
```

Removing `ssn:Stimulus` removed only `ssn:Stimulus`, leaving `sosa:Observation` and `sosa:Sensor`. This supports treating `ssn:Stimulus` as attached to the Observation/Sensor interaction rather than as the best first deferral candidate.

## Group Candidate Results

All interpretable groups that contained at least one one-at-a-time clearing candidate were HermiT-clean. The group checks did not identify a smaller group than the one-triple direct property candidates or the single `sosa:hosts` property-chain mapping.

Important group results:

- `sosa:hosts` + `sosa:isHostedBy` cleared the trio.
- `sosa:madeBySensor` + `sosa:madeObservation` cleared the trio.
- `sosa:observedProperty` + `sosa:observes` cleared the trio.
- all Sensor/Observation property-chain mappings cleared the trio.
- all Sensor/Observation direct property mappings cleared the trio.
- `sosa:Sensor` + `sosa:Observation` cleared the trio.

Because single candidates already clear the trio, broad group deferrals are not preferred as first fix-evaluation candidates.

## Minimality And Subpart Results

Subpart tests sharpened the one-at-a-time candidate results:

- `sosa:Sensor rdf:type owl:Class` alone was not responsible; removing only the `sosa:Sensor` subclass class-expression cleared the trio.
- The approximate Sensor bearer/realization subpart and approximate `cco:agent_in` subpart each cleared the trio in this temporary decomposition. This means the Sensor expression is high-impact, but the split is not fine enough to identify one safe replacement expression.
- `sosa:hosts rdf:type owl:ObjectProperty` was not responsible; removing only the `sosa:hosts owl:propertyChainAxiom` cleared the trio.
- Removing only `sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833` cleared the trio.
- Removing only `sosa:observedProperty rdfs:subPropertyOf cco:ont00001921` cleared the trio.
- `ssn:Stimulus rdf:type owl:Class` was not responsible; removing the equivalent-class expression cleared only `ssn:Stimulus`.

The narrowest tested clearing candidates are therefore the one-triple direct property mappings for `sosa:madeBySensor` and `sosa:observedProperty`. The narrowest property-chain clearing candidate is the `sosa:hosts` property-chain axiom.

## Reconstruction Results

Reconstruction variants show that no top candidate block is sufficient by itself:

- source/import-only + `sosa:Sensor` mapping block was clean;
- source/import-only + `sosa:hosts` mapping block was clean;
- source/import-only + `sosa:madeBySensor` mapping block was clean;
- source/import-only + `sosa:observedProperty` mapping block was clean;
- source/import-only + all top individually clearing blocks was clean;
- source/import-only + top candidates + `ssn:System` and property context was still clean.

The trio was reproduced only when the broader sensor/observation cluster mapping base was combined with `ssn:System` and property context:

```text
G8_source_plus_cluster_base_System_PropertyContext
```

That result suggests each clearing candidate is necessary in the current mixed graph but not sufficient alone. The dependency is mixed across source context, class-expression mappings, direct property mappings, and property-chain mappings.

The full-core exclusion checks also support candidate necessity:

- all core mappings except `sosa:Sensor` was clean;
- all core mappings except `sosa:hosts` was clean;
- all core mappings except `sosa:madeBySensor` was clean;
- all core mappings except `sosa:observedProperty` was clean.

## Expected Validation Impact

This branch did not edit repo files or regenerate canonical reports. If a later temporary fix-evaluation branch defers one of the clearing candidates, expected validation impact is:

| Candidate | Direct class count | Direct property count | Property-chain count | Restriction/expression count | Expected report updates |
| --- | ---: | ---: | ---: | ---: | --- |
| `sosa:Sensor` | 0 | 0 | 0 | -1 | `SSN2BFO.ttl`, spreadsheet row, mapping audit, ELK entailment report, evaluation report |
| `sosa:hosts` | 0 | 0 | -1 | 0 | `SSN2BFO.ttl`, spreadsheet row, mapping audit, ELK entailment report, evaluation report |
| `sosa:madeBySensor` | 0 | -1 | 0 | 0 | `SSN2BFO.ttl`, spreadsheet row, mapping audit, ELK entailment report, evaluation report |
| `sosa:observedProperty` | 0 | -1 | 0 | 0 | `SSN2BFO.ttl`, spreadsheet row, mapping audit, ELK entailment report, evaluation report |

The future spreadsheet update would need to clear only the active OWL mapping cell for the selected row and add rationale explaining that intended semantics are deferred for HermiT-safe OWL or rule/COMS treatment. The future ELK report should be regenerated because active direct/property-chain expectations would change.

## Candidate Recommendation Matrix

| Rank | Candidate | HermiT effect | Scope | Semantic and validation risk | Assessment |
| ---: | --- | --- | --- | --- | --- |
| 1 | `sosa:observedProperty rdfs:subPropertyOf cco:ont00001921` | clears trio | one direct property assertion | affects observed-property-to-input semantics and direct property expectations | Best first temporary fix-evaluation candidate because it is a one-triple reducer and uses an input-like target relation already adjacent to prior Input/Output HermiT work. Do not claim semantic invalidity. |
| 2 | `sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833` | clears trio | one direct property assertion | affects observation/sensor agent semantics and direct property expectations | Strong alternate one-triple candidate if the first candidate is not acceptable or does not survive full validation as a repo edit. |
| 3 | `sosa:hosts owl:propertyChainAxiom (...)` | clears trio | one property-chain mapping block | affects hosting chain expectations and property-chain validation coverage | Good candidate, but broader than the one-triple direct property candidates because it changes property-chain behavior. |
| 4 | `sosa:Sensor` class-expression mapping | clears trio | broad class/restriction-style expression | high semantic blast radius and class/restriction coverage impact | Too broad for first fix-evaluation unless narrower direct property and property-chain candidates fail. |
| 5 | `ssn:Stimulus` equivalent-class expression | partial only | class-expression mapping | removes only `ssn:Stimulus` from the trio | Not a good first candidate for clearing the full cluster. |

## Explanation Assessment

The trio is best understood as a mixed Observation/Sensor/Stimulus interaction rather than a single isolated source or target axiom.

The strongest clearing candidates are not sufficient by themselves in reconstruction tests. Instead, they appear to be necessary components of a broader interaction that also needs sensor/observation cluster mappings plus `ssn:System` and property context.

Evidence does not prove that `sosa:observedProperty`, `sosa:madeBySensor`, `sosa:hosts`, or `sosa:Sensor` is semantically wrong. It only shows that each can break the HermiT unsatisfiability cycle in temporary graphs.

The class-level `sosa:Sensor` candidate is effective but too broad for a first narrow fix-evaluation branch. The `sosa:hosts` property-chain candidate is effective and narrower than `sosa:Sensor`, but it affects property-chain behavior. The direct property candidates are the narrowest tested full-trio reducers.

## Recommendation

Do not make a final mapping change from this report alone.

Recommended next branch:

```text
review/evaluate-defer-sosa-observedProperty-mapping
```

Recommended temporary edit for that branch:

```ttl
sosa:observedProperty rdfs:subPropertyOf cco:ont00001921 .
```

That branch should temporarily defer only the `sosa:observedProperty` direct property mapping, update only the corresponding spreadsheet row, regenerate the mapping audit and ELK entailment report, and run the standard validation suite plus M2 HermiT before/after checks.

If that candidate is rejected during human review, the next narrow alternate should be:

```ttl
sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833 .
```

The already-fixed Input/Output and SSN Systems deferrals should remain separate from this final Observation/Sensor/Stimulus cluster.
