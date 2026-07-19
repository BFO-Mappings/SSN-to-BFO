# Sampler Equivalent-Class Decision

This note supersedes the conservative recommendation in the Sampler relation-strength review.

No TTL or spreadsheet changes are made by this note.

## Decision

Keep the spreadsheet `sosa:Sampler` mapping as `equivalentTo`.

The intended modeling decision is that the corrected Sampler target expression gives necessary and sufficient conditions for `sosa:Sampler`:

- `bfo:MaterialEntity`;
- `bfo:bearer_of some (bfo:RealizableEntity and (BFO_0000054 some sosa:Sampling))`;
- `cco:agent_in some sosa:Sampling`.

## Consequence

The remaining Sampler audit issue should be resolved by updating `SSN2BFO.ttl` from `rdfs:subClassOf` to `owl:equivalentClass`, preserving the corrected realized-in target expression.

The spreadsheet should not be changed from `equivalentTo` to `subClassOf`.
