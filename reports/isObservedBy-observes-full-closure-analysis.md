# IsObservedBy / Observes Full-Closure Analysis

## Scope

This report is a focused, report-only analysis of the SOSA inverse-property pair:

```text
sosa:isObservedBy / sosa:observes
```

It follows `reports/sosa-inverse-property-pairs-full-closure-analysis.md`, which classified this pair as low risk. This is the final SOSA inverse-property pair from the current full-closure inverse-pair risk audit list.

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

## Full-Closure Method

All HermiT runs used the current full local SOSA closure graph built from:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

After loading, each graph removed:

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

`imports/sosa.ttl` asserts the inverse relation on the `isObservedBy` side:

```ttl
sosa:isObservedBy owl:inverseOf sosa:observes .
```

It records source-level domain/range notes using `schema:domainIncludes` and `schema:rangeIncludes`:

| Property | SOSA source note |
|---|---|
| `sosa:isObservedBy` | ObservableProperty -> Sensor |
| `sosa:observes` | Sensor -> ObservableProperty |

The materialized SOSA source file does not assert these notes as global `rdfs:domain` / `rdfs:range` axioms.

### SSN Source Context

`imports/ssn.ttl` contributes this source property relation:

```ttl
sosa:observes rdfs:subPropertyOf ssn:forProperty .
```

It also contains source restrictions connecting the pair to `sosa:ObservableProperty` and `sosa:Sensor`:

| Source class | Restriction pattern |
|---|---|
| `sosa:ObservableProperty` | `sosa:isObservedBy only sosa:Sensor` |
| `sosa:Sensor` | `sosa:observes only sosa:ObservableProperty` |

`ssn:forProperty` is an imported SSN object property with a source definition that covers, among other examples, a sensor and the properties it can observe. It is not itself mapped in `SSN2BFO.ttl` to a direct CCO/BFO inverse target pair.

### Active Mapping Context

`SSN2BFO.ttl` currently contains:

```ttl
sosa:isObservedBy rdfs:domain sosa:ObservableProperty ;
                  rdfs:range sosa:Sensor .

sosa:observes rdfs:domain sosa:Sensor ;
              rdfs:range sosa:ObservableProperty ;
              rdfs:subPropertyOf ssn:forProperty .
```

The `sosa:observes rdfs:subPropertyOf ssn:forProperty` triple is also present in `imports/ssn.ttl`. Therefore, removing only the local `SSN2BFO.ttl` contribution of that triple does not remove the effective axiom from the full local SOSA closure graph.

There is no active direct CCO/BFO subproperty mapping for either side of this pair. This is the most important structural difference from the mitigated actuation-agent pair.

### Related Class Mappings

Relevant active local class mappings are:

```text
sosa:ObservableProperty subclassOf
  (bfo:SpecificallyDependentContinuant and bfo:inheres_in some sosa:FeatureOfInterest)
  or
  (bfo:ProcessProfile and bfo:occurrent_part_of some sosa:FeatureOfInterest)

sosa:Sensor subclassOf
  bfo:MaterialEntity
  and (bfo:bearer_of some (bfo:RealizableEntity and bfo:has_realization some sosa:Observation))
  and (cco:agent_in some sosa:Observation)
```

The active `sosa:Sensor` mapping is the known version-alignment area in the mapping audit, but the current full local SOSA closure is HermiT-clean with this mapping active.

### Workbook Context

The corresponding workbook rows are in `Common OPs`:

| Row | Source term | Active OWL cell summary | Rationale summary |
|---:|---|---|---|
| 22 | `sosa:isObservedBy` | `rdfs:domain sosa:ObservableProperty`; `rdfs:range sosa:Sensor`; inverse note | source-level domain/range typing; inverse note remains |
| 34 | `sosa:observes` | `rdfs:domain sosa:Sensor`; `rdfs:range sosa:ObservableProperty`; `rdfs:subPropertyOf ssn:forProperty` | source-level domain/range typing; existing `ssn:forProperty` mapping unchanged |

Relevant class rows are in `Common Classes`:

| Row | Source term | Active OWL cell summary |
|---:|---|---|
| 8 | `sosa:ObservableProperty` | subclass of SDC/inheres-in-FOI or ProcessProfile/occurrent-part-of-FOI |
| 18 | `sosa:Sensor` | equivalent-to CCO Sensor note in workbook; TTL currently has a subclass expression |

### Comparison Cases

Similarity to the mitigated `madeActuation` / `madeByActuator` pair:

- SOSA materializes an inverse relation between the two properties.
- Source restrictions connect each side to the relevant source classes.
- The pair touches the historically sensitive Sensor/Observation area indirectly through `sosa:Sensor`.

Differences from the mitigated actuation agent pair:

- There is no direct inverse CCO/BFO target pair.
- `sosa:observes` maps to the source property `ssn:forProperty`, not to `cco:has_agent`, `cco:agent_in`, or a BFO participant property.
- `sosa:isObservedBy` has source-level domain/range typing only.
- The current full local SOSA closure is HermiT-clean with the inverse axiom, source restrictions, `sosa:Sensor` mapping, and `sosa:ObservableProperty` mapping all active.

Comparison to previously checked clean pairs:

- Like `madeObservation` / `madeBySensor`, `madeSampling` / `madeBySampler`, `isActedOnBy` / `actsOnProperty`, `isResultOf` / `hasResult`, and `isHostedBy` / `hosts`, the current active state is full-closure HermiT-clean.
- Unlike the observation/sensor and sampling/sampler agent pairs, this pair does not map both sides to inverse CCO agent properties.
- Unlike the result pair, this pair does not involve direct CCO output relations.
- Unlike the hosting pair, this pair does not use active BFO property chains.

## Focused HermiT Variants

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis
```

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set | Sample blocker |
|---|---|---|---:|---:|---|---:|---:|---|---|
| V0 | Current full closure baseline | `/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis/V0-baseline.ttl` | 15769 | 0 | yes | 0 | 0 | clean | no |
| V1 | Remove only the `SSN2BFO.ttl` contribution of `sosa:observes rdfs:subPropertyOf ssn:forProperty` | `/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis/V1-remove-observes-mapping-only.ttl` | 15769 | 0 | yes | 0 | 0 | clean | no |
| V2 | Remove active `SSN2BFO.ttl` source-level domain/range mapping for `sosa:isObservedBy` | `/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis/V2-remove-isObservedBy-mapping-only.ttl` | 15767 | 0 | yes | 0 | 0 | clean | no |
| V3 | Remove local `observes` mapping contribution and local `isObservedBy` domain/range mapping | `/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis/V3-remove-both-pair-mappings.ttl` | 15767 | 0 | yes | 0 | 0 | clean | no |
| V4 | Skipped: no missing symmetric source-level domain/range axiom was identified | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| V5 | Skipped: no missing workbook-proposed CCO/BFO mapping was identified | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| V6 | Remove materialized SOSA inverse axiom `sosa:isObservedBy owl:inverseOf sosa:observes` | `/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis/V6-remove-sosa-inverse.ttl` | 15768 | 0 | yes | 0 | 0 | clean | no |
| V7 | Remove source restrictions involving `sosa:isObservedBy` / `sosa:observes` | `/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis/V7-remove-source-restrictions.ttl` | 15761 | 0 | yes | 0 | 0 | clean | no |
| V8 | Remove active `sosa:Sensor` class-expression mapping | `/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis/V8-remove-sensor-class-mapping.ttl` | 15745 | 0 | yes | 0 | 0 | clean | no |
| V9 | Remove active `sosa:ObservableProperty` class-expression mapping | `/tmp/ssn-to-bfo-isObservedBy-observes-full-closure-analysis/V9-remove-observable-property-class-mapping.ttl` | 15744 | 0 | yes | 0 | 0 | clean | no |

V1 is baseline-equivalent in the effective full-closure graph because `imports/ssn.ttl` also asserts:

```ttl
sosa:observes rdfs:subPropertyOf ssn:forProperty .
```

V2 removed the local `sosa:isObservedBy rdfs:domain sosa:ObservableProperty` and `sosa:isObservedBy rdfs:range sosa:Sensor` triples. Because `sosa:isObservedBy` is inverse to `sosa:observes`, and `sosa:observes` keeps source-level domain/range typing, the effective range behavior is still partly reconstructable through the inverse.

V7 removed:

```text
sosa:ObservableProperty rdfs:subClassOf (sosa:isObservedBy only sosa:Sensor)
sosa:Sensor rdfs:subClassOf (sosa:observes only sosa:ObservableProperty)
```

All executed variants were HermiT-clean.

## Interpretation

The current active `isObservedBy` / `observes` pair is HermiT-clean under the full local SOSA closure.

The pair has inverse-side coupling through SOSA:

```text
sosa:isObservedBy inverseOf sosa:observes
```

But it does not have the direct inverse CCO/BFO target pattern that caused the mitigated actuation-agent failure. There is no pair of active mappings like:

```text
source-forward relation -> CCO inverse-side relation
source-reverse relation -> CCO forward-side relation
```

Instead:

- `sosa:isObservedBy` is source-level domain/range only.
- `sosa:observes` is source-level domain/range plus `rdfs:subPropertyOf ssn:forProperty`.
- `ssn:forProperty` is a source SSN property in this profile, not an active direct CCO/BFO inverse target.

Removing the SOSA inverse axiom, source restrictions, `sosa:Sensor` class mapping, or `sosa:ObservableProperty` class mapping all preserved cleanliness. Since the baseline is already clean, these are not reducers for an observed inconsistency, but they confirm that the pair is not currently hiding a full-closure HermiT failure.

The sensor/observable-property context does carry normal project caution:

- `sosa:Sensor` remains the known two-issue version-alignment audit area.
- `sosa:ObservableProperty` has a BFO union mapping involving specifically dependent continuants and process profiles.
- `sosa:observedProperty -> cco:has_input` remains removed/rejected from earlier HermiT work.

None of that creates a current HermiT issue for `isObservedBy` / `observes`.

## Risk Classification

This pair remains low risk.

It can be read as lower-risk than the medium-risk agent pairs because it lacks direct inverse CCO/BFO agent mappings, and lower-risk than the hosting pair because it lacks active BFO property chains. Future changes should still use the full local SOSA closure HermiT guardrail, especially if any direct CCO/BFO mapping is proposed for either side.

## Recommendation

No mapping change is warranted for `sosa:isObservedBy` / `sosa:observes`.

Recommended next step: no mapping change and close the current inverse-property-pair audit. The full local SOSA closure HermiT validation check should remain the guardrail for any future strengthening of Sensor, ObservableProperty, observes, isObservedBy, or related observation-property mappings.

## Validation

Validation commands:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/isObservedBy-observes-full-closure-analysis.md

git diff --check
```

Result: PASS.

Workflow-check summary:

- Validation suite: PASS.
- Full local SOSA closure HermiT check: PASS.
- Python compile check: PASS.
- Git whitespace check: PASS.
- Expected changed file set: only `reports/isObservedBy-observes-full-closure-analysis.md`.
