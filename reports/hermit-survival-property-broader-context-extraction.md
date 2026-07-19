# HermiT SurvivalProperty Broader-Context Extraction

## Scope

This diagnostic tests broader context dependencies for the remaining SSN Systems HermiT unsatisfiable-class cluster:

- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

No repository ontology mappings, spreadsheets, imports, source examples, generated/release artifacts, or existing reports were modified. Temporary graphs, ROBOT outputs, stdout/stderr captures, and the diagnostic JSON summary were written under:

`/tmp/ssn-to-bfo-hermit-survival-property-broader-context-extraction`

This is a report-only diagnostic. Temporary removals and additions identify interaction context; they do not by themselves prove that a source axiom or mapping axiom is wrong.

## Prior Context

`reports/hermit-survival-property-minimal-conflict-extraction.md` showed that small extracted graphs did not reproduce the SSN Systems trio. The smallest tested reproduction in that report was near-full Variant B2:

- full source/import graph plus current `SSN2BFO.ttl` mapping graph;
- sample cleanup applied;
- targeted core reducer subjects removed:
  - `sosa:Sensor`
  - `sosa:hosts`
  - `sosa:madeBySensor`
  - `sosa:observedProperty`
  - `ssn:hasInput`
  - `ssn:hasOutput`
- result: exactly the SSN Systems trio remained unsatisfiable.

This report starts from that B2 systems-only reproduction and subtracts or adds broader context groups to identify what additional source/import or mapping context is required.

## Method

Every full-graph variant was built from an M2-style temporary graph merging:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Every variant removed:

- all `owl:imports` triples;
- `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Each HermiT run used:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

- ROBOT: `ROBOT version 1.9.7`
- Java: `java version "22.0.2" 2024-07-16`

No tested variant reintroduced the sample simplicity blocker.

## B2 Systems-Only Reproduction

Variant B reproduced the systems-only control:

| Variant | Temporary graph | Triples | Return code | Reasoned output | `owl:Nothing` | Unsat count | Unsat set |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| A | Full M2 baseline. | 15,514 | 1 | no | n/a | 8 | core 5 plus systems trio |
| B | B2: targeted core reducer mapping subjects removed. | 15,477 | 1 | no | n/a | 3 | systems trio |

The B2 unsatisfiable classes were exactly:

- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

## Remaining Mapping/Source Context Inventory

Mapping group counts in B2 after the targeted core reducer subjects were removed:

| Mapping group | Count |
| --- | ---: |
| Remaining `sosa:` mapping subjects | 29 |
| Remaining `ssn:` core mapping subjects, excluding `ssn-system:` | 15 |
| Remaining core direct class mapping subjects | 7 |
| Remaining core direct property mapping subjects | 18 |
| Remaining core property-chain mapping subjects | 4 |
| Remaining core restriction-style mapping subjects | 6 |
| Active SSN Systems direct class mapping subjects | 21 |
| Active SSN Systems direct property mapping subjects | 4 |
| Active survival-related SSN Systems mapping subjects | 3 |
| Active broader SSN Systems property/capability mapping subjects | 7 |

Additional `sosa:` subgroup counts:

| `sosa:` subgroup | Count |
| --- | ---: |
| Direct class mappings | 5 |
| Direct property mappings | 11 |
| Property-chain mappings | 3 |
| Restriction-style mappings | 6 |
| Sample Relationship mappings | 2 |
| Non-Sample-Relationship mappings | 27 |

Source group triple counts used in B2 source-side subtraction:

| Source group | Removed triples |
| --- | ---: |
| `ssn:Property` source package | 39 |
| `ssn:System` source package | 80 |
| `sosa:ObservableProperty` source package | 28 |
| `sosa:FeatureOfInterest` source package | 48 |
| `sosa:Observation` source package | 68 |
| `sosa:Sensor` source package | 31 |
| `ssn:Input` / `ssn:Output` source package | 38 |
| All `sosa:` source context from `imports/ssn.ttl` | 44 effective B2 triples |
| All `ssn:` core source context from `imports/ssn.ttl` | 120 effective B2 triples |
| All `sosa:` / `ssn:` core source context from `imports/ssn.ttl` | 164 effective B2 triples |
| `SurvivalProperty` source package | 32 |
| `SurvivalRange` source package | 32 |
| `SystemProperty` source package | 119 |
| `OperatingProperty` source package | 32 |
| `OperatingRange` source package | 32 |
| `SystemCapability` source package | 36 |
| SSN Systems restrictions involving `ssn:Property` | 4 |
| SSN Systems restrictions using `hasProperty` family predicates | 69 |

## Variant Summary Table

The shorthand "systems trio" means:

`ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime`.

The shorthand "core 5" means:

`sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus`.

| Variant | Temporary graph construction/removal | Triples | Return code | Reasoned output | `owl:Nothing` | Unsat count | Unsat set |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| A | Full M2 baseline. | 15,514 | 1 | no | n/a | 8 | core 5 plus systems trio |
| B | B2 systems-only reproduction. | 15,477 | 1 | no | n/a | 3 | systems trio |
| C1 | B2 minus all remaining `sosa:` mappings. | 15,194 | 0 | yes | 0 | 0 | none |
| C2 | B2 minus all remaining `ssn:` core mappings. | 15,421 | 1 | no | n/a | 3 | systems trio |
| C3 | B2 minus remaining core direct class mappings. | 15,371 | 1 | no | n/a | 3 | systems trio |
| C4 | B2 minus remaining core direct property mappings. | 15,459 | 1 | no | n/a | 3 | systems trio |
| C5 | B2 minus remaining core property-chain mappings. | 15,454 | 1 | no | n/a | 3 | systems trio |
| C6 | B2 minus remaining core restriction-style mappings. | 15,364 | 1 | no | n/a | 3 | systems trio |
| D1 | B2 minus `ssn:Property` source package. | 15,469 | 1 | no | n/a | 3 | systems trio |
| D2 | B2 minus `ssn:System` source package. | 15,467 | 1 | no | n/a | 3 | systems trio |
| D3 | B2 minus `sosa:ObservableProperty` source package. | 15,475 | 1 | no | n/a | 3 | systems trio |
| D4 | B2 minus `sosa:FeatureOfInterest` source package. | 15,473 | 1 | no | n/a | 3 | systems trio |
| D5 | B2 minus `sosa:Observation` source package. | 15,476 | 1 | no | n/a | 3 | systems trio |
| D6 | B2 minus `sosa:Sensor` source package. | 15,475 | 1 | no | n/a | 3 | systems trio |
| D7 | B2 minus `ssn:Input` / `ssn:Output` source package. | 15,469 | 1 | no | n/a | 3 | systems trio |
| D8 | B2 minus all `sosa:` source context from `imports/ssn.ttl`. | 15,433 | 1 | no | n/a | 3 | systems trio |
| D9 | B2 minus all `ssn:` core source context from `imports/ssn.ttl`. | 15,357 | 0 | yes | 0 | 0 | none |
| D10 | B2 minus all `sosa:` / `ssn:` core source context from `imports/ssn.ttl`. | 15,313 | 0 | yes | 0 | 0 | none |
| E1 | B2 minus all active SSN Systems direct class mappings. | 14,829 | 0 | yes | 0 | 0 | none |
| E2 | B2 minus all active SSN Systems direct property mappings. | 15,473 | 1 | no | n/a | 3 | systems trio |
| E3 | B2 minus active mappings involving `SurvivalProperty`, `SystemLifetime`, and `SurvivalRange`. | 15,366 | 0 | yes | 0 | 0 | none |
| E4 | B2 minus broader active mappings involving `SystemProperty`, `OperatingProperty`, `OperatingRange`, `SurvivalRange`, `SystemCapability`, `SurvivalProperty`, `SystemLifetime`. | 15,302 | 0 | yes | 0 | 0 | none |
| F1 | B2 minus `SurvivalProperty` source package. | 15,461 | 1 | no | n/a | 1 | `ssn-system:SurvivalProperty` |
| F2 | B2 minus `SurvivalRange` source package. | 15,472 | 1 | no | n/a | 3 | systems trio |
| F3 | B2 minus `SystemProperty` source package. | 15,411 | 1 | no | n/a | 3 | systems trio |
| F4 | B2 minus `OperatingProperty` source package. | 15,462 | 1 | no | n/a | 3 | systems trio |
| F5 | B2 minus `OperatingRange` source package. | 15,472 | 1 | no | n/a | 3 | systems trio |
| F6 | B2 minus `SystemCapability` source package. | 15,472 | 1 | no | n/a | 3 | systems trio |
| F7 | B2 minus SSN Systems restrictions involving `ssn:Property`. | 15,477 | 1 | no | n/a | 3 | systems trio |
| F8 | B2 minus SSN Systems restrictions using `hasProperty`, `hasSurvivalProperty`, `hasOperatingProperty`, `hasSystemProperty`. | 15,477 | 1 | no | n/a | 3 | systems trio |
| G0 | H5-style clean base: all `ssn-systems` source, all active SSN Systems direct class mappings, full CCO/BFO, no core mappings. | 14,630 | 0 | yes | 0 | 0 | none |
| G1 | G0 plus `ssn:` source context. | 14,833 | 0 | yes | 0 | 0 | none |
| G2 | G0 plus `sosa:` source context. | 14,928 | 0 | yes | 0 | 0 | none |
| G3 | G0 plus remaining `ssn:` core mappings. | 14,696 | 0 | yes | 0 | 0 | none |
| G4 | G0 plus remaining `sosa:` mappings. | 14,917 | 0 | yes | 0 | 0 | none |
| G5 | G0 plus remaining property-chain mappings. | 14,654 | 0 | yes | 0 | 0 | none |
| G6 | G0 plus remaining restriction-style mappings. | 14,744 | 0 | yes | 0 | 0 | none |
| G7 | G0 plus `ssn:` source context and remaining `ssn:` core mappings. | 14,889 | 0 | yes | 0 | 0 | none |
| G8 | G0 plus `sosa:` source context and remaining `sosa:` mappings. | 15,211 | 0 | yes | 0 | 0 | none |
| G9 | G0 plus all core source context and all remaining core mappings. | 15,470 | 1 | no | n/a | 3 | systems trio |
| G10 | G0 plus all core source context only. | 15,131 | 0 | yes | 0 | 0 | none |
| G11 | G0 plus all remaining core mappings only. | 14,983 | 0 | yes | 0 | 0 | none |
| G12 | G0 plus all core source context and remaining `sosa:` mappings only. | 15,414 | 1 | no | n/a | 3 | systems trio |

## B2 Subtraction Results

Mapping-side subtraction:

- Removing all remaining `sosa:` mappings from B2 cleared the systems trio.
- Removing all remaining `ssn:` core mappings did not reduce the systems trio.
- Removing remaining core direct class, direct property, property-chain, or restriction-style mappings by those broad categories did not reduce the systems trio.

Source-side subtraction:

- Removing individual source packages for `ssn:Property`, `ssn:System`, `sosa:ObservableProperty`, `sosa:FeatureOfInterest`, `sosa:Observation`, `sosa:Sensor`, or `ssn:Input` / `ssn:Output` did not reduce the systems trio.
- Removing all `sosa:` source context from `imports/ssn.ttl` did not reduce the systems trio.
- Removing all `ssn:` core source context from `imports/ssn.ttl` cleared the systems trio.
- Removing all `sosa:` / `ssn:` core source context also cleared the systems trio.

SSN Systems controls:

- Removing all active SSN Systems direct class mappings cleared the systems trio.
- Removing active SSN Systems direct property mappings did not reduce the trio.
- Removing the survival-related active mappings for `SurvivalProperty`, `SystemLifetime`, and `SurvivalRange` cleared the trio.
- Removing the broader active SSN Systems property/capability mapping group also cleared the trio.
- Removing the `SurvivalProperty` source package reduced the trio to only `SurvivalProperty`.
- Removing other tested SSN Systems source packages did not reduce the trio.

## Group-Addition Reconstruction Results

The H5-style base was clean:

- all `ssn-systems` source;
- all active SSN Systems direct class mappings;
- full local CCO/BFO;
- no core SOSA/SSN mappings.

Additions that remained HermiT-clean:

- `ssn:` source context alone;
- `sosa:` source context alone;
- remaining `ssn:` core mappings alone;
- remaining `sosa:` mappings alone;
- remaining property-chain mappings alone;
- remaining restriction-style mappings alone;
- `ssn:` source context plus remaining `ssn:` mappings;
- `sosa:` source context plus remaining `sosa:` mappings;
- all core source context alone;
- all remaining core mappings alone.

Additions that reproduced the systems trio:

- all core source context plus all remaining core mappings;
- all core source context plus remaining `sosa:` mappings only.

This means the reproducing addition does not require remaining `ssn:` core mappings, but it does require broader core source context plus remaining `sosa:` mappings.

## Focused Candidate Dependency Results

Focused `sosa:` mapping subgroup removals from B2:

| Variant | Temporary removal from B2 | Result |
| --- | --- | --- |
| H14 | Remaining `sosa:` direct class mappings only | systems trio remains |
| H15 | Remaining `sosa:` direct property mappings only | systems trio remains |
| H16 | Remaining `sosa:` property-chain mappings only | systems trio remains |
| H17 | Remaining `sosa:` restriction-style mappings only | systems trio remains |
| H18 | Remaining `sosa:` class plus property mappings | systems trio remains |
| H19 | Remaining `sosa:` class plus chain mappings | systems trio remains |
| H20 | Remaining `sosa:` property plus chain mappings | systems trio remains |
| H21 | Remaining `sosa:` class, property, and chain mappings | systems trio remains |
| H22 | `sosa-rel:` Sample Relationship mappings only | systems trio remains |
| H23 | Remaining non-Sample-Relationship `sosa:` mappings | clean |
| H24 | Remaining `sosa:` mappings except direct class mappings | clean |
| H25 | Remaining `sosa:` mappings except direct property mappings | clean |
| H26 | Remaining `sosa:` mappings except property-chain mappings | clean |
| H27 | Remaining `sosa:` mappings except restriction-style mappings | clean |

Interpretation:

- The dependency is not isolated to a single tested `sosa:` mapping subtype.
- Removing only one `sosa:` subtype does not reduce the trio.
- Removing the non-Sample-Relationship `sosa:` group clears the trio.
- Removing all remaining `sosa:` mappings except any one subtype also clears the trio.
- This points to a distributed `sosa:` mapping-side dependency, not a single obvious `sosa:` category.

Focused SSN Systems mapping/source removals from B2:

| Variant | Temporary removal from B2 | Result |
| --- | --- | --- |
| H1 | `SystemProperty` mapping | systems trio remains |
| H2 | `OperatingProperty` mapping | systems trio remains |
| H3 | `OperatingRange` mapping | systems trio remains |
| H4 | `SurvivalRange` mapping | clean |
| H5 | `SystemCapability` mapping | systems trio remains |
| H6 | `SurvivalProperty` mapping | systems trio remains |
| H7 | `SystemLifetime` mapping | systems trio remains |
| H8 | `SystemProperty` source package | systems trio remains |
| H9 | `OperatingProperty` source package | systems trio remains |
| H10 | `OperatingRange` source package | systems trio remains |
| H11 | `SurvivalRange` source package | systems trio remains |
| H12 | `SystemCapability` source package | systems trio remains |
| H13 | `SurvivalProperty` source package | only `SurvivalProperty` remains unsatisfiable |

The strongest single mapping-side reducer in this focused set was the active `ssn-system:SurvivalRange` class mapping. Removing it from B2 cleared the systems trio. This does not prove the mapping is wrong; it identifies it as a high-impact dependency in the broader context.

The smallest tested graph that still reproduced the systems trio was H21, with 15,344 triples, where remaining `sosa:` class, property, and property-chain mappings were removed but the systems trio persisted. This is smaller than B2 but still a near-full graph, not a minimal extracted conflict.

## Cross-Check Against Deferred BFO Dependence Property Mappings

The current graph still has these direct BFO dependence mappings deferred:

| Deferred mapping check | Active in `SSN2BFO.ttl`? |
| --- | --- |
| `ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194` | no |
| `ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194` | no |
| `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194` | no |

This diagnostic gives no new reason to revisit those deferred direct BFO dependence property mappings. The remaining systems trio is still driven through class/source context and active class mappings, not active direct BFO dependence property mappings.

## Explanation Assessment

What context appears required for the systems trio:

- B2 requires broader context beyond the survival-only extracted graph.
- Removing all remaining `sosa:` mappings clears the systems trio.
- Removing all `ssn:` core source context clears the systems trio.
- In reconstruction, all core source context plus remaining `sosa:` mappings reproduces the trio.
- Remaining `sosa:` mappings alone do not reproduce the trio.
- Core source context alone does not reproduce the trio.

This points to a mixed dependency:

- mapping-side: remaining `sosa:` mappings, especially the non-Sample-Relationship group as a whole;
- source-side: broad `ssn:` core source context;
- SSN Systems side: active SSN Systems class mappings, with `SurvivalRange` emerging as a high-impact individual class mapping in B2.

Which removals clear or reduce the trio:

- clear: all remaining `sosa:` mappings;
- clear: all `ssn:` core source context;
- clear: all active SSN Systems direct class mappings;
- clear: survival-related mappings as a group;
- clear: broader SSN Systems property/capability mappings as a group;
- clear: individual `SurvivalRange` class mapping;
- reduce to only `SurvivalProperty`: `SurvivalProperty` source package.

Which removals do nothing:

- remaining `ssn:` core mappings;
- remaining core direct class, direct property, property-chain, or restriction-style mappings by type;
- tested individual core source packages;
- active SSN Systems direct property mappings;
- individual `SystemProperty`, `OperatingProperty`, `OperatingRange`, `SystemCapability`, `SurvivalProperty`, or `SystemLifetime` mappings;
- tested SSN Systems source packages other than `SurvivalProperty`.

Which additions reproduce the trio:

- H5-style clean base plus all core source context and all remaining core mappings;
- H5-style clean base plus all core source context and remaining `sosa:` mappings only.

Is the missing dependency mapping-side, source-side, or mixed?

It is mixed. The trio was not reproduced by source context alone or mapping context alone. It appeared when broad core source context was combined with remaining `sosa:` mappings, and it disappeared from B2 when either all remaining `sosa:` mappings or all `ssn:` core source context were removed.

Are the already-deferred direct BFO dependence property mappings implicated?

No. They remain inactive, and the high-impact controls involve class mappings and source/class context, not those deferred direct property mappings.

## Recommendation

Do not make repository mapping changes in this branch.

The evidence is stronger than the previous extraction but still not enough for a direct ontology fix. The next branch should be another explanation branch, focused on the new high-impact dependency:

`review/hermit-survival-range-sosa-context-explanation`

That branch should start from B2 and test:

- the active `ssn-system:SurvivalRange` class mapping against the broad `ssn:` source context;
- the active `SurvivalRange`, `SurvivalProperty`, and `SystemLifetime` class mappings with and without the remaining non-Sample-Relationship `sosa:` mappings;
- smaller groups inside the remaining non-Sample-Relationship `sosa:` mappings;
- whether the `SurvivalRange` mapping is merely a marker for the broader function/realization pattern shared by other SSN Systems class mappings.

A fix branch deferring a specific class mapping is not yet justified. The core SOSA/SSN cluster should remain separate from this SSN Systems explanation track.
