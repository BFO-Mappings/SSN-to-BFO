# Object-Property Domain/Range Minimal Basis

## Scope

This report identifies a policy-preferred subset of the 62 locally asserted object-property `rdfs:domain` and `rdfs:range` triples in `SSN2BFO.ttl`. The objective is to preserve every intended typing entailment currently supplied by those local triples while removing local domain/range assertions where the remaining local/source/mapping context still entails the same typing.

This is report-only. It does not edit `SSN2BFO.ttl`, the workbook, imports, tools, examples, releases, generated artifacts, or existing reports.

Inputs used:

- `reports/object-property-domain-range-fallback-policy-audit.md`
- `reports/deferred-candidate-domain-range-causality-retest.md`
- `reports/object-property-domain-range-entailment-audit.md`

## Method

All HermiT graphs used the full local SOSA closure:

- `imports/cco.ttl`
- `imports/sosa.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl` or a temporary `SSN2BFO.ttl` variant

Standard cleanup removed all `owl:imports` triples and the two sample simplicity blockers:

- `sosa:isSampleOf rdf:type owl:FunctionalProperty`
- `sosa:hasSample rdf:type owl:InverseFunctionalProperty`

For a candidate basis, the temporary graph removed every local object-property domain/range triple not in the basis, then added all 62 probe classes at once. A basis was accepted only when all 62 probes were unsatisfiable and no unrelated named class was unsatisfiable. HermiT was then run again without probes to confirm the basis graph itself was clean.

The search used six deterministic greedy removal orders: active-candidate properties first, domain-first, range-first, inverse-pair grouped, workbook row order, and reverse workbook row order. It also exhaustively checked the small dependency clusters found in the inspected graph: nine inverse-pair clusters with four local triples each, and thirteen single-property clusters with two local triples each.

## Inventory

The 62 local triples partition into 22 tested dependency components: 9 inverse-pair components and 13 single-property components. Every component had minimum size 1 in the cluster tests. The preferred basis therefore retains one representative per component.

| Idx | Component | Property | Kind | Intended class | Status | Workbook row | Preferred action |
|---:|---|---|---|---|---|---|---|
| 0 | I1 | `sosa:actsOnProperty` | domain | `sosa:Actuation` | active | Common OPs row 2 | remove |
| 1 | I1 | `sosa:actsOnProperty` | range | `sosa:ActuatableProperty` | active | Common OPs row 2 | remove |
| 2 | I2 | `sosa:hasSample` | domain | `sosa:FeatureOfInterest` | active | Common OPs row 13 | remove |
| 3 | I2 | `sosa:hasSample` | range | `sosa:Sample` | active | Common OPs row 13 | remove |
| 4 | I1 | `sosa:isActedOnBy` | domain | `sosa:ActuatableProperty` | active | Common OPs row 19 | retain |
| 5 | I1 | `sosa:isActedOnBy` | range | `sosa:Actuation` | active | Common OPs row 19 | remove |
| 6 | I3 | `sosa:isObservedBy` | domain | `sosa:ObservableProperty` | none | Common OPs row 22 | retain |
| 7 | I3 | `sosa:isObservedBy` | range | `sosa:Sensor` | none | Common OPs row 22 | remove |
| 8 | I2 | `sosa:isSampleOf` | domain | `sosa:Sample` | active | Common OPs row 26 | retain |
| 9 | I2 | `sosa:isSampleOf` | range | `sosa:FeatureOfInterest` | active | Common OPs row 26 | remove |
| 10 | I4 | `sosa:madeActuation` | domain | `sosa:Actuator` | deferred | Common OPs row 27 | remove |
| 11 | I4 | `sosa:madeActuation` | range | `sosa:Actuation` | deferred | Common OPs row 27 | remove |
| 12 | I4 | `sosa:madeByActuator` | domain | `sosa:Actuation` | deferred | Common OPs row 28 | retain |
| 13 | I4 | `sosa:madeByActuator` | range | `sosa:Actuator` | deferred | Common OPs row 28 | remove |
| 14 | I5 | `sosa:madeBySampler` | domain | `sosa:Sampling` | active | Common OPs row 29 | remove |
| 15 | I5 | `sosa:madeBySampler` | range | `sosa:Sampler` | active | Common OPs row 29 | remove |
| 16 | I6 | `sosa:madeBySensor` | domain | `sosa:Observation` | active | Common OPs row 30 | remove |
| 17 | I6 | `sosa:madeBySensor` | range | `sosa:Sensor` | active | Common OPs row 30 | remove |
| 18 | I6 | `sosa:madeObservation` | domain | `sosa:Sensor` | active | Common OPs row 31 | retain |
| 19 | I6 | `sosa:madeObservation` | range | `sosa:Observation` | active | Common OPs row 31 | remove |
| 20 | I5 | `sosa:madeSampling` | domain | `sosa:Sampler` | active | Common OPs row 32 | retain |
| 21 | I5 | `sosa:madeSampling` | range | `sosa:Sampling` | active | Common OPs row 32 | remove |
| 22 | S1 | `sosa:observedProperty` | domain | `sosa:Observation` | rejected | Common OPs row 33 | retain |
| 23 | S1 | `sosa:observedProperty` | range | `sosa:ObservableProperty` | rejected | Common OPs row 33 | remove |
| 24 | I3 | `sosa:observes` | domain | `sosa:Sensor` | active | Common OPs row 34 | remove |
| 25 | I3 | `sosa:observes` | range | `sosa:ObservableProperty` | active | Common OPs row 34 | remove |
| 26 | I7 | `ssn:deployedOnPlatform` | domain | `ssn:Deployment` | active | Common OPs row 3 | remove |
| 27 | I7 | `ssn:deployedOnPlatform` | range | `sosa:Platform` | active | Common OPs row 3 | remove |
| 28 | I8 | `ssn:deployedSystem` | domain | `ssn:Deployment` | active | Common OPs row 4 | remove |
| 29 | I8 | `ssn:deployedSystem` | range | `ssn:System` | active | Common OPs row 4 | remove |
| 30 | S2 | `ssn:detects` | domain | `sosa:Sensor` | active | Common OPs row 5 | retain |
| 31 | S2 | `ssn:detects` | range | `ssn:Stimulus` | active | Common OPs row 5 | remove |
| 32 | I8 | `ssn:hasDeployment` | domain | `ssn:System` | active | Common OPs row 7 | retain |
| 33 | I8 | `ssn:hasDeployment` | range | `ssn:Deployment` | active | Common OPs row 7 | remove |
| 34 | S3 | `ssn:hasInput` | domain | `sosa:Procedure` | rejected | Common OPs row 9 | retain |
| 35 | S3 | `ssn:hasInput` | range | `ssn:Input` | rejected | Common OPs row 9 | remove |
| 36 | S4 | `ssn:hasOutput` | domain | `sosa:Procedure` | rejected | Common OPs row 10 | retain |
| 37 | S4 | `ssn:hasOutput` | range | `ssn:Output` | rejected | Common OPs row 10 | remove |
| 38 | S5 | `ssn:hasSubSystem` | domain | `ssn:System` | active | Common OPs row 14 | retain |
| 39 | S5 | `ssn:hasSubSystem` | range | `ssn:System` | active | Common OPs row 14 | remove |
| 40 | I9 | `ssn:implementedBy` | domain | `sosa:Procedure` | active | Common OPs row 16 | remove |
| 41 | I9 | `ssn:implementedBy` | range | `ssn:System` | active | Common OPs row 16 | remove |
| 42 | I9 | `ssn:implements` | domain | `ssn:System` | none | Common OPs row 17 | retain |
| 43 | I9 | `ssn:implements` | range | `sosa:Procedure` | none | Common OPs row 17 | remove |
| 44 | I7 | `ssn:inDeployment` | domain | `sosa:Platform` | active | Common OPs row 18 | retain |
| 45 | I7 | `ssn:inDeployment` | range | `ssn:Deployment` | active | Common OPs row 18 | remove |
| 46 | S6 | `ssn:isProxyFor` | domain | `ssn:Stimulus` | none | Common OPs row 24 | retain |
| 47 | S6 | `ssn:isProxyFor` | range | `sosa:ObservableProperty` | none | Common OPs row 24 | remove |
| 48 | S7 | `ssn-system:hasOperatingProperty` | domain | `ssn-system:OperatingRange` | deferred | System Capability row 9 | retain |
| 49 | S7 | `ssn-system:hasOperatingProperty` | range | `ssn-system:OperatingProperty` | deferred | System Capability row 9 | remove |
| 50 | S8 | `ssn-system:hasOperatingRange` | domain | `ssn:System` | active | System Capability row 10 | retain |
| 51 | S8 | `ssn-system:hasOperatingRange` | range | `ssn-system:OperatingRange` | active | System Capability row 10 | remove |
| 52 | S9 | `ssn-system:hasSurvivalProperty` | domain | `ssn-system:SurvivalRange` | deferred | System Capability row 11 | retain |
| 53 | S9 | `ssn-system:hasSurvivalProperty` | range | `ssn-system:SurvivalProperty` | deferred | System Capability row 11 | remove |
| 54 | S10 | `ssn-system:hasSurvivalRange` | domain | `ssn:System` | active | System Capability row 12 | retain |
| 55 | S10 | `ssn-system:hasSurvivalRange` | range | `ssn-system:SurvivalRange` | active | System Capability row 12 | remove |
| 56 | S11 | `ssn-system:hasSystemCapability` | domain | `ssn:System` | active | System Capability row 13 | retain |
| 57 | S11 | `ssn-system:hasSystemCapability` | range | `ssn-system:SystemCapability` | active | System Capability row 13 | remove |
| 58 | S12 | `ssn-system:hasSystemProperty` | domain | `ssn-system:SystemCapability` | deferred | System Capability row 14 | retain |
| 59 | S12 | `ssn-system:hasSystemProperty` | range | `ssn-system:SystemProperty` | deferred | System Capability row 14 | remove |
| 60 | S13 | `ssn:wasOriginatedBy` | domain | `sosa:Observation` | active | Common OPs row 37 | retain |
| 61 | S13 | `ssn:wasOriginatedBy` | range | `ssn:Stimulus` | active | Common OPs row 37 | remove |

## Dependency Components

The relevant support patterns were:

- **Inverse-property support**: for materialized inverse pairs, a retained domain or range representative on either side can entail the corresponding typing on the inverse side.
- **Source-restriction support**: imported source restrictions such as `allValuesFrom` constraints participate with one retained local representative to recover the companion typing.
- **Cross-property support**: inverse pairs combine inverse-property support and source restrictions, so one representative can support all four local domain/range typings in that pair.
- **Property-chain support**: property-chain mappings were not assumed to supply typing. They were accepted only where the all-probe basis test confirmed the entailments still held.

### Inverse-Pair Components

| Component | Properties | Local triple indexes | Exhaustive minimum | Preferred retained index |
|---|---|---|---:|---:|
| I1 | `sosa:actsOnProperty` / `sosa:isActedOnBy` | 0, 1, 4, 5 | 1 | 4 |
| I2 | `sosa:hasSample` / `sosa:isSampleOf` | 2, 3, 8, 9 | 1 | 8 |
| I3 | `sosa:isObservedBy` / `sosa:observes` | 6, 7, 24, 25 | 1 | 6 |
| I4 | `sosa:madeActuation` / `sosa:madeByActuator` | 10, 11, 12, 13 | 1 | 12 |
| I5 | `sosa:madeBySampler` / `sosa:madeSampling` | 14, 15, 20, 21 | 1 | 20 |
| I6 | `sosa:madeBySensor` / `sosa:madeObservation` | 16, 17, 18, 19 | 1 | 18 |
| I7 | `ssn:deployedOnPlatform` / `ssn:inDeployment` | 26, 27, 44, 45 | 1 | 44 |
| I8 | `ssn:deployedSystem` / `ssn:hasDeployment` | 28, 29, 32, 33 | 1 | 32 |
| I9 | `ssn:implementedBy` / `ssn:implements` | 40, 41, 42, 43 | 1 | 42 |

### Single-Property Components

| Component | Property | Local triple indexes | Exhaustive minimum | Preferred retained index |
|---|---|---|---:|---:|
| S1 | `sosa:observedProperty` | 22, 23 | 1 | 22 |
| S2 | `ssn:detects` | 30, 31 | 1 | 30 |
| S3 | `ssn:hasInput` | 34, 35 | 1 | 34 |
| S4 | `ssn:hasOutput` | 36, 37 | 1 | 36 |
| S5 | `ssn:hasSubSystem` | 38, 39 | 1 | 38 |
| S6 | `ssn:isProxyFor` | 46, 47 | 1 | 46 |
| S7 | `ssn-system:hasOperatingProperty` | 48, 49 | 1 | 48 |
| S8 | `ssn-system:hasOperatingRange` | 50, 51 | 1 | 50 |
| S9 | `ssn-system:hasSurvivalProperty` | 52, 53 | 1 | 52 |
| S10 | `ssn-system:hasSurvivalRange` | 54, 55 | 1 | 54 |
| S11 | `ssn-system:hasSystemCapability` | 56, 57 | 1 | 56 |
| S12 | `ssn-system:hasSystemProperty` | 58, 59 | 1 | 58 |
| S13 | `ssn:wasOriginatedBy` | 60, 61 | 1 | 60 |

Cluster minimality note: the 22-triple basis is proven minimal for the tested dependency-component decomposition because every one of the 22 components required at least one representative. A global exhaustive search over all `2^62` subsets was not attempted, so the result should be described as cluster-minimal and greedily stable, not as a complete global minimum proof.

## Greedy Search Results

| Removal order | Retained triples | Removed triples | All probes preserved |
|---|---:|---:|---|
| active-candidate-first | 22 | 40 | yes |
| domain-first | 22 | 40 | yes |
| range-first | 22 | 40 | yes |
| inverse-pair-grouped | 22 | 40 | yes |
| workbook-row-order | 22 | 40 | yes |
| reverse-workbook-row-order | 22 | 40 | yes |

All six orders found a 22-triple basis. The retained representatives differed by order; the preferred basis is the `active-candidate-first` result because it removes local domain/range from active-mapped properties where possible and retains fallback representatives for rejected, deferred, unsafe, or unmapped properties where needed.

## Preferred Basis

The preferred basis retains 22 local domain triples and zero local range triples. It removes 9 local domain triples and all 31 local range triples, for 40 removals total.

### Retained TTL Triples

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

### TTL Triples To Remove

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

## Required Caution Properties

| Property | Candidate status | Preferred retained local typing | Removed local typing | Interpretation |
|---|---|---|---|---|
| `sosa:madeActuation` | deferred | none | `sosa:madeActuation rdfs:domain sosa:Actuator .`<br>`sosa:madeActuation rdfs:range sosa:Actuation .` | Retain one fallback representative where needed; rejected/deferred candidate mappings are not counted as replacement mappings. |
| `sosa:madeByActuator` | deferred | `sosa:madeByActuator rdfs:domain sosa:Actuation .` | `sosa:madeByActuator rdfs:range sosa:Actuator .` | Retain one fallback representative where needed; rejected/deferred candidate mappings are not counted as replacement mappings. |
| `sosa:observedProperty` | rejected | `sosa:observedProperty rdfs:domain sosa:Observation .` | `sosa:observedProperty rdfs:range sosa:ObservableProperty .` | Retain one fallback representative where needed; rejected/deferred candidate mappings are not counted as replacement mappings. |
| `ssn:hasInput` | rejected | `ssn:hasInput rdfs:domain sosa:Procedure .` | `ssn:hasInput rdfs:range ssn:Input .` | Retain one fallback representative where needed; rejected/deferred candidate mappings are not counted as replacement mappings. |
| `ssn:hasOutput` | rejected | `ssn:hasOutput rdfs:domain sosa:Procedure .` | `ssn:hasOutput rdfs:range ssn:Output .` | Retain one fallback representative where needed; rejected/deferred candidate mappings are not counted as replacement mappings. |
| `ssn-system:hasOperatingProperty` | deferred | `ssn-system:hasOperatingProperty rdfs:domain ssn-system:OperatingRange .` | `ssn-system:hasOperatingProperty rdfs:range ssn-system:OperatingProperty .` | Retain one fallback representative where needed; rejected/deferred candidate mappings are not counted as replacement mappings. |
| `ssn-system:hasSurvivalProperty` | deferred | `ssn-system:hasSurvivalProperty rdfs:domain ssn-system:SurvivalRange .` | `ssn-system:hasSurvivalProperty rdfs:range ssn-system:SurvivalProperty .` | Retain one fallback representative where needed; rejected/deferred candidate mappings are not counted as replacement mappings. |
| `ssn-system:hasSystemProperty` | deferred | `ssn-system:hasSystemProperty rdfs:domain ssn-system:SystemCapability .` | `ssn-system:hasSystemProperty rdfs:range ssn-system:SystemProperty .` | Retain one fallback representative where needed; rejected/deferred candidate mappings are not counted as replacement mappings. |

## Verification

| Check | Graph path | Triple count | Return code | Reasoned output | Result |
|---|---|---:|---:|---|---|
| All 62 probes on preferred basis | `/tmp/ssn-to-bfo-domain-range-minimal-basis/059_active-candidate-first_try_37.ttl` | 16256 | 1 | false | 62 probes unsat; 0 missing; no unrelated unsats |
| Preferred basis, no probes | `/tmp/ssn-to-bfo-domain-range-minimal-basis/preferred_basis_clean.ttl` | 15729 | 0 | true | `owl:Nothing` count 0; unsat count 0; clean |

The no-probe reasoned output contained zero `owl:Nothing` subclass/equivalent-class hits. The reasoned graph had 15,759 triples.

### Temporary Mapping Audit

The preferred-basis temporary TTL was `/tmp/ssn-to-bfo-domain-range-minimal-basis/preferred-SSN2BFO.ttl`. Running `tools/compare_mappings.py` against the current workbook produced the same audit summary as the current baseline:

- `ttl_candidate_mapping_assertions=68`
- total issues: `2`
- `missing_in_spreadsheet=1`
- `missing_in_ttl=1`
- both issues are the known `sosa:Sensor` version-alignment issues

### Temporary ELK Instance-Entailment Check

- return code: `0`
- direct class expectations: `6`
- direct property expectations: `75`
- property-chain expectations: `5`
- restriction expectations: `2`
- expectation failures: `0`
- uncovered direct/property-chain/restriction mappings: `0` / `0` / `0`

## Workbook Implications

A future mapping-change branch applying the preferred basis would need to revise the OWL axiom cell (`E`) for every row listed below. The rationale/comment cell (`F`) should explain that the removed local domain/range typing remains entailed through the retained representative plus source/inverse/property context. No workbook edit is made in this report.

| Workbook row | Property | Cell(s) to revise | Remove from OWL axiom cell | Retain/document |
|---|---|---|---|---|
| Common OPs row 10 | `ssn:hasOutput` | `E` and `F` | `ssn:hasOutput rdfs:range ssn:Output .` | `ssn:hasOutput rdfs:domain sosa:Procedure .` |
| Common OPs row 13 | `sosa:hasSample` | `E` and `F` | `sosa:hasSample rdfs:domain sosa:FeatureOfInterest .`<br>`sosa:hasSample rdfs:range sosa:Sample .` | typing entailed by another retained component representative |
| Common OPs row 14 | `ssn:hasSubSystem` | `E` and `F` | `ssn:hasSubSystem rdfs:range ssn:System .` | `ssn:hasSubSystem rdfs:domain ssn:System .` |
| Common OPs row 16 | `ssn:implementedBy` | `E` and `F` | `ssn:implementedBy rdfs:domain sosa:Procedure .`<br>`ssn:implementedBy rdfs:range ssn:System .` | typing entailed by another retained component representative |
| Common OPs row 17 | `ssn:implements` | `E` and `F` | `ssn:implements rdfs:range sosa:Procedure .` | `ssn:implements rdfs:domain ssn:System .` |
| Common OPs row 18 | `ssn:inDeployment` | `E` and `F` | `ssn:inDeployment rdfs:range ssn:Deployment .` | `ssn:inDeployment rdfs:domain sosa:Platform .` |
| Common OPs row 19 | `sosa:isActedOnBy` | `E` and `F` | `sosa:isActedOnBy rdfs:range sosa:Actuation .` | `sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty .` |
| Common OPs row 2 | `sosa:actsOnProperty` | `E` and `F` | `sosa:actsOnProperty rdfs:domain sosa:Actuation .`<br>`sosa:actsOnProperty rdfs:range sosa:ActuatableProperty .` | typing entailed by another retained component representative |
| Common OPs row 22 | `sosa:isObservedBy` | `E` and `F` | `sosa:isObservedBy rdfs:range sosa:Sensor .` | `sosa:isObservedBy rdfs:domain sosa:ObservableProperty .` |
| Common OPs row 24 | `ssn:isProxyFor` | `E` and `F` | `ssn:isProxyFor rdfs:range sosa:ObservableProperty .` | `ssn:isProxyFor rdfs:domain ssn:Stimulus .` |
| Common OPs row 26 | `sosa:isSampleOf` | `E` and `F` | `sosa:isSampleOf rdfs:range sosa:FeatureOfInterest .` | `sosa:isSampleOf rdfs:domain sosa:Sample .` |
| Common OPs row 27 | `sosa:madeActuation` | `E` and `F` | `sosa:madeActuation rdfs:domain sosa:Actuator .`<br>`sosa:madeActuation rdfs:range sosa:Actuation .` | typing entailed by another retained component representative |
| Common OPs row 28 | `sosa:madeByActuator` | `E` and `F` | `sosa:madeByActuator rdfs:range sosa:Actuator .` | `sosa:madeByActuator rdfs:domain sosa:Actuation .` |
| Common OPs row 29 | `sosa:madeBySampler` | `E` and `F` | `sosa:madeBySampler rdfs:domain sosa:Sampling .`<br>`sosa:madeBySampler rdfs:range sosa:Sampler .` | typing entailed by another retained component representative |
| Common OPs row 3 | `ssn:deployedOnPlatform` | `E` and `F` | `ssn:deployedOnPlatform rdfs:domain ssn:Deployment .`<br>`ssn:deployedOnPlatform rdfs:range sosa:Platform .` | typing entailed by another retained component representative |
| Common OPs row 30 | `sosa:madeBySensor` | `E` and `F` | `sosa:madeBySensor rdfs:domain sosa:Observation .`<br>`sosa:madeBySensor rdfs:range sosa:Sensor .` | typing entailed by another retained component representative |
| Common OPs row 31 | `sosa:madeObservation` | `E` and `F` | `sosa:madeObservation rdfs:range sosa:Observation .` | `sosa:madeObservation rdfs:domain sosa:Sensor .` |
| Common OPs row 32 | `sosa:madeSampling` | `E` and `F` | `sosa:madeSampling rdfs:range sosa:Sampling .` | `sosa:madeSampling rdfs:domain sosa:Sampler .` |
| Common OPs row 33 | `sosa:observedProperty` | `E` and `F` | `sosa:observedProperty rdfs:range sosa:ObservableProperty .` | `sosa:observedProperty rdfs:domain sosa:Observation .` |
| Common OPs row 34 | `sosa:observes` | `E` and `F` | `sosa:observes rdfs:domain sosa:Sensor .`<br>`sosa:observes rdfs:range sosa:ObservableProperty .` | typing entailed by another retained component representative |
| Common OPs row 37 | `ssn:wasOriginatedBy` | `E` and `F` | `ssn:wasOriginatedBy rdfs:range ssn:Stimulus .` | `ssn:wasOriginatedBy rdfs:domain sosa:Observation .` |
| Common OPs row 4 | `ssn:deployedSystem` | `E` and `F` | `ssn:deployedSystem rdfs:domain ssn:Deployment .`<br>`ssn:deployedSystem rdfs:range ssn:System .` | typing entailed by another retained component representative |
| Common OPs row 5 | `ssn:detects` | `E` and `F` | `ssn:detects rdfs:range ssn:Stimulus .` | `ssn:detects rdfs:domain sosa:Sensor .` |
| Common OPs row 7 | `ssn:hasDeployment` | `E` and `F` | `ssn:hasDeployment rdfs:range ssn:Deployment .` | `ssn:hasDeployment rdfs:domain ssn:System .` |
| Common OPs row 9 | `ssn:hasInput` | `E` and `F` | `ssn:hasInput rdfs:range ssn:Input .` | `ssn:hasInput rdfs:domain sosa:Procedure .` |
| System Capability row 10 | `ssn-system:hasOperatingRange` | `E` and `F` | `ssn-system:hasOperatingRange rdfs:range ssn-system:OperatingRange .` | `ssn-system:hasOperatingRange rdfs:domain ssn:System .` |
| System Capability row 11 | `ssn-system:hasSurvivalProperty` | `E` and `F` | `ssn-system:hasSurvivalProperty rdfs:range ssn-system:SurvivalProperty .` | `ssn-system:hasSurvivalProperty rdfs:domain ssn-system:SurvivalRange .` |
| System Capability row 12 | `ssn-system:hasSurvivalRange` | `E` and `F` | `ssn-system:hasSurvivalRange rdfs:range ssn-system:SurvivalRange .` | `ssn-system:hasSurvivalRange rdfs:domain ssn:System .` |
| System Capability row 13 | `ssn-system:hasSystemCapability` | `E` and `F` | `ssn-system:hasSystemCapability rdfs:range ssn-system:SystemCapability .` | `ssn-system:hasSystemCapability rdfs:domain ssn:System .` |
| System Capability row 14 | `ssn-system:hasSystemProperty` | `E` and `F` | `ssn-system:hasSystemProperty rdfs:range ssn-system:SystemProperty .` | `ssn-system:hasSystemProperty rdfs:domain ssn-system:SystemCapability .` |
| System Capability row 9 | `ssn-system:hasOperatingProperty` | `E` and `F` | `ssn-system:hasOperatingProperty rdfs:range ssn-system:OperatingProperty .` | `ssn-system:hasOperatingProperty rdfs:domain ssn-system:OperatingRange .` |

## Interpretation

- Smallest sufficient basis found: `22` retained triples.
- Minimality status: cluster-minimal and stable across six greedy orders; not globally proven by exhaustive `2^62` search.
- Domain removals: `9`; range removals: `31`; total removals: `40`.
- Retained local triples: `22` domains and `0` ranges.
- The retained triples each support multiple intended typings within their dependency component. In each inverse-pair component, one retained representative supports all four local domain/range typings for the pair. In each single-property component, one retained representative supports both the domain and range typing for that property.
- The original goal of using local domain/range only as fallback can be partially satisfied. Active-mapping properties in inverse or source-restriction clusters can lose many local domain/range assertions, but some active-mapped components still need one local representative to preserve exact source-level typing.
- Rejected, deferred, HermiT-unsafe, and unmapped properties are not treated as having replacement mappings. The preferred basis keeps fallback representatives for all such caution areas except where another retained representative in the same inverse component is policy-preferred.
- The preferred basis remains HermiT-clean under full local SOSA closure.
- Temporary mapping-audit and ELK counts do not change from the current baseline.

## Recommendation

Recommend exactly one next branch:

```text
fix/apply-object-property-domain-range-minimal-basis
```

Expected changed files for that branch:

- `SSN2BFO.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`
- `reports/mapping-consistency-audit.md`
- `reports/mapping-consistency-audit.csv` if regenerated content changes
- `reports/elk-instance-mapping-entailments.md` if regenerated content changes
- a new implementation report for the basis application

Expected validation effects if the preferred basis is applied exactly:

- Full local SOSA closure HermiT remains PASS with unsat count `0`.
- ELK instance-entailment counts remain direct class `6`, direct property `75`, property-chain `5`, restriction `2`, with no uncovered active mappings.
- Mapping audit remains at `ttl_candidate_mapping_assertions=68` and the two expected `sosa:Sensor` version-alignment issues, based on the temporary audit.
- All 62 intended domain/range typing probes remain entailed.

## Human Review Summary

- The current 62 local object-property domain/range triples can be reduced to a 22-triple cluster-minimal preferred basis.
- The preferred basis retains 22 domain triples, removes 9 domain triples, and removes all 31 range triples.
- Every intended typing probe remains unsatisfiable under the preferred basis.
- The preferred no-probe graph is HermiT-clean with triple count `15729`, return code `0`, `owl:Nothing` count `0`, and unsat count `0`.
- Temporary mapping-audit and ELK checks remain aligned with the current baseline.
- The basis is cluster-minimal and stable across tested greedy orders, but not globally exhaustively proven over all subsets.
- Recommended next branch: `fix/apply-object-property-domain-range-minimal-basis`.
