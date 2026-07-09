# `ssn-system:ActuationRange` Simplification Evaluation

## Scope

This report evaluates a report-only candidate for simplifying the active `ssn-system:ActuationRange` mapping. It does not edit `SSN2BFO.ttl`, the workbook, imports, examples, tools, generated artifacts, release artifacts, or existing reports.

The purpose is independent cleanup. This evaluation does not add or recommend adding:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The prior `madeByActuator` range issue remains separate.

## Current Baseline

Current branch: `review/evaluate-simplify-actuation-range-mapping`

Current commit: `aba6de6`

Established current validation baseline:

| Check | Current baseline |
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

The current graph already includes the HermiT-clean source-level domain axiom:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

The range axiom remains absent:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

## Current Mapping Context

The active `SSN2BFO.ttl` mapping for `ssn-system:ActuationRange` makes it a BFO function realized in a `sosa:Actuation`. The realization is constrained by a nested expression saying the actuation:

- has output some BFO specifically dependent continuant; or
- affects some BFO process profile;
- and is prescribed by a CCO artifact function specification.

Abbreviated current mapping shape:

```ttl
ssn-system:ActuationRange
  rdfs:subClassOf [
    owl:intersectionOf (
      bfo:BFO_0000034
      [
        owl:onProperty bfo:BFO_0000054 ;
        owl:someValuesFrom [
          owl:intersectionOf (
            sosa:Actuation
            [
              owl:intersectionOf (
                [
                  owl:unionOf (
                    [ owl:onProperty cco:ont00001986 ;
                      owl:someValuesFrom bfo:BFO_0000020 ]
                    [ owl:onProperty cco:ont00001834 ;
                      owl:someValuesFrom bfo:BFO_0000144 ]
                  )
                ]
                [ owl:onProperty cco:ont00001920 ;
                  owl:someValuesFrom cco:ont00000118 ]
              )
            ]
          )
        ]
      ]
    )
  ] .
```

Relevant labels:

| IRI | Local label / role |
|---|---|
| `bfo:BFO_0000034` | function |
| `bfo:BFO_0000054` | has realization |
| `bfo:BFO_0000020` | specifically dependent continuant |
| `bfo:BFO_0000144` | process profile |
| `cco:ont00001986` | has output |
| `cco:ont00001834` | affects |
| `cco:ont00001920` | prescribed by |
| `cco:ont00000118` | artifact function specification |

The workbook row is `System Capability` row 3:

| Cell | Current value summary |
|---|---|
| `A3` | `ssn-system:ActuationRange` |
| `B3` | Source definition: range of values an actuator can return as the result of an actuation under conditions |
| `C3` | Rationale: function of a system whose realizations determine ranges of values produced or affected by actuation processes |
| `D3` | States the current function-realized-in-actuation expression with output-or-affects and prescription |
| `E3` | Active OWL class-expression mapping |
| `F3` | Rationale for modeling as a function realized in actuation processes |

## Source Context

The imported `imports/ssn-systems.ttl` source ontology defines `ssn-system:ActuationRange` as a subclass of `ssn-system:SystemProperty`.

It also constrains `ActuationRange` through an inverse `hasSystemProperty` / inverse `hasSystemCapability` restriction whose ultimate filler is `sosa:Actuator`.

Abbreviated source shape:

```ttl
ssn-system:ActuationRange
  rdfs:subClassOf
    ssn-system:SystemProperty ,
    [
      owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
      owl:allValuesFrom [
        owl:onProperty [ owl:inverseOf ssn-system:hasSystemCapability ] ;
        owl:allValuesFrom sosa:Actuator
      ]
    ] .
```

The source definition is actuation-oriented, but the imported source ontology itself does not assert the current BFO/CCO function-realization class expression.

## Prior Context

`reports/actuation-range-mapping-correction-evaluation.md` found:

- the current `ActuationRange` mapping is HermiT-clean in the baseline;
- removing the current `ActuationRange` mapping does not make `sosa:madeByActuator rdfs:range sosa:Actuator` HermiT-clean;
- therefore an `ActuationRange` simplification should not be presented as a fix for the held-back `madeByActuator` range axiom;
- the suspicious subpart is the `cco:affects some bfo:BFO_0000144` branch;
- that branch tested alone is not HermiT-clean because the local `affects` / `is affected by` target pattern drives a continuant target, while `bfo:BFO_0000144` is process-profile / occurrent-like.

## Preferred Simplification Candidate

The preferred simplification is the smallest HermiT-clean cleanup that preserves the current workbook's function-realized-in-actuation framing while removing the unsafe `affects some ProcessProfile` branch.

Candidate shape:

```ttl
ssn-system:ActuationRange
  rdfs:subClassOf [
    owl:intersectionOf (
      bfo:BFO_0000034
      [
        owl:onProperty bfo:BFO_0000054 ;
        owl:someValuesFrom [
          owl:intersectionOf (
            sosa:Actuation
            [
              owl:intersectionOf (
                [ owl:onProperty cco:ont00001986 ;
                  owl:someValuesFrom bfo:BFO_0000020 ]
                [ owl:onProperty cco:ont00001920 ;
                  owl:someValuesFrom cco:ont00000118 ]
              )
            ]
          )
        ]
      ]
    )
  ] .
```

This is equivalent to:

```text
Function
and has_realization some (
  sosa:Actuation
  and has_output some specifically dependent continuant
  and prescribed_by some artifact function specification
)
```

This candidate is narrower than the current mapping because it removes the `affects some ProcessProfile` disjunct. It is more specific than a pure `SystemProperty` fallback because it retains actuation realization, output, and prescription structure.

The conservative fallback remains: remove the specific `ActuationRange` class-expression mapping and rely on the imported `ActuationRange rdfs:subClassOf ssn-system:SystemProperty` plus the active `SystemProperty` mapping. That fallback is safer but loses more of the current actuation-range interpretation.

## HermiT Method

Temporary files were written only under:

```text
/tmp/ssn-to-bfo-actuation-range-simplification-evaluation
```

Each temporary graph was built from:

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

Each variant was run with:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

| Tool | Version |
|---|---|
| ROBOT | 1.9.7 |
| Java | 22.0.2 |

## Variant Summary

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsat set | Sample blocker |
|---|---|---|---:|---:|---|---:|---|---|
| A | Baseline current graph | `/tmp/ssn-to-bfo-actuation-range-simplification-evaluation/A-baseline.ttl` | 15535 | 0 | yes | 0 | none | no |
| B | Replace current `ActuationRange` mapping with output-only simplification | `/tmp/ssn-to-bfo-actuation-range-simplification-evaluation/B-output-only.ttl` | 15526 | 0 | yes | 0 | none | no |
| C | Output-only simplification plus explicit `sosa:madeByActuator rdfs:range sosa:Actuator` | `/tmp/ssn-to-bfo-actuation-range-simplification-evaluation/C-output-only-plus-range.ttl` | 15527 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` | no |
| D | Replace current `ActuationRange` mapping with `affects some ProcessProfile` branch only | `/tmp/ssn-to-bfo-actuation-range-simplification-evaluation/D-affects-only.ttl` | 15526 | 1 | no | n/a | `ssn-system:ActuationRange` | no |

## Interpretation

### Current Mapping

The current `ActuationRange` mapping is HermiT-clean in the current baseline. It is not currently breaking the integrated graph.

However, the current mapping is stronger than the imported source ontology by adding a BFO/CCO function-realization expression. The `affects some ProcessProfile` branch is specifically suspicious because it is not HermiT-clean when isolated.

### Preferred Simplification

The output-only simplification is HermiT-clean:

```text
return code: 0
reasoned output: yes
owl:Nothing count: 0
unsat count: 0
```

It preserves the function-realized-in-actuation and prescribed-by-functional-specification interpretation while removing the unsafe `affects some ProcessProfile` branch.

### Held-Back `madeByActuator` Range

The simplification does not unblock the held-back range axiom. When the output-only simplification is paired with:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

HermiT still reports:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

Therefore this simplification should not be described as a fix for the `madeByActuator` range issue.

### Suspicious Subpart

The isolated suspicious branch:

```text
Function
and has_realization some (
  sosa:Actuation
  and affects some ProcessProfile
  and prescribed_by some ArtifactFunctionSpecification
)
```

is not HermiT-clean. It makes `ssn-system:ActuationRange` unsatisfiable by itself in the current integrated graph. This confirms the prior finding that the `affects some ProcessProfile` branch should not be retained as an independent mapping component.

## Assessment

The current mapping is clean only because the unsafe `affects some ProcessProfile` branch is inside a union with the `has_output some SDC` branch. That makes the whole expression satisfiable, but it leaves a known-bad modeling branch embedded in the active mapping.

The output-only simplification is the best supported cleanup candidate if the goal is to preserve most of the current workbook intent. It removes the known-bad branch while retaining:

- `ActuationRange` as a function;
- realization in `sosa:Actuation`;
- output of a specifically dependent continuant;
- prescription by an artifact function specification.

This evidence supports a future mapping-change branch as independent cleanup. It does not support adding the held-back `madeByActuator` range axiom.

## Recommendation

Recommend a narrow future mapping-change branch:

```text
fix/simplify-actuation-range-mapping
```

That branch should:

- replace the current `ssn-system:ActuationRange` class expression with the output-only simplification tested here;
- update `System Capability` row 3 in the workbook to remove the `affects some ProcessProfile` branch from the active OWL mapping and rationale;
- not add `sosa:madeByActuator rdfs:range sosa:Actuator`;
- not reactivate failed BFO/CCO subproperty mappings;
- regenerate the mapping audit and any directly affected validation reports;
- preserve the current HermiT-clean baseline.

The `madeByActuator` range issue should remain a separate explanation/design task.
