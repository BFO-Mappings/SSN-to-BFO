# Remaining Mapping Audit Disposition

This note records the disposition of the remaining mapping audit issues after the reviewed direct mappings and spreadsheet/TTL corrections.

No TTL, spreadsheet, tool, or generated audit files are changed by this note.

## Current audit state

The current audit state is:

- total issues: 11
- `missing_in_spreadsheet`: 1
- `missing_in_ttl`: 10
- `target_mismatch`: 0
- `relation_mismatch`: 0

The remaining issues are not ordinary mechanical cleanup candidates.

## No-action rows

### Datatype property placeholders

The following rows are retained as spreadsheet placeholders and do not require TTL implementation:

- `sosa:hasSimpleResult rdfs:subPropertyOf owl:topDataProperty`
- `sosa:resultTime rdfs:subPropertyOf owl:topDataProperty`

These are datatype-property placeholder rows, not substantive BFO/CCO object-property mappings.

### Sample Relationship rows

The remaining `Sample Relationship` rows are not treated as required TTL mapping omissions in the current reconciliation pass.

They are retained as non-mechanical / out-of-scope for this audit cleanup.

## Complex reviewed rows

### `sosa:hosts`

The remaining `sosa:hosts` issues come from property-chain material in the spreadsheet row.

This was reviewed in `reports/hosts-implementedby-complex-mapping-review.md`.

Disposition:

- do not implement mechanically as a TTL-only subproperty patch;
- do not treat the current audit issue as an accidental omission;
- revisit only through a separate modeling decision about the intended property-chain pattern.

### `ssn:implementedBy`

The remaining `ssn:implementedBy` issue also comes from property-chain material in the spreadsheet row.

This was reviewed in `reports/hosts-implementedby-complex-mapping-review.md`.

Disposition:

- do not implement mechanically as a TTL-only subproperty patch;
- do not treat the current audit issue as an accidental omission;
- revisit only through a separate modeling decision about the intended process-mediated implementation pattern.

## Deferred version issue

### `sosa:Sensor`

The remaining `sosa:Sensor` issue is a known version/alignment issue involving the current TTL and the spreadsheet's intended CCO target.

Disposition:

- do not mechanically revise the TTL in this cleanup pass;
- preserve as a deferred issue pending the relevant CCO-version alignment decision.

## Summary

The remaining audit issues are intentionally retained as classified issues:

1. no-action placeholder / out-of-scope rows;
2. complex property-chain modeling rows requiring separate decisions;
3. deferred `sosa:Sensor` version-alignment issue.

They should not be interpreted as unresolved accidental omissions from the direct spreadsheet/TTL reconciliation cleanup.
