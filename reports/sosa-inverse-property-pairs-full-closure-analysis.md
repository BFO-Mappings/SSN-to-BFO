# SOSA Inverse Property Pairs Full-Closure Analysis

## Scope

This report analyzes selected SOSA inverse-property pairs under the current full local SOSA closure HermiT profile.

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

The full local SOSA closure graph is built from:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

After loading, the graph removes:

```ttl
owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty .
sosa:hasSample rdf:type owl:InverseFunctionalProperty .
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

## Comparison Case

The actuation pair is the comparison case:

```text
sosa:madeActuation / sosa:madeByActuator
```

Earlier full-closure diagnostics found that the pair became unsafe when both direct CCO agent mappings were active:

```ttl
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

Those direct CCO mappings are now deferred. The current active source-level state is:

```ttl
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The current full local SOSA closure is clean with that source-level state active.

## Pair Inventory

The materialized `imports/sosa.ttl` primarily uses `schema:domainIncludes` and `schema:rangeIncludes` for source-side domain/range notes. Active logical `rdfs:domain` / `rdfs:range` operationalization comes from `SSN2BFO.ttl` where present.

| Pair | SOSA inverse axiom | SOSA source domain/range notes | Active `SSN2BFO.ttl` side A | Active `SSN2BFO.ttl` side B | Workbook rows | Target relation pattern |
|---|---|---|---|---|---|---|
| `sosa:madeObservation` / `sosa:madeBySensor` | `madeBySensor owl:inverseOf madeObservation` | `madeObservation`: Sensor -> Observation; `madeBySensor`: Observation -> Sensor | `madeObservation rdfs:domain sosa:Sensor`; `rdfs:range sosa:Observation`; `rdfs:subPropertyOf cco:ont00001787` | `madeBySensor rdfs:domain sosa:Observation`; `rdfs:range sosa:Sensor`; `rdfs:subPropertyOf cco:ont00001833` | `Common OPs` rows 31 / 30 | Both sides map to inverse CCO agent relations: `cco:agent_in` / `cco:has_agent`. |
| `sosa:madeSampling` / `sosa:madeBySampler` | `madeBySampler owl:inverseOf madeSampling` | `madeSampling`: Sampler -> Sampling; `madeBySampler`: Sampling -> Sampler | `madeSampling rdfs:domain sosa:Sampler`; `rdfs:range sosa:Sampling`; `rdfs:subPropertyOf cco:ont00001787` | `madeBySampler rdfs:domain sosa:Sampling`; `rdfs:range sosa:Sampler`; `rdfs:subPropertyOf cco:ont00001833` | `Common OPs` rows 32 / 29 | Both sides map to inverse CCO agent relations: `cco:agent_in` / `cco:has_agent`. |
| `sosa:isActedOnBy` / `sosa:actsOnProperty` | `actsOnProperty owl:inverseOf isActedOnBy` | `isActedOnBy`: ActuatableProperty -> Actuation; `actsOnProperty`: Actuation -> ActuatableProperty | `isActedOnBy rdfs:domain sosa:ActuatableProperty`; `rdfs:range sosa:Actuation`; `rdfs:subPropertyOf cco:ont00001886` | `actsOnProperty rdfs:domain sosa:Actuation`; `rdfs:range sosa:ActuatableProperty`; `rdfs:subPropertyOf cco:ont00001834`; `rdf:type owl:ObjectProperty` | `Common OPs` rows 19 / 2 | Both sides map to inverse CCO relations: `cco:ont00001886` / `cco:ont00001834`, with BFO participant parent paths. |
| `sosa:isResultOf` / `sosa:hasResult` | `hasResult owl:inverseOf isResultOf` | `isResultOf`: Result/Sample -> Actuation/Observation/Sampling; `hasResult`: Actuation/Observation/Sampling -> Result/Sample | `isResultOf rdfs:subPropertyOf cco:ont00001816` | `hasResult rdfs:subPropertyOf cco:ont00001986` | `Common OPs` rows 25 / 12 | Both sides map to inverse CCO output relations: `cco:is_output_of` / `cco:has_output`. |
| `sosa:isHostedBy` / `sosa:hosts` | `hosts owl:inverseOf isHostedBy` | `isHostedBy`: Actuator/Platform/Sampler/Sensor -> Platform; `hosts`: Platform -> Actuator/Platform/Sampler/Sensor | `isHostedBy rdf:type owl:ObjectProperty`; property chain over BFO `participates_in`, `realizes`, `inheres_in` | `hosts rdf:type owl:ObjectProperty`; property chain over BFO `bearer_of`, `has_realization`, `has_participant` | `Common OPs` rows 21 / 15 | Both sides have active complex property-chain mappings, but not direct subproperty mappings to an inverse CCO target pair. |
| `sosa:isObservedBy` / `sosa:observes` | `isObservedBy owl:inverseOf observes` | `isObservedBy`: ObservableProperty -> Sensor; `observes`: Sensor -> ObservableProperty | `isObservedBy rdfs:domain sosa:ObservableProperty`; `rdfs:range sosa:Sensor` | `observes rdfs:domain sosa:Sensor`; `rdfs:range sosa:ObservableProperty`; `rdfs:subPropertyOf ssn:forProperty` | `Common OPs` rows 22 / 34 | No direct inverse CCO/BFO target pair. |

## Source Restrictions

The source `imports/ssn.ttl` includes all-values/cardinality restrictions for several of these pairs:

| Pair | Relevant source restriction pattern |
|---|---|
| `madeObservation` / `madeBySensor` | `sosa:Sensor` only `madeObservation` `sosa:Observation`; `sosa:Observation` only/cardinality on `madeBySensor` `sosa:Sensor`. |
| `madeSampling` / `madeBySampler` | `sosa:Sampler` only `madeSampling` `sosa:Sampling`; `sosa:Sampling` only/cardinality on `madeBySampler` `sosa:Sampler`. |
| `isActedOnBy` / `actsOnProperty` | `sosa:ActuatableProperty` only `isActedOnBy` `sosa:Actuation`; `sosa:Actuation` only/min-cardinality on `actsOnProperty` `sosa:ActuatableProperty`. |
| `isResultOf` / `hasResult` | Result/Sample and Actuation/Observation/Sampling source restrictions connect result-bearing processes and outputs. |
| `isHostedBy` / `hosts` | `ssn:System` / `sosa:Platform` restrictions connect hosted systems and hosting platforms. |
| `isObservedBy` / `observes` | `sosa:ObservableProperty` only `isObservedBy` `sosa:Sensor`; `sosa:Sensor` only `observes` `sosa:ObservableProperty`. |

These restrictions are part of the current full-closure clean baseline.

## HermiT Variants

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis
```

Each variant used the current full local SOSA closure graph and standard cleanup.

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| V0 | current full closure baseline | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V0.ttl` | 15769 | 0 | yes | 0 | 0 | clean |
| V1 | actuation comparison: re-add both deferred CCO agent mappings | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V1.ttl` | 15771 | 1 | no | n/a | 3 | `sosa:Actuation`, `sosa:Actuator`, `ssn-system:ActuationRange` |
| V2a | `madeObservation` / `madeBySensor`: remove `madeObservation -> agent_in` | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V2a.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V2b | `madeObservation` / `madeBySensor`: remove `madeBySensor -> has_agent` | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V2b.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V2c | `madeObservation` / `madeBySensor`: remove both direct agent mappings | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V2c.ttl` | 15767 | 0 | yes | 0 | 0 | clean |
| V3a | `madeSampling` / `madeBySampler`: remove `madeSampling -> agent_in` | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V3a.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V3b | `madeSampling` / `madeBySampler`: remove `madeBySampler -> has_agent` | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V3b.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V3c | `madeSampling` / `madeBySampler`: remove both direct agent mappings | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V3c.ttl` | 15767 | 0 | yes | 0 | 0 | clean |
| V4a | `isActedOnBy` / `actsOnProperty`: remove `isActedOnBy -> affected_by` | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V4a.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V4b | `isActedOnBy` / `actsOnProperty`: remove `actsOnProperty -> affects` | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V4b.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V4c | `isActedOnBy` / `actsOnProperty`: remove both direct mappings | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V4c.ttl` | 15767 | 0 | yes | 0 | 0 | clean |
| V5a | `isResultOf` / `hasResult`: remove `isResultOf -> is_output_of` | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V5a.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V5b | `isResultOf` / `hasResult`: remove `hasResult -> has_output` | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V5b.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V5c | `isResultOf` / `hasResult`: remove both direct output mappings | `/tmp/ssn-to-bfo-sosa-inverse-property-pairs-full-closure-analysis/V5c.ttl` | 15767 | 0 | yes | 0 | 0 | clean |

The removal variants are not proposed as mapping changes. They are diagnostic checks to see whether the current active graph is silently close to a HermiT failure around an inverse pair. None of the active non-actuation pairs produced an unsatisfiable class in either the baseline or the focused removals.

## Risk Classification

| Pair | Classification | Reason |
|---|---|---|
| `madeActuation` / `madeByActuator` | Already mitigated | The direct CCO agent mappings are deferred. Re-adding both reproduces the known three-class full-closure failure. The active source-level domain/range state is clean. |
| `madeObservation` / `madeBySensor` | Medium risk | This is the closest active structural analog to actuation: materialized SOSA inverse, source restrictions, and both sides mapped to inverse CCO agent relations. However, the current full closure is clean and focused removals are clean, so there is no current HermiT failure evidence. |
| `madeSampling` / `madeBySampler` | Medium risk | Same active CCO agent/agent-in pattern as observation and actuation, but current full closure and removal variants are clean. |
| `isActedOnBy` / `actsOnProperty` | Medium risk | Both sides map to inverse CCO affected-by/affects relations with participant-path ancestry. Current full closure and removal variants are clean. |
| `isResultOf` / `hasResult` | Medium risk | Both sides map to inverse CCO output relations. Current full closure and removal variants are clean. |
| `isHostedBy` / `hosts` | Medium-low risk | Both sides have active complex property-chain mappings and a materialized SOSA inverse, but they are not direct subproperty mappings to an inverse CCO target pair. Current full closure is clean. |
| `isObservedBy` / `observes` | Low risk | Active source-level domain/range and one `observes -> ssn:forProperty` mapping are present, but there is no direct inverse CCO/BFO target pair resembling the actuation failure. Current full closure is clean. |

## Pair Answers

### `madeObservation` / `madeBySensor`

- Materialized SOSA inverse axiom: yes, as `madeBySensor owl:inverseOf madeObservation`.
- Active mappings: both sides have source-level domain/range and direct CCO agent mappings.
- Both sides mapped to inverse CCO/BFO relations: yes, `cco:agent_in` / `cco:has_agent`.
- Current full closure proves active state HermiT-clean: yes.
- Evidence of actuation-agent failure pattern: structural similarity only; no current failure.
- Separate focused analysis needed: not urgent, but this is the first candidate if the project wants a deeper pair-level review.

### `madeSampling` / `madeBySampler`

- Materialized SOSA inverse axiom: yes, as `madeBySampler owl:inverseOf madeSampling`.
- Active mappings: both sides have source-level domain/range and direct CCO agent mappings.
- Both sides mapped to inverse CCO/BFO relations: yes.
- Current full closure proves active state HermiT-clean: yes.
- Evidence of actuation-agent failure pattern: structural similarity only; no current failure.
- Separate focused analysis needed: not before the observation/sensor analog.

### `isActedOnBy` / `actsOnProperty`

- Materialized SOSA inverse axiom: yes, as `actsOnProperty owl:inverseOf isActedOnBy`.
- Active mappings: both sides have source-level domain/range and direct CCO affected-by/affects mappings.
- Both sides mapped to inverse CCO/BFO relations: yes.
- Current full closure proves active state HermiT-clean: yes.
- Evidence of actuation-agent failure pattern: inverse target structure, but not the agent/agent-in pattern; no current failure.
- Separate focused analysis needed: only if future changes touch actuation/property mappings.

### `isResultOf` / `hasResult`

- Materialized SOSA inverse axiom: yes, as `hasResult owl:inverseOf isResultOf`.
- Active mappings: both sides have direct CCO output mappings.
- Both sides mapped to inverse CCO/BFO relations: yes.
- Current full closure proves active state HermiT-clean: yes.
- Evidence of actuation-agent failure pattern: inverse target structure, but no current failure.
- Separate focused analysis needed: not immediately.

### `isHostedBy` / `hosts`

- Materialized SOSA inverse axiom: yes, as `hosts owl:inverseOf isHostedBy`.
- Active mappings: both sides have property-chain mappings over BFO role/realization/participation paths.
- Both sides mapped to inverse CCO/BFO relations: no direct inverse CCO/BFO target pair.
- Current full closure proves active state HermiT-clean: yes.
- Evidence of actuation-agent failure pattern: no direct analog, but property-chain complexity deserves caution.
- Separate focused analysis needed: not immediately.

### `isObservedBy` / `observes`

- Materialized SOSA inverse axiom: yes, as `isObservedBy owl:inverseOf observes`.
- Active mappings: source-level domain/range on both sides; `observes rdfs:subPropertyOf ssn:forProperty`.
- Both sides mapped to inverse CCO/BFO relations: no.
- Current full closure proves active state HermiT-clean: yes.
- Evidence of actuation-agent failure pattern: no.
- Separate focused analysis needed: no.

## ELK Note

ELK instance-entailment coverage is separate from this full-closure HermiT risk analysis. The ELK report is useful for active mapping coverage and regression expectations, but an ELK pass should not be treated as evidence that inverse-property pairs are full-closure HermiT-safe.

The current validation suite now has both:

- ELK instance-entailment coverage; and
- full local SOSA closure HermiT consistency.

This report relies on the full-closure HermiT results for consistency claims.

## Interpretation

The current active full local SOSA closure is HermiT-clean.

The actuation comparison still fails if the two deferred actuation-side CCO agent mappings are reintroduced. This confirms that the actuation mitigation remains necessary.

The active non-actuation inverse-property pairs are covered by the current full-closure clean baseline. The structurally closest active analogs are:

```text
sosa:madeObservation / sosa:madeBySensor
sosa:madeSampling / sosa:madeBySampler
```

because both sides map to the same CCO `agent_in` / `has_agent` inverse target pair that was unsafe for actuation. They do not currently fail, and focused removal variants did not reveal hidden unsats.

The `isActedOnBy` / `actsOnProperty` and `isResultOf` / `hasResult` pairs also map to inverse target relations, but their target semantics differ from the agent pair and the current full closure is clean.

The `isHostedBy` / `hosts` and `isObservedBy` / `observes` pairs do not have the same direct inverse CCO/BFO subproperty pattern.

## Recommendation

Recommend exactly one next step:

```text
review/analyze-madeObservation-madeBySensor-agent-pair-full-closure
```

This should be report-only. It should not propose a mapping change unless a focused full-closure explanation finds evidence that the active observation/sensor agent pair is unsafe.

Rationale: `madeObservation` / `madeBySensor` is the closest active structural analog to the mitigated actuation pair and also touches the historically important Observation/Sensor area. The current full closure is clean, so this is a cautionary explanation branch, not a fix branch.

## Validation

Validation commands:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/sosa-inverse-property-pairs-full-closure-analysis.md

git diff --check
```

Result: pending at report creation.

Final result:

- `workflow_check.py --mode report-only`: PASS
- validation suite: PASS
- mapping audit: PASS with the two expected `sosa:Sensor` version-alignment issues only
- ELK direct property expectations: 75
- full local SOSA closure HermiT check: PASS (`15769` triples, return code `0`, `owl:Nothing` count `0`, unsat count `0`)
- Python compile check: PASS
- `git diff --check`: PASS
