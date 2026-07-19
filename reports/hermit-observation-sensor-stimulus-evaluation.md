# HermiT Observation / Sensor / Stimulus Evaluation

## Scope

This is a diagnostic-only report for the final remaining core SOSA/SSN HermiT cluster:

```text
sosa:Observation
sosa:Sensor
ssn:Stimulus
```

No ontology mappings, spreadsheets, imports, source examples, generated artifacts, release artifacts, or existing reports were edited for this diagnostic. Temporary HermiT files were written only under:

```text
/tmp/ssn-to-bfo-hermit-observation-sensor-stimulus-evaluation
```

The purpose is to determine whether the remaining trio is driven by active class mappings, direct property mappings, property-chain mappings, source restrictions, target BFO/CCO context, or a mixed interaction.

## Prior Context

Earlier HermiT diagnostics split the original merged-profile unsatisfiabilities into separable clusters. After the SSN Systems and Input/Output fixes, the expected full M2 HermiT unsat set is now:

```text
sosa:Observation
sosa:Sensor
ssn:Stimulus
```

Prior probes suggested that this trio behaves as one interaction cluster:

- removing active mappings directly mentioning `sosa:Observation` cleared the trio;
- removing active mappings directly mentioning `sosa:Sensor` cleared the trio;
- removing the `sosa:Sensor` mapping subject cleared the trio;
- removing `sosa:hosts`, `sosa:madeBySensor`, or `sosa:observedProperty` cleared the trio;
- removing property-chain mappings cleared the trio.

This report re-runs those checks on the current post-Input/Output baseline and adds focused reconstruction and dependency checks.

## Method

For full-graph variants, the temporary M2 graph was built from:

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

Every HermiT variant used this command shape:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

ROBOT version:

```text
ROBOT version 1.9.7
```

For unsatisfiable variants, ROBOT returned nonzero and did not produce a reasoned output. For clean variants, ROBOT produced a reasoned output and no `owl:Nothing` entities were found. The sample simplicity blocker did not reappear in any reported variant.

## Current Baseline

Variant A reproduced the current full M2 baseline:

```text
sosa:Observation
sosa:Sensor
ssn:Stimulus
```

Variant B, source/import-only without `SSN2BFO.ttl`, was HermiT-clean. This confirms that the trio is not present in the source/import profile alone.

## Active Mapping Inventory

Relevant active mappings in `SSN2BFO.ttl`:

| Source | Mapping type | Active mapping summary |
| --- | --- | --- |
| `sosa:Observation` | class/restriction-style | subclass of `cco:PlannedAct` and `cco:has_process_part some (cco:ActOfObservation and cco:ActOfMeasuring)` |
| `sosa:Sensor` | class/restriction-style | subclass of `bfo:MaterialEntity` bearing a realizable entity realized in `sosa:Observation`, and `cco:agent_in some sosa:Observation` |
| `ssn:Stimulus` | class/restriction-style | equivalent to a CCO/BFO target class with a restriction to `sosa:Observation` |
| `sosa:hosts` | property-chain mapping | chain over `bfo:BFO_0000196`, `bfo:BFO_0000054`, `bfo:BFO_0000057` |
| `sosa:isHostedBy` | property-chain mapping | chain over `bfo:BFO_0000056`, `bfo:BFO_0000055`, `bfo:BFO_0000197` |
| `sosa:madeBySensor` | direct property mapping | `rdfs:subPropertyOf cco:ont00001833` |
| `sosa:madeObservation` | direct property mapping | `rdfs:subPropertyOf cco:ont00001787` |
| `sosa:observedProperty` | direct property mapping | `rdfs:subPropertyOf cco:ont00001921` |
| `sosa:observes` | direct property mapping | `rdfs:subPropertyOf ssn:forProperty` |
| `ssn:detects` | direct property mapping | `rdfs:subPropertyOf cco:ont00001886` |

Active core property-chain subjects discovered in `SSN2BFO.ttl`:

```text
sosa:hasSample
sosa:hosts
sosa:isHostedBy
sosa:isSampleOf
ssn:implementedBy
```

## Source Context Inventory

Relevant imported source context from `imports/ssn.ttl`:

- `sosa:Observation`
  - restrictions on `sosa:hasResult`, `sosa:madeBySensor`, `sosa:observedProperty`, `sosa:usedProcedure`, and values involving `ssn:Stimulus`;
  - source package used in this diagnostic: 107 triples.
- `sosa:Sensor`
  - subclass of `ssn:System`;
  - restrictions involving `sosa:madeObservation`, `sosa:observes`, `ssn:detects`, and `ssn:implements`;
  - source package used in this diagnostic: 125 triples.
- `ssn:Stimulus`
  - source restrictions linking to `sosa:Sensor` and `sosa:Observation`;
  - source package used in this diagnostic: 107 triples.
- `sosa:hosts`
  - source property chain in the imported source profile;
  - source package used in this diagnostic: 15 triples.
- `sosa:madeBySensor`, `sosa:madeObservation`, `sosa:observedProperty`, and `sosa:observes`
  - source packages connect the observation/sensor restrictions and property hierarchy.

The combined source package for Observation/Sensor/Stimulus was 125 triples.

## Target BFO/CCO Context Summary

Local target labels verified in `imports/cco.ttl`:

| Identifier | Label |
| --- | --- |
| `bfo:BFO_0000017` | realizable entity |
| `bfo:BFO_0000040` | material entity |
| `bfo:BFO_0000054` | has realization |
| `bfo:BFO_0000196` | bearer of |
| `bfo:BFO_0000197` | inheres in |
| `bfo:BFO_0000055` | realizes |
| `bfo:BFO_0000056` | participates in |
| `bfo:BFO_0000057` | has participant |
| `cco:ont00001787` | agent in |
| `cco:ont00001833` | has agent |
| `cco:ont00001886` | is affected by |
| `cco:ont00000037` | Act of Observation |
| `cco:ont00000228` | Planned Act |
| `cco:ont00000345` | Act of Measuring |
| `cco:ont00001777` | has process part |
| `cco:ont00001921` | has input |

Coarse target-context packages tested:

| Target-context group | Package size | Result |
| --- | ---: | --- |
| sensor bearer/function-style context | 62 triples | removal cleared trio |
| observation/planned-act context | 28 triples | removal did not clear trio |
| observedProperty / `cco:has input` context | 7 triples | removal did not clear trio |
| hosting BFO relation context | 96 triples | removal did not clear trio |

The sensor target-context result is informative but broad; it should not be read as identifying a single target axiom.

## Variant Summary Table

| ID | Variant | Triples | Return code | Output? | Unsat count | Unsat set |
| --- | --- | ---: | ---: | --- | ---: | --- |
| A | `A_full_m2` | 15475 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| B | `B_source_import_only` | 14485 | 0 | yes | 0 | clean |
| C | `C_remove_mapping_mentions_Observation` | 15400 | 0 | yes | 0 | clean |
| D | `D_remove_mapping_mentions_Sensor` | 15450 | 0 | yes | 0 | clean |
| E | `E_remove_Observation_subject` | 15458 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| F | `F_remove_Sensor_subject` | 15450 | 0 | yes | 0 | clean |
| G1 | `G1_remove_sosa_hosts_subject` | 15467 | 0 | yes | 0 | clean |
| G2 | `G2_remove_sosa_isHostedBy_subject` | 15467 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| G3 | `G3_remove_sosa_madeBySensor_subject` | 15474 | 0 | yes | 0 | clean |
| G4 | `G4_remove_sosa_madeObservation_subject` | 15474 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| G5 | `G5_remove_sosa_observedProperty_subject` | 15474 | 0 | yes | 0 | clean |
| G6 | `G6_remove_sosa_observes_subject` | 15474 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| G7 | `G7_remove_ssn_detects_subject` | 15474 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| H1 | `H1_remove_all_core_property_chains` | 15443 | 0 | yes | 0 | clean |
| H2 | `H2_remove_hosting_property_chains` | 15459 | 0 | yes | 0 | clean |
| H3 | `H3_remove_sample_property_chains` | 15465 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| H4 | `H4_remove_hosts_isHostedBy_chains` | 15459 | 0 | yes | 0 | clean |
| H5 | `H5_remove_obs_sensor_related_chains` | 15459 | 0 | yes | 0 | clean |
| I1 | `I1_remove_all_sensor_observation_direct_property_mappings` | 15454 | 0 | yes | 0 | clean |
| I2 | `I2_remove_madeBySensor_madeObservation` | 15473 | 0 | yes | 0 | clean |
| I3 | `I3_remove_observedProperty_observes` | 15473 | 0 | yes | 0 | clean |
| I4 | `I4_remove_hosting_relation_mappings` | 15459 | 0 | yes | 0 | clean |
| J1 | `J1_remove_Sensor_class_mapping` | 15450 | 0 | yes | 0 | clean |
| J2 | `J2_remove_Observation_class_mapping` | 15458 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| J3 | `J3_remove_Sensor_Observation_class_mappings` | 15433 | 0 | yes | 0 | clean |
| J4 | `J4_remove_Stimulus_mapping` | 15464 | 1 | no | 2 | `sosa:Observation`, `sosa:Sensor` |
| K1 | `K1_remove_source_sosa_Observation` | 15368 | 0 | yes | 0 | clean |
| K2 | `K2_remove_source_sosa_Sensor` | 15350 | 0 | yes | 0 | clean |
| K3 | `K3_remove_source_ssn_Stimulus` | 15368 | 0 | yes | 0 | clean |
| K4 | `K4_remove_source_sosa_hosts` | 15460 | 0 | yes | 0 | clean |
| K5 | `K5_remove_source_sosa_isHostedBy` | 15436 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| K6 | `K6_remove_source_sosa_madeBySensor` | 15404 | 0 | yes | 0 | clean |
| K7 | `K7_remove_source_sosa_madeObservation` | 15456 | 0 | yes | 0 | clean |
| K8 | `K8_remove_source_sosa_observedProperty` | 15415 | 0 | yes | 0 | clean |
| K9 | `K9_remove_source_sosa_observes` | 15455 | 0 | yes | 0 | clean |
| K10 | `K10_remove_source_trio_packages` | 15350 | 0 | yes | 0 | clean |
| L1 | `L1_remove_sensor_target_context` | 15413 | 0 | yes | 0 | clean |
| L2 | `L2_remove_observation_target_context` | 15447 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| L3 | `L3_remove_observedProperty_target_context` | 15468 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| L4 | `L4_remove_hosting_target_context` | 15379 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| M1 | `M1_source_plus_Sensor_mapping` | 14510 | 0 | yes | 0 | clean |
| M2 | `M2_source_plus_Observation_mapping` | 14501 | 0 | yes | 0 | clean |
| M3 | `M3_source_plus_Sensor_Observation_mappings` | 14526 | 0 | yes | 0 | clean |
| M4 | `M4_source_plus_hosting_group` | 14501 | 0 | yes | 0 | clean |
| M5 | `M5_source_plus_made_group` | 14487 | 0 | yes | 0 | clean |
| M6 | `M6_source_plus_observed_group` | 14486 | 0 | yes | 0 | clean |
| M7 | `M7_source_plus_all_sensor_obs_direct_property_mappings` | 14505 | 0 | yes | 0 | clean |
| M8 | `M8_source_plus_sensor_obs_property_chains` | 14501 | 0 | yes | 0 | clean |
| M9 | `M9_source_plus_sensor_obs_class_and_property_mappings` | 14556 | 0 | yes | 0 | clean |
| M10 | `M10_source_plus_all_core_mappings` | 14859 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |

Focused dependency variants:

| ID | Variant | Triples | Return code | Output? | Unsat count | Unsat set |
| --- | --- | ---: | ---: | --- | ---: | --- |
| N1 | `N1_source_plus_Sensor_and_hosting` | 14526 | 0 | yes | 0 | clean |
| N2 | `N2_source_plus_Sensor_and_made_group` | 14512 | 0 | yes | 0 | clean |
| N3 | `N3_source_plus_Sensor_and_observed_group` | 14511 | 0 | yes | 0 | clean |
| N4 | `N4_source_plus_Observation_and_made_group` | 14503 | 0 | yes | 0 | clean |
| N5 | `N5_source_plus_Observation_and_observed_group` | 14502 | 0 | yes | 0 | clean |
| N6 | `N6_source_plus_Sensor_Observation_and_hosting` | 14542 | 0 | yes | 0 | clean |
| N7 | `N7_source_plus_Sensor_Observation_and_made_observed` | 14529 | 0 | yes | 0 | clean |
| N8 | `N8_full_remove_Sensor_hosts_made_observed` | 15440 | 0 | yes | 0 | clean |
| N9 | `Nfull_remove_ssn_System` | 15464 | 0 | yes | 0 | clean |
| N10 | `Nfull_remove_sosa_Platform` | 15464 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N11 | `Nfull_remove_sosa_Result` | 15450 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N12 | `Nfull_remove_sosa_FeatureOfInterest` | 15433 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N13 | `Nfull_remove_sosa_ObservableProperty` | 15449 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N14 | `Nfull_remove_ssn_Property` | 15467 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N15 | `Nrecon_core_class_only` | 14807 | 0 | yes | 0 | clean |
| N16 | `Nrecon_core_class_plus_sensor_obs_direct_props` | 14827 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N17 | `Nsplit_base_System_FOIgroup` | 14641 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N18 | `Nsplit_base_Platform_FOIgroup` | 14642 | 0 | yes | 0 | clean |
| N19 | `Nsplit_base_System_FOI` | 14608 | 0 | yes | 0 | clean |
| N20 | `Nsplit_base_System_ObservableProperty` | 14592 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N21 | `Nsplit_base_System_Property` | 14573 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N22 | `Nsplit_base_System_FOI_ObservableProperty` | 14634 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N23 | `Nsplit_base_System_FOI_Property` | 14615 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| N24 | `Nsplit_base_System_ObservableProperty_Property` | 14599 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |

## Observation/Sensor/Stimulus Cluster Analysis

The trio behaves as a tightly coupled interaction cluster in the full graph.

Most successful removals clear all three classes together:

- mapping packages directly mentioning `sosa:Observation`;
- mapping packages directly mentioning `sosa:Sensor`;
- `sosa:Sensor` mapping subject;
- `sosa:hosts`;
- `sosa:madeBySensor`;
- `sosa:observedProperty`;
- all core property-chain mappings;
- hosting property-chain mappings;
- all sensor/observation direct property mapping groups;
- `sosa:Sensor` class/restriction mapping;
- source packages for `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus`, `sosa:hosts`, `sosa:madeBySensor`, `sosa:madeObservation`, `sosa:observedProperty`, and `sosa:observes`;
- coarse sensor target context.

The only tested removal that produced a subset rather than clearing the full trio was removing the `ssn:Stimulus` mapping subject. That left:

```text
sosa:Observation
sosa:Sensor
```

This suggests `ssn:Stimulus` is downstream or parallel in the cluster, while the Observation/Sensor side remains active.

## Property-Chain Results

Property-chain removals are high-impact:

- removing all core SOSA/SSN property chains cleared the trio;
- removing only hosting-related chains cleared the trio;
- removing sample-related property chains did not clear the trio;
- removing `sosa:hosts` / `sosa:isHostedBy` chains cleared the trio.

This points specifically to the hosting chain area, not to sample-chain cleanup.

The active `sosa:hosts` property-chain mapping is a one-subject reducer:

```text
sosa:hosts
```

Removing `sosa:isHostedBy` alone did not clear the trio.

## Direct Property Mapping Results

Direct property mapping removals are also high-impact:

- removing `sosa:madeBySensor` alone cleared the trio;
- removing `sosa:observedProperty` alone cleared the trio;
- removing `sosa:madeObservation` alone did not clear the trio;
- removing `sosa:observes` alone did not clear the trio;
- removing `ssn:detects` alone did not clear the trio;
- removing grouped `madeBySensor` / `madeObservation` cleared the trio;
- removing grouped `observedProperty` / `observes` cleared the trio.

This makes `sosa:madeBySensor` and `sosa:observedProperty` the strongest direct-property reducers in the tested set.

## Class/Restriction Mapping Results

Class/restriction-style mapping removals show an asymmetric pattern:

- removing `sosa:Sensor` clears the trio;
- removing `sosa:Observation` alone does not clear the trio;
- removing both clears the trio;
- removing `ssn:Stimulus` removes only `ssn:Stimulus`, leaving `sosa:Observation` and `sosa:Sensor`.

The `sosa:Sensor` class/restriction mapping is therefore a high-impact full-graph reducer. The `sosa:Observation` mapping is still part of the interaction, but removing it alone is not sufficient in the current graph.

## Source-Context Results

Source-context removals are broad but informative:

- removing source packages for `sosa:Observation`, `sosa:Sensor`, or `ssn:Stimulus` cleared the trio;
- removing source packages for `sosa:hosts`, `sosa:madeBySensor`, `sosa:madeObservation`, `sosa:observedProperty`, or `sosa:observes` cleared the trio;
- removing the `sosa:isHostedBy` source package did not clear the trio.

These results show that the source ontology restrictions and property commitments are necessary to the tested full-OWL interaction. They do not show that the source ontology is wrong.

## Target-Context Results

Target-context removals were intentionally coarse and should be interpreted cautiously.

The only target-context removal that cleared the trio was the sensor bearer/function-style target package, which included BFO/CCO context around:

```text
bfo:BFO_0000040
bfo:BFO_0000196
bfo:BFO_0000017
bfo:BFO_0000054
cco:ont00001787
```

Removing observation target context, observedProperty target context, or hosting BFO relation context did not clear the trio.

This supports a mixed mapping/target interaction around the `sosa:Sensor` mapping, but the removal is too broad to identify a single BFO or CCO axiom.

## Reconstruction Results

Small reconstruction variants stayed clean:

- `sosa:Sensor` mapping alone;
- `sosa:Observation` mapping alone;
- both Sensor and Observation mappings;
- hosting group alone;
- made group alone;
- observed group alone;
- all sensor/observation direct property mappings;
- sensor/observation property chains;
- sensor/observation class and property mappings together.

The trio was reproduced by:

- source/import-only plus all current core SOSA/SSN mappings;
- source/import-only plus all core class mappings and sensor/observation direct/property-chain groups;
- source/import-only plus the sensor/observation cluster mapping set, `ssn:System`, and the `FeatureOfInterest` / `ObservableProperty` / `ssn:Property` group;
- source/import-only plus the sensor/observation cluster mapping set, `ssn:System`, and `sosa:ObservableProperty`;
- source/import-only plus the sensor/observation cluster mapping set, `ssn:System`, and `ssn:Property`.

The same cluster mapping set plus `sosa:Platform` and the FeatureOfInterest/ObservableProperty/Property group stayed clean. That makes `ssn:System`, not `sosa:Platform`, the high-impact broader class mapping in the tested reconstruction.

## Focused Candidate Dependency Results

Smallest tested full-graph clearing actions:

| Clear action | Result |
| --- | --- |
| remove `sosa:Sensor` mapping subject | clean |
| remove `sosa:hosts` mapping subject | clean |
| remove `sosa:madeBySensor` mapping subject | clean |
| remove `sosa:observedProperty` mapping subject | clean |
| remove `ssn:System` mapping subject | clean |
| remove all hosting property chains | clean |
| remove all sensor/observation direct property mappings | clean |

Smallest tested reconstruction groups:

| Reconstruction | Result |
| --- | --- |
| source + sensor/observation cluster mapping set | clean |
| source + sensor/observation cluster + `ssn:System` | clean |
| source + sensor/observation cluster + `sosa:ObservableProperty` | clean |
| source + sensor/observation cluster + `ssn:Property` | clean |
| source + sensor/observation cluster + `ssn:System` + `sosa:ObservableProperty` | trio reproduced |
| source + sensor/observation cluster + `ssn:System` + `ssn:Property` | trio reproduced |

The smallest tested reproductions therefore require:

- the source/import ontology;
- the sensor/observation cluster mapping set;
- the active `ssn:System` mapping;
- at least one property-context class mapping such as `sosa:ObservableProperty` or `ssn:Property`.

## Explanation Assessment

### Does The Trio Behave As One Inseparable Cluster?

Mostly yes, in the tested full graph. Most reducers clear all three classes together. The main partial result is:

- removing `ssn:Stimulus` clears only `ssn:Stimulus`, leaving `sosa:Observation` and `sosa:Sensor`.

So the cluster has a core Observation/Sensor interaction with `ssn:Stimulus` attached through the source/mapping pattern.

### Which Mappings Are High-Impact?

High-impact mapping subjects or groups:

- `sosa:Sensor`;
- `sosa:hosts`;
- `sosa:madeBySensor`;
- `sosa:observedProperty`;
- `ssn:System`;
- hosting-related property chains;
- sensor/observation direct property groups.

The `sosa:Observation` mapping is involved, but its subject-only removal did not clear the trio in the current full graph.

### Which Source Restrictions Are High-Impact?

High-impact source packages include:

- `sosa:Observation`;
- `sosa:Sensor`;
- `ssn:Stimulus`;
- `sosa:hosts`;
- `sosa:madeBySensor`;
- `sosa:madeObservation`;
- `sosa:observedProperty`;
- `sosa:observes`.

These source packages define the local observation/sensor/stimulus shape that the active mappings interact with.

### Is The Dependency Mapping-Side, Source-Side, Target-Side, Or Mixed?

The dependency is mixed.

Source-only is clean. Small mapping-only additions are clean. The trio is reproduced only when a broader combination is present:

- source restrictions;
- sensor/observation class and property mappings;
- `ssn:System` mapping;
- property-context mappings such as `sosa:ObservableProperty` or `ssn:Property`;
- BFO/CCO target context for the `sosa:Sensor` bearer/function pattern.

### Does The Evidence Support A Fix-Evaluation Branch?

Yes, but it should be explicitly framed as a fix-evaluation branch, not a final fix branch.

There are several high-impact reducers, and the smallest semantic target is not obvious from this report alone. A good next branch should compare narrow temporary deferrals rather than immediately choosing one final mapping correction.

## Recommendation

No repo mapping change should be made in this diagnostic branch.

Recommended next branch:

```text
review/evaluate-observation-sensor-stimulus-deferrals
```

That branch should temporarily compare HermiT, ELK, and audit impact for narrow alternatives such as:

- defer `sosa:Sensor` class/restriction mapping;
- defer `sosa:hosts` property-chain mapping;
- defer `sosa:madeBySensor` direct property mapping;
- defer `sosa:observedProperty` direct property mapping;
- defer `ssn:System` class mapping;
- compare grouped rule/COMS-only treatments for the observation/sensor/stimulus pattern.

The strongest current evidence points to an interaction involving `sosa:Sensor`, `ssn:System`, hosting/property mappings, and property-context mappings. It does not prove that any single mapping is semantically wrong.

Keep this final cluster separate from the already-fixed SSN Systems and Input/Output work.
