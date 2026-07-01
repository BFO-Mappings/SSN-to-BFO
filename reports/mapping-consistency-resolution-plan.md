# Mapping Consistency Resolution Plan

Sources:

- `reports/mapping-consistency-audit-triage.md`
- `reports/mapping-consistency-audit.csv`

This checklist tracks review work for high-priority audit findings only. It does not create, infer, revise, normalize, move, split, or suggest ontology mappings.

## 1. Prefix / Schema Cleanup

| Status | Issue ID | Source term | Sheet / row | Problem | Proposed resolution type | Fix belongs in |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | `ISSUE-0017` | `sampling:hasSampleRelationship` | `Sample Relationship` / 2 | `sampling:` prefix is unresolved, so the source IRI cannot be expanded for comparison. | Define the intended `sampling:` namespace before rerunning mechanical comparison. | Spreadsheet documentation / audit prefix map |
| [ ] | `ISSUE-0021` | `sampling:natureOfRelationship` | `Sample Relationship` / 3 | `sampling:` prefix is unresolved, including target reference `sampling:SampleRelationship`. | Define the intended `sampling:` namespace before rerunning mechanical comparison. | Spreadsheet documentation / audit prefix map |
| [ ] | `ISSUE-0025` | `sampling:relatedSample` | `Sample Relationship` / 4 | `sampling:` prefix is unresolved, including target reference `sampling:SampleRelationship`. | Define the intended `sampling:` namespace before rerunning mechanical comparison. | Spreadsheet documentation / audit prefix map |
| [ ] | `ISSUE-0029` | `sampling:RelationshipNature` | `Sample Relationship` / 5 | `sampling:` prefix is unresolved for the source term. | Define the intended `sampling:` namespace before rerunning mechanical comparison. | Spreadsheet documentation / audit prefix map |
| [ ] | `ISSUE-0033` | `sampling:SampleRelationship` | `Sample Relationship` / 6 | `sampling:` prefix is unresolved for the source term and related sample relationship targets. | Define the intended `sampling:` namespace before rerunning mechanical comparison. | Spreadsheet documentation / audit prefix map |

Notes:

- Do not edit TTL based on these rows until the `sampling:` namespace is resolved.
- If the workbook is intended to govern these rows, the namespace should be documented where future audits can read it consistently.

## 2. CCO Label / IRI Resolution

| Status | Issue ID | Source term | Sheet / row | Problem | Proposed resolution type | Fix belongs in |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | `ISSUE-0039` | `sosa:Procedure` | `Common Classes` / 12 | Spreadsheet target includes unresolved label alias `cco:PrescriptiveInformationContentEntity`; the audit could not resolve it to a unique CCO IRI or CURIE. | Replace or supplement the label-style target with a resolvable CCO IRI or CURIE before mechanical comparison. | Spreadsheet |

Notes:

- Do not edit TTL mechanically from this issue.
- The next review step is to make the spreadsheet target resolvable, not to infer an ontology mapping.

## 3. Target Mismatch Review

| Status | Issue ID | Source term | Sheet / row | Problem | Proposed resolution type | Fix belongs in |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | `ISSUE-0022` | `ssn-system:ActuationRange` | `System Capability` / 3 | TTL target includes `ssn:hasOutput`; spreadsheet target includes `cco:ont00001986`. | Compare intended OWL axiom before editing. | Manual review |
| [ ] | `ISSUE-0026` | `sosa:Actuator` | `Common Classes` / 4 | TTL target includes `bfo:BFO_0000054`; spreadsheet target includes `bfo:BFO_0000055`. | Review whether the intended relation is realizes or realized-in style before editing. | Manual review |
| [ ] | `ISSUE-0053` | `sosa:Sampling` | `Common Classes` / 17 | TTL target includes `ssn:hasOutput`; spreadsheet target includes `cco:ont00001986`. | Compare intended OWL axiom before editing. | Manual review |
| [ ] | `ISSUE-0059` | `ssn-system:OperatingRange` | `System Capability` / 21 | TTL target includes `cco:ont00000118`; spreadsheet target includes `cco:ont00000319`. | Review target class choice before editing. | Manual review |

Notes:

- These rows require human review of intended OWL axioms before any file-specific fix is selected.
- This checklist does not decide whether any eventual fix belongs in TTL or spreadsheet content.

## 4. Unparsed Spreadsheet Axiom Review

| Status | Issue ID | Source term | Sheet / row | Problem | Proposed resolution type | Fix belongs in |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | `ISSUE-0032` | `ssn:forProperty` | `Common OPs` / 6 | Spreadsheet OWL axiom could not be parsed into a supported comparison assertion. | Review and normalize the spreadsheet OWL Axiom cell format if this row should be machine-comparable. | Manual review / spreadsheet |

Notes:

- Do not edit TTL mechanically from this issue.
- The first decision is whether the spreadsheet axiom should be made machine-comparable in a future spreadsheet-focused change.

## Explicit Non-Actions

- No ontology mapping edits are made or recommended by this checklist.
- No spreadsheet edits are made by this checklist.
- No import, release, `src`, or `sosa-next` files are changed by this checklist.
- `missing_in_ttl` and `missing_in_spreadsheet` audit findings remain outside this high-priority review pass.
