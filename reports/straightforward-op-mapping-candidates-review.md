# Straightforward Object-Property Mapping Candidates Review

This note reviews the five remaining direct object-property mappings classified as straightforward candidates in the remaining `missing_in_ttl` review.

No TTL or spreadsheet changes are made by this note.

## Current candidates

The spreadsheet currently contains the following mapping assertions that are not yet present in `SSN2BFO.ttl`:

- `ssn:hasProperty rdfs:subPropertyOf bfo:bearer_of`
- `ssn:hasProperty rdfs:subPropertyOf bfo:has_occurrent_part`
- `ssn:hasSubSystem rdfs:subPropertyOf bfo:has_continuant_part`
- `sosa:observes rdfs:subPropertyOf bfo:has_participant`
- `sosa:usedProcedure rdfs:subPropertyOf cco:prescribed_by`

## Row-level review

### `ssn:hasProperty`

Spreadsheet reasoning:

`ssn:hasProperty` must cover both specifically dependent continuants and process profiles. The spreadsheet maps it to both:

- `bfo:bearer_of`, for specifically dependent continuants inhering in continuants; and
- `bfo:has_occurrent_part`, for process profiles that are occurrent parts of processes.

Review finding:

This is a substantive dual mapping. It should be implemented only if the repository accepts `ssn:Property` as covering both continuant-dependent and process-profile cases.

### `ssn:hasSubSystem`

Spreadsheet reasoning:

Subsystems are structural components of larger systems, and the spreadsheet maps `ssn:hasSubSystem` to `bfo:has_continuant_part`.

Review finding:

This appears to be a straightforward TTL implementation candidate.

### `sosa:observes`

Spreadsheet reasoning:

`sosa:observes` is a capability-level relation between a sensor and a property. The spreadsheet maps it to `bfo:has_participant` as a conservative upper mapping.

Review finding:

This mapping should be handled with care. Although the spreadsheet explicitly records it, `bfo:has_participant` is process-oriented, while `sosa:observes` relates a sensor to a property it is capable of observing. This should not be applied mechanically without accepting the spreadsheet’s conservative-upper-mapping rationale.

### `sosa:usedProcedure`

Spreadsheet reasoning:

Using a procedure is operationally being carried out according to its prescriptions. The spreadsheet maps `sosa:usedProcedure` to `cco:prescribed_by`.

Review finding:

This appears to be a straightforward TTL implementation candidate.

## Recommended implementation sequence

1. Implement `ssn:hasSubSystem rdfs:subPropertyOf bfo:has_continuant_part`.
2. Implement `sosa:usedProcedure rdfs:subPropertyOf cco:prescribed_by`.
3. Review `ssn:hasProperty` as a dual mapping before applying both subproperty assertions.
4. Review `sosa:observes` carefully before applying the `bfo:has_participant` upper mapping.
