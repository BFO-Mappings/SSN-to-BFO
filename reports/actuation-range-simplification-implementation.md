# `ssn-system:ActuationRange` Simplification Implementation

## Scope

This report documents the mapping-change implementation of the independently justified `ssn-system:ActuationRange` simplification identified in:

```text
reports/actuation-range-simplification-evaluation.md
```

This branch does not add:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

It also does not claim to solve the separate `madeByActuator` range redundancy discrepancy.

## Baseline Before This Branch

Current stable baseline before this branch:

| Check | Baseline |
|---|---:|
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 71 |
| audit issues | 2 expected `sosa:Sensor` version-alignment issues only |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 77 |
| ELK property-chain expectations | 5 |
| ELK restriction expectations | 2 |
| active direct/property-chain/restriction mappings not covered | 0 |
| HermiT M2 baseline under established cleanup | clean |

## TTL Mapping Before

Before this branch, the active `ssn-system:ActuationRange` mapping included a union between:

- `cco:has_output some bfo:BFO_0000020`; and
- `cco:affects some bfo:BFO_0000144`.

Exact mapping shape before:

```ttl
<http://www.w3.org/ns/ssn/systems/ActuationRange> rdf:type owl:Class ;
  rdfs:subClassOf [ owl:intersectionOf (
    <http://purl.obolibrary.org/obo/BFO_0000034>
    [ rdf:type owl:Restriction ;
      owl:onProperty <http://purl.obolibrary.org/obo/BFO_0000054> ;
      owl:someValuesFrom [ owl:intersectionOf (
        <http://www.w3.org/ns/sosa/Actuation>
        [ owl:intersectionOf (
          [ rdf:type owl:Class ;
            owl:unionOf (
              [ rdf:type owl:Restriction ;
                owl:onProperty <https://www.commoncoreontologies.org/ont00001986> ;
                owl:someValuesFrom <http://purl.obolibrary.org/obo/BFO_0000020> ]
              [ rdf:type owl:Restriction ;
                owl:onProperty <https://www.commoncoreontologies.org/ont00001834> ;
                owl:someValuesFrom <http://purl.obolibrary.org/obo/BFO_0000144> ]
            ) ]
          [ rdf:type owl:Restriction ;
            owl:onProperty <https://www.commoncoreontologies.org/ont00001920> ;
            owl:someValuesFrom <https://www.commoncoreontologies.org/ont00000118> ]
        ) ; rdf:type owl:Class ]
      ) ; rdf:type owl:Class ]
    ]
  ) ; rdf:type owl:Class ] .
```

## TTL Mapping After

The active mapping now removes the suspicious `cco:affects some bfo:BFO_0000144` branch and keeps the HermiT-clean output-only simplification from the evaluation report.

Exact mapping shape after:

```ttl
<http://www.w3.org/ns/ssn/systems/ActuationRange> rdf:type owl:Class ;
  rdfs:subClassOf [ owl:intersectionOf (
    <http://purl.obolibrary.org/obo/BFO_0000034>
    [ rdf:type owl:Restriction ;
      owl:onProperty <http://purl.obolibrary.org/obo/BFO_0000054> ;
      owl:someValuesFrom [ owl:intersectionOf (
        <http://www.w3.org/ns/sosa/Actuation>
        [ owl:intersectionOf (
          [ rdf:type owl:Restriction ;
            owl:onProperty <https://www.commoncoreontologies.org/ont00001986> ;
            owl:someValuesFrom <http://purl.obolibrary.org/obo/BFO_0000020> ]
          [ rdf:type owl:Restriction ;
            owl:onProperty <https://www.commoncoreontologies.org/ont00001920> ;
            owl:someValuesFrom <https://www.commoncoreontologies.org/ont00000118> ]
        ) ; rdf:type owl:Class ]
      ) ; rdf:type owl:Class ]
    ]
  ) ; rdf:type owl:Class ] .
```

In shorthand:

```text
Function
and has_realization some (
  sosa:Actuation
  and has_output some specifically dependent continuant
  and prescribed_by some artifact function specification
)
```

## Workbook Changes

Workbook changed:

```text
Current_SOSA-SSN to BFO-CCO.xlsx
```

Sheet and row:

```text
System Capability row 3
```

Cells changed:

| Cell | New value |
|---|---|
| `D3` | `Every ssn-system:ActuationRange is a BFO:Function that has a realization which is a sosa:Actuation that has output some BFO:SpecificallyDependentContinuant and is prescribed by a CCO:ArtifactFunctionSpecification.` |
| `E3` | `subClassOf bfo:Function and bfo:has_realization some (sosa:Actuation and ((cco:has_output some bfo:SpecificallyDependentContinuant) and (cco:prescribed_by some cco:ArtifactFunctionSpecification)))` |
| `F3` | `Mapping simplified by removing the overstrong/suspicious affects some ProcessProfile branch. The simplified expression remains HermiT-clean. This change does not add sosa:madeByActuator rdfs:range sosa:Actuator and does not resolve the separate madeByActuator range redundancy discrepancy.` |

Cells `A3`, `B3`, and `C3` were left unchanged.

## HermiT Edited-Graph Result

Temporary files were written under:

```text
/tmp/ssn-to-bfo-actuation-range-simplification-implementation
```

The edited M2 graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Then the graph removed:

```text
all owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty
sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-actuation-range-simplification-implementation/edited-m2.ttl --output /tmp/ssn-to-bfo-actuation-range-simplification-implementation/edited-m2-reasoned.ttl
```

Result:

| Field | Value |
|---|---:|
| graph path | `/tmp/ssn-to-bfo-actuation-range-simplification-implementation/edited-m2.ttl` |
| triple count | 15526 |
| return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | none |
| sample simplicity blocker reappeared | no |

## Audit And ELK Results

`make audit-write` was run after the TTL and workbook edits.

Mapping audit result:

| Field | Value |
|---|---:|
| inspected sheets | 5 |
| spreadsheet rows | 93 |
| `ttl_candidate_mapping_assertions` | 71 |
| total issues | 2 |
| `missing_in_spreadsheet` | 1 |
| `missing_in_ttl` | 1 |

The two issues remain the expected `sosa:Sensor` version-alignment issues only.

The mapping audit markdown changed because the branch/commit context changed and the blank-node ignored-triple count changed from `904` to `895`. The audit CSV was regenerated but its content did not change.

The ELK instance mapping entailment report was regenerated to a temporary file and compared with the canonical report. Content was unchanged, so `reports/elk-instance-mapping-entailments.md` was not modified.

ELK temporary result:

| Check | Result |
|---|---:|
| example files tested | 16 |
| ROBOT pass/fail | 16/0 |
| direct class expectations checked | 6 |
| direct property expectations checked | 77 |
| property-chain expectations checked | 5 |
| restriction expectations checked | 2 |
| expectation failures | 0 |
| active direct mappings not covered | 0 |
| active property-chain mappings not covered | 0 |
| active restriction mappings not covered | 0 |

## Conclusion

The `ssn-system:ActuationRange` mapping was simplified by removing the suspicious `cco:affects some bfo:BFO_0000144` branch while preserving the output and prescription components of the function-realization pattern.

The edited graph is HermiT-clean under the established M2 cleanup conditions.

This branch does not add:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

This branch does not resolve or claim to resolve the separate `madeByActuator` range issue.
