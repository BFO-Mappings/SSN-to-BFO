# All Mapping Changes And Rationales Since Cleanup Baseline

## Scope

This report compares the mapping state at baseline commit `8d34254a5a4b323a150c30e91110b18dc5583e3c` with current `HEAD` on the tests branch after the object-property typing-probe validation guardrail was merged.

Baseline:

- SHA: `8d34254a5a4b323a150c30e91110b18dc5583e3c`
- Subject: `Merge pull request #23 from BFO-Mappings/feature/validate-current-examples`

Current:

- SHA: `0080385f5a804f1aae8fc8a1731cdf6decc8402e`
- Subject: `Merge pull request #166 from BFO-Mappings/validation/add-object-property-typing-probe-check`
- Branch for this report: `review/document-all-mapping-changes`

The comparison covers mapping-bearing assertions and workbook mapping representations involving `rdfs:subClassOf`, `owl:equivalentClass`, `rdfs:subPropertyOf`, `owl:equivalentProperty`, `owl:propertyChainAxiom`, OWL class restrictions used as mappings, local object-property domain/range operationalization, and mapping removals, deferrals, restorations, replacements, and simplifications.

It does not count imported source ontology axioms, validation-tooling changes, formatting-only changes, or generated/release artifacts as mapping decisions. Workbook rationale-only changes are listed separately.

## Comparison Summary

Raw diff for the two compared source files:

```text
Current_SOSA-SSN to BFO-CCO.xlsx | Bin 27453 -> 26813 bytes
SSN2BFO.ttl                      | 263 ++++++++++++++++-----------------------
2 files changed, 105 insertions(+), 158 deletions(-)
```

Semantic TTL counts:

| Metric | Baseline | Current | Delta |
|---|---:|---:|---:|
| TTL triples in `SSN2BFO.ttl` | 1172 | 1075 | -97 |
| `rdfs:subClassOf` triples | 32 | 31 | -1 |
| `owl:equivalentClass` triples | 10 | 11 | +1 |
| `rdfs:subPropertyOf` triples | 28 | 21 | -7 |
| `owl:propertyChainAxiom` triples | 3 | 5 | +2 |
| Local object-property `rdfs:domain` triples | 0 | 22 | +22 |
| Local object-property `rdfs:range` triples | 0 | 0 | 0 |

Workbook cell-value comparison:

| Metric | Count |
|---|---:|
| Sheets added | 0 |
| Sheets removed | 0 |
| Cells added | 0 |
| Cells removed | 9 |
| Cells changed | 84 |
| Total changed cells | 93 |

Changed workbook rows by sheet:

| Sheet | Changed rows | Changed cells |
|---|---:|---:|
| `Common Classes` | 3 | 3 |
| `Common OPs` | 30 | 60 |
| `Common DPs` | 2 | 4 |
| `Sample Relationship` | 2 | 2 |
| `System Capability` | 11 | 24 |

Overall change totals in this ledger:

| Category | Source terms / rows |
|---|---:|
| Source terms with substantive mapping changes | 47 |
| Cross-ontology property mappings removed, rejected, or deferred | 13 |
| Cross-ontology property mappings added, restored, replaced, or retained in changed form | 14 |
| Class-expression mappings replaced, simplified, weakened, or deferred | 8 |
| Source-level object-property operationalization rows affected by the 62-to-22 basis | 31 |
| Workbook-only assertion/rationale alignment rows | 6 |
| Intentionally unresolved mapping decisions | 1 |
| Changed mapping assertions without confident rationale | 0 |

## Controlling Evidence

The main evidence sources are:

- `reports/mapping-consistency-target-mismatch-review.md`
- `reports/mapping-consistency-resolution-plan.md`
- `reports/sampler-equivalentclass-decision.md`
- `reports/reasoner-unsafe-system-mapping-deferral.md`
- `reports/ssn-hasproperty-modeling-options.md`
- `reports/hasproperty-observes-mapping-review.md`
- `reports/observes-upper-mapping-decision.md`
- `reports/hosts-implementedby-complex-mapping-review.md`
- `reports/deferred-reactivation-results.md`
- `reports/input-output-cco-mapping-rationale-cleanup.md`
- `reports/ssn-systems-domain-range-operationalization-evaluation.md`
- `reports/all-source-domain-range-operationalization-evaluation.md`
- `reports/hermit-clean-source-domain-range-axioms.md`
- `reports/actuation-range-simplification-implementation.md`
- `reports/system-property-direct-mapping-deferral.md`
- `reports/materialized-sosa-import-hermit-evaluation.md`
- `reports/sosa-actuation-agent-unsat-explanation.md`
- `reports/actuation-agent-property-mapping-deferral.md`
- `reports/madeByActuator-range-after-agent-deferral.md`
- `reports/object-property-domain-range-minimal-basis.md`
- `reports/object-property-domain-range-minimal-basis-implementation.md`
- `reports/object-property-typing-probe-check.md`
- `reports/sosa-sensor-version-alignment-deferral.md`
- `reports/full-sosa-closure-hermit-check.md`
- `reports/mapping-consistency-audit.md`
- `reports/elk-instance-mapping-entailments.md`

Where a detailed decision report exists, this report uses that report over commit messages. First-parent PR subjects were used only for chronology and traceability.

## A. Cross-Ontology Mapping Changes

### Removed, Rejected, Or Deferred Property Mappings

| Source term | Workbook row | Baseline mapping | Current mapping | Change category | Reason | Evidence | Current status |
|---|---|---|---|---|---|---|---|
| `sosa:hasFeatureOfInterest` | `Common OPs` row 8 | `sosa:hasFeatureOfInterest rdfs:subPropertyOf cco:ont00001921 .` | No active direct CCO/BFO mapping asserted. | removed mapping | rejected target-property semantics; spreadsheet/TTL audit cleanup | `remaining-ttl-only-assertions-review.md`; `mapping-consistency-audit.md` | rejected / no active mapping |
| `sosa:isFeatureOfInterestOf` | `Common OPs` row 20 | `sosa:isFeatureOfInterestOf rdfs:subPropertyOf cco:ont00001841 .` | `sosa:isFeatureOfInterestOf rdf:type owl:ObjectProperty .` only | removed mapping | inverse-side feature-of-interest target was not retained as an active mapping | `inverse-side-direct-mapping-policy-review.md`; `mapping-consistency-audit.md` | rejected / source property only |
| `ssn:hasInput` | `Common OPs` row 9 | `ssn:hasInput rdfs:subPropertyOf cco:ont00001921 .` | `ssn:hasInput rdfs:domain sosa:Procedure .` | rejected mapping; active source-level fallback | old direct CCO candidate failed HermiT reactivation and was later treated as removed/rejected, not intended deferred | `input-output-cco-mapping-rationale-cleanup.md`; `deferred-reactivation-results.md`; `object-property-domain-range-minimal-basis-implementation.md` | rejected CCO mapping; active fallback |
| `ssn:hasOutput` | `Common OPs` row 10 | `ssn:hasOutput rdf:type owl:ObjectProperty ; rdfs:subPropertyOf cco:ont00001986 .` | `ssn:hasOutput rdf:type owl:ObjectProperty ; rdfs:domain sosa:Procedure .` | rejected mapping; active source-level fallback | old direct CCO candidate failed HermiT reactivation and was later treated as removed/rejected | `input-output-cco-mapping-rationale-cleanup.md`; `deferred-reactivation-results.md`; `object-property-domain-range-minimal-basis-implementation.md` | rejected CCO mapping; active fallback |
| `sosa:observedProperty` | `Common OPs` row 33 | `sosa:observedProperty rdfs:subPropertyOf cco:ont00001921 .` | `sosa:observedProperty rdfs:domain sosa:Observation .` | deferred/rejected direct CCO mapping; active source-level fallback | direct CCO input mapping was HermiT-unsafe; current mapping keeps source-level typing only | `hermit-observedProperty-reactivation-canary.md`; `deferred-reactivation-results.md`; `object-property-domain-range-minimal-basis-implementation.md` | rejected / active fallback |
| `sosa:madeActuation` | `Common OPs` row 27 | `sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .` | No active direct CCO mapping asserted. | deferred mapping | full local SOSA closure became inconsistent when both actuation-side CCO agent mappings were active; removing both cleared `sosa:Actuator`, `sosa:Actuation`, and `ssn-system:ActuationRange` unsats | `sosa-actuation-agent-unsat-explanation.md`; `actuation-agent-property-mapping-deferral.md` | deferred as HermiT-unsafe together |
| `sosa:madeByActuator` | `Common OPs` row 28 | `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .` | `sosa:madeByActuator rdfs:domain sosa:Actuation .` | deferred CCO mapping; active source-level representative | paired CCO `has_agent` / `agent_in` mappings were unsafe under full SOSA closure; source-level range was later shown clean after deferral, then minimized to the retained domain representative | `sosa-actuation-agent-unsat-explanation.md`; `actuation-agent-property-mapping-deferral.md`; `madeByActuator-range-after-agent-deferral.md`; `object-property-domain-range-minimal-basis-implementation.md` | deferred CCO mapping; active fallback |
| `ssn:hasProperty` | `Common OPs` row 11 | Workbook asserted two intended direct mappings: `ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000196 .` and `ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000117 .` | No active TTL or workbook OWL mapping cell. | deferred mapping | broad `hasProperty` spans continuant and occurrent/property-profile cases; direct OWL subproperty mapping was reasoner-sensitive and over-broad | `ssn-hasproperty-modeling-options.md`; `reasoner-safe-replacement-mapping-review.md`; `ssn-hasproperty-rule-mapping-artifact.md` | deferred; future rule/COMS-style treatment only |
| `ssn-system:hasOperatingProperty` | `System Capability` row 9 | `ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000195 .` | `ssn-system:hasOperatingProperty rdfs:domain ssn-system:OperatingRange .` | deferred BFO dependence mapping; active source-level fallback | direct BFO dependence mapping was directionally problematic and failed HermiT reactivation; source-level typing remains | `ssn-systems-dependence-reactivation-results.md`; `deferred-reactivation-results.md`; `ssn-systems-domain-range-operationalization-evaluation.md`; `object-property-domain-range-minimal-basis-implementation.md` | deferred as HermiT-unsafe |
| `ssn-system:hasSurvivalProperty` | `System Capability` row 11 | `ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000195 .` | `ssn-system:hasSurvivalProperty rdfs:domain ssn-system:SurvivalRange .` | deferred BFO dependence mapping; active source-level fallback | direct BFO dependence mapping failed HermiT reactivation; source-level typing remains | `ssn-systems-dependence-reactivation-results.md`; `deferred-reactivation-results.md`; `object-property-domain-range-minimal-basis-implementation.md` | deferred as HermiT-unsafe |
| `ssn-system:hasSystemProperty` | `System Capability` row 14 | `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000195 .` | `ssn-system:hasSystemProperty rdfs:domain ssn-system:SystemCapability .` | deferred BFO dependence mapping; active source-level fallback | direct BFO dependence mapping failed HermiT reactivation; source-level typing remains | `ssn-systems-dependence-reactivation-results.md`; `deferred-reactivation-results.md`; `object-property-domain-range-minimal-basis-implementation.md` | deferred as HermiT-unsafe |
| `ssn-system:inCondition` | `System Capability` related row | `ssn-system:inCondition owl:propertyChainAxiom ( bfo:BFO_0000196 bfo:BFO_0000054 cco:ont00001819 bfo:BFO_0000055 ) .` | No active local property-chain mapping asserted. | removed property chain | chain was not carried forward in the cleaned active mapping set; it is not part of the current ELK/property-chain expectation set | `mapping-consistency-audit.md`; `elk-instance-mapping-entailments.md` | superseded / not active |
| `sosa:hasSimpleResult`, `sosa:resultTime` | `Common DPs` rows 2-3 | Workbook asserted `rdfs:subPropertyOf owl:topDataProperty` placeholders. | Workbook OWL mapping cells cleared. | removed datatype-property placeholder | top-data-property placeholders were not meaningful mapping commitments and remained outside object-property mapping validation | `remaining-missing-in-ttl-review.md`; `mapping-consistency-audit.md` | rejected placeholder / no active mapping |

### Added, Replaced, Or Retained-In-Changed-Form Property Mappings

| Source term | Workbook row | Baseline mapping | Current mapping | Change category | Reason | Evidence | Current status |
|---|---|---|---|---|---|---|---|
| `sosa:hasResult` | `Common OPs` row 12 | `sosa:hasResult rdfs:subPropertyOf cco:ont00001986 .` | Unchanged: `sosa:hasResult rdfs:subPropertyOf cco:ont00001986 .` | unchanged required area | clean under full closure with inverse `sosa:isResultOf`; no mapping change recommended | `isResultOf-hasResult-full-closure-analysis.md` | active |
| `sosa:isResultOf` | `Common OPs` row 25 | `sosa:isResultOf rdfs:subPropertyOf cco:ont00001816 .` | Unchanged: `sosa:isResultOf rdfs:subPropertyOf cco:ont00001816 .` | unchanged required area | clean under full closure; result/output pair remains active | `isResultOf-hasResult-full-closure-analysis.md` | active |
| `sosa:hasSample` | `Common OPs` row 13 | `sosa:hasSample owl:propertyChainAxiom ( cco:ont00001873 bfo:BFO_0000084 ) .` plus workbook domain/range text | Same property chain retained; local domain/range removed by basis. | property-chain retained; source-level operationalization minimized | sample/property-chain mapping remained useful, but local D/R was redundant in the preferred basis | `sample-representation-property-chains-review.md`; `object-property-domain-range-minimal-basis-implementation.md` | active property chain |
| `sosa:isSampleOf` | `Common OPs` row 26 | `sosa:isSampleOf owl:propertyChainAxiom ( bfo:BFO_0000101 cco:ont00001938 ) .` | `sosa:isSampleOf rdfs:domain sosa:Sample ; owl:propertyChainAxiom ( bfo:BFO_0000101 cco:ont00001938 ) .` | source-level operationalization added/minimized | current basis retains one domain representative for the sample inverse pair | `sample-representation-property-chains-review.md`; `object-property-domain-range-minimal-basis-implementation.md` | active property chain plus fallback |
| `sosa:hosts` | `Common OPs` row 15 | `sosa:hosts rdf:type owl:ObjectProperty .` | `sosa:hosts rdf:type owl:ObjectProperty ; owl:propertyChainAxiom ( bfo:BFO_0000196 bfo:BFO_0000054 bfo:BFO_0000057 ) .` | added property-chain mapping | direct hosting relation needed a HermiT/ELK-safe complex representation through bearer/realization/participant structure | `hosts-implementedby-complex-mapping-review.md`; `elk-instance-mapping-entailments.md` | active property chain |
| `sosa:isHostedBy` | `Common OPs` row 21 | No active local mapping. | `sosa:isHostedBy rdf:type owl:ObjectProperty ; owl:propertyChainAxiom ( bfo:BFO_0000056 bfo:BFO_0000055 bfo:BFO_0000197 ) .` | added property-chain mapping | inverse hosting direction represented with a safe property-chain counterpart | `hosts-implementedby-complex-mapping-review.md`; `isHostedBy-hosts-full-closure-analysis.md` | active property chain |
| `sosa:observes` | `Common OPs` row 34 | Workbook recorded `sosa:observes rdfs:subPropertyOf bfo:BFO_0000057 .`; no baseline TTL triple. | `sosa:observes rdfs:subPropertyOf ssn:forProperty .` | replaced mapping | BFO participant mapping was over-broad; `ssn:forProperty` preserves source-level relation and remains full-closure clean | `hasproperty-observes-mapping-review.md`; `observes-upper-mapping-decision.md`; `isObservedBy-observes-full-closure-analysis.md` | active source-level mapping |
| `sosa:isObservedBy` | `Common OPs` row 22 | Inverse-note only in workbook; no baseline TTL mapping. | `sosa:isObservedBy rdfs:domain sosa:ObservableProperty .` | source-level operationalization added/minimized | inverse-pair basis keeps this domain representative; no direct CCO/BFO inverse mapping is active | `sosa-inverse-property-pairs-full-closure-analysis.md`; `object-property-domain-range-minimal-basis-implementation.md` | active fallback |
| `sosa:actsOnProperty` | `Common OPs` row 2 | Workbook/TLL area mapped to `cco:affects`. | `sosa:actsOnProperty rdfs:subPropertyOf cco:ont00001834 .` | active mapping retained; D/R minimized | pair remains full-closure clean; representative typing moved to inverse-side domain | `isActedOnBy-actsOnProperty-full-closure-analysis.md`; `object-property-domain-range-minimal-basis-implementation.md` | active |
| `sosa:isActedOnBy` | `Common OPs` row 19 | Inverse-note only in workbook. | `sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty ; rdfs:subPropertyOf cco:ont00001886 .` | added active mapping plus fallback | full-closure analysis found pair clean; basis retains inverse-side domain representative | `isActedOnBy-actsOnProperty-full-closure-analysis.md`; `object-property-domain-range-minimal-basis-implementation.md` | active |
| `sosa:madeObservation` | `Common OPs` row 31 | Inverse-note only in workbook. | `sosa:madeObservation rdfs:domain sosa:Sensor ; rdfs:subPropertyOf cco:ont00001787 .` | added active mapping plus fallback | observation/sensor agent pair is structurally analogous to actuation but was tested clean under full closure | `madeObservation-madeBySensor-agent-pair-full-closure-analysis.md`; `object-property-domain-range-minimal-basis-implementation.md` | active |
| `sosa:madeBySensor` | `Common OPs` row 30 | `sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833 .` plus later local D/R text | `sosa:madeBySensor rdfs:subPropertyOf cco:ont00001833 .` | active mapping retained; D/R minimized | full-closure focused analysis found the pair clean; local D/R removed by basis | `madeObservation-madeBySensor-agent-pair-full-closure-analysis.md`; `object-property-domain-range-minimal-basis-implementation.md` | active |
| `sosa:madeSampling` | `Common OPs` row 32 | Inverse-note only in workbook. | `sosa:madeSampling rdfs:domain sosa:Sampler ; rdfs:subPropertyOf cco:ont00001787 .` | added active mapping plus fallback | sampling/sampler pair is medium-risk but full-closure clean | `madeSampling-madeBySampler-full-closure-analysis.md`; `object-property-domain-range-minimal-basis-implementation.md` | active |
| `sosa:madeBySampler` | `Common OPs` row 29 | `sosa:madeBySampler rdfs:subPropertyOf cco:ont00001833 .` plus later local D/R text | `sosa:madeBySampler rdfs:subPropertyOf cco:ont00001833 .` | active mapping retained; D/R minimized | full-closure focused analysis found pair clean; local D/R removed by basis | `madeSampling-madeBySampler-full-closure-analysis.md`; `object-property-domain-range-minimal-basis-implementation.md` | active |
| `ssn:hasDeployment` | `Common OPs` row 7 | Inverse-note only in workbook. | `ssn:hasDeployment rdfs:domain ssn:System ; rdfs:subPropertyOf bfo:BFO_0000056 .` | added mapping plus fallback | straightforward deployment relation made active and kept in the 22-triple representative basis | `object-property-domain-range-minimal-basis-implementation.md`; `elk-instance-mapping-entailments.md` | active |
| `ssn:inDeployment` | `Common OPs` row 18 | Inverse-note only in workbook. | `ssn:inDeployment rdfs:domain sosa:Platform ; rdfs:subPropertyOf bfo:BFO_0000056 .` | added mapping plus fallback | deployment inverse component keeps one representative domain after minimization | `object-property-domain-range-minimal-basis-implementation.md`; `elk-instance-mapping-entailments.md` | active |
| `ssn:hasSubSystem` | `Common OPs` row 14 | Workbook had domain/range plus `subPropertyOf` text; no baseline TTL mapping. | `ssn:hasSubSystem rdfs:domain ssn:System ; rdfs:subPropertyOf bfo:BFO_0000178 .` | active mapping added/minimized | system parthood mapping retained; range removed by 62-to-22 basis | `object-property-domain-range-minimal-basis-implementation.md`; `elk-instance-mapping-entailments.md` | active |
| `ssn:implementedBy` | `Common OPs` row 16 | Workbook used an anonymous/unsupported subproperty-chain expression. | `ssn:implementedBy owl:propertyChainAxiom ( cco:ont00001942 cco:ont00001833 ) .` | replaced with property chain | chain normalized into a machine-checkable property-chain axiom | `hosts-implementedby-complex-mapping-review.md`; `object-property-domain-range-minimal-basis-implementation.md` | active property chain |
| `ssn:implements` | `Common OPs` row 17 | Inverse-note only. | `ssn:implements rdfs:domain ssn:System .` | source-level representative added | representative domain retained for the `implementedBy` / `implements` dependency component | `object-property-domain-range-minimal-basis-implementation.md` | active fallback |
| `ssn:detects` | `Common OPs` row 5 | Workbook had domain/range plus `subPropertyOf cco:ont00001886`. | `ssn:detects rdfs:domain sosa:Sensor ; rdfs:subPropertyOf cco:ont00001886 .` | source-level operationalization minimized | active CCO relation retained; range removed by basis | `object-property-domain-range-minimal-basis-implementation.md`; `elk-instance-mapping-entailments.md` | active |
| `ssn:isProxyFor` | `Common OPs` row 24 | Workbook had object-property plus domain/range. | `ssn:isProxyFor rdfs:domain ssn:Stimulus .` | source-level operationalization minimized | no direct CCO/BFO candidate; domain retained as fallback representative | `object-property-domain-range-minimal-basis-implementation.md` | active fallback |
| `ssn:wasOriginatedBy` | `Common OPs` row 37 | `ssn:wasOriginatedBy rdfs:subPropertyOf cco:ont00001962 .` with workbook range text | `ssn:wasOriginatedBy rdfs:domain sosa:Observation ; rdfs:subPropertyOf cco:ont00001962 .` | source-level operationalization minimized | active CCO relation retained; representative domain kept, range removed | `object-property-domain-range-minimal-basis-implementation.md`; `elk-instance-mapping-entailments.md` | active |
| `ssn-system:hasOperatingRange` | `System Capability` row 10 | `ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:BFO_0000196 .` | `ssn-system:hasOperatingRange rdfs:domain ssn:System ; rdfs:subPropertyOf bfo:BFO_0000196 .` | source-level operationalization minimized | active bearer/dependence-side relation retained with representative domain only | `object-property-domain-range-minimal-basis-implementation.md` | active |
| `ssn-system:hasSurvivalRange` | `System Capability` row 12 | `ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:BFO_0000196 .` | `ssn-system:hasSurvivalRange rdfs:domain ssn:System ; rdfs:subPropertyOf bfo:BFO_0000196 .` | source-level operationalization minimized | active relation retained; representative domain only | `object-property-domain-range-minimal-basis-implementation.md` | active |
| `ssn-system:hasSystemCapability` | `System Capability` row 13 | `ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:BFO_0000196 .` | `ssn-system:hasSystemCapability rdfs:domain ssn:System ; rdfs:subPropertyOf bfo:BFO_0000196 .` | source-level operationalization minimized | active relation retained; representative domain only | `object-property-domain-range-minimal-basis-implementation.md` | active |

## B. Source-Level Operationalization Changes

The cleanup added source-level object-property domain/range operationalization for properties where direct BFO/CCO mappings were absent, unsafe, or not adequate. Later, the 62 local typing assertions were minimized to a preferred cluster-minimal 22-triple basis.

### Preferred 22-Triple Basis Retained At HEAD

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

These are active source-level fallback or representative typing assertions. They preserve all 62 intended object-property typing entailments verified by `reports/object-property-typing-probe-check.md`.

### Local Domain/Range Triples Removed During Basis Minimization

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

The basis report describes this as a preferred cluster-minimal basis, not a globally exhaustive proof of minimum size. The retained representatives are enough to keep the intended typing probes unsatisfiable, while removing 40 redundant local triples from the active mapping file.

## C. Class-Expression Changes

| Source term | Workbook row | Baseline mapping | Current mapping | Change category | Reason | Evidence | Current status |
|---|---|---|---|---|---|---|---|
| `sosa:Sampler` | `Common Classes` row 16 | `rdfs:subClassOf` explicit material entity / bearer / realized-in / Sampling expression | `owl:equivalentClass` to the same intended corrected Sampler expression | replaced class mapping | workbook intended equivalence; TTL was strengthened after ELK/testing showed it was safe | `sampler-equivalentclass-decision.md`; `sampler-sensor-class-mapping-reconciliation-review.md` | active equivalent class |
| `sosa:Sampling` | `Common Classes` related row | `sosa:Sampling` class expression used `ssn:hasOutput some sosa:Sample` | expression uses `cco:ont00001986` / `cco:has_output some sosa:Sample` | replaced restriction target | spreadsheet/TTL target mismatch; `has_output` is the intended CCO relation | `mapping-consistency-target-mismatch-review.md` | active |
| `ssn-system:OperatingRange` | `System Capability` related row | class expression used a previous prescribed-by target | class expression uses corrected `cco:ont00000319` target | replaced class-expression target | spreadsheet/TTL target mismatch correction | `mapping-consistency-target-mismatch-review.md` | active |
| `ssn-system:ActuationRange` | `System Capability` row 3 | Function realized in `sosa:Actuation` with `ssn:hasOutput`/output structure plus a branch equivalent to `cco:affects some bfo:BFO_0000144` and `cco:prescribed_by some cco:ArtifactFunctionSpecification` | Function realized in `sosa:Actuation` with `cco:has_output some bfo:BFO_0000020` and `cco:prescribed_by some cco:ont00000118`; suspicious `affects some ProcessProfile` branch removed | simplified mapping | `affects` branch was overstrong/suspicious; simplification was independently HermiT-clean and did not claim to fix the separate `madeByActuator` range issue | `actuation-range-simplification-evaluation.md`; `actuation-range-simplification-implementation.md` | active but simplified |
| `ssn-system:SystemProperty` | `System Capability` row 32 | `(bfo:specifically dependent continuant or bfo:Process Profile) and cco:prescribed_by some cco:ArtifactFunctionSpecification` | no direct active BFO/CCO class-expression mapping asserted | deferred mapping | broader union target is inherited through `ssn:Property`; `prescribed_by some ArtifactFunctionSpecification` branch was over-specific and unsupported by imported `ssn-systems.ttl` source axioms | `system-property-mapping-simplification-evaluation.md`; `system-property-direct-mapping-deferral.md` | deferred / source class only |
| `ssn-system:BatteryLifetime` | `System Capability` row 4 | active direct class-expression mapping | workbook mapping cell blank; no active TTL mapping | deferred mapping | reasoner-unsafe SSN Systems class mapping; deferral helped preserve clean baseline | `reasoner-unsafe-system-mapping-deferral.md`; `hermit-clean-baseline-after-deferrals.md` | deferred |
| `ssn-system:MeasurementRange` | `System Capability` row 18 | active direct class-expression mapping | workbook mapping cell blank; no active TTL mapping | deferred mapping | reasoner-unsafe SSN Systems class mapping; deferral helped preserve clean baseline | `reasoner-unsafe-system-mapping-deferral.md`; `hermit-clean-baseline-after-deferrals.md` | deferred |
| `ssn-system:SurvivalRange` | `System Capability` row 29 | large survival-oriented function/design class expression | workbook mapping cell blank; no active TTL mapping | deferred mapping | HermiT diagnostics identified `SurvivalRange` as high-impact in the mixed `ssn:hasProperty` / `hasSurvivalProperty` / non-sample SOSA context | `hermit-survival-range-deferral-evaluation.md`; `reasoner-unsafe-system-mapping-deferral.md` | deferred |
| `sampling:RelationshipNature`, `sampling:SampleRelationship` | `Sample Relationship` rows 5-6 | no stable top-level mapping in baseline TTL | active provisional class mappings to CCO information/content-entity structures plus restrictions | added provisional mapping | needed for instance-data/testing coverage and sample relationship representation | `sample-relationship-deferral.md`; `sample-representation-property-chains-review.md`; `remaining-missing-in-ttl-review.md` | active provisional |

The active mappings for `sosa:Actuator`, `sosa:Actuation`, and `sosa:Sensor` remain important validation context, but their TTL class-expression structures are not materially changed between the baseline and current HEAD. `sosa:Sensor` remains an intentionally unresolved workbook/TTL version-alignment issue described below.

## D. Workbook-Only Alignment And Rationale Changes

These rows changed in the workbook without a corresponding substantive current TTL mapping change:

| Source term | Workbook row | Baseline workbook state | Current workbook state | Reason | Evidence | Status |
|---|---|---|---|---|---|---|
| `sosa:Actuator` | `Common Classes` row 4 | used label-like `bfo:realizes` in mapping cell | uses exact `bfo:BFO_0000054` IRI | spreadsheet/TTL assertion alignment | `mapping-consistency-target-mismatch-review.md` | workbook aligned to TTL |
| `sosa:Procedure` | `Common Classes` row 12 | used unresolved `cco:PrescriptiveInformationContentEntity` target | uses `cco:ont00000965` | spreadsheet/TTL assertion alignment to current local CCO IRI | `mapping-consistency-resolution-plan.md` | workbook aligned to TTL |
| `ssn:forProperty` | `Common OPs` row 6 | workbook cell had unsupported/unclear mapping text | mapping cell cleared | unsupported spreadsheet assertion; `sosa:observes -> ssn:forProperty` remains the active source-level upper mapping | `mapping-consistency-resolution-plan.md`; `observes-upper-mapping-decision.md` | no direct mapping |
| `sosa:hasSimpleResult` | `Common DPs` row 2 | `rdfs:subPropertyOf owl:topDataProperty` placeholder | mapping cell cleared | placeholder datatype-property mapping not treated as an active mapping | `remaining-missing-in-ttl-review.md` | no active mapping |
| `sosa:resultTime` | `Common DPs` row 3 | `rdfs:subPropertyOf owl:topDataProperty` placeholder | mapping cell cleared | placeholder datatype-property mapping not treated as an active mapping | `remaining-missing-in-ttl-review.md` | no active mapping |
| `sampling:RelationshipNature`, `sampling:SampleRelationship` | `Sample Relationship` rows 5-6 | earlier rationale | updated provisional-mapping rationale | documentation of current provisional sample relationship handling | `sample-relationship-deferral.md`; `sample-representation-property-chains-review.md` | active provisional / rationale clarified |

## E. Intentionally Unresolved Items

| Source term | Workbook row | Current TTL | Current workbook | Why unresolved | Evidence | Current status |
|---|---|---|---|---|---|---|
| `sosa:Sensor` | `Common Classes` row 18 | explicit local CCO-compatible class expression using material entity, realizable-entity bearer/realized-in Observation structure, and agent-in relation to Observation | forward-looking/latest-CCO-style equivalent mapping to `cco:Sensor` / `cco:ont00000569` | TTL and workbook are aligned to different CCO/version/modeling assumptions. Both tested variants were HermiT-clean, so this is not an immediate consistency problem. Changing either side now would choose the target CCO version prematurely. | `sosa-sensor-version-alignment-resolution.md`; `sosa-sensor-version-alignment-deferral.md`; `mapping-consistency-audit.md` | intentionally unresolved version mismatch |

The two current expected mapping-audit issues are:

- `ISSUE-0001 missing_in_spreadsheet`: current TTL `sosa:Sensor` expression is not represented in the workbook row.
- `ISSUE-0002 missing_in_ttl`: workbook row 18 `sosa:Sensor => bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569` is not asserted in TTL.

Expected-issue handling remains intentional until CCO target-version policy is settled.

## Required Mapping Areas Checklist

| Required area | Accounted for in this report |
|---|---|
| `sosa:madeActuation` | CCO `agent_in` mapping deferred; local D/R minimized away. |
| `sosa:madeByActuator` | CCO `has_agent` mapping deferred; source-level domain retained; explicit range added after deferral then removed by minimal basis while entailment is preserved. |
| `sosa:madeObservation` / `sosa:madeBySensor` | active CCO agent pair tested clean under full closure; local D/R minimized to `madeObservation` domain representative. |
| `sosa:madeSampling` / `sosa:madeBySampler` | active CCO agent pair tested clean under full closure; local D/R minimized to `madeSampling` domain representative. |
| `sosa:observedProperty` | direct CCO input mapping rejected; source-level domain retained. |
| `sosa:actsOnProperty` / `sosa:isActedOnBy` | active affects / affected-by pair; source-level representative retained on inverse side. |
| `sosa:hasResult` / `sosa:isResultOf` | active output / is-output-of pair unchanged and full-closure clean. |
| `sosa:hosts` / `sosa:isHostedBy` | property-chain mappings added and full-closure clean. |
| `sosa:observes` / `sosa:isObservedBy` | `observes -> ssn:forProperty`; representative domain retained on `isObservedBy`. |
| `sosa:hasSample` / `sosa:isSampleOf` | property-chain mappings retained; representative domain retained on `isSampleOf`. |
| `ssn:hasInput` / `ssn:hasOutput` | old CCO candidates rejected; source-level Procedure domains retained. |
| `ssn:hasProperty` | direct BFO dual mapping deferred; no active direct mapping. |
| SSN Systems dependence properties | direct BFO dependence mappings deferred; source-level domains retained. |
| `sosa:Sensor` | intentionally unresolved workbook/TTL version mismatch. |
| `sosa:Sampler` | TTL strengthened from subclass to equivalent class to match workbook intent. |
| `sosa:Actuator`, `sosa:Actuation` | TTL class mappings remain active and full-closure clean; workbook `Actuator` IRI alignment corrected. |
| `ssn-system:ActuationRange` | class expression simplified by removing suspicious `affects some ProcessProfile` branch. |
| `ssn-system:SystemProperty` | direct class-expression mapping deferred; broader typing inherited via `ssn:Property`. |
| `ssn-system:BatteryLifetime`, `ssn-system:MeasurementRange`, `ssn-system:SurvivalRange` | unsafe class mappings deferred. |
| Feature-of-interest mappings | direct CCO feature/input-side mappings removed/rejected. |
| Property-chain decisions | `hasSample/isSampleOf`, `hosts/isHostedBy`, and `implementedBy` chains retained in active mapping set. |
| 62-to-22 domain/range basis | exact retained and removed triples listed above. |

## Validation-State Comparison

| Validation dimension | Baseline commit | Current HEAD |
|---|---|---|
| `ttl_candidate_mapping_assertions` | 73 under current audit tooling against baseline files | 68 |
| Mapping audit issue count | 37 under current audit tooling against baseline files | 2 expected `sosa:Sensor` version-alignment issues |
| Audit issue types | `missing_in_ttl=16`, `missing_in_spreadsheet=15`, `target_mismatch=4`, `needs_human_review=1`, `prefix_or_iri_issue=1` | `missing_in_spreadsheet=1`, `missing_in_ttl=1` |
| ELK direct class expectations | current ELK tooling not present at baseline | 6 |
| ELK direct property expectations | current ELK tooling not present at baseline | 75 |
| Property-chain expectations | current ELK tooling not present at baseline | 5 |
| Restriction expectations | current ELK tooling not present at baseline | 2 |
| Uncovered active direct/property-chain/restriction mappings | current ELK tooling not present at baseline | 0 |
| Full local SOSA closure HermiT | not available; local `imports/sosa.ttl` was not materialized | PASS |
| Full closure triple count | not available | 15729 |
| `owl:Nothing` count | not available | 0 |
| Unsat count/set | not available | 0 / clean |
| Object-property typing probes | not available | PASS: 62/62 expected unsatisfiable probes, 0 unexpected unsats |

## Project-Wide Interpretation

The biggest TTL changes since the baseline are:

- direct BFO/CCO mappings that were directionally problematic or HermiT-unsafe were removed, rejected, or deferred;
- several previously spreadsheet-only or unsupported mappings were either normalized into active TTL assertions or cleared from the workbook;
- source-level object-property domain/range operationalization was added for properties whose direct BFO/CCO mappings were unsafe, absent, or insufficient;
- that source-level typing was later minimized from 62 local domain/range assertions to a preferred 22-triple basis while preserving all 62 intended typing entailments;
- full local SOSA closure was materialized and used to identify the paired actuation-agent CCO mapping conflict;
- `sosa:madeByActuator rdfs:range sosa:Actuator` was made safe only after the paired actuation-side CCO agent mappings were deferred, and was later represented by the minimal basis rather than retained as a local range triple;
- class-expression mappings for the highest-risk SSN Systems area were simplified or deferred to preserve HermiT safety.

The biggest workbook changes are:

- clearing or revising assertion-bearing cells that no longer match safe active TTL mappings;
- marking old `ssn:hasInput`, `ssn:hasOutput`, `sosa:observedProperty`, SSN Systems dependence, and actuation-agent mappings as removed/deferred rather than intended active mappings;
- documenting the preferred cluster-minimal local typing basis;
- preserving `sosa:Sensor` as an intentional version-alignment deferral.

Changes made for source-level fidelity include the retained 22 domain representatives and the source-level handling of `observes`, `madeByActuator`, input/output, observed property, and SSN Systems property relations.

Changes made for HermiT/full-closure safety include deferring the actuation-agent CCO mappings, rejecting the observedProperty/input/output CCO mappings, deferring SSN Systems dependence mappings, deferring reasoner-unsafe class expressions, simplifying `ActuationRange`, and removing `SystemProperty`'s over-specific prescribed-by branch.

Changes made for audit/tooling alignment include workbook target IRI corrections, clearing unsupported spreadsheet placeholders, materializing SOSA closure validation, adding the object-property typing-probe validation check, and reducing audit issues from 37 baseline issues to two expected `sosa:Sensor` issues.

## Release-Readiness Effect

The current state is materially safer and more release-ready than the baseline because:

- all active mappings are covered by the current validation suite;
- full local SOSA closure HermiT passes with no unsatisfiable named classes;
- ELK direct class, direct property, property-chain, and restriction expectations pass with no uncovered active mappings;
- the 62 intended object-property typing entailments are now guarded by a maintained probe check;
- the only remaining mapping-audit issues are documented expected `sosa:Sensor` version-alignment deferrals.

The current state still intentionally leaves some semantics deferred rather than forced into unsafe direct OWL mappings. Deferred or rejected does not mean the intended domain semantics are invalid; it means the old direct OWL representation was not safe or not adequately justified in the current integrated profile.

## Appendix A: Quality Check Coverage

Semantic TTL subject changes accounted for:

```text
sosa:Sampler
sosa:Sampling
sosa:hasFeatureOfInterest
sosa:hosts
sosa:isActedOnBy
sosa:isFeatureOfInterestOf
sosa:isHostedBy
sosa:isObservedBy
sosa:isSampleOf
sosa:madeActuation
sosa:madeByActuator
sosa:madeObservation
sosa:madeSampling
sosa:observedProperty
sosa:observes
sosa:sampling/RelationshipNature
sosa:sampling/SampleRelationship
sosa:usedProcedure
ssn:detects
ssn:hasDeployment
ssn:hasInput
ssn:hasOutput
ssn:hasSubSystem
ssn:implementedBy
ssn:implements
ssn:inDeployment
ssn:isProxyFor
ssn-system:ActuationRange
ssn-system:BatteryLifetime
ssn-system:MeasurementRange
ssn-system:OperatingRange
ssn-system:SurvivalRange
ssn-system:SystemProperty
ssn-system:hasOperatingProperty
ssn-system:hasOperatingRange
ssn-system:hasSurvivalProperty
ssn-system:hasSurvivalRange
ssn-system:hasSystemCapability
ssn-system:hasSystemProperty
ssn-system:inCondition
ssn:wasOriginatedBy
```

Workbook assertion-bearing or rationale rows accounted for:

```text
Common Classes rows 4, 12, 16, 18
Common OPs rows 2-7, 9-19, 21-22, 24-34, 37
Common DPs rows 2-3
Sample Relationship rows 5-6
System Capability rows 3-4, 9-14, 18, 29, 32
```

Changed mapping assertions without confident rationale: none.

No imported-source change is labeled here as a mapping decision. No formatting-only blank-node serialization change is counted as a substantive mapping change.

## Human Review Summary

- Compared `SSN2BFO.ttl` and `Current_SOSA-SSN to BFO-CCO.xlsx` from baseline `8d34254a5a4b323a150c30e91110b18dc5583e3c` to current HEAD `0080385f5a804f1aae8fc8a1731cdf6decc8402e`.
- Accounted for 47 source terms with substantive mapping changes.
- Accounted for 13 removed/deferred/rejected cross-ontology property mapping decisions, 14 added/replaced/retained-in-changed-form property mapping decisions, 8 class-expression mapping decisions, 31 source-level domain/range basis rows, 6 workbook-only alignment rows, and 1 intentionally unresolved version mismatch.
- The most important safety changes were the input/output, observedProperty, SSN Systems dependence, and actuation-agent deferrals; the `ActuationRange` simplification; the `SystemProperty` direct mapping deferral; and the full SOSA closure correction.
- The most important semantic-preservation change was the 62-to-22 object-property typing basis, now guarded by the object-property typing-probe validation check.
- The only intentionally unresolved mapping decision is `sosa:Sensor` TTL/workbook CCO-version alignment.
- All substantive TTL and workbook mapping changes found in the baseline-to-HEAD comparison are assigned a rationale in this ledger.
