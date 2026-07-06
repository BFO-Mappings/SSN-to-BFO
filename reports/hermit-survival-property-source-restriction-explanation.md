# HermiT SurvivalProperty Source-Restriction Explanation

## Scope

This diagnostic focuses on the remaining SSN Systems HermiT unsatisfiable-class cluster:

- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

No repository ontology mappings, spreadsheets, imports, source examples, generated/release artifacts, or existing reports were modified. Temporary graphs, ROBOT outputs, stdout/stderr captures, and the diagnostic JSON summary were written under:

`/tmp/ssn-to-bfo-hermit-survival-property-source-restriction-explanation`

This is a HermiT reducer/explanation report only. Temporary removals identify interaction points; they do not by themselves prove that a source ontology axiom or mapping axiom is wrong.

## Prior Context

`reports/hermit-remaining-unsat-isolation.md` showed that after selected SSN Systems direct BFO dependence property mappings were deferred, the current M2-style HermiT baseline still has 8 unsatisfiable classes:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

That prior report also showed:

- source/import-only control is HermiT-clean;
- removing all active SSN Systems mappings leaves only the 5 core SOSA/SSN unsats;
- removing active SSN Systems direct class mappings leaves only the 5 core SOSA/SSN unsats;
- removing active SSN Systems direct property mappings does not reduce the 8 unsats;
- the remaining SSN Systems trio is separable from the core SOSA/SSN cluster.

This report narrows the SSN Systems side and asks which `SurvivalProperty` source axioms and class mappings are high-impact.

## Current Baseline Setup

Each variant was built from an M2-style temporary graph merging:

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

The sample simplicity blocker did not reappear in any variant.

## Active Mappings Involving The Three SSN Systems Classes

### `ssn-system:BatteryLifetime`

No active `SSN2BFO.ttl` mapping axiom directly involving `ssn-system:BatteryLifetime` was found.

The local source ontology states:

```ttl
ssn-system:BatteryLifetime rdfs:subClassOf ssn-system:SurvivalProperty .
```

### `ssn-system:SurvivalProperty`

`SSN2BFO.ttl` contains an active class mapping for `ssn-system:SurvivalProperty`.

Direct mapping subject triples:

```ttl
ssn-system:SurvivalProperty rdf:type owl:Class ;
    rdfs:subClassOf [ ... ] .
```

The class expression uses these local BFO/CCO targets:

| Target | Local label |
| --- | --- |
| `bfo:BFO_0000034` | function |
| `bfo:BFO_0000054` | has realization |
| `bfo:BFO_0000015` | process |
| `bfo:BFO_0000055` | realizes |
| `cco:ont00001819` | caused by |
| `cco:ont00000177` | Affordance |
| `cco:ont00001920` | prescribed by |
| `cco:ont00000319` | Artifact Design |

### `ssn-system:SystemLifetime`

`SSN2BFO.ttl` contains an active class mapping for `ssn-system:SystemLifetime`.

Direct mapping subject triples:

```ttl
ssn-system:SystemLifetime rdf:type owl:Class ;
    rdfs:subClassOf [ ... ] .
```

The class expression uses these local BFO/CCO targets:

| Target | Local label |
| --- | --- |
| `bfo:BFO_0000034` | function |
| `bfo:BFO_0000054` | has realization |
| `bfo:BFO_0000015` | process |
| `bfo:BFO_0000055` | realizes |
| `cco:ont00001213` | Stasis of Artifact Operationality |
| `cco:ont00001819` | caused by |
| `cco:ont00000177` | Affordance |
| `cco:ont00001920` | prescribed by |
| `cco:ont00000319` | Artifact Design |

The local source ontology states:

```ttl
ssn-system:SystemLifetime rdfs:subClassOf ssn-system:SurvivalProperty .
```

## Imported Source Restriction Cluster Involving `SurvivalProperty`

The local `imports/ssn-systems.ttl` source evidence includes the following compacted Turtle-style excerpts.

`SurvivalProperty` is an `ssn:Property` with inverse-`hasSurvivalProperty` restrictions:

```ttl
ssn-system:SurvivalProperty rdfs:subClassOf ssn:Property .

ssn-system:SurvivalProperty rdfs:subClassOf [
  rdf:type owl:Restriction ;
  owl:onProperty [ owl:inverseOf ssn-system:hasSurvivalProperty ] ;
  owl:allValuesFrom ssn-system:SurvivalRange
] .

ssn-system:SurvivalProperty rdfs:subClassOf [
  rdf:type owl:Restriction ;
  owl:onProperty [ owl:inverseOf ssn-system:hasSurvivalProperty ] ;
  owl:minCardinality "1"^^xsd:nonNegativeInteger
] .
```

`SurvivalRange` constrains direct `hasSurvivalProperty` fillers:

```ttl
ssn-system:SurvivalRange rdfs:subClassOf [
  rdf:type owl:Restriction ;
  owl:onProperty ssn-system:hasSurvivalProperty ;
  owl:allValuesFrom ssn-system:SurvivalProperty
] .
```

Category counts extracted from the temporary graph:

| Category | Removed triples | Restriction nodes | Pattern |
| --- | ---: | ---: | --- |
| `SurvivalProperty` as restriction subject | 10 | 2 | inverse `hasSurvivalProperty`; filler `SurvivalRange`; min cardinality 1 |
| `SurvivalProperty` as restriction filler | 4 | 1 | direct `hasSurvivalProperty`; filler `SurvivalProperty` |
| `owl:onProperty ssn-system:hasSurvivalProperty` | 4 | 1 | same direct `SurvivalRange` all-values restriction |
| inverse `hasSurvivalProperty` expressions | 10 | 2 | same inverse restrictions on `SurvivalProperty` |
| restriction-only union | 14 | 3 | direct plus inverse restriction nodes |
| broader `SurvivalProperty` source axiom package | 22 | 3 | restriction-only union plus direct/incoming class-level source axioms |
| `BatteryLifetime` direct source package | 6 | 0 | class declaration, subclass, labels/annotations |
| `SystemLifetime` direct source package | 6 | 0 | class declaration, subclass, labels/annotations |

### Refinement Of Prior `SurvivalProperty` Reducer

`reports/hermit-remaining-unsat-isolation.md` used a coarser removal category for source restrictions directly attached to or mentioning `ssn-system:SurvivalProperty`. That result should be read as a coarse interaction signal, not as proof that the explicit `SurvivalProperty` restriction nodes alone caused all three SSN Systems unsats.

This focused diagnostic decomposes that earlier reducer into smaller source-side categories and source/mapping pairwise variants. Under that decomposition, explicit restriction-node removals alone do not reduce the 8-class baseline.

The broader `SurvivalProperty` source axiom package alone removes the two subclass unsats, `ssn-system:BatteryLifetime` and `ssn-system:SystemLifetime`, but leaves `ssn-system:SurvivalProperty` unsatisfiable. The full three-class SSN Systems reduction is reproduced only when that broader source package is paired with the active `ssn-system:SurvivalProperty` direct class mapping.

This is a refinement of reducer granularity. It does not show that the prior report was wrong, that the source ontology is wrong, or that the `SurvivalProperty` mapping is wrong.

## Variant Summary Table

| Variant | Exact temporary edit | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Delta vs baseline |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| A | Current M2 baseline: source/import graph plus current `SSN2BFO.ttl`. | 1 | no | n/a | 8 | 0 |
| B | Remove active direct class mappings in `SSN2BFO.ttl` whose source term is in `ssn-system:`. | 1 | no | n/a | 5 | -3 |
| C | Remove broader source axioms/restrictions directly attached to or mentioning `ssn-system:SurvivalProperty` from the temporary source graph. | 1 | no | n/a | 6 | -2 |
| D | Remove only source restrictions where `ssn-system:SurvivalProperty` is the subject. | 1 | no | n/a | 8 | 0 |
| E | Remove only source restrictions where `ssn-system:SurvivalProperty` is the filler. | 1 | no | n/a | 8 | 0 |
| F | Remove only source restrictions whose `owl:onProperty` is `ssn-system:hasSurvivalProperty`. | 1 | no | n/a | 8 | 0 |
| G | Remove only source restrictions involving inverse property expressions of `ssn-system:hasSurvivalProperty`. | 1 | no | n/a | 8 | 0 |
| H | Remove source axioms/restrictions directly attached to or mentioning `ssn-system:BatteryLifetime`. | 1 | no | n/a | 7 | -1 |
| I | Remove source axioms/restrictions directly attached to or mentioning `ssn-system:SystemLifetime`. | 1 | no | n/a | 7 | -1 |
| J | Remove active direct class mapping for `ssn-system:SurvivalProperty` only. | 1 | no | n/a | 8 | 0 |
| K | Remove active direct class mapping for `ssn-system:BatteryLifetime` only; no active mapping was found, so this is effectively a no-op. | 1 | no | n/a | 8 | 0 |
| L | Remove active direct class mapping for `ssn-system:SystemLifetime` only. | 1 | no | n/a | 8 | 0 |
| M | Remove active direct class mappings for `BatteryLifetime`, `SurvivalProperty`, and `SystemLifetime`; `BatteryLifetime` has no active direct mapping. | 1 | no | n/a | 8 | 0 |
| N1 | Remove broader `SurvivalProperty` source axiom package plus the `SurvivalProperty` direct class mapping. | 1 | no | n/a | 5 | -3 |
| N2 | Remove broader `SurvivalProperty` source axiom package plus the three direct class mapping subjects. | 1 | no | n/a | 5 | -3 |
| O1 | Remove subject-plus-filler `SurvivalProperty` restriction categories only. | 1 | no | n/a | 8 | 0 |
| O2 | Remove subject-plus-inverse `SurvivalProperty` restriction categories only. | 1 | no | n/a | 8 | 0 |
| O3 | Remove direct and inverse `hasSurvivalProperty` restriction categories only. | 1 | no | n/a | 8 | 0 |
| O4 | Remove broader `SurvivalProperty` source axiom package plus `BatteryLifetime` mapping subject. | 1 | no | n/a | 6 | -2 |
| O5 | Remove broader `SurvivalProperty` source axiom package plus `SystemLifetime` mapping subject. | 1 | no | n/a | 6 | -2 |
| O6 | Remove broader `SurvivalProperty` source axiom package plus `BatteryLifetime` and `SystemLifetime` mapping subjects. | 1 | no | n/a | 6 | -2 |

No variant in this focused matrix was HermiT-clean. All variants retained at least the 5 core SOSA/SSN unsats.

## Baseline Unsat Set

Variant A reproduced the current 8-class baseline:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

## Source-Restriction Category Results

Restriction-only category removals did not reduce the 8-class baseline:

- removing the two inverse-`hasSurvivalProperty` restrictions on `SurvivalProperty` left all 8 unsats;
- removing the direct `hasSurvivalProperty` all-values restriction where `SurvivalProperty` is the filler left all 8 unsats;
- removing direct and inverse `hasSurvivalProperty` restriction categories together left all 8 unsats.

The broader `SurvivalProperty` source axiom package did reduce the set, but only partially:

- Variant C removed 22 source triples and left 6 unsats.
- It removed `BatteryLifetime` and `SystemLifetime`.
- It did not remove `SurvivalProperty`.

The direct source packages for `BatteryLifetime` and `SystemLifetime` behaved as one-class controls:

- removing the `BatteryLifetime` direct source package removed only `BatteryLifetime`;
- removing the `SystemLifetime` direct source package removed only `SystemLifetime`.

This means the evidence does not support saying that the explicit `SurvivalProperty` restriction nodes alone drive the full systems trio. The stronger statement supported by this run is that the broader `SurvivalProperty` source axiom package participates in the interaction for the two subclasses, while `SurvivalProperty` itself also requires the active mapping side of the interaction.

## Direct Class Mapping Results

Removing all active SSN Systems direct class mappings removed the three SSN Systems unsats:

- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

Removing individual mapping subjects did not reduce the baseline:

- removing only the `SurvivalProperty` direct class mapping left all 8 unsats;
- removing only the `SystemLifetime` direct class mapping left all 8 unsats;
- `BatteryLifetime` has no active direct mapping, so that single-subject variant was effectively a no-op;
- removing the three named subjects together also left all 8 unsats, because this set does not include the broader SSN Systems class mapping context.

The all-SSN-Systems-class-mapping reducer is therefore high-impact, but it is too broad to identify a single incorrect mapping.

## Pairwise Interaction Results

The most informative pairwise variants were:

| Pairwise variant | Remaining unsats | Interpretation |
| --- | --- | --- |
| Broader `SurvivalProperty` source axiom package only | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus`, `ssn-system:SurvivalProperty` | Removes the two subclass unsats but leaves `SurvivalProperty`. |
| `SurvivalProperty` class mapping only | all 8 baseline classes | No reduction alone. |
| Broader source package plus `SurvivalProperty` class mapping | 5 core SOSA/SSN classes only | Clears the entire SSN Systems trio. |
| Broader source package plus `BatteryLifetime` mapping subject | `SurvivalProperty` still remains | Same as broader source package alone; `BatteryLifetime` has no active mapping. |
| Broader source package plus `SystemLifetime` mapping subject | `SurvivalProperty` still remains | Same as broader source package alone. |
| Broader source package plus `BatteryLifetime` and `SystemLifetime` mapping subjects | `SurvivalProperty` still remains | Same as broader source package alone. |

The key interaction is therefore not any single restriction node and not the `BatteryLifetime`/`SystemLifetime` mapping subjects. The clearest reducer is the combination of:

- the broader source axiom package around `ssn-system:SurvivalProperty`; and
- the active `ssn-system:SurvivalProperty` class mapping.

## Explanation Assessment

### Which Restrictions Appear Necessary Or High-Impact?

The explicit restriction nodes are relevant source evidence, but restriction-only removals were not high-impact in this focused run.

The high-impact source-side unit was the broader `SurvivalProperty` source axiom package, which includes:

- direct `SurvivalProperty` subclass commitments;
- inverse `hasSurvivalProperty` all-values and min-cardinality restrictions;
- incoming subclass/filler mentions involving `BatteryLifetime`, `SystemLifetime`, and `SurvivalRange`;
- source class declaration/annotation context.

That broader package removed `BatteryLifetime` and `SystemLifetime` from the unsat set, but not `SurvivalProperty`.

### Which Class Mappings Appear Necessary Or High-Impact?

The active `SurvivalProperty` class mapping is a high-impact partner only when the broader source axiom package is also removed. Removing the `SurvivalProperty` mapping alone did not reduce the baseline.

Removing all active SSN Systems direct class mappings removed the entire systems trio. This confirms that the systems trio is mapping-amplified by active SSN Systems class mappings, but the all-class-mapping variant is too broad to use as a fix plan.

### Is The Interaction Specific To `SurvivalProperty` Or Broader To SSN Systems Class Mappings?

Both are involved:

- the broader SSN Systems direct class mapping set is sufficient as a broad reducer;
- within the focused source-side probes, the decisive source package is centered on `SurvivalProperty`;
- `BatteryLifetime` and `SystemLifetime` are affected through their source subclass relation to `SurvivalProperty`;
- no active direct mapping for `BatteryLifetime` was found.

This points to a `SurvivalProperty`-centered source/mapping interaction rather than a generic active SSN Systems property-mapping issue.

### Are The Already-Deferred BFO Dependence Property Mappings Implicated?

No new evidence implicates the already-deferred direct BFO dependence property mappings.

In the current mapping file, the selected direct BFO dependence property mappings for `hasOperatingProperty`, `hasSurvivalProperty`, and `hasSystemProperty` are already deferred. The prior report showed that removing active SSN Systems direct property mappings did not reduce the current 8-class baseline. This focused report found the remaining SSN Systems trio through class mappings and source class/restriction context, not through active direct BFO dependence property mappings.

## Modeling Interpretation

The local source ontology says:

- `BatteryLifetime` is a subclass of `SurvivalProperty`;
- `SystemLifetime` is a subclass of `SurvivalProperty`;
- `SurvivalProperty` is constrained by inverse `hasSurvivalProperty` restrictions;
- `SurvivalRange` constrains direct `hasSurvivalProperty` fillers to `SurvivalProperty`.

The mapping file adds active class-level BFO/CCO expressions for `SurvivalProperty` and `SystemLifetime`, while `BatteryLifetime` has no active direct mapping. HermiT unsatisfiability appears when these source class commitments are merged with active SSN Systems class mappings.

This report does not prove that the source restrictions are wrong. It also does not prove that the `SurvivalProperty` class mapping is wrong. It shows that the smallest successful reducer tested here combines the broader `SurvivalProperty` source axiom package with the active `SurvivalProperty` mapping. A real fix should therefore be preceded by a smaller explanation/minimal-conflict extraction for that interaction.

## Recommendation

Do not make repository mapping changes in this diagnostic branch.

Recommended next step:

- create `review/hermit-survival-property-minimal-conflict-extraction`;
- extract a smaller temporary ontology containing:
  - the `SurvivalProperty`, `BatteryLifetime`, `SystemLifetime`, and `SurvivalRange` source axioms;
  - the active `SurvivalProperty` and `SystemLifetime` mapping expressions;
  - the BFO/CCO target fragments needed by those expressions;
  - enough `ssn:Property` context to reproduce the systems trio if possible;
- use HermiT on that extracted graph to identify the minimal source/mapping conflict before any fix branch.

If a later fix branch is justified, keep it separate from the core SOSA/SSN cluster. The core `sosa:Observation` / `sosa:Sensor` / `ssn:Stimulus` and `ssn:Input` / `ssn:Output` issues remain a separate HermiT cleanup track.

The ELK validation suite should remain the near-term regression baseline while full OWL/HermiT cleanup proceeds in narrow diagnostic branches.
