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

## Provisional Sample Relationship mappings

The prior `Sample Relationship` audit rows have been implemented to support instance-data testing.

They remain provisional and require close review before being treated as release-quality or authoritative BFO/CCO mappings. The sample relationship material appears to model relation-like content through classes and class restrictions, which makes the BFO/CCO alignment non-mechanical.

See:

- `reports/sample-relationship-deferral.md`

## Deferred reasoner-unsafe mappings

The following mappings were deferred after ELK reasoner diagnostics showed they made the ontology unsatisfiable:

- `ssn:hasProperty`
- `ssn-system:BatteryLifetime`
- `ssn-system:MeasurementRange`

The corresponding spreadsheet `OWL Axiom` cells were cleared, and the TTL mapping blocks were removed from the current reasoner-testable mapping file.

These mappings require separate reasoner-safe modeling review before reintroduction.

See:

- `reports/reasoner-unsafe-system-mapping-deferral.md`

## Deferred version issue

### `sosa:Sensor`

The remaining `sosa:Sensor` issues are known version/alignment issues involving the current TTL and the spreadsheet's intended CCO target.

Disposition:

- do not mechanically revise the root `SSN2BFO.ttl` in this cleanup pass;
- do not create separate current-CCO and next-CCO `sosa:Sensor` mapping files yet;
- defer the versioned mapping split until the next relevant CCO version is released;
- preserve the audit rows as deferred version/alignment issues.

See:

- `reports/sensor-next-cco-deferral.md`

## Summary

The remaining audit issues are intentionally retained as classified issues:

1. provisional `Sample Relationship` mappings requiring close review;
2. deferred `sosa:Sensor` version-alignment issues.

They should not be interpreted as unresolved accidental omissions from the direct spreadsheet/TTL reconciliation cleanup.
