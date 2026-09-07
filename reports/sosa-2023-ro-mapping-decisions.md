# SOSA-2023 to RO Mapping Decisions

## Final governance

- Governed SOSA-2023 properties: **82**
- Active logical mappings: **16**
- `no_direct_mapping`: **66**
- Deferred: **0**
- Unreviewed: **0**
- SKOS mappings: **0**

Only governed OWL `rdfs:subPropertyOf` mapping assertions are admitted in this RO mapping track.

## Authorities

- Approved SOSA source identity: `sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`
- External reviewed crosswalk SHA-256: `26458f43ceab78ce11fa99e86f34494bfd53f9bcafd96f3bb1ff7e7103900d61`
- Relations Ontology release: `v2025-12-17`
- Relations Ontology commit: `13620e1d75465c6504c755d2fdfa706922e9b7e7`
- Reviewed `ro-full.owl` SHA-256: `debfb46f91fa1ed8e1af02cf087ece8d02983c37789bfd027b47c2e8c8a5f179`
- Governed RO COMS workbook SHA-256: `87855d69542209411c5cde638bca83c225df245c4d4bf4a66fa0716f33911355`

The pinned RO distribution supplies generic `BFO:0000050` (`part of`) and `BFO:0000051` (`has part`) but not the continuant-specific `BFO:0000176` / `BFO:0000178` pair. The generic BFO relations are therefore legitimate RO-profile targets.

## Active logical mappings

| Source property | RO-profile target |
| --- | --- |
| `sosa:deployedAsset` | `RO:0000057` |
| `sosa:deployedOnPlatform` | `RO:0000057` |
| `sosa:deployedSystem` | `RO:0000057` |
| `sosa:hasDeployment` | `RO:0000056` |
| `sosa:hasSubSystem` | `BFO:0000051` |
| `sosa:inDeployment` | `RO:0000056` |
| `sosa:isSubSystemOf` | `BFO:0000050` |
| `sosa:madeActuation` | `RO:0002500` |
| `sosa:madeByActuator` | `RO:0002608` |
| `sosa:madeBySampler` | `RO:0002608` |
| `sosa:madeBySensor` | `RO:0002608` |
| `sosa:madeBySystem` | `RO:0002608` |
| `sosa:madeExecution` | `RO:0002500` |
| `sosa:madeObservation` | `RO:0002500` |
| `sosa:madeSampling` | `RO:0002500` |
| `sosa:systemDeployment` | `RO:0000056` |

## No-direct decisions

| Source property | Decision rationale |
| --- | --- |
| `sampling:hasSampleRelationship` | No direct RO mapping is adopted. Sample->SampleRelationship (an ICE); no RO counterpart (reification of a relationship as an information entity). |
| `sampling:natureOfRelationship` | No direct RO mapping is adopted. SampleRelationship->RelationshipNature (ICE->category); no RO counterpart. |
| `sampling:relatedSample` | No direct RO mapping is adopted. SampleRelationship->Sample; no RO counterpart. |
| `sosa:actsOn` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Capability-level (Actuator capable of acting on a Property). Same range mismatch as observes (RO capable_of targets processes). Related. |
| `sosa:actsOnProperty` | No direct RO mapping is adopted. Actuation->targeted Property (corrected super cco:affects); RO causally_influences has a continuant subject, not a process. No clean RO counterpart. See-also RO causally_influences. |
| `sosa:detects` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Corrected super cco:is_affected_by (a stimulus makes a causal difference to the sensor); RO causally_influenced_by is the nearest causal relation, but domains differ (RO continuant->continuant). Related. |
| `sosa:endTime` | No direct RO mapping is adopted. Data property (temporal literal); RO is a relations ontology with no datatype counterpart. No counterpart. |
| `sosa:featureHasUltimateSample` | No direct RO mapping is adopted. FeatureOfInterest->terminal Sample across a chain; no RO relation captures this representative-terminus. No counterpart. |
| `sosa:forProperty` | No direct RO mapping is adopted. Procedure/System->Property specification; no RO counterpart (property-specification is not an RO relation). |
| `sosa:hasFeatureOfInterest` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Execution->FeatureOfInterest; the FOI participates in the act, so RO has_participant is the nearest relation, but hasFeatureOfInterest is more specific (the act's subject). Related. |
| `sosa:hasInput` | No direct RO mapping is adopted. Corrected sosa:hasInput is procedure-level (Procedure->ICE, a continuant subject); RO has_input is process-level (process->material). Domain clash: no RO counterpart. See-also RO has_input. |
| `sosa:hasInputValue` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Execution->input ICE (process subject, RO-compatible domain), but RO has_input ranges over material entities while an input value is an ICE. Related. |
| `sosa:hasMember` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: RO has_member is a mereological collection->item relation; sosa:hasMember deliberately carries NO parthood commitment (per the corrected design), so the match is related, not equivalent. |
| `sosa:hasOperatingConditions` | No direct RO mapping is adopted. System->OperatingConditions (an observation about the system); no RO counterpart (the aboutness intent is IAO/SHACL). No counterpart. |
| `sosa:hasOriginalSample` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: hasOriginalSample runs from a downstream Sample to the original it came from — the new-to-old direction, which in RO is derives-from (RO_0001000), not derives-into. That keeps the pair consistent with hasSample under derives-into and isSampleOf under derives-from. Related rather than a sub-property because sosa:Sample need not be material and the original persists after sub-sampling, so RO's material-transformation reading of derivation does not fully hold. RO_0001000 is not deprecated. |
| `sosa:hasOutput` | No direct RO mapping is adopted. Procedure-level (Procedure->ICE); RO has_output is process-level. No RO counterpart. See-also RO has_output. |
| `sosa:hasProcedure` | No direct RO mapping is adopted. Execution/System->Procedure (a specification relation); no RO counterpart. |
| `sosa:hasProperty` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: entity->Property; RO has_characteristic covers the specifically-dependent-continuant branch of sosa:Property but not the process-profile branch. Related. |
| `sosa:hasProxy` | No direct RO mapping is adopted. Stimulus proxies a Property for a Sensor; no RO proxy relation. No counterpart. |
| `sosa:hasResult` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Corrected super cco:has_output; RO has_output (process->participant). Close: RO leans material-entity outputs while sosa results include information entities. |
| `sosa:hasSample` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Inverse; RO derives_into. Related, same caveats. |
| `sosa:hasSimpleResult` | No direct RO mapping is adopted. Data property (literal result); no RO counterpart. |
| `sosa:hasSystemCapability` | No direct RO mapping is adopted. System->capability-describing Observation; no RO counterpart. |
| `sosa:hasUltimateFeatureOfInterest` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Ultimate subject of an act; nearest RO has_participant. Related. |
| `sosa:hasValidityContext` | No direct RO mapping is adopted. Validity-context relation among observations/properties; no RO counterpart. |
| `sosa:hosts` | No direct RO mapping is adopted. Platform hosts a System/Platform (physical mounting/support). RO host relations are biological (parasite/organism); not applicable. No RO counterpart. |
| `sosa:implementedBy` | No direct RO mapping is adopted. Inverse; no RO counterpart. |
| `sosa:implements` | No direct RO mapping is adopted. System->Procedure capability/specification; no RO counterpart. |
| `sosa:inputFor` | No direct RO mapping is adopted. Inverse of the procedure-level hasInput; no RO counterpart (see hasInput). |
| `sosa:inputValueForExecution` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Inverse; RO input_of, same range caveat. Related. |
| `sosa:isActedOnBy` | No direct RO mapping is adopted. Inverse of actsOn; no RO counterpart. |
| `sosa:isDetectedBy` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Inverse; RO causally_influences. Related, domain differs. |
| `sosa:isFeatureOfInterestOf` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Inverse; RO participates_in. Related. |
| `sosa:isHostedBy` | No direct RO mapping is adopted. Inverse; RO host relations are biological. No counterpart. |
| `sosa:isMemberOf` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: RO member-of (RO_0002350) matches isMemberOf almost exactly: both relate an item to the collection it belongs to, in the same direction, and neither is transitive. The one difference is that RO places member-of under part-of, while SOSA membership is deliberately not parthood — enough to rule out an asserted sub-property, not a close match. Not deprecated. |
| `sosa:isObservedBy` | No direct RO mapping is adopted. Inverse of observes (Property->Sensor); RO has no property-is-sensed-by relation. No counterpart. |
| `sosa:isOriginalSampleOf` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: The inverse: from the original sample to what derives from it — old-to-new, which in RO is derives-into (RO_0001001), again matching hasSample under derives-into and isSampleOf under derives-from. Related for the same reason as hasOriginalSample: sosa:Sample need not be material, so RO's derivation semantics only partly apply. RO_0001001 is not deprecated. |
| `sosa:isProcedureFor` | No direct RO mapping is adopted. Inverse; no RO counterpart. |
| `sosa:isPropertyOf` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Inverse; RO characteristic_of, same partial coverage. Related. |
| `sosa:isProxyFor` | No direct RO mapping is adopted. Inverse; no RO counterpart. |
| `sosa:isResultOf` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Inverse; RO output_of. Same material-leaning caveat. |
| `sosa:isResultOfMadeBySampler` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Chain-defined shortcut (isResultOf o madeBySampler); relates a Sample to its Sampler. Nearest RO output_of but the shortcut is sampler-specific. Related. |
| `sosa:isResultOfUsedProcedure` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Chain-defined shortcut; relates a Sample to the Procedure used. Related to output_of only distantly. Related. |
| `sosa:isSampleOf` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: A Sample is taken from its FeatureOfInterest; RO derives_from (material->material) is the nearest lineage relation, but sosa samples may be non-material and 'is sample of' adds representativeness. Related. |
| `sosa:isSampleOfUltimateFOI` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Terminal sample derives (across a chain) from the ultimate FOI; RO derives_from nearest. Related. |
| `sosa:isUltimateFeatureOfInterestOf` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Inverse; RO participates_in. Related. |
| `sosa:madeSamplingHasResult` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Chain shortcut Sampler->Sample (madeSampling o hasResult); nearest RO has_output but sampler-specific. Related. |
| `sosa:observationRelatedTo` | No direct RO mapping is adopted. Observation->Observation topical link; no RO counterpart. |
| `sosa:observedProperty` | No direct RO mapping is adopted. Observation->observed Property (a topical/aboutness relation); RO has no observation-to-property relation. No counterpart. |
| `sosa:observes` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Capability-level (Sensor capable of sensing a Property). RO capable_of is the capability relation but ranges over PROCESSES, not properties; direction/range differ. Related, not asserted. |
| `sosa:originated` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Corrected super cco:is_cause_of; RO causally_upstream_of (occurrent->occurrent) matches Stimulus->Observation causal precedence. Close. |
| `sosa:outputFor` | No direct RO mapping is adopted. Inverse of the procedure-level hasOutput; no RO counterpart. |
| `sosa:phenomenonOccurred` | No direct RO mapping is adopted. Temporal region->Execution; no RO counterpart (RO temporal relations relate occurrents, not to a phenomenon-time literal/entity in this sense). No counterpart. |
| `sosa:phenomenonTime` | No direct RO mapping is adopted. Execution->temporal region; no RO counterpart of this result-time relation. No counterpart. |
| `sosa:propertyFor` | No direct RO mapping is adopted. Inverse; no RO counterpart. |
| `sosa:qualityOf` | No direct RO mapping is adopted. Corrected super cco:is_about (the quality ICE is about the observation); aboutness lives in IAO, not RO. RO quality_of is a false friend (inheres-in, not aboutness). No counterpart. |
| `sosa:relatedObservation` | No direct RO mapping is adopted. Inverse; no RO counterpart. |
| `sosa:resultQuality` | No direct RO mapping is adopted. Corrected super cco:is_subject_of (inverse of is_about); aboutness is IAO territory. No RO counterpart. |
| `sosa:resultTime` | No direct RO mapping is adopted. Data property; no RO counterpart. |
| `sosa:startTime` | No direct RO mapping is adopted. Data property; no RO counterpart. |
| `sosa:usedForExecution` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Something used for an Execution (input side); RO input_of is the nearest process-input relation, but usedForExecution spans procedures/inputs generically. Related. |
| `sosa:usedForExecutionHasResult` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Chain shortcut Procedure->Sample; related to has_output distantly. Related. |
| `sosa:usedProcedure` | No direct RO mapping is adopted. Corrected super cco:prescribed_by; prescription is deontic/informational (IAO), not RO. No counterpart. |
| `sosa:wasActedOnBy` | No direct RO mapping is adopted. Property->Actuation (inverse of actsOnProperty); no RO counterpart. |
| `sosa:wasObservedBy` | No direct RO mapping is adopted. Property->Observation (inverse of observedProperty); no RO counterpart. |
| `sosa:wasOriginatedBy` | No direct RO mapping is adopted. The prior positive crosswalk candidate was reviewed for promotion to an OWL rdfs:subPropertyOf mapping, but its semantics are not uniformly entailed by the SOSA source relation. External candidate analysis: Inverse; corrected super cco:process_started_by has no RO counterpart, but the causal-downstream reading relates to RO immediately_causally_upstream_of family. Related. |

## Architecture boundary

This RO mapping track is parallel to the established SOSA-2023 BFO/CCO product set. This governance tranche does not modify `integrated`, `strict_bfo_mapping`, or `cco_extension`, and RO is not yet added to the existing formal SOSA-2023 release scope.
