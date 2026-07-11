# Object-Property Domain/Range Fallback Policy Audit

## Scope

This report audits current source object-property mappings under the proposed fallback policy:

> A local `rdfs:domain` or `rdfs:range` assertion should be present in `SSN2BFO.ttl` only when there is no candidate mapping for that source object property using `rdfs:subPropertyOf`, `owl:equivalentProperty`, or `owl:propertyChainAxiom`.

This is a report-only audit. It does not edit `SSN2BFO.ttl`, the workbook, imports, tools, examples, release artifacts, or existing reports.

Important scope distinction: this audit considers only locally asserted `rdfs:domain` / `rdfs:range` triples in `SSN2BFO.ttl` and mapping/output assertions represented in the workbook. Imported source ontology axioms in `imports/sosa.ttl`, `imports/ssn.ttl`, and `imports/ssn-systems.ttl` are inspected as evidence, but they are not candidates for removal.

## Method

Inputs inspected:

- `SSN2BFO.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`
- `imports/sosa.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `reports/hermit-clean-source-domain-range-axioms.md`
- `reports/ssn-systems-domain-range-operationalization-evaluation.md`
- `reports/actuation-agent-property-mapping-deferral.md`
- `reports/madeByActuator-range-after-agent-deferral.md`
- `reports/input-output-cco-mapping-rationale-cleanup.md`
- `reports/deferred-reactivation-results.md`
- `reports/sosa-inverse-property-pairs-full-closure-analysis.md`

The inventory distinguishes:

- **Active candidate**: current TTL has `rdfs:subPropertyOf`, `owl:equivalentProperty`, or `owl:propertyChainAxiom` for the source property.
- **Viable/inactive candidate**: workbook has a candidate mapping using one of the policy predicates, but it is not active and is not marked rejected/deferred. No clear cases were found in the current object-property inventory.
- **Deferred candidate**: prior or current documentation says a direct mapping remains deferred pending a safer representation.
- **Rejected candidate**: current documentation says the prior direct CCO mapping is removed/rejected or no longer intended.
- **None**: no policy candidate identified.

## Inventory Summary

| Item | Count |
|---|---:|
| Source object properties inventoried | 43 |
| Properties with local `rdfs:domain`/`rdfs:range` in `SSN2BFO.ttl` | 31 |
| Local domain triples | 31 |
| Local range triples | 31 |
| Strict Policy A affected properties | 28 |
| Policy A affected properties with active candidates | 20 |
| Policy A affected properties with only deferred/rejected candidates | 8 |

## Full Object-Property Inventory

| Source property | Workbook row | Local domain | Local range | Source-import domain/range evidence | Candidate status | Candidate details | Policy A action |
|---|---|---|---|---|---|---|---|
| `sosa:actsOnProperty` | Common OPs row 2 | `sosa:Actuation` | `sosa:ActuatableProperty` | schema_domainIncludes: sosa:Actuation; schema_rangeIncludes: sosa:ActuatableProperty | `active` | `sosa:actsOnProperty rdfs:subPropertyOf cco:ont00001834`<br>`subPropertyOf cco:affects` | remove local domain/range |
| `sosa:hasFeatureOfInterest` | Common OPs row 8 | none | none | schema_domainIncludes: sosa:Observation, sosa:Actuation, sosa:Sampling; schema_rangeIncludes: sosa:FeatureOfInterest, sosa:Sample | `none` | none | no local rdfs domain/range |
| `sosa:hasResult` | Common OPs row 12 | none | none | schema_domainIncludes: sosa:Observation, sosa:Actuation, sosa:Sampling; schema_rangeIncludes: sosa:Sample, sosa:Result | `active` | `sosa:hasResult rdfs:subPropertyOf cco:ont00001986`<br>`subPropertyOf cco:has_output` | no local rdfs domain/range |
| `sosa:hasSample` | Common OPs row 13 | `sosa:FeatureOfInterest` | `sosa:Sample` | schema_domainIncludes: sosa:FeatureOfInterest; schema_rangeIncludes: sosa:Sample | `active` | `sosa:hasSample owl:propertyChainAxiom ( cco:ont00001873 bfo:BFO_0000084 ) `<br>`sosa:hasSample owl:propertyChainAxiom (...)` | remove local domain/range |
| `sosa:hosts` | Common OPs row 15 | none | none | schema_domainIncludes: sosa:Platform; schema_rangeIncludes: sosa:Sampler, sosa:Actuator, sosa:Sensor, sosa:Platform | `active` | `sosa:hosts owl:propertyChainAxiom ( bfo:bearer_of bfo:has_realization bfo:has_participant ) `<br>`sosa:hosts owl:propertyChainAxiom (...)` | no local rdfs domain/range |
| `sosa:isActedOnBy` | Common OPs row 19 | `sosa:ActuatableProperty` | `sosa:Actuation` | schema_domainIncludes: sosa:ActuatableProperty; schema_rangeIncludes: sosa:Actuation | `active` | `sosa:isActedOnBy rdfs:subPropertyOf cco:ont00001886`<br>`sosa:isActedOnBy rdfs:subPropertyOf cco:ont00001886 ` | remove local domain/range |
| `sosa:isFeatureOfInterestOf` | Common OPs row 20 | none | none | schema_domainIncludes: sosa:FeatureOfInterest, sosa:Sample; schema_rangeIncludes: sosa:Observation, sosa:Actuation, sosa:Sampling | `none` | none | no local rdfs domain/range |
| `sosa:isHostedBy` | Common OPs row 21 | none | none | schema_domainIncludes: sosa:Sensor, sosa:Platform, sosa:Sampler, sosa:Actuator; schema_rangeIncludes: sosa:Platform | `active` | `sosa:isHostedBy owl:propertyChainAxiom ( bfo:participates_in bfo:realizes bfo:inheres_in ) `<br>`sosa:isHostedBy owl:propertyChainAxiom (...)` | no local rdfs domain/range |
| `sosa:isObservedBy` | Common OPs row 22 | `sosa:ObservableProperty` | `sosa:Sensor` | schema_domainIncludes: sosa:ObservableProperty; schema_rangeIncludes: sosa:Sensor | `none` | none | retain local domain/range |
| `sosa:isResultOf` | Common OPs row 25 | none | none | schema_domainIncludes: sosa:Sample, sosa:Result; schema_rangeIncludes: sosa:Sampling, sosa:Observation, sosa:Actuation | `active` | `sosa:isResultOf rdfs:subPropertyOf cco:ont00001816`<br>`sosa:isResultOf rdfs:subPropertyOf cco:ont00001816 ` | no local rdfs domain/range |
| `sosa:isSampleOf` | Common OPs row 26 | `sosa:Sample` | `sosa:FeatureOfInterest` | schema_domainIncludes: sosa:Sample; schema_rangeIncludes: sosa:FeatureOfInterest | `active` | `sosa:isSampleOf owl:propertyChainAxiom ( bfo:BFO_0000101 cco:ont00001938 ) `<br>`sosa:isSampleOf owl:propertyChainAxiom (...)` | remove local domain/range |
| `sosa:madeActuation` | Common OPs row 27 | `sosa:Actuator` | `sosa:Actuation` | schema_domainIncludes: sosa:Actuator; schema_rangeIncludes: sosa:Actuation | `deferred` | `sosa:madeActuation rdfs:subPropertyOf cco:ont00001787` | remove local domain/range |
| `sosa:madeByActuator` | Common OPs row 28 | `sosa:Actuation` | `sosa:Actuator` | schema_domainIncludes: sosa:Actuation; schema_rangeIncludes: sosa:Actuator | `deferred` | `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` | remove local domain/range |
| `sosa:madeBySampler` | Common OPs row 29 | `sosa:Sampling` | `sosa:Sampler` | schema_domainIncludes: sosa:Sampling; schema_rangeIncludes: sosa:Sampler | `active` | `sosa:madeBySampler rdfs:subPropertyOf cco:has_agent `<br>`sosa:madeBySampler rdfs:subPropertyOf cco:ont00001833` | remove local domain/range |
| `sosa:madeBySensor` | Common OPs row 30 | `sosa:Observation` | `sosa:Sensor` | schema_domainIncludes: sosa:Observation; schema_rangeIncludes: sosa:Sensor | `active` | `sosa:madeBySensor rdfs:subPropertyOf cco:has_agent `<br>`sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833` | remove local domain/range |
| `sosa:madeObservation` | Common OPs row 31 | `sosa:Sensor` | `sosa:Observation` | schema_domainIncludes: sosa:Sensor; schema_rangeIncludes: sosa:Observation | `active` | `sosa:madeObservation rdfs:subPropertyOf cco:ont00001787`<br>`sosa:madeObservation rdfs:subPropertyOf cco:ont00001787 ` | remove local domain/range |
| `sosa:madeSampling` | Common OPs row 32 | `sosa:Sampler` | `sosa:Sampling` | schema_domainIncludes: sosa:Sampler; schema_rangeIncludes: sosa:Sampling | `active` | `sosa:madeSampling rdfs:subPropertyOf cco:ont00001787`<br>`sosa:madeSampling rdfs:subPropertyOf cco:ont00001787 ` | remove local domain/range |
| `sosa:observedProperty` | Common OPs row 33 | `sosa:Observation` | `sosa:ObservableProperty` | schema_domainIncludes: sosa:Observation; schema_rangeIncludes: sosa:ObservableProperty | `rejected` | `sosa:observedProperty rdfs:subPropertyOf cco:ont00001921` | remove local domain/range |
| `sosa:observes` | Common OPs row 34 | `sosa:Sensor` | `sosa:ObservableProperty` | schema_domainIncludes: sosa:Sensor; schema_rangeIncludes: sosa:ObservableProperty | `active` | `sosa:observes rdfs:subPropertyOf ssn:forProperty`<br>`sosa:observes rdfs:subPropertyOf ssn:forProperty ` | remove local domain/range |
| `sosa:phenomenonTime` | Common OPs row 35 | none | none | schema_domainIncludes: sosa:Observation, sosa:Actuation, sosa:Sampling; schema_rangeIncludes: <http://www.w3.org/2006/time#TemporalEntity> | `none` | none | no local rdfs domain/range |
| `sampling:hasSampleRelationship` | Sample Relationship row 2 | none | none | none found | `none` | none | no local rdfs domain/range |
| `sampling:natureOfRelationship` | Sample Relationship row 3 | none | none | none found | `none` | none | no local rdfs domain/range |
| `sampling:relatedSample` | Sample Relationship row 4 | none | none | none found | `none` | none | no local rdfs domain/range |
| `sosa:usedProcedure` | Common OPs row 36 | none | none | schema_domainIncludes: sosa:Observation, sosa:Actuation, sosa:Sampling; schema_rangeIncludes: sosa:Procedure | `active` | `sosa:usedProcedure rdfs:subPropertyOf cco:ont00001920`<br>`subPropertyOf cco:prescribed_by` | no local rdfs domain/range |
| `ssn-system:hasOperatingProperty` | System Capability row 9 | `ssn-system:OperatingRange` | `ssn-system:OperatingProperty` | none found | `deferred` | `ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194` | remove local domain/range |
| `ssn-system:hasOperatingRange` | System Capability row 10 | `ssn:System` | `ssn-system:OperatingRange` | none found | `active` | `ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:BFO_0000196`<br>`ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:bearer_of ` | remove local domain/range |
| `ssn-system:hasSurvivalProperty` | System Capability row 11 | `ssn-system:SurvivalRange` | `ssn-system:SurvivalProperty` | none found | `deferred` | `ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194` | remove local domain/range |
| `ssn-system:hasSurvivalRange` | System Capability row 12 | `ssn:System` | `ssn-system:SurvivalRange` | none found | `active` | `ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:BFO_0000196`<br>`ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:bearer_of ` | remove local domain/range |
| `ssn-system:hasSystemCapability` | System Capability row 13 | `ssn:System` | `ssn-system:SystemCapability` | none found | `active` | `ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:BFO_0000196`<br>`ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:bearer_of ` | remove local domain/range |
| `ssn-system:hasSystemProperty` | System Capability row 14 | `ssn-system:SystemCapability` | `ssn-system:SystemProperty` | none found | `deferred` | `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194` | remove local domain/range |
| `ssn-system:qualityOfObservation` | System Capability row 23 | none | none | none found | `active` | `ssn-system:qualityOfObservation rdfs:subPropertyOf cco:has_output `<br>`ssn-system:qualityOfObservation rdfs:subPropertyOf cco:ont00001986` | no local rdfs domain/range |
| `ssn:deployedOnPlatform` | Common OPs row 3 | `ssn:Deployment` | `sosa:Platform` | none found | `active` | `ssn:deployedOnPlatform rdfs:subPropertyOf bfo:BFO_0000057`<br>`ssn:deployedOnPlatform rdfs:subPropertyOf bfo:has_participant ` | remove local domain/range |
| `ssn:deployedSystem` | Common OPs row 4 | `ssn:Deployment` | `ssn:System` | none found | `active` | `ssn:deployedSystem rdfs:subPropertyOf bfo:BFO_0000057`<br>`ssn:deployedSystem rdfs:subPropertyOf bfo:has_participant ` | remove local domain/range |
| `ssn:detects` | Common OPs row 5 | `sosa:Sensor` | `ssn:Stimulus` | none found | `active` | `ssn:detects rdfs:subPropertyOf cco:is_affected_by `<br>`ssn:detects rdfs:subPropertyOf cco:ont00001886` | remove local domain/range |
| `ssn:hasDeployment` | Common OPs row 7 | `ssn:System` | `ssn:Deployment` | none found | `active` | `ssn:hasDeployment rdfs:subPropertyOf bfo:BFO_0000056`<br>`ssn:hasDeployment rdfs:subPropertyOf bfo:BFO_0000056 ` | remove local domain/range |
| `ssn:hasInput` | Common OPs row 9 | `sosa:Procedure` | `ssn:Input` | none found | `rejected` | `ssn:hasInput rdfs:subPropertyOf cco:ont00001921` | remove local domain/range |
| `ssn:hasOutput` | Common OPs row 10 | `sosa:Procedure` | `ssn:Output` | none found | `rejected` | `ssn:hasOutput rdfs:subPropertyOf cco:ont00001986` | remove local domain/range |
| `ssn:hasSubSystem` | Common OPs row 14 | `ssn:System` | `ssn:System` | none found | `active` | `ssn:hasSubSystem rdfs:subPropertyOf bfo:BFO_0000178`<br>`ssn:hasSubSystem rdfs:subPropertyOf bfo:has_continuant_part ` | remove local domain/range |
| `ssn:implementedBy` | Common OPs row 16 | `sosa:Procedure` | `ssn:System` | none found | `active` | `ssn:implementedBy owl:propertyChainAxiom ( cco:ont00001942 cco:ont00001833 ) `<br>`ssn:implementedBy owl:propertyChainAxiom (...)` | remove local domain/range |
| `ssn:implements` | Common OPs row 17 | `ssn:System` | `sosa:Procedure` | none found | `none` | none | retain local domain/range |
| `ssn:inDeployment` | Common OPs row 18 | `sosa:Platform` | `ssn:Deployment` | none found | `active` | `ssn:inDeployment rdfs:subPropertyOf bfo:BFO_0000056`<br>`ssn:inDeployment rdfs:subPropertyOf bfo:BFO_0000056 ` | remove local domain/range |
| `ssn:isProxyFor` | Common OPs row 24 | `ssn:Stimulus` | `sosa:ObservableProperty` | none found | `none` | none | retain local domain/range |
| `ssn:wasOriginatedBy` | Common OPs row 37 | `sosa:Observation` | `ssn:Stimulus` | none found | `active` | `ssn:wasOriginatedBy rdfs:subPropertyOf cco:ont00001962`<br>`subPropertyOf cco:process_started_by` | remove local domain/range |

## Policy Variants

The requested policy is Policy A. Policies B and C are sensitivity analyses only.

| Policy | Candidate interpretation | Properties losing local domain/range | Domain triples removed | Range triples removed | Properties retaining local domain/range |
|---|---|---:|---:|---:|---|
| A | Any active, viable, deferred, or rejected candidate prevents local domain/range. | 28 | 28 | 28 | `sosa:isObservedBy`, `ssn:implements`, `ssn:isProxyFor` |
| B | Only active or still-viable candidates prevent local domain/range; rejected and deferred candidates are separately identified and retained. | 20 | 20 | 20 | `sosa:isObservedBy`, `sosa:madeActuation`, `sosa:madeByActuator`, `sosa:observedProperty`, `ssn-system:hasOperatingProperty`, `ssn-system:hasSurvivalProperty`, `ssn-system:hasSystemProperty`, `ssn:hasInput`, `ssn:hasOutput`, `ssn:implements`, `ssn:isProxyFor` |
| C | Only active TTL candidates prevent local domain/range. | 20 | 20 | 20 | `sosa:isObservedBy`, `sosa:madeActuation`, `sosa:madeByActuator`, `sosa:observedProperty`, `ssn-system:hasOperatingProperty`, `ssn-system:hasSurvivalProperty`, `ssn-system:hasSystemProperty`, `ssn:hasInput`, `ssn:hasOutput`, `ssn:implements`, `ssn:isProxyFor` |

### Policy A Losing Properties

`sosa:actsOnProperty`, `sosa:hasSample`, `sosa:isActedOnBy`, `sosa:isSampleOf`, `sosa:madeActuation`, `sosa:madeByActuator`, `sosa:madeBySampler`, `sosa:madeBySensor`, `sosa:madeObservation`, `sosa:madeSampling`, `sosa:observedProperty`, `sosa:observes`, `ssn-system:hasOperatingProperty`, `ssn-system:hasOperatingRange`, `ssn-system:hasSurvivalProperty`, `ssn-system:hasSurvivalRange`, `ssn-system:hasSystemCapability`, `ssn-system:hasSystemProperty`, `ssn:deployedOnPlatform`, `ssn:deployedSystem`, `ssn:detects`, `ssn:hasDeployment`, `ssn:hasInput`, `ssn:hasOutput`, `ssn:hasSubSystem`, `ssn:implementedBy`, `ssn:inDeployment`, `ssn:wasOriginatedBy`

### Policy A Retaining Local Domain/Range

Only three local source-level domain/range blocks remain under strict Policy A because no active, viable, deferred, or rejected policy candidate was identified for them:

- `sosa:isObservedBy`: domain `sosa:ObservableProperty`, range `sosa:Sensor`
- `ssn:implements`: domain `ssn:System`, range `sosa:Procedure`
- `ssn:isProxyFor`: domain `ssn:Stimulus`, range `sosa:ObservableProperty`

## Exact Policy A Local Triples To Remove

Strict Policy A would remove these local `SSN2BFO.ttl` triples. Imported source ontology domain/range notes remain untouched.

```ttl
sosa:actsOnProperty rdfs:domain sosa:Actuation .
sosa:actsOnProperty rdfs:range sosa:ActuatableProperty .
sosa:hasSample rdfs:domain sosa:FeatureOfInterest .
sosa:hasSample rdfs:range sosa:Sample .
sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty .
sosa:isActedOnBy rdfs:range sosa:Actuation .
sosa:isSampleOf rdfs:domain sosa:Sample .
sosa:isSampleOf rdfs:range sosa:FeatureOfInterest .
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeByActuator rdfs:range sosa:Actuator .
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
ssn-system:hasOperatingProperty rdfs:domain ssn-system:OperatingRange .
ssn-system:hasOperatingProperty rdfs:range ssn-system:OperatingProperty .
ssn-system:hasOperatingRange rdfs:domain ssn:System .
ssn-system:hasOperatingRange rdfs:range ssn-system:OperatingRange .
ssn-system:hasSurvivalProperty rdfs:domain ssn-system:SurvivalRange .
ssn-system:hasSurvivalProperty rdfs:range ssn-system:SurvivalProperty .
ssn-system:hasSurvivalRange rdfs:domain ssn:System .
ssn-system:hasSurvivalRange rdfs:range ssn-system:SurvivalRange .
ssn-system:hasSystemCapability rdfs:domain ssn:System .
ssn-system:hasSystemCapability rdfs:range ssn-system:SystemCapability .
ssn-system:hasSystemProperty rdfs:domain ssn-system:SystemCapability .
ssn-system:hasSystemProperty rdfs:range ssn-system:SystemProperty .
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
ssn:inDeployment rdfs:domain sosa:Platform .
ssn:inDeployment rdfs:range ssn:Deployment .
ssn:wasOriginatedBy rdfs:domain sosa:Observation .
ssn:wasOriginatedBy rdfs:range ssn:Stimulus .
```

## Deferred And Rejected Candidate Cases

Strict Policy A removes fallback domain/range even when the only candidate is deferred or rejected. These are the controversial cases the sensitivity analysis is meant to expose.

| Property | Status | Local domain/range removed by Policy A | Candidate / decision evidence | Policy B/C treatment |
|---|---|---|---|---|
| `sosa:madeActuation` | `deferred` | domain sosa:Actuator; range sosa:Actuation | `sosa:madeActuation rdfs:subPropertyOf cco:ont00001787` | retained under Policy B and Policy C because no active or viable candidate remains |
| `sosa:madeByActuator` | `deferred` | domain sosa:Actuation; range sosa:Actuator | `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` | retained under Policy B and Policy C because no active or viable candidate remains |
| `sosa:observedProperty` | `rejected` | domain sosa:Observation; range sosa:ObservableProperty | `sosa:observedProperty rdfs:subPropertyOf cco:ont00001921` | retained under Policy B and Policy C because no active or viable candidate remains |
| `ssn-system:hasOperatingProperty` | `deferred` | domain ssn-system:OperatingRange; range ssn-system:OperatingProperty | `ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194` | retained under Policy B and Policy C because no active or viable candidate remains |
| `ssn-system:hasSurvivalProperty` | `deferred` | domain ssn-system:SurvivalRange; range ssn-system:SurvivalProperty | `ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194` | retained under Policy B and Policy C because no active or viable candidate remains |
| `ssn-system:hasSystemProperty` | `deferred` | domain ssn-system:SystemCapability; range ssn-system:SystemProperty | `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194` | retained under Policy B and Policy C because no active or viable candidate remains |
| `ssn:hasInput` | `rejected` | domain sosa:Procedure; range ssn:Input | `ssn:hasInput rdfs:subPropertyOf cco:ont00001921` | retained under Policy B and Policy C because no active or viable candidate remains |
| `ssn:hasOutput` | `rejected` | domain sosa:Procedure; range ssn:Output | `ssn:hasOutput rdfs:subPropertyOf cco:ont00001986` | retained under Policy B and Policy C because no active or viable candidate remains |

These eight properties are the main modeling caution for strict Policy A: `sosa:madeActuation`, `sosa:madeByActuator`, `ssn:hasInput`, `ssn:hasOutput`, `sosa:observedProperty`, `ssn-system:hasOperatingProperty`, `ssn-system:hasSurvivalProperty`, and `ssn-system:hasSystemProperty`. In each case, strict Policy A removes useful local source-level typing even though no active BFO/CCO subproperty mapping remains.

## Special Cases

| Property | Workbook row | Local domain | Local range | Candidate status | Policy A action | Candidate details |
|---|---|---|---|---|---|---|
| `sosa:madeActuation` | Common OPs row 27 | `sosa:Actuator` | `sosa:Actuation` | `deferred` | remove local domain/range under Policy A | `sosa:madeActuation rdfs:subPropertyOf cco:ont00001787` |
| `sosa:madeByActuator` | Common OPs row 28 | `sosa:Actuation` | `sosa:Actuator` | `deferred` | remove local domain/range under Policy A | `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` |
| `sosa:madeObservation` | Common OPs row 31 | `sosa:Sensor` | `sosa:Observation` | `active` | remove local domain/range under Policy A | `sosa:madeObservation rdfs:subPropertyOf cco:ont00001787`<br>`sosa:madeObservation rdfs:subPropertyOf cco:ont00001787 ` |
| `sosa:madeBySensor` | Common OPs row 30 | `sosa:Observation` | `sosa:Sensor` | `active` | remove local domain/range under Policy A | `sosa:madeBySensor rdfs:subPropertyOf cco:has_agent `<br>`sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833` |
| `sosa:madeSampling` | Common OPs row 32 | `sosa:Sampler` | `sosa:Sampling` | `active` | remove local domain/range under Policy A | `sosa:madeSampling rdfs:subPropertyOf cco:ont00001787`<br>`sosa:madeSampling rdfs:subPropertyOf cco:ont00001787 ` |
| `sosa:madeBySampler` | Common OPs row 29 | `sosa:Sampling` | `sosa:Sampler` | `active` | remove local domain/range under Policy A | `sosa:madeBySampler rdfs:subPropertyOf cco:has_agent `<br>`sosa:madeBySampler rdfs:subPropertyOf cco:ont00001833` |
| `sosa:actsOnProperty` | Common OPs row 2 | `sosa:Actuation` | `sosa:ActuatableProperty` | `active` | remove local domain/range under Policy A | `sosa:actsOnProperty rdfs:subPropertyOf cco:ont00001834`<br>`subPropertyOf cco:affects` |
| `sosa:isActedOnBy` | Common OPs row 19 | `sosa:ActuatableProperty` | `sosa:Actuation` | `active` | remove local domain/range under Policy A | `sosa:isActedOnBy rdfs:subPropertyOf cco:ont00001886`<br>`sosa:isActedOnBy rdfs:subPropertyOf cco:ont00001886 ` |
| `sosa:hasResult` | Common OPs row 12 | none | none | `active` | no local rdfs:domain/range to remove | `sosa:hasResult rdfs:subPropertyOf cco:ont00001986`<br>`subPropertyOf cco:has_output` |
| `sosa:isResultOf` | Common OPs row 25 | none | none | `active` | no local rdfs:domain/range to remove | `sosa:isResultOf rdfs:subPropertyOf cco:ont00001816`<br>`sosa:isResultOf rdfs:subPropertyOf cco:ont00001816 ` |
| `sosa:hosts` | Common OPs row 15 | none | none | `active` | no local rdfs:domain/range to remove | `sosa:hosts owl:propertyChainAxiom ( bfo:bearer_of bfo:has_realization bfo:has_participant ) `<br>`sosa:hosts owl:propertyChainAxiom (...)` |
| `sosa:isHostedBy` | Common OPs row 21 | none | none | `active` | no local rdfs:domain/range to remove | `sosa:isHostedBy owl:propertyChainAxiom ( bfo:participates_in bfo:realizes bfo:inheres_in ) `<br>`sosa:isHostedBy owl:propertyChainAxiom (...)` |
| `sosa:observes` | Common OPs row 34 | `sosa:Sensor` | `sosa:ObservableProperty` | `active` | remove local domain/range under Policy A | `sosa:observes rdfs:subPropertyOf ssn:forProperty`<br>`sosa:observes rdfs:subPropertyOf ssn:forProperty ` |
| `sosa:isObservedBy` | Common OPs row 22 | `sosa:ObservableProperty` | `sosa:Sensor` | `none` | retain local domain/range under Policy A | none |
| `ssn:hasInput` | Common OPs row 9 | `sosa:Procedure` | `ssn:Input` | `rejected` | remove local domain/range under Policy A | `ssn:hasInput rdfs:subPropertyOf cco:ont00001921` |
| `ssn:hasOutput` | Common OPs row 10 | `sosa:Procedure` | `ssn:Output` | `rejected` | remove local domain/range under Policy A | `ssn:hasOutput rdfs:subPropertyOf cco:ont00001986` |
| `sosa:observedProperty` | Common OPs row 33 | `sosa:Observation` | `sosa:ObservableProperty` | `rejected` | remove local domain/range under Policy A | `sosa:observedProperty rdfs:subPropertyOf cco:ont00001921` |
| `ssn-system:hasOperatingProperty` | System Capability row 9 | `ssn-system:OperatingRange` | `ssn-system:OperatingProperty` | `deferred` | remove local domain/range under Policy A | `ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194` |
| `ssn-system:hasSurvivalProperty` | System Capability row 11 | `ssn-system:SurvivalRange` | `ssn-system:SurvivalProperty` | `deferred` | remove local domain/range under Policy A | `ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194` |
| `ssn-system:hasSystemProperty` | System Capability row 14 | `ssn-system:SystemCapability` | `ssn-system:SystemProperty` | `deferred` | remove local domain/range under Policy A | `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194` |
| `ssn-system:hasOperatingRange` | System Capability row 10 | `ssn:System` | `ssn-system:OperatingRange` | `active` | remove local domain/range under Policy A | `ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:BFO_0000196`<br>`ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:bearer_of ` |
| `ssn-system:hasSurvivalRange` | System Capability row 12 | `ssn:System` | `ssn-system:SurvivalRange` | `active` | remove local domain/range under Policy A | `ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:BFO_0000196`<br>`ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:bearer_of ` |
| `ssn-system:hasSystemCapability` | System Capability row 13 | `ssn:System` | `ssn-system:SystemCapability` | `active` | remove local domain/range under Policy A | `ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:BFO_0000196`<br>`ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:bearer_of ` |
| `ssn-system:qualityOfObservation` | System Capability row 23 | none | none | `active` | no local rdfs:domain/range to remove | `ssn-system:qualityOfObservation rdfs:subPropertyOf cco:has_output `<br>`ssn-system:qualityOfObservation rdfs:subPropertyOf cco:ont00001986` |

## Temporary Simulation

Temporary files were written under `/tmp/ssn-to-bfo-object-property-domain-range-fallback-policy-audit`. Each HermiT graph loaded the full local SOSA closure, then removed all `owl:imports` triples and the established sample simplicity blockers.

| Variant | Graph path | Triple count | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Unsat set |
|---|---|---:|---:|---|---:|---:|---|
| `baseline-current-full-sosa-closure` | `/tmp/ssn-to-bfo-object-property-domain-range-fallback-policy-audit/baseline-current-full-sosa-closure.ttl` | 15769 | 0 | yes | 0 | 0 | clean |
| `policy-A-strict` | `/tmp/ssn-to-bfo-object-property-domain-range-fallback-policy-audit/policy-A-strict.ttl` | 15713 | 0 | yes | 0 | 0 | clean |
| `policy-B-viable` | `/tmp/ssn-to-bfo-object-property-domain-range-fallback-policy-audit/policy-B-viable.ttl` | 15729 | 0 | yes | 0 | 0 | clean |

Both strict Policy A and Policy B temporary graphs remain HermiT-clean under the current full local SOSA closure profile.

## Mapping Audit And ELK Effects

The current mapping-audit and ELK tools do not count `rdfs:domain` / `rdfs:range` source-typing assertions as candidate direct mapping assertions. That is consistent with `tools/compare_mappings.py`, whose mapping predicate set excludes `rdfs:domain` and `rdfs:range`.

| Variant | Audit return | `ttl_candidate_mapping_assertions` | Audit issues | Issue categories | ELK return | ELK direct class | ELK direct property | ELK chains | ELK restrictions | Uncovered active mappings |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `baseline-current-full-sosa-closure` | 0 | 68 | 2 | missing_in_spreadsheet=1, missing_in_ttl=1 | 0 | 6 | 75 | 5 | 2 | 0 |
| `policy-A-strict` | 0 | 68 | 2 | missing_in_spreadsheet=1, missing_in_ttl=1 | 0 | 6 | 75 | 5 | 2 | 0 |
| `policy-B-viable` | 0 | 68 | 2 | missing_in_spreadsheet=1, missing_in_ttl=1 | 0 | 6 | 75 | 5 | 2 | 0 |

Result: Policy A and Policy B leave the audit and ELK expectation counts unchanged: `ttl_candidate_mapping_assertions=68`, two expected `sosa:Sensor` audit issues, ELK direct class expectations `6`, direct property expectations `75`, property-chain expectations `5`, restriction expectations `2`, and uncovered active mappings `0`.

## Source-Property Typing Effects

Strict Policy A removes exact local `rdfs:domain` / `rdfs:range` typing from all affected properties. For many SOSA properties, the source import still has `schema:domainIncludes` / `schema:rangeIncludes` notes, but those are not global OWL `rdfs:domain` / `rdfs:range` entailments. For many SSN and SSN Systems properties, no exact source-import global domain/range axiom was found. Therefore Policy A is HermiT-clean but materially weakens local source-property typing in examples or downstream data that rely on local `rdfs:domain` / `rdfs:range` entailments.

| Property | Local domain typing lost | Local range typing lost | Source-import evidence retained |
|---|---|---|---|
| `sosa:actsOnProperty` | `sosa:Actuation` | `sosa:ActuatableProperty` | schema_domainIncludes: sosa:Actuation; schema_rangeIncludes: sosa:ActuatableProperty |
| `sosa:hasSample` | `sosa:FeatureOfInterest` | `sosa:Sample` | schema_domainIncludes: sosa:FeatureOfInterest; schema_rangeIncludes: sosa:Sample |
| `sosa:isActedOnBy` | `sosa:ActuatableProperty` | `sosa:Actuation` | schema_domainIncludes: sosa:ActuatableProperty; schema_rangeIncludes: sosa:Actuation |
| `sosa:isSampleOf` | `sosa:Sample` | `sosa:FeatureOfInterest` | schema_domainIncludes: sosa:Sample; schema_rangeIncludes: sosa:FeatureOfInterest |
| `sosa:madeActuation` | `sosa:Actuator` | `sosa:Actuation` | schema_domainIncludes: sosa:Actuator; schema_rangeIncludes: sosa:Actuation |
| `sosa:madeByActuator` | `sosa:Actuation` | `sosa:Actuator` | schema_domainIncludes: sosa:Actuation; schema_rangeIncludes: sosa:Actuator |
| `sosa:madeBySampler` | `sosa:Sampling` | `sosa:Sampler` | schema_domainIncludes: sosa:Sampling; schema_rangeIncludes: sosa:Sampler |
| `sosa:madeBySensor` | `sosa:Observation` | `sosa:Sensor` | schema_domainIncludes: sosa:Observation; schema_rangeIncludes: sosa:Sensor |
| `sosa:madeObservation` | `sosa:Sensor` | `sosa:Observation` | schema_domainIncludes: sosa:Sensor; schema_rangeIncludes: sosa:Observation |
| `sosa:madeSampling` | `sosa:Sampler` | `sosa:Sampling` | schema_domainIncludes: sosa:Sampler; schema_rangeIncludes: sosa:Sampling |
| `sosa:observedProperty` | `sosa:Observation` | `sosa:ObservableProperty` | schema_domainIncludes: sosa:Observation; schema_rangeIncludes: sosa:ObservableProperty |
| `sosa:observes` | `sosa:Sensor` | `sosa:ObservableProperty` | schema_domainIncludes: sosa:Sensor; schema_rangeIncludes: sosa:ObservableProperty |
| `ssn-system:hasOperatingProperty` | `ssn-system:OperatingRange` | `ssn-system:OperatingProperty` | none found |
| `ssn-system:hasOperatingRange` | `ssn:System` | `ssn-system:OperatingRange` | none found |
| `ssn-system:hasSurvivalProperty` | `ssn-system:SurvivalRange` | `ssn-system:SurvivalProperty` | none found |
| `ssn-system:hasSurvivalRange` | `ssn:System` | `ssn-system:SurvivalRange` | none found |
| `ssn-system:hasSystemCapability` | `ssn:System` | `ssn-system:SystemCapability` | none found |
| `ssn-system:hasSystemProperty` | `ssn-system:SystemCapability` | `ssn-system:SystemProperty` | none found |
| `ssn:deployedOnPlatform` | `ssn:Deployment` | `sosa:Platform` | none found |
| `ssn:deployedSystem` | `ssn:Deployment` | `ssn:System` | none found |
| `ssn:detects` | `sosa:Sensor` | `ssn:Stimulus` | none found |
| `ssn:hasDeployment` | `ssn:System` | `ssn:Deployment` | none found |
| `ssn:hasInput` | `sosa:Procedure` | `ssn:Input` | none found |
| `ssn:hasOutput` | `sosa:Procedure` | `ssn:Output` | none found |
| `ssn:hasSubSystem` | `ssn:System` | `ssn:System` | none found |
| `ssn:implementedBy` | `sosa:Procedure` | `ssn:System` | none found |
| `ssn:inDeployment` | `sosa:Platform` | `ssn:Deployment` | none found |
| `ssn:wasOriginatedBy` | `sosa:Observation` | `ssn:Stimulus` | none found |

## Workbook Implications Under Policy A

The following workbook rows would need revision if strict Policy A is implemented. The `OWL Axiom` cell is shown exactly as currently recorded; an implementation branch would remove only the listed local domain/range lines from the cell and revise the rationale where it currently says source-level typing is active.

### `sosa:actsOnProperty` — `Common OPs` row 2

Current `OWL Axiom` cell:

```text
sosa:actsOnProperty rdfs:domain sosa:Actuation .
sosa:actsOnProperty rdfs:range sosa:ActuatableProperty .
subPropertyOf cco:affects
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Actuation and range sosa:ActuatableProperty. The existing CCO subproperty mapping remains unchanged.
```

Policy A would remove:

```ttl
sosa:actsOnProperty rdfs:domain sosa:Actuation .
sosa:actsOnProperty rdfs:range sosa:ActuatableProperty .
```

Candidate mapping remaining:

```text
sosa:actsOnProperty rdfs:subPropertyOf cco:ont00001834
subPropertyOf cco:affects
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:hasSample` — `Common OPs` row 13

Current `OWL Axiom` cell:

```text
sosa:hasSample rdfs:domain sosa:FeatureOfInterest ; rdfs:range sosa:Sample .
sosa:hasSample owl:propertyChainAxiom ( cco:ont00001873 bfo:BFO_0000084 ) .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:FeatureOfInterest and range sosa:Sample. Existing property-chain mapping remains unchanged.
```

Policy A would remove:

```ttl
sosa:hasSample rdfs:domain sosa:FeatureOfInterest .
sosa:hasSample rdfs:range sosa:Sample .
```

Candidate mapping remaining:

```text
sosa:hasSample owl:propertyChainAxiom ( cco:ont00001873 bfo:BFO_0000084 ) 
sosa:hasSample owl:propertyChainAxiom (...)
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:isActedOnBy` — `Common OPs` row 19

Current `OWL Axiom` cell:

```text
sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty .
sosa:isActedOnBy rdfs:range sosa:Actuation .
sosa:isActedOnBy owl:inverseOf sosa:actsOnProperty .
sosa:isActedOnBy rdfs:subPropertyOf cco:ont00001886 .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:ActuatableProperty and range sosa:Actuation. Existing inverse and CCO affected-by mapping notes remain unchanged.
```

Policy A would remove:

```ttl
sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty .
sosa:isActedOnBy rdfs:range sosa:Actuation .
```

Candidate mapping remaining:

```text
sosa:isActedOnBy rdfs:subPropertyOf cco:ont00001886
sosa:isActedOnBy rdfs:subPropertyOf cco:ont00001886 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:isSampleOf` — `Common OPs` row 26

Current `OWL Axiom` cell:

```text
sosa:isSampleOf rdfs:domain sosa:Sample .
sosa:isSampleOf rdfs:range sosa:FeatureOfInterest .
sosa:isSampleOf owl:inverseOf sosa:hasSample .
sosa:isSampleOf owl:propertyChainAxiom ( bfo:BFO_0000101 cco:ont00001938 ) .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Sample and range sosa:FeatureOfInterest. Existing inverse and property-chain mapping notes remain unchanged.
```

Policy A would remove:

```ttl
sosa:isSampleOf rdfs:domain sosa:Sample .
sosa:isSampleOf rdfs:range sosa:FeatureOfInterest .
```

Candidate mapping remaining:

```text
sosa:isSampleOf owl:propertyChainAxiom ( bfo:BFO_0000101 cco:ont00001938 ) 
sosa:isSampleOf owl:propertyChainAxiom (...)
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:madeActuation` — `Common OPs` row 27

Current `OWL Axiom` cell:

```text
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
```

Current `Reasoning` cell:

```text
OWL operationalization retains source-level domain/range typing: domain sosa:Actuator and range sosa:Actuation. Direct CCO agent-in mapping is deferred/removed as part of the paired actuation-agent deferral required for HermiT safety under the materialized SOSA import closure. This does not reject the intended agent semantics; future representation should be reviewed for HermiT-safe OWL or rule/COMS treatment.
```

Policy A would remove:

```ttl
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
```

Candidate mapping remaining:

```text
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:madeByActuator` — `Common OPs` row 28

Current `OWL Axiom` cell:

```text
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeByActuator rdfs:range sosa:Actuator .
sosa:madeByActuator owl:inverseOf sosa:madeActuation .
```

Current `Reasoning` cell:

```text
OWL operationalization now records source-level domain/range typing: domain sosa:Actuation and range sosa:Actuator. Direct CCO has-agent mapping remains deferred/removed as part of the paired actuation-agent deferral required for HermiT safety under the materialized SOSA import closure. This does not reject the intended agent semantics; future CCO/BFO agent representation should be reviewed for HermiT-safe OWL or rule/COMS treatment.
```

Policy A would remove:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeByActuator rdfs:range sosa:Actuator .
```

Candidate mapping remaining:

```text
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:madeBySampler` — `Common OPs` row 29

Current `OWL Axiom` cell:

```text
sosa:madeBySampler rdfs:domain sosa:Sampling .
sosa:madeBySampler rdfs:range sosa:Sampler .
sosa:madeBySampler rdfs:subPropertyOf cco:has_agent .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Sampling and range sosa:Sampler. The existing CCO has-agent mapping remains unchanged.
```

Policy A would remove:

```ttl
sosa:madeBySampler rdfs:domain sosa:Sampling .
sosa:madeBySampler rdfs:range sosa:Sampler .
```

Candidate mapping remaining:

```text
sosa:madeBySampler rdfs:subPropertyOf cco:has_agent 
sosa:madeBySampler rdfs:subPropertyOf cco:ont00001833
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:madeBySensor` — `Common OPs` row 30

Current `OWL Axiom` cell:

```text
sosa:madeBySensor rdfs:domain sosa:Observation .
sosa:madeBySensor rdfs:range sosa:Sensor .
sosa:madeBySensor rdfs:subPropertyOf cco:has_agent .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Observation and range sosa:Sensor. The existing CCO has-agent mapping remains unchanged.
```

Policy A would remove:

```ttl
sosa:madeBySensor rdfs:domain sosa:Observation .
sosa:madeBySensor rdfs:range sosa:Sensor .
```

Candidate mapping remaining:

```text
sosa:madeBySensor rdfs:subPropertyOf cco:has_agent 
sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:madeObservation` — `Common OPs` row 31

Current `OWL Axiom` cell:

```text
sosa:madeObservation rdfs:domain sosa:Sensor .
sosa:madeObservation rdfs:range sosa:Observation .
sosa:madeObservation owl:inverseOf sosa:madeBySensor .
sosa:madeObservation rdfs:subPropertyOf cco:ont00001787 .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Sensor and range sosa:Observation. Existing inverse and CCO agent-in mapping notes remain unchanged.
```

Policy A would remove:

```ttl
sosa:madeObservation rdfs:domain sosa:Sensor .
sosa:madeObservation rdfs:range sosa:Observation .
```

Candidate mapping remaining:

```text
sosa:madeObservation rdfs:subPropertyOf cco:ont00001787
sosa:madeObservation rdfs:subPropertyOf cco:ont00001787 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:madeSampling` — `Common OPs` row 32

Current `OWL Axiom` cell:

```text
sosa:madeSampling rdfs:domain sosa:Sampler .
sosa:madeSampling rdfs:range sosa:Sampling .
sosa:madeSampling owl:inverseOf sosa:madeBySampler .
sosa:madeSampling rdfs:subPropertyOf cco:ont00001787 .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Sampler and range sosa:Sampling. Existing inverse and CCO agent-in mapping notes remain unchanged.
```

Policy A would remove:

```ttl
sosa:madeSampling rdfs:domain sosa:Sampler .
sosa:madeSampling rdfs:range sosa:Sampling .
```

Candidate mapping remaining:

```text
sosa:madeSampling rdfs:subPropertyOf cco:ont00001787
sosa:madeSampling rdfs:subPropertyOf cco:ont00001787 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:observedProperty` — `Common OPs` row 33

Current `OWL Axiom` cell:

```text
sosa:observedProperty rdfs:domain sosa:Observation .
sosa:observedProperty rdfs:range sosa:ObservableProperty .
```

Current `Reasoning` cell:

```text
Prior direct CCO mapping to cco:has_input remains removed. OWL operationalization is source-level domain/range typing: domain sosa:Observation and range sosa:ObservableProperty; no active CCO property mapping is asserted.
```

Policy A would remove:

```ttl
sosa:observedProperty rdfs:domain sosa:Observation .
sosa:observedProperty rdfs:range sosa:ObservableProperty .
```

Candidate mapping remaining:

```text
sosa:observedProperty rdfs:subPropertyOf cco:ont00001921
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `sosa:observes` — `Common OPs` row 34

Current `OWL Axiom` cell:

```text
sosa:observes rdfs:domain sosa:Sensor .
sosa:observes rdfs:range sosa:ObservableProperty .
sosa:observes rdfs:subPropertyOf ssn:forProperty .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Sensor and range sosa:ObservableProperty. The existing ssn:forProperty mapping remains unchanged.
```

Policy A would remove:

```ttl
sosa:observes rdfs:domain sosa:Sensor .
sosa:observes rdfs:range sosa:ObservableProperty .
```

Candidate mapping remaining:

```text
sosa:observes rdfs:subPropertyOf ssn:forProperty
sosa:observes rdfs:subPropertyOf ssn:forProperty 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn-system:hasOperatingProperty` — `System Capability` row 9

Current `OWL Axiom` cell:

```text
ssn-system:hasOperatingProperty rdfs:domain ssn-system:OperatingRange .
ssn-system:hasOperatingProperty rdfs:range ssn-system:OperatingProperty .
```

Current `Reasoning` cell:

```text
BFO dependence subproperty mapping remains deferred. OWL operationalization is provided by source-level domain/range typing: hasOperatingProperty has domain OperatingRange and range OperatingProperty. BFO dependence entailment is not active OWL in this branch; future rule/COMS treatment is paused/not implemented here.
```

Policy A would remove:

```ttl
ssn-system:hasOperatingProperty rdfs:domain ssn-system:OperatingRange .
ssn-system:hasOperatingProperty rdfs:range ssn-system:OperatingProperty .
```

Candidate mapping remaining:

```text
ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn-system:hasOperatingRange` — `System Capability` row 10

Current `OWL Axiom` cell:

```text
ssn-system:hasOperatingRange rdfs:domain ssn:System .
ssn-system:hasOperatingRange rdfs:range ssn-system:OperatingRange .
ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:bearer_of .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain ssn:System and range ssn-system:OperatingRange. The existing BFO bearer relation mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn-system:hasOperatingRange rdfs:domain ssn:System .
ssn-system:hasOperatingRange rdfs:range ssn-system:OperatingRange .
```

Candidate mapping remaining:

```text
ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:BFO_0000196
ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:bearer_of 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn-system:hasSurvivalProperty` — `System Capability` row 11

Current `OWL Axiom` cell:

```text
ssn-system:hasSurvivalProperty rdfs:domain ssn-system:SurvivalRange .
ssn-system:hasSurvivalProperty rdfs:range ssn-system:SurvivalProperty .
```

Current `Reasoning` cell:

```text
BFO dependence subproperty mapping remains deferred. OWL operationalization is provided by source-level domain/range typing: hasSurvivalProperty has domain SurvivalRange and range SurvivalProperty. BFO dependence entailment is not active OWL in this branch; future rule/COMS treatment is paused/not implemented here.
```

Policy A would remove:

```ttl
ssn-system:hasSurvivalProperty rdfs:domain ssn-system:SurvivalRange .
ssn-system:hasSurvivalProperty rdfs:range ssn-system:SurvivalProperty .
```

Candidate mapping remaining:

```text
ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn-system:hasSurvivalRange` — `System Capability` row 12

Current `OWL Axiom` cell:

```text
ssn-system:hasSurvivalRange rdfs:domain ssn:System .
ssn-system:hasSurvivalRange rdfs:range ssn-system:SurvivalRange .
ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:bearer_of .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain ssn:System and range ssn-system:SurvivalRange. The existing BFO bearer relation mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn-system:hasSurvivalRange rdfs:domain ssn:System .
ssn-system:hasSurvivalRange rdfs:range ssn-system:SurvivalRange .
```

Candidate mapping remaining:

```text
ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:BFO_0000196
ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:bearer_of 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn-system:hasSystemCapability` — `System Capability` row 13

Current `OWL Axiom` cell:

```text
ssn-system:hasSystemCapability rdfs:domain ssn:System .
ssn-system:hasSystemCapability rdfs:range ssn-system:SystemCapability .
ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:bearer_of .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain ssn:System and range ssn-system:SystemCapability. The existing BFO bearer relation mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn-system:hasSystemCapability rdfs:domain ssn:System .
ssn-system:hasSystemCapability rdfs:range ssn-system:SystemCapability .
```

Candidate mapping remaining:

```text
ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:BFO_0000196
ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:bearer_of 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn-system:hasSystemProperty` — `System Capability` row 14

Current `OWL Axiom` cell:

```text
ssn-system:hasSystemProperty rdfs:domain ssn-system:SystemCapability .
ssn-system:hasSystemProperty rdfs:range ssn-system:SystemProperty .
```

Current `Reasoning` cell:

```text
BFO dependence subproperty mapping remains deferred. OWL operationalization is provided by source-level domain/range typing: hasSystemProperty has domain SystemCapability and range SystemProperty. BFO dependence entailment is not active OWL in this branch; future rule/COMS treatment is paused/not implemented here.
```

Policy A would remove:

```ttl
ssn-system:hasSystemProperty rdfs:domain ssn-system:SystemCapability .
ssn-system:hasSystemProperty rdfs:range ssn-system:SystemProperty .
```

Candidate mapping remaining:

```text
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:deployedOnPlatform` — `Common OPs` row 3

Current `OWL Axiom` cell:

```text
ssn:deployedOnPlatform rdfs:domain ssn:Deployment .
ssn:deployedOnPlatform rdfs:range sosa:Platform .
ssn:deployedOnPlatform rdfs:subPropertyOf bfo:has_participant .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain ssn:Deployment and range sosa:Platform. The existing BFO participant mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn:deployedOnPlatform rdfs:domain ssn:Deployment .
ssn:deployedOnPlatform rdfs:range sosa:Platform .
```

Candidate mapping remaining:

```text
ssn:deployedOnPlatform rdfs:subPropertyOf bfo:BFO_0000057
ssn:deployedOnPlatform rdfs:subPropertyOf bfo:has_participant 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:deployedSystem` — `Common OPs` row 4

Current `OWL Axiom` cell:

```text
ssn:deployedSystem rdfs:domain ssn:Deployment .
ssn:deployedSystem rdfs:range ssn:System .
ssn:deployedSystem rdfs:subPropertyOf bfo:has_participant .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain ssn:Deployment and range ssn:System. The existing BFO participant mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn:deployedSystem rdfs:domain ssn:Deployment .
ssn:deployedSystem rdfs:range ssn:System .
```

Candidate mapping remaining:

```text
ssn:deployedSystem rdfs:subPropertyOf bfo:BFO_0000057
ssn:deployedSystem rdfs:subPropertyOf bfo:has_participant 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:detects` — `Common OPs` row 5

Current `OWL Axiom` cell:

```text
ssn:detects rdfs:domain sosa:Sensor .
ssn:detects rdfs:range ssn:Stimulus .
ssn:detects rdfs:subPropertyOf cco:is_affected_by .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Sensor and range ssn:Stimulus. The existing CCO affected-by mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn:detects rdfs:domain sosa:Sensor .
ssn:detects rdfs:range ssn:Stimulus .
```

Candidate mapping remaining:

```text
ssn:detects rdfs:subPropertyOf cco:is_affected_by 
ssn:detects rdfs:subPropertyOf cco:ont00001886
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:hasDeployment` — `Common OPs` row 7

Current `OWL Axiom` cell:

```text
ssn:hasDeployment rdfs:domain ssn:System .
ssn:hasDeployment rdfs:range ssn:Deployment .
ssn:hasDeployment owl:inverseOf ssn:deployedSystem .
ssn:hasDeployment rdfs:subPropertyOf bfo:BFO_0000056 .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain ssn:System and range ssn:Deployment. Existing inverse and BFO continuant-part mapping notes remain unchanged.
```

Policy A would remove:

```ttl
ssn:hasDeployment rdfs:domain ssn:System .
ssn:hasDeployment rdfs:range ssn:Deployment .
```

Candidate mapping remaining:

```text
ssn:hasDeployment rdfs:subPropertyOf bfo:BFO_0000056
ssn:hasDeployment rdfs:subPropertyOf bfo:BFO_0000056 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:hasInput` — `Common OPs` row 9

Current `OWL Axiom` cell:

```text
ssn:hasInput rdfs:domain sosa:Procedure .
ssn:hasInput rdfs:range ssn:Input .
```

Current `Reasoning` cell:

```text
Prior direct CCO mapping to cco:has_input remains removed/rejected. OWL operationalization is source-level domain/range typing: domain sosa:Procedure and range ssn:Input; no active CCO property mapping is asserted.
```

Policy A would remove:

```ttl
ssn:hasInput rdfs:domain sosa:Procedure .
ssn:hasInput rdfs:range ssn:Input .
```

Candidate mapping remaining:

```text
ssn:hasInput rdfs:subPropertyOf cco:ont00001921
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:hasOutput` — `Common OPs` row 10

Current `OWL Axiom` cell:

```text
ssn:hasOutput rdfs:domain sosa:Procedure .
ssn:hasOutput rdfs:range ssn:Output .
```

Current `Reasoning` cell:

```text
Prior direct CCO mapping to cco:has_output remains removed/rejected. OWL operationalization is source-level domain/range typing: domain sosa:Procedure and range ssn:Output; no active CCO property mapping is asserted.
```

Policy A would remove:

```ttl
ssn:hasOutput rdfs:domain sosa:Procedure .
ssn:hasOutput rdfs:range ssn:Output .
```

Candidate mapping remaining:

```text
ssn:hasOutput rdfs:subPropertyOf cco:ont00001986
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:hasSubSystem` — `Common OPs` row 14

Current `OWL Axiom` cell:

```text
ssn:hasSubSystem rdfs:domain ssn:System .
ssn:hasSubSystem rdfs:range ssn:System .
ssn:hasSubSystem rdfs:subPropertyOf bfo:has_continuant_part .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain ssn:System and range ssn:System. The existing BFO continuant-part mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn:hasSubSystem rdfs:domain ssn:System .
ssn:hasSubSystem rdfs:range ssn:System .
```

Candidate mapping remaining:

```text
ssn:hasSubSystem rdfs:subPropertyOf bfo:BFO_0000178
ssn:hasSubSystem rdfs:subPropertyOf bfo:has_continuant_part 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:implementedBy` — `Common OPs` row 16

Current `OWL Axiom` cell:

```text
ssn:implementedBy rdfs:domain sosa:Procedure .
ssn:implementedBy rdfs:range ssn:System .
ssn:implementedBy owl:propertyChainAxiom ( cco:ont00001942 cco:ont00001833 ) .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Procedure and range ssn:System. Existing property-chain mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn:implementedBy rdfs:domain sosa:Procedure .
ssn:implementedBy rdfs:range ssn:System .
```

Candidate mapping remaining:

```text
ssn:implementedBy owl:propertyChainAxiom ( cco:ont00001942 cco:ont00001833 ) 
ssn:implementedBy owl:propertyChainAxiom (...)
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:inDeployment` — `Common OPs` row 18

Current `OWL Axiom` cell:

```text
ssn:inDeployment rdfs:domain sosa:Platform .
ssn:inDeployment rdfs:range ssn:Deployment .
ssn:inDeployment owl:inverseOf ssn:deployedOnPlatform .
ssn:inDeployment rdfs:subPropertyOf bfo:BFO_0000056 .
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Platform and range ssn:Deployment. Existing inverse and BFO continuant-part mapping notes remain unchanged.
```

Policy A would remove:

```ttl
ssn:inDeployment rdfs:domain sosa:Platform .
ssn:inDeployment rdfs:range ssn:Deployment .
```

Candidate mapping remaining:

```text
ssn:inDeployment rdfs:subPropertyOf bfo:BFO_0000056
ssn:inDeployment rdfs:subPropertyOf bfo:BFO_0000056 
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

### `ssn:wasOriginatedBy` — `Common OPs` row 37

Current `OWL Axiom` cell:

```text
ssn:wasOriginatedBy rdfs:domain sosa:Observation .
ssn:wasOriginatedBy rdfs:range ssn:Stimulus .
subPropertyOf cco:process_started_by
```

Current `Reasoning` cell:

```text
OWL operationalization includes source-level domain/range typing: domain sosa:Observation and range ssn:Stimulus. The existing CCO process-started-by mapping remains unchanged.
```

Policy A would remove:

```ttl
ssn:wasOriginatedBy rdfs:domain sosa:Observation .
ssn:wasOriginatedBy rdfs:range ssn:Stimulus .
```

Candidate mapping remaining:

```text
ssn:wasOriginatedBy rdfs:subPropertyOf cco:ont00001962
subPropertyOf cco:process_started_by
```

Rationale update: Revise rationale to remove source-level rdfs:domain/range fallback language and explain that fallback typing was removed under the strict candidate rule.

## Interpretation

Strict Policy A identifies 28 properties with both local domain/range and a policy candidate. It would remove 28 local domain triples and 28 local range triples from `SSN2BFO.ttl`.

Of those 28 affected properties, 20 have active candidates and 8 have only deferred or rejected candidates. This means strict Policy A is implementable, but it is intentionally more aggressive than an active-only policy: it removes fallback source typing even from properties whose direct BFO/CCO mapping was rejected or deferred as unsafe.

The strict-policy temporary graph remains HermiT-clean. It also leaves current mapping-audit and ELK expectation counts unchanged because those tools do not count local domain/range source-typing triples as direct/property-chain/restriction mapping expectations.

The main tradeoff is semantic/operational rather than reasoner consistency: Policy A removes local source-level typing from rows where the project deliberately added it to operationalize source domains/ranges while direct mappings were unsafe or rejected.

## Recommendation

Recommended next branch:

```text
fix/apply-object-property-domain-range-fallback-policy
```

This recommendation follows the user-stated strict Policy A because the temporary strict-policy graph is HermiT-clean and audit/ELK counts are unchanged. The implementation branch should be reviewed carefully because it will remove fallback source-level typing from deferred/rejected-candidate cases as well as from active-candidate cases.

Expected implementation scope:

- Remove the 56 exact local domain/range triples listed above from `SSN2BFO.ttl`.
- Update the 28 workbook rows listed in the workbook-implications section, mostly `OWL Axiom` and `Reasoning` cells.
- Regenerate `reports/mapping-consistency-audit.md` and `reports/mapping-consistency-audit.csv`. Counts are expected to remain at `ttl_candidate_mapping_assertions=68` with only the two expected `sosa:Sensor` issues.
- Regenerate `reports/elk-instance-mapping-entailments.md` only if content changes; the temporary ELK run suggests expectation counts should remain `6 / 75 / 5 / 2` with uncovered active mappings `0`.
- Run `tools/test_full_sosa_closure_hermit.py`; the temporary strict-policy run suggests full-closure HermiT should remain clean with unsat count `0`.

## Human Review Summary

- Strict Policy A is technically clean in the tested full local SOSA closure profile.
- The policy would remove 28 domain and 28 range triples, across 28 properties.
- The most sensitive policy choice is whether rejected/deferred direct mappings should still block fallback domain/range. Under strict Policy A they do; under Policies B/C they do not.
- If the project wants to preserve fallback typing for rejected/deferred mappings such as `ssn:hasInput`, `ssn:hasOutput`, `sosa:observedProperty`, and the SSN Systems property relations, use Policy B/C instead of Policy A.
- If the project wants the exact requested candidate rule, proceed with `fix/apply-object-property-domain-range-fallback-policy` and document the intentional loss of fallback source-property typing.

## Validation

Requested validation commands for this report:

```bash
rm -f catalog-v001.xml

python tools/workflow_check.py --mode report-only \
  --expected-file reports/object-property-domain-range-fallback-policy-audit.md

git diff --check
```

Results are recorded in the final assistant summary for this branch.
