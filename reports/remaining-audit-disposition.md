# Remaining Mapping Audit Disposition

This note records the disposition of the remaining mapping audit issues after the reviewed direct mappings, spreadsheet/TTL corrections, and property-chain corrections.

## Current audit state

The current audit state is:

- total issues: 8
- `missing_in_spreadsheet`: 1
- `missing_in_ttl`: 7
- `target_mismatch`: 0
- `relation_mismatch`: 0

The remaining issues are not ordinary mechanical cleanup candidates.

## Resolved since prior disposition

The prior complex property-chain rows for the following terms have been resolved and no longer appear as audit issues:

- `sosa:hosts`
- `sosa:isHostedBy`
- `ssn:implementedBy`

These were resolved by correcting the spreadsheet rows to direct `owl:propertyChainAxiom` mappings and adding matching TTL property-chain axioms.

## No-action rows

### Datatype property placeholders

The following rows are retained as spreadsheet placeholders and do not require TTL implementation:

- `sosa:hasSimpleResult rdfs:subPropertyOf owl:topDataProperty`
- `sosa:resultTime rdfs:subPropertyOf owl:topDataProperty`

These are datatype-property placeholder rows, not substantive BFO/CCO object-property mappings.

### Sample Relationship rows

The remaining `Sample Relationship` rows are not treated as required TTL mapping omissions in the current reconciliation pass.

They are retained as non-mechanical / out-of-scope for this audit cleanup unless the project decides that the Sample Relationship sheet is governed by `SSN2BFO.ttl`.

## Deferred version issue

### `sosa:Sensor`

The remaining `sosa:Sensor` issues are known version/alignment issues involving the current TTL and the spreadsheet's intended CCO target.

Disposition:

- do not mechanically revise the TTL in this cleanup pass;
- preserve as deferred pending the relevant CCO-version alignment decision.

## Summary

The remaining audit issues are intentionally retained as classified issues:

1. no-action datatype-property placeholder rows;
2. Sample Relationship rows that are out of scope for this reconciliation pass unless separately accepted;
3. deferred `sosa:Sensor` version-alignment issues.

They should not be interpreted as unresolved accidental omissions from the direct spreadsheet/TTL reconciliation cleanup.
