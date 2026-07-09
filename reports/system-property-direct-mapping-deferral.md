# SystemProperty Direct Mapping Deferral

## Scope

This report documents the implementation of the recommendation from `reports/system-property-mapping-simplification-evaluation.md`.

The branch defers the direct active `ssn-system:SystemProperty` class-expression mapping. It does not edit source imports, does not add `sosa:madeByActuator rdfs:range sosa:Actuator .`, and does not claim to resolve the separate `madeByActuator` range redundancy discrepancy.

## Baseline Before This Branch

The starting baseline for this branch was the current stable validation baseline:

| Check | Baseline |
| --- | --- |
| Validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 71 |
| Mapping audit issues | 2 expected `sosa:Sensor` version-alignment issues only |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 77 |
| ELK property-chain expectations | 5 |
| ELK restriction expectations | 2 |
| Active direct mappings not covered | 0 |
| Active property-chain mappings not covered | 0 |
| Active restriction mappings not covered | 0 |
| HermiT M2 baseline | Clean under established cleanup conditions |

## Source Report Used

The controlling evaluation report is:

`reports/system-property-mapping-simplification-evaluation.md`

That report found that:

- the active `SystemProperty` mapping was HermiT-clean;
- removing only the `prescribed_by some ArtifactFunctionSpecification` branch was HermiT-clean;
- removing the direct `SystemProperty` class-expression mapping entirely was HermiT-clean;
- the broader target, `BFO specifically dependent continuant OR BFO Process Profile`, remained entailed without the direct `SystemProperty` mapping;
- neither simplification changed the separate `madeByActuator` range behavior.

## TTL Mapping Before

The active mapping before this branch was:

```ttl
###  http://www.w3.org/ns/ssn/systems/SystemProperty
<http://www.w3.org/ns/ssn/systems/SystemProperty> rdf:type owl:Class ;
                                                  rdfs:subClassOf [ owl:intersectionOf ( [ rdf:type owl:Class ;
                                                                                           owl:unionOf ( <http://purl.obolibrary.org/obo/BFO_0000020>
                                                                                                         <http://purl.obolibrary.org/obo/BFO_0000144>
                                                                                                       )
                                                                                         ]
                                                                                         [ rdf:type owl:Restriction ;
                                                                                           owl:onProperty <https://www.commoncoreontologies.org/ont00001920> ;
                                                                                           owl:someValuesFrom <https://www.commoncoreontologies.org/ont00000118>
                                                                                         ]
                                                                                       ) ;
                                                                    rdf:type owl:Class
                                                                  ] .
```

In shorthand, this asserted:

```text
SystemProperty subClassOf
  (BFO specifically dependent continuant OR BFO Process Profile)
  AND (cco:prescribed_by some cco:ArtifactFunctionSpecification)
```

## TTL Mapping After

The direct class-expression mapping is now deferred:

```ttl
###  http://www.w3.org/ns/ssn/systems/SystemProperty
<http://www.w3.org/ns/ssn/systems/SystemProperty> rdf:type owl:Class .
# Direct class-expression mapping deferred; broader typing is inherited via ssn:Property.
```

No direct active BFO/CCO class-expression mapping is asserted for `ssn-system:SystemProperty` in `SSN2BFO.ttl`.

## Why The Broader Union Is Still Covered

The imported source ontology asserts:

```ttl
ssn-system:SystemProperty rdfs:subClassOf ssn:Property .
```

The active `ssn:Property` mapping in `SSN2BFO.ttl` asserts:

```ttl
<http://www.w3.org/ns/ssn/Property> owl:equivalentClass [
  owl:unionOf (
    <http://purl.obolibrary.org/obo/BFO_0000020>
    <http://purl.obolibrary.org/obo/BFO_0000144>
  )
] .
```

Therefore `SystemProperty` inherits the broader target:

```text
BFO specifically dependent continuant OR BFO Process Profile
```

without a separate direct `SystemProperty` class-expression mapping.

## Why The Prescribed-By Branch Was Deferred

The branch:

```text
cco:prescribed_by some cco:ArtifactFunctionSpecification
```

was over-specific for the imported source axioms. The `imports/ssn-systems.ttl` source context defines `SystemProperty` as an `ssn:Property` with inverse `hasSystemProperty` restrictions, but does not assert that every `SystemProperty` is prescribed by an artifact function specification.

Deferring the direct mapping removes that additional design-intent commitment while preserving the broader inherited typing through `ssn:Property`.

## Workbook Changes

Only `Current_SOSA-SSN to BFO-CCO.xlsx`, sheet `System Capability`, row 32 was changed.

Preserved cells:

| Cell | Value |
| --- | --- |
| `A32` | `ssn-system:SystemProperty` |
| `B32` | Source definition preserved |
| `C32` | Existing BFO definition text preserved |

Changed cells:

| Cell | Before | After |
| --- | --- | --- |
| `D32` | `Every ssn-system:SystemProperty is either a BFO:SpecificallyDependentContinuant or a BFO:ProcessProfile that is prescribed by at least one CCO:ArtifactFunctionSpecification.` | `No direct active BFO/CCO class-expression mapping is asserted for ssn-system:SystemProperty; broader typing is inherited via ssn:Property.` |
| `E32` | `subClassOf (bfo:SpecificallyDependentContinuant or bfo:ProcessProfile) and cco:prescribed_by some cco:ArtifactFunctionSpecification` | empty |
| `F32` | Rationale for the prior direct class-expression mapping | `Direct SystemProperty class-expression mapping deferred/removed. Broader target (specifically dependent continuant OR Process Profile) is inherited via ssn:Property. The prescribed_by some ArtifactFunctionSpecification branch is over-specific and not supported by imported ssn-systems.ttl source axioms. This change does not add sosa:madeByActuator rdfs:range sosa:Actuator and does not resolve the separate madeByActuator range redundancy discrepancy.` |

## HermiT Edited-Graph Validation

Temporary directory:

`/tmp/ssn-to-bfo-system-property-deferral`

Graph construction:

- parsed `imports/cco.ttl`;
- parsed `imports/ssn.ttl`;
- parsed `imports/ssn-systems.ttl`;
- parsed edited `SSN2BFO.ttl`;
- removed all `owl:imports` triples;
- removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- removed `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Result:

| Field | Result |
| --- | --- |
| Graph path | `/tmp/ssn-to-bfo-system-property-deferral/edited-graph.ttl` |
| Triple count | 15,510 |
| `owl:imports` triples removed | 5 |
| Sample simplicity triples removed | 2 |
| HermiT return code | 0 |
| Reasoned output produced | yes |
| Reasoned output path | `/tmp/ssn-to-bfo-system-property-deferral/edited-graph-reasoned.ttl` |
| `owl:Nothing` count | 0 |
| Unsat count | 0 |
| Unsat set | empty |
| Sample simplicity blocker | did not reappear |

The edited graph remains HermiT-clean under the established M2 cleanup conditions.

## Regenerated Reports

`reports/mapping-consistency-audit.md` was regenerated.

The regenerated audit reports:

| Field | Result |
| --- | --- |
| `ttl_candidate_mapping_assertions` | 70 |
| Total issues | 2 |
| Issue categories | 1 `missing_in_spreadsheet`, 1 `missing_in_ttl` |
| Unexpected issues | none |

The two remaining audit issues are the expected `sosa:Sensor` version-alignment issues.

`reports/mapping-consistency-audit.csv` did not change.

`reports/elk-instance-mapping-entailments.md` was checked and did not change. The ELK entailment test still reports:

| Field | Result |
| --- | --- |
| Direct class expectations | 6 |
| Direct property expectations | 77 |
| Property-chain expectations | 5 |
| Restriction expectations | 2 |
| Total expectation failures | 0 |
| Active direct mappings not covered | 0 |
| Active property-chain mappings not covered | 0 |
| Active restriction mappings not covered | 0 |

## Explicit Non-Changes

This branch does not add:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

This branch does not claim to solve the separate `madeByActuator` range issue.

This branch does not add SWRL, SPARQL, SHACL, or COMS materialization.

This branch does not reactivate any failed BFO/CCO mappings.

## Conclusion

The direct `ssn-system:SystemProperty` class-expression mapping has been deferred while preserving inherited broader typing through `ssn:Property`.

The edited M2 graph is HermiT-clean, the standard audit still has only the expected `sosa:Sensor` issues, and the ELK entailment report remains unchanged.
