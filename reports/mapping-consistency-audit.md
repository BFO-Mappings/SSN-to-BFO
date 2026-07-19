# Mapping Consistency Audit

## Files Inspected
- TTL mapping file: `SSN2BFO.ttl`
- Spreadsheet mapping source: `Current_SOSA-SSN to BFO-CCO.xlsx`
- Sheets inspected: `Common Classes`, `Common OPs`, `Common DPs`, `System Capability`, `Sample Relationship`

## Git Context
- Current branch: `fix/apply-object-property-domain-range-minimal-basis`
- Current commit: `64cb89df318832a5e6dab8f065514bb022d0de1e`
- Working tree had untracked audit files at report generation time: no
- Audit file status entries at report generation time: none

## Detected Spreadsheet Schema
| Sheet | Header Row | Source/IRI Column | OWL Axiom Column | Comment/Notes Columns | Status/Review Columns | Candidate Mapping Rows |
| --- | ---: | --- | --- | --- | --- | ---: |
| Common Classes | 1 | A (`IRI`) | E (`OWL Axiom`) | B (`Definition`); C (`BFO Definition`); D (`Natural Language OWL`); F (`Reasoning`); G (`SHACL`) | none detected | 19 |
| Common OPs | 1 | A (`IRI`) | E (`OWL Axiom`) | B (`Definition`); C (`BFO Definition`); D (`Natural Language OWL`); F (`Reasoning`); G (`SHACL`) | none detected | 36 |
| Common DPs | 1 | A (`IRI`) | E (`OWL Axiom`) | B (`Definition`); C (`BFO Definition`); D (`Natural Language OWL`); F (`Reasoning`); G (`SHACL`) | none detected | 2 |
| System Capability | 1 | A (`IRI`) | E (`OWL Axiom`) | B (`Definition`); C (`BFO Definition`); D (`Natural Language OWL`); F (`Reasoning`); G (`SHACL`) | none detected | 31 |
| Sample Relationship | 1 | A (`IRI`) | E (`OWL Axiom`) | B (`Definition`); C (`BFO Definition`); D (`Natural Language OWL`); F (`Reasoning`); G (`SHACL`) | none detected | 5 |

## Comparison Method
- Spreadsheet rows were treated as authoritative only when a sheet had both `IRI` and `OWL Axiom` columns.
- TTL assertions were considered candidate mapping assertions only when they used recognized mapping predicates and had SSN/SOSA source subjects or spreadsheet-governed source subjects.
- Declarations, imports, labels, comments, and non-mapping metadata triples were ignored for mismatch classification.
- Prefixes were expanded to full IRIs. CCO and BFO label-style CURIEs in the spreadsheet were resolved through labels in `imports/cco.ttl` where unique.
- Blank-node OWL class expressions were summarized by the named IRIs they contain; these require human review before any ontology edit.

## TTL Extraction Criteria
- Candidate mapping assertions: triples whose predicate is one of the recognized mapping predicates, whose subject is an SSN/SOSA source IRI or a spreadsheet-governed source IRI, and whose object or blank-node expression can be summarized for comparison.
- Supporting ontology/context triples: blank-node triples inside OWL restrictions, intersections, unions, and property chains. These are traversed only to collect named IRIs for a candidate mapping expression.
- Ignored metadata/declaration triples: ontology imports, `rdf:type` declarations for classes/properties/ontologies, labels, comments, definitions, and other non-mapping predicates.
- Declarations are excluded because they only state entity kind, not mapping intent. Imports are excluded because they establish context, not source-to-target mapping rows. Labels/comments/definitions are excluded because the audit compares IRIs and asserted relations rather than relying on prose. Blank-subject triples are excluded as standalone mappings because they are expression structure without their owning source subject. Non-mapping predicates are excluded to keep supporting ontology context from being reported as spreadsheet-governed mappings.

## Exact Command Used

```bash
/opt/miniconda3/bin/python tools/compare_mappings.py --ttl SSN2BFO.ttl --spreadsheet 'Current_SOSA-SSN to BFO-CCO.xlsx' --output-md reports/mapping-consistency-audit.md --output-csv reports/mapping-consistency-audit.csv
```

## Portable Command Example

```bash
python tools/compare_mappings.py --ttl SSN2BFO.ttl --spreadsheet "Current_SOSA-SSN to BFO-CCO.xlsx" --output-md reports/mapping-consistency-audit.md --output-csv reports/mapping-consistency-audit.csv
```

## Summary
- Total spreadsheet mapping rows: 93
- Total spreadsheet expected assertions parsed: 68
- Total TTL candidate mapping assertions: 68
- Exact spreadsheet row matches: 65
- Exact assertion matches: 67
- Total issues: 2

## Issues by Category
- `missing_in_ttl`: 1
- `missing_in_spreadsheet`: 1
- `target_mismatch`: 0
- `relation_mismatch`: 0
- `status_mismatch`: 0
- `duplicate_mapping`: 0
- `conflicting_mapping`: 0
- `label_only_match`: 0
- `prefix_or_iri_issue`: 0
- `needs_human_review`: 0

Note: not all supported issue categories necessarily appear in this run; zero-count categories are still supported by the audit taxonomy.

## Ignored TTL Triples
- `blank_subject`: 880
- `declaration`: 102
- `non_mapping_predicate`: 25

## Skipped or Partially Parsed Rows
| Sheet | Row | Source | Reason |
| --- | ---: | --- | --- |
| Common OPs | 6 | ssn:forProperty | no parsed expected assertions |
| Common OPs | 8 | sosa:hasFeatureOfInterest | no parsed expected assertions |
| Common OPs | 9 | ssn:hasInput | no parsed expected assertions |
| Common OPs | 10 | ssn:hasOutput | no parsed expected assertions |
| Common OPs | 11 | ssn:hasProperty | no parsed expected assertions |
| Common OPs | 17 | ssn:implements | no parsed expected assertions |
| Common OPs | 20 | sosa:isFeatureOfInterestOf | no parsed expected assertions |
| Common OPs | 22 | sosa:isObservedBy | no parsed expected assertions |
| Common OPs | 23 | ssn:isPropertyOf | no parsed expected assertions |
| Common OPs | 24 | ssn:isProxyFor | no parsed expected assertions |
| Common OPs | 27 | sosa:madeActuation | no parsed expected assertions |
| Common OPs | 28 | sosa:madeByActuator | no parsed expected assertions |
| Common OPs | 33 | sosa:observedProperty | no parsed expected assertions |
| Common OPs | 35 | sosa:phenomenonTime | no parsed expected assertions |
| Common DPs | 2 | sosa:hasSimpleResult | no parsed expected assertions |
| Common DPs | 3 | sosa:resultTime | no parsed expected assertions |
| System Capability | 4 | ssn-system:BatteryLifetime | no parsed expected assertions |
| System Capability | 9 | ssn-system:hasOperatingProperty | no parsed expected assertions |
| System Capability | 11 | ssn-system:hasSurvivalProperty | no parsed expected assertions |
| System Capability | 14 | ssn-system:hasSystemProperty | no parsed expected assertions |
| System Capability | 15 | ssn-system:inCondition | no parsed expected assertions |
| System Capability | 18 | ssn-system:MeasurementRange | no parsed expected assertions |
| System Capability | 29 | ssn-system:SurvivalRange | no parsed expected assertions |
| System Capability | 32 | ssn-system:SystemProperty | no parsed expected assertions |
| Sample Relationship | 2 | sampling:hasSampleRelationship | no parsed expected assertions |
| Sample Relationship | 3 | sampling:natureOfRelationship | no parsed expected assertions |
| Sample Relationship | 4 | sampling:relatedSample | no parsed expected assertions |

## Detailed Issues
| Issue ID | Category | Sheet | Row | Source | Source IRI | TTL Predicate | Spreadsheet Relation | TTL Target | Spreadsheet Target | TTL Line | Recommended Action |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: | --- |
| ISSUE-0001 | missing_in_spreadsheet |  |  | sosa:Sensor | http://www.w3.org/ns/sosa/Sensor | rdfs:subClassOf |  | bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Observation; cco:ont00001787 |  | 575 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0002 | missing_in_ttl | Common Classes | 18 | sosa:Sensor | http://www.w3.org/ns/sosa/Sensor |  | owl:equivalentClass |  | bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |

## Proposed Minimal Correction Plan

### Proposed TTL Edits
- Do not edit `SSN2BFO.ttl` until each `target_mismatch`, `relation_mismatch`, and `missing_in_ttl` row has been reviewed against the spreadsheet's `OWL Axiom` and reasoning text.
- For confirmed spreadsheet-governed rows, align the TTL predicate and named target IRIs with the spreadsheet axiom using the smallest possible axiom change.
- Treat rows involving unresolved prefixes or blank-node expression differences as human-review items, not mechanical edits.

### Proposed Spreadsheet Edits
- For `missing_in_spreadsheet` findings, add spreadsheet rows only if the TTL assertion is intended to be governed by this source workbook.
- Add explicit status/review columns if maintainers want rejected, deferred, or provisional mappings to be machine-checkable.
- `sampling:` is accepted by this audit as an alias for the SOSA sample-relationship namespace; `sosa-rel:` is the preferred repo-facing alias.

## Assumptions
- The `OWL Axiom` column is the authoritative machine-comparison source for spreadsheet-governed mappings.
- The workbook has no explicit status or review column in the inspected schema.
- `sampling:` is accepted by this audit as an alias for the SOSA sample-relationship namespace; `sosa-rel:` is the preferred repo-facing alias for the same namespace.
- Label-style `bfo:` and `cco:` spreadsheet tokens are resolved only when they map uniquely to imported labels.
