# HermiT Unsatisfiable-Cluster Isolation

## Scope

This diagnostic isolates which clusters of active `SSN2BFO.ttl` mapping axioms contribute to the 24 HermiT unsatisfiable classes previously reported for the source/import-plus-mapping profile.

No repository ontology, spreadsheet, import, source example, release, generated, or existing report file was modified for this diagnostic. All variant graphs and ROBOT outputs were written under:

`/tmp/ssn-to-bfo-hermit-unsat-cluster-isolation`

This report starts from the same M2-style temporary graph used by `reports/hermit-source-vs-mapping-isolation.md`:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`
- all `owl:imports` triples removed
- `sosa:isSampleOf rdf:type owl:FunctionalProperty` removed
- `sosa:hasSample rdf:type owl:InverseFunctionalProperty` removed

## Baseline M2 Reproduction

The M2 baseline reproduced the prior HermiT result.

| Item | Result |
| --- | --- |
| Temporary graph | `/tmp/ssn-to-bfo-hermit-unsat-cluster-isolation/M2_baseline.ttl` |
| Triples | 15517 |
| Command | `robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-unsat-cluster-isolation/M2_baseline.ttl --output /tmp/ssn-to-bfo-hermit-unsat-cluster-isolation/M2_baseline-reasoned.ttl` |
| Return code | 1 |
| Reasoned output | no |
| Major result | HermiT reported 24 unsatisfiable classes |
| Sample simplicity blocker | did not reappear |

Baseline unsatisfiable classes:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:Accuracy`
- `ssn-system:ActuationRange`
- `ssn-system:BatteryLifetime`
- `ssn-system:DetectionLimit`
- `ssn-system:Drift`
- `ssn-system:Frequency`
- `ssn-system:Latency`
- `ssn-system:MaintenanceSchedule`
- `ssn-system:MeasurementRange`
- `ssn-system:OperatingPowerRange`
- `ssn-system:OperatingProperty`
- `ssn-system:Precision`
- `ssn-system:Resolution`
- `ssn-system:ResponseTime`
- `ssn-system:Selectivity`
- `ssn-system:Sensitivity`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`
- `ssn-system:SystemProperty`

## Cluster Removal Method

The diagnostic parsed `SSN2BFO.ttl` with `rdflib`, grouped mapping subjects by source namespace and mapping role, and removed cluster-owned triples from a temporary copy of the mapping graph only. For each removed mapping subject, attached blank-node expression triples were removed recursively so that temporary variants did not leave disconnected RDF lists or restriction blank nodes.

Each variant was then merged with unchanged source/import graphs, had `owl:imports` and the two sample functional-property assertions removed, and was tested with:

`robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>`

Tool versions:

- ROBOT: `ROBOT version 1.9.7`
- Java: `java version "22.0.2" 2024-07-16`

Clusters tested:

- A, core SOSA class mappings: `sosa:ActuatableProperty`, `sosa:Actuator`, `sosa:ObservableProperty`, `sosa:Observation`, `sosa:Procedure`, `sosa:Sensor`
- B, core SOSA property mappings: `sosa:actsOnProperty`, `sosa:hasResult`, `sosa:isActedOnBy`, `sosa:isResultOf`, `sosa:madeActuation`, `sosa:madeByActuator`, `sosa:madeBySampler`, `sosa:madeBySensor`, `sosa:madeObservation`, `sosa:madeSampling`, `sosa:observedProperty`, `sosa:observes`, `sosa:usedProcedure`
- C, SOSA sample/property-chain mappings: `sosa:hasSample`, `sosa:hosts`, `sosa:isHostedBy`, `sosa:isSampleOf`
- D, SSN core class mappings: `ssn:Input`, `ssn:Output`
- E, SSN core property mappings: `ssn:deployedOnPlatform`, `ssn:deployedSystem`, `ssn:detects`, `ssn:hasDeployment`, `ssn:hasInput`, `ssn:hasOutput`, `ssn:hasSubSystem`, `ssn:implementedBy`, `ssn:inDeployment`, `ssn:wasOriginatedBy`
- F, SSN Systems class mappings: `ssn-system:Accuracy`, `ssn-system:ActuationRange`, `ssn-system:Condition`, `ssn-system:DetectionLimit`, `ssn-system:Drift`, `ssn-system:Frequency`, `ssn-system:Latency`, `ssn-system:MaintenanceSchedule`, `ssn-system:OperatingPowerRange`, `ssn-system:OperatingProperty`, `ssn-system:OperatingRange`, `ssn-system:Precision`, `ssn-system:Resolution`, `ssn-system:ResponseTime`, `ssn-system:Selectivity`, `ssn-system:Sensitivity`, `ssn-system:SurvivalProperty`, `ssn-system:SurvivalRange`, `ssn-system:SystemCapability`, `ssn-system:SystemLifetime`, `ssn-system:SystemProperty`
- G, SSN Systems property mappings: `ssn-system:hasOperatingProperty`, `ssn-system:hasOperatingRange`, `ssn-system:hasSurvivalProperty`, `ssn-system:hasSurvivalRange`, `ssn-system:hasSystemCapability`, `ssn-system:hasSystemProperty`, `ssn-system:qualityOfObservation`
- H, Sample Relationship mappings: `sosa-rel:RelationshipNature`, `sosa-rel:SampleRelationship`

## Variant Summary Table

| Variant | Removed subjects | Return code | Unsat count | Change vs baseline | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `M2_baseline` | 0 | 1 | 24 | 0 | unsatisfiable classes |
| `A_core_sosa_class_mappings` | 6 | 1 | 19 | -5 | unsatisfiable classes |
| `B_core_sosa_property_mappings` | 13 | 1 | 21 | -3 | unsatisfiable classes |
| `C_sosa_sample_property_chain_mappings` | 4 | 1 | 21 | -3 | unsatisfiable classes |
| `D_ssn_core_class_mappings` | 2 | 1 | 24 | 0 | unsatisfiable classes |
| `E_ssn_core_property_mappings` | 10 | 1 | 22 | -2 | unsatisfiable classes |
| `F_ssn_systems_class_mappings` | 21 | 1 | 24 | 0 | unsatisfiable classes |
| `G_ssn_systems_property_mappings` | 7 | 1 | 8 | -16 | unsatisfiable classes |
| `H_sample_relationship_mappings` | 2 | 1 | 24 | 0 | unsatisfiable classes |
| `I_all_class_mappings` | 31 | 1 | 19 | -5 | unsatisfiable classes |
| `J_all_property_mappings` | 34 | 1 | 3 | -21 | unsatisfiable classes |
| `K_remove_sosa_classes_and_sosa_properties` | 23 | 1 | 19 | -5 | unsatisfiable classes |
| `L_remove_ssn_core_and_systems_properties` | 17 | 1 | 6 | -18 | unsatisfiable classes |
| `M_remove_sosa_sample_chains_and_system_properties` | 11 | 1 | 5 | -19 | unsatisfiable classes |
| `N_remove_sosa_class_and_all_properties` | 40 | 1 | 3 | -21 | unsatisfiable classes |
| `O_remove_all_class_and_all_property_mappings` | 65 | 0 | 0 | -24 | clean |
| `P_all_properties_plus_system_class_mappings` | 55 | 0 | 0 | -24 | clean |

For the clean variants `O` and `P`, reasoned output files were produced and parsed. Both had `owl:Nothing` count `0`.

No tested variant reintroduced the `sosa:hasSample` / `sosa:isSampleOf` simplicity blocker, because the two sample functional-property cleanup removals were applied consistently to every variant.

## Unsatisfiable-Class Set Comparison

Key reductions:

| Variant | Remaining unsatisfiable classes |
| --- | --- |
| `A_core_sosa_class_mappings` | `ssn-system:Accuracy`, `ssn-system:ActuationRange`, `ssn-system:BatteryLifetime`, `ssn-system:DetectionLimit`, `ssn-system:Drift`, `ssn-system:Frequency`, `ssn-system:Latency`, `ssn-system:MaintenanceSchedule`, `ssn-system:MeasurementRange`, `ssn-system:OperatingPowerRange`, `ssn-system:OperatingProperty`, `ssn-system:Precision`, `ssn-system:Resolution`, `ssn-system:ResponseTime`, `ssn-system:Selectivity`, `ssn-system:Sensitivity`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime`, `ssn-system:SystemProperty` |
| `G_ssn_systems_property_mappings` | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus`, `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |
| `J_all_property_mappings` | `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |
| `L_remove_ssn_core_and_systems_properties` | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus`, `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |
| `M_remove_sosa_sample_chains_and_system_properties` | `ssn:Input`, `ssn:Output`, `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, `ssn-system:SystemLifetime` |
| `O_remove_all_class_and_all_property_mappings` | none |
| `P_all_properties_plus_system_class_mappings` | none |

Interpretation of the set comparison:

- Removing all property mappings reduced 24 unsatisfiable classes to 3.
- The 3 classes left after removing all property mappings were `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, and `ssn-system:SystemLifetime`.
- Removing all property mappings plus all SSN Systems class mappings cleared the remaining 3 classes.
- Removing all class mappings alone reduced only the same 5 classes as the core SOSA class cluster.

## Cluster Findings

### Clusters That Appeared Irrelevant In Isolation

These removals did not change the 24-class unsatisfiable set:

- D, SSN core class mappings
- F, SSN Systems class mappings
- H, Sample Relationship mappings

This does not prove those mappings are semantically correct. It means only that removing the cluster by itself did not reduce the HermiT unsatisfiable-class set in this M2 diagnostic graph.

### Clusters That Reduced The Set

Core SOSA class mappings reduced the set from 24 to 19. The removed unsatisfiable classes were:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`

Core SOSA property mappings reduced the set from 24 to 21. The removed unsatisfiable classes were:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Stimulus`

SOSA sample/property-chain mappings reduced the set from 24 to 21. The removed unsatisfiable classes were:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Stimulus`

SSN core property mappings reduced the set from 24 to 22. The removed unsatisfiable classes were:

- `ssn:Input`
- `ssn:Output`

SSN Systems property mappings reduced the set from 24 to 8. The removed unsatisfiable classes were:

- `ssn-system:Accuracy`
- `ssn-system:ActuationRange`
- `ssn-system:DetectionLimit`
- `ssn-system:Drift`
- `ssn-system:Frequency`
- `ssn-system:Latency`
- `ssn-system:MaintenanceSchedule`
- `ssn-system:MeasurementRange`
- `ssn-system:OperatingPowerRange`
- `ssn-system:OperatingProperty`
- `ssn-system:Precision`
- `ssn-system:Resolution`
- `ssn-system:ResponseTime`
- `ssn-system:Selectivity`
- `ssn-system:Sensitivity`
- `ssn-system:SystemProperty`

All active property mappings together reduced the set from 24 to 3. This was the largest broad reduction short of clearing all active mapping axioms.

### Clusters That Cleared The Set

Two broad temporary removals cleared the unsatisfiable-class set:

- all active class mappings plus all active property mappings
- all active property mappings plus all SSN Systems class mappings

These broad clean variants are diagnostic only. They do not imply that all removed mappings are wrong, and they are too broad to use as a correction plan.

## Second-Level Isolation Findings

Individual reducer tests were run inside the clusters that changed the baseline set.

| Variant | Unsat count | Removed from baseline |
| --- | ---: | --- |
| `A1_remove_Procedure` | 22 | `ssn:Input`, `ssn:Output` |
| `A1_remove_Sensor` | 21 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| `B1_remove_madeBySensor` | 21 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| `B1_remove_observedProperty` | 21 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| `C1_remove_hosts` | 21 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| `E1_remove_hasInput` | 23 | `ssn:Input` |
| `E1_remove_hasOutput` | 23 | `ssn:Output` |
| `G1_remove_hasOperatingProperty` | 21 | `ssn-system:MaintenanceSchedule`, `ssn-system:OperatingPowerRange`, `ssn-system:OperatingProperty` |
| `G1_remove_hasSystemProperty` | 11 | `ssn-system:Accuracy`, `ssn-system:ActuationRange`, `ssn-system:DetectionLimit`, `ssn-system:Drift`, `ssn-system:Frequency`, `ssn-system:Latency`, `ssn-system:MeasurementRange`, `ssn-system:Precision`, `ssn-system:Resolution`, `ssn-system:ResponseTime`, `ssn-system:Selectivity`, `ssn-system:Sensitivity`, `ssn-system:SystemProperty` |

Second-level observations:

- `ssn-system:hasSystemProperty` is the largest individual reducer, dropping the count from 24 to 11.
- `ssn-system:hasOperatingProperty` accounts for a smaller SSN Systems cluster involving `OperatingProperty`, `OperatingPowerRange`, and `MaintenanceSchedule`.
- `sosa:Sensor`, `sosa:madeBySensor`, `sosa:observedProperty`, and `sosa:hosts` each remove the same SOSA/SSN stimulus cluster: `sosa:Observation`, `sosa:Sensor`, and `ssn:Stimulus`.
- `ssn:hasInput` and `ssn:hasOutput` isolate the direct `ssn:Input` and `ssn:Output` cases.
- No single individual mapping removal cleared the full unsatisfiable set.

The final 3 unsatisfiable classes after removing all active property mappings were not cleared by removing `ssn-system:SystemLifetime`, `ssn-system:SurvivalProperty`, or `ssn-system:SystemProperty` individually in the same temporary graph. They were cleared only when all active SSN Systems class mappings were removed together with all active property mappings.

## Assessment

### Clusters That Appear Irrelevant To This HermiT Set

The Sample Relationship cluster did not affect the M2 24-class set in this diagnostic. SSN core class mappings and SSN Systems class mappings also did not reduce the set when removed alone.

### Clusters That Reduce Or Clear Unsats

The strongest contributor cluster is the active SSN Systems property-mapping cluster. Within it, `ssn-system:hasSystemProperty` is the largest single reducer. This points to a focused follow-up around the SSN Systems property-mapping pattern, especially dependence-direction and domain/range interaction under full OWL DL.

The SOSA observation/sensor/stimulus cluster is affected by multiple mappings in different sections. Because `sosa:Sensor`, `sosa:madeBySensor`, `sosa:observedProperty`, and `sosa:hosts` each remove the same three classes when removed individually, the current diagnostic shows an interaction cluster rather than one uniquely isolated axiom.

The `ssn:Input` and `ssn:Output` cases are narrower: removing `ssn:hasInput` removes `ssn:Input`, and removing `ssn:hasOutput` removes `ssn:Output`.

The final `ssn-system:BatteryLifetime`, `ssn-system:SurvivalProperty`, and `ssn-system:SystemLifetime` unsats appear only after larger interacting clusters are removed. They require explanation-driven follow-up rather than a direct conclusion from this broad cluster test.

### What This Diagnostic Cannot Conclude

This report does not identify minimal unsatisfiable axiom explanations. It also does not prove that a mapping is semantically wrong merely because removing it reduces HermiT unsatisfiability. The results only identify which temporary mapping-cluster removals change the HermiT unsatisfiable-class set under the M2 cleanup profile.

## Recommendation

- Do not make repository ontology changes from this diagnostic branch.
- Keep the ELK validation suite as the near-term regression baseline.
- Keep HermiT/full OWL DL cleanup separate from ELK/instance entailment testing.
- If HermiT cleanup continues, start with the smallest high-impact reducer cluster: the SSN Systems property mappings, especially `ssn-system:hasSystemProperty`, then run explanation-driven follow-up before changing any mapping.
- Treat the SOSA observation/sensor/stimulus group as a second follow-up cluster because several mappings reduce the same three unsatisfiable classes.
- Treat `ssn:hasInput` and `ssn:hasOutput` as narrow follow-up candidates for the `ssn:Input` and `ssn:Output` cases.
- Do not use the broad clean variants as correction plans; they are only bounds showing that the unsats are mapping-cluster-dependent.
