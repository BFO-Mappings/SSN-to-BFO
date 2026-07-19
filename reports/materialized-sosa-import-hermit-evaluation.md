# Materialized SOSA Import HermiT Evaluation

## Scope

This report documents the new local SOSA import materialization and reruns the `sosa:madeByActuator` / `sosa:madeActuation` HermiT diagnostics against both the old reduced M2 graph and the full local SOSA closure graph.

No mappings were changed. `SSN2BFO.ttl`, the workbook, `imports/cco.ttl`, `imports/ssn.ttl`, `imports/ssn-systems.ttl`, examples, tools, and generated/release artifacts were not edited.

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation
```

## Local SOSA Source Import

The new local file exists:

```text
imports/sosa.ttl
```

Parse and ontology summary:

| Item | Result |
|---|---|
| Turtle parse | OK |
| triple count | 327 |
| ontology IRI | `http://www.w3.org/ns/sosa/` |

Relevant SOSA triples in `imports/sosa.ttl`:

```ttl
sosa:madeActuation rdf:type owl:ObjectProperty ;
    owl:inverseOf sosa:madeByActuator ;
    schema:domainIncludes sosa:Actuator ;
    schema:rangeIncludes sosa:Actuation .

sosa:madeByActuator rdf:type owl:ObjectProperty ;
    schema:domainIncludes sosa:Actuation ;
    schema:rangeIncludes sosa:Actuator .

sosa:Actuation rdf:type owl:Class .
sosa:Actuator rdf:type owl:Class .
```

`imports/sosa.ttl` asserts:

```ttl
sosa:madeActuation owl:inverseOf sosa:madeByActuator .
```

That one-way raw triple is semantically sufficient for inverse reasoning. The reverse raw triple:

```ttl
sosa:madeByActuator owl:inverseOf sosa:madeActuation .
```

is not present as a serialized source triple, but it follows under OWL inverse-property semantics.

The materialized SOSA file does not itself assert the local active `rdfs:domain` / `rdfs:range` triples previously checked in the reduced M2 diagnostics. In particular, it does not assert:

```ttl
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeByActuator rdfs:range sosa:Actuator .
```

It also does not contain the `owl:allValuesFrom` restrictions on `sosa:Actuation` or `sosa:Actuator`. Those restrictions are present through `imports/ssn.ttl`.

Therefore prior reduced-M2 reports omitted this indirect SOSA import unless they explicitly added a proxy inverse axiom.

## Graph Profiles

Both profiles were loaded from local files, then normalized by removing all `owl:imports` triples and the established sample simplicity blockers:

```ttl
sosa:isSampleOf rdf:type owl:FunctionalProperty .
sosa:hasSample rdf:type owl:InverseFunctionalProperty .
```

Profile A, old reduced M2 graph:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Profile B, full local SOSA closure graph:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Profile comparison:

| Item | Profile A reduced M2 | Profile B full local SOSA closure |
|---|---:|---:|
| triple count after cleanup | 15510 | 15770 |
| sample simplicity blockers present | no | no |
| `sosa:madeActuation owl:inverseOf sosa:madeByActuator` | absent | present |
| `sosa:madeByActuator owl:inverseOf sosa:madeActuation` as raw triple | absent | absent |
| `sosa:madeActuation rdfs:domain sosa:Actuator` | present | present |
| `sosa:madeActuation rdfs:range sosa:Actuation` | present | present |
| `sosa:madeByActuator rdfs:domain sosa:Actuation` | present | present |
| `sosa:madeByActuator rdfs:range sosa:Actuator` | absent | absent |
| `sosa:Actuation subClassOf madeByActuator only Actuator` | present | present |
| `sosa:Actuator subClassOf madeActuation only Actuation` | present | present |

The main logical difference for this diagnostic is that Profile B contains the SOSA inverse axiom and object-property declarations from `imports/sosa.ttl`.

## HermiT Variants

ROBOT/HermiT was run with:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

| Variant | Graph path | Temporary edit | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| A0 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/A0_reduced_baseline.ttl` | old reduced M2 baseline | 15510 | 0 | yes | 0 | 0 | clean |
| A1 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/A1_reduced_plus_range.ttl` | A0 plus `sosa:madeByActuator rdfs:range sosa:Actuator` | 15511 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B0 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B0_full_sosa_baseline.ttl` | full local SOSA closure baseline | 15770 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B1 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B1_full_sosa_plus_range.ttl` | B0 plus `sosa:madeByActuator rdfs:range sosa:Actuator` | 15771 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B2 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B2_minus_madeActuation_agent_in.ttl` | B0 minus `sosa:madeActuation rdfs:subPropertyOf cco:ont00001787` | 15769 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B3 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B3_minus_madeByActuator_has_agent.ttl` | B0 minus `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` | 15769 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B4 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B4_minus_both_agent_mappings.ttl` | B0 minus both CCO agent mappings | 15768 | 0 | yes | 0 | 0 | clean |
| B5 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B5_minus_sosa_inverse.ttl` | B0 minus `sosa:madeActuation owl:inverseOf sosa:madeByActuator` | 15769 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B6 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B6_minus_inverse_plus_range.ttl` | B0 minus SOSA inverse plus explicit `madeByActuator` range | 15770 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B7 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B7_minus_madeActuation_agent_in_plus_range.ttl` | B0 minus `madeActuation -> agent_in` plus explicit `madeByActuator` range | 15770 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B8 | `/tmp/ssn-to-bfo-materialized-sosa-import-hermit-evaluation/B8_minus_madeByActuator_has_agent_plus_range.ttl` | B0 minus `madeByActuator -> has_agent` plus explicit `madeByActuator` range | 15770 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |

The sample simplicity blockers did not reappear in any variant.

## Interpretation

Materializing SOSA changes the baseline HermiT result.

The old reduced M2 baseline remains clean:

```text
A0: 0 unsatisfiable classes
```

The full local SOSA closure baseline is not HermiT-clean:

```text
B0: sosa:Actuator, sosa:Actuation, ssn-system:ActuationRange
```

The inconsistency is therefore no longer only a consequence of adding the explicit `sosa:madeByActuator rdfs:range sosa:Actuator` axiom. Once SOSA is materialized, the baseline already contains enough additional SOSA context to reproduce the same three-class failure.

The failure does not depend only on the raw SOSA inverse axiom. Variant B5 removes:

```ttl
sosa:madeActuation owl:inverseOf sosa:madeByActuator .
```

but the same three unsatisfiable classes remain. This means the full SOSA materialization contributes more relevant logical context than that single inverse triple alone, such as object-property declarations and other SOSA property/class axioms.

The failure also does not clear when only one CCO agent mapping is removed:

```ttl
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

Variants B2 and B3 each remain not HermiT-clean. Variant B4, which removes both CCO agent mappings, is HermiT-clean. This suggests the problem is a mixed full-closure interaction involving the paired SOSA actuation properties, their SOSA materialization, and the active CCO `agent_in` / `has_agent` mappings. The current evidence does not justify removing a single mapping as the final fix.

Adding the explicit range axiom to the full local SOSA closure does not change the unsat set:

```text
B0: sosa:Actuator, sosa:Actuation, ssn-system:ActuationRange
B1: sosa:Actuator, sosa:Actuation, ssn-system:ActuationRange
```

So, under the full local SOSA closure, the explicit range axiom is not the decisive trigger. The graph is already failing before it is added.

Prior reduced-M2 madeByActuator reports need a correction note or limitation note. Their conclusions apply to reduced M2 graphs that did not include the materialized indirect SOSA import unless they explicitly added a proxy inverse or related SOSA context.

## Recommendation

The safest next step is not a mapping-change branch yet. The evidence supports an import/diagnostic update plus focused explanation extraction:

1. Treat `imports/sosa.ttl` as required local import-closure material for HermiT diagnostics that claim to match Protégé.
2. Update future diagnostic graph construction to distinguish reduced M2 from full local SOSA closure explicitly.
3. Add correction notes to prior reduced-M2 `madeByActuator` reports.
4. Open a focused explanation branch for the full local SOSA closure conflict, with attention to the paired CCO agent mappings:

```text
review/explain-full-sosa-actuation-agent-conflict
```

Do not remove or defer `sosa:madeActuation -> cco:agent_in` or `sosa:madeByActuator -> cco:has_agent` solely from this report. Variant B4 shows that removing both clears the full-closure issue, but the current variants do not establish which replacement representation would preserve intended semantics.
