# SSN Systems Domain/Range Operationalization Evaluation

## Scope

This evaluation tests an OWL-only operational replacement for the deferred SSN Systems BFO dependence property mappings.

The failed mappings remain deferred:

```ttl
ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSurvivalProperty  rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSystemProperty    rdfs:subPropertyOf bfo:BFO_0000194 .
```

The replacement tested here is source-level domain/range typing for the three SSN Systems property relations. It does not add BFO dependence entailments, BFO domain/range constraints, SWRL, SPARQL, or COMS rules.

## Current Stable Baseline

Before this evaluation branch, the stable baseline was:

| Check | Result |
| --- | --- |
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 71 |
| audit issues | 2 expected `sosa:Sensor` version-alignment issues only |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 77 |
| property-chain expectations | 5 |
| restriction expectations | 2 |
| active direct mappings not covered | 0 |
| active property-chain mappings not covered | 0 |
| active restriction mappings not covered | 0 |
| HermiT M2 baseline | clean under established cleanup conditions |

The established HermiT M2 cleanup conditions are:

- merge `imports/cco.ttl`, `imports/ssn.ttl`, `imports/ssn-systems.ttl`, and `SSN2BFO.ttl`;
- remove all `owl:imports` triples;
- remove `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- remove `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

## Existing Source-Level Domain/Range Check

The six candidate source-level domain/range triples were checked exactly against:

- `imports/ssn-systems.ttl`;
- `SSN2BFO.ttl`.

None of the six exact triples already existed in either file before this branch.

| Candidate triple | In `imports/ssn-systems.ttl`? | In `SSN2BFO.ttl` before edit? |
| --- | --- | --- |
| `ssn-system:hasOperatingProperty rdfs:domain ssn-system:OperatingRange .` | no | no |
| `ssn-system:hasOperatingProperty rdfs:range ssn-system:OperatingProperty .` | no | no |
| `ssn-system:hasSurvivalProperty rdfs:domain ssn-system:SurvivalRange .` | no | no |
| `ssn-system:hasSurvivalProperty rdfs:range ssn-system:SurvivalProperty .` | no | no |
| `ssn-system:hasSystemProperty rdfs:domain ssn-system:SystemCapability .` | no | no |
| `ssn-system:hasSystemProperty rdfs:range ssn-system:SystemProperty .` | no | no |

The import already contains related class restrictions using these relations, but not the exact `rdfs:domain` / `rdfs:range` axioms tested here.

## Candidate Axioms Tested

The temporary HermiT candidate added exactly these six source-level typing triples:

```ttl
<http://www.w3.org/ns/ssn/systems/hasOperatingProperty>
  rdfs:domain <http://www.w3.org/ns/ssn/systems/OperatingRange> ;
  rdfs:range <http://www.w3.org/ns/ssn/systems/OperatingProperty> .

<http://www.w3.org/ns/ssn/systems/hasSurvivalProperty>
  rdfs:domain <http://www.w3.org/ns/ssn/systems/SurvivalRange> ;
  rdfs:range <http://www.w3.org/ns/ssn/systems/SurvivalProperty> .

<http://www.w3.org/ns/ssn/systems/hasSystemProperty>
  rdfs:domain <http://www.w3.org/ns/ssn/systems/SystemCapability> ;
  rdfs:range <http://www.w3.org/ns/ssn/systems/SystemProperty> .
```

These axioms provide OWL operational typing for subjects and objects of the SSN Systems source properties. They do not entail:

```text
y bfo:BFO_0000195 x
```

from:

```text
x ssn-system:has...Property y
```

## HermiT Results

Each graph was built from:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

and then applied the established cleanup conditions.

Command form:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

| Variant | Graph path | Triples added | Triple count | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Unsat set | Sample simplicity blocker |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- | --- |
| A baseline current graph | `/tmp/ssn-to-bfo-ssn-systems-domain-range-operationalization/A_baseline.ttl` | 0 | 15474 | 0 | yes | 0 | 0 | clean | no |
| B temporary candidate graph | `/tmp/ssn-to-bfo-ssn-systems-domain-range-operationalization/B_candidate_domain_range.ttl` | 6 | 15480 | 0 | yes | 0 | 0 | clean | no |
| C edited graph | `/tmp/ssn-to-bfo-ssn-systems-domain-range-operationalization/C_edited_graph.ttl` | active edit present | 15480 | 0 | yes | 0 | 0 | clean | no |

The temporary candidate graph was HermiT-clean, so the candidate was promoted to an active OWL edit in `SSN2BFO.ttl` and the corresponding spreadsheet rows were updated.

## Active TTL Changes

Active TTL edits were made in `SSN2BFO.ttl`.

The BFO dependence subproperty mappings remain deferred. The active replacements are source-level domain/range typing:

```ttl
###  http://www.w3.org/ns/ssn/systems/hasOperatingProperty
# BFO dependence subproperty mapping remains deferred; source-level typing is active.
<http://www.w3.org/ns/ssn/systems/hasOperatingProperty>
  rdfs:domain <http://www.w3.org/ns/ssn/systems/OperatingRange> ;
  rdfs:range <http://www.w3.org/ns/ssn/systems/OperatingProperty> .

###  http://www.w3.org/ns/ssn/systems/hasSurvivalProperty
# BFO dependence subproperty mapping remains deferred; source-level typing is active.
<http://www.w3.org/ns/ssn/systems/hasSurvivalProperty>
  rdfs:domain <http://www.w3.org/ns/ssn/systems/SurvivalRange> ;
  rdfs:range <http://www.w3.org/ns/ssn/systems/SurvivalProperty> .

###  http://www.w3.org/ns/ssn/systems/hasSystemProperty
# BFO dependence subproperty mapping remains deferred; source-level typing is active.
<http://www.w3.org/ns/ssn/systems/hasSystemProperty>
  rdfs:domain <http://www.w3.org/ns/ssn/systems/SystemCapability> ;
  rdfs:range <http://www.w3.org/ns/ssn/systems/SystemProperty> .
```

No `rdfs:subPropertyOf bfo:BFO_0000194` mapping was reactivated.

## Spreadsheet Changes

The workbook `Current_SOSA-SSN to BFO-CCO.xlsx` was updated only on `System Capability` rows 9, 11, and 14.

| Sheet | Row | Source term | Cells changed |
| --- | ---: | --- | --- |
| `System Capability` | 9 | `ssn-system:hasOperatingProperty` | `E9`, `F9` |
| `System Capability` | 11 | `ssn-system:hasSurvivalProperty` | `E11`, `F11` |
| `System Capability` | 14 | `ssn-system:hasSystemProperty` | `E14`, `F14` |

The OWL Axiom cells now record the source-level domain/range axioms. The rationale cells state that:

- the failed BFO dependence subproperty mapping remains deferred;
- OWL operationalization is provided by source-level domain/range typing;
- BFO dependence entailment is not active OWL in this branch;
- future rule/COMS treatment is paused/not implemented here.

## Mapping Audit Result

The mapping audit was regenerated after the TTL and spreadsheet edits.

| Metric | Before | After |
| --- | ---: | ---: |
| `ttl_candidate_mapping_assertions` | 71 | 71 |
| total issues | 2 | 2 |
| `missing_in_spreadsheet` | 1 | 1 |
| `missing_in_ttl` | 1 | 1 |

The remaining issues are still only the known `sosa:Sensor` version-alignment issues:

| Issue | Category | Source |
| --- | --- | --- |
| `ISSUE-0001` | `missing_in_spreadsheet` | `sosa:Sensor` |
| `ISSUE-0002` | `missing_in_ttl` | `sosa:Sensor`, `Common Classes` row 18 |

The added TTL domain/range triples are source-level typing axioms. They do not change the audit's active direct mapping counts.

## ELK Instance Mapping Result

The ELK instance mapping entailment report was regenerated.

| Metric | Before | After |
| --- | ---: | ---: |
| example files tested | 16 | 16 |
| ROBOT pass/fail | 16/0 | 16/0 |
| direct class expectations checked | 6 | 6 |
| direct property expectations checked | 77 | 77 |
| property-chain expectations checked | 5 | 5 |
| restriction expectations checked | 2 | 2 |
| expectation failures | 0 | 0 |
| active direct mappings not covered | 0 | 0 |
| active property-chain mappings not covered | 0 | 0 |
| active restriction mappings not covered | 0 | 0 |

The regenerated ELK report had no content diff after this change, because the active direct mapping expectation model does not count these source-level domain/range typing axioms as direct property mapping expectations.

## Assessment

This candidate is HermiT-clean in both temporary and edited M2 graphs.

It provides useful OWL operational typing for the SSN Systems source properties:

- `hasOperatingProperty` subjects are typed as `OperatingRange` and objects as `OperatingProperty`;
- `hasSurvivalProperty` subjects are typed as `SurvivalRange` and objects as `SurvivalProperty`;
- `hasSystemProperty` subjects are typed as `SystemCapability` and objects as `SystemProperty`.

It does not provide BFO dependence entailment. The intended dependence semantics remain:

```text
If range/capability x has property y, then y specifically depends on x.
```

That intended BFO inference remains deferred. This branch pauses rule/COMS work and does not implement it.

## Recommendation

The source-level domain/range operationalization is suitable as a narrow OWL mapping change because:

- the exact source-level domain/range axioms were absent from the source import and `SSN2BFO.ttl`;
- the temporary candidate graph was HermiT-clean;
- the edited graph remains HermiT-clean;
- the mapping audit remains at only the expected `sosa:Sensor` issues;
- the ELK entailment suite remains PASS with unchanged expectation counts.

Do not reactivate the old BFO dependence subproperty mappings in this branch.

Future work can separately revisit BFO dependence semantics through a HermiT-safe replacement design, but that work is intentionally not implemented here.
