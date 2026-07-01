# Mapping Consistency Audit

## Files Inspected
- TTL mapping file: `SSN2BFO.ttl`
- Spreadsheet mapping source: `Current_SOSA-SSN to BFO-CCO.xlsx`
- Sheets inspected: `Common Classes`, `Common OPs`, `Common DPs`, `System Capability`, `Sample Relationship`

## Git Context
- Current branch: `fix/spreadsheet-forproperty-axiom`
- Current commit: `f8bae8acdbcd7318c7143d7f85dbeb3ec2eca1a7`
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
- Total spreadsheet expected assertions parsed: 120
- Total TTL candidate mapping assertions: 73
- Exact spreadsheet row matches: 53
- Exact assertion matches: 59
- Total issues: 75

## Issues by Category
- `missing_in_ttl`: 61
- `missing_in_spreadsheet`: 14
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
- `blank_subject`: 994
- `declaration`: 102
- `non_mapping_predicate`: 3

## Skipped or Partially Parsed Rows
| Sheet | Row | Source | Reason |
| --- | ---: | --- | --- |
| Common OPs | 6 | ssn:forProperty | no parsed expected assertions |
| System Capability | 15 | ssn-system:inCondition | no parsed expected assertions |

## Detailed Issues
| Issue ID | Category | Sheet | Row | Source | Source IRI | TTL Predicate | Spreadsheet Relation | TTL Target | Spreadsheet Target | TTL Line | Recommended Action |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: | --- |
| ISSUE-0001 | missing_in_spreadsheet |  |  | sosa:Sampler | http://www.w3.org/ns/sosa/Sampler | rdfs:subClassOf |  | bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Sampling; cco:ont00001787 |  | 478 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0002 | missing_in_spreadsheet |  |  | sosa:Sensor | http://www.w3.org/ns/sosa/Sensor | rdfs:subClassOf |  | bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Observation; cco:ont00001787 |  | 517 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0003 | missing_in_spreadsheet |  |  | sosa:hasFeatureOfInterest | http://www.w3.org/ns/sosa/hasFeatureOfInterest | rdfs:subPropertyOf |  | cco:ont00001921 |  | 59 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0004 | missing_in_spreadsheet |  |  | sosa:hasSample | http://www.w3.org/ns/sosa/hasSample | owl:propertyChainAxiom |  | bfo:BFO_0000084; cco:ont00001873 |  | 67 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0005 | missing_in_spreadsheet |  |  | sosa:isActedOnBy | http://www.w3.org/ns/sosa/isActedOnBy | rdfs:subPropertyOf |  | cco:ont00001886 |  | 77 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0006 | missing_in_spreadsheet |  |  | sosa:isFeatureOfInterestOf | http://www.w3.org/ns/sosa/isFeatureOfInterestOf | rdfs:subPropertyOf |  | cco:ont00001841 |  | 81 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0007 | missing_in_spreadsheet |  |  | sosa:isResultOf | http://www.w3.org/ns/sosa/isResultOf | rdfs:subPropertyOf |  | cco:ont00001816 |  | 86 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0008 | missing_in_spreadsheet |  |  | sosa:isSampleOf | http://www.w3.org/ns/sosa/isSampleOf | owl:propertyChainAxiom |  | bfo:BFO_0000101; cco:ont00001938 |  | 90 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0009 | missing_in_spreadsheet |  |  | sosa:madeByActuator | http://www.w3.org/ns/sosa/madeByActuator | rdfs:subPropertyOf |  | cco:ont00001833 |  | 100 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0010 | missing_in_spreadsheet |  |  | sosa:madeObservation | http://www.w3.org/ns/sosa/madeObservation | rdfs:subPropertyOf |  | cco:ont00001787 |  | 112 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0011 | missing_in_spreadsheet |  |  | sosa:madeSampling | http://www.w3.org/ns/sosa/madeSampling | rdfs:subPropertyOf |  | cco:ont00001787 |  | 116 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0012 | missing_in_spreadsheet |  |  | ssn-system:inCondition | http://www.w3.org/ns/ssn/systems/inCondition | owl:propertyChainAxiom |  | bfo:BFO_0000054; bfo:BFO_0000055; bfo:BFO_0000196; cco:ont00001819 |  | 187 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0013 | missing_in_spreadsheet |  |  | ssn:hasDeployment | http://www.w3.org/ns/ssn/hasDeployment | rdfs:subPropertyOf |  | bfo:BFO_0000056 |  | 138 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0014 | missing_in_spreadsheet |  |  | ssn:inDeployment | http://www.w3.org/ns/ssn/inDeployment | rdfs:subPropertyOf |  | bfo:BFO_0000056 |  | 155 | Reconcile this extra TTL mapping with the source spreadsheet row for the same term. |
| ISSUE-0015 | missing_in_ttl | Sample Relationship | 2 | sampling:hasSampleRelationship | http://www.w3.org/ns/sosa/sampling/hasSampleRelationship |  | schema:domainIncludes |  | sosa:Sample |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0016 | missing_in_ttl | Sample Relationship | 2 | sampling:hasSampleRelationship | http://www.w3.org/ns/sosa/sampling/hasSampleRelationship |  | schema:rangeIncludes |  | sampling:SampleRelationship |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0017 | missing_in_ttl | Common DPs | 2 | sosa:hasSimpleResult | http://www.w3.org/ns/sosa/hasSimpleResult |  | rdfs:subPropertyOf |  | owl:topDataProperty |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0018 | missing_in_ttl | Sample Relationship | 3 | sampling:natureOfRelationship | http://www.w3.org/ns/sosa/sampling/natureOfRelationship |  | schema:domainIncludes |  | sampling:SampleRelationship |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0019 | missing_in_ttl | Sample Relationship | 3 | sampling:natureOfRelationship | http://www.w3.org/ns/sosa/sampling/natureOfRelationship |  | schema:rangeIncludes |  | sampling:RelationshipNature |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0020 | missing_in_ttl | Common DPs | 3 | sosa:resultTime | http://www.w3.org/ns/sosa/resultTime |  | rdfs:subPropertyOf |  | owl:topDataProperty |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0021 | missing_in_ttl | Common OPs | 3 | ssn:deployedOnPlatform | http://www.w3.org/ns/ssn/deployedOnPlatform |  | rdfs:domain |  | ssn:Deployment |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0022 | missing_in_ttl | Common OPs | 3 | ssn:deployedOnPlatform | http://www.w3.org/ns/ssn/deployedOnPlatform |  | rdfs:range |  | sosa:Platform |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0023 | missing_in_ttl | Sample Relationship | 4 | sampling:relatedSample | http://www.w3.org/ns/sosa/sampling/relatedSample |  | schema:domainIncludes |  | sampling:SampleRelationship |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0024 | missing_in_ttl | Sample Relationship | 4 | sampling:relatedSample | http://www.w3.org/ns/sosa/sampling/relatedSample |  | schema:rangeIncludes |  | sosa:Sample |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0025 | missing_in_ttl | Common OPs | 4 | ssn:deployedSystem | http://www.w3.org/ns/ssn/deployedSystem |  | rdfs:domain |  | ssn:Deployment |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0026 | missing_in_ttl | Common OPs | 4 | ssn:deployedSystem | http://www.w3.org/ns/ssn/deployedSystem |  | rdfs:range |  | ssn:System |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0027 | missing_in_ttl | Sample Relationship | 5 | sampling:RelationshipNature | http://www.w3.org/ns/sosa/sampling/RelationshipNature |  | rdfs:subClassOf |  | cco:ont00000958 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0028 | missing_in_ttl | Common OPs | 5 | ssn:detects | http://www.w3.org/ns/ssn/detects |  | rdfs:domain |  | sosa:Sensor |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0029 | missing_in_ttl | Common OPs | 5 | ssn:detects | http://www.w3.org/ns/ssn/detects |  | rdfs:range |  | ssn:Stimulus |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0030 | missing_in_ttl | Sample Relationship | 6 | sampling:SampleRelationship | http://www.w3.org/ns/sosa/sampling/SampleRelationship |  | rdfs:subClassOf |  | cco:ont00000958 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0031 | missing_in_ttl | Sample Relationship | 6 | sampling:SampleRelationship | http://www.w3.org/ns/sosa/sampling/SampleRelationship |  | rdfs:subClassOf |  | owl:Restriction; owl:onProperty; owl:someValuesFrom; sosa:Sample; sampling:relatedSample |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0032 | missing_in_ttl | Sample Relationship | 6 | sampling:SampleRelationship | http://www.w3.org/ns/sosa/sampling/SampleRelationship |  | rdfs:subClassOf |  | owl:Restriction; owl:onProperty; owl:someValuesFrom; sampling:RelationshipNature; sampling:natureOfRelationship |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0033 | missing_in_ttl | Common OPs | 7 | ssn:hasDeployment | http://www.w3.org/ns/ssn/hasDeployment |  | owl:inverseOf |  | ssn:deployedSystem |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0034 | missing_in_ttl | Common OPs | 8 | sosa:hasFeatureOfInterest | http://www.w3.org/ns/sosa/hasFeatureOfInterest |  | rdfs:domain |  | owl:Class; owl:unionOf; sosa:Actuation; sosa:Observation; sosa:Sampling |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0035 | missing_in_ttl | Common OPs | 8 | sosa:hasFeatureOfInterest | http://www.w3.org/ns/sosa/hasFeatureOfInterest |  | rdfs:range |  | sosa:FeatureOfInterest |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0036 | missing_in_ttl | Common OPs | 11 | ssn:hasProperty | http://www.w3.org/ns/ssn/hasProperty |  | rdfs:subPropertyOf |  | bfo:BFO_0000196 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0037 | missing_in_ttl | Common OPs | 11 | ssn:hasProperty | http://www.w3.org/ns/ssn/hasProperty |  | rdfs:subPropertyOf |  | bfo:BFO_0000117 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0038 | missing_in_ttl | Common OPs | 13 | sosa:hasSample | http://www.w3.org/ns/sosa/hasSample |  | rdfs:domain |  | sosa:FeatureOfInterest |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0039 | missing_in_ttl | Common OPs | 13 | sosa:hasSample | http://www.w3.org/ns/sosa/hasSample |  | rdfs:range |  | sosa:Sample |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0040 | missing_in_ttl | Common OPs | 14 | ssn:hasSubSystem | http://www.w3.org/ns/ssn/hasSubSystem |  | rdfs:domain |  | ssn:System |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0041 | missing_in_ttl | Common OPs | 14 | ssn:hasSubSystem | http://www.w3.org/ns/ssn/hasSubSystem |  | rdfs:range |  | ssn:System |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0042 | missing_in_ttl | Common OPs | 14 | ssn:hasSubSystem | http://www.w3.org/ns/ssn/hasSubSystem |  | rdfs:subPropertyOf |  | bfo:BFO_0000178 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0043 | missing_in_ttl | Common OPs | 15 | sosa:hosts | http://www.w3.org/ns/sosa/hosts |  | owl:inverseOf |  | sosa:isHostedBy |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0044 | missing_in_ttl | Common OPs | 15 | sosa:hosts | http://www.w3.org/ns/sosa/hosts |  | rdfs:domain |  | sosa:Platform |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0045 | missing_in_ttl | Common OPs | 15 | sosa:hosts | http://www.w3.org/ns/sosa/hosts |  | rdfs:range |  | owl:Class; owl:unionOf; sosa:Platform; ssn:System |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0046 | missing_in_ttl | Common OPs | 15 | sosa:hosts | http://www.w3.org/ns/sosa/hosts |  | rdfs:subPropertyOf |  | bfo:BFO_0000054; bfo:BFO_0000057; bfo:BFO_0000196; owl:ObjectProperty; owl:propertyChainAxiom |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0047 | missing_in_ttl | Common OPs | 15 | sosa:hosts | http://www.w3.org/ns/sosa/hosts |  | rdfs:subPropertyOf |  | bfo:BFO_0000054; bfo:BFO_0000057; bfo:BFO_0000196; owl:ObjectProperty; owl:inverseOf; owl:propertyChainAxiom |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0048 | missing_in_ttl | Common Classes | 16 | sosa:Sampler | http://www.w3.org/ns/sosa/Sampler |  | owl:equivalentClass |  | bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000055; bfo:BFO_0000196; sosa:Sampling; cco:ont00001787 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0049 | missing_in_ttl | Common OPs | 16 | ssn:implementedBy | http://www.w3.org/ns/ssn/implementedBy |  | rdfs:subPropertyOf |  | owl:inverseOf; owl:propertyChainAxiom; cco:ont00001787; cco:ont00001920 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0050 | missing_in_ttl | Common OPs | 17 | ssn:implements | http://www.w3.org/ns/ssn/implements |  | owl:inverseOf |  | ssn:implementedBy |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0051 | missing_in_ttl | Common Classes | 18 | sosa:Sensor | http://www.w3.org/ns/sosa/Sensor |  | owl:equivalentClass |  | bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0052 | missing_in_ttl | Common OPs | 18 | ssn:inDeployment | http://www.w3.org/ns/ssn/inDeployment |  | owl:inverseOf |  | ssn:deployedOnPlatform |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0053 | missing_in_ttl | Common OPs | 19 | sosa:isActedOnBy | http://www.w3.org/ns/sosa/isActedOnBy |  | owl:inverseOf |  | sosa:actsOnProperty |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0054 | missing_in_ttl | Common OPs | 20 | sosa:isFeatureOfInterestOf | http://www.w3.org/ns/sosa/isFeatureOfInterestOf |  | owl:inverseOf |  | sosa:hasFeatureOfInterest |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0055 | missing_in_ttl | Common OPs | 21 | sosa:isHostedBy | http://www.w3.org/ns/sosa/isHostedBy |  | owl:inverseOf |  | sosa:hosts |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0056 | missing_in_ttl | Common OPs | 22 | sosa:isObservedBy | http://www.w3.org/ns/sosa/isObservedBy |  | owl:inverseOf |  | sosa:observes |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0057 | missing_in_ttl | Common OPs | 23 | ssn:isPropertyOf | http://www.w3.org/ns/ssn/isPropertyOf |  | owl:inverseOf |  | ssn:hasProperty |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0058 | missing_in_ttl | Common OPs | 24 | ssn:isProxyFor | http://www.w3.org/ns/ssn/isProxyFor |  | rdfs:domain |  | ssn:Stimulus |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0059 | missing_in_ttl | Common OPs | 24 | ssn:isProxyFor | http://www.w3.org/ns/ssn/isProxyFor |  | rdfs:range |  | ssn:Property |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0060 | missing_in_ttl | Common OPs | 25 | sosa:isResultOf | http://www.w3.org/ns/sosa/isResultOf |  | owl:inverseOf |  | sosa:hasResult |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0061 | missing_in_ttl | Common OPs | 26 | sosa:isSampleOf | http://www.w3.org/ns/sosa/isSampleOf |  | owl:inverseOf |  | sosa:hasSample |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0062 | missing_in_ttl | Common OPs | 28 | sosa:madeByActuator | http://www.w3.org/ns/sosa/madeByActuator |  | owl:inverseOf |  | sosa:madeActuation |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0063 | missing_in_ttl | Common OPs | 29 | sosa:madeBySampler | http://www.w3.org/ns/sosa/madeBySampler |  | rdfs:domain |  | sosa:Sampling |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0064 | missing_in_ttl | Common OPs | 29 | sosa:madeBySampler | http://www.w3.org/ns/sosa/madeBySampler |  | rdfs:range |  | sosa:Sampler |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0065 | missing_in_ttl | Common OPs | 30 | sosa:madeBySensor | http://www.w3.org/ns/sosa/madeBySensor |  | rdfs:domain |  | sosa:Observation |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0066 | missing_in_ttl | Common OPs | 30 | sosa:madeBySensor | http://www.w3.org/ns/sosa/madeBySensor |  | rdfs:range |  | sosa:Sensor |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0067 | missing_in_ttl | Common OPs | 31 | sosa:madeObservation | http://www.w3.org/ns/sosa/madeObservation |  | owl:inverseOf |  | sosa:madeBySensor |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0068 | missing_in_ttl | Common OPs | 32 | sosa:madeSampling | http://www.w3.org/ns/sosa/madeSampling |  | owl:inverseOf |  | sosa:madeBySampler |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0069 | missing_in_ttl | Common OPs | 33 | sosa:observedProperty | http://www.w3.org/ns/sosa/observedProperty |  | rdfs:domain |  | sosa:Observation |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0070 | missing_in_ttl | Common OPs | 33 | sosa:observedProperty | http://www.w3.org/ns/sosa/observedProperty |  | rdfs:range |  | ssn:Property |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0071 | missing_in_ttl | Common OPs | 34 | sosa:observes | http://www.w3.org/ns/sosa/observes |  | rdfs:domain |  | sosa:Sensor |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0072 | missing_in_ttl | Common OPs | 34 | sosa:observes | http://www.w3.org/ns/sosa/observes |  | rdfs:range |  | ssn:Property |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0073 | missing_in_ttl | Common OPs | 34 | sosa:observes | http://www.w3.org/ns/sosa/observes |  | rdfs:subPropertyOf |  | bfo:BFO_0000057 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0074 | missing_in_ttl | Common OPs | 35 | sosa:phenomenonTime | http://www.w3.org/ns/sosa/phenomenonTime |  | rdfs:range |  | time:TemporalEntity |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |
| ISSUE-0075 | missing_in_ttl | Common OPs | 36 | sosa:usedProcedure | http://www.w3.org/ns/sosa/usedProcedure |  | rdfs:subPropertyOf |  | cco:ont00001920 |  | Add or revise the TTL mapping only after confirming the spreadsheet row is authoritative. |

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
