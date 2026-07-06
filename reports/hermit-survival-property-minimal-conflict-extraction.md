# HermiT SurvivalProperty Minimal-Conflict Extraction

## Scope

This diagnostic tries to extract a smaller temporary ontology that reproduces the remaining SSN Systems HermiT unsatisfiable-class cluster:

- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

No repository ontology mappings, spreadsheets, imports, source examples, generated/release artifacts, or existing reports were modified. All temporary graphs, ROBOT outputs, stdout/stderr captures, and the diagnostic JSON summary were written under:

`/tmp/ssn-to-bfo-hermit-survival-property-minimal-conflict-extraction`

This is a report-only diagnostic. A temporary graph that reproduces unsatisfiability identifies an interaction context, not by itself an incorrect source axiom or mapping axiom.

## Prior Context

`reports/hermit-survival-property-source-restriction-explanation.md` showed:

- the current M2-style baseline has 8 HermiT unsats;
- the SSN Systems trio is separable from the 5 core SOSA/SSN unsats;
- active SSN Systems direct property mappings are not implicated in the current post-defer baseline;
- `BatteryLifetime` has no active direct mapping;
- `SurvivalProperty` and `SystemLifetime` have active class mappings;
- `BatteryLifetime` and `SystemLifetime` are source subclasses of `SurvivalProperty`;
- explicit `SurvivalProperty` restriction-node removals alone do not reduce the baseline;
- the broader `SurvivalProperty` source axiom package alone removes `BatteryLifetime` and `SystemLifetime`, but leaves `SurvivalProperty`;
- the broader `SurvivalProperty` source axiom package plus the active `SurvivalProperty` class mapping removes the full SSN Systems trio.

This report tests whether that interaction can be reproduced in a smaller extracted graph.

## Method

Full-graph controls used the same M2-style temporary merge:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Every full-graph and extracted-graph variant removed:

- all `owl:imports` triples;
- `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Each HermiT run used this command pattern:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

- ROBOT: `ROBOT version 1.9.7`
- Java: `java version "22.0.2" 2024-07-16`

No variant reintroduced the sample simplicity blocker.

## Extracted Source-Side Cluster

The extracted source-side cluster had 94 triples.

It included source-side packages for:

- `ssn-system:SurvivalProperty`
- `ssn-system:BatteryLifetime`
- `ssn-system:SystemLifetime`
- `ssn-system:SurvivalRange`
- `ssn-system:hasSurvivalProperty`
- immediately referenced support terms such as `ssn-system:hasSurvivalRange`, `ssn-system:inCondition`, `ssn-system:Condition`, `ssn:System`, `ssn:Property`, and `ssn:hasProperty`.

Source-side summary:

| Entity | Label | Subject package triples | Incoming package triples | Direct subclass/subproperty evidence |
| --- | --- | ---: | ---: | --- |
| `ssn-system:BatteryLifetime` | Battery Lifetime | 6 | 0 | `rdfs:subClassOf ssn-system:SurvivalProperty` |
| `ssn-system:SurvivalProperty` | Survival Property | 16 | 16 | `rdfs:subClassOf ssn:Property` plus two blank-node restrictions |
| `ssn-system:SystemLifetime` | System Lifetime | 6 | 0 | `rdfs:subClassOf ssn-system:SurvivalProperty` |
| `ssn-system:SurvivalRange` | Survival Range | 23 | 9 | `rdfs:subClassOf ssn:Property` plus four blank-node restrictions |
| `ssn-system:hasSurvivalProperty` | has survival property | 6 | 14 | source subproperty/comment/label package |

The source-only extracted cluster was HermiT-clean.

## Extracted Mapping-Side Cluster

The active mapping-side extraction confirmed:

| Source term | Active direct mapping? | Mapping-expression triples | Notes |
| --- | --- | ---: | --- |
| `ssn-system:BatteryLifetime` | no | 0 | No active direct mapping was found. |
| `ssn-system:SurvivalProperty` | yes | 38 | Active class mapping expression. |
| `ssn-system:SystemLifetime` | yes | 38 | Active class mapping expression. |
| `ssn-system:SurvivalRange` | yes | 38 | Relevant nearby active class mapping expression, tested as an extra control. |

The `SurvivalProperty` mapping expression references:

- `bfo:BFO_0000034` / function
- `bfo:BFO_0000054` / has realization
- `bfo:BFO_0000015` / process
- `bfo:BFO_0000055` / realizes
- `cco:ont00001819` / caused by
- `cco:ont00000177` / Affordance
- `cco:ont00001920` / prescribed by
- `cco:ont00000319` / Artifact Design

The `SystemLifetime` mapping expression references the same targets plus:

- `cco:ont00001213` / Stasis of Artifact Operationality

## Extracted BFO/CCO Target Context

Target-context layers were extracted from `imports/cco.ttl` for the BFO/CCO identifiers used by the active `SurvivalProperty`, `SystemLifetime`, and `SurvivalRange` mapping expressions.

| Target context layer | Triples |
| --- | ---: |
| Target declarations | 18 |
| Target superclass chains | 84 |
| Target domain/range/subproperty axioms | 17 |
| Target disjointness axioms | 23 |
| Target property characteristics/inverses | 25 |
| Full local CCO/BFO import context | 13,649 |

The full local CCO/BFO context was also tested because the smaller target-context layers did not reproduce the cluster.

## Variant Summary Table

| Variant | Temporary graph construction or removal | Triples | Return code | Reasoned output | `owl:Nothing` | Unsat count | Unsat set |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| A | Full M2 baseline. | 15,514 | 1 | no | n/a | 8 | Core 5 plus systems trio |
| B | Full graph with all active core SOSA/SSN mapping subjects removed. | 15,138 | 0 | yes | 0 | 0 | none |
| B2 | Full graph with targeted core reducer subjects removed: `sosa:Sensor`, `sosa:hosts`, `sosa:madeBySensor`, `sosa:observedProperty`, `ssn:hasInput`, `ssn:hasOutput`. | 15,477 | 1 | no | n/a | 3 | systems trio |
| C | Source-only extracted cluster. | 94 | 0 | yes | 0 | 0 | none |
| D | Source cluster plus `SurvivalProperty` mapping expression and target declarations. | 149 | 0 | yes | 0 | 0 | none |
| E | Source cluster plus `SystemLifetime` mapping expression and target declarations. | 149 | 0 | yes | 0 | 0 | none |
| F | Source cluster plus both `SurvivalProperty` and `SystemLifetime` mapping expressions and target declarations. | 186 | 0 | yes | 0 | 0 | none |
| G1 | F, target declarations only. | 186 | 0 | yes | 0 | 0 | none |
| G2 | F plus target superclass chains. | 252 | 0 | yes | 0 | 0 | none |
| G3 | G2 plus target domain/range/subproperty axioms. | 260 | 0 | yes | 0 | 0 | none |
| G4 | G3 plus target disjointness axioms. | 283 | 0 | yes | 0 | 0 | none |
| G5 | G4 plus target property characteristics/inverses. | 296 | 0 | yes | 0 | 0 | none |
| G6 | Source cluster plus both mappings plus full CCO/BFO context. | 13,817 | 0 | yes | 0 | 0 | none |
| H1 | G6 plus `ssn:Property` immediate context. | 13,828 | 0 | yes | 0 | 0 | none |
| H2 | G6 with `SurvivalRange` restrictions explicitly included; equivalent to the base source cluster plus full CCO. | 13,817 | 0 | yes | 0 | 0 | none |
| H3 | Full CCO plus broader SSN Systems source hierarchy around `SystemProperty`, `OperatingProperty`, `SurvivalProperty`, `SystemCapability`, and `SurvivalRange`. | 13,913 | 0 | yes | 0 | 0 | none |
| H4 | H3 plus all active SSN Systems direct class mappings, no core SOSA/SSN mappings. | 14,500 | 0 | yes | 0 | 0 | none |
| H5 | All `ssn-systems` source plus all active SSN Systems direct class mappings and full CCO. | 14,630 | 0 | yes | 0 | 0 | none |
| I1 | Full M2 graph with only `SurvivalProperty` mapping expression removed. | 15,477 | 1 | no | n/a | 8 | baseline 8 |
| I2 | Full M2 graph with only `SystemLifetime` mapping expression removed. | 15,477 | 1 | no | n/a | 8 | baseline 8 |
| I3 | Full M2 graph with both `SurvivalProperty` and `SystemLifetime` mappings removed. | 15,440 | 1 | no | n/a | 8 | baseline 8 |
| I4 | Full M2 graph with broader `SurvivalProperty` source package removed. | 15,498 | 1 | no | n/a | 6 | core 5 plus `SurvivalProperty` |
| I5 | Full M2 graph with broader source package plus `SurvivalProperty` mapping removed. | 15,460 | 1 | no | n/a | 5 | core 5 |
| J1 | Source cluster plus `SurvivalRange` mapping expression and full CCO. | 13,780 | 0 | yes | 0 | 0 | none |
| J2 | Source cluster plus `SurvivalProperty`, `SurvivalRange`, and `SystemLifetime` mappings with full CCO. | 13,854 | 0 | yes | 0 | 0 | none |

For the table above:

- "core 5" means `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, and `ssn:Stimulus`;
- "systems trio" means `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, and `ssn-system:SystemLifetime`;
- "baseline 8" means both sets together.

## Source-Only Result

Variant C was HermiT-clean:

- return code: `0`;
- reasoned output: yes;
- `owl:Nothing` count: `0`;
- unsatisfiable classes: none.

The extracted SSN Systems source-side neighborhood alone does not reproduce the systems trio.

## Mapping-Expression Increment Results

Variants D-F were HermiT-clean:

- D: source cluster plus only the `SurvivalProperty` mapping expression;
- E: source cluster plus only the `SystemLifetime` mapping expression;
- F: source cluster plus both mapping expressions.

This means neither active mapping expression was independently problematic in the extracted source cluster with target declarations.

## Target-Context Increment Results

Variants G1-G6 progressively added target BFO/CCO context:

1. target declarations;
2. target superclass chains;
3. target domain/range/subproperty axioms;
4. target disjointness axioms;
5. target property characteristics/inverses;
6. full local CCO/BFO import context.

All G variants were HermiT-clean with `owl:Nothing` count `0`.

The SSN Systems trio was not reproduced by adding local BFO/CCO target context to the extracted source/mapping cluster.

## Source-Context Increment Results

Variants H1-H5 progressively added source context:

- `ssn:Property` immediate context;
- explicitly included `SurvivalRange` restrictions;
- broader SSN Systems source hierarchy around related classes;
- all active SSN Systems direct class mappings without core SOSA/SSN mappings;
- all local `ssn-systems` source plus all active SSN Systems direct class mappings and full CCO.

All H variants were HermiT-clean with `owl:Nothing` count `0`.

This is the main negative extraction result: even all local SSN Systems source plus all active SSN Systems class mappings and full CCO did not reproduce the trio without broader source/import and mapping context.

## Full-Graph Cross-Check Results

The full-graph cross-checks reproduced the previous focused findings:

- Removing only the `SurvivalProperty` mapping did not reduce the 8-class baseline.
- Removing only the `SystemLifetime` mapping did not reduce the 8-class baseline.
- Removing both mappings did not reduce the 8-class baseline.
- Removing the broader `SurvivalProperty` source package reduced 8 to 6 by removing `BatteryLifetime` and `SystemLifetime`, but left `SurvivalProperty`.
- Removing the broader source package plus the `SurvivalProperty` mapping reduced 8 to 5 by removing the full systems trio.

Two core-suppression controls were informative:

- Removing all active core SOSA/SSN mapping subjects made the full graph HermiT-clean.
- Removing only targeted core reducer subjects left exactly the systems trio.

The second control provides a systems-only full-graph reproduction, but it is still a near-full graph rather than a small minimal conflict extraction.

## Minimal Reproduction Result

No small extracted graph reproduced:

- `SurvivalProperty` unsat;
- `BatteryLifetime` plus `SystemLifetime` unsats;
- the full three-class SSN Systems trio.

The smallest tested graph that reproduced the full SSN Systems trio was the near-full graph in Variant B2:

- 15,477 triples;
- full source/import graph plus current mapping graph;
- targeted core reducer subjects removed to suppress the 5 core SOSA/SSN unsats;
- result: exactly `BatteryLifetime`, `SurvivalProperty`, and `SystemLifetime` unsatisfiable.

This means the tested minimal source/mapping/target extraction was too small. The trio appears to require broader imported and mapping context not captured by the focused `SurvivalProperty`/`SystemLifetime`/`SurvivalRange` extraction, even when full CCO and all SSN Systems class mappings are added.

## Explanation Assessment

What is now known:

- The source-only extracted cluster is HermiT-clean.
- The `SurvivalProperty` mapping expression is not independently HermiT-problematic in the extracted cluster.
- The `SystemLifetime` mapping expression is not independently HermiT-problematic in the extracted cluster.
- The two mapping expressions together remain HermiT-clean across all target-context layers, including full local CCO.
- Adding broader SSN Systems source context and all active SSN Systems direct class mappings still remains HermiT-clean.
- The full systems trio can be reproduced only in a near-full graph with targeted core reducers removed.

What is still not isolated:

- The additional broader source/import or mapping context needed to make the systems trio unsatisfiable.
- Whether that missing context is a specific remaining core mapping, a source restriction outside the survival-property neighborhood, or an interaction among several such axioms.

Whether `SurvivalProperty` mapping appears independently problematic:

- No. Removing it alone does not reduce the full baseline, and adding it to the extracted graph does not create unsatisfiability.

Whether `SystemLifetime` mapping appears independently problematic:

- No. Removing it alone does not reduce the full baseline, and adding it to the extracted graph does not create unsatisfiability.

Whether the problem requires broader SSN Systems class-mapping context:

- Broader SSN Systems class mappings are not sufficient by themselves in the extracted graphs.
- In the full graph, the systems trio survives targeted core suppression, so broader context outside the survival-only extraction is still required.

Whether the already-deferred direct BFO dependence property mappings are implicated:

- No. This diagnostic did not reintroduce or rely on those deferred mappings, and the systems trio persisted or disappeared according to class/source context rather than active direct BFO dependence property mappings.

## Recommendation

Do not make repository mapping changes in this branch.

The next step should be another extraction branch with broader context, not a fix branch deferring a specific class mapping yet. A useful next branch would be:

`review/hermit-survival-property-broader-context-extraction`

That branch should start from Variant B2, which reproduces exactly the systems trio, and then subtract or group the remaining active mapping/source context to identify which non-targeted core mapping or source package is required. In particular, compare:

- B2 minus remaining core SOSA/SSN mapping groups not already removed;
- B2 minus SSN deployment/core property mappings;
- B2 minus remaining SOSA class/property mappings;
- B2 minus broader `ssn:Property` and source hierarchy commitments.

Only after that narrower dependency is isolated should a fix branch consider deferring or revising a specific class mapping. The core SOSA/SSN cluster should remain a separate cleanup track.
