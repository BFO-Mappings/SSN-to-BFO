# `sosa:observes` Conservative Upper Mapping Decision

This note records the decision for the remaining `sosa:observes` mapping candidate.

No TTL or spreadsheet changes are made by this note.

## Spreadsheet mapping

The spreadsheet contains:

- `sosa:observes rdfs:domain sosa:Sensor`
- `sosa:observes rdfs:range ssn:Property`
- `sosa:observes rdfs:subPropertyOf bfo:has_participant`

The spreadsheet reasoning describes `sosa:observes` as a capability-level relation between a sensor and a property, and maps it to `bfo:has_participant` as a conservative upper mapping.

## Review

This mapping should not be implemented mechanically.

`sosa:observes` relates a sensor to a property it is capable of observing. `bfo:has_participant` is process-oriented. A direct subproperty assertion would therefore require accepting an indirect interpretation: the sensor and observed property participate in observation processes associated with the observing capability.

## Decision

Defer TTL implementation of:

- `sosa:observes rdfs:subPropertyOf bfo:has_participant`

until the project explicitly accepts the conservative-upper-mapping rationale.

## Audit treatment

The remaining `missing_in_ttl` issue for `sosa:observes` is retained as a known deferred modeling issue, not a mechanical omission.
