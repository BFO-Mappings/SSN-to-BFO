# IsActedOnBy / ActsOnProperty Full-Closure Analysis

## Scope

This report is a focused, report-only analysis of the SOSA inverse-property pair:

```text
sosa:isActedOnBy / sosa:actsOnProperty
```

It follows `reports/sosa-inverse-property-pairs-full-closure-analysis.md`, which classified this pair as medium risk. This pair is actuation-adjacent, so it was checked after the mitigated `madeActuation` / `madeByActuator` issue and after the clean `madeObservation` / `madeBySensor` and `madeSampling` / `madeBySampler` reports.

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

## Full-Closure Method

All HermiT runs use the current full local SOSA closure graph built from:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

After loading, each graph removes:

```ttl
owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty .
sosa:hasSample rdf:type owl:InverseFunctionalProperty .
```

HermiT command pattern:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

## Baseline Confirmation

Command:

```bash
python tools/test_full_sosa_closure_hermit.py --output /tmp/full-sosa-current.md
```

Result:

| Item | Result |
|---|---:|
| triple count | 15769 |
| HermiT return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |

The current active full local SOSA closure is HermiT-clean.

## Pair Inventory

### SOSA Source Context

`imports/sosa.ttl` asserts the inverse relation on the `actsOnProperty` side:

```ttl
sosa:actsOnProperty owl:inverseOf sosa:isActedOnBy .
```

It records source-level domain/range notes using `schema:domainIncludes` and `schema:rangeIncludes`:

| Property | SOSA source note |
|---|---|
| `sosa:actsOnProperty` | Actuation -> ActuatableProperty |
| `sosa:isActedOnBy` | ActuatableProperty -> Actuation |

The materialized SOSA source file does not assert these notes as global `rdfs:domain` / `rdfs:range` axioms. Active logical source-level domain/range operationalization comes from `SSN2BFO.ttl`.

### SSN Source Restrictions

`imports/ssn.ttl` contains source restrictions that connect the pair to `sosa:Actuation` and `sosa:ActuatableProperty`:

| Source class | Restriction pattern |
|---|---|
| `sosa:ActuatableProperty` | `sosa:isActedOnBy only sosa:Actuation` |
| `sosa:Actuation` | `sosa:actsOnProperty only sosa:ActuatableProperty` |
| `sosa:Actuation` | `sosa:actsOnProperty minCardinality 1` |

These restrictions are active in the full local SOSA closure baseline.

### Active Mapping Context

`SSN2BFO.ttl` currently contains:

```ttl
sosa:actsOnProperty rdf:type owl:ObjectProperty ;
  rdfs:domain sosa:Actuation ;
  rdfs:range sosa:ActuatableProperty ;
  rdfs:subPropertyOf cco:ont00001834 .

sosa:isActedOnBy rdfs:domain sosa:ActuatableProperty ;
  rdfs:range sosa:Actuation ;
  rdfs:subPropertyOf cco:ont00001886 .
```

The CCO target properties are an inverse affected-by pair:

```ttl
cco:ont00001834 owl:inverseOf cco:ont00001886 .
cco:ont00001834 rdfs:subPropertyOf bfo:BFO_0000057 .
cco:ont00001886 rdfs:subPropertyOf bfo:BFO_0000056 .
```

Local labels and target constraints:

| CCO/BFO term | Local label / role |
|---|---|
| `cco:ont00001834` | `affects`; domain `bfo:Process`; range `bfo:Continuant`; subproperty of `bfo:has_participant` |
| `cco:ont00001886` | `is affected by`; domain `bfo:Continuant`; range `bfo:Process`; subproperty of `bfo:participates_in` |
| `bfo:BFO_0000057` | has-participant parent path |
| `bfo:BFO_0000056` | participates-in parent path |

### Related Class Mappings

The active local mapping for `sosa:Actuation` is:

```text
sosa:Actuation equivalentTo cco:PlannedAct and (sosa:actsOnProperty some sosa:ActuatableProperty)
```

The active local mapping for `sosa:ActuatableProperty` is:

```text
sosa:ActuatableProperty subClassOf
  (bfo:SpecificallyDependentContinuant and bfo:inheres_in some sosa:FeatureOfInterest)
  or
  (bfo:ProcessProfile and bfo:occurrent_part_of some sosa:FeatureOfInterest)
```

The second branch makes this pair worth tracking: CCO `affects` expects a continuant range, while the source-side `ActuatableProperty` mapping allows an occurrent-like process-profile branch. The current full closure remains clean despite that mixed profile.

### Workbook Context

The corresponding workbook rows are:

| Sheet | Row | Source term | Active OWL cell summary | Rationale summary |
|---|---:|---|---|---|
| `Common OPs` | 2 | `sosa:actsOnProperty` | domain `sosa:Actuation`; range `sosa:ActuatableProperty`; subproperty of `cco:affects` | source-level domain/range operationalization; existing CCO subproperty mapping unchanged |
| `Common OPs` | 19 | `sosa:isActedOnBy` | domain `sosa:ActuatableProperty`; range `sosa:Actuation`; inverse note; subproperty of `cco:ont00001886` | source-level domain/range operationalization; inverse and CCO affected-by mapping notes unchanged |

### Comparison Cases

Similarity to the mitigated actuation agent pair:

- The pair is actuation-adjacent.
- SOSA materializes an inverse relation between the two properties.
- Each side has source domain/range support.
- Source restrictions connect the source classes through the paired properties.
- Both sides map to inverse CCO/BFO target relations with participant parent paths.

Difference from the mitigated actuation agent pair:

- The target relations are `affects` / `is affected by`, not `has_agent` / `agent_in`.
- The target range/domain constraints align with actuation/process and actuatable-property/continuant intent more directly than the failed actuation-agent pair did.
- The paired CCO mappings are active in the current baseline, and the full local SOSA closure is HermiT-clean.

Comparison to the clean observation/sensor and sampling/sampler pairs:

- Like those pairs, this pair is active and full-closure clean.
- Unlike those pairs, this pair is actuation-specific and touches the same `sosa:Actuation` area as the previously mitigated issue.
- The target semantics differ from the agent pattern; this pair is about affected continuants/processes rather than process agents.

## Focused HermiT Variants

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis
```

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| V0 | Current full closure baseline | `/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis/V0.ttl` | 15769 | 0 | yes | 0 | 0 | clean |
| V1 | Remove only `sosa:actsOnProperty rdfs:subPropertyOf cco:ont00001834` | `/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis/V1.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V2 | Remove only `sosa:isActedOnBy rdfs:subPropertyOf cco:ont00001886` | `/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis/V2.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V3 | Remove both active CCO/BFO mappings for the pair | `/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis/V3.ttl` | 15767 | 0 | yes | 0 | 0 | clean |
| V4 | Add missing symmetric source-level domain/range axiom | skipped | n/a | n/a | n/a | n/a | n/a | No missing symmetric source-level domain/range axiom was identified. Both sides already have active source-level domain/range in `SSN2BFO.ttl`. |
| V5 | Test workbook-proposed missing CCO/BFO mapping | skipped | n/a | n/a | n/a | n/a | n/a | Both sides are already mapped to the workbook-proposed CCO/BFO target properties. |
| V6 | Remove the materialized SOSA inverse axiom `sosa:actsOnProperty owl:inverseOf sosa:isActedOnBy` | `/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis/V6.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V7 | Remove direct source class restrictions involving `sosa:isActedOnBy` / `sosa:actsOnProperty` | `/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis/V7.ttl` | 15757 | 0 | yes | 0 | 0 | clean |
| V8 | Remove active `sosa:Actuation` class-expression mapping only | `/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis/V8.ttl` | 15759 | 0 | yes | 0 | 0 | clean |
| V9 | Remove active `sosa:ActuatableProperty` class-expression mapping only | `/tmp/ssn-to-bfo-isActedOnBy-actsOnProperty-full-closure-analysis/V9.ttl` | 15744 | 0 | yes | 0 | 0 | clean |

V7 removed three direct source restrictions:

- `sosa:ActuatableProperty rdfs:subClassOf [ owl:onProperty sosa:isActedOnBy ; owl:allValuesFrom sosa:Actuation ]`
- `sosa:Actuation rdfs:subClassOf [ owl:onProperty sosa:actsOnProperty ; owl:allValuesFrom sosa:ActuatableProperty ]`
- `sosa:Actuation rdfs:subClassOf [ owl:onProperty sosa:actsOnProperty ; owl:minCardinality 1 ]`

V8 removed the active local `sosa:Actuation owl:equivalentClass` mapping expression while leaving source/imported restrictions intact.

V9 removed the active local `sosa:ActuatableProperty rdfs:subClassOf` union class-expression mapping while leaving source/imported restrictions intact.

All focused variants were HermiT-clean.

## Inverse Reconstruction Check

The pair has the structural ingredients for inverse-side coupling:

```text
sosa:actsOnProperty inverseOf sosa:isActedOnBy
cco:affects inverseOf cco:is_affected_by
```

So a one-sided mapping should be treated as coupled modeling context, even if only one direct subproperty assertion is present.

As a practical reasoned-output check, the V1/V2 reasoned graphs were inspected for the omitted direct subproperty triple:

| Variant | Removed direct mapping | Omitted direct subproperty materialized in reasoned output? |
|---|---|---|
| V1 | `sosa:actsOnProperty -> cco:affects` | no |
| V2 | `sosa:isActedOnBy -> cco:is_affected_by` | no |

This materialization check is not a complete OWL entailment proof. It does show that the tested reasoned outputs did not expose a simple materialized one-side reconstruction, and none of the one-sided removal variants revealed a HermiT problem.

## Interpretation

The current active `isActedOnBy` / `actsOnProperty` pair is HermiT-clean under the full local SOSA closure.

The pair is structurally analogous to the mitigated actuation agent pair in that it is an actuation-adjacent inverse-property pair with active inverse CCO/BFO targets and participant parent paths. It is not the same pattern, however:

- the target relations are affected-by/affects rather than agent-in/has-agent;
- the source property pair is about a process changing an actuatable property, not a device or agent making an actuation;
- the current active pair does not implicate the previously failing `sosa:Actuator` / `ssn-system:ActuationRange` context.

The actuation-specific context makes this pair worth keeping at medium-risk documentation level. The active `sosa:Actuation` class mapping, active `sosa:ActuatableProperty` mapping, source restrictions, and inverse property axiom are all in the neighborhood of the previous actuation failure. But the focused variants did not show an unsafe active mapping:

- the baseline full closure is clean;
- removing either direct CCO/BFO mapping is clean;
- removing both direct CCO/BFO mappings is clean;
- removing the materialized SOSA inverse is clean;
- removing source restrictions is clean;
- removing the active `sosa:Actuation` mapping is clean;
- removing the active `sosa:ActuatableProperty` mapping is clean.

The best current explanation is that this pair remains clean because the affected-by/affects target semantics are compatible enough with the current source and class mapping context, whereas the mitigated actuation agent failure involved the specific `madeActuation` / `madeByActuator` agent path together with the `sosa:Actuator` / `ssn-system:ActuationRange` context.

This does not prove the mapping pattern is risk-free. Future changes to `sosa:Actuation`, `sosa:ActuatableProperty`, `sosa:actsOnProperty`, `sosa:isActedOnBy`, or CCO affected-by/affects target context should continue to run the full local SOSA closure HermiT check.

## Recommendation

Recommend exactly one next step:

```text
No mapping change for sosa:isActedOnBy / sosa:actsOnProperty.
```

Keep the current mappings active and guarded by the full local SOSA closure HermiT validation check. This pair should remain documented as medium-risk because it is actuation-adjacent and has inverse CCO/BFO targets, but this focused analysis does not justify a mapping-change branch or an immediate follow-up branch for this pair.

## Validation

Validation commands:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/isActedOnBy-actsOnProperty-full-closure-analysis.md

git diff --check
```

Final result:

- `workflow_check.py --mode report-only`: PASS
- validation suite: PASS
- mapping audit: PASS with the two expected `sosa:Sensor` version-alignment issues only
- ELK direct property expectations: 75
- full local SOSA closure HermiT check: PASS (`15769` triples, return code `0`, `owl:Nothing` count `0`, unsat count `0`)
- Python compile check: PASS
- `git diff --check`: PASS
