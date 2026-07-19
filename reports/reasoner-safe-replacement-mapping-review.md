# Reasoner-Safe Replacement Mapping Review

## Scope

This review covers three deferred mappings:

- `ssn:hasProperty`
- `ssn-system:BatteryLifetime`
- `ssn-system:MeasurementRange`

This is a review-only note. It does not change `SSN2BFO.ttl`, the source spreadsheet, imports, generated/release artifacts, or existing reports. The goal is to identify whether there are narrower, reasoner-safer replacement candidates that are supported by the inspected source text and local BFO/CCO terms.

## Files Inspected

- `SSN2BFO.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `imports/cco.ttl`
- `reports/reasoner-diagnostic-report.md`
- `reports/reasoner-unsafe-system-mapping-deferral.md`
- `reports/mapping-consistency-audit.md`
- `reports/remaining-audit-disposition.md`

## Evidence Summary

The current `SSN2BFO.ttl` contains no active mapping block for `ssn:hasProperty`, `ssn-system:BatteryLifetime`, or `ssn-system:MeasurementRange`.

The current spreadsheet rows remain present, but the relevant `OWL Axiom` cells are cleared:

| Term | Sheet | Row | Current spreadsheet status |
| --- | --- | ---: | --- |
| `ssn:hasProperty` | Common OPs | 11 | No active OWL axiom; reasoning cell records ELK deferral. |
| `ssn-system:BatteryLifetime` | System Capability | 4 | No active OWL axiom; reasoning cell records ELK deferral. |
| `ssn-system:MeasurementRange` | System Capability | 18 | No active OWL axiom; reasoning cell records ELK deferral. |

The current mapping audit lists the same three rows under skipped or partially parsed rows with "no parsed expected assertions":

| Term | Audit evidence |
| --- | --- |
| `ssn:hasProperty` | `reports/mapping-consistency-audit.md`, skipped row for Common OPs row 11. |
| `ssn-system:BatteryLifetime` | `reports/mapping-consistency-audit.md`, skipped row for System Capability row 4. |
| `ssn-system:MeasurementRange` | `reports/mapping-consistency-audit.md`, skipped row for System Capability row 18. |

The deferral reports state that ELK diagnostics found the prior mappings to be mapping-induced or mapping-amplified sources of unsatisfiability. After deferring them, ELK produced a reasoned output with zero entities typed `owl:Nothing`. HermiT/full OWL DL cleanup remains explicitly out of scope.

## Review Criteria

Candidate forms are classified as one of:

- annotation-only
- `rdfs:subClassOf` named class
- `rdfs:subPropertyOf` named property
- OWL restriction
- property chain
- no active mapping recommended

Any candidate that changes active logical content should be tested under the same ELK merged-profile workflow before it is accepted. Annotation-only candidates are not expected to affect ELK satisfiability, but a normal validation run is still prudent if annotations are added to the mapping file.

## Summary Recommendations

| Term | Conservative recommendation |
| --- | --- |
| `ssn:hasProperty` | No active replacement yet. Keep the deferral until a narrower property-level review can separate continuant property cases from occurrent/process-profile cases. |
| `ssn-system:BatteryLifetime` | No active replacement yet. The source term is an SSN Systems `SurvivalProperty`; do not reintroduce the prior function/restriction block without a separate ELK-tested modeling review. |
| `ssn-system:MeasurementRange` | No active replacement yet. The source term is an SSN Systems `SystemProperty` with sensor-specific restrictions; do not map it directly to a CCO/BFO function or information-content class without separate justification and ELK testing. |

## `ssn:hasProperty`

### Current Status

- Current TTL: no active mapping in `SSN2BFO.ttl`.
- Spreadsheet: Common OPs row 11 is present, with the `OWL Axiom` cell cleared.
- Audit: skipped as "no parsed expected assertions".
- Source ontology evidence: `imports/ssn.ttl` declares `ssn:hasProperty` as an `owl:ObjectProperty`, inverse of `ssn:isPropertyOf`, with definition "Relation between an entity and a Property of that entity." The SSN import also uses `ssn:hasProperty` in `sosa:FeatureOfInterest` restrictions requiring `ssn:Property` values.
- SSN Systems evidence: several system properties are declared as subproperties of `ssn:hasProperty`, including `hasOperatingRange`, `hasSurvivalRange`, `hasSystemCapability`, and `hasSystemProperty`.

### Previous Mapping Deferred

The previous active mapping was a dual mapping to BFO relations:

- `bfo:BFO_0000196` / "bearer of"
- `bfo:BFO_0000117` / "has occurrent part"

The spreadsheet reasoning cell describes the deferred intent as a relation where the SSN property either inheres in an entity as a specifically dependent continuant or is an occurrent part of a relevant process as a process profile.

### Why The Previous Mapping Was Unsafe

The deferral report states that the prior dual mapping made `ssn:hasProperty` unsatisfiable under ELK. The unsafe pattern was placing one broad SOSA/SSN property under two BFO relations with different domain/range behavior:

- `bfo:BFO_0000196` has domain independent continuant and range specifically dependent continuant.
- `bfo:BFO_0000117` has domain and range occurrent.

The SSN source definition is intentionally broad: "an entity" to "a Property". The SSN Systems subproperty hierarchy makes that breadth operationally important. A single active subproperty assertion to either BFO relation, or a dual assertion to both, overstates the SSN property.

### Ranked Candidate Options

| Rank | Candidate | Form | Support | ELK before acceptance? | Risk |
| ---: | --- | --- | --- | --- | --- |
| 1 | Leave `ssn:hasProperty` without an active BFO/CCO mapping. | no active mapping recommended | Supported by the current ELK-clean baseline and cleared spreadsheet axiom. | Not applicable for no new axiom. | Safest; preserves current reasoner-safe state. |
| 2 | Add only a review/documentation annotation describing why the active mapping remains deferred. | annotation-only | Supported by current spreadsheet reasoning and deferral reports. | Not expected to affect ELK, but run normal validation if added to TTL. | Low; does not assert a logical alignment. |
| 3 | Test a single `rdfs:subPropertyOf bfo:BFO_0000196` candidate. | `rdfs:subPropertyOf` named property | Partially aligns only continuant-to-dependent-continuant readings. | Yes, mandatory. | High; excludes occurrent/process-profile readings and resembles part of the unsafe prior mapping. Not recommended now. |
| 4 | Test a single `rdfs:subPropertyOf bfo:BFO_0000117` candidate. | `rdfs:subPropertyOf` named property | Partially aligns only occurrent-part readings. | Yes, mandatory. | High; excludes continuant/property readings and resembles part of the unsafe prior mapping. Not recommended now. |
| 5 | Introduce a split mapping or property-chain design to distinguish continuant and occurrent cases. | property chain | Would require new modeling beyond the inspected source rows. | Yes, mandatory. | Highest; broad redesign and out of scope for this review. |

### Conservative Recommendation

Do not add an active replacement mapping for `ssn:hasProperty` yet. The only reasoner-safe near-term action would be annotation-only documentation of the deferral. Any logical replacement should wait for a dedicated property modeling review and ELK testing.

## `ssn-system:BatteryLifetime`

### Current Status

- Current TTL: no active mapping in `SSN2BFO.ttl`.
- Spreadsheet: System Capability row 4 is present, with the `OWL Axiom` cell cleared.
- Audit: skipped as "no parsed expected assertions".
- Source ontology evidence: `imports/ssn-systems.ttl` declares `ssn-system:BatteryLifetime` as a subclass of `ssn-system:SurvivalProperty`, with definition "Total useful life of a System's battery in the specified Conditions."
- Nearby source hierarchy: `ssn-system:SurvivalProperty` is a subclass of `ssn:Property`, and describes an identifiable characteristic representing the extent of a system's useful life under specified conditions.

### Previous Mapping Deferred

The exact prior TTL class expression is not present in the current inspected files. The recoverable spreadsheet description says the prior intended mapping treated every `ssn-system:BatteryLifetime` as a BFO function with a realization involving:

- a stasis of artifact operationality;
- an occurrent part involving power;
- a process realizing an affordance;
- prescription by a CCO artifact design.

The deferral report summarizes this as a prior `BatteryLifetime` class mapping block.

### Why The Previous Mapping Was Unsafe

The diagnostic and deferral reports state that the prior `BatteryLifetime` class mapping block made `ssn-system:BatteryLifetime` unsatisfiable under ELK when combined with SSN Systems, CCO, and BFO constraints. The current source definition supports a survival property about useful battery life under conditions, but the deferred mapping used a large function/restriction pattern. That pattern was stronger than the current source row can safely support without additional modeling review.

### Ranked Candidate Options

| Rank | Candidate | Form | Support | ELK before acceptance? | Risk |
| ---: | --- | --- | --- | --- | --- |
| 1 | Leave `ssn-system:BatteryLifetime` without an active BFO/CCO mapping. | no active mapping recommended | Supported by the current ELK-clean baseline and cleared spreadsheet axiom. | Not applicable for no new axiom. | Safest; preserves current reasoner-safe state. |
| 2 | Add only a review/documentation annotation describing the source definition and deferral. | annotation-only | Supported by the spreadsheet reasoning cell and deferral reports. | Not expected to affect ELK, but run normal validation if added to TTL. | Low; does not assert class placement. |
| 3 | Evaluate a simple named superclass such as BFO `function` or CCO `Artifact Function`. | `rdfs:subClassOf` named class | The spreadsheet's BFO definition uses function language, and local CCO includes `cco:ont00000323` / "Artifact Function". | Yes, mandatory. | Medium to high; the SSN Systems source class is a `SurvivalProperty`, so this may overstate the term as a function rather than a property about battery life. |
| 4 | Evaluate a more specific power-related CCO function such as "Electrical Power Storage Artifact Function". | `rdfs:subClassOf` named class | Local CCO contains `cco:ont00001092` / "Electrical Power Storage Artifact Function". | Yes, mandatory. | High; the source term is battery lifetime, not the storage function itself. This is not supported as an automatic replacement. |
| 5 | Reintroduce the prior large class expression. | OWL restriction | Recoverable only as a natural-language description in the spreadsheet and deferral reports. | Yes, mandatory. | Highest; this is the pattern already reported unsafe under ELK. Do not reintroduce as-is. |

### Conservative Recommendation

Do not add an active replacement mapping for `ssn-system:BatteryLifetime` yet. The source evidence supports its current SSN Systems placement as a `SurvivalProperty`, but not a reasoner-safe BFO/CCO replacement in `SSN2BFO.ttl`. If a future candidate is considered, start with a single named superclass candidate and test it under ELK before accepting it.

## `ssn-system:MeasurementRange`

### Current Status

- Current TTL: no active mapping in `SSN2BFO.ttl`.
- Spreadsheet: System Capability row 18 is present, with the `OWL Axiom` cell cleared.
- Audit: skipped as "no parsed expected assertions".
- Source ontology evidence: `imports/ssn-systems.ttl` declares `ssn-system:MeasurementRange` as a subclass of `ssn-system:SystemProperty`, with restrictions tying inverse `hasSystemProperty` and inverse `hasSystemCapability` use to `sosa:Sensor`.
- Source definition: "The set of values that the Sensor can return as the Result of an Observation under the defined Conditions."
- Nearby source hierarchy: `ssn-system:SystemProperty` is a subclass of `ssn:Property`, and describes an identifiable and observable characteristic of a system's ability to operate its primary purpose.

### Previous Mapping Deferred

The exact prior TTL class expression is not present in the current inspected files. The recoverable spreadsheet description says the prior intended mapping treated every `ssn-system:MeasurementRange` as a BFO function with a realization that is:

- a `sosa:Observation`;
- affected by a `ssn:Stimulus`;
- prescribed by a CCO artifact function specification.

The deferral report summarizes this as a prior `MeasurementRange` class mapping block.

### Why The Previous Mapping Was Unsafe

The diagnostic and deferral reports state that the prior `MeasurementRange` class mapping block made `ssn-system:MeasurementRange` unsatisfiable under ELK when combined with SSN Systems, CCO, and BFO constraints. The source definition speaks about a set of values returned by a sensor as observation results under conditions. Mapping it directly to a function or to a large observation/stimulus/specification restriction risks conflating a system property/range specification with the function or process that realizes measurement.

### Ranked Candidate Options

| Rank | Candidate | Form | Support | ELK before acceptance? | Risk |
| ---: | --- | --- | --- | --- | --- |
| 1 | Leave `ssn-system:MeasurementRange` without an active BFO/CCO mapping. | no active mapping recommended | Supported by the current ELK-clean baseline and cleared spreadsheet axiom. | Not applicable for no new axiom. | Safest; preserves current reasoner-safe state. |
| 2 | Add only a review/documentation annotation describing the source definition and deferral. | annotation-only | Supported by the spreadsheet reasoning cell and deferral reports. | Not expected to affect ELK, but run normal validation if added to TTL. | Low; does not assert class placement. |
| 3 | Evaluate a simple named superclass such as BFO `function`, CCO `Artifact Function`, or CCO `Measurement Artifact Function`. | `rdfs:subClassOf` named class | The spreadsheet's BFO definition uses function language; local CCO contains `cco:ont00000323` / "Artifact Function" and `cco:ont00001100` / "Measurement Artifact Function". | Yes, mandatory. | Medium to high; the SSN Systems source term is a `SystemProperty` describing a range of returnable values, not necessarily the measurement function itself. |
| 4 | Evaluate an information-content interpretation such as a directive/specification class. | `rdfs:subClassOf` named class | Local CCO includes `cco:ont00000965` / "Directive Information Content Entity" and `cco:ont00000118` / "Artifact Function Specification". | Yes, mandatory. | High; the source text does not state that the class is an information content entity. Not recommended without explicit modeling evidence. |
| 5 | Reintroduce the prior observation/stimulus/specification class expression. | OWL restriction | Recoverable only as a natural-language description in the spreadsheet and deferral reports. | Yes, mandatory. | Highest; this is the pattern already reported unsafe under ELK. Do not reintroduce as-is. |

### Conservative Recommendation

Do not add an active replacement mapping for `ssn-system:MeasurementRange` yet. A future candidate should first decide whether the term is to be aligned as a system property, a function, or an information specification. Any non-annotation candidate must be tested under ELK before acceptance.

## ELK Testing Recommendation

Before accepting any active logical replacement for these deferred terms, run the same no-imports merged-profile ELK test used to establish the current baseline. This is mandatory for:

- any `rdfs:subClassOf` named class candidate;
- any `rdfs:subPropertyOf` named property candidate;
- any OWL restriction;
- any property chain.

Annotation-only review notes are not expected to change ELK satisfiability, but validation should still be run if annotations are added to `SSN2BFO.ttl`.

## Final Disposition

No active replacement mapping is recommended for any of the three deferred terms in this review. The safest next state is to keep the current deferral, preserve the ELK-clean baseline, and open a narrower modeling review only when there is explicit source-backed justification for a testable candidate.
