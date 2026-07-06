# HermiT Diagnostic: `ssn:hasProperty` Domain/Range Architecture

## Scope

This report tests a proposed future architecture for `ssn:hasProperty` and selected SSN Systems subproperties in temporary HermiT graphs only.

No repository ontology mappings, spreadsheets, imports, source examples, generated/release artifacts, or existing reports were modified. All temporary graphs and ROBOT outputs were written under:

`/tmp/ssn-to-bfo-hermit-hasProperty-domain-range-architecture`

The primary question is whether selected SSN Systems property relations can be left only under `ssn:hasProperty`, with broad `ssn:hasProperty` domain/range constraints, while finer-grained BFO relation semantics are handled outside active OWL through rule/COMS architecture.

## Proposed Architecture Being Tested

The proposed architecture is:

1. Keep generic `ssn:hasProperty` unmapped to a concrete BFO relation.
2. Potentially add broad OWL 2 DL domain/range constraints to `ssn:hasProperty`:
   - domain: `continuant OR occurrent`
   - range: `specifically dependent continuant OR Process Profile`
3. Remove selected direct BFO dependence subproperty mappings for:
   - `ssn-system:hasOperatingProperty`
   - `ssn-system:hasSurvivalProperty`
   - `ssn-system:hasSystemProperty`
4. Preserve the source/import `rdfs:subPropertyOf ssn:hasProperty` hierarchy.
5. Represent the more specific BFO relation semantics through rule/COMS architecture rather than active OWL `rdfs:subPropertyOf` mappings.

The selected active mappings tested for removal were:

```ttl
ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

The broad temporary domain/range pattern tested was:

```ttl
ssn:hasProperty
  rdfs:domain [
    a owl:Class ;
    owl:unionOf ( bfo:BFO_0000002 bfo:BFO_0000003 )
  ] ;
  rdfs:range [
    a owl:Class ;
    owl:unionOf ( bfo:BFO_0000020 bfo:BFO_0000144 )
  ] .
```

## Verified BFO Identifiers And Labels

The following labels were verified locally in `imports/cco.ttl` before running variants:

| IRI | Local label |
| --- | --- |
| `bfo:BFO_0000002` | continuant |
| `bfo:BFO_0000003` | occurrent |
| `bfo:BFO_0000020` | specifically dependent continuant |
| `bfo:BFO_0000144` | Process Profile |
| `bfo:BFO_0000194` | specifically depended on by |

## Baseline Setup

Every variant was built from an M2-style temporary graph that merged:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Temporary cleanup applied to every variant:

- removed all `owl:imports` triples;
- removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- removed `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Each variant used this command pattern:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

- ROBOT: `ROBOT version 1.9.7`
- Java: `java version "22.0.2" 2024-07-16`

## Variant Summary Table

| Variant | Temporary edit | Input graph | Return code | Reasoned output | Unsat count | Delta vs baseline | Delta vs `hasSystemProperty` removal | Sample blocker |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| A. M2 baseline | Current source/import plus current `SSN2BFO.ttl` mappings. | `/tmp/ssn-to-bfo-hermit-hasProperty-domain-range-architecture/A_M2_baseline.ttl` | 1 | no | 24 | 0 | +13 | no |
| B. Remove `hasSystemProperty` only | Remove only `hasSystemProperty -> BFO_0000194`. | `/tmp/ssn-to-bfo-hermit-hasProperty-domain-range-architecture/B_remove_hasSystemProperty_only.ttl` | 1 | no | 11 | -13 | 0 | no |
| C. Remove selected BFO dependence mappings | Remove `hasOperatingProperty`, `hasSurvivalProperty`, and `hasSystemProperty` direct `BFO_0000194` mappings. No `ssn:hasProperty` domain/range added. | `/tmp/ssn-to-bfo-hermit-hasProperty-domain-range-architecture/C_remove_selected_BFO_dependence_mappings.ttl` | 1 | no | 8 | -16 | -3 | no |
| D. Selected removed plus `hasProperty` domain/range | Same as C, plus broad disjunctive domain/range on `ssn:hasProperty`. | `/tmp/ssn-to-bfo-hermit-hasProperty-domain-range-architecture/D_selected_removed_plus_hasProperty_domain_range.ttl` | 1 | no | 8 | -16 | -3 | no |
| E. Domain/range with current selected mappings | Keep current selected `BFO_0000194` mappings active and add broad disjunctive domain/range on `ssn:hasProperty`. | `/tmp/ssn-to-bfo-hermit-hasProperty-domain-range-architecture/E_domain_range_with_current_selected_mappings.ttl` | 1 | no | 24 | 0 | +13 | no |
| F. All SSN Systems property mappings removed plus domain/range | Remove all active SSN Systems property mappings and add broad disjunctive domain/range on `ssn:hasProperty`. | `/tmp/ssn-to-bfo-hermit-hasProperty-domain-range-architecture/F_all_system_property_mappings_removed_plus_domain_range.ttl` | 1 | no | 8 | -16 | -3 | no |

No tested variant was HermiT-clean. No tested variant produced a reasoned output, so `owl:Nothing` counts were not available. No tested variant reintroduced the `sosa:hasSample` / `sosa:isSampleOf` sample simplicity blocker.

## Unsat Set Comparison

The M2 baseline reported 24 unsatisfiable classes:

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

Removing only `hasSystemProperty -> BFO_0000194` left 11 unsatisfiable classes:

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

Removing all three selected BFO dependence mappings left 8 unsatisfiable classes:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

The primary proposed architecture variant, with the three selected mappings removed and broad `ssn:hasProperty` domain/range added, left the same 8 classes:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- `ssn-system:BatteryLifetime`
- `ssn-system:SurvivalProperty`
- `ssn-system:SystemLifetime`

Adding the broad `ssn:hasProperty` domain/range while keeping the current selected `BFO_0000194` mappings active left all 24 baseline unsatisfiable classes.

The optional variant removing all active SSN Systems property mappings plus adding broad `ssn:hasProperty` domain/range also left the same 8 classes. In this branch, the additional removed SSN Systems property mappings beyond the three selected ones did not reduce the set further.

## Architecture Assessment

### Does Removing Selected BFO Dependence Subproperty Mappings Help?

Yes. Removing the three selected direct `BFO_0000194` mappings reduced the HermiT unsatisfiable-class count from 24 to 8.

This improves beyond removing only `hasSystemProperty`, which reduced the count from 24 to 11. The additional reduction removed:

- `ssn-system:MaintenanceSchedule`
- `ssn-system:OperatingPowerRange`
- `ssn-system:OperatingProperty`

Those classes are consistent with the additional temporary removal of `hasOperatingProperty -> BFO_0000194` and `hasSurvivalProperty -> BFO_0000194`, though this is still a reducer diagnostic, not a formal explanation.

### Does Adding Broad Domain/Range On `ssn:hasProperty` Help, Hurt, Or Have No Effect?

In these HermiT tests, adding the broad disjunctive domain/range on `ssn:hasProperty` had no observable effect on the unsatisfiable-class count.

- With the selected BFO dependence mappings removed, adding the broad domain/range remained at 8 unsats.
- With the selected BFO dependence mappings still active, adding the broad domain/range remained at 24 unsats.
- With all active SSN Systems property mappings removed, adding the broad domain/range remained at 8 unsats.

This means the broad domain/range approximation did not repair the HermiT interaction caused by the current direct BFO dependence mappings. It also did not worsen the tested full OWL profile under HermiT.

### Does Keeping Current `BFO_0000194` Mappings While Adding Broad Domain/Range Help?

No. Variant E remained at 24 unsatisfiable classes. The broad `ssn:hasProperty` domain/range constraints did not counteract the interaction from the selected direct BFO dependence subproperty mappings.

### Is The Rule/COMS-Only Path Still The Most HermiT-Friendly Option?

For the selected relations tested here, yes. The most HermiT-friendly active-OWL shape tested was to remove the direct BFO dependence subproperty mappings and leave finer-grained relation semantics for a rule/COMS architecture.

The broad `ssn:hasProperty` domain/range restrictions appear neutral in this diagnostic. They did not improve beyond removal/no-active-BFO-subproperty, and they do not validate the intended finer-grained BFO semantics by themselves.

## Modeling Cautions

- Domain/range constraints on `ssn:hasProperty` can propagate to subproperties of `ssn:hasProperty`, including SSN Systems subproperties. This diagnostic tested HermiT behavior but does not prove the propagated domain/range is semantically appropriate in every case.
- The tested domain/range pattern uses `owl:unionOf`, which is outside OWL EL. This diagnostic is HermiT/full OWL focused, not an ELK-profile recommendation.
- Broad domain/range constraints do not distinguish the intended finer-grained BFO relations. They only constrain the general subject/object class space.
- This report does not validate rule/COMS semantics. It only tests whether an active OWL profile shaped for future rule/COMS treatment changes the HermiT unsatisfiable-class set.
- None of the tested variants was HermiT-clean, so this architecture does not solve all full OWL DL issues in the merged profile.

## Recommendation

- Do not make repository ontology changes in this diagnostic branch.
- A future fix branch may reasonably consider deferring the selected direct BFO dependence mappings for:
  - `ssn-system:hasOperatingProperty`
  - `ssn-system:hasSurvivalProperty`
  - `ssn-system:hasSystemProperty`
- The future fix should preserve source/import `rdfs:subPropertyOf ssn:hasProperty` and document the intended finer-grained mappings through rule/COMS architecture rather than active OWL `rdfs:subPropertyOf` assertions.
- The broad `ssn:hasProperty` domain/range restrictions should not be treated as necessary for HermiT improvement, because they were neutral in this diagnostic.
- If the broad domain/range architecture is pursued, it should be reviewed as a separate modeling decision, with explicit attention to propagation across all `ssn:hasProperty` subproperties and the fact that `owl:unionOf` is not ELK-friendly.
- Keep the current ELK validation suite as the regression baseline while HermiT/full OWL cleanup proceeds in narrow branches.
