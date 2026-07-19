# `sosa:observes` Mapping Decision

This note records the decision for the remaining `sosa:observes` mapping candidate.

No TTL or spreadsheet changes are made by this note.

## Spreadsheet mapping under review

The spreadsheet currently contains:

- `sosa:observes rdfs:domain sosa:Sensor`
- `sosa:observes rdfs:range ssn:Property`
- `sosa:observes rdfs:subPropertyOf bfo:has_participant`

The spreadsheet reasoning describes `sosa:observes` as a capability-level relation between a sensor and a property, and maps it to `bfo:has_participant` as a conservative upper mapping.

## Review

The `bfo:has_participant` mapping should not be accepted.

`sosa:observes` relates a sensor to the property it is capable of observing. It is therefore closer to the SSN/SOSA property-directed relation pattern than to a BFO process-participation relation.

`bfo:has_participant` is process-oriented. Treating `sosa:observes` as a direct subproperty of `bfo:has_participant` would overstate the mapping by treating a capability/property relation as if it were directly a process/participant relation.

## Decision

Do not implement:

- `sosa:observes rdfs:subPropertyOf bfo:has_participant`

Instead, preserve the SSN/SOSA-level relation:

- `sosa:observes rdfs:subPropertyOf ssn:forProperty`

## Implementation guidance

Implement this in a separate correction PR.

That correction should update the spreadsheet row for `sosa:observes` so the OWL axiom uses:

- `sosa:observes rdfs:subPropertyOf ssn:forProperty`

Then the TTL should be aligned with the corrected spreadsheet mapping.

Do not add the `bfo:has_participant` mapping.
