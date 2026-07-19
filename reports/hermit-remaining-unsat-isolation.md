# HermiT Remaining Unsat Isolation

## Scope

This report documents a HermiT/full OWL diagnostic focused on the remaining unsatisfiable classes after the selected SSN Systems BFO dependence mappings were deferred.

No repository ontology mappings, spreadsheets, imports, source examples, generated/release artifacts, or existing reports were modified for this diagnostic. All temporary graphs, ROBOT outputs, and captured stdout/stderr files were written under:

`/tmp/ssn-to-bfo-hermit-remaining-unsat-isolation`

This is a reducer/isolation diagnostic. A temporary edit that reduces the HermiT unsatisfiable-class set identifies an interaction point, not by itself an incorrect mapping.

## Current Baseline And Prior Context

Earlier HermiT diagnostics found that the merged source/import-plus-mapping profile was not HermiT-clean, and that selected direct SSN Systems BFO dependence mappings were high-impact interaction points. After those selected mappings were deferred, the expected remaining HermiT unsatisfiable set was approximately:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

This diagnostic reproduced that current 8-class baseline and then tested temporary mapping/removal variants to isolate whether the remaining classes are source/import-only issues, direct mapping issues, property-chain issues, SSN Systems issues, or core SOSA/SSN issues.

## Baseline Setup

Every HermiT variant was built from a temporary no-imports merged graph using:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Temporary cleanup applied to every variant:

- removed all `owl:imports` triples;
- removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- removed `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Each variant used this command pattern:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

- ROBOT: `ROBOT version 1.9.7`
- Java: `java version "22.0.2" 2024-07-16`

Counts discovered from the active mapping graph for the temporary removals:

| Mapping group | Count |
| --- | ---: |
| Direct property mapping subjects | 26 |
| Direct class mapping subjects | 31 |
| Property-chain mapping subjects | 5 |
| SSN Systems mapping subjects | 25 |
| Core SOSA/SSN mapping subjects | 35 |
| Focused reducer subjects | 14 |

The sample simplicity blocker did not reappear in any variant because the two sample functional-property cleanup removals were applied consistently.

## Variant Summary Table

| Variant | Temporary edit | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Delta vs baseline |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| A. Current M2 baseline | Current source/import graph plus current `SSN2BFO.ttl` after selected dependence deferrals. | 1 | no | n/a | 8 | 0 |
| B. Source/import-only control | Omit the `SSN2BFO.ttl` mapping graph. | 0 | yes | 0 | 0 | -8 |
| C. Remove all active direct property mappings | Remove active direct `rdfs:subPropertyOf` mapping assertions from source properties to BFO/CCO target properties. | 1 | no | n/a | 3 | -5 |
| D. Remove all active direct class mappings | Remove active direct class mapping assertions from source classes to BFO/CCO target classes. | 0 | yes | 0 | 0 | -8 |
| E. Remove direct class and direct property mappings | Remove both active direct class mappings and active direct property mappings. | 0 | yes | 0 | 0 | -8 |
| F. Remove property-chain mappings only | Remove named `owl:propertyChainAxiom` mapping constructs from `SSN2BFO.ttl`. | 1 | no | n/a | 5 | -3 |
| G. Remove all active SSN Systems mappings | Remove mapping axioms whose source term is in the `ssn-system:` namespace. | 1 | no | n/a | 5 | -3 |
| H. Remove all active core SOSA/SSN mappings | Remove mapping axioms whose source term is in the `sosa:` or `ssn:` namespaces, excluding `ssn-system:`. | 1 | no | n/a | 3 | -5 |

Clean variants:

- B, source/import-only control;
- D, remove all active direct class mappings;
- E, remove all active direct class and direct property mappings.

No other tested variant was HermiT-clean.

## Current Remaining Unsat Set

Variant A reproduced the current M2-style baseline with 8 unsatisfiable classes:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

The temporary baseline graph had 15,514 triples. HermiT returned code `1`, did not produce a reasoned output, and reported unsatisfiable classes rather than the earlier sample simplicity blocker.

## Source/Import-Only Control Result

Variant B omitted the `SSN2BFO.ttl` mapping graph while keeping the same source/import files and sample cleanup.

Result:

- return code: `0`;
- reasoned output: yes;
- `owl:Nothing` count: `0`;
- unsatisfiable classes: none.

This indicates that the current 8 remaining unsatisfiable classes are introduced or amplified by mapping content in the merged profile, not by the local source/import profile alone under this no-imports diagnostic setup.

## Direct Class Vs Direct Property Vs Property-Chain Contribution

| Temporary edit | Remaining unsatisfiable classes | Classes removed from baseline |
| --- | --- | --- |
| C. Remove all active direct property mappings | `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| D. Remove all active direct class mappings | none | all 8 baseline classes |
| E. Remove all active direct class and property mappings | none | all 8 baseline classes |
| F. Remove property-chain mappings only | `ssn:Input`, `ssn:Output`, `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |

Interpretation:

- Direct property mappings are sufficient to account for the 5 core `sosa:` / `ssn:` unsats, because removing all active direct property mappings leaves only the 3 SSN Systems classes.
- Direct class mappings are also high-impact; removing all active direct class mappings clears all 8 classes. This is a broad reducer, not a correction plan.
- Property-chain mappings contribute to the `sosa:Observation`, `sosa:Sensor`, and `ssn:Stimulus` cluster, but do not affect `ssn:Input`, `ssn:Output`, or the 3 SSN Systems classes in isolation.

## Core SOSA/SSN Unsat Analysis

Variant H removed all active core SOSA/SSN mappings and left only the 3 SSN Systems unsats:

- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

This means the 5 core unsats are driven by active core SOSA/SSN mapping content in the temporary merged graph:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`

Focused core reducer probes found:

| Focused temporary edit | Unsat count | Classes removed from baseline |
| --- | ---: | --- |
| Remove active mappings directly mentioning `sosa:Observation` | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| Remove active mappings directly mentioning `sosa:Sensor` | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| Remove single focused `sosa:Sensor` mapping subject | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| Remove single focused `sosa:hosts` mapping subject | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| Remove single focused `sosa:madeBySensor` mapping subject | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| Remove single focused `sosa:observedProperty` mapping subject | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| Remove single focused `ssn:hasInput` mapping subject | 7 | `ssn:Input` |
| Remove single focused `ssn:hasOutput` mapping subject | 7 | `ssn:Output` |

Core observations:

- `sosa:Observation`, `sosa:Sensor`, and `ssn:Stimulus` behave as one interaction cluster in these reducers.
- `ssn:Input` and `ssn:Output` are separable one-class reducers through `ssn:hasInput` and `ssn:hasOutput`.
- Removing the property-chain mapping cluster removes the same `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` trio, so the core cluster likely involves the combined effect of source restrictions, direct property mappings, and chain-like commitments. This diagnostic does not prove a single axiom is wrong.

## SSN Systems Unsat Analysis

Variant G removed all active SSN Systems mappings and left only the 5 core unsats:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`

The removed SSN Systems unsats were:

- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

Focused SSN Systems reducer probes found:

| Focused temporary edit | Unsat count | Classes removed from baseline |
| --- | ---: | --- |
| Remove active SSN Systems direct class mappings | 5 | `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |
| Remove active SSN Systems direct property mappings | 8 | none |
| Remove `SurvivalProperty` and `SystemLifetime` mapping subjects | 8 | none |
| Remove source restrictions directly attached to or mentioning `ssn-system:BatteryLifetime` | 8 | none |
| Remove source restrictions directly attached to or mentioning `ssn-system:SurvivalProperty` | 5 | `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |
| Remove source restrictions directly attached to or mentioning `ssn-system:SystemLifetime` | 8 | none |
| Remove combined remaining-system source restrictions | 5 | `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |
| Remove SSN Systems class mappings plus `SurvivalProperty` source restrictions | 5 | `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |

SSN Systems observations:

- The remaining SSN Systems unsats appear tied to the interaction between active SSN Systems class mappings and imported source restrictions, especially restrictions involving `ssn-system:SurvivalProperty`.
- Active SSN Systems direct property mappings did not reduce the remaining 8-class set in this post-defer baseline.
- Removing source restrictions involving `ssn-system:SurvivalProperty` reduced the same 3 systems classes, while analogous removals for `BatteryLifetime` and `SystemLifetime` did not.
- This suggests the next explanatory work should focus on the `SurvivalProperty` source-restriction cluster and the active SSN Systems class mappings, not on restoring or changing the recently deferred direct BFO dependence property mappings.

## One-At-A-Time Class Mapping Results

The required one-at-a-time variants removed active `SSN2BFO.ttl` mapping axioms directly mentioning each remaining unsat source class IRI where such axioms existed.

| Source class | Temporary result |
| --- | --- |
| `sosa:Observation` | Reduced 8 to 5; removed `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus`. |
| `sosa:Sensor` | Reduced 8 to 5; removed `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus`. |
| `ssn:Input` | No reduction. |
| `ssn:Output` | No reduction. |
| `ssn:Stimulus` | No active mapping axioms directly mentioning this source class were found for this test, so no forced edit was run. |
| `ssn-system:BatteryLifetime` | No active mapping axioms directly mentioning this source class were found for this test, so no forced edit was run. |
| `ssn-system:SurvivalProperty` | No reduction. |
| `ssn-system:SystemLifetime` | No reduction. |

Additional focused mapping-subject probes showed one-class reducers for `ssn:Input` and `ssn:Output` through their corresponding properties:

- removing `ssn:hasInput` removed `ssn:Input`;
- removing `ssn:hasOutput` removed `ssn:Output`.

## Targeted Source-Restriction Results

The source-restriction variants modified only temporary copies of imported source restrictions. Repository imports were not changed.

| Targeted source-restriction removal | Extra triples removed | Unsat count | Classes removed from baseline |
| --- | ---: | ---: | --- |
| `ssn-system:BatteryLifetime` restrictions | 0 | 8 | none |
| `ssn-system:SurvivalProperty` restrictions | 51 | 5 | `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |
| `ssn-system:SystemLifetime` restrictions | 37 | 8 | none |
| Combined remaining-system restrictions | 88 | 5 | `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |

The `SurvivalProperty` restriction result is the only targeted source-restriction removal that changed the remaining set. This does not imply that the source restrictions are wrong; it shows that this source-restriction cluster participates in the HermiT interaction when combined with active mapping content.

## Reducer Summary

Temporary edits that cleared all 8 unsats:

- remove all active direct class mappings;
- remove all active direct class mappings plus all active direct property mappings.

Temporary edits that reduced the 8 unsats but did not clear them:

- remove all active direct property mappings: leaves 3 SSN Systems unsats;
- remove property-chain mappings only: leaves `ssn:Input`, `ssn:Output`, and 3 SSN Systems unsats;
- remove all active SSN Systems mappings: leaves 5 core SOSA/SSN unsats;
- remove all active core SOSA/SSN mappings: leaves 3 SSN Systems unsats;
- remove active SSN Systems direct class mappings: leaves 5 core SOSA/SSN unsats;
- remove source restrictions involving `ssn-system:SurvivalProperty`: leaves 5 core SOSA/SSN unsats.

Temporary edits that did not reduce the 8 unsats in this diagnostic:

- remove active SSN Systems direct property mappings;
- remove `SurvivalProperty` and `SystemLifetime` mapping subjects alone;
- remove source restrictions involving `ssn-system:BatteryLifetime`;
- remove source restrictions involving `ssn-system:SystemLifetime`;
- remove focused `ssn-system:hasOperatingRange`, `ssn-system:hasSurvivalRange`, or `ssn-system:hasSystemCapability` mapping subjects.

Which remaining classes appear tied to mapping content:

- All 8 baseline classes disappear in the source/import-only control and under broad direct-class mapping removal, so all are mapping-introduced or mapping-amplified in this no-imports HermiT diagnostic.

Which classes appear tied to core SOSA/SSN mapping content:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`

Which classes appear tied to source restrictions plus mapping content:

- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

The SSN Systems trio is especially associated with temporary removal of `ssn-system:SurvivalProperty` source restrictions and active SSN Systems class mappings.

## Recommendation

Do not make repository mapping changes from this diagnostic branch.

The evidence supports separating follow-up work into at least two narrow branches:

1. `review/hermit-core-sosa-sensor-cluster-explanation`
   - Focus on the `sosa:Observation` / `sosa:Sensor` / `ssn:Stimulus` cluster.
   - Include active mapping subjects such as `sosa:Sensor`, `sosa:hosts`, `sosa:madeBySensor`, and `sosa:observedProperty`, plus relevant source restrictions.
   - Keep this as explanation/minimal-conflict work before any mapping edit.

2. `review/hermit-survival-property-source-restriction-explanation`
   - Focus on `ssn-system:SurvivalProperty` source restrictions and active SSN Systems class mappings.
   - Explain why removing `SurvivalProperty` source restrictions removes `BatteryLifetime`, `SurvivalProperty`, and `SystemLifetime` from the unsat set.
   - Keep this separate from the core SOSA/SSN cleanup.

If a single next branch is needed, start with `review/hermit-survival-property-source-restriction-explanation` because the SSN Systems trio is now isolated from direct property mappings and appears to involve a smaller source-restriction/class-mapping interaction. The core SOSA/SSN cluster should remain separate because it involves different mapping subjects and property-chain effects.

The ELK validation suite should remain the near-term regression baseline while HermiT/full OWL cleanup proceeds through these isolated diagnostic branches.
