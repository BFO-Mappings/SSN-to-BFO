# HermiT Diagnostic: `hasSystemProperty` Alternatives

## Scope

This report tests temporary alternatives for the active mapping:

```ttl
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

where `bfo:BFO_0000194` is locally labeled `specifically depended on by`.

The diagnostic is report-only. It does not modify `SSN2BFO.ttl`, spreadsheets, imports, source examples, generated/release artifacts, or existing reports. All variant graphs and ROBOT outputs were written under:

`/tmp/ssn-to-bfo-hermit-hasSystemProperty-alternatives`

## Baseline Setup

The temporary M2-style baseline graph was built by merging:

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
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-hasSystemProperty-alternatives/M2_baseline.ttl --output /tmp/ssn-to-bfo-hermit-hasSystemProperty-alternatives/M2_baseline-reasoned.ttl
```

Tool versions:

- ROBOT: `ROBOT version 1.9.7`
- Java: `java version "22.0.2" 2024-07-16`

Baseline result:

- Return code: `1`
- Reasoned output: no
- Sample simplicity blocker: no
- HermiT-reported unsatisfiable classes: 24

## Current Modeling Intent

The current modeling rationale is:

```text
If x ssn-system:hasSystemProperty y, then y specifically depends on x.
```

Because the source relation runs from `SystemCapability` to `SystemProperty`, while the intended dependence runs from the property back to the capability, the current active OWL mapping uses the inverse BFO relation:

```text
x bfo:BFO_0000194 y
```

The prior report, `reports/hermit-hasSystemProperty-explanation.md`, found that this mapping interacts with:

- source restrictions involving `hasSystemProperty` and inverse `hasSystemProperty`;
- the BFO `BFO_0000194` / `BFO_0000195` domain-range package;
- `SystemProperty` subclasses.

This report tests whether temporary alternatives improve the HermiT result while preserving, approximating, or explicitly deferring that modeling intent.

## Variant Summary Table

| Variant | Temporary edit | Return code | Reasoned output | Unsat count | Delta vs baseline | Delta vs removal | Sample blocker |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| `M2_baseline` | No `hasSystemProperty` edit. | 1 | no | 24 | 0 | +13 | no |
| `A_remove_hasSystemProperty_mapping` | Remove the `hasSystemProperty` mapping subject from the temporary `SSN2BFO` graph. | 1 | no | 11 | -13 | 0 | no |
| `B_annotation_no_logical_mapping` | Remove the logical `rdfs:subPropertyOf` mapping; no replacement logical triple added. | 1 | no | 11 | -13 | 0 | no |
| `C_topObjectProperty_placeholder` | Remove `BFO_0000194` mapping; add `hasSystemProperty rdfs:subPropertyOf owl:topObjectProperty`. | 1 | no | 11 | -13 | 0 | no |
| `D_wrong_direction_BFO0000195` | Remove `BFO_0000194` mapping; add `hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000195`. | 1 | no | 24 | 0 | +13 | no |
| `E_inverse_bridge_to_BFO0000195` | Remove direct mapping; add `ssn2bfo-test:systemPropertyOf owl:inverseOf hasSystemProperty` and `ssn2bfo-test:systemPropertyOf rdfs:subPropertyOf bfo:BFO_0000195`. | 1 | no | 24 | 0 | +13 | no |
| `F_rule_only_no_OWL_subproperty` | Remove logical `rdfs:subPropertyOf` mapping; richer semantics assumed outside OWL. | 1 | no | 11 | -13 | 0 | no |
| `G_weak_inverse_bridge_to_topObjectProperty` | Remove direct mapping; add local inverse bridge property only under `owl:topObjectProperty`. | 1 | no | 11 | -13 | 0 | no |
| `H_disconnected_top_placeholder` | Remove direct mapping; add unrelated local placeholder `rdfs:subPropertyOf owl:topObjectProperty`. | 1 | no | 11 | -13 | 0 | no |

No variant fully cleared the HermiT unsatisfiable-class set. No variant reintroduced the `sosa:hasSample` / `sosa:isSampleOf` simplicity blocker.

## Unsat Set Comparison

The baseline M2 graph reported 24 unsatisfiable classes. The removal/no-logical-mapping/top-object-property variants removed the same 13 classes from the baseline set:

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

The 11 classes that remained under removal/no-logical-mapping/top-object-property variants were:

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

The `BFO_0000195` direct replacement and inverse-bridge-to-`BFO_0000195` variants removed none of the baseline unsatisfiable classes. Both remained at 24.

## Alternative-By-Alternative Assessment

### A. Remove `hasSystemProperty` Mapping Only

Temporary edit:

```ttl
# removed from temporary graph only
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

Result:

- HermiT unsats: 11
- Change vs baseline: -13

This reproduces the known reducer baseline from the prior explanation report. It improves HermiT behavior but removes the active OWL representation of the intended BFO relation.

### B. Annotation / No Logical Mapping

Temporary edit:

```text
Remove the logical subproperty mapping and add no replacement logical axiom.
```

Result:

- HermiT unsats: 11
- Change vs baseline: -13

This is graph-equivalent to removal for the HermiT test. It represents the idea that the mapping could be documented outside active OWL, but this diagnostic did not add annotations to repo files.

### C. `owl:topObjectProperty` Placeholder

Temporary edit:

```ttl
ssn-system:hasSystemProperty rdfs:subPropertyOf owl:topObjectProperty .
```

Result:

- HermiT unsats: 11
- Change vs baseline: -13

The placeholder behaves like removal. This is expected because `owl:topObjectProperty` adds no BFO dependence domain/range constraints. It is not a substantive BFO mapping.

### D. Direct Replacement With `BFO_0000195`

Temporary edit:

```ttl
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000195 .
```

Result:

- HermiT unsats: 24
- Change vs baseline: 0

This variant is directionally wrong under the current modeling rationale, because it asserts the source subject depends on the source object. It also did not improve HermiT behavior. This alternative should not be recommended from this diagnostic.

### E. Inverse Bridge To `BFO_0000195`

Temporary edit:

```ttl
ssn2bfo-test:systemPropertyOf
  a owl:ObjectProperty ;
  owl:inverseOf ssn-system:hasSystemProperty ;
  rdfs:subPropertyOf bfo:BFO_0000195 .
```

Result:

- HermiT unsats: 24
- Change vs baseline: 0

This was intended to model the same dependence direction by introducing a local inverse bridge property. It did not help HermiT. A likely reason is that the inverse bridge still brings the BFO dependence property constraints into the `hasSystemProperty` / inverse-`hasSystemProperty` source-restriction pattern.

This does not prove that a bridge-property design is impossible, but this direct OWL inverse bridge did not improve the merged HermiT profile.

### F. Rule-Only / No OWL Subproperty Mapping

Temporary edit:

```text
No active OWL subproperty mapping for hasSystemProperty.
Richer intended mapping would be handled outside OWL, for example by rule/COMS architecture.
```

Result:

- HermiT unsats: 11
- Change vs baseline: -13

This is graph-equivalent to removal in the HermiT test. Its practical distinction is architectural: it preserves the possibility of documenting or computing the intended conditional mapping outside active OWL.

No rule file was created in this branch.

### G. Weak Inverse Bridge Under `owl:topObjectProperty`

Temporary edit:

```ttl
ssn2bfo-test:systemPropertyApproximationOf
  a owl:ObjectProperty ;
  owl:inverseOf ssn-system:hasSystemProperty ;
  rdfs:subPropertyOf owl:topObjectProperty .
```

Result:

- HermiT unsats: 11
- Change vs baseline: -13

This weak bridge behaves like removal because it does not connect the source relation to BFO dependence constraints. It gives contrast against the `BFO_0000195` inverse bridge, but it is not a substantive BFO mapping.

### H. Disconnected Top Placeholder

Temporary edit:

```ttl
ssn2bfo-test:hasSystemPropertyApproximation
  a owl:ObjectProperty ;
  rdfs:subPropertyOf owl:topObjectProperty .
```

Result:

- HermiT unsats: 11
- Change vs baseline: -13

This is effectively a control variant. The placeholder is disconnected from `ssn-system:hasSystemProperty`, so the graph behaves like removal.

## Interpretation

### Does Any Alternative Improve Beyond Removal?

No. None of the tested temporary alternatives reduced the unsatisfiable-class set below the 11 classes observed when the active `hasSystemProperty` mapping is removed.

### Does The Inverse Bridge Help?

No. The inverse bridge to `BFO_0000195` produced the same 24 unsatisfiable classes as the baseline. This suggests that representing the intended dependence direction through an OWL inverse bridge still exposes the source `hasSystemProperty` pattern to the BFO dependence constraints that participate in the HermiT interaction.

### Does `owl:topObjectProperty` Behave Like Removal?

Yes. Both the direct `hasSystemProperty rdfs:subPropertyOf owl:topObjectProperty` placeholder and the weak inverse bridge under `owl:topObjectProperty` behaved like removal, with 11 unsatisfiable classes. This is useful diagnostically but not a substantive mapping.

### Does The Directionally Wrong `BFO_0000195` Mapping Behave Better Or Worse?

It behaves no better than the current baseline, remaining at 24 unsatisfiable classes. Because it is also directionally wrong under the current modeling rationale, this diagnostic gives no reason to pursue it.

## Recommendation

- Do not change repository mappings based on this diagnostic alone.
- If a future fix is pursued, prefer the smallest alternative that preserves modeling intent and improves HermiT behavior.
- Among tested alternatives, only no-logical-mapping / rule-only / top-object-property-placeholder variants improved HermiT behavior, and they all improved only to the same 11-class result as removal.
- The inverse bridge did not help in this form.
- A rule/COMS-compatible approach remains the most HermiT-friendly among these options because it avoids active OWL dependence propagation while preserving the intended mapping for external documentation or computation.
- Keep the ELK validation suite as the regression baseline while HermiT/full OWL DL cleanup remains a separate modeling/profile task.
