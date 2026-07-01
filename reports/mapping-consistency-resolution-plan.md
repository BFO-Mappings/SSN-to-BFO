# Mapping Consistency Resolution Plan

Sources:

- `reports/mapping-consistency-audit-triage.md`
- `reports/mapping-consistency-audit.csv`

This checklist tracks review work for high-priority audit findings only. It does not create, infer, revise, normalize, move, split, or suggest ontology mappings.

## 1. Prefix / Schema Cleanup

The audit now accepts `sampling:` as an alias for the SOSA sample-relationship namespace. The preferred repo-facing alias is `sosa-rel:`.

Former `sampling:` findings are normal comparable findings in the current audit, mostly `missing_in_ttl`, not prefix failures. These checklist items are for alias/documentation cleanup only and do not propose TTL edits.

| Status | Issue ID | Source term | Sheet / row | Problem | Proposed resolution type | Fix belongs in |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | `ISSUE-0016` | `sampling:hasSampleRelationship` | `Sample Relationship` / 2 | Comparable assertion uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0017` | `sampling:hasSampleRelationship` | `Sample Relationship` / 2 | Comparable assertion uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0019` | `sampling:natureOfRelationship` | `Sample Relationship` / 3 | Comparable assertion uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0020` | `sampling:natureOfRelationship` | `Sample Relationship` / 3 | Comparable assertion uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0025` | `sampling:relatedSample` | `Sample Relationship` / 4 | Comparable assertion uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0026` | `sampling:relatedSample` | `Sample Relationship` / 4 | Comparable assertion uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0030` | `sampling:RelationshipNature` | `Sample Relationship` / 5 | Comparable assertion uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0033` | `sampling:SampleRelationship` | `Sample Relationship` / 6 | Comparable assertion uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0034` | `sampling:SampleRelationship` | `Sample Relationship` / 6 | Comparable restriction uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |
| [ ] | `ISSUE-0035` | `sampling:SampleRelationship` | `Sample Relationship` / 6 | Comparable restriction uses accepted `sampling:` alias; repo-facing alias should be `sosa-rel:`. | Alias/documentation cleanup; keep mechanical comparison enabled. | Audit prefix map / documentation |

Notes:

- Do not edit TTL based on these rows from this checklist.
- These rows are no longer unresolved-prefix blockers.

## 2. CCO Label / IRI Resolution

| Status | Issue ID | Source term | Sheet / row | Problem | Proposed resolution type | Fix belongs in |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | `ISSUE-0044` | `sosa:Procedure` | `Common Classes` / 12 | Spreadsheet target includes unresolved label alias `cco:PrescriptiveInformationContentEntity`; the audit could not resolve it to a unique CCO IRI or CURIE. The local CCO import does not contain that label/token. | Human review confirmed `cco:ont00000965` is the correct spreadsheet replacement for `cco:PrescriptiveInformationContentEntity`. Update the spreadsheet separately with the resolvable CCO IRI or CURIE. | Spreadsheet |

Notes:

- This is the only remaining `prefix_or_iri_issue` in the current audit.
- The local CCO import contains `cco:ont00000965` with label `"Directive Information Content Entity"`, alt label `"Directive ICE"`, and definition `"An Information Content Entity that consists of a set of propositions or images (as in the case of a blueprint) that prescribe some Entity."`
- Human review confirmed `cco:ont00000965` is the correct replacement for the spreadsheet token `cco:PrescriptiveInformationContentEntity`.
- The spreadsheet should be updated separately for this issue.
- Do not edit `SSN2BFO.ttl` for this issue.

## 3. Target Mismatch Review

| Status | Issue ID | Source term | Sheet / row | Problem | Proposed resolution type | Fix belongs in |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | `ISSUE-0024` | `ssn-system:ActuationRange` | `System Capability` / 3 | TTL target includes `ssn:hasOutput`; spreadsheet target includes `cco:ont00001986`. | Compare intended OWL axiom before selecting any corrective action. | Manual review |
| [ ] | `ISSUE-0029` | `sosa:Actuator` | `Common Classes` / 4 | TTL target includes `bfo:BFO_0000054`; spreadsheet target includes `bfo:BFO_0000055`. | Review whether the intended relation is realizes or realized-in style before selecting any corrective action. | Manual review |
| [ ] | `ISSUE-0058` | `sosa:Sampling` | `Common Classes` / 17 | TTL target includes `ssn:hasOutput`; spreadsheet target includes `cco:ont00001986`. | Compare intended OWL axiom before selecting any corrective action. | Manual review |
| [ ] | `ISSUE-0064` | `ssn-system:OperatingRange` | `System Capability` / 21 | TTL target includes `cco:ont00000118`; spreadsheet target includes `cco:ont00000319`. | Review target class choice before selecting any corrective action. | Manual review |

Notes:

- These rows require human review of intended OWL axioms before any file-specific fix is selected.
- This checklist does not decide whether any eventual fix belongs in TTL or spreadsheet content.

## 4. Unparsed Spreadsheet Axiom Review

| Status | Issue ID | Source term | Sheet / row | Problem | Proposed resolution type | Fix belongs in |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | `ISSUE-0035` | `ssn:forProperty` | `Common OPs` / 6 | Spreadsheet OWL Axiom cell currently asserts `rdfs:range`, `rdfs:domain`, and a property-chain `subPropertyOf` axiom that could not be parsed into a supported comparison assertion. | Human review determined the spreadsheet OWL Axiom cell is wrong and should be cleared or removed separately. Do not carry forward the shown domain axiom, range axiom, or property-chain axiom using `cco:described_by` followed by `cco:is_about`. | Spreadsheet |

Notes:

- Do not edit `SSN2BFO.ttl` for this issue.
- `ssn:forProperty` should not have the domain axiom shown in the spreadsheet.
- `ssn:forProperty` should not have the range axiom shown in the spreadsheet.
- The property-chain axiom using `cco:described_by` followed by `cco:is_about` is also wrong.
- The spreadsheet should be updated separately by clearing or removing the OWL Axiom cell for `ssn:forProperty`.

## Explicit Non-Actions

- No ontology mapping edits are made or recommended by this checklist.
- No spreadsheet edits are made by this checklist.
- No import, release, `src`, or `sosa-next` files are changed by this checklist.
- `missing_in_ttl` and `missing_in_spreadsheet` audit findings remain outside this high-priority review pass.
