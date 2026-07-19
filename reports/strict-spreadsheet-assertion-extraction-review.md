# Strict Spreadsheet Assertion Extraction Review

This note reviews whether `tools/compare_mappings.py` is generating spreadsheet-expected assertions from documentation columns or only from explicit assertion-bearing spreadsheet content.

No TTL, spreadsheet, or audit-tool changes are made by this note.

## Finding

The audit tool is already reading the spreadsheet narrowly for expected mapping assertions.

The inspected workbook sheets use the following relevant columns:

- `IRI`
- `OWL Axiom`
- `Reasoning`
- other documentation columns

The audit tool requires a sheet to contain both `IRI` and `OWL Axiom` before treating it as a mapping sheet. For each row, it reads:

- the source term from the `IRI` column;
- the expected assertion text from the `OWL Axiom` column.

It then parses expected assertions from the `OWL Axiom` value only.

## Consequence

The current remaining `missing_in_spreadsheet` issues should not be treated as caused by the audit tool reading `Definition`, `BFO Definition`, `Natural Language OWL`, `Reasoning`, or `SHACL` as assertion-bearing fields.

Those columns may provide modeling rationale or documentation, but they are not currently used by the tool to generate expected spreadsheet assertions.

## Revised interpretation

The 13 `missing_in_spreadsheet` issues are more likely genuine differences between:

- mapping assertions present in `SSN2BFO.ttl`; and
- assertions currently present in the spreadsheet's `OWL Axiom` column.

This is consistent with the possibility that the spreadsheet has been updated since some TTL assertions were added.

## Next review step

Review the 13 `missing_in_spreadsheet` issues against the current spreadsheet `OWL Axiom` cells and reasoning text.

Where the spreadsheet intentionally omits or rejects a TTL assertion, the appropriate follow-up is a narrowly scoped TTL-removal PR, not an audit-tool correction PR.

Where the TTL assertion is still intended but missing from the spreadsheet `OWL Axiom` cell, the appropriate follow-up is a spreadsheet-documentation PR.

Where the issue depends on broader modeling policy, record and defer.
