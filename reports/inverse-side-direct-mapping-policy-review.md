# Inverse-Side Direct Mapping Policy Review

This note reviews the remaining TTL-only inverse-side direct mapping assertions.

No TTL or spreadsheet changes are made by this note.

## Current audit status

After ignoring schema/context predicates and documenting the sample representation property chains, the remaining `missing_in_spreadsheet` bucket contains:

- `sosa:Sensor`, already deferred as an upcoming-CCO version-target issue; and
- seven inverse-side direct mapping assertions.

This note concerns only the seven inverse-side direct mappings.

## Out of scope

`SOSA:Sensor` is not part of this policy decision.

The `sosa:Sensor` discrepancy is version-targeted: the spreadsheet maps to an upcoming CCO version, while the TTL remains aligned to the current imported CCO version.

## Inverse-side direct mappings reviewed

The TTL currently includes the following direct mappings on inverse-side SOSA/SSN properties:

- `sosa:isActedOnBy rdfs:subPropertyOf cco:is_affected_by`
- `sosa:isResultOf rdfs:subPropertyOf cco:is_output_of`
- `sosa:madeByActuator rdfs:subPropertyOf cco:has_agent`
- `sosa:madeObservation rdfs:subPropertyOf cco:agent_in`
- `sosa:madeSampling rdfs:subPropertyOf cco:agent_in`
- `ssn:hasDeployment rdfs:subPropertyOf bfo:participates_in`
- `ssn:inDeployment rdfs:subPropertyOf bfo:participates_in`

## Spreadsheet basis

Inspection of the spreadsheet rows confirmed that all seven TTL-only assertions are inverse-derived from mappings already represented in the spreadsheet:

- `sosa:isActedOnBy` is inverse-derived from `sosa:actsOnProperty rdfs:subPropertyOf cco:affects`.
- `sosa:isResultOf` is inverse-derived from `sosa:hasResult rdfs:subPropertyOf cco:has_output`.
- `sosa:madeByActuator` is inverse-derived from `sosa:madeActuation rdfs:subPropertyOf cco:agent_in`.
- `sosa:madeObservation` is inverse-derived from `sosa:madeBySensor rdfs:subPropertyOf cco:has_agent`.
- `sosa:madeSampling` is inverse-derived from `sosa:madeBySampler rdfs:subPropertyOf cco:has_agent`.
- `ssn:hasDeployment` is inverse-derived from `ssn:deployedSystem rdfs:subPropertyOf bfo:has_participant`.
- `ssn:inDeployment` is inverse-derived from `ssn:deployedOnPlatform rdfs:subPropertyOf bfo:has_participant`.

## Decision

Keep the seven inverse-side direct mappings in `SSN2BFO.ttl`.

These assertions are not arbitrary stale TTL content. They are materialized inverse-side consequences of spreadsheet mappings plus inverse-property relationships.

Because they are actual BFO/CCO source-to-target mapping assertions, they should be documented in the spreadsheet `OWL Axiom` cells rather than left as undocumented TTL-only assertions.

## Recommended follow-up

Create spreadsheet-only PRs documenting the seven materialized inverse-side direct mappings.

Do not edit `SSN2BFO.ttl` for this issue.

Do not mix this policy decision with the deferred `sosa:Sensor` upcoming-CCO issue.
