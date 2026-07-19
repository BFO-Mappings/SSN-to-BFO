# HermiT Diagnostic: `ssn-system:hasSystemProperty`

## Scope

This diagnostic focuses on the active mapping:

```ttl
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

where local `imports/cco.ttl` labels `bfo:BFO_0000194` as `specifically depended on by`.

Prior cluster isolation found that temporarily removing this mapping was the largest individual reducer in the M2 HermiT profile. This report reproduces that result and tests nearby temporary variants. It does not modify repository ontology files, spreadsheets, imports, source examples, generated/release artifacts, or existing reports.

All temporary files were written under:

`/tmp/ssn-to-bfo-hermit-hasSystemProperty-explanation`

## Baseline Setup

The baseline graph was built by merging:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Temporary cleanup applied to every variant:

- removed all `owl:imports` triples;
- removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- removed `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Baseline command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-hasSystemProperty-explanation/M2_baseline.ttl --output /tmp/ssn-to-bfo-hermit-hasSystemProperty-explanation/M2_baseline-reasoned.ttl
```

Tool versions:

- ROBOT: `ROBOT version 1.9.7`
- Java: `java version "22.0.2" 2024-07-16`

Baseline result:

- Return code: `1`
- Reasoned output: no
- Major result: HermiT reported 24 unsatisfiable classes
- The `sosa:hasSample` / `sosa:isSampleOf` simplicity blocker did not reappear

## Local Evidence For `hasSystemProperty`

### Active Mapping

`SSN2BFO.ttl` contains:

```ttl
<http://www.w3.org/ns/ssn/systems/hasSystemProperty>
  rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
```

The current modeling rationale is directional:

```text
If x ssn-system:hasSystemProperty y, then y specifically depends on x.
```

So the source relation from capability to property maps to inverse dependence:

```text
x bfo:BFO_0000194 y
```

### Source Ontology Evidence

`imports/ssn-systems.ttl` defines `ssn-system:hasSystemProperty` as:

- an `owl:ObjectProperty`;
- an `rdfs:subPropertyOf ssn:hasProperty`;
- "Relation from an SystemCapability of a System to a SystemProperty describing the capabilities of the System."

The source pattern is therefore:

```text
SystemCapability -> SystemProperty
```

`ssn-system:SystemCapability` is a subclass of `ssn:Property` and has, among other restrictions:

```ttl
owl:onProperty ssn-system:hasSystemProperty ;
owl:allValuesFrom ssn-system:SystemProperty
```

`ssn-system:SystemProperty` is also a subclass of `ssn:Property` and has inverse restrictions:

```ttl
owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
owl:allValuesFrom ssn-system:SystemCapability
```

and:

```ttl
owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
owl:minCardinality "1"^^xsd:nonNegativeInteger
```

### Local BFO Evidence

Local labels and constraints verified in `imports/cco.ttl`:

| IRI | Label | Relevant local constraints |
| --- | --- | --- |
| `bfo:BFO_0000194` | specifically depended on by | `owl:inverseOf bfo:BFO_0000195`; domain is `bfo:BFO_0000020` or independent continuant excluding spatial region; range is `bfo:BFO_0000020` |
| `bfo:BFO_0000195` | specifically depends on | domain is `bfo:BFO_0000020`; range is `bfo:BFO_0000020` or independent continuant excluding spatial region |
| `bfo:BFO_0000020` | specifically dependent continuant | used in the BFO dependence constraints |
| `bfo:BFO_0000144` | Process Profile | appears in the current `SystemCapability` and `SystemProperty` class mappings |

### Current Class Mappings

`SSN2BFO.ttl` maps both related classes with a union involving SDC or process profile:

```ttl
ssn-system:SystemCapability
  rdfs:subClassOf (bfo:BFO_0000020 or bfo:BFO_0000144)
    and (cco:condition_described_by some cco:PerformanceSpecification) .
```

```ttl
ssn-system:SystemProperty
  rdfs:subClassOf (bfo:BFO_0000020 or bfo:BFO_0000144)
    and (cco:prescribed_by some cco:ArtifactFunctionSpecification) .
```

Verified local labels:

- `cco:ont00001884`: condition described by
- `cco:ont00000127`: Performance Specification
- `cco:ont00001920`: prescribed by
- `cco:ont00000118`: Artifact Function Specification

### Spreadsheet Evidence

Read-only inspection of `Current_SOSA-SSN to BFO-CCO.xlsx`, sheet `System Capability`, found:

| Row | Source term | Relevant spreadsheet evidence |
| ---: | --- | --- |
| 14 | `ssn-system:hasSystemProperty` | OWL axiom maps to `bfo:specifically_depended_on_by`; rationale says the source relation runs from capability `x` to property `y`, while the intended dependence runs from `y` specifically depending on `x`. |
| 30 | `ssn-system:SystemCapability` | Class row says SDC or Process Profile, described by a Performance Specification. |
| 32 | `ssn-system:SystemProperty` | Class row says SDC or Process Profile, prescribed by an Artifact Function Specification. |

## Variant Summary Table

| Variant | Temporary change | Return code | Unsat count | Delta vs baseline | Result |
| --- | --- | ---: | ---: | ---: | --- |
| `M2_baseline` | source/import plus `SSN2BFO.ttl` with sample cleanup | 1 | 24 | 0 | unsatisfiable classes |
| `remove_hasSystemProperty_mapping` | remove only the `SSN2BFO.ttl` `hasSystemProperty rdfs:subPropertyOf BFO_0000194` mapping subject | 1 | 11 | -13 | unsatisfiable classes |
| `remove_SystemCapability_class_mapping` | remove only the `SSN2BFO.ttl` `SystemCapability` class mapping subject | 1 | 24 | 0 | unsatisfiable classes |
| `remove_SystemProperty_class_mapping` | remove only the `SSN2BFO.ttl` `SystemProperty` class mapping subject | 1 | 24 | 0 | unsatisfiable classes |
| `remove_hasSystemProperty_plus_SystemCapability` | remove property mapping plus `SystemCapability` class mapping | 1 | 11 | -13 | unsatisfiable classes |
| `remove_hasSystemProperty_plus_SystemProperty` | remove property mapping plus `SystemProperty` class mapping | 1 | 11 | -13 | unsatisfiable classes |
| `remove_hasSystemProperty_plus_both_classes` | remove property mapping plus both related class mappings | 1 | 11 | -13 | unsatisfiable classes |
| `remove_source_hasSystemProperty_restrictions` | remove source `SystemCapability`/`SystemProperty` restrictions that mention `hasSystemProperty` | 1 | 11 | -13 | unsatisfiable classes |
| `remove_hasSystemProperty_and_source_restrictions` | remove property mapping plus source restrictions mentioning `hasSystemProperty` | 1 | 11 | -13 | unsatisfiable classes |
| `remove_BFO194_domain_range` | remove local `BFO_0000194` domain/range constraints only | 1 | 24 | 0 | unsatisfiable classes |
| `remove_BFO194_inverseOf_only` | remove `BFO_0000194 owl:inverseOf BFO_0000195` only | 1 | 24 | 0 | unsatisfiable classes |
| `remove_BFO195_domain_range` | remove local `BFO_0000195` domain/range constraints only | 1 | 24 | 0 | unsatisfiable classes |
| `remove_BFO194_BFO195_domain_range` | remove domain/range constraints for both `BFO_0000194` and `BFO_0000195` | 1 | 8 | -16 | unsatisfiable classes |
| `remove_BFO194_BFO195_domain_range_and_inverse` | remove domain/range constraints for both dependence properties plus their inverse link | 1 | 8 | -16 | unsatisfiable classes |

No variant in this focused report fully cleared the HermiT unsatisfiable-class set.

## Unsatisfiable-Class Set Comparison

The M2 baseline unsatisfiable classes were:

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

Removing only the `hasSystemProperty` mapping removed these 13 classes from the reported unsatisfiable set:

- `ssn-system:Accuracy`
- `ssn-system:ActuationRange`
- `ssn-system:DetectionLimit`
- `ssn-system:Drift`
- `ssn-system:Frequency`
- `ssn-system:Latency`
- `ssn-system:MeasurementRange`
- `ssn-system:Precision`
- `ssn-system:Resolution`
- `ssn-system:ResponseTime`
- `ssn-system:Selectivity`
- `ssn-system:Sensitivity`
- `ssn-system:SystemProperty`

The remaining 11 classes after removing only `hasSystemProperty` were:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:BatteryLifetime`
- `ssn-system:MaintenanceSchedule`
- `ssn-system:OperatingPowerRange`
- `ssn-system:OperatingProperty`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

Removing domain/range constraints for both `BFO_0000194` and `BFO_0000195` left 8 classes:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

## Interpretation Of The 13 Classes Removed By Removing `hasSystemProperty`

The 13 removed classes are all `ssn-system` classes. Most are subclasses or specializations connected to `SystemProperty` in the local SSN Systems source ontology. This is consistent with the source pattern where `SystemProperty` instances are constrained by inverse `hasSystemProperty` restrictions back to `SystemCapability`.

The diagnostic points to an interaction between:

1. the active mapping `hasSystemProperty rdfs:subPropertyOf BFO_0000194`;
2. source restrictions on `SystemCapability` and `SystemProperty` that use `hasSystemProperty` and its inverse;
3. BFO dependence-property domain/range constraints around `BFO_0000194` and `BFO_0000195`;
4. the broader mapped class context where `SystemCapability` and `SystemProperty` are modeled as SDC-or-process-profile unions.

This is a likely interaction pattern, not a formal minimal explanation. The test did not prove that the `hasSystemProperty` mapping is wrong; it showed that removing it, temporarily, removes 13 HermiT-reported unsatisfiable classes from this merged profile.

## Additional Related-Class Interaction Variants

Removing only the related class mappings did not reduce the unsatisfiable set:

- Removing only `SystemCapability` class mapping: 24 unsats remain.
- Removing only `SystemProperty` class mapping: 24 unsats remain.

Adding related class removals on top of `hasSystemProperty` did not reduce below 11:

- `hasSystemProperty` plus `SystemCapability`: 11 unsats remain.
- `hasSystemProperty` plus `SystemProperty`: 11 unsats remain.
- `hasSystemProperty` plus both classes: 11 unsats remain.

The same 24-to-11 reduction occurs when source restrictions mentioning `hasSystemProperty` are removed while leaving the property mapping in place. Adding the property mapping removal to that source-restriction removal does not reduce further.

This suggests that the high-impact reduction is not driven by the standalone class mappings for `SystemCapability` or `SystemProperty`. It is more likely driven by the relation between the active `BFO_0000194` property mapping and the imported SSN Systems restrictions that constrain `SystemCapability` and `SystemProperty` through `hasSystemProperty` and its inverse.

The BFO probe is also informative:

- Removing only `BFO_0000194` domain/range constraints did not reduce the set.
- Removing only `BFO_0000195` domain/range constraints did not reduce the set.
- Removing domain/range constraints for both `BFO_0000194` and `BFO_0000195` reduced 24 unsats to 8.

Because `BFO_0000194` and `BFO_0000195` are inverse properties locally, the dependence-property constraint package appears relevant as a pair. This does not imply those imported BFO constraints should be changed; it only helps explain why the `hasSystemProperty` subproperty mapping can have broad HermiT effects.

## Assessment

### What Is Likely

The largest effect is likely a full OWL DL interaction between:

- `hasSystemProperty` as a subproperty of `BFO_0000194`;
- source restrictions using `hasSystemProperty` and inverse `hasSystemProperty`;
- the inverse/domain/range package around `BFO_0000194` and `BFO_0000195`;
- SSN Systems classes under `SystemProperty`.

The reduction is not mainly explained by the `SystemCapability` or `SystemProperty` class mappings alone, because removing those class mappings by themselves did not change the unsat set.

### What Is Not Proved

This report does not prove:

- that `hasSystemProperty -> BFO_0000194` is semantically wrong;
- that the spreadsheet rationale is wrong;
- that `SystemCapability` or `SystemProperty` class mappings are wrong;
- that imported BFO domain/range constraints should be changed;
- that the 13 removed classes share one minimal conflict explanation.

The result is a controlled reducer diagnostic, not a minimal unsatisfiable-axiom explanation.

### What Needs More Explanation Tooling

The next useful step would be a minimal-conflict or explanation extraction for one representative class, such as:

- `ssn-system:SystemProperty`;
- `ssn-system:Accuracy`;
- `ssn-system:ActuationRange`;
- `ssn-system:MeasurementRange`.

If explanation extraction is not feasible with local tooling, the next-best diagnostic is to test narrowly scoped temporary alternatives for the property mapping while keeping the source restrictions and BFO constraints intact.

## Recommendation

- Do not change repository mappings in this branch.
- Keep the current ELK validation suite as the regression baseline.
- Treat HermiT/full OWL DL cleanup as a separate modeling/profile task.
- In the next branch, either:
  - attempt explanation/minimal-conflict extraction for one representative removed class; or
  - test a narrowly scoped HermiT-compatible alternative for `hasSystemProperty` in temporary graphs only.
- Do not use this report alone to decide that `hasSystemProperty` should be removed, deferred, or replaced. It identifies the highest-impact HermiT interaction point for follow-up review.
