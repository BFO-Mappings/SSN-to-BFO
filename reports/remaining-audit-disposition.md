# Remaining Mapping Audit Disposition

This note records the disposition of the remaining mapping audit issues after the reviewed direct mappings, spreadsheet/TTL corrections, property-chain corrections, and datatype-property placeholder cleanup.

## Current audit state

The current audit state is:

- total issues: 6
- `missing_in_spreadsheet`: 1
- `missing_in_ttl`: 5
- `target_mismatch`: 0
- `relation_mismatch`: 0

The remaining issues are not ordinary mechanical cleanup candidates.

## Resolved since prior disposition

The prior datatype-property placeholder rows for the following terms have been resolved and no longer appear as audit issues:

- `sosa:hasSimpleResult`
- `sosa:resultTime`

The previous `owl:topDataProperty` placeholder axioms were removed from the spreadsheet `OWL Axiom` cells. They were not added to TTL because `owl:topDataProperty` is semantically redundant as a mapping target and could obscure later placement under a more specific datatype-property hierarchy.

The prior complex property-chain rows for the following terms have also been resolved and no longer appear as audit issues:

- `sosa:hosts`
- `sosa:isHostedBy`
- `ssn:implementedBy`

These were resolved by correcting the spreadsheet rows to direct `owl:propertyChainAxiom` mappings and adding matching TTL property-chain axioms.

## Deferred Sample Relationship mappings

The remaining `Sample Relationship` rows are deferred substantive mappings.

They are not no-action rows and should not be treated as ordinary TTL omissions. The sample relationship material appears to model relation-like content through classes and class restrictions, which makes the BFO/CCO alignment non-mechanical.

These rows require a separate modeling pass to determine how SOSA's sample relationship pattern should be represented in BFO/CCO.

See:

- `reports/sample-relationship-deferral.md`

## Deferred version issue

### `sosa:Sensor`

The remaining `sosa:Sensor` issues are known version/alignment issues involving the current TTL and the spreadsheet's intended CCO target.

Disposition:

- do not mechanically revise the TTL in this cleanup pass;
- preserve as deferred pending the relevant CCO-version alignment decision.

## Summary

The remaining audit issues are intentionally retained as classified issues:

1. deferred `Sample Relationship` substantive mapping issues;
2. deferred `sosa:Sensor` version-alignment issues.

They should not be interpreted as unresolved accidental omissions from the direct spreadsheet/TTL reconciliation cleanup.
