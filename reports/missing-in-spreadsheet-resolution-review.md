# Missing-in-Spreadsheet Mapping Assertions Review

This note reviews the remaining `missing_in_spreadsheet` audit category after PR #43.

No TTL or spreadsheet changes are made by this note.

## Current audit status

After the latest cleanup, the audit reports:

- `missing_in_ttl`: 61
- `missing_in_spreadsheet`: 13
- `target_mismatch`: 0
- `prefix_or_iri_issue`: 0
- `needs_human_review`: 0

The remaining `missing_in_spreadsheet` items are TTL assertions that the current audit does not find in the spreadsheet.

## Audit interpretation policy

These issues should not yet be treated as modeling decisions.

For reconciliation purposes, the spreadsheet should be read narrowly. A spreadsheet mapping assertion should be extracted only from explicit assertion-bearing fields, namely:

- source term;
- mapping predicate / relation;
- mapping target.

Other spreadsheet fields should be treated as possible documentation only, including notes, explanations, labels, examples, comments, modeling rationale, background OWL text, or other descriptive columns.

Accordingly, the audit tool should not infer expected mapping assertions merely from contextual or explanatory spreadsheet content unless the relevant spreadsheet column is explicitly intended to encode a mapping assertion.

## Consequence for the 13 `missing_in_spreadsheet` issues

The 13 remaining `missing_in_spreadsheet` items should be treated as requiring audit-method review before ontology or spreadsheet edits are made.

For each item, the next question is not immediately:

- "Is the TTL assertion correct?"

The prior question is:

- "Is the spreadsheet expected to contain this assertion under the strict source-term / predicate / target reading?"

Only after that question is answered should a modeling decision be made.

## Recommended next step

Before applying TTL or spreadsheet changes, update or review `tools/compare_mappings.py` so that spreadsheet-derived expected assertions are generated only from explicit source-term, predicate/relation, and target fields.

After the audit extraction policy is confirmed, rerun the audit command and reassess the remaining `missing_in_spreadsheet` and `missing_in_ttl` categories.
