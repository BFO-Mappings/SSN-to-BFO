# `ssn:hasProperty` and `sosa:observes` Mapping Review

This note reviews two remaining object-property mapping candidates from the `missing_in_ttl` bucket.

No TTL or spreadsheet changes are made by this note.

## Current inspection

Neither `ssn:hasProperty` nor `sosa:observes` currently appears in `SSN2BFO.ttl`.

The spreadsheet contains mapping assertions for both rows.

## `ssn:hasProperty`

Spreadsheet `OWL Axiom`:

- `ssn:hasProperty rdfs:subPropertyOf bfo:bearer_of`
- `ssn:hasProperty rdfs:subPropertyOf bfo:has_occurrent_part`

Spreadsheet reasoning:

`ssn:hasProperty` must cover both:

- specifically dependent continuants, which inhere in continuants and are related through `bfo:bearer_of`; and
- process profiles, which are occurrent parts of processes and are related through `bfo:has_occurrent_part`.

Review finding:

This is a coherent dual mapping if the repository accepts the spreadsheet treatment of `ssn:Property` as covering both specifically dependent continuants and process profiles.

Recommended follow-up:

Implement both `ssn:hasProperty` subproperty assertions together in a narrow TTL-only PR. Do not implement only one side of the dual mapping.

## `sosa:observes`

Spreadsheet `OWL Axiom`:

- `sosa:observes rdfs:subPropertyOf bfo:has_participant`

Spreadsheet reasoning:

`sosa:observes` is described as a capability-level relation between a sensor and a property. The spreadsheet maps it to `bfo:has_participant` as a conservative upper mapping.

Review finding:

This mapping is more fragile than `ssn:hasProperty`.

`bfo:has_participant` is process-oriented, while `sosa:observes` relates a sensor to a property it is capable of observing. Treating this as a direct subproperty mapping may overstate the relation unless the project accepts the conservative-upper-mapping rationale.

Recommended follow-up:

Do not add `sosa:observes rdfs:subPropertyOf bfo:has_participant` mechanically. Record a separate modeling decision before any TTL implementation.

## Recommended implementation order

1. Create a TTL-only PR for the two `ssn:hasProperty` assertions.
2. Defer `sosa:observes` pending a separate modeling decision.
