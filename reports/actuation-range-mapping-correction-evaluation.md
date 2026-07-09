# `ssn-system:ActuationRange` Mapping Correction Evaluation

## Scope

This report evaluates suspected problems in the active `ssn-system:ActuationRange` mapping area. It is report-only and does not edit `SSN2BFO.ttl`, the workbook, imports, examples, tools, generated artifacts, or existing reports.

Local context:

- Branch: `review/evaluate-actuation-range-mapping-corrections`
- Temporary directory: `/tmp/ssn-to-bfo-actuation-range-mapping-correction-evaluation`

## Current Baseline

The current stable baseline is:

- validation suite: PASS
- `ttl_candidate_mapping_assertions=71`
- audit issues: 2 expected `sosa:Sensor` version-alignment issues only
- ELK direct class expectations: 6
- ELK direct property expectations: 77
- property-chain expectations: 5
- restriction expectations: 2
- active direct/property-chain/restriction mappings not covered: 0
- current HermiT M2 baseline: clean under established cleanup conditions

Important current state:

- `sosa:madeByActuator rdfs:domain sosa:Actuation` is active and HermiT-clean.
- `sosa:madeByActuator rdfs:range sosa:Actuator` remains held back.
- The current baseline appears to entail effective `madeByActuator` range behavior through the active domain plus imported `sosa:Actuation` all-values restriction.
- Explicitly adding the range axiom still reproduces a HermiT failure involving:

```text
sosa:Actuation
sosa:Actuator
ssn-system:ActuationRange
```

## Source Context

Imported `imports/ssn-systems.ttl` source axioms define `ssn-system:ActuationRange` as:

```ttl
ssn-system:ActuationRange
    rdf:type owl:Class ;
    rdfs:subClassOf ssn-system:SystemProperty ,
        [ owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
          owl:allValuesFrom [
            owl:onProperty [ owl:inverseOf ssn-system:hasSystemCapability ] ;
            owl:allValuesFrom sosa:Actuator
          ] ] .
```

Its source definition says it is:

```text
The set of values that the Actuator can return as the Result of an Actuation under the defined Conditions with the defined system properties.
```

Nearby source context:

- `ssn-system:hasSystemCapability` is a subproperty of `ssn:hasProperty`.
- `ssn-system:hasSystemProperty` is a subproperty of `ssn:hasProperty`.
- `ssn-system:SystemCapability` is a subclass of `ssn:Property` with restrictions on `hasSystemProperty`, `inCondition`, and inverse `hasSystemCapability`.
- `ssn-system:SystemProperty` is a subclass of `ssn:Property` with inverse `hasSystemProperty` all-values/min-cardinality restrictions.
- `sosa:Actuation` source restrictions include `sosa:madeByActuator only sosa:Actuator` and exact-cardinality 1 on `sosa:madeByActuator`.
- `sosa:Actuator` source restrictions include `sosa:madeActuation only sosa:Actuation`.

## Active Mapping Context

The active `SSN2BFO.ttl` mapping for `ssn-system:ActuationRange` is:

```ttl
ssn-system:ActuationRange
    rdfs:subClassOf [
        owl:intersectionOf (
            bfo:BFO_0000034
            [ owl:onProperty bfo:BFO_0000054 ;
              owl:someValuesFrom [
                owl:intersectionOf (
                    sosa:Actuation
                    [
                      owl:intersectionOf (
                        [ owl:unionOf (
                            [ owl:onProperty cco:ont00001986 ;
                              owl:someValuesFrom bfo:BFO_0000020 ]
                            [ owl:onProperty cco:ont00001834 ;
                              owl:someValuesFrom bfo:BFO_0000144 ]
                          ) ]
                        [ owl:onProperty cco:ont00001920 ;
                          owl:someValuesFrom cco:ont00000118 ]
                      )
                    ]
                )
              ] ]
        )
    ] .
```

Labels for key target terms:

- `bfo:BFO_0000034` = function
- `bfo:BFO_0000054` = has realization
- `bfo:BFO_0000020` = specifically dependent continuant
- `bfo:BFO_0000144` = Process Profile
- `cco:ont00001986` = has output
- `cco:ont00001834` = affects
- `cco:ont00001920` = prescribed by
- `cco:ont00000118` = Artifact Function Specification

The corresponding workbook row is `System Capability` row 3:

- source term: `ssn-system:ActuationRange`
- workbook target/rationale: a BFO Function realized in `sosa:Actuation`, where the actuation either has output some specifically dependent continuant or affects some process profile, and is prescribed by an Artifact Function Specification.

## Apparent Mapping Mismatch

The active mapping is HermiT-clean in the current baseline, but it appears stronger than the source semantics require.

The imported source ontology says `ActuationRange` is a `SystemProperty`, and its definition talks about a set/range of values that an actuator can return as the result of an actuation. The active TTL/workbook mapping makes it a BFO `function` with realization in an actuation process. That may be a defensible capability-style interpretation, but it is more committed than the source axiom itself.

The most suspicious subpart is:

```ttl
cco:affects some bfo:BFO_0000144
```

where `bfo:BFO_0000144` is Process Profile. A focused candidate containing this branch alone was not HermiT-clean. ROBOT explanation showed:

```text
cco:affects inverseOf cco:is affected by
cco:is affected by domain bfo:continuant
bfo:ProcessProfile subclassOf bfo:occurrent
bfo:continuant disjointWith bfo:occurrent
```

So the `affects some ProcessProfile` branch is not safe as a standalone existential. In the current active mapping it appears under a union with `has_output some SDC`, which allows the class expression to remain satisfiable, but the branch remains a modeling smell.

## Candidate Corrections

The following temporary `ActuationRange`-only candidates were tested:

| Candidate | Description | Support level |
|---|---|---|
| No specific mapping | Remove the active `ActuationRange` class-expression mapping and rely on source subclass `SystemProperty` plus inherited `SystemProperty` mapping. | conservative fallback |
| Function only | Replace with `subClassOf bfo:Function`. | weak, underspecified |
| Function realized in Actuation | Replace with `Function and has_realization some sosa:Actuation`. | keeps actuation realization but drops output/affects/prescription details |
| Function realized in Actuation plus prescription | Keep actuation realization and `prescribed_by some ArtifactFunctionSpecification`. | moderate weakening |
| Function realized in Actuation plus has-output | Keep actuation realization, `has_output some SDC`, and prescription; drop affects branch. | plausible if function framing is retained |
| Function realized in Actuation plus affects | Keep only the affects/ProcessProfile branch and prescription. | tested as a negative control |
| SystemProperty-style | Use the general `SystemProperty` style: `(SDC or ProcessProfile) and prescribed_by some AFS`. | aligned with inherited parent mapping |
| Function realized in generic process | Replace `sosa:Actuation` realization with generic BFO process realization. | weaker and less source-specific |
| Function realized in prescribed process | Generic process realization plus prescription. | weaker and less source-specific |
| Function realized in prescribed planned act | CCO PlannedAct realization plus prescription. | weaker than `sosa:Actuation`, still planned-act oriented |

Unsupported final corrections were not proposed. These are temporary probes only.

## HermiT Method

For each temporary graph, the input graph was built from:

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

No variant reintroduced the sample simplicity blocker.

## Variant Results

| Variant | Temporary edit | Triples | Return | Reasoned output | `owl:Nothing` | Unsats |
|---|---|---:|---:|---|---:|---|
| A | Baseline current graph | 15535 | 0 | yes | 0 | none |
| B | Add explicit `sosa:madeByActuator rdfs:range sosa:Actuator` | 15536 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` |
| C | Remove active `ActuationRange` mapping only | 15498 | 0 | yes | 0 | none |
| D | Remove active `ActuationRange` mapping plus explicit range | 15499 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator` |
| E1 | Function only | 15503 | 0 | yes | 0 | none |
| F1 | Function only plus explicit range | 15504 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator` |
| E2 | Function realized in `sosa:Actuation` | 15508 | 0 | yes | 0 | none |
| F2 | Function realized in `sosa:Actuation` plus explicit range | 15509 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` |
| E3 | Function realized in `sosa:Actuation` plus prescription | 15517 | 0 | yes | 0 | none |
| F3 | Function realized in `sosa:Actuation` plus prescription plus explicit range | 15518 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` |
| E4 | Function realized in `sosa:Actuation` plus `has_output some SDC` plus prescription | 15522 | 0 | yes | 0 | none |
| F4 | Same as E4 plus explicit range | 15523 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` |
| E5 | Function realized in `sosa:Actuation` plus `affects some ProcessProfile` plus prescription | 15522 | 1 | no | n/a | `ssn-system:ActuationRange` |
| F5 | Same as E5 plus explicit range | 15523 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` |
| E6 | SystemProperty-style mapping | 15514 | 0 | yes | 0 | none |
| F6 | SystemProperty-style mapping plus explicit range | 15515 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator` |
| E7 | Function realized in generic BFO process | 15508 | 0 | yes | 0 | none |
| F7 | Function realized in generic BFO process plus explicit range | 15509 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator` |
| E8 | Function realized in prescribed BFO process | 15517 | 0 | yes | 0 | none |
| F8 | Function realized in prescribed BFO process plus explicit range | 15518 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator` |
| E9 | Function realized in prescribed CCO PlannedAct | 15517 | 0 | yes | 0 | none |
| F9 | Function realized in prescribed CCO PlannedAct plus explicit range | 15518 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator` |

## Findings

### Current Mapping

The current `ActuationRange` mapping is HermiT-clean in the baseline. It is not currently breaking the integrated graph.

### Explicit `madeByActuator` Range

The explicit held-back range axiom still reproduces the known three-class failure:

```text
sosa:Actuation
sosa:Actuator
ssn-system:ActuationRange
```

### Removing `ActuationRange`

Removing the active `ActuationRange` mapping is HermiT-clean by itself. With the explicit range axiom added, it removes only `ssn-system:ActuationRange` from the unsat set:

```text
sosa:Actuation
sosa:Actuator
```

Therefore `ActuationRange` is a downstream or partial contributor, not the root cause of the explicit-range failure.

### Candidate Corrections

Most candidate corrections were independently HermiT-clean. The exception was the `affects some ProcessProfile` candidate, which is not HermiT-clean even without the held-back range axiom.

Candidate corrections that avoid direct realization in `sosa:Actuation`, or that fall back to SystemProperty-style mapping, remove `ActuationRange` from the explicit-range failure. None of them make the explicit `sosa:madeByActuator` range axiom HermiT-clean.

### Suspicious Branch

The `affects some ProcessProfile` branch should not be promoted as a standalone correction. It creates an immediate continuant/occurrent conflict:

```text
cco:affects / cco:is affected by implies a continuant target
bfo:ProcessProfile is an occurrent
continuant disjointWith occurrent
```

The current mapping hides that branch inside a union with `has_output some SDC`, which keeps the full expression satisfiable but makes the modeling harder to defend.

## Answers To Required Questions

**Is the current `ActuationRange` mapping itself HermiT-clean in the baseline?**

Yes. Variant A is clean, and removing the mapping in Variant C is also clean.

**Does removing it make the explicit `madeByActuator` range axiom HermiT-clean?**

No. Variant D still fails with `sosa:Actuation` and `sosa:Actuator`.

**Is `ActuationRange` the root cause, downstream member, or partial contributor?**

It is downstream or a partial contributor. Removing or weakening its mapping can remove `ssn-system:ActuationRange` from the explicit-range unsat set, but it does not resolve the core `sosa:Actuation` / `sosa:Actuator` failure.

**Which suspected correction is HermiT-clean?**

HermiT-clean candidates include:

- no specific `ActuationRange` mapping;
- function only;
- function realized in `sosa:Actuation`;
- function realized in `sosa:Actuation` plus prescription;
- function realized in `sosa:Actuation` plus `has_output some SDC` plus prescription;
- SystemProperty-style mapping;
- function realized in generic BFO process;
- function realized in prescribed BFO process;
- function realized in prescribed CCO PlannedAct.

The standalone `affects some ProcessProfile` correction is not HermiT-clean.

**Which correction makes `madeByActuator rdfs:range sosa:Actuator` HermiT-clean?**

None of the `ActuationRange`-only corrections tested make the explicit range axiom HermiT-clean.

**Is there enough evidence for a mapping-change branch?**

There is evidence that the current `ActuationRange` mapping is unnecessarily strong and contains a suspicious `affects some ProcessProfile` branch. There is not enough evidence that correcting `ActuationRange` will solve the `madeByActuator` range problem.

## Recommendation

Do not add the explicit held-back axiom yet:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

Do not start a fix branch claiming that `ActuationRange` correction unblocks that range axiom. It does not.

A narrow `ActuationRange` cleanup may still be justified independently, especially to remove or avoid the `affects some ProcessProfile` branch. The safest candidate is to align `ActuationRange` with the inherited `SystemProperty` style or to defer the specific class-expression mapping and rely on the source `ActuationRange rdfs:subClassOf ssn-system:SystemProperty` plus the active `SystemProperty` mapping.

Recommended next branch:

```text
review/continue-madeByActuator-range-debug
```

If the user wants an independent cleanup branch for the suspicious `ActuationRange` expression, use:

```text
fix/simplify-actuation-range-mapping
```

That branch should not claim to make `sosa:madeByActuator rdfs:range sosa:Actuator` HermiT-clean unless a separate minimized reproduction proves that result.
