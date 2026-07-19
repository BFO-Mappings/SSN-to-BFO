# Object-Property Domain/Range Minimal Basis Implementation

## Policy And Qualification

This branch implements the preferred object-property domain/range basis documented in `reports/object-property-domain-range-minimal-basis.md`.

The implemented basis is cluster-minimal and stable across six deterministic removal orders. It is not claimed to be a globally exhaustive minimum over all possible subsets. The purpose is to preserve all 62 intended domain/range typing entailments while reducing local fallback assertions to one preferred representative per dependency component.

No imported source ontology files were edited. No active `rdfs:subPropertyOf`, `owl:equivalentProperty`, `owl:propertyChainAxiom`, class mapping, or deferred/rejected candidate mapping was reactivated or removed. No replacement range axioms were added.

## Exact Retained TTL Triples

Retained local object-property domain count: `22`.
Retained local object-property range count: `0`.

```ttl
sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty .
sosa:isObservedBy rdfs:domain sosa:ObservableProperty .
sosa:isSampleOf rdfs:domain sosa:Sample .
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeObservation rdfs:domain sosa:Sensor .
sosa:madeSampling rdfs:domain sosa:Sampler .
sosa:observedProperty rdfs:domain sosa:Observation .
ssn:detects rdfs:domain sosa:Sensor .
ssn:hasDeployment rdfs:domain ssn:System .
ssn:hasInput rdfs:domain sosa:Procedure .
ssn:hasOutput rdfs:domain sosa:Procedure .
ssn:hasSubSystem rdfs:domain ssn:System .
ssn:implements rdfs:domain ssn:System .
ssn:inDeployment rdfs:domain sosa:Platform .
ssn:isProxyFor rdfs:domain ssn:Stimulus .
ssn-system:hasOperatingProperty rdfs:domain ssn-system:OperatingRange .
ssn-system:hasOperatingRange rdfs:domain ssn:System .
ssn-system:hasSurvivalProperty rdfs:domain ssn-system:SurvivalRange .
ssn-system:hasSurvivalRange rdfs:domain ssn:System .
ssn-system:hasSystemCapability rdfs:domain ssn:System .
ssn-system:hasSystemProperty rdfs:domain ssn-system:SystemCapability .
ssn:wasOriginatedBy rdfs:domain sosa:Observation .
```

## Exact Removed TTL Triples

Removed local domain count: `9`.
Removed local range count: `31`.
Removed local domain/range triples total: `40`.

```ttl
sosa:actsOnProperty rdfs:domain sosa:Actuation .
sosa:actsOnProperty rdfs:range sosa:ActuatableProperty .
sosa:hasSample rdfs:domain sosa:FeatureOfInterest .
sosa:hasSample rdfs:range sosa:Sample .
sosa:isActedOnBy rdfs:range sosa:Actuation .
sosa:isObservedBy rdfs:range sosa:Sensor .
sosa:isSampleOf rdfs:range sosa:FeatureOfInterest .
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
sosa:madeByActuator rdfs:range sosa:Actuator .
sosa:madeBySampler rdfs:domain sosa:Sampling .
sosa:madeBySampler rdfs:range sosa:Sampler .
sosa:madeBySensor rdfs:domain sosa:Observation .
sosa:madeBySensor rdfs:range sosa:Sensor .
sosa:madeObservation rdfs:range sosa:Observation .
sosa:madeSampling rdfs:range sosa:Sampling .
sosa:observedProperty rdfs:range sosa:ObservableProperty .
sosa:observes rdfs:domain sosa:Sensor .
sosa:observes rdfs:range sosa:ObservableProperty .
ssn:deployedOnPlatform rdfs:domain ssn:Deployment .
ssn:deployedOnPlatform rdfs:range sosa:Platform .
ssn:deployedSystem rdfs:domain ssn:Deployment .
ssn:deployedSystem rdfs:range ssn:System .
ssn:detects rdfs:range ssn:Stimulus .
ssn:hasDeployment rdfs:range ssn:Deployment .
ssn:hasInput rdfs:range ssn:Input .
ssn:hasOutput rdfs:range ssn:Output .
ssn:hasSubSystem rdfs:range ssn:System .
ssn:implementedBy rdfs:domain sosa:Procedure .
ssn:implementedBy rdfs:range ssn:System .
ssn:implements rdfs:range sosa:Procedure .
ssn:inDeployment rdfs:range ssn:Deployment .
ssn:isProxyFor rdfs:range sosa:ObservableProperty .
ssn-system:hasOperatingProperty rdfs:range ssn-system:OperatingProperty .
ssn-system:hasOperatingRange rdfs:range ssn-system:OperatingRange .
ssn-system:hasSurvivalProperty rdfs:range ssn-system:SurvivalProperty .
ssn-system:hasSurvivalRange rdfs:range ssn-system:SurvivalRange .
ssn-system:hasSystemCapability rdfs:range ssn-system:SystemCapability .
ssn-system:hasSystemProperty rdfs:range ssn-system:SystemProperty .
ssn:wasOriginatedBy rdfs:range ssn:Stimulus .
```

Affected properties: `sosa:actsOnProperty`, `ssn:deployedOnPlatform`, `ssn:deployedSystem`, `ssn:detects`, `ssn:hasDeployment`, `ssn:hasInput`, `ssn:hasOutput`, `sosa:hasSample`, `ssn:hasSubSystem`, `ssn:implementedBy`, `ssn:implements`, `ssn:inDeployment`, `sosa:isActedOnBy`, `sosa:isObservedBy`, `ssn:isProxyFor`, `sosa:isSampleOf`, `sosa:madeActuation`, `sosa:madeByActuator`, `sosa:madeBySampler`, `sosa:madeBySensor`, `sosa:madeObservation`, `sosa:madeSampling`, `sosa:observedProperty`, `sosa:observes`, `ssn:wasOriginatedBy`, `ssn-system:hasOperatingProperty`, `ssn-system:hasOperatingRange`, `ssn-system:hasSurvivalProperty`, `ssn-system:hasSurvivalRange`, `ssn-system:hasSystemCapability`, `ssn-system:hasSystemProperty`.

## Workbook Changes

The workbook was updated only in the affected object-property rows. For each row, cell `E` was revised to remove the corresponding local domain/range text for the 40 removed TTL triples while preserving retained domain assertions and active subproperty, inverse-note, and property-chain text already present in the row. Cell `F` was revised to explain the preferred cluster-minimal basis, the retained representative typing, and the fact that imported source axioms are untouched.

| Sheet | Row | Source term | Cells changed |
|---|---:|---|---|
| Common OPs | 2 | `sosa:actsOnProperty` | `E`, `F` |
| Common OPs | 3 | `ssn:deployedOnPlatform` | `E`, `F` |
| Common OPs | 4 | `ssn:deployedSystem` | `E`, `F` |
| Common OPs | 5 | `ssn:detects` | `E`, `F` |
| Common OPs | 7 | `ssn:hasDeployment` | `E`, `F` |
| Common OPs | 9 | `ssn:hasInput` | `E`, `F` |
| Common OPs | 10 | `ssn:hasOutput` | `E`, `F` |
| Common OPs | 13 | `sosa:hasSample` | `E`, `F` |
| Common OPs | 14 | `ssn:hasSubSystem` | `E`, `F` |
| Common OPs | 16 | `ssn:implementedBy` | `E`, `F` |
| Common OPs | 17 | `ssn:implements` | `E`, `F` |
| Common OPs | 18 | `ssn:inDeployment` | `E`, `F` |
| Common OPs | 19 | `sosa:isActedOnBy` | `E`, `F` |
| Common OPs | 22 | `sosa:isObservedBy` | `E`, `F` |
| Common OPs | 24 | `ssn:isProxyFor` | `E`, `F` |
| Common OPs | 26 | `sosa:isSampleOf` | `E`, `F` |
| Common OPs | 27 | `sosa:madeActuation` | `E`, `F` |
| Common OPs | 28 | `sosa:madeByActuator` | `E`, `F` |
| Common OPs | 29 | `sosa:madeBySampler` | `E`, `F` |
| Common OPs | 30 | `sosa:madeBySensor` | `E`, `F` |
| Common OPs | 31 | `sosa:madeObservation` | `E`, `F` |
| Common OPs | 32 | `sosa:madeSampling` | `E`, `F` |
| Common OPs | 33 | `sosa:observedProperty` | `E`, `F` |
| Common OPs | 34 | `sosa:observes` | `E`, `F` |
| Common OPs | 37 | `ssn:wasOriginatedBy` | `E`, `F` |
| System Capability | 9 | `ssn-system:hasOperatingProperty` | `E`, `F` |
| System Capability | 10 | `ssn-system:hasOperatingRange` | `E`, `F` |
| System Capability | 11 | `ssn-system:hasSurvivalProperty` | `E`, `F` |
| System Capability | 12 | `ssn-system:hasSurvivalRange` | `E`, `F` |
| System Capability | 13 | `ssn-system:hasSystemCapability` | `E`, `F` |
| System Capability | 14 | `ssn-system:hasSystemProperty` | `E`, `F` |

## Inverse-Pair Representative Typing

For inverse-property components, only one local representative is retained. The removed side remains entailed through the retained representative plus imported inverse/source restrictions. Examples include:

- `sosa:madeActuation` local domain/range text was removed from the workbook and TTL, while `sosa:madeByActuator rdfs:domain sosa:Actuation .` is retained as the component representative.
- `sosa:actsOnProperty` local domain/range text was removed, while `sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty .` is retained.
- `ssn:implementedBy` local domain/range text was removed, while `ssn:implements rdfs:domain ssn:System .` is retained.

This does not delete or alter imported SOSA/SSN inverse or source restrictions.

## Count Verification

Programmatic comparison against the preferred basis after editing `SSN2BFO.ttl` found:

- retained local object-property domain count: `22`
- retained local object-property range count: `0`
- missing preferred retained triples: `0`
- extra local domain/range triples: `0`
- removed local domains relative to the prior 62-triple baseline: `9`
- removed local ranges relative to the prior 62-triple baseline: `31`

## Full Local SOSA Closure HermiT

Before this branch, the full local SOSA closure report recorded triple count `15769`, HermiT return code `0`, `owl:Nothing` count `0`, and unsat count `0`.

After applying the basis, `python tools/test_full_sosa_closure_hermit.py --output reports/full-sosa-closure-hermit-check.md` recorded:

| Graph | Triple count | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Unsat set |
|---|---:|---:|---|---:|---:|---|
| full local SOSA closure after basis | 15729 | 0 | yes | 0 | 0 | clean |

The triple-count drop is exactly the 40 removed local domain/range triples.

## 62-Probe Verification

The implementation reconstructed the 62 domain/range entailment probes used in `reports/object-property-domain-range-minimal-basis.md` and ran HermiT over the current tracked implementation.

| Probe graph | Triple count | HermiT return code | Probes tested | Passed | Failed | Unrelated unsats |
|---|---:|---:|---:|---:|---:|---:|
| `/tmp/ssn-to-bfo-minimal-basis-implementation-probes/implementation-62-probes.ttl` | 16256 | 1 | 62 | 62 | 0 | 0 |

All 62 probe classes were unsatisfiable, which is the expected pass condition for these negative probes. ROBOT returned code `1` because HermiT reports the intentionally unsatisfiable probe classes; no unrelated unsatisfiable classes were reported.

Failed probes: none.

## Mapping Audit

Before this branch, the mapping audit baseline was:

- `ttl_candidate_mapping_assertions=68`
- total issues: `2`
- `missing_in_spreadsheet=1`
- `missing_in_ttl=1`
- recognized expected `sosa:Sensor` version-alignment issues only

After regenerating `reports/mapping-consistency-audit.md` and `reports/mapping-consistency-audit.csv` with `make audit-write`, the audit remained:

- `ttl_candidate_mapping_assertions=68`
- total issues: `2`
- `missing_in_spreadsheet=1`
- `missing_in_ttl=1`
- recognized expected `sosa:Sensor` version-alignment issues only

The regenerated audit report changed line-number/context metadata and the ignored non-mapping predicate count because the 40 local domain/range triples were removed.

## ELK Instance Mapping Entailments

Before this branch, ELK baseline counts were:

- direct class expectations: `6`
- direct property expectations: `75`
- property-chain expectations: `5`
- restriction expectations: `2`
- expectation failures: `0`
- uncovered active mappings: `0`

After regenerating `reports/elk-instance-mapping-entailments.md`, the ELK check remained:

- direct class expectations: `6`
- direct property expectations: `75`
- property-chain expectations: `5`
- restriction expectations: `2`
- expectation failures: `0`
- uncovered direct/property-chain/restriction mappings: `0 / 0 / 0`

The tracked ELK report content did not change.

## Validation Suite

`python tools/run_validation_suite.py` passed after the implementation:

- Turtle parse check: PASS
- Mapping consistency audit: PASS
- Audit issue summary: PASS, with only the expected two `sosa:Sensor` issues
- Instance-data smoke test: PASS
- ELK instance mapping entailment test: PASS
- Full local SOSA closure HermiT check: PASS
- Python compile check: PASS
- Git whitespace check: PASS

## Human Review Summary

- Implemented the preferred 22-triple cluster-minimal object-property domain/range basis.
- Removed exactly 40 local domain/range triples from `SSN2BFO.ttl`: 9 domain triples and 31 range triples.
- Updated 31 workbook rows, cells `E` and `F`, to match the reduced local basis and explain representative typing.
- Confirmed all 62 intended typing probes remain entailed.
- Confirmed full local SOSA closure remains HermiT-clean with triple count `15729`.
- Mapping audit and ELK counts remain unchanged from the current baseline.
- Imported source axioms were untouched.
