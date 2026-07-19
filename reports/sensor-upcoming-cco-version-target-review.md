# Sensor Upcoming-CCO Version Target Review

This note records the status of the remaining `sosa:Sensor` discrepancy between `SSN2BFO.ttl` and `Current_SOSA-SSN to BFO-CCO.xlsx`.

No TTL or spreadsheet changes are made by this note.

## Current audit pattern

The spreadsheet currently maps `sosa:Sensor` as:

`equivalentTo cco:Sensor`

The current TTL retains a more explicit current-CCO-compatible mapping:

`sosa:Sensor rdfs:subClassOf ...`

with restrictions including:

- `bfo:MaterialEntity`;
- `bfo:bearer_of some (bfo:RealizableEntity and (BFO_0000054 some sosa:Observation))`;
- `cco:agent_in some sosa:Observation`.

## Version-targeted interpretation

This discrepancy is intentional or at least expected.

The spreadsheet is targeting an upcoming version of CCO in which `cco:Sensor` is expected to have stronger semantics. The current TTL remains aligned with the currently imported CCO version in this repository.

Accordingly, the `sosa:Sensor` audit issue should not be treated as evidence that either file is simply wrong.

## Decision

Defer the `sosa:Sensor` TTL update until the repository imports the relevant upcoming CCO version or creates a separate future-CCO / next-version mapping track.

Do not weaken the spreadsheet row merely to match the current TTL.

Do not update the TTL to `equivalentTo cco:Sensor` while the repo still imports the current CCO version unless an explicit project decision authorizes that forward-looking mapping.

## Recommended follow-up

When the upcoming CCO version is available in the repo, revisit the `sosa:Sensor` row and determine whether the TTL should be updated from the current explicit subclass expression to the spreadsheet’s `equivalentTo cco:Sensor` mapping.
