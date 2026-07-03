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

These appear to be inverse-side consequences of canonical forward-side mappings plus inverse-property relationships.

## Policy question

Should `SSN2BFO.ttl` include materialized inverse-side direct mappings that are not explicitly asserted in the spreadsheet `OWL Axiom` cells?

## Review finding

These assertions should not be treated as accidental stale TTL content merely because they are absent from the spreadsheet.

They are plausible materialized inverse-side mappings. However, because they are actual BFO/CCO source-to-target mapping assertions, they should not remain undocumented if the spreadsheet is the governing mapping source.

## Decision

Defer mechanical TTL removal.

The repository should make an explicit policy choice:

1. **Document materialized inverse-side mappings**  
   Keep these TTL assertions and add them to the spreadsheet `OWL Axiom` cells, making clear that the TTL intentionally materializes inverse-side direct mappings.

2. **Canonical-only TTL policy**  
   Remove these TTL assertions and keep only the spreadsheet-canonical forward-side mappings and inverse/property metadata.

## Recommended follow-up

Recommended next step: choose whether the repository wants a materialized inverse-side mapping policy.

If yes, create spreadsheet-only PRs documenting the seven TTL assertions.

If no, create TTL-removal PRs removing the seven inverse-side direct mappings.

Do not mix this policy decision with the deferred `sosa:Sensor` upcoming-CCO issue.
