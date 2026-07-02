# Sampler `subClassOf` vs `equivalentClass` Review

This note reviews the remaining `sosa:Sampler` relation mismatch after the Sampler spreadsheet axiom was corrected to use the realized-in direction.

No TTL or spreadsheet changes are made by this note.

## Current audit status

The `sosa:Sampler` target expression is now aligned between the TTL and spreadsheet.

Remaining mismatch:

- TTL relation: `rdfs:subClassOf`
- Spreadsheet relation: `owl:equivalentClass`
- Target expression: aligned

This means the remaining question is relation strength only.

## Evidence reviewed

The current TTL maps `sosa:Sampler` as a subclass of a conjunction including:

- `bfo:MaterialEntity`;
- `bfo:bearer_of some (bfo:RealizableEntity and (BFO_0000054 some sosa:Sampling))`;
- `cco:agent_in some sosa:Sampling`.

The current spreadsheet maps `sosa:Sampler` to the same target expression, but uses `equivalentTo`.

The spreadsheet says `sosa:Sampler` is modeled analogously to `sosa:Sensor` and `sosa:Actuator`.

The `sosa:Actuator` spreadsheet row uses the same kind of material-entity / bearer-of-realizable / agent-in pattern, but its relation is `subClassOf`, not `equivalentTo`.

## Sensor note

The `sosa:Sensor` discrepancy should not be used as evidence for this Sampler decision.

The spreadsheet `sosa:Sensor` row targets an upcoming CCO version in which `cco:Sensor` is expected to have stronger semantics than the current local CCO import. The current TTL remains aligned to the current imported CCO version.

Accordingly, `sosa:Sensor` should be treated as a version-targeted deferred issue, not as evidence that the spreadsheet is wrong.

## Review finding

The Sampler spreadsheet row appears to be too strong as written.

The target expression provides necessary conditions for being a `sosa:Sampler`, but equivalence would also make those conditions sufficient for class membership. That stronger claim should not be applied mechanically unless the project explicitly accepts it as a definitional equivalence.

Given the analogous `sosa:Actuator` row remains `subClassOf`, and the TTL already uses `rdfs:subClassOf` for `sosa:Sampler`, the conservative reconciliation is to change the spreadsheet Sampler relation from `equivalentTo` to `subClassOf`.

## Recommended follow-up

Create a spreadsheet-only PR changing the `sosa:Sampler` `OWL Axiom` relation from:

`equivalentTo`

to:

`subClassOf`

while preserving the corrected target expression.

Do not edit `SSN2BFO.ttl` for this issue unless a separate modeling decision later accepts `sosa:Sampler` equivalence.
