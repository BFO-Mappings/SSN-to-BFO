# `sosa:madeByActuator` Range Minimal Reproduction

## Scope

This report documents a report-only minimization diagnostic for the held-back axiom:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The diagnostic was run after the merged `ssn-system:ActuationRange` simplification from PR #134. It does not edit `SSN2BFO.ttl`, the workbook, imports, examples, tools, generated artifacts, release artifacts, or existing reports.

Temporary files were written only under:

```text
/tmp/ssn-to-bfo-madeByActuator-range-minimal-reproduction
```

## Current Baseline

Current branch:

```text
review/minimize-madeByActuator-range-redundancy-discrepancy
```

Current commit:

```text
dffa3be
```

Current stable baseline:

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
| current HermiT M2 baseline under established cleanup | clean |

Current relevant active mapping state:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation ;
                     rdfs:subPropertyOf cco:ont00001833 .
```

The held-back range axiom is still absent:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The current `ssn-system:ActuationRange` mapping is the simplified post-PR #134 version:

```text
Function
and has_realization some (
  sosa:Actuation
  and has_output some specifically dependent continuant
  and prescribed_by some artifact function specification
)
```

## Method

For full-graph HermiT variants, the M2 graph was built from:

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

Each HermiT run used:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

| Tool | Version |
|---|---|
| ROBOT | 1.9.7 |
| Java | 22.0.2 |

No run in this report reintroduced the sample simplicity blocker.

## Full-Graph Reproduction

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsat set |
|---|---|---|---:|---:|---|---:|---|
| A | Baseline, no explicit range | `/tmp/ssn-to-bfo-madeByActuator-range-minimal-reproduction/A-baseline.ttl` | 15526 | 0 | yes | 0 | none |
| B | Add explicit `sosa:madeByActuator rdfs:range sosa:Actuator` | `/tmp/ssn-to-bfo-madeByActuator-range-minimal-reproduction/B-explicit-range.ttl` | 15527 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |

The explicit range failure still reproduces after the `ActuationRange` simplification.

## Redundancy Probe Repeat

The current post-PR #134 baseline still behaves as though the effective range is already entailed by:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:Actuation rdfs:subClassOf [
  owl:onProperty sosa:madeByActuator ;
  owl:allValuesFrom sosa:Actuator
] .
```

Probe results:

| Variant | Probe | Triples | Return | Reasoned output | `owl:Nothing` | Unsat set |
|---|---|---:|---:|---|---:|---|
| C | `sosa:madeByActuator some owl:Thing` | 15531 | 0 | yes | 0 | none |
| D | `sosa:madeByActuator some sosa:Actuator` | 15531 | 0 | yes | 0 | none |
| E | `sosa:madeByActuator some (not sosa:Actuator)` | 15533 | 1 | no | n/a | `MadeByActuatorNonActuatorProbe` |
| F | explicit range plus non-Actuator probe | 15534 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange`; `MadeByActuatorRangeNonActuatorProbe` |

Interpretation: `madeByActuator some owl:Thing` and `madeByActuator some sosa:Actuator` remain satisfiable, so the property is not simply unusable. The non-Actuator probe is unsatisfiable, so the baseline still entails the effective range-like behavior. The explicit `rdfs:range` axiom nevertheless still changes the HermiT outcome for named classes.

## Full-Graph Reducers

The following reducers were tested against the full explicit-range graph.

| Reducer | Result | Unsat set |
|---|---|---|
| Remove `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` | clean | none |
| Remove active `sosa:Actuator` class-expression mapping | clean | none |
| Remove active `sosa:Actuation` class-expression mapping | clean | none |
| Remove simplified active `ssn-system:ActuationRange` mapping | still fails, reduced | `sosa:Actuator`; `sosa:Actuation` |
| Remove source package directly attached to `sosa:Actuation` | clean | none |
| Remove source package directly attached to `sosa:Actuator` | clean | none |

Additional controls did not reduce the failure:

| Reducer | Result | Unsat set |
|---|---|---|
| Remove `sosa:madeActuation rdfs:subPropertyOf cco:ont00001787` | still fails | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| Remove `sosa:madeActuation` domain/range/subproperty mapping | still fails | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| Remove source `sosa:usedProcedure` property-chain axioms | still fails | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| Remove `sosa:usedProcedure rdfs:subPropertyOf cco:ont00001920` | still fails | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| Remove active `ssn:implements` domain/range mapping | still fails | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| Remove source `sosa:Actuator` `ssn:implements` min-cardinality restriction | still fails | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| Remove source `sosa:Actuation` `sosa:usedProcedure` all-values restriction | still fails | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |

These reducers confirm that the strongest local dependencies are:

- the explicit range axiom;
- `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833`;
- active `sosa:Actuator` mapping;
- active `sosa:Actuation` mapping;
- source packages for `sosa:Actuator` and `sosa:Actuation`.

They also show that the simplified `ActuationRange` mapping is not required for the core conflict. Removing it removes only `ssn-system:ActuationRange` from the reported unsat set.

## Bottom-Up Extraction Attempts

Small local extractions did not reproduce the failure.

| Variant | Included context | Triples | Result |
|---|---|---:|---|
| S1 | Source `Actuation` / `Actuator` / `madeByActuator` / `madeActuation` plus explicit range | 70 | clean |
| S2 | S1 plus `madeByActuator` domain/subproperty mapping | 72 | clean |
| S3 | S1 plus active `Actuator` mapping | 94 | clean |
| S4 | S1 plus active `Actuation` mapping | 80 | clean |
| S5 | S1 plus `madeByActuator`, `Actuator`, and `Actuation` mappings | 106 | clean |
| S6 | S5 plus local target closure | 444 | clean |
| S7 | S6 plus source/simplified `ActuationRange` context | 622 | clean |

Full CCO plus full SSN source also remained clean until broader mapping context was added.

| Variant | Included context | Triples | Result |
|---|---|---:|---|
| T0 | Full CCO + full SSN source, explicit range, no SSN2BFO mappings | 14159 | clean |
| T1 | T0 plus `madeByActuator` mapping | 14161 | clean |
| T2 | T1 plus `Actuation` mapping | 14171 | clean |
| T3 | T1 plus `Actuator` mapping | 14186 | clean |
| T4 | T1 plus `Actuation` and `Actuator` mappings | 14196 | clean |
| T5 | T4 plus `madeActuation` mapping | 14199 | clean |
| T6 | T5 plus `usedProcedure` and `implements` mappings | 14202 | clean |
| T7 | T6 plus SSN Systems source and `ActuationRange` mapping | 14557 | clean |

Conclusion from these bottom-up attempts: the local `madeByActuator` / `Actuator` / `Actuation` core plus CCO target context is not sufficient to reproduce the full failure.

## Mapping-Group Reconstruction

The next reconstruction started from the full source/import graph, added the selected local core mapping subjects, and then added broader SSN2BFO mapping groups.

Selected local core mapping subjects:

```text
sosa:madeByActuator
sosa:madeActuation
sosa:Actuation
sosa:Actuator
sosa:usedProcedure
ssn:implements
ssn-system:ActuationRange
```

Results:

| Variant | Added mapping groups | Triples | Result |
|---|---|---:|---|
| W0 | selected local core only | 14557 | clean |
| W1 | all SSN2BFO subject packages, excluding `owl:imports` | 15527 | fails: `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| W2 | selected local core + all SOSA mappings + all core SSN mappings | 14936 | fails: `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| W3 | selected local core + all SOSA mappings + all SSN Systems mappings | 15448 | clean |
| W4 | selected local core + all core SSN mappings + all SSN Systems mappings | 15225 | clean |
| W5 | selected local core + all SOSA/core SSN/SSN Systems mappings | 15526 | fails: `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| W6 | selected local core + non-SOSA/non-SSN support subjects | 14558 | clean |

This isolates the broader dependency to a mixed SOSA + core SSN mapping context, not SSN Systems mappings as a group.

## Finer Mapping-Group Split

Adding all SOSA mappings to the selected local core was clean. Adding all core SSN mappings to the selected local core was also clean. Their combination failed.

Further minimization showed:

- with all SOSA mappings present, adding only the `ssn:System` mapping reproduced the failure;
- with all core SSN mappings present, no individual remaining SOSA subject reproduced the failure;
- with only `ssn:System` present, no individual remaining SOSA subject reproduced the failure;
- with only `ssn:System` present, SOSA class mappings alone were clean;
- SOSA property mappings alone were clean;
- SOSA property-chain mappings alone were clean;
- any pair of those SOSA mapping categories was clean;
- all SOSA mapping categories together plus `ssn:System` reproduced the failure.

Key results:

| Variant | Included mapping context | Triples | Result |
|---|---|---:|---|
| Y | selected local core + all SOSA mappings + `ssn:System` | 14868 | fails: `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| Q1 | selected local core + `ssn:System` + SOSA class mappings | 14809 | clean |
| Q2 | selected local core + `ssn:System` + SOSA property mappings | 14608 | clean |
| Q3 | selected local core + `ssn:System` + SOSA property-chain mappings | 14597 | clean |
| Q4 | selected local core + `ssn:System` + SOSA class/property mappings | 14850 | clean |
| Q5 | selected local core + `ssn:System` + SOSA class/chain mappings | 14839 | clean |
| Q6 | selected local core + `ssn:System` + SOSA property/chain mappings | 14624 | clean |
| Q7 | selected local core + `ssn:System` + all SOSA mappings | 14868 | fails: `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| Q8 | same as Q7, but without active `ActuationRange` mapping | 14840 | fails: `sosa:Actuator`; `sosa:Actuation` |

The smallest tested reproducing component set for the full three-class cluster is:

```text
full source/import graph
+ explicit sosa:madeByActuator range axiom
+ selected local core mappings
+ ssn:System mapping
+ all current SOSA mapping subjects
```

The smallest tested reproducing component set for the core two-class conflict is the same, but without the active `ssn-system:ActuationRange` mapping:

```text
sosa:Actuator
sosa:Actuation
```

No tested individual SOSA mapping subject, and no tested pair of SOSA mapping categories, reproduced the failure with `ssn:System`.

## Relevant `ssn:System` Mapping

The `ssn:System` mapping implicated by the minimization is:

```ttl
ssn:System
  owl:equivalentClass [
    owl:intersectionOf (
      bfo:BFO_0000040
      [ owl:onProperty ssn:implements ;
        owl:someValuesFrom sosa:Procedure ]
    )
  ] .
```

This connects systems to material entity typing plus a procedure implementation commitment. Since `sosa:Actuator` is a source subclass of `ssn:System`, this mapping participates in the mixed context once the broader SOSA mapping set is present.

## Assessment

### Does the explicit range axiom still fail after `ActuationRange` simplification?

Yes. The full M2 graph plus:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

still fails with:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

### Does the current baseline still entail effective range behavior?

Yes, by the probe test. The class:

```text
sosa:madeByActuator some (not sosa:Actuator)
```

is unsatisfiable, while both:

```text
sosa:madeByActuator some owl:Thing
sosa:madeByActuator some sosa:Actuator
```

are satisfiable.

This repeats the redundancy discrepancy in the post-PR #134 baseline.

### What is the smallest reproducing component set found?

The smallest tested reproduction for the full three-class set is the full source/import graph plus:

- explicit `sosa:madeByActuator rdfs:range sosa:Actuator`;
- selected local core mappings around `madeByActuator`, `madeActuation`, `Actuation`, `Actuator`, `usedProcedure`, `ssn:implements`, and `ActuationRange`;
- `ssn:System` mapping;
- all current SOSA mapping subjects.

That graph has 14868 triples and reproduces the full three-class failure.

The smallest tested reproduction for the core two-class conflict removes the `ActuationRange` mapping and still fails with:

```text
sosa:Actuator
sosa:Actuation
```

That graph has 14840 triples.

### Is `ssn-system:ActuationRange` still required?

No. `ActuationRange` is not required for the core failure. It is still pulled into the full reported set when its active mapping is present, but removing that mapping leaves the core `sosa:Actuator` / `sosa:Actuation` conflict.

### Is the core conflict only local `madeByActuator` / `Actuator` / `Actuation` plus CCO `has_agent`?

No. Local extractions containing the source `madeByActuator` / `Actuator` / `Actuation` context, active local mappings, CCO target context, and even `ActuationRange` context remained HermiT-clean.

The reproducer requires broader mapping context:

```text
ssn:System mapping
+ distributed current SOSA mapping set
+ local madeByActuator / Actuator / Actuation core
```

### Is the issue mapping-side, source-side, or graph-construction?

The issue is mixed.

Reducer evidence points to these necessary or high-impact ingredients:

- explicit `sosa:madeByActuator rdfs:range sosa:Actuator`;
- `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833`;
- active `sosa:Actuator` mapping;
- active `sosa:Actuation` mapping;
- source packages for `sosa:Actuator` and `sosa:Actuation`;
- `ssn:System` mapping;
- distributed SOSA mapping context.

The same graph-construction function was used for baseline, explicit-range, probe, reducer, and reconstruction variants. The stale-temp-file explanation is therefore less likely for this run.

However, the monotonicity discrepancy remains: the baseline probe still indicates effective range behavior, while the explicit `rdfs:range` axiom still causes named-class unsatisfiability. This report does not resolve that explanation-level mismatch.

### Is `ssn-system:SystemProperty` implicated?

No direct evidence from this minimization makes the active `ssn-system:SystemProperty` mapping or its `cco:prescribed_by` branch necessary for the core `madeByActuator` / `Actuator` / `Actuation` failure.

The strongest evidence is that the failure reproduces in Variant W2 with:

```text
selected local core mappings
+ all SOSA mappings
+ all core SSN mappings
```

and without adding the active SSN Systems mapping group that contains `ssn-system:SystemProperty`.

Likewise, Variant Q8 removes the active `ssn-system:ActuationRange` mapping from the smallest reproducing context and still reports the core two-class failure:

```text
sosa:Actuator
sosa:Actuation
```

That said, this branch did not run a dedicated `SystemProperty` or `prescribed_by` minimization. The active `SystemProperty` mapping remains a possible follow-up issue only in the weaker sense that many SSN Systems class mappings use `cco:prescribed_by` patterns, and those patterns have been high-impact elsewhere. It should not be treated as implicated in this specific minimal reproducer without a separate report-only test.

## Recommendation

Do not add:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The next branch should focus on the mixed mapping context identified here, especially the interaction among:

- `sosa:madeByActuator -> cco:ont00001833`;
- `sosa:Actuator` mapping;
- `sosa:Actuation` mapping;
- `ssn:System` mapping;
- the distributed SOSA mapping set.

Recommended next branch:

```text
review/design-madeByActuator-agent-mapping-adjustment
```

That branch should test HermiT-safe alternatives for the `madeByActuator` / CCO has-agent representation in temporary graphs before any mapping edit. It should keep the `ActuationRange` simplification separate, because `ActuationRange` is no longer required for the core failure.
