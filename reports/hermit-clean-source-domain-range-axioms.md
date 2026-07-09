# HermiT-Clean Source Domain/Range Axioms

## Scope

This mapping-change branch implements the HermiT-clean source-level domain/range subset identified in `reports/all-source-domain-range-operationalization-evaluation.md`.

The implementation adds only source-level `rdfs:domain` and `rdfs:range` axioms. It does not add BFO or CCO domain/range shortcuts, SWRL rules, SPARQL rules, SHACL rules, or COMS materialization.

The previously failed BFO/CCO `rdfs:subPropertyOf` mappings remain inactive.

## Stable Baseline Before This Branch

- Validation suite: PASS
- `ttl_candidate_mapping_assertions`: 71
- Mapping audit issues: 2 expected `sosa:Sensor` version-alignment issues only
- ELK direct class expectations: 6
- ELK direct property expectations: 77
- Property-chain expectations: 5
- Restriction expectations: 2
- Active direct/property-chain/restriction mappings not covered: 0
- HermiT M2 baseline: clean under established cleanup conditions

## Source Report Used

- `reports/all-source-domain-range-operationalization-evaluation.md`

That evaluation found 62 simple source-level domain/range axioms, with 6 already active in `SSN2BFO.ttl`. Of the 56 absent-but-supported tested axioms, the full batch failed only because of one source-level range axiom:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The clean implementation batch adds the other 55 axioms.

## Axiom Counts

| Item | Count |
| --- | ---: |
| Already-present source-level domain/range axioms left unchanged | 6 |
| New source-level domain/range axioms added | 55 |
| Held-back failing axiom | 1 |
| Workbook rows changed | 28 |
| Workbook cell values changed | 49 |

## New Source-Level Axioms Added

```ttl
sosa:actsOnProperty rdfs:domain sosa:Actuation .
sosa:actsOnProperty rdfs:range sosa:ActuatableProperty .

sosa:hasSample rdfs:domain sosa:FeatureOfInterest .
sosa:hasSample rdfs:range sosa:Sample .

sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty .
sosa:isActedOnBy rdfs:range sosa:Actuation .

sosa:isObservedBy rdfs:domain sosa:ObservableProperty .
sosa:isObservedBy rdfs:range sosa:Sensor .

sosa:isSampleOf rdfs:domain sosa:Sample .
sosa:isSampleOf rdfs:range sosa:FeatureOfInterest .

sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .

sosa:madeByActuator rdfs:domain sosa:Actuation .

sosa:madeBySampler rdfs:domain sosa:Sampling .
sosa:madeBySampler rdfs:range sosa:Sampler .

sosa:madeBySensor rdfs:domain sosa:Observation .
sosa:madeBySensor rdfs:range sosa:Sensor .

sosa:madeObservation rdfs:domain sosa:Sensor .
sosa:madeObservation rdfs:range sosa:Observation .

sosa:madeSampling rdfs:domain sosa:Sampler .
sosa:madeSampling rdfs:range sosa:Sampling .

sosa:observedProperty rdfs:domain sosa:Observation .
sosa:observedProperty rdfs:range sosa:ObservableProperty .

sosa:observes rdfs:domain sosa:Sensor .
sosa:observes rdfs:range sosa:ObservableProperty .

ssn:deployedOnPlatform rdfs:domain ssn:Deployment .
ssn:deployedOnPlatform rdfs:range sosa:Platform .

ssn:deployedSystem rdfs:domain ssn:Deployment .
ssn:deployedSystem rdfs:range ssn:System .

ssn:detects rdfs:domain sosa:Sensor .
ssn:detects rdfs:range ssn:Stimulus .

ssn:hasDeployment rdfs:domain ssn:System .
ssn:hasDeployment rdfs:range ssn:Deployment .

ssn:hasInput rdfs:domain sosa:Procedure .
ssn:hasInput rdfs:range ssn:Input .

ssn:hasOutput rdfs:domain sosa:Procedure .
ssn:hasOutput rdfs:range ssn:Output .

ssn:hasSubSystem rdfs:domain ssn:System .
ssn:hasSubSystem rdfs:range ssn:System .

ssn:implementedBy rdfs:domain sosa:Procedure .
ssn:implementedBy rdfs:range ssn:System .

ssn:implements rdfs:domain ssn:System .
ssn:implements rdfs:range sosa:Procedure .

ssn:inDeployment rdfs:domain sosa:Platform .
ssn:inDeployment rdfs:range ssn:Deployment .

ssn:isProxyFor rdfs:domain ssn:Stimulus .
ssn:isProxyFor rdfs:range sosa:ObservableProperty .

ssn:wasOriginatedBy rdfs:domain sosa:Observation .
ssn:wasOriginatedBy rdfs:range ssn:Stimulus .

ssn-system:hasOperatingRange rdfs:domain ssn:System .
ssn-system:hasOperatingRange rdfs:range ssn-system:OperatingRange .

ssn-system:hasSurvivalRange rdfs:domain ssn:System .
ssn-system:hasSurvivalRange rdfs:range ssn-system:SurvivalRange .

ssn-system:hasSystemCapability rdfs:domain ssn:System .
ssn-system:hasSystemCapability rdfs:range ssn-system:SystemCapability .
```

## Held-Back Axiom

The following axiom was explicitly not added:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

It was the smallest tested failing axiom in the prior evaluation and reintroduced:

- `sosa:Actuation`
- `sosa:Actuator`
- `ssn-system:ActuationRange`

## Workbook Rows Updated

Only workbook rows corresponding to the newly added source-level axioms were changed.

| Sheet | Row | Cells updated |
| --- | ---: | --- |
| `Common OPs` | 2 | `E2`, `F2` |
| `Common OPs` | 3 | `F3` |
| `Common OPs` | 4 | `F4` |
| `Common OPs` | 5 | `F5` |
| `Common OPs` | 7 | `E7`, `F7` |
| `Common OPs` | 9 | `E9`, `F9` |
| `Common OPs` | 10 | `E10`, `F10` |
| `Common OPs` | 13 | `F13` |
| `Common OPs` | 14 | `F14` |
| `Common OPs` | 16 | `E16`, `F16` |
| `Common OPs` | 17 | `E17`, `F17` |
| `Common OPs` | 18 | `E18`, `F18` |
| `Common OPs` | 19 | `E19`, `F19` |
| `Common OPs` | 22 | `E22`, `F22` |
| `Common OPs` | 24 | `E24`, `F24` |
| `Common OPs` | 26 | `E26`, `F26` |
| `Common OPs` | 27 | `E27`, `F27` |
| `Common OPs` | 28 | `E28`, `F28` |
| `Common OPs` | 29 | `F29` |
| `Common OPs` | 30 | `F30` |
| `Common OPs` | 31 | `E31`, `F31` |
| `Common OPs` | 32 | `E32`, `F32` |
| `Common OPs` | 33 | `E33`, `F33` |
| `Common OPs` | 34 | `E34`, `F34` |
| `Common OPs` | 37 | `E37`, `F37` |
| `System Capability` | 10 | `E10`, `F10` |
| `System Capability` | 12 | `E12`, `F12` |
| `System Capability` | 13 | `E13`, `F13` |

The workbook rationale now describes this branch as source-level domain/range operationalization. It does not present the failed CCO/BFO direct mappings as intended deferred mappings.

## HermiT Edited-Graph Result

Temporary graph:

```text
/tmp/ssn-to-bfo-hermit-clean-source-domain-range-axioms/edited-graph.ttl
```

Reasoned output:

```text
/tmp/ssn-to-bfo-hermit-clean-source-domain-range-axioms/edited-graph-reasoned.ttl
```

| Check | Result |
| --- | --- |
| Triple count before reasoning | 15535 |
| ROBOT/HermiT return code | 0 |
| Reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| Unsat count | 0 |
| Unsat set | none |
| Sample simplicity blocker reappeared | no |

## Mapping Audit

After regenerating the canonical mapping audit:

- `ttl_candidate_mapping_assertions`: 71
- Total issues: 2
- `missing_in_spreadsheet`: 1
- `missing_in_ttl`: 1
- Both issues are the expected `sosa:Sensor` version-alignment issues.

The audit CSV changed because the canonical audit was regenerated after the mapping file and workbook updates.

## ELK Report Check

The ELK entailment test was run to a temporary output path and compared against the canonical report.

Result:

- Example files tested: 16
- ROBOT pass/fail: 16/0
- Direct class expectations checked: 6
- Direct property expectations checked: 77
- Property-chain expectations checked: 5
- Restriction expectations checked: 2
- Expectation failures: 0
- Active direct/property-chain/restriction mappings not covered: 0

The temporary ELK report was identical to `reports/elk-instance-mapping-entailments.md`, so the canonical ELK report was not regenerated.

## Recommendation

This implementation preserves the HermiT-clean M2 baseline while adding the HermiT-clean source-level domain/range operationalization subset.

The held-back `sosa:madeByActuator rdfs:range sosa:Actuator` axiom should remain out of the active mapping until a focused HermiT explanation or replacement-design branch isolates the interaction.
