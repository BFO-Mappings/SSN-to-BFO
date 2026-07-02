# Remaining TTL-Only Assertions Review

This note classifies the remaining `missing_in_spreadsheet` assertions after the Sampler and feature-of-interest cleanup sequence.

No TTL or spreadsheet changes are made by this note.

## Current audit status

The current audit reports:

- `missing_in_spreadsheet`: 10
- `missing_in_ttl`: 60
- `relation_mismatch`: 0
- `target_mismatch`: 0

The remaining `missing_in_spreadsheet` rows are TTL assertions that are not currently represented in the spreadsheet `OWL Axiom` cells.

## Classification

### Deferred / version-targeted

- `sosa:Sensor`
  - TTL: `rdfs:subClassOf` explicit current-CCO-compatible Sensor pattern.
  - Spreadsheet: `equivalentTo cco:Sensor`.
  - Decision: defer. This issue is already documented as targeting an upcoming CCO version. Do not resolve this against the current imported CCO.

### Sample representation property chains

- `sosa:hasSample`
  - TTL: `owl:propertyChainAxiom`
  - Target summary: `bfo:BFO_0000084; cco:ont00001873`

- `sosa:isSampleOf`
  - TTL: `owl:propertyChainAxiom`
  - Target summary: `bfo:BFO_0000101; cco:ont00001938`

Decision: defer for sample-as-representation modeling review. These should not be mechanically removed or documented until the intended sample representation model is settled.

### Inverse-side direct mappings

The following TTL assertions are direct mappings on inverse-side SOSA/SSN properties, while the spreadsheet generally records inverse-property axioms or canonical forward-side mappings:

- `sosa:isActedOnBy rdfs:subPropertyOf cco:is_affected_by`
- `sosa:isResultOf rdfs:subPropertyOf cco:is_output_of`
- `sosa:madeByActuator rdfs:subPropertyOf cco:has_agent`
- `sosa:madeObservation rdfs:subPropertyOf cco:agent_in`
- `sosa:madeSampling rdfs:subPropertyOf cco:agent_in`
- `ssn:hasDeployment rdfs:subPropertyOf bfo:participates_in`
- `ssn:inDeployment rdfs:subPropertyOf bfo:participates_in`

Decision: defer pending a repository policy decision.

The policy question is whether `SSN2BFO.ttl` should include inverse-derived direct mapping assertions in addition to the spreadsheet's canonical asserted axioms.

## Recommended next decisions

Do not mechanically apply all remaining `missing_in_spreadsheet` rows.

Recommended sequence:

1. Leave `sosa:Sensor` deferred until the relevant upcoming CCO version or next-version mapping track is available.
2. Review the sample representation property chains separately.
3. Decide whether inverse-side direct mappings are allowed in the TTL when they are derivable from spreadsheet inverse axioms plus forward-side mappings.
4. Only after that policy decision, either:
   - document inverse-derived mappings in the spreadsheet; or
   - remove inverse-derived direct mappings from the TTL.
