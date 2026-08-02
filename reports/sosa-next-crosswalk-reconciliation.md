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
| `sosa:wasOriginatedBy` | `already_represented` | The current process_started_by mapping matches the external corrected row. Its coherence with the separately proposed redesign of sosa:originated must still be reviewed in the semantic-redesign set. |

### Disposition totals

- Already represented: **21**
- Adapt: **1**

The `already_represented` disposition means that the external workbook introduces no change to that row's cross-ontology axiom. It does not duplicate source-native domain, range, inverse, declaration, restriction, label, or comment axioms in COMS.

`sosa:System` and `sosa:wasOriginatedBy` remain subject to dependency review when the related `sosa:implements` and `sosa:originated` rows are reconciled.

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
