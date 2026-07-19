# Mapping Consistency Target Mismatch Review

This is a review-only note for current `target_mismatch` rows in `reports/mapping-consistency-audit.csv`. It does not create, infer, revise, normalize, move, split, or suggest ontology mappings.

Sources inspected:

- `reports/mapping-consistency-audit.csv`
- `SSN2BFO.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`

The audit CSV is the controlling source for issue IDs. Earlier stale issue IDs are not used here.

## ISSUE-0024: ssn-system:ActuationRange

Metadata:

- Issue ID: `ISSUE-0024`
- Sheet: `System Capability`
- Spreadsheet row: `3`
- Source term: `ssn-system:ActuationRange`
- Source IRI: `http://www.w3.org/ns/ssn/systems/ActuationRange`
- TTL predicate: `rdfs:subClassOf`
- Spreadsheet relation: `rdfs:subClassOf`
- TTL line: `632`

TTL excerpt:

```ttl
632 ###  http://www.w3.org/ns/ssn/systems/ActuationRange
633 <http://www.w3.org/ns/ssn/systems/ActuationRange> rdf:type owl:Class ;
634                                                   rdfs:subClassOf [ owl:intersectionOf ( <http://purl.obolibrary.org/obo/BFO_0000034>
635                                                                                          [ rdf:type owl:Restriction ;
636                                                                                            owl:onProperty <http://purl.obolibrary.org/obo/BFO_0000054> ;
637                                                                                            owl:someValuesFrom [ owl:intersectionOf ( <http://www.w3.org/ns/sosa/Actuation>
638                                                                                                                                      [ owl:intersectionOf ( [ rdf:type owl:Class ;
639                                                                                                                                                               owl:unionOf ( [ rdf:type owl:Restriction ;
640                                                                                                                                                                               owl:onProperty <http://www.w3.org/ns/ssn/hasOutput> ;
641                                                                                                                                                                               owl:someValuesFrom <http://purl.obolibrary.org/obo/BFO_0000020>
642                                                                                                                                                                             ]
643                                                                                                                                                                             [ rdf:type owl:Restriction ;
644                                                                                                                                                                               owl:onProperty <https://www.commoncoreontologies.org/ont00001834> ;
645                                                                                                                                                                               owl:someValuesFrom <http://purl.obolibrary.org/obo/BFO_0000144>
646                                                                                                                                                                             ]
647                                                                                                                                                                           )
648                                                                                                                                                             ]
649                                                                                                                                                             [ rdf:type owl:Restriction ;
650                                                                                                                                                               owl:onProperty <https://www.commoncoreontologies.org/ont00001920> ;
651                                                                                                                                                               owl:someValuesFrom <https://www.commoncoreontologies.org/ont00000118>
652                                                                                                                                                             ]
```

Spreadsheet excerpts:

- Definition: "The set of values that the Actuator can return as the Result of an Actuation under the defined Conditions with the defined system properties."
- BFO Definition: "A function of a system whose realizations determine the range of property values that can be produced or affected by actuation processes under specified conditions."
- Natural Language OWL: "Every ssn-system:ActuationRange is a BFO:Function that has a realization which is a sosa:Actuation that either has output some BFO:SpecificallyDependentContinuant or affects some BFO:ProcessProfile and is prescribed by a CCO:ArtifactFunctionSpecification."
- OWL Axiom: `subClassOf bfo:Function and bfo:has_realization some (sosa:Actuation and (((cco:has_output some bfo:SpecificallyDependentContinuant) or (cco:affects some bfo:ProcessProfile)) and cco:prescribed_by some cco:ArtifactFunctionSpecification))`
- Reasoning: "ActuationRange is modeled as a function because it characterizes the system's capacity to bring about changes during actuation. The realization in actuation processes reflects that ranges are manifested through actual system behavior prescribed by functional specifications."

Audit target summaries:

- TTL target summary: `bfo:BFO_0000020; bfo:BFO_0000034; bfo:BFO_0000054; bfo:BFO_0000144; sosa:Actuation; ssn:hasOutput; cco:ont00000118; cco:ont00001834; cco:ont00001920`
- Spreadsheet target summary: `bfo:BFO_0000020; bfo:BFO_0000034; bfo:BFO_0000054; bfo:BFO_0000144; sosa:Actuation; cco:ont00000118; cco:ont00001834; cco:ont00001920; cco:ont00001986`
- Exact target difference detected by the audit: TTL target includes `ssn:hasOutput`; spreadsheet target includes `cco:ont00001986`.

Review questions:

- Does the audit difference reflect an intentional distinction between the TTL expression and the spreadsheet OWL Axiom?
- Is either side stale relative to the intended source of truth?
- Could this be an audit parser or prefix-resolution limitation rather than a content mismatch?
- Where should any later reviewed change be made, if a change is approved?

Possible resolution location:

- [ ] spreadsheet only
- [x] TTL only
- [ ] both
- [ ] audit parser limitation
- [ ] needs ontology review

Human decision fields:

- Decision: Spreadsheet is correct.
- Selected resolution: TTL only.
- Reviewer:
- Date:
- Rationale: The intended relation is cco:ont00001986, not ssn:hasOutput.
- Follow-up issue/PR: Update the ssn-system:ActuationRange mapping in SSN2BFO.ttl to use cco:ont00001986 where the mismatching expression currently uses ssn:hasOutput.

## ISSUE-0029: sosa:Actuator

Metadata:

- Issue ID: `ISSUE-0029`
- Sheet: `Common Classes`
- Spreadsheet row: `4`
- Source term: `sosa:Actuator`
- Source IRI: `http://www.w3.org/ns/sosa/Actuator`
- TTL predicate: `rdfs:subClassOf`
- Spreadsheet relation: `rdfs:subClassOf`
- TTL line: `326`

TTL excerpt:

```ttl
326 ###  http://www.w3.org/ns/sosa/Actuator
327 <http://www.w3.org/ns/sosa/Actuator> rdf:type owl:Class ;
328                                      rdfs:subClassOf [ owl:intersectionOf ( <http://purl.obolibrary.org/obo/BFO_0000040>
329                                                                             [ rdf:type owl:Restriction ;
330                                                                               owl:onProperty <http://purl.obolibrary.org/obo/BFO_0000196> ;
331                                                                               owl:someValuesFrom [ owl:intersectionOf ( <http://purl.obolibrary.org/obo/BFO_0000017>
332                                                                                                                         [ rdf:type owl:Restriction ;
333                                                                                                                           owl:onProperty <http://purl.obolibrary.org/obo/BFO_0000054> ;
334                                                                                                                           owl:someValuesFrom <http://www.w3.org/ns/sosa/Actuation>
335                                                                                                                         ]
336                                                                                                                       ) ;
337                                                                                                    rdf:type owl:Class
338                                                                                                  ]
339                                                                             ]
340                                                                             [ rdf:type owl:Restriction ;
341                                                                               owl:onProperty <https://www.commoncoreontologies.org/ont00001787> ;
342                                                                               owl:someValuesFrom <http://www.w3.org/ns/sosa/Actuation>
343                                                                             ]
344                                                                           ) ;
345                                                        rdf:type owl:Class
346                                                      ] .
```

Spreadsheet excerpts:

- Definition: "A device that is used by, or implements, an (Actuation) Procedure that changes the state of the world."
- BFO Definition: "A bfo:MaterialEntity that bears a bfo:RealizableEntity which is realized in a sosa:Actuation and that functions as an agent in that sosa:Actuation."
- Natural Language OWL: "Every sosa:Actuator is a bfo:MaterialEntity that bears a bfo:RealizableEntity realized in some sosa:Actuation and that is an agent in some sosa:Actuation."
- OWL Axiom:

```text
subClassOf bfo:MaterialEntity
    and (bfo:bearer_of some
         (bfo:RealizableEntity and (bfo:realizes some sosa:Actuation)))
    and (cco:agent_in some sosa:Actuation)
```

- Reasoning: "sosa:Actuator is a bfo:MaterialEntity because actuators are physical devices. The bfo:RealizableEntity it bears is realized in actuation processes, capturing the functional rather than purely structural definition of actuators. The cco:agent_in restriction captures that the actuator plays a causative role in the actuation."

Audit target summaries:

- TTL target summary: `bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Actuation; cco:ont00001787`
- Spreadsheet target summary: `bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000055; bfo:BFO_0000196; sosa:Actuation; cco:ont00001787`
- Exact target difference detected by the audit: TTL target includes `bfo:BFO_0000054`; spreadsheet target includes `bfo:BFO_0000055`.

Review questions:

- Does the audit difference reflect an intentional distinction between the TTL expression and the spreadsheet OWL Axiom?
- Is either side stale relative to the intended source of truth?
- Could this be an audit parser or prefix-resolution limitation rather than a content mismatch?
- Where should any later reviewed change be made, if a change is approved?

Possible resolution location:

- [x] spreadsheet only
- [ ] TTL only
- [ ] both
- [ ] audit parser limitation
- [ ] needs ontology review

Human decision fields:

- Decision: TTL is correct.
- Selected resolution: spreadsheet only.
- Reviewer:
- Date:
- Rationale: The intended BFO relation is BFO_0000054, not BFO_0000055.
- Follow-up issue/PR: Update the spreadsheet OWL Axiom for sosa:Actuator to use bfo:BFO_0000054.

## ISSUE-0057: sosa:Sampling

Metadata:

- Issue ID: `ISSUE-0057`
- Sheet: `Common Classes`
- Spreadsheet row: `17`
- Source term: `sosa:Sampling`
- Source IRI: `http://www.w3.org/ns/sosa/Sampling`
- TTL predicate: `owl:equivalentClass`
- Spreadsheet relation: `owl:equivalentClass`
- TTL line: `501`

TTL excerpt:

```ttl
501 ###  http://www.w3.org/ns/sosa/Sampling
502 <http://www.w3.org/ns/sosa/Sampling> rdf:type owl:Class ;
503                                      owl:equivalentClass [ owl:intersectionOf ( <https://www.commoncoreontologies.org/ont00000228>
504                                                                                 [ rdf:type owl:Restriction ;
505                                                                                   owl:onProperty <http://www.w3.org/ns/ssn/hasOutput> ;
506                                                                                   owl:someValuesFrom <http://www.w3.org/ns/sosa/Sample>
507                                                                                 ]
508                                                                                 [ rdf:type owl:Restriction ;
509                                                                                   owl:onProperty <https://www.commoncoreontologies.org/ont00001920> ;
510                                                                                   owl:someValuesFrom <http://www.w3.org/ns/sosa/Procedure>
511                                                                                 ]
512                                                                               ) ;
513                                                            rdf:type owl:Class
514                                                          ] .
```

Spreadsheet excerpts:

- Definition: "An act of Sampling carries out a sampling Procedure to create or transform one or more samples."
- BFO Definition: "A cco:PlannedAct in which a sosa:Procedure is carried out to create or transform one or more sosa:Samples."
- Natural Language OWL: "An individual is a sosa:Sampling if and only if it is a cco:PlannedAct that is prescribed by some sosa:Procedure and has output some sosa:Sample."
- OWL Axiom: `equivalentTo cco:PlannedAct and (cco:prescribed_by some sosa:Procedure) and (cco:has_output some sosa:Sample)`
- Reasoning: "sosa:Sampling is modeled as a cco:PlannedAct because it is intentionally carried out according to a procedure to create or transform samples. The equivalentTo axiom captures that being prescribed by a procedure and producing a sample as output is both necessary and sufficient for being a sampling."

Audit target summaries:

- TTL target summary: `sosa:Procedure; sosa:Sample; ssn:hasOutput; cco:ont00000228; cco:ont00001920`
- Spreadsheet target summary: `sosa:Procedure; sosa:Sample; cco:ont00000228; cco:ont00001920; cco:ont00001986`
- Exact target difference detected by the audit: TTL target includes `ssn:hasOutput`; spreadsheet target includes `cco:ont00001986`.

Review questions:

- Does the audit difference reflect an intentional distinction between the TTL expression and the spreadsheet OWL Axiom?
- Is either side stale relative to the intended source of truth?
- Could this be an audit parser or prefix-resolution limitation rather than a content mismatch?
- Where should any later reviewed change be made, if a change is approved?

Possible resolution location:

- [ ] spreadsheet only
- [x] TTL only
- [ ] both
- [ ] audit parser limitation
- [ ] needs ontology review

Human decision fields:

- Decision: Spreadsheet is correct.
- Selected resolution: TTL only.
- Reviewer:
- Date:
- Rationale: The intended relation is cco:ont00001986, not ssn:hasOutput.
- Follow-up issue/PR: Update the sosa:Sampling mapping in SSN2BFO.ttl to use cco:ont00001986 where the mismatching expression currently uses ssn:hasOutput.

## ISSUE-0062: ssn-system:OperatingRange

Metadata:

- Issue ID: `ISSUE-0062`
- Sheet: `System Capability`
- Spreadsheet row: `21`
- Source term: `ssn-system:OperatingRange`
- Source IRI: `http://www.w3.org/ns/ssn/systems/OperatingRange`
- TTL predicate: `rdfs:subClassOf`
- Spreadsheet relation: `rdfs:subClassOf`
- TTL line: `952`

TTL excerpt:

```ttl
952 ###  http://www.w3.org/ns/ssn/systems/OperatingRange
953 <http://www.w3.org/ns/ssn/systems/OperatingRange> rdf:type owl:Class ;
954                                                   rdfs:subClassOf [ owl:intersectionOf ( [ rdf:type owl:Class ;
955                                                                                            owl:unionOf ( <http://purl.obolibrary.org/obo/BFO_0000020>
956                                                                                                          <http://purl.obolibrary.org/obo/BFO_0000144>
957                                                                                                        )
958                                                                                          ]
959                                                                                          [ rdf:type owl:Restriction ;
960                                                                                            owl:onProperty <https://www.commoncoreontologies.org/ont00001920> ;
961                                                                                            owl:someValuesFrom <https://www.commoncoreontologies.org/ont00000118>
962                                                                                          ]
963                                                                                        ) ;
964                                                                     rdf:type owl:Class
965                                                                   ] .
```

Spreadsheet excerpts:

- Definition: "Describes normal OperatingProperties of a System under some specified Conditions. For example, to the power requirement or maintenance schedule of a System under a specified temperature range. In the absence of OperatingProperties, it simply describes the Conditions in which a System is expected to operate. The System continues to operate as defined using SystemCapability. If, however, the SurvivalRange is violated, the System is 'damaged' and SystemCapability specifications may no longer hold."
- BFO Definition: "A specifically dependent continuant or process profile that characterizes the conditions under which a system is expected to operate normally."
- Natural Language OWL: "Every ssn-system:OperatingRange is either a BFO:SpecificallyDependentContinuant or a BFO:ProcessProfile that is prescribed by a CCO:ArtifactDesign."
- OWL Axiom: `subClassOf (bfo:SpecificallyDependentContinuant or bfo:ProcessProfile) and cco:prescribed_by some cco:ArtifactDesign`
- Reasoning: "OperatingRange is modeled as a specifically dependent continuant or process profile because it describes permissible conditions for normal operation rather than behavior itself. The link to ArtifactDesign reflects that operating ranges are design-specified constraints."

Audit target summaries:

- TTL target summary: `bfo:BFO_0000020; bfo:BFO_0000144; cco:ont00000118; cco:ont00001920`
- Spreadsheet target summary: `bfo:BFO_0000020; bfo:BFO_0000144; cco:ont00000319; cco:ont00001920`
- Exact target difference detected by the audit: TTL target includes `cco:ont00000118`; spreadsheet target includes `cco:ont00000319`.

Review questions:

- Does the audit difference reflect an intentional distinction between the TTL expression and the spreadsheet OWL Axiom?
- Is either side stale relative to the intended source of truth?
- Could this be an audit parser or prefix-resolution limitation rather than a content mismatch?
- Where should any later reviewed change be made, if a change is approved?

Possible resolution location:

- [ ] spreadsheet only
- [x] TTL only
- [ ] both
- [ ] audit parser limitation
- [ ] needs ontology review

Human decision fields:

- Decision: Spreadsheet is correct.
- Selected resolution: TTL only.
- Reviewer:
- Date:
- Rationale: The intended target is cco:ont00000319, not cco:ont00000118.
- Follow-up issue/PR: Update the ssn-system:OperatingRange mapping in SSN2BFO.ttl to use cco:ont00000319 where the mismatching expression currently uses cco:ont00000118.

## Explicit Non-Actions

- No actual mapping corrections are written in this note.
- This note does not say whether the TTL or spreadsheet side is correct.
- This note does not edit mappings, source spreadsheets, audit outputs, audit scripts, imports, release files, `src` mapping files, or `sosa-next` files.
