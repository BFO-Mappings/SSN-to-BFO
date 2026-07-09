# All Source Domain/Range Operationalization Evaluation

## Scope

This report evaluates whether source-level `rdfs:domain` and `rdfs:range` axioms can be added across the current mapping profile while preserving the HermiT-clean M2 baseline.

No BFO or CCO domain/range shortcuts were tested. No failed BFO/CCO `rdfs:subPropertyOf` mapping was reactivated. No SWRL, SPARQL, SHACL, or COMS materialization was added.

This branch is report-only because the full candidate batch was not HermiT-clean.

## Current Stable Baseline

- Branch: `review/evaluate-all-source-domain-range-operationalization`
- Commit tested: `4b854e5c4d5999d8423eeded21713f484e9a03f3`
- Standard validation suite: PASS
- `ttl_candidate_mapping_assertions`: 71
- Mapping audit issues: 2 expected `sosa:Sensor` version-alignment issues only
- ELK direct class expectations: 6
- ELK direct property expectations: 77
- Property-chain expectations: 5
- Restriction expectations: 2
- Active direct/property-chain/restriction mappings not covered: 0
- HermiT M2 baseline: clean under established cleanup conditions

## Method

Inputs inspected:

- `SSN2BFO.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`

Candidate criteria:

- The property is represented in the workbook and/or `SSN2BFO.ttl`.
- Proposed domain/range targets are source-level classes, not BFO or CCO classes.
- Evidence comes from explicit workbook OWL cells, workbook source definitions, or imported source restrictions.
- Complex union domains/ranges and intentionally loose `schema:domainIncludes`/`schema:rangeIncludes` rows are held out for later review.

HermiT graph setup for each variant:

- Merge `imports/cco.ttl`, `imports/ssn.ttl`, `imports/ssn-systems.ttl`, and `SSN2BFO.ttl`.
- Remove all `owl:imports` triples.
- Remove `sosa:isSampleOf rdf:type owl:FunctionalProperty`.
- Remove `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.
- Run `robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>`.

Temporary files were written under:

```text
/tmp/ssn-to-bfo-all-source-domain-range-operationalization
```

## Candidate Inventory Summary

| Category | Count |
| --- | ---: |
| Simple source-level domain/range axioms inventoried | 62 |
| Already present in `SSN2BFO.ttl` | 6 |
| Already present in imports | 0 |
| Absent but supported and tested | 56 |
| Active edits made | 0 |

## Already Present Source-Level Axioms

These source-level typing axioms were already active in `SSN2BFO.ttl`, from the earlier SSN Systems operationalization work.

| Property | Domain | Range | Exists in |
| --- | --- | --- | --- |
| `ssn-system:hasOperatingProperty` | `ssn-system:OperatingRange` | `ssn-system:OperatingProperty` | `SSN2BFO.ttl` |
| `ssn-system:hasSurvivalProperty` | `ssn-system:SurvivalRange` | `ssn-system:SurvivalProperty` | `SSN2BFO.ttl` |
| `ssn-system:hasSystemProperty` | `ssn-system:SystemCapability` | `ssn-system:SystemProperty` | `SSN2BFO.ttl` |

## Absent But Supported Candidates Tested

The following 56 absent source-level domain/range axioms were tested as a full batch.

| Property | Proposed domain | Proposed range | Evidence |
| --- | --- | --- | --- |
| `sosa:actsOnProperty` | `sosa:Actuation` | `sosa:ActuatableProperty` | Workbook `Common OPs` row 2; imported source restriction on `sosa:Actuation` |
| `ssn:deployedOnPlatform` | `ssn:Deployment` | `sosa:Platform` | Workbook `Common OPs` row 3 explicit domain/range |
| `ssn:deployedSystem` | `ssn:Deployment` | `ssn:System` | Workbook `Common OPs` row 4 explicit domain/range |
| `ssn:detects` | `sosa:Sensor` | `ssn:Stimulus` | Workbook `Common OPs` row 5 explicit domain/range |
| `ssn:hasDeployment` | `ssn:System` | `ssn:Deployment` | Workbook `Common OPs` row 7; inverse of `ssn:deployedSystem` |
| `sosa:hasSample` | `sosa:FeatureOfInterest` | `sosa:Sample` | Workbook `Common OPs` row 13 explicit domain/range |
| `ssn:hasInput` | `sosa:Procedure` | `ssn:Input` | Workbook `Common OPs` row 9; imported source restriction on `sosa:Procedure` |
| `ssn:hasOutput` | `sosa:Procedure` | `ssn:Output` | Workbook `Common OPs` row 10; imported source restriction on `sosa:Procedure` |
| `ssn:hasSubSystem` | `ssn:System` | `ssn:System` | Workbook `Common OPs` row 14 explicit domain/range |
| `ssn:implementedBy` | `sosa:Procedure` | `ssn:System` | Workbook `Common OPs` row 16; imported source restriction on `sosa:Procedure` |
| `ssn:implements` | `ssn:System` | `sosa:Procedure` | Workbook `Common OPs` row 17; imported source restrictions on systems and system subclasses |
| `ssn:inDeployment` | `sosa:Platform` | `ssn:Deployment` | Workbook `Common OPs` row 18; inverse of `ssn:deployedOnPlatform` |
| `sosa:isActedOnBy` | `sosa:ActuatableProperty` | `sosa:Actuation` | Workbook `Common OPs` row 19; inverse of `sosa:actsOnProperty` |
| `sosa:isObservedBy` | `sosa:ObservableProperty` | `sosa:Sensor` | Workbook `Common OPs` row 22; inverse of `sosa:observes` |
| `sosa:isSampleOf` | `sosa:Sample` | `sosa:FeatureOfInterest` | Workbook `Common OPs` row 26; inverse of `sosa:hasSample` |
| `ssn:isProxyFor` | `ssn:Stimulus` | `sosa:ObservableProperty` | Workbook `Common OPs` row 24; imported source restriction uses `sosa:ObservableProperty` |
| `sosa:madeActuation` | `sosa:Actuator` | `sosa:Actuation` | Workbook `Common OPs` row 27 source definition |
| `sosa:madeByActuator` | `sosa:Actuation` | `sosa:Actuator` | Workbook `Common OPs` row 28; inverse of `sosa:madeActuation` |
| `sosa:madeBySampler` | `sosa:Sampling` | `sosa:Sampler` | Workbook `Common OPs` row 29 explicit domain/range |
| `sosa:madeBySensor` | `sosa:Observation` | `sosa:Sensor` | Workbook `Common OPs` row 30 explicit domain/range |
| `sosa:madeObservation` | `sosa:Sensor` | `sosa:Observation` | Workbook `Common OPs` row 31; inverse of `sosa:madeBySensor` |
| `sosa:madeSampling` | `sosa:Sampler` | `sosa:Sampling` | Workbook `Common OPs` row 32; inverse of `sosa:madeBySampler` |
| `sosa:observedProperty` | `sosa:Observation` | `sosa:ObservableProperty` | Workbook `Common OPs` row 33; imported source restrictions use `sosa:ObservableProperty` |
| `sosa:observes` | `sosa:Sensor` | `sosa:ObservableProperty` | Workbook `Common OPs` row 34; imported source restrictions use `sosa:ObservableProperty` |
| `ssn:wasOriginatedBy` | `sosa:Observation` | `ssn:Stimulus` | Workbook `Common OPs` row 37; imported source restrictions |
| `ssn-system:hasOperatingRange` | `ssn:System` | `ssn-system:OperatingRange` | Workbook `System Capability` row 10; imported source restrictions |
| `ssn-system:hasSurvivalRange` | `ssn:System` | `ssn-system:SurvivalRange` | Workbook `System Capability` row 12; imported source restrictions |
| `ssn-system:hasSystemCapability` | `ssn:System` | `ssn-system:SystemCapability` | Workbook `System Capability` row 13; imported source restrictions |

## Skipped Or Ambiguous Candidates

These rows were inventoried but not placed in the full test batch.

| Source row or property | Reason held out |
| --- | --- |
| `sosa:hasFeatureOfInterest` | Requires a union domain over `sosa:Observation`, `sosa:Actuation`, and `sosa:Sampling`; not a simple named-class source-level axiom. |
| `sosa:hasResult` and `sosa:isResultOf` | Domain/range are mixed across observations, actuations, samplings, results, and samples; needs a separate union/disjunction review. |
| `sosa:hosts` and `sosa:isHostedBy` | Hosted entity side is a source-level union over sensors, actuators, samplers, and platforms; also already has property-chain sensitivity. |
| `sosa:usedProcedure` | Domain is a union over observation, actuation, and sampling process classes. |
| `ssn:forProperty`, `ssn:hasProperty`, and `ssn:isPropertyOf` | Broad generic property pattern with prior reasoner-sensitive modeling history; not suitable for a broad rdfs domain/range shortcut in this pass. |
| `sosa:phenomenonTime` | Range is `time:TemporalEntity`, not a SOSA/SSN/SSN Systems source class. |
| `sosa:hasSimpleResult` and `sosa:resultTime` | Datatype-property rows; out of scope for this source-class object-property pass. |
| `ssn-system:inCondition` | Source-side domain is a union over `OperatingRange`, `SurvivalRange`, and `SystemCapability`; not a simple named-class axiom. |
| `ssn-system:qualityOfObservation` | Source definition links observation quality and result quality, but a precise source-level range class is not explicit enough for this pass. |
| Sample Relationship properties | Workbook intentionally uses `schema:domainIncludes`/`schema:rangeIncludes` rather than `rdfs:domain`/`rdfs:range`; do not convert without a separate modeling decision. |

## HermiT Results

| Variant | Added triples | Triple count | Return code | Reasoned output | `owl:Nothing` count | Unsat set | Sample simplicity blocker |
| --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| Baseline current graph | 0 | 15480 | 0 | yes | 0 | none | no |
| Full supported candidate batch | 56 | 15536 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | no |
| Full batch minus `sosa:madeByActuator` | 54 | 15534 | 0 | yes | 0 | none | no |
| `sosa:isObservedBy` only | 2 | 15482 | 0 | yes | 0 | none | no |

## Split-Test Results

The original 54-axiom batch without `sosa:isObservedBy` showed the same reducer pattern. Adding `sosa:isObservedBy` did not change the result.

| Source group | Added triples | HermiT result | Unsat set |
| --- | ---: | --- | --- |
| Actuation-side properties | 8 | fail | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` |
| Deployment properties | 8 | clean | none |
| Implementation properties | 4 | clean | none |
| Input/Output properties | 4 | clean | none |
| Sampling properties | 8 | clean | none |
| Sensor/Observation/Stimulus properties | 14 | clean | none |
| Supplemental `sosa:isObservedBy` inverse property | 2 | clean | none |
| SSN Systems range/capability properties | 6 | clean | none |
| Core system part property | 2 | clean | none |
| Full batch minus actuation-side properties | 48 | clean | none |
| Full batch minus `sosa:madeByActuator` | 54 | clean | none |

## Focused `sosa:madeByActuator` Result

| Variant | Added triples | HermiT result | Unsat set |
| --- | ---: | --- | --- |
| `sosa:madeByActuator rdfs:domain sosa:Actuation` only | 1 | clean | none |
| `sosa:madeByActuator rdfs:range sosa:Actuator` only | 1 | fail | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` |
| Both `sosa:madeByActuator` domain and range | 2 | fail | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` |

The smallest tested failing axiom is:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

This does not prove that the source-level range is semantically wrong. It shows that adding this range axiom is not HermiT-safe in the current merged full-OWL profile.

## Active Edits

No active TTL or workbook edits were made.

Because the full supported candidate batch failed HermiT, this branch follows the requested stop condition:

- Do not edit `SSN2BFO.ttl`.
- Do not edit `Current_SOSA-SSN to BFO-CCO.xlsx`.
- Do not regenerate canonical mapping audit or ELK reports.

## Mapping Audit And ELK

No active mapping files were changed, so canonical audit and ELK reports were not regenerated.

The expected validation baseline remains:

- Mapping audit: two expected `sosa:Sensor` version-alignment issues only.
- ELK instance mapping entailment: PASS with 6 direct class expectations, 77 direct property expectations, 5 property-chain expectations, 2 restriction expectations, and 0 uncovered active mappings.

## Recommendation

Do not add the full source-level domain/range batch as one mapping change.

Recommended next step:

- Split the work into a safe-subset branch that excludes `sosa:madeByActuator rdfs:range sosa:Actuator`.
- Keep the `sosa:madeByActuator` range axiom deferred for a focused HermiT explanation branch.
- If the safe subset is pursued, retest exactly the 54 clean source-level axioms in a mapping-change branch and update the corresponding workbook rows there.

Suggested branch names:

- `fix/add-hermit-safe-source-domain-range-subset`
- `review/explain-madeByActuator-range-hermit-interaction`
