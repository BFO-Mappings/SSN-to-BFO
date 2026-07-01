# Mapping Consistency Audit Triage

## Audit Context

- Source report: `reports/mapping-consistency-audit.md`
- Source CSV: `reports/mapping-consistency-audit.csv`
- Total issues: 84
- High-priority categories reviewed:
  - `prefix_or_iri_issue`: 1
  - `target_mismatch`: 4
  - `needs_human_review`: 1

This note triages only the high-priority categories listed above. It does not create, infer, revise, normalize, move, split, or suggest ontology mappings.

## Prefix / IRI Issues

The audit now accepts `sampling:` as an alias for the SOSA sample-relationship namespace. The preferred repo-facing alias is `sosa-rel:`.

Former `sampling:` findings are now normal comparable findings, mostly classified as `missing_in_ttl`, rather than prefix failures. They should not be treated as unresolved-prefix blockers in this review pass.

The only remaining prefix or IRI issue is an unresolved CCO label alias:

| Issue ID | Source term | Sheet / row | Summary |
| --- | --- | --- | --- |
| `ISSUE-0044` | `sosa:Procedure` | `Common Classes` / 12 | Spreadsheet target includes unresolved label alias `cco:PrescriptiveInformationContentEntity`. |

Recommended action:

- Replace or supplement the label-style target with a resolvable CCO IRI or CURIE in the spreadsheet.
- Do not edit TTL mechanically.

## Sampling Alias Comparable Findings

The following former `sampling:` prefix findings are now comparable audit rows under the accepted alias. They remain review items, but not prefix failures.

| Issue ID | Source term | Sheet / row | Current category | Summary |
| --- | --- | --- | --- | --- |
| `ISSUE-0016` | `sampling:hasSampleRelationship` | `Sample Relationship` / 2 | `missing_in_ttl` | Spreadsheet assertion for `schema:domainIncludes sosa:Sample` is now comparable. |
| `ISSUE-0017` | `sampling:hasSampleRelationship` | `Sample Relationship` / 2 | `missing_in_ttl` | Spreadsheet assertion for `schema:rangeIncludes sampling:SampleRelationship` is now comparable. |
| `ISSUE-0019` | `sampling:natureOfRelationship` | `Sample Relationship` / 3 | `missing_in_ttl` | Spreadsheet assertion for `schema:domainIncludes sampling:SampleRelationship` is now comparable. |
| `ISSUE-0020` | `sampling:natureOfRelationship` | `Sample Relationship` / 3 | `missing_in_ttl` | Spreadsheet assertion for `schema:rangeIncludes sampling:RelationshipNature` is now comparable. |
| `ISSUE-0025` | `sampling:relatedSample` | `Sample Relationship` / 4 | `missing_in_ttl` | Spreadsheet assertion for `schema:domainIncludes sampling:SampleRelationship` is now comparable. |
| `ISSUE-0026` | `sampling:relatedSample` | `Sample Relationship` / 4 | `missing_in_ttl` | Spreadsheet assertion for `schema:rangeIncludes sosa:Sample` is now comparable. |
| `ISSUE-0030` | `sampling:RelationshipNature` | `Sample Relationship` / 5 | `missing_in_ttl` | Spreadsheet assertion for `rdfs:subClassOf cco:ont00000958` is now comparable. |
| `ISSUE-0033` | `sampling:SampleRelationship` | `Sample Relationship` / 6 | `missing_in_ttl` | Spreadsheet assertion for `rdfs:subClassOf cco:ont00000958` is now comparable. |
| `ISSUE-0034` | `sampling:SampleRelationship` | `Sample Relationship` / 6 | `missing_in_ttl` | Spreadsheet restriction involving `sampling:relatedSample` is now comparable. |
| `ISSUE-0035` | `sampling:SampleRelationship` | `Sample Relationship` / 6 | `missing_in_ttl` | Spreadsheet restriction involving `sampling:natureOfRelationship` is now comparable. |

Recommended action:

- Keep `sampling:` supported in the audit as an alias.
- Prefer `sosa-rel:` in repo-facing documentation and future review notes.
- Do not propose TTL edits from these rows in this triage.

## Target Mismatches

| Issue ID | Source term | TTL target detail | Spreadsheet target detail | Recommended action |
| --- | --- | --- | --- | --- |
| `ISSUE-0024` | `ssn-system:ActuationRange` | TTL target includes `ssn:hasOutput`. | Spreadsheet target includes `cco:ont00001986`. | Compare intended OWL axiom before selecting any corrective action. |
| `ISSUE-0029` | `sosa:Actuator` | TTL target includes `bfo:BFO_0000054`. | Spreadsheet target includes `bfo:BFO_0000055`. | Review whether the intended relation is realizes or realized-in style before selecting any corrective action. |
| `ISSUE-0058` | `sosa:Sampling` | TTL target includes `ssn:hasOutput`. | Spreadsheet target includes `cco:ont00001986`. | Compare intended OWL axiom before selecting any corrective action. |
| `ISSUE-0064` | `ssn-system:OperatingRange` | TTL target includes `cco:ont00000118`. | Spreadsheet target includes `cco:ont00000319`. | Review target class choice before selecting any corrective action. |

## Human-Review Item

| Issue ID | Source term | Summary | Recommended action |
| --- | --- | --- | --- |
| `ISSUE-0038` | `ssn:forProperty` | Spreadsheet OWL axiom could not be parsed into a supported comparison assertion. | Review and normalize the spreadsheet OWL Axiom cell format if this row should be machine-comparable. Do not edit TTL mechanically. |

## Explicit Non-Actions

- No TTL mapping edits should be made from this triage alone.
- No spreadsheet edits are made in this PR.
- No release artifacts are changed.
- `missing_in_ttl` and `missing_in_spreadsheet` issues remain for later review.
