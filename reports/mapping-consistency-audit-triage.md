# Mapping Consistency Audit Triage

## Audit Context

- Source report: `reports/mapping-consistency-audit.md`
- Source CSV: `reports/mapping-consistency-audit.csv`
- Total issues: 79
- High-priority categories reviewed:
  - `prefix_or_iri_issue`: 6
  - `target_mismatch`: 4
  - `needs_human_review`: 1

This note triages only the high-priority categories listed above. It does not create, infer, revise, normalize, move, split, or suggest ontology mappings.

## Prefix / IRI Issues

Five issues are caused by an unresolved `sampling:` prefix in the `Sample Relationship` sheet:

| Issue ID | Source term | Summary |
| --- | --- | --- |
| `ISSUE-0017` | `sampling:hasSampleRelationship` | `sampling:` prefix is unresolved for comparison. |
| `ISSUE-0021` | `sampling:natureOfRelationship` | `sampling:` prefix is unresolved for comparison. |
| `ISSUE-0025` | `sampling:relatedSample` | `sampling:` prefix is unresolved for comparison. |
| `ISSUE-0029` | `sampling:RelationshipNature` | `sampling:` prefix is unresolved for comparison. |
| `ISSUE-0033` | `sampling:SampleRelationship` | `sampling:` prefix is unresolved for comparison. |

Recommended action:

- Define the intended `sampling:` prefix in workbook or repository documentation before mechanical comparison.
- Do not edit TTL based on these rows until the prefix is resolved.

One additional prefix or IRI issue involves an unresolved CCO label alias:

| Issue ID | Source term | Summary |
| --- | --- | --- |
| `ISSUE-0039` | `sosa:Procedure` | Spreadsheet target includes unresolved label alias `cco:PrescriptiveInformationContentEntity`. |

Recommended action:

- Replace or supplement the label-style target with a resolvable CCO IRI or CURIE in the spreadsheet.
- Do not edit TTL mechanically.

## Target Mismatches

| Issue ID | Source term | TTL target detail | Spreadsheet target detail | Recommended action |
| --- | --- | --- | --- | --- |
| `ISSUE-0022` | `ssn-system:ActuationRange` | TTL target includes `ssn:hasOutput`. | Spreadsheet target includes `cco:ont00001986`. | Compare intended OWL axiom before editing. |
| `ISSUE-0026` | `sosa:Actuator` | TTL target includes `bfo:BFO_0000054`. | Spreadsheet target includes `bfo:BFO_0000055`. | Review whether the intended relation is realizes or realized-in style before editing. |
| `ISSUE-0053` | `sosa:Sampling` | TTL target includes `ssn:hasOutput`. | Spreadsheet target includes `cco:ont00001986`. | Compare intended OWL axiom before editing. |
| `ISSUE-0059` | `ssn-system:OperatingRange` | TTL target includes `cco:ont00000118`. | Spreadsheet target includes `cco:ont00000319`. | Review target class choice before editing. |

## Human-Review Item

| Issue ID | Source term | Summary | Recommended action |
| --- | --- | --- | --- |
| `ISSUE-0032` | `ssn:forProperty` | Spreadsheet OWL axiom could not be parsed into a supported comparison assertion. | Review and normalize the spreadsheet OWL Axiom cell format if this row should be machine-comparable. Do not edit TTL mechanically. |

## Explicit Non-Actions

- No TTL mapping edits should be made from this triage alone.
- No spreadsheet edits are made in this PR.
- No release artifacts are changed.
- `missing_in_ttl` and `missing_in_spreadsheet` issues remain for later review.
