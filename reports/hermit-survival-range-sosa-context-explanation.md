# HermiT SurvivalRange SOSA Context Explanation

## Scope

This report is a read-only HermiT diagnostic for the high-impact `ssn-system:SurvivalRange` mapping dependency identified in `reports/hermit-survival-property-broader-context-extraction.md`.

The task was to explain why the SSN Systems trio:

```text
ssn-system:BatteryLifetime
ssn-system:SurvivalProperty
ssn-system:SystemLifetime
```

remains unsatisfiable in the B2 systems-only reproduction, and why removing the active `ssn-system:SurvivalRange` class mapping clears that trio.

No repository ontology mappings, spreadsheets, imports, source examples, generated artifacts, release artifacts, or existing reports were edited for this diagnostic. All temporary HermiT inputs and outputs were written under:

```text
/tmp/ssn-to-bfo-hermit-survival-range-sosa-context-explanation
```

## Prior Context

The prior broader-context diagnostic established:

- Full M2 baseline: 8 unsatisfiable classes.
- B2 systems-only reproduction: remove targeted core reducer mapping subjects:
  - `sosa:Sensor`
  - `sosa:hosts`
  - `sosa:madeBySensor`
  - `sosa:observedProperty`
  - `ssn:hasInput`
  - `ssn:hasOutput`
- B2 leaves exactly the SSN Systems trio:
  - `ssn-system:BatteryLifetime`
  - `ssn-system:SurvivalProperty`
  - `ssn-system:SystemLifetime`
- Removing all remaining `sosa:` mappings from B2 clears the trio.
- Removing broad core `ssn:` source context from B2 clears the trio.
- Reconstructing from a clean H5-style base reproduces the trio only when broad core source context is combined with remaining `sosa:` mappings.
- Removing the active `ssn-system:SurvivalRange` class mapping from B2 clears the trio.

The prior report did not treat the `SurvivalRange` result as proof that the mapping is wrong. This report keeps that same caution and refines the dependency.

## Method

Every full-graph HermiT variant used the same M2-style temporary graph:

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

For each variant, the diagnostic recorded temporary graph construction, approximate triple count, return code, reasoned-output presence, sample-simplicity blocker presence, unsatisfiable class set, and `owl:Nothing` count when a reasoned output was produced.

No variant reintroduced the sample simplicity blocker.

## SurvivalRange Mapping Expression Summary

The active `ssn-system:SurvivalRange` mapping expression in `SSN2BFO.ttl` is at approximately lines 1117-1147. It maps `SurvivalRange` as a subclass of a function/realization pattern:

```text
ssn-system:SurvivalRange
  rdfs:subClassOf
    bfo:BFO_0000034
    and bfo:BFO_0000054 some
      (bfo:BFO_0000015
       and cco:ont00001819 some
         (bfo:BFO_0000015
          and bfo:BFO_0000055 some
            (cco:ont00000177
             and cco:ont00001920 some cco:ont00000319)))
```

Verified local labels for the target pattern:

| Identifier | Local label |
| --- | --- |
| `bfo:BFO_0000034` | function |
| `bfo:BFO_0000054` | has realization |
| `bfo:BFO_0000015` | process |
| `cco:ont00001819` | caused by |
| `bfo:BFO_0000055` | realizes |
| `cco:ont00000177` | Affordance |
| `cco:ont00001920` | prescribed by |
| `cco:ont00000319` | Artifact Design |

## Comparable SSN Systems Class Mapping Pattern Summary

| Mapping subject | Target pattern summary | Shares SurvivalRange function/realization pattern? | Removal from B2 result | H5 reconstruction with only this mapping plus `ssn:` source and non-sample `sosa:` mappings |
| --- | --- | --- | --- | --- |
| `ssn-system:SurvivalRange` | `function` with `has realization`/`caused by`/`realizes`/`Affordance`/`prescribed by Artifact Design` | Yes | Clears systems trio | Reproduces systems trio |
| `ssn-system:SurvivalProperty` | Same function/realization pattern as `SurvivalRange` | Yes | No reduction | Clean |
| `ssn-system:SystemLifetime` | Same function/realization pattern, plus `cco:ont00001213` / Stasis of Artifact Operationality | Yes | No reduction | Clean |
| `ssn-system:OperatingRange` | `specifically dependent continuant OR Process Profile`, `prescribed by Artifact Design` | No | No reduction | Clean |
| `ssn-system:SystemCapability` | `specifically dependent continuant OR Process Profile`, `condition described by Performance Specification` | No | No reduction | Clean |
| `ssn-system:SystemProperty` | `specifically dependent continuant OR Process Profile`, `prescribed by Artifact Function Specification` | No | No reduction | Not tested as replacement |
| `ssn-system:OperatingProperty` | `specifically dependent continuant OR Process Profile`, `prescribed by Artifact Design` | No | No reduction | Not tested as replacement |

This is the strongest signal in this diagnostic: `SurvivalRange` behaves differently from both the similarly named range/capability mappings and from the function-style `SurvivalProperty` and `SystemLifetime` mappings.

## Relevant Source Context Summary

Local `imports/ssn-systems.ttl` evidence:

- `ssn-system:hasSurvivalProperty`
  - `rdfs:subPropertyOf ssn:hasProperty`
  - definition: relation from a `SurvivalRange` of a System to a `SurvivalProperty`.
- `ssn-system:hasSurvivalRange`
  - `rdfs:subPropertyOf ssn:hasProperty`
  - definition: relation from a System to a `SurvivalRange`.
- `ssn-system:SurvivalProperty`
  - `rdfs:subClassOf ssn:Property`
  - inverse `hasSurvivalProperty` all-values restriction to `ssn-system:SurvivalRange`
  - inverse `hasSurvivalProperty` minimum-cardinality restriction.
- `ssn-system:SurvivalRange`
  - `rdfs:subClassOf ssn:Property`
  - `hasSurvivalProperty` all-values restriction to `ssn-system:SurvivalProperty`
  - `inCondition` all-values restriction to `ssn-system:Condition`
  - inverse `hasSurvivalRange` all-values restriction to `ssn:System`
  - `inCondition` minimum-cardinality restriction.
- `ssn-system:SystemLifetime`
  - `rdfs:subClassOf ssn-system:SurvivalProperty`.

Source package sizes used in this diagnostic:

| Source group | Triple count |
| --- | ---: |
| `SurvivalRange` source package | 32 |
| `hasSurvivalRange` source package | 15 |
| `hasSurvivalProperty` source package | 20 |
| `SurvivalRange` restrictions only | 17 |
| restrictions mentioning `SurvivalRange` | 26 |
| source axioms using `ssn:hasProperty` | 14 |
| source axioms involving `ssn:Property` | 39 |
| source axioms involving `ssn:System` | 80 |
| all core `ssn:` source context | 204 |

## Remaining Non-Sample-Relationship `sosa:` Mapping Inventory

B2 removes the targeted core reducer subjects, but leaves 27 non-Sample-Relationship `sosa:` mapping subjects:

| Mapping group | Count |
| --- | ---: |
| Remaining non-sample `sosa:` subjects | 27 |
| Remaining `sosa:` direct class mappings | 5 |
| Remaining `sosa:` direct property mappings | 11 |
| Remaining `sosa:` property-chain mappings | 3 |
| Remaining `sosa:` restriction-style mappings | 6 |

Inventory of remaining non-sample `sosa:` mapping subjects:

| Subject | Mapping type | Target summary |
| --- | --- | --- |
| `sosa:ActuatableProperty` | direct class + restriction-style | `bfo:BFO_0000020`, `bfo:BFO_0000132`, `bfo:BFO_0000144`, `bfo:BFO_0000197`, `sosa:FeatureOfInterest` |
| `sosa:Actuation` | other | `cco:ont00000228`, `sosa:ActuatableProperty`, `sosa:actsOnProperty` |
| `sosa:Actuator` | direct class + restriction-style | `bfo:BFO_0000017`, `bfo:BFO_0000040`, `bfo:BFO_0000054`, `bfo:BFO_0000196`, `cco:ont00001787`, `sosa:Actuation` |
| `sosa:FeatureOfInterest` | other | `bfo:BFO_0000015`, `bfo:BFO_0000040`, `cco:ont00000345`, `cco:ont00001936`, `sosa:Actuation`, `sosa:Sampling`, `sosa:isFeatureOfInterestOf` |
| `sosa:ObservableProperty` | direct class + restriction-style | `bfo:BFO_0000020`, `bfo:BFO_0000132`, `bfo:BFO_0000144`, `bfo:BFO_0000197`, `sosa:FeatureOfInterest` |
| `sosa:Observation` | direct class + restriction-style | `cco:ont00000037`, `cco:ont00000228`, `cco:ont00000345`, `cco:ont00001777` |
| `sosa:Platform` | other | `bfo:BFO_0000040`, `sosa:hosts`, `ssn:System` |
| `sosa:Procedure` | direct class + restriction-style | `bfo:BFO_0000015`, `cco:ont00000965`, `cco:ont00001942` |
| `sosa:Result` | other | `bfo:BFO_0000040`, `cco:ont00000958`, `cco:ont00001816`, `sosa:Actuation`, `sosa:Observation`, `sosa:Sampling` |
| `sosa:Sample` | other | `bfo:BFO_0000040`, `cco:ont00001936`, `sosa:Sampling` |
| `sosa:Sampler` | other | `bfo:BFO_0000017`, `bfo:BFO_0000040`, `bfo:BFO_0000054`, `bfo:BFO_0000196`, `cco:ont00001787`, `sosa:Sampling` |
| `sosa:Sampling` | other | `cco:ont00000228`, `cco:ont00001920`, `cco:ont00001986`, `sosa:Procedure`, `sosa:Sample` |
| `sosa:actsOnProperty` | direct property | `cco:ont00001834` |
| `sosa:hasResult` | direct property | `cco:ont00001986` |
| `sosa:hasSample` | property chain | `bfo:BFO_0000084`, `cco:ont00001873` |
| `sosa:isActedOnBy` | direct property | `cco:ont00001886` |
| `sosa:isFeatureOfInterestOf` | other | none |
| `sosa:isHostedBy` | property chain | `bfo:BFO_0000055`, `bfo:BFO_0000056`, `bfo:BFO_0000197` |
| `sosa:isResultOf` | direct property | `cco:ont00001816` |
| `sosa:isSampleOf` | property chain | `bfo:BFO_0000101`, `cco:ont00001938` |
| `sosa:madeActuation` | direct property | `cco:ont00001787` |
| `sosa:madeByActuator` | direct property | `cco:ont00001833` |
| `sosa:madeBySampler` | direct property | `cco:ont00001833` |
| `sosa:madeObservation` | direct property | `cco:ont00001787` |
| `sosa:madeSampling` | direct property | `cco:ont00001787` |
| `sosa:observes` | direct property | `ssn:forProperty` |
| `sosa:usedProcedure` | direct property | `cco:ont00001920` |

## Variant Summary Table

Result labels:

- `baseline 8`: the full 8-class M2 unsat set.
- `systems trio`: `BatteryLifetime`, `SurvivalProperty`, `SystemLifetime`.
- `clean`: HermiT returned 0, a reasoned output was produced, and `owl:Nothing` count was 0.

| Variant | Temporary edit | Triples | Return code | Result |
| --- | --- | ---: | ---: | --- |
| A | Full M2 baseline | 15514 | 1 | baseline 8 |
| B | B2 targeted core reducer subjects removed | 15477 | 1 | systems trio |
| C | B2 minus `SurvivalRange` class mapping | 15440 | 0 | clean |
| D1 | B2 minus `OperatingRange` class mapping | 15461 | 1 | systems trio |
| D2 | B2 minus `SystemCapability` class mapping | 15461 | 1 | systems trio |
| D3 | B2 minus `SurvivalProperty` class mapping | 15440 | 1 | systems trio |
| D4 | B2 minus `SystemLifetime` class mapping | 15440 | 1 | systems trio |
| D5 | B2 minus `SystemProperty` class mapping | 15461 | 1 | systems trio |
| D6 | B2 minus `OperatingProperty` class mapping | 15461 | 1 | systems trio |
| E1 | B2 minus `SurvivalRange` + `SurvivalProperty` mappings | 15403 | 0 | clean |
| E2 | B2 minus `SurvivalRange` + `SystemLifetime` mappings | 15403 | 0 | clean |
| E3 | B2 minus `SurvivalRange` + `SurvivalProperty` + `SystemLifetime` mappings | 15366 | 0 | clean |
| E4 | B2 minus identifiable range/capability function-style mappings | 15366 | 0 | clean |
| F1 | B2 minus `SurvivalRange` source package | 15472 | 1 | systems trio |
| F2 | B2 minus `hasSurvivalRange` source package | 15471 | 1 | systems trio |
| F3 | B2 minus `hasSurvivalProperty` source package | 15471 | 0 | clean |
| F4 | B2 minus `SurvivalRange` restrictions only | 15477 | 1 | systems trio |
| F5 | B2 minus source restrictions mentioning `SurvivalRange` | 15477 | 1 | systems trio |
| G1 | B2 minus all remaining non-sample `sosa:` mappings | 15204 | 0 | clean |
| G2 | B2 minus remaining `sosa:` direct class mappings | 15373 | 1 | systems trio |
| G3 | B2 minus remaining `sosa:` direct property mappings | 15466 | 1 | systems trio |
| G4 | B2 minus remaining `sosa:` property chains | 15459 | 1 | systems trio |
| G5 | B2 minus remaining `sosa:` restriction-style mappings | 15364 | 1 | systems trio |
| G6 | B2 minus remaining `sosa:` class + property mappings | 15362 | 1 | systems trio |
| G7 | B2 minus remaining `sosa:` class + chain mappings | 15355 | 1 | systems trio |
| G8 | B2 minus remaining `sosa:` property + chain mappings | 15448 | 1 | systems trio |
| G9 | B2 minus remaining `sosa:` class + property + chain mappings | 15344 | 1 | systems trio |
| G10 | B2 minus non-sample `sosa:` direct class mappings | 15373 | 1 | systems trio |
| G11 | B2 minus non-sample `sosa:` direct property mappings | 15466 | 1 | systems trio |
| G12 | B2 minus non-sample `sosa:` property chains | 15459 | 1 | systems trio |
| G13 | B2 minus non-sample `sosa:` restriction-style mappings | 15373 | 1 | systems trio |
| G14 | B2 minus non-sample `sosa:` mappings except direct class mappings | 15308 | 0 | clean |
| G15 | B2 minus non-sample `sosa:` mappings except direct property mappings | 15215 | 0 | clean |
| G16 | B2 minus non-sample `sosa:` mappings except chains | 15222 | 0 | clean |
| G17 | B2 minus non-sample `sosa:` mappings except restrictions | 15308 | 0 | clean |
| H1 | B2 minus `ssn:Property` source package | 15469 | 1 | systems trio |
| H2 | B2 minus `ssn:System` source package | 15467 | 1 | systems trio |
| H3 | B2 minus source axioms using `ssn:hasProperty` | 15471 | 0 | clean |
| H4 | B2 minus source axioms involving `ssn:Property` | 15469 | 1 | systems trio |
| H5 | B2 minus source axioms involving `ssn:System` | 15467 | 1 | systems trio |
| H6 | B2 minus all core `ssn:` source context | 15357 | 0 | clean |
| I0 | H5-style clean base | 14630 | 0 | clean |
| I1 | H5 + broad `ssn:` source context | 14833 | 0 | clean |
| I2 | H5 + broad `ssn:` source context + non-sample `sosa:` mappings | 15110 | 1 | systems trio |
| I3 | H5 + all core source context + non-sample `sosa:` mappings | 15404 | 1 | systems trio |
| I4 | H5 without `SurvivalRange` mapping + `ssn:` source + non-sample `sosa:` mappings | 15073 | 0 | clean |
| I5 | H5 with only `SurvivalRange` system mapping + `ssn:` source + non-sample `sosa:` mappings | 14499 | 1 | systems trio |
| I6 | H5 with only `OperatingRange` replacing `SurvivalRange` | 14478 | 0 | clean |
| I7 | H5 with only `SystemCapability` replacing `SurvivalRange` | 14478 | 0 | clean |
| I8 | H5 with only `SurvivalProperty` replacing `SurvivalRange` | 14499 | 0 | clean |
| I9 | H5 with only `SystemLifetime` replacing `SurvivalRange` | 14499 | 0 | clean |

## B2 Reproduction And SurvivalRange Removal Result

B2 reproduced exactly the SSN Systems trio:

```text
ssn-system:BatteryLifetime
ssn-system:SurvivalProperty
ssn-system:SystemLifetime
```

Removing only the active `ssn-system:SurvivalRange` class mapping from B2 produced a HermiT-clean graph with `owl:Nothing` count 0. Removing any single comparable class mapping did not reduce the trio.

This makes `SurvivalRange` a specific high-impact dependency in the tested B2 context.

## Comparable Mapping Removal Results

The one-at-a-time comparable mapping removals did not behave like `SurvivalRange`.

- Removing `OperatingRange`: no reduction.
- Removing `SystemCapability`: no reduction.
- Removing `SurvivalProperty`: no reduction.
- Removing `SystemLifetime`: no reduction.
- Removing `SystemProperty`: no reduction.
- Removing `OperatingProperty`: no reduction.

Pair/group removals that included `SurvivalRange` were clean, but they did not improve on removing `SurvivalRange` alone. The identifiable function-style group was clean because it included `SurvivalRange`.

## SurvivalRange Source-Context Results

The source-side tests distinguish the class mapping from the local source restrictions.

- Removing the `SurvivalRange` source package did not reduce the systems trio.
- Removing the `hasSurvivalRange` source package did not reduce the systems trio.
- Removing the `hasSurvivalProperty` source package cleared the systems trio.
- Removing `SurvivalRange` restrictions only did not reduce the systems trio.
- Removing source restrictions mentioning `SurvivalRange` did not reduce the systems trio.

This suggests that the source-side dependency is not the explicit `SurvivalRange` restriction nodes alone. The `hasSurvivalProperty` source package and the broader `ssn:hasProperty` source relation are the higher-impact source-side pieces.

## `sosa:` Mapping Subgroup Results

Removing all remaining non-Sample-Relationship `sosa:` mappings from B2 cleared the systems trio.

However, no single tested `sosa:` mapping category cleared the trio:

- direct class mappings alone: no reduction;
- direct property mappings alone: no reduction;
- property-chain mappings alone: no reduction;
- restriction-style mappings alone: no reduction;
- class + property mappings: no reduction;
- class + chain mappings: no reduction;
- property + chain mappings: no reduction;
- class + property + chain mappings: no reduction.

The variants that removed "all non-sample `sosa:` mappings except one category" were clean. That means the dependency appears distributed across the remaining non-sample `sosa:` mapping set rather than isolated to one category in this diagnostic.

## `ssn:` Source-Context Subgroup Results

Removing all core `ssn:` source context from B2 cleared the systems trio.

Smaller source-context tests showed:

- removing only the `ssn:Property` source package: no reduction;
- removing only the `ssn:System` source package: no reduction;
- removing source axioms using `ssn:hasProperty`: clean;
- removing source axioms involving `ssn:Property`: no reduction;
- removing source axioms involving `ssn:System`: no reduction.

This points to the `ssn:hasProperty` source relation package as a smaller high-impact source-side dependency.

## Reconstruction Results

The reconstruction variants are the most informative part of this diagnostic.

Starting from a clean H5-style base:

- H5 base alone was clean.
- H5 + broad `ssn:` source context was clean.
- H5 + broad `ssn:` source context + remaining non-sample `sosa:` mappings reproduced the systems trio.
- H5 + all core source context + remaining non-sample `sosa:` mappings also reproduced the systems trio.
- H5 without `SurvivalRange` mapping + broad `ssn:` source context + non-sample `sosa:` mappings was clean.
- H5 with only the `SurvivalRange` system mapping + broad `ssn:` source context + non-sample `sosa:` mappings reproduced the systems trio.
- Replacing `SurvivalRange` with only `OperatingRange`, `SystemCapability`, `SurvivalProperty`, or `SystemLifetime` was clean.

This strongly suggests that `SurvivalRange` is specifically required in the tested reconstruction. It is not merely a marker for "some SSN Systems class mapping" or "some function-style mapping" in these variants.

## Cross-Check Against Deferred BFO Dependence Property Mappings

The diagnostic confirmed that the following direct BFO dependence property mappings remain inactive in the current graph:

| Deferred mapping check | Active? |
| --- | --- |
| `ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194` | No |
| `ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194` | No |
| `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194` | No |

This diagnostic does not implicate the already-deferred BFO dependence property mappings. The remaining SSN Systems trio persists without those direct BFO dependence property mappings active.

## Explanation Assessment

`SurvivalRange` appears specifically required in the tested mixed context:

- B2 minus `SurvivalRange` mapping is HermiT-clean.
- B2 minus any comparable single mapping remains unsatisfiable.
- H5 reconstruction with only `SurvivalRange` plus broad `ssn:` source context and non-sample `sosa:` mappings reproduces the trio.
- Comparable H5 reconstructions replacing `SurvivalRange` with `OperatingRange`, `SystemCapability`, `SurvivalProperty`, or `SystemLifetime` remain clean.

The dependency is mixed, not purely mapping-side or purely source-side:

- `SurvivalRange` mapping alone in the H5-style base is not enough; the reproduction needs broad `ssn:` source context and remaining non-sample `sosa:` mappings.
- Broad `ssn:` source context alone is not enough.
- Non-sample `sosa:` mappings plus broad `ssn:` source context are enough when `SurvivalRange` is present.
- Removing the `ssn:hasProperty` source axiom package clears the B2 trio.
- Removing the `hasSurvivalProperty` source package clears the B2 trio.
- Removing all remaining non-sample `sosa:` mappings clears the B2 trio, but no smaller tested `sosa:` category did so.

The evidence supports this narrower interpretation:

```text
SurvivalRange mapping expression
+ ssn:hasProperty / hasSurvivalProperty source context
+ distributed non-sample sosa mapping context
= HermiT reproduction of the SSN Systems trio
```

The evidence does not prove:

- that the source ontology restrictions are wrong;
- that the `SurvivalRange` mapping is semantically wrong;
- that a single `sosa:` mapping subject is the cause;
- that the already-deferred BFO dependence property mappings should be revisited.

## Recommendation

Do not make repo mapping changes from this diagnostic branch alone.

The next narrow branch should focus on `ssn-system:SurvivalRange` specifically, because it is the only tested comparable mapping that both clears the B2 trio when removed and reproduces the trio when isolated with the needed broader context.

Two reasonable next steps are:

1. A temporary fix-evaluation branch that defers only the active `SurvivalRange` class mapping in the repo and spreadsheet, then runs the standard validation suite and HermiT M2 baseline to quantify impact.
2. A deeper explanation branch that isolates the smallest subset of non-sample `sosa:` mappings needed with `SurvivalRange`, `ssn:hasProperty`, and `hasSurvivalProperty`.

The core SOSA/SSN 5-class cluster remains separate and should not be mixed into this SSN Systems follow-up.
