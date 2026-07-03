# `sosa:Sensor` Next CCO Version Deferral

This note records the disposition of the remaining `sosa:Sensor` audit rows.

No TTL, spreadsheet, tool, generated audit, or versioned mapping files are changed by this note.

## Current issue

The remaining `sosa:Sensor` audit rows reflect a version/alignment split between:

- the current `SSN2BFO.ttl` treatment of `sosa:Sensor`; and
- the spreadsheet's intended target for a future / next CCO version.

## Decision

Defer the `sosa:Sensor` mapping split until the next relevant CCO version is released.

Do not create separate current-CCO and next-CCO `sosa:Sensor` mapping files yet.

Do not mechanically revise the root `SSN2BFO.ttl` in this cleanup pass.

## Rationale

Creating versioned mapping files before the next CCO release is available would risk encoding a speculative target. The safer approach is to preserve the current mapping, keep the audit issue visible, and revisit the mapping once the next CCO version can be referenced directly.

## Audit treatment

The remaining `sosa:Sensor` audit rows are retained as known deferred version/alignment issues.

They should not be interpreted as accidental omissions from the direct spreadsheet/TTL reconciliation cleanup.
