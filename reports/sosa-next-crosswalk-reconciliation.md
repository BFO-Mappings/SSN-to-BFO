# SOSA-next Crosswalk Reconciliation Audit

**Status:** Preliminary, report-only comparison. No COMS mappings are changed by this audit.

## Evidence

- External workbook: `SOSA-SSN to BFO-CCO-RO.xlsx`
- External workbook SHA-256: `26458f43ceab78ce11fa99e86f34494bfd53f9bcafd96f3bb1ff7e7103900d61`
- Governed workbook: `mappings/SOSA-next-to-BFO-COMS.xlsx`
- Governed workbook SHA-256: `a753664eca2ce2bd4249fc2521f6043751b01a2d3e970e9b351a0dbfbb66c435`
- The external workbook remains outside the repository; the reports record its identity and provenance.

## External source basis

- **SOSA/SSN 2023:** w3c/sdw-sosa-ssn @ 929f9a8 (2026-07-16); core + system + sample-relations extensions.
- **BFO 2020:** BFO-ontology/BFO-2020, tag release-2024-01-29 (044490f), src/owl/bfo-core.owl.
- **CCO:** CommonCoreOntologies release/2.2 (010c998). Your release pins CCO 2024-11-06; the Tab 5 fix and the Tab 3 current-SOSA mapping were validated against your pins, not 2.2.
- **RO:** oborel/obo-relations, tag v2025-12-17 (13620e1).

- **Version-control implication:** The external BFO/CCO crosswalk was evaluated against the versions listed above. Any proposed mapping must be rechecked against the exact target versions pinned by this repository before adoption.

- **Held open in source workbook:** Two modeling points are deliberately left as your questions, not decided here: whether sosa:Sensor is equivalent to cco:Sensor, and whether every sosa:Observation must contain an act of observation. Both are flagged where they occur.

## Scope

- In scope: Tab 1, SOSA/SSN 2023 to BFO/CCO.
- Out of scope for this branch phase: the RO mappings and BFO/CCO-to-RO bridge.
- This audit compares evidence and records candidate dispositions; it does not automatically adopt axioms.

## Inventory summary

- External BFO/CCO rows: **115**
- Governed COMS rows: **119**
- Exact term matches: **110**
- Namespace-alias matches: **5**
- External rows unmatched to COMS: **0**
- COMS terms absent from the external crosswalk: **4**

### External verdicts

| Verdict | Count |
|---|---:|
| Decision needed (default in place) | 9 |
| Not DL-expressible | 8 |
| OK as-is | 62 |
| Semantic redesign | 26 |
| Syntactic repair | 10 |

### Governed COMS status

| Status | Count |
|---|---:|
| active | 61 |
| deferred | 9 |
| explicitly_unmapped | 49 |

### Crosswalk coverage of governed COMS

- The external crosswalk covers all **61 active mappings**.
- It covers **5 of the 9 reasoned deferrals**.
- It covers all **49 explicitly unmapped rows**.
- The four governed terms absent from the external crosswalk are themselves reasoned deferrals: `sosa:ActuatableProperty`, `sosa:Asset`, `sosa:ObservableProperty`, and `sosa:Result`.
- Accordingly, the external-row status inventory is **61 active / 5 deferred / 49 explicitly unmapped**, while the complete governed-workbook inventory remains **61 active / 9 deferred / 49 explicitly unmapped**.

## Priority review queue

| Term | External verdict | Current COMS status | Preliminary disposition |
|---|---|---|---|
| `sosa:Observation` | Decision needed (default in place) | active | human decision — determine required process-part commitment |
| `sosa:Sampler` | Syntactic repair | active | substantive review — proposed equivalence conflicts with prior project decision |
| `sosa:Sensor` | Syntactic repair | deferred | defer — resolve equivalence against the exact target CCO version |
| `sosa:endTime` | OK as-is | deferred | preserve datatype-property deferral pending repository-wide support |
| `sosa:hasProperty` | Not DL-expressible | explicitly_unmapped | preserve outside active OWL mapping pending rule/SHACL design |
| `sosa:hasSample` | OK as-is | explicitly_unmapped | review as SOSA-next relation; do not transfer the current-SOSA simplicity rationale |
| `sosa:hasSimpleResult` | OK as-is | deferred | preserve datatype-property deferral pending repository-wide support |
| `sosa:isSampleOf` | OK as-is | explicitly_unmapped | review as SOSA-next relation; do not transfer the current-SOSA simplicity rationale |
| `sosa:resultTime` | OK as-is | deferred | preserve datatype-property deferral pending repository-wide support |
| `sosa:startTime` | OK as-is | deferred | preserve datatype-property deferral pending repository-wide support |

## Reconciliation rules

1. Treat the external workbook as expert evidence, not as an executable mapping authority.
2. Verify every target term against the repository's exact pinned BFO and CCO versions.
3. Preserve the datatype-property deferrals until repository-wide datatype-property support exists.
4. Keep `sosa:Sensor` version-sensitive and deferred until the target CCO definition is pinned and reviewed.
5. Treat `sosa:Observation` and `sosa:Sampler` as substantive modeling decisions, not syntax repairs.
6. Do not transfer the current-SOSA sample-property simplicity rationale to SOSA-next.
7. Route non-DL representation intent to a separately governed rule, SHACL, or annotation layer.

## Evidence-based dispositions for the first active set

This phase reviews the eleven active COMS mappings whose external corrected axioms contain no retained BFO/CCO mapping.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa:actsOn` | `deactivate` | The source relation has an Actuator subject, whereas bfo:has_participant has a process domain. The current subproperty axiom can therefore classify an actuator as a process. |
| `sosa:actsOnProperty` | `deactivate` | cco:affects has a continuant range, whereas sosa:Property includes the ProcessProfile branch. The current mapping can therefore impose continuant typing on an occurrent property. |
| `sosa:forProperty` | `deactivate` | The chain cco:described_by o cco:is_about captures an entity being described by information that is about a property. It does not establish that the entity acts on or observes that property, which is the intended meaning of sosa:forProperty. This semantic mismatch applies regardless of the CCO version. |
| `sosa:hasOperatingConditions` | `deactivate` | The chain bfo:bearer_of o cco:is_subject_of concludes in an Information Content Entity, whereas the SOSA-next relation ranges over OperatingConditions, Observation, or ObservationCollection. The chain does not express the source relation. |
| `sosa:hasSystemCapability` | `deactivate` | The chain bfo:bearer_of o cco:is_subject_of concludes in an Information Content Entity, whereas the SOSA-next relation ranges over Observation or ObservationCollection. The chain does not express the source relation. |
| `sosa:hosts` | `defer_decision` | The chain is valid OWL and compositionally well typed, but it infers that a platform hosts every participant in a realization of something the platform bears. Whether that breadth is acceptable requires a modeling decision. |
| `sosa:implementedBy` | `adapt` | Replace the misdirected chain with cco:prescribes o cco:has_agent. The pinned CCO confirms that prescribes is inverse to prescribed_by and has_agent is inverse to agent_in. |
| `sosa:implements` | `adapt` | Replace the category-incompatible chain with cco:agent_in o cco:prescribed_by. This follows the path from a system through an execution in which it is an agent to the procedure prescribing that execution. |
| `sosa:madeByActuator` | `retain` | The SOSA domain and range agree with cco:has_agent: an Actuation or ActuationCollection process has an Actuator as its agent. |
| `sosa:observedProperty` | `deactivate` | cco:has_input has a continuant range, whereas sosa:Property includes the ProcessProfile branch. The current mapping can impose continuant typing on an occurrent property. |
| `sosa:observes` | `deactivate` | The source relation has a Sensor subject, whereas bfo:has_participant has a process domain. The current subproperty axiom can therefore classify a sensor as a process. |

### Disposition totals

- Retain: **1**
- Adapt: **2**
- Deactivate: **7**
- Defer for a modeling decision: **1**

These are audit dispositions only. No COMS row or ontology product is changed in this phase.

### `sosa:forProperty` correction

The current `cco:described_by o cco:is_about` chain is deactivated on semantic grounds, not because of a version-specific inconsistency. Description/aboutness does not entail that the described entity acts on or observes the property.

## Evidence-based dispositions for the BFO/CCO-bearing OK-as-is set

This phase reviews the 22 external rows marked `OK as-is` whose corrected axioms contain a BFO or CCO commitment.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa-rel:RelationshipNature` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa-rel:SampleRelationship` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:Actuation` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:ActuationCollection` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:Execution` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:ExecutionCollection` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:MaterialSample` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:ObservationCollection` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:Sample` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:Sampling` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:SamplingCollection` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:StatisticalSample` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:System` | `already_represented` | The System class axiom itself already matches the external cross-ontology commitment. Its use of sosa:implements remains dependency-sensitive to the separately validated adaptation of that relation's property chain. |
| `sosa:deployedAsset` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:deployedOnPlatform` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:deployedSystem` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:detects` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:hasDeployment` | `adapt` | Replace the current cco:is_output_of superproperty with bfo:participates_in. The source relation is inverse to sosa:deployedAsset, whose governed mapping is under bfo:has_participant; participates_in is the corresponding inverse direction. |
| `sosa:hasSubSystem` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:madeActuation` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:qualityOf` | `already_represented` | The governed COMS axiom has the same BFO/CCO direction and logical strength as the external corrected axiom. Source-native declarations, domains, ranges, inverses, restrictions, labels, and comments do not require an additional COMS axiom. |
| `sosa:wasOriginatedBy` | `adapt` | Replace cco:process_started_by with cco:caused_by. This is the inverse-side counterpart of adapting sosa:originated to cco:is_cause_of. The source supports Observation-to-Stimulus causal direction but does not entail the stronger temporal-start conditions of cco:process_started_by. |

### Disposition totals

- Already represented: **20**
- Adapt: **2**

The `already_represented` disposition means that the external workbook introduces no change to that row's cross-ontology axiom. It does not duplicate source-native domain, range, inverse, declaration, restriction, label, or comment axioms in COMS.

`sosa:System` remains dependency-sensitive to the adaptation of `sosa:implements`. The prior `sosa:wasOriginatedBy` disposition has now been revised to `adapt`, using `cco:caused_by` as the inverse-side counterpart of `sosa:originated` under `cco:is_cause_of`.

These remain report-only dispositions. No COMS row or ontology product is changed in this phase.

## Evidence-based dispositions for the BFO/CCO-bearing syntactic-repair set

The external `Syntactic repair` label does not by itself establish that the corrected axiom has appropriate semantic strength. These dispositions use the exact pinned SOSA-next and CCO definitions together with the project's modeling decisions.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa:Actuator` | `adapt` | Replace the current composite subclass mapping with sosa:Actuator rdfs:subClassOf bfo:MaterialEntity. Remove the bearer_of, has_realization, and agent_in existential restrictions. This preserves the project's deliberate materiality commitment without requiring an actual Actuation. |
| `sosa:Battery` | `already_represented` | The pinned SOSA-next source already asserts Battery subClassOf System. The governed COMS row supplies the same additional BFO commitment as the external corrected axiom: bearer_of some Function. |
| `sosa:Sampler` | `adapt` | Replace the current equivalent-class mapping with sosa:Sampler rdfs:subClassOf bfo:MaterialEntity. Remove the reverse implication and the bearer_of, has_realization, and agent_in existential restrictions. This preserves the project's deliberate materiality commitment without requiring an actual Sampling. |
| `sosa:Stimulus` | `adapt` | Replace the equivalent-class axiom with a one-way subclass axiom. Every SOSA Stimulus may be modeled as a CCO Cause that is cause of some Observation, but not every cause of an Observation is thereby a SOSA Stimulus. |
| `sosa:Sensor` | `preserve_deferral` | Do not adopt the proposed equivalence against the current pinned CCO. Its Sensor class is a Transducer designed to convert incoming energy into a corresponding output signal, whereas SOSA-next Sensor also includes humans, software-based systems, and simulation systems. Reconsider only after an explicit target-version decision. |

### Disposition totals

- Already represented: **1**
- Adapt: **3**
- Preserve existing deferral: **1**

`sosa:Actuator` and `sosa:Sampler` are retained as explicit subclasses of `bfo:MaterialEntity`, but the stronger realization, actual-agent, and equivalence commitments are removed.

These remain report-only dispositions. No COMS row or ontology product is changed in this phase.

## Evidence-based dispositions for the semantic-redesign class set

These three rows were assessed against the exact pinned SOSA-next hierarchy, property signatures, definitions, and BFO/CCO targets.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa:FeatureOfInterest` | `adapt` | Widen the current equivalent-class filler from Observation-or-Sampling-or-Actuation to Execution-or-ExecutionCollection-or-Deployment. This matches the exact pinned isFeatureOfInterestOf signature: the narrower execution classes are already subclasses of Execution, and their collection classes are subclasses of ExecutionCollection. |
| `sosa:Platform` | `adapt` | Replace the current equivalence with sosa:Platform owl:equivalentClass sosa:Asset and bfo:MaterialEntity and (sosa:hosts some sosa:Asset). The pinned definition characterizes a Platform as an Asset that hosts other Assets, particularly Systems and Platforms; the external System-or-Platform filler is therefore still too narrow. The MaterialEntity conjunct preserves the project's existing materiality commitment. |
| `sosa:SpatialSample` | `deactivate` | Remove the active cross-ontology restriction and retain the native SpatialSample subClassOf Sample axiom. The source defines spatiality through the sample's own location and shape. Neither requiring the represented FeatureOfInterest to occupy a spatial region nor requiring production by a Sampling whose FeatureOfInterest occupies a spatial region captures that defining condition. |

### Disposition totals

- Adapt: **2**
- Deactivate: **1**

`sosa:FeatureOfInterest` accepts the external widening. `sosa:Platform` retains the material-entity equivalence but uses the exact native genus and filler, `sosa:Asset`. `sosa:SpatialSample` receives no replacement BFO/CCO axiom because neither proposed restriction captures the source's location-and-shape criterion.

These remain report-only dispositions. No COMS row or ontology product is changed in this phase.

## Evidence-based dispositions for the semantic-redesign input/output set

These rows distinguish Procedure-level input and output specifications from concrete inputs and outputs of an Execution. The exact CCO relations require Process subjects and Continuant inputs or outputs.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa:hasInput` | `deactivate` | Remove the cco:has_input superproperty. The source relation runs from a Procedure, which is mapped as a prescriptive information content entity, whereas CCO has_input has a Process domain. No direct CCO superproperty expresses a Procedure-to-required-input-specification relation. |
| `sosa:hasInputValue` | `deactivate` | Remove the cco:has_input superproperty. Although the source subject is an Execution or ExecutionCollection, SOSA only states that the object assigns a value to an input used in the execution. It does not entail the stronger CCO condition that the object is a Continuant whose presence at the beginning is necessary for the Process to start. |
| `sosa:hasOutput` | `deactivate` | Remove the cco:is_output_of superproperty. The source relation runs from a Procedure to an output specification, while is_output_of runs from a Continuant output to the Process that produced it. A Procedure is not that process, and the current mapping also reverses the relation. |
| `sosa:hasResult` | `adapt` | Replace cco:is_output_of with cco:has_output. The SOSA relation runs from an Execution or ExecutionCollection to its result, matching the CCO Process-to-Continuant output direction. The current mapping uses the inverse direction. |

### Disposition totals

- Adapt: **1**
- Deactivate: **3**

The exact pinned SOSA-next closure contained no relevant cardinality restrictions or property-chain axioms for these property families. The external workbook's simplicity rationale was therefore not independently reproduced, but no replacement property chain is adopted.

`sosa:hasResult` is the only direct CCO mapping retained: its superproperty changes from `cco:is_output_of` to the correct process-to-output relation `cco:has_output`.

These remain report-only dispositions. No COMS row or ontology product is changed in this phase.

## Evidence-based dispositions for the remaining semantic-redesign relations

These rows were assessed with their exact source directions, the current process mappings for Execution and ExecutionCollection, and the pinned CCO inverse pairs.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa:madeBySampler` | `already_represented` | The current cco:has_agent superproperty preserves the Sampling-to-Sampler direction. A Sampler that made a Sampling is causally active as its agent. The external domain widening to SamplingCollection is source-native and does not require a different COMS axiom. |
| `sosa:madeBySensor` | `already_represented` | The current cco:has_agent superproperty preserves the Observation-to-Sensor direction. A Sensor involved in making an Observation is causally active as its agent. The external domain widening to ObservationCollection is source-native and does not require a different COMS axiom. |
| `sosa:madeBySystem` | `already_represented` | The current cco:has_agent superproperty preserves the Execution-to-System direction. The source relation states that the System made the Execution, which supports its being causally active as agent in that process. The expanded source domain list does not alter the cross-ontology axiom. |
| `sosa:originated` | `adapt` | Replace cco:process_starts with cco:is_cause_of. The source states that a Stimulus originated an Observation and thus supports causal direction from Stimulus to Observation, but does not establish the stronger temporal-start conditions required by cco:process_starts. |
| `sosa:resultQuality` | `adapt` | Replace cco:is_about with cco:is_subject_of. The source relation runs from an Observation or ObservationCollection to quality information pertaining to it. The Observation is therefore the subject of the InformationContentEntity; the inverse source relation qualityOf correctly maps to cco:is_about. |
| `sosa:usedProcedure` | `already_represented` | The current cco:prescribed_by superproperty preserves the Execution-to-Procedure direction. The governed Procedure mapping places Procedure under PrescriptiveInformationContentEntity, and a Procedure used in an Execution serves as its rule or guide. The widened source domain list does not alter the cross-ontology axiom. |

### Dependency revision

The previously reviewed `sosa:wasOriginatedBy` row is revised from `already_represented` to `adapt`. Its superproperty changes from `cco:process_started_by` to `cco:caused_by`, preserving inverse coherence with `sosa:originated` under `cco:is_cause_of` without adding the unsupported temporal-start condition.

The inverse quality relation `sosa:qualityOf` remains `already_represented` under `cco:is_about`.

### Disposition totals for this phase

- Newly already represented: **4**
- Newly adapted: **2**
- Prior disposition revised to adapt: **1**

These remain report-only dispositions. No COMS row or ontology product is changed in this phase.

## Evidence-based dispositions for the phenomenon-time semantic-redesign pair

The pinned source establishes that both properties are object properties and inverses. They relate an Execution to the temporal entity to which its result applies, rather than to the temporal region occupied by the Execution itself.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa:phenomenonOccurred` | `adapt` | Replace the current rdfs:range bfo:TemporalRegion axiom with rdfs:domain bfo:TemporalRegion. The native inverse orientation runs from a temporal entity to an Execution or ExecutionCollection. No BFO or CCO temporal relation is adopted as a superproperty because the temporal entity is the time to which the result pertains, not necessarily the temporal region occupied by the Execution. |
| `sosa:phenomenonTime` | `adapt` | Replace the explicitly unmapped disposition with rdfs:range bfo:TemporalRegion. The pinned source declares phenomenonTime as an owl:ObjectProperty from an Execution or ExecutionCollection to the time at which its result applies. Retain no BFO or CCO temporal superproperty, because this time may differ from the Execution's own occupied temporal region. |

### Disposition totals

- Adapt: **2**

The resulting cross-ontology commitments are limited to `sosa:phenomenonTime rdfs:range bfo:TemporalRegion` and `sosa:phenomenonOccurred rdfs:domain bfo:TemporalRegion`. No BFO or CCO temporal object property is asserted as a superproperty.

The external note characterizing `sosa:phenomenonTime` as a datatype property is rejected as inconsistent with the pinned source, which declares it an `owl:ObjectProperty` and gives it an object-property inverse.

These remain report-only dispositions. No COMS row or ontology product is changed in this phase.

## Evidence-based dispositions for the not-DL-expressible cross-ontology set

These rows cannot be repaired by retaining their current direct BFO/CCO superproperties. Two incorrectly treat Samples as production processes; the third requires a conditional choice between distinct BFO relations.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa:featureHasUltimateSample` | `deactivate` | Remove the cco:is_output_of superproperty. The source relation runs from a FeatureOfInterest to an ultimate Sample or SampleCollection. It does not relate a Continuant output to the Sampling process that produced it. The current mapping would instead place the source and target into the CCO output-to-process signature. |
| `sosa:hasOriginalSample` | `deactivate` | Remove the cco:is_output_of superproperty. The source relation runs from one Sample to another Sample identified as its original. It does not relate an output to the Sampling process that produced it, and the CCO mapping would incorrectly type the target Sample as a Process. |
| `sosa:hasProperty` | `retain_unmapped` | Retain the explicitly unmapped status. sosa:Property may be either a bfo:SpecificallyDependentContinuant or a bfo:ProcessProfile. The corresponding relations would be bfo:bearer_of for the continuant branch and an occurrent-parthood relation for the process-profile branch. OWL cannot select the appropriate superproperty according to the filler type, so no single sound BFO superproperty is asserted. |

### Disposition totals

- Deactivate: **2**
- Retain explicitly unmapped: **1**

The output-of-a-Sampling semantics remain represented on the appropriate Sampling and Sample mappings rather than being asserted directly between a FeatureOfInterest or Sample and another Sample.

`sosa:hasProperty` remains available for a later rule, SHACL, or other conditional representation layer that can distinguish the continuant and process-profile branches.

These remain report-only dispositions. No COMS row or ontology product is changed in this phase.

## Evidence-based dispositions for the Procedure-family decision set

The exact pinned CCO contains `cco:ont00000965`, labelled `Directive Information Content Entity`. It does not contain a class labelled `Prescriptive Information Content Entity`. The target class is itself defined using a `prescribes some Entity` restriction.

| Term | Validated disposition | Evidence basis |
|---|---|---|
| `sosa:Procedure` | `adapt` | Replace the current composite mapping with the single axiom sosa:Procedure rdfs:subClassOf cco:DirectiveInformationContentEntity. The exact pinned target is cco:ont00000965, labelled Directive Information Content Entity, not Prescriptive Information Content Entity. Remove the additional cco:prescribes some bfo:Process restriction because the source definition does not require every reusable Procedure to prescribe an actual Process. The weaker existential inherited from the CCO target's own definition remains. |
| `sosa:ActuatingProcedure` | `deactivate` | Remove the cco:prescribes restriction and rely on the native ActuatingProcedure subClassOf Procedure hierarchy. The source definition supports the specialization: an ActuatingProcedure specifies how to make an Actuation. The current existential nevertheless entails an actual Actuation, while the external universal over the broad CCO prescribes relation would require every entity for which the directive serves as a rule, guide, or model to be an Actuation. Neither CCO restriction safely expresses the source specialization. |
| `sosa:ObservingProcedure` | `deactivate` | Remove the cco:prescribes restriction and rely on the native ObservingProcedure subClassOf Procedure hierarchy. The source definition supports the specialization: an ObservingProcedure specifies how to make an Observation. The current existential nevertheless entails an actual Observation, while the external universal over the broad CCO prescribes relation would require every entity for which the directive serves as a rule, guide, or model to be an Observation. Neither CCO restriction safely expresses the source specialization. |
| `sosa:SamplingProcedure` | `deactivate` | Remove the cco:prescribes restriction and rely on the native SamplingProcedure subClassOf Procedure hierarchy. The source definition supports the specialization: a SamplingProcedure specifies how to make a Sampling. The current existential nevertheless entails an actual Sampling, while the external universal over the broad CCO prescribes relation would require every entity for which the directive serves as a rule, guide, or model to be a Sampling. Neither CCO restriction safely expresses the source specialization. |

### Disposition totals

- Adapt: **1**
- Deactivate: **3**

The general Procedure mapping retains only the direct subclass relation to CCO's Directive Information Content Entity and removes the additional Process-specific existential.

The three specialized procedure rows receive no additional cross-ontology restriction. Their native SOSA subclass relations and definitions preserve the distinction between actuating, observing, and sampling procedures. The current existentials entail actual executions, while the proposed universals use the broader semantics of `cco:prescribes`; neither safely formalizes that source specialization.

These remain report-only dispositions. No COMS row or ontology product is changed in this phase.

## Unmatched inventory

- Every external BFO/CCO term matched a governed COMS term, directly or through an approved namespace alias.

### Governed COMS terms absent from external crosswalk

- `sosa:ActuatableProperty`
- `sosa:Asset`
- `sosa:ObservableProperty`
- `sosa:Result`

## Detailed matrix

The complete row-level comparison is recorded in `reports/sosa-next-crosswalk-reconciliation.csv`.

Rows with a non-empty `validated_disposition` field have completed this audit phase. Those dispositions remain report-only evidence until implemented and revalidated in COMS; all other rows remain preliminary.
