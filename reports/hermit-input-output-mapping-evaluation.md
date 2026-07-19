# HermiT Input/Output Mapping Evaluation

## Scope

This report is a diagnostic-only review of the remaining `ssn:Input` / `ssn:Output` HermiT subcluster.

It does not edit ontology mappings, spreadsheets, imports, source examples, generated artifacts, release artifacts, or existing reports. All HermiT test graphs were built under:

```text
/tmp/ssn-to-bfo-hermit-input-output-mapping-evaluation
```

The purpose is to determine whether the remaining `ssn:Input` and `ssn:Output` unsatisfiabilities are driven by active class mappings, active property mappings, source restrictions, target BFO/CCO context, or a mixed interaction.

## Prior Context

The current post-SSN-Systems-fix M2 HermiT profile has five remaining unsatisfiable classes:

```text
sosa:Observation
sosa:Sensor
ssn:Input
ssn:Output
ssn:Stimulus
```

The previous focused report, `reports/hermit-core-sosa-sensor-cluster-explanation.md`, showed that these separate into:

- an Observation / Sensor / Stimulus cluster;
- an Input / Output pair.

It also showed that removing `ssn:hasInput` removes `ssn:Input`, and removing `ssn:hasOutput` removes `ssn:Output`. This report narrows in on that Input/Output pair.

## Method

For full-graph variants, the temporary graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Then the following cleanup was applied:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

Each variant was tested with:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

ROBOT version: `ROBOT version 1.9.7`

Java version:

```text
java version "22.0.2" 2024-07-16
Java(TM) SE Runtime Environment (build 22.0.2+9-70)
Java HotSpot(TM) 64-Bit Server VM (build 22.0.2+9-70, mixed mode, sharing)
```

For unsatisfiable variants, ROBOT returned nonzero and did not write a reasoned output. For clean variants, a reasoned output was produced and no `owl:Nothing` entities were found. The sample simplicity blocker did not reappear in these variants.

## Current Baseline

Variant A reproduced the current full M2 baseline:

```text
sosa:Observation
sosa:Sensor
ssn:Input
ssn:Output
ssn:Stimulus
```

Variant B, the source/import-only control without `SSN2BFO.ttl`, was HermiT-clean. This confirms that the Input/Output pair is not present in the source/import profile alone.

## Active Input/Output Mapping Inventory

Relevant active mappings in `SSN2BFO.ttl`:

| Source | Mapping type | Active target or expression |
| --- | --- | --- |
| `ssn:Input` | direct class mapping | `rdfs:subClassOf cco:ont00000958` |
| `ssn:Output` | direct class mapping | `rdfs:subClassOf cco:ont00000958` |
| `ssn:hasInput` | direct property mapping | `rdfs:subPropertyOf cco:ont00001921` |
| `ssn:hasOutput` | direct property mapping | `rdfs:subPropertyOf cco:ont00001986` |
| `sosa:Procedure` | class-expression mapping | subclass of `cco:ont00000965` and `cco:ont00001942 some bfo:BFO_0000015` |
| `sosa:Result` | class-expression mapping | equivalent class using `bfo:BFO_0000040 OR cco:ont00000958` and `cco:ont00001816 some Actuation/Observation/Sampling` |
| `sosa:usedProcedure` | direct property mapping | `rdfs:subPropertyOf cco:ont00001920` |
| `sosa:hasResult` | direct property mapping | `rdfs:subPropertyOf cco:ont00001986` |

The `ssn:Input` and `ssn:Output` class mappings are intentionally simple named-class mappings. The active one-class reducers are the property mappings:

```ttl
ssn:hasInput rdfs:subPropertyOf cco:ont00001921 .
ssn:hasOutput rdfs:subPropertyOf cco:ont00001986 .
```

## Source Context Inventory

Relevant imported source axioms in `imports/ssn.ttl` include:

- `ssn:hasInput`
  - object property;
  - comment/definition: relation between a `Procedure` and an `Input`.
- `ssn:hasOutput`
  - object property;
  - comment/definition: relation between a `Procedure` and an `Output`.
- `sosa:Procedure`
  - `ssn:hasInput only ssn:Input`;
  - `ssn:hasOutput only ssn:Output`;
  - `ssn:implementedBy only ssn:System`.
- `ssn:Input`
  - inverse `ssn:hasInput` all-values restriction to `sosa:Procedure`;
  - inverse `ssn:hasInput` minimum-cardinality restriction.
- `ssn:Output`
  - inverse `ssn:hasOutput` all-values restriction to `sosa:Procedure`;
  - inverse `ssn:hasOutput` minimum-cardinality restriction.

The focused package counts used in the temporary removals were:

| Source/context package | Removed triples |
| --- | ---: |
| `ssn:Input` source package | 28 |
| `ssn:Output` source package | 28 |
| `ssn:hasInput` source package | 28 |
| `ssn:hasOutput` source package | 28 |
| source restrictions using `ssn:hasInput` | 28 |
| source restrictions using `ssn:hasOutput` | 28 |

These package counts overlap because the source class restrictions and inverse-property restriction nodes connect `Procedure`, `Input`, `Output`, `hasInput`, and `hasOutput`.

## Target BFO/CCO Context Summary

Local labels and key commitments verified in `imports/cco.ttl`:

| Identifier | Local label | Relevant local context |
| --- | --- | --- |
| `cco:ont00000958` | Information Content Entity | subclass of `bfo:BFO_0000031` / generically dependent continuant |
| `cco:ont00001921` | has input | subproperty of `bfo:BFO_0000057`; domain `bfo:BFO_0000015`; range `bfo:BFO_0000002` |
| `cco:ont00001986` | has output | subproperty of `bfo:BFO_0000057`; domain `bfo:BFO_0000015`; range `bfo:BFO_0000002` |
| `cco:ont00000965` | Directive Information Content Entity | subclass of `cco:ont00000958` |
| `cco:ont00001942` | prescribes | domain `cco:ont00000965` |
| `bfo:BFO_0000057` | has participant | domain `bfo:BFO_0000015` |
| `bfo:BFO_0000015` | process | subclass of occurrent |
| `bfo:BFO_0000002` | continuant | disjoint with occurrent |
| `bfo:BFO_0000031` | generically dependent continuant | subclass of continuant |

Important interaction pattern:

- `cco:ont00001921` / `has input` and `cco:ont00001986` / `has output` give `ssn:hasInput` and `ssn:hasOutput` process-domain and continuant-range behavior through the active property mappings.
- `sosa:Procedure` is actively mapped into directive information-content context, not process context.
- The source restrictions connect `Procedure`, `Input`, and `Output` through `ssn:hasInput` / `ssn:hasOutput` and inverse restrictions.

## Variant Summary Table

| ID | Variant | Triples | Return code | Output? | Unsat count | Unsat set |
| --- | --- | ---: | ---: | --- | ---: | --- |
| A | `A_full_m2` | 15477 | 1 | no | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| B | `B_source_import_only` | 14485 | 0 | yes | 0 | clean |
| C | `C_remove_hasInput_mapping` | 15476 | 1 | no | 4 | `sosa:Observation`, `sosa:Sensor`, `ssn:Output`, `ssn:Stimulus` |
| D | `D_remove_hasOutput_mapping` | 15475 | 1 | no | 4 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Stimulus` |
| E | `E_remove_both_property_mappings` | 15474 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| F | `F_remove_Input_class_mapping` | 15475 | 1 | no | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| G | `G_remove_Output_class_mapping` | 15475 | 1 | no | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| H | `H_remove_Input_Output_class_mappings` | 15473 | 1 | no | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| I1 | `I1_remove_source_Input_package` | 15449 | 1 | no | 4 | `sosa:Observation`, `sosa:Sensor`, `ssn:Output`, `ssn:Stimulus` |
| I2 | `I2_remove_source_Output_package` | 15449 | 1 | no | 4 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Stimulus` |
| I3 | `I3_remove_source_hasInput_package` | 15449 | 1 | no | 4 | `sosa:Observation`, `sosa:Sensor`, `ssn:Output`, `ssn:Stimulus` |
| I4 | `I4_remove_source_hasOutput_package` | 15449 | 1 | no | 4 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Stimulus` |
| I5 | `I5_remove_source_restrictions_hasInput` | 15449 | 1 | no | 4 | `sosa:Observation`, `sosa:Sensor`, `ssn:Output`, `ssn:Stimulus` |
| I6 | `I6_remove_source_restrictions_hasOutput` | 15449 | 1 | no | 4 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Stimulus` |
| I7 | `I7_remove_source_restrictions_both` | 15434 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| J1 | `J1_remove_target_hasInput_domain_range` | 15475 | 1 | no | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| J2 | `J2_remove_target_hasOutput_domain_range` | 15475 | 1 | no | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| J3 | `J3_remove_target_both_domain_range` | 15473 | 1 | no | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| J4 | `J4_remove_ICE_super_equiv` | 15475 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| J5 | `J5_remove_ICE_subject_package` | 15459 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| K1 | `K1_source_plus_Input_class_mapping` | 14486 | 0 | yes | 0 | clean |
| K2 | `K2_source_plus_Output_class_mapping` | 14486 | 0 | yes | 0 | clean |
| K3 | `K3_source_plus_both_class_mappings` | 14487 | 0 | yes | 0 | clean |
| K4 | `K4_source_plus_hasInput_mapping` | 14486 | 0 | yes | 0 | clean |
| K5 | `K5_source_plus_hasOutput_mapping` | 14486 | 0 | yes | 0 | clean |
| K6 | `K6_source_plus_both_property_mappings` | 14487 | 0 | yes | 0 | clean |
| K7 | `K7_source_plus_Input_class_hasInput` | 14487 | 0 | yes | 0 | clean |
| K8 | `K8_source_plus_Output_class_hasOutput` | 14487 | 0 | yes | 0 | clean |
| K9 | `K9_source_plus_all_IO_mappings` | 14489 | 0 | yes | 0 | clean |
| K10 | `K10_source_plus_all_core_class_mappings_hasInput` | 14808 | 1 | no | 1 | `ssn:Input` |
| K11 | `K11_source_plus_all_core_class_mappings_hasOutput` | 14808 | 1 | no | 1 | `ssn:Output` |
| K12 | `K12_source_plus_all_core_class_mappings_IO_props` | 14809 | 1 | no | 2 | `ssn:Input`, `ssn:Output` |
| L1 | `L1_core_classes_without_Procedure_mapping_plus_IO_props` | 14798 | 0 | yes | 0 | clean |
| L2 | `L2_core_classes_without_Result_mapping_plus_IO_props` | 14784 | 1 | no | 2 | `ssn:Input`, `ssn:Output` |
| L3 | `L3_Procedure_Input_class_hasInput` | 14498 | 1 | no | 1 | `ssn:Input` |
| L4 | `L4_Procedure_Output_class_hasOutput` | 14498 | 1 | no | 1 | `ssn:Output` |
| L5 | `L5_Procedure_both_classes_IO_props` | 14500 | 1 | no | 2 | `ssn:Input`, `ssn:Output` |
| L6 | `L6_core_classes_no_ObservationSensorStimulus_plus_IO_props` | 14758 | 1 | no | 2 | `ssn:Input`, `ssn:Output` |
| L7 | `L7_Procedure_hasInput_only` | 14497 | 1 | no | 1 | `ssn:Input` |
| L8 | `L8_Procedure_hasOutput_only` | 14497 | 1 | no | 1 | `ssn:Output` |
| L9 | `L9_Procedure_both_IO_props_no_IO_class_mappings` | 14498 | 1 | no | 2 | `ssn:Input`, `ssn:Output` |
| L10 | `L10_full_remove_Procedure_mapping` | 15466 | 1 | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| L11 | `L11_core_classes_without_InputOutput_class_plus_IO_props` | 14807 | 1 | no | 2 | `ssn:Input`, `ssn:Output` |
| L12 | `L12_core_classes_without_Procedure_InputOutput_plus_IO_props` | 14796 | 0 | yes | 0 | clean |

## `ssn:Input` Analysis

The `ssn:Input` unsat is independent from `ssn:Output` in the full graph:

- removing `ssn:hasInput` removes `ssn:Input` and leaves `ssn:Output` plus the Observation/Sensor/Stimulus trio;
- removing `ssn:hasOutput` does not remove `ssn:Input`;
- removing both properties removes both Input and Output and leaves only the trio.

The active `ssn:Input` class mapping is not sufficient or necessary in the tested variants:

- removing the `ssn:Input -> cco:ont00000958` class mapping from full M2 does not remove `ssn:Input`;
- source/import-only plus `ssn:Input` class mapping is clean;
- source/import-only plus `ssn:Input` class mapping and `ssn:hasInput` property mapping is clean;
- `sosa:Procedure` mapping plus `ssn:hasInput` is sufficient to reproduce `ssn:Input`, even without the `ssn:Input` class mapping.

The smallest tested reproduction for `ssn:Input` was:

```text
source/import-only graph
+ sosa:Procedure mapping
+ ssn:hasInput -> cco:ont00001921
```

That result points to a mixed interaction among:

- source inverse/min-cardinality restrictions on `ssn:Input`;
- source `sosa:Procedure` restrictions involving `ssn:hasInput`;
- the active `ssn:hasInput` property mapping to CCO `has input`;
- the active `sosa:Procedure` class-expression mapping into directive information-content context.

## `ssn:Output` Analysis

The `ssn:Output` pattern is parallel to `ssn:Input`:

- removing `ssn:hasOutput` removes `ssn:Output`;
- removing `ssn:hasInput` does not remove `ssn:Output`;
- removing both removes the pair.

The active `ssn:Output` class mapping is not sufficient or necessary in the tested variants:

- removing the `ssn:Output -> cco:ont00000958` class mapping from full M2 does not remove `ssn:Output`;
- source/import-only plus `ssn:Output` class mapping is clean;
- source/import-only plus `ssn:Output` class mapping and `ssn:hasOutput` property mapping is clean;
- `sosa:Procedure` mapping plus `ssn:hasOutput` is sufficient to reproduce `ssn:Output`, even without the `ssn:Output` class mapping.

The smallest tested reproduction for `ssn:Output` was:

```text
source/import-only graph
+ sosa:Procedure mapping
+ ssn:hasOutput -> cco:ont00001986
```

This makes the Output side a close mirror of the Input side.

## Source-Context Results

Source-side removal variants support the same split:

- removing source context for `ssn:Input`, `ssn:hasInput`, or restrictions using `ssn:hasInput` removes `ssn:Input`;
- removing source context for `ssn:Output`, `ssn:hasOutput`, or restrictions using `ssn:hasOutput` removes `ssn:Output`;
- removing both source-restriction packages removes the Input/Output pair.

These source removals do not clear the Observation/Sensor/Stimulus trio. They are specific to the Input/Output side of the remaining core cluster.

The source context should not be read as wrong from this diagnostic alone. The result only shows that the imported source restriction pattern participates in the full-OWL conflict once the relevant mapping axioms are added.

## Target-Context Results

The CCO target property domain/range removals were not sufficient:

- removing the domain/range of `cco:ont00001921` did not remove `ssn:Input`;
- removing the domain/range of `cco:ont00001986` did not remove `ssn:Output`;
- removing both target property domain/range packages did not remove either class.

However, removing the superclass/equivalent-class context for `cco:ont00000958` removed both `ssn:Input` and `ssn:Output`, leaving only the Observation/Sensor/Stimulus trio.

This does not prove that the `Information Content Entity` target is wrong. It shows that the ICE target context is part of the contradiction path. The focused reconstruction variants indicate that `sosa:Procedure`'s mapping to directive information-content context is more directly involved than the simple `ssn:Input` / `ssn:Output` class mappings.

## Reconstruction Results

Clean reconstruction variants:

- source/import-only;
- source/import-only plus `ssn:Input` mapping;
- source/import-only plus `ssn:Output` mapping;
- source/import-only plus both Input/Output class mappings;
- source/import-only plus `ssn:hasInput`;
- source/import-only plus `ssn:hasOutput`;
- source/import-only plus both Input/Output property mappings;
- source/import-only plus all four Input/Output mappings.

Unsat reconstruction variants:

- source/import-only plus all core class mappings and `ssn:hasInput` reproduced only `ssn:Input`;
- source/import-only plus all core class mappings and `ssn:hasOutput` reproduced only `ssn:Output`;
- source/import-only plus all core class mappings and both Input/Output property mappings reproduced the pair;
- source/import-only plus `sosa:Procedure` mapping and `ssn:hasInput` reproduced `ssn:Input`;
- source/import-only plus `sosa:Procedure` mapping and `ssn:hasOutput` reproduced `ssn:Output`;
- source/import-only plus `sosa:Procedure` mapping and both Input/Output property mappings reproduced the pair.

The key negative control was:

- all core class mappings except `sosa:Procedure`, plus `ssn:hasInput` and `ssn:hasOutput`, was HermiT-clean.

That makes `sosa:Procedure` the high-impact class mapping in the tested Input/Output interaction. By contrast, removing the `ssn:Input` and `ssn:Output` class mappings while keeping `sosa:Procedure` and the two property mappings still reproduced the pair.

## Focused Candidate Dependency Results

Smallest tested clearing groups:

| Unsat class | Smallest tested full-graph clearing action |
| --- | --- |
| `ssn:Input` | remove `ssn:hasInput` mapping, or remove source restrictions using `ssn:hasInput` |
| `ssn:Output` | remove `ssn:hasOutput` mapping, or remove source restrictions using `ssn:hasOutput` |
| Input/Output pair | remove both `ssn:hasInput` and `ssn:hasOutput`, remove both source restriction packages, remove ICE superclass/equivalent context, or remove `sosa:Procedure` mapping |

Smallest tested reproductions:

| Unsat class | Smallest tested reconstruction |
| --- | --- |
| `ssn:Input` | source/import-only plus `sosa:Procedure` mapping plus `ssn:hasInput` mapping |
| `ssn:Output` | source/import-only plus `sosa:Procedure` mapping plus `ssn:hasOutput` mapping |
| Input/Output pair | source/import-only plus `sosa:Procedure` mapping plus both Input/Output property mappings |

## Explanation Assessment

### Are Input And Output Independent?

Yes. The pair separates cleanly into two parallel one-class subclusters:

- `ssn:Input` depends on the `ssn:hasInput` side;
- `ssn:Output` depends on the `ssn:hasOutput` side.

Removing one property mapping does not remove the other class.

### Are `ssn:hasInput` And `ssn:hasOutput` Specifically Required?

They are specifically required in the tested reconstruction and removal variants.

The simple property mapping alone is not enough to reproduce the issue, but each property mapping becomes sufficient when combined with the active `sosa:Procedure` mapping and the imported source restrictions.

### Are Class Mappings Implicated?

The `ssn:Input` and `ssn:Output` class mappings themselves are not strongly implicated:

- removing them from full M2 does not clear their unsats;
- adding them alone does not reproduce the unsats;
- adding them with the corresponding property mapping remains clean.

The active `sosa:Procedure` class-expression mapping is implicated:

- removing it from full M2 clears the Input/Output pair;
- adding it with `ssn:hasInput` reproduces `ssn:Input`;
- adding it with `ssn:hasOutput` reproduces `ssn:Output`;
- excluding it from a broad core-class reconstruction keeps the Input/Output side clean.

### Is The Issue Mapping-Side, Source-Side, Target-Side, Or Mixed?

The evidence supports a mixed interaction:

- source-side restrictions connect `Procedure`, `Input`, `Output`, `hasInput`, and `hasOutput`;
- mapping-side property axioms connect `hasInput` and `hasOutput` to CCO process-domain input/output properties;
- mapping-side `sosa:Procedure` class expression places `Procedure` into directive information-content context;
- target ICE context participates, but the CCO target property domain/range removals alone did not clear the pair.

The current evidence does not support saying that the source ontology is wrong, that the CCO target terms are wrong, or that any one mapping is semantically invalid. It does support treating the active OWL combination as HermiT-risky.

### Does The Evidence Support A Fix-Evaluation Branch?

Yes, but it should be framed as evaluation, not a final semantic correction.

The narrowest practical evaluation branch would test temporarily deferring the active `ssn:hasInput` and `ssn:hasOutput` direct property mappings. That should be separated from any change to the Observation/Sensor/Stimulus cluster.

A second possible evaluation branch would test the `sosa:Procedure` class-expression mapping, because it is a smaller reconstruction trigger than the full core class-mapping context. That branch would need to be especially careful because `sosa:Procedure` is broader than the Input/Output pair and may affect sampling, observation, and actuation mappings.

## Recommendation

No repo mapping change should be made from this diagnostic branch.

Recommended next branch:

1. Create a fix-evaluation branch for the Input/Output pair.
2. Temporarily defer `ssn:hasInput -> cco:ont00001921` and `ssn:hasOutput -> cco:ont00001986` together, with spreadsheet cells updated consistently.
3. Regenerate the mapping audit and ELK instance entailment report.
4. Run the standard validation suite.
5. Run a HermiT M2 check to confirm whether the full baseline drops from five unsats to the Observation/Sensor/Stimulus trio.

Keep this separate from the Observation/Sensor/Stimulus cluster. The evidence here supports treating Input/Output as an independent pair, not as part of one monolithic core SOSA/SSN fix.
