# Actuation Agent Property Mapping Deferral

## Scope

This branch implements the recommendation from:

```text
reports/sosa-actuation-agent-unsat-explanation.md
```

The change defers the paired active CCO agent property mappings for the SOSA actuation-side properties. It does not change source imports, examples, tools, generated/release artifacts, or unrelated mappings.

## TTL Changes

The following active direct CCO property mappings were removed/deferred from `SSN2BFO.ttl`:

```ttl
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

The source-level domain/range axioms were retained:

```ttl
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

This branch does not add:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The resulting TTL block is:

```ttl
###  http://www.w3.org/ns/sosa/madeActuation
<http://www.w3.org/ns/sosa/madeActuation> rdfs:domain <http://www.w3.org/ns/sosa/Actuator> ;
                                          rdfs:range <http://www.w3.org/ns/sosa/Actuation> .
# Direct CCO agent-in property mapping deferred with madeByActuator pending HermiT-safe treatment.

###  http://www.w3.org/ns/sosa/madeByActuator
<http://www.w3.org/ns/sosa/madeByActuator> rdfs:domain <http://www.w3.org/ns/sosa/Actuation> .
# Direct CCO has-agent property mapping deferred with madeActuation pending HermiT-safe treatment.
```

## Workbook Changes

Workbook file:

```text
Current_SOSA-SSN to BFO-CCO.xlsx
```

Changed sheet and cells:

| Sheet | Row | Source | Cell | Change |
|---|---:|---|---|---|
| `Common OPs` | 27 | `sosa:madeActuation` | `E27` | Removed `subPropertyOf cco:agent_in`; retained source-level domain/range axioms. |
| `Common OPs` | 27 | `sosa:madeActuation` | `F27` | Updated rationale to state that the direct CCO agent-in mapping is deferred as part of the paired actuation-agent deferral required for HermiT safety under the materialized SOSA import closure. |
| `Common OPs` | 28 | `sosa:madeByActuator` | `E28` | Removed `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833`; retained source-level domain and source inverse note. |
| `Common OPs` | 28 | `sosa:madeByActuator` | `F28` | Updated rationale to state that the direct CCO has-agent mapping is deferred as part of the paired actuation-agent deferral required for HermiT safety under the materialized SOSA import closure. |

Updated `E27`:

```ttl
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
```

Updated `E28`:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeByActuator owl:inverseOf sosa:madeActuation .
```

The workbook rationale does not claim that the intended agent semantics are invalid. It only records that the direct CCO property mappings are not HermiT-safe together in the full local SOSA closure profile.

## Count Changes

Before this branch, the current baseline reported:

```text
ttl_candidate_mapping_assertions=70
ELK direct property expectations=77
```

After this branch:

```text
ttl_candidate_mapping_assertions=68
ELK direct property expectations=75
```

Other ELK expectation counts after the change:

```text
direct class expectations: 6
property-chain expectations: 5
restriction expectations: 2
active direct mappings not covered: 0
active property-chain mappings not covered: 0
active restriction mappings not covered: 0
```

The mapping consistency audit remains limited to the two expected `sosa:Sensor` version-alignment issues:

```text
total issues: 2
missing_in_spreadsheet: 1
missing_in_ttl: 1
```

## HermiT Full Local SOSA Closure Check

HermiT graph construction:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Cleanup applied:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

ROBOT/HermiT command:

```bash
robot reason --reasoner HermiT \
  --input /tmp/ssn-to-bfo-actuation-agent-property-mapping-deferral/full-sosa-closure-after-deferral.ttl \
  --output /tmp/ssn-to-bfo-actuation-agent-property-mapping-deferral/full-sosa-closure-after-deferral-reasoned.ttl
```

Result:

| Item | Result |
|---|---|
| graph path | `/tmp/ssn-to-bfo-actuation-agent-property-mapping-deferral/full-sosa-closure-after-deferral.ttl` |
| triple count | 15768 |
| return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |
| sample simplicity blocker reappeared | no |

The three prior full-closure unsatisfiable classes are cleared:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

## Validation

Commands run:

```bash
make audit-write
python tools/test_elk_instance_mapping_entailments.py --output reports/elk-instance-mapping-entailments.md
python tools/run_validation_suite.py
```

Results:

```text
Mapping consistency audit: PASS
ELK instance mapping entailment test: PASS
Validation suite: PASS
```

The audit CSV was regenerated by `make audit-write`, but it did not differ from the tracked file in this branch.

## Interpretation

This branch defers a paired direct CCO property representation that is not HermiT-safe in the full local SOSA closure profile. It does not reject the intended agent / agent-in semantics. The intended semantics remain candidates for a later HermiT-safe OWL redesign, rule/COMS treatment, or other reviewed representation.
