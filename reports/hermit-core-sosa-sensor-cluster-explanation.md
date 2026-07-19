# HermiT Core SOSA Sensor Cluster Explanation

## Scope

This report is a focused, report-only HermiT diagnostic for the remaining core SOSA/SSN unsatisfiable-class cluster after the SSN Systems fixes.

Current remaining full-OWL/HermiT cluster:

```text
sosa:Observation
sosa:Sensor
ssn:Input
ssn:Output
ssn:Stimulus
```

No ontology mappings, spreadsheet files, imports, source examples, generated/release artifacts, existing reports, branches, or PR content were edited. Temporary files were written only under:

```text
/tmp/ssn-to-bfo-hermit-core-sosa-sensor-cluster-explanation
```

## Prior Context

Prior diagnostics established:

- source/import-only controls are HermiT-clean;
- selected SSN Systems dependence mappings have been deferred;
- the active `ssn-system:SurvivalRange` class-expression mapping has been deferred;
- the SSN Systems trio is cleared from the current full M2 baseline;
- the remaining full M2 HermiT unsats are the five core SOSA/SSN classes listed above.

Earlier reducer probes suggested that:

- `sosa:Observation`, `sosa:Sensor`, and `ssn:Stimulus` behave as one interaction cluster;
- `ssn:Input` and `ssn:Output` are separable one-class reducers tied to `ssn:hasInput` and `ssn:hasOutput`;
- active direct property mappings and property-chain mappings are high-impact for the core cluster.

This report decomposes those signals more precisely.

## Method

For each HermiT variant, a temporary M2-style graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

The temporary graph was then cleaned by removing:

```text
all owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty
sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

Each variant was run with:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

```text
ROBOT version 1.9.7
java version "22.0.2" 2024-07-16
```

For each variant, the diagnostic recorded graph construction, approximate triple count, return code, reasoned-output presence, sample-simplicity blocker status, unsat count, unsat class set, and `owl:Nothing` count when reasoned output was produced.

No variant reintroduced the sample simplicity blocker.

## Current Baseline

The current full M2 baseline reproduces exactly five unsatisfiable classes:

```text
ssn:Output
sosa:Sensor
sosa:Observation
ssn:Stimulus
ssn:Input
```

The source/import-only control is HermiT-clean with `owl:Nothing` count 0.

This confirms the remaining issue is introduced or amplified by `SSN2BFO.ttl` mapping content interacting with otherwise clean source/import context.

## Active Mapping Inventory

| Source | Mapping type | Target summary |
| --- | --- | --- |
| `sosa:Observation` | direct class, restriction-style | `cco:ont00000228` / Planned Act; process-part restriction to `cco:ont00000037` / Act of Observation and `cco:ont00000345` / Act of Measuring through `cco:ont00001777` / has process part |
| `sosa:Sensor` | direct class, restriction-style | `bfo:BFO_0000040` / material entity; `bfo:BFO_0000196` / bearer of some realizable entity; `bfo:BFO_0000054` / has realization some `sosa:Observation`; `cco:ont00001787` / agent in some `sosa:Observation` |
| `ssn:Stimulus` | direct class, restriction-style | `cco:ont00000978` / Cause; `cco:ont00001803` / is cause of some `sosa:Observation` |
| `ssn:Input` | direct class | `cco:ont00000958` / Information Content Entity |
| `ssn:Output` | direct class | `cco:ont00000958` / Information Content Entity |
| `ssn:hasInput` | direct property | `cco:ont00001921` / has input |
| `ssn:hasOutput` | direct property | `cco:ont00001986` / has output |
| `sosa:hosts` | property chain | `bfo:BFO_0000196` / bearer of -> `bfo:BFO_0000054` / has realization -> `bfo:BFO_0000057` / has participant |
| `sosa:madeBySensor` | direct property | `cco:ont00001833` / has agent |
| `sosa:observedProperty` | direct property | `cco:ont00001921` / has input |

Core mapping group counts:

| Group | Count |
| --- | ---: |
| Core SOSA/SSN direct class mapping subjects | 19 |
| Core SOSA/SSN direct property mapping subjects | 22 |
| Core SOSA/SSN property-chain mapping subjects | 5 |
| Core SOSA/SSN restriction-style mapping subjects | 17 |
| Selected sensor/observation direct property subjects | 7 |
| Hosting-related property-chain subjects | 2 |

The selected sensor/observation direct property group used in focused variants was:

```text
sosa:hasResult
sosa:madeBySensor
sosa:madeObservation
sosa:observedProperty
sosa:observes
ssn:detects
ssn:wasOriginatedBy
```

The hosting-related chain group was:

```text
sosa:hosts
sosa:isHostedBy
```

## Source Context Inventory

Imported `imports/ssn.ttl` source context includes:

- `sosa:Observation`
  - all-values restrictions using `sosa:madeBySensor`, `sosa:observedProperty`, `ssn:wasOriginatedBy`, and other SOSA relations;
  - cardinality restrictions on `sosa:madeBySensor`, `sosa:observedProperty`, `ssn:wasOriginatedBy`, and observation result/time relations.
- `sosa:Sensor`
  - subclass of `ssn:System`;
  - restrictions to `sosa:Observation`, `sosa:ObservableProperty`, and `ssn:Stimulus`.
- `ssn:Stimulus`
  - restrictions involving `ssn:isProxyFor`, inverse `ssn:detects`, and inverse `ssn:wasOriginatedBy`.
- `ssn:Input`
  - inverse `ssn:hasInput` all-values and minimum-cardinality restrictions.
- `ssn:Output`
  - inverse `ssn:hasOutput` all-values and minimum-cardinality restrictions.

Source package sizes used in this diagnostic:

| Source package | Triple count |
| --- | ---: |
| `sosa:Observation` source package | 107 |
| `sosa:Sensor` source package | 107 |
| `ssn:Stimulus` source package | 107 |
| `sosa:observedProperty` source package | 71 |
| `sosa:madeBySensor` source package | 71 |
| `ssn:Input` + `ssn:Output` source packages | 43 |
| `ssn:hasInput` + `ssn:hasOutput` source restrictions | 53 |
| `sosa:Observation` source restrictions | 107 |
| `sosa:Sensor` source restrictions | 105 |
| `ssn:Stimulus` source restrictions | 107 |

## Target BFO/CCO Context Summary

Relevant local target identifiers and labels:

| Identifier | Label |
| --- | --- |
| `bfo:BFO_0000017` | realizable entity |
| `bfo:BFO_0000040` | material entity |
| `bfo:BFO_0000054` | has realization |
| `bfo:BFO_0000196` | bearer of |
| `cco:ont00001787` | agent in |
| `cco:ont00000037` | Act of Observation |
| `cco:ont00000228` | Planned Act |
| `cco:ont00000345` | Act of Measuring |
| `cco:ont00001777` | has process part |
| `cco:ont00001921` | has input |
| `cco:ont00001986` | has output |

## Variant Summary Table

| Variant | Temporary edit | Triples | Return | Result |
| --- | --- | ---: | ---: | --- |
| A | Full M2 baseline | 15477 | 1 | 5 unsats: `ssn:Output`, `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus`, `ssn:Input` |
| B | Source/import-only control, no `SSN2BFO.ttl` mapping graph | 14485 | 0 | clean; `owl:Nothing` count 0 |
| C | Remove all active core SOSA/SSN direct property mappings | 15455 | 0 | clean |
| D | Remove all active core SOSA/SSN direct class mappings | 15165 | 0 | clean |
| E | Remove all active core SOSA/SSN property-chain mappings | 15446 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| F1 | Remove `sosa:Sensor` mapping subject | 15452 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| F2 | Remove `sosa:Observation` mapping subject | 15461 | 1 | 5 unsats remain |
| F3 | Remove `sosa:hosts` mapping subject | 15469 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| F4 | Remove `sosa:madeBySensor` mapping subject | 15476 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| F5 | Remove `sosa:observedProperty` mapping subject | 15476 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| F6 | Remove `ssn:hasInput` mapping subject | 15476 | 1 | 4 unsats; `ssn:Input` removed |
| F7 | Remove `ssn:hasOutput` mapping subject | 15476 | 1 | 4 unsats; `ssn:Output` removed |
| F8 | Remove `ssn:Input` mapping subject | 15476 | 1 | 5 unsats remain |
| F9 | Remove `ssn:Output` mapping subject | 15476 | 1 | 5 unsats remain |
| F10 | Remove `ssn:Stimulus` mapping subject | 15467 | 1 | 4 unsats; `ssn:Stimulus` removed |
| G1 | Remove `sosa:Sensor` + `sosa:Observation` mappings | 15436 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| G2 | Remove `sosa:Sensor` + `sosa:hosts` mappings | 15444 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| G3 | Remove `sosa:Sensor` + `sosa:madeBySensor` mappings | 15451 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| G4 | Remove `sosa:Sensor` + `sosa:observedProperty` mappings | 15451 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| G5 | Remove `sosa:hosts` + `sosa:madeBySensor` + `sosa:observedProperty` | 15467 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| G6 | Remove hosting-related property chains | 15461 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| G7 | Remove selected sensor/observation direct properties | 15471 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| H1 | Remove `ssn:hasInput` only | 15476 | 1 | 4 unsats; `ssn:Input` removed |
| H2 | Remove `ssn:hasOutput` only | 15476 | 1 | 4 unsats; `ssn:Output` removed |
| H3 | Remove `ssn:hasInput` + `ssn:hasOutput` | 15475 | 1 | 3 unsats: `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus` |
| H4 | Remove `ssn:Input` + `ssn:Output` source packages | 15436 | 1 | 3 unsats: `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus` |
| H5 | Remove source restrictions using `ssn:hasInput` + `ssn:hasOutput` | 15427 | 1 | 3 unsats: `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus` |
| I1 | Remove `sosa:Observation` source package | 15372 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| I2 | Remove `sosa:Sensor` source package | 15372 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| I3 | Remove `ssn:Stimulus` source package | 15372 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| I4 | Remove `sosa:observedProperty` source package | 15407 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| I5 | Remove `sosa:madeBySensor` source package | 15407 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| I6 | Remove `sosa:Observation` source restrictions | 15372 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| I7 | Remove `sosa:Sensor` source restrictions | 15374 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| I8 | Remove `ssn:Stimulus` source restrictions | 15372 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| J1 | Source/import-only + `sosa:Sensor` mapping only | 14510 | 0 | clean |
| J2 | Source/import-only + `sosa:Observation` mapping only | 14501 | 0 | clean |
| J2b | Source/import-only + `sosa:Sensor` + `sosa:Observation` mappings | 14526 | 0 | clean |
| J3 | Source/import-only + selected sensor/observation direct properties | 14491 | 0 | clean |
| J4 | Source/import-only + hosting-related property chains | 14501 | 0 | clean |
| J5 | Source/import-only + `ssn:hasInput` + `ssn:hasOutput` | 14487 | 0 | clean |
| J6 | Source/import-only + all core direct properties | 14507 | 0 | clean |
| J7 | Source/import-only + all core property chains | 14516 | 0 | clean |
| J8 | Source/import-only + all core SOSA/SSN mappings | 14859 | 1 | 5 unsats |
| J9 | Source + Sensor/Observation mappings + selected direct properties + hosting chains | 14548 | 0 | clean |
| J10 | Source + all core direct properties + all core chains | 14538 | 0 | clean |
| J11 | Source + all core class, direct property, and property-chain mappings | 14850 | 1 | 5 unsats |
| K1 | Source + all core class mappings | 14797 | 0 | clean |
| K2 | Source + all core class mappings + all core direct properties | 14819 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| K3 | Source + all core class mappings + all core property chains | 14828 | 0 | clean |
| K4 | Source + all core class mappings + all core direct properties + hosting chains | 14835 | 1 | 5 unsats |
| K5 | Source + all core class mappings + selected sensor/observation properties + hosting chains | 14819 | 1 | 3 unsats: `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus` |
| K6 | Source + only Observation/Sensor/Stimulus class mappings + selected properties + hosting chains | 14558 | 0 | clean |
| K7 | Source + Input/Output class mappings + `hasInput`/`hasOutput` | 14489 | 0 | clean |
| K8 | Source + Input class mapping + `hasInput` | 14487 | 0 | clean |
| K9 | Source + Output class mapping + `hasOutput` | 14487 | 0 | clean |
| K10 | Source + all core class mappings + `hasInput`/`hasOutput` | 14799 | 1 | 2 unsats: `ssn:Output`, `ssn:Input` |
| K11 | Source + all core class mappings + `hasInput` | 14798 | 1 | 1 unsat: `ssn:Input` |
| K12 | Source + all core class mappings + `hasOutput` | 14798 | 1 | 1 unsat: `ssn:Output` |

## Observation/Sensor/Stimulus Cluster Analysis

The `sosa:Observation` / `sosa:Sensor` / `ssn:Stimulus` trio is separable from `ssn:Input` and `ssn:Output`.

Removals that clear the trio and leave only `ssn:Input` / `ssn:Output`:

- all core property-chain mappings;
- `sosa:Sensor`;
- `sosa:hosts`;
- `sosa:madeBySensor`;
- `sosa:observedProperty`;
- hosting-related property chains;
- selected sensor/observation direct properties;
- source packages or source restrictions involving `sosa:Observation`, `sosa:Sensor`, or `ssn:Stimulus`.

Removals that do not clear the trio:

- `sosa:Observation` mapping alone;
- `ssn:Stimulus` mapping alone clears only `ssn:Stimulus`, leaving `sosa:Observation` and `sosa:Sensor`;
- `ssn:hasInput` and `ssn:hasOutput` removals affect only the Input/Output side.

Reconstruction results sharpen the interaction:

- source/import-only is clean;
- `sosa:Sensor` mapping alone is clean;
- `sosa:Observation` mapping alone is clean;
- selected direct properties alone are clean;
- hosting chains alone are clean;
- `sosa:Sensor` + `sosa:Observation` + selected properties + hosting chains are still clean;
- all core class mappings + selected sensor/observation direct properties + hosting chains reproduce exactly the trio;
- only Observation/Sensor/Stimulus class mappings + selected properties + hosting chains are clean.

This means the trio is not explained by one local class mapping alone. It requires broader core class-mapping context plus the selected sensor/observation property and hosting-chain mappings.

## Input/Output Analysis

`ssn:Input` and `ssn:Output` are separable one-class reducers.

Evidence:

- removing `ssn:hasInput` removes only `ssn:Input` from the five-class baseline;
- removing `ssn:hasOutput` removes only `ssn:Output`;
- removing both `ssn:hasInput` and `ssn:hasOutput` leaves only the Observation/Sensor/Stimulus trio;
- removing source packages or restrictions for Input/Output also leaves only the trio.

Reconstruction evidence:

- `ssn:Input` class mapping + `ssn:hasInput` alone is clean;
- `ssn:Output` class mapping + `ssn:hasOutput` alone is clean;
- Input/Output class mappings + `hasInput`/`hasOutput` alone are clean;
- all core class mappings + `hasInput` reproduces `ssn:Input`;
- all core class mappings + `hasOutput` reproduces `ssn:Output`;
- all core class mappings + both `hasInput` and `hasOutput` reproduces the Input/Output pair.

So the Input/Output issue is not simply "`ssn:hasInput` is wrong" or "`ssn:Input` is wrong." It is a mixed interaction between the simple Input/Output class mappings, their source inverse/cardinality restrictions, `hasInput`/`hasOutput` mappings, and broader core class-mapping context.

## Source-Context Results

Source/import-only is HermiT-clean, so source context alone is not dirty.

However, source context is high-impact when mapping content is present:

- removing source packages for `sosa:Observation`, `sosa:Sensor`, or `ssn:Stimulus` clears the trio;
- removing source packages for `sosa:observedProperty` or `sosa:madeBySensor` clears the trio;
- removing source restrictions involving Observation/Sensor/Stimulus clears the trio;
- removing Input/Output source packages or `hasInput`/`hasOutput` source restrictions clears the Input/Output pair.

This supports a mixed source/mapping explanation rather than a source-only explanation.

## Reconstruction Results

Small reconstructions did not reproduce the full cluster:

- individual `sosa:Sensor` or `sosa:Observation` mappings were clean;
- individual selected property groups were clean;
- all core direct properties without core class mappings were clean;
- all core property chains without core class mappings were clean;
- all core class mappings alone were clean.

Reproductions found:

- all core mappings reproduced all five classes;
- all core class mappings + all core direct properties reproduced only `ssn:Input` and `ssn:Output`;
- all core class mappings + all core direct properties + hosting chains reproduced all five classes;
- all core class mappings + selected sensor/observation direct properties + hosting chains reproduced exactly the Observation/Sensor/Stimulus trio;
- all core class mappings + `hasInput` reproduced only `ssn:Input`;
- all core class mappings + `hasOutput` reproduced only `ssn:Output`.

Smallest tested reproductions:

| Cluster | Smallest tested reproduction |
| --- | --- |
| Observation/Sensor/Stimulus trio | source/imports + all core class mappings + selected sensor/observation direct property mappings + hosting-related property chains |
| `ssn:Input` | source/imports + all core class mappings + `ssn:hasInput` |
| `ssn:Output` | source/imports + all core class mappings + `ssn:hasOutput` |
| Full five-class cluster | source/imports + all core class mappings + all core direct properties + hosting-related property chains |

The diagnostic did not find a smaller local reproduction using only the directly named cluster classes and properties.

## Focused Candidate Dependency Results

High-impact mapping-side dependencies:

- `sosa:Sensor` class/restriction mapping;
- `sosa:hosts` property-chain mapping;
- `sosa:madeBySensor` direct property mapping;
- `sosa:observedProperty` direct property mapping;
- core property-chain mappings as a group;
- selected sensor/observation direct property mappings as a group;
- `ssn:hasInput`;
- `ssn:hasOutput`.

High-impact source-side dependencies:

- source restrictions around `sosa:Observation`;
- source restrictions around `sosa:Sensor`;
- source restrictions around `ssn:Stimulus`;
- source packages around `sosa:observedProperty` and `sosa:madeBySensor`;
- source restrictions around `ssn:hasInput` and `ssn:hasOutput`.

The high-impact removals are reducers, not proof of invalidity. In several cases, a mapping subject is high-impact only in the presence of broader core class mappings and source restrictions.

## Explanation Assessment

The five classes are not one indivisible cluster.

They split into:

1. Observation/Sensor/Stimulus cluster:
   - `sosa:Observation`
   - `sosa:Sensor`
   - `ssn:Stimulus`
2. Input/Output pair:
   - `ssn:Input`
   - `ssn:Output`

The dependency is mixed:

- source/import-only is clean;
- mapping-only groups in small reconstructions are clean;
- removals and reconstructions show the unsats require combinations of source restrictions, core class mappings, direct property mappings, and property chains.

No single tested mapping has enough evidence here to justify a final fix branch by itself.

The evidence does justify narrower fix-evaluation branches:

- evaluate deferring or weakening `ssn:hasInput` and `ssn:hasOutput` separately from the Observation/Sensor/Stimulus cluster;
- evaluate the Observation/Sensor/Stimulus cluster separately, starting with `sosa:hosts`, `sosa:madeBySensor`, and `sosa:observedProperty` because each is an individual reducer;
- avoid mixing Input/Output changes with Observation/Sensor/Stimulus changes unless a later report proves they must be handled together.

## Recommendation

Do not make ontology changes in this diagnostic branch.

Recommended next steps:

1. Create a fix-evaluation branch for the Input/Output pair:
   - temporarily defer `ssn:hasInput` and/or `ssn:hasOutput` direct property mappings;
   - measure HermiT, mapping audit, and ELK instance entailment impact;
   - keep this separate from Observation/Sensor/Stimulus.
2. Create a separate explanation or fix-evaluation branch for the Observation/Sensor/Stimulus cluster:
   - test `sosa:hosts` property-chain deferral as one narrowly scoped candidate;
   - separately test `sosa:madeBySensor` and `sosa:observedProperty` direct property mapping deferrals;
   - do not conclude semantic wrongness from reducer behavior alone.

The standard ELK validation suite should remain the near-term regression baseline while HermiT/full OWL cleanup proceeds in these narrow branches.
