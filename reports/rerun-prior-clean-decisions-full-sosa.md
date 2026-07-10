# Rerun Prior Clean Decisions Under Full SOSA Closure

## Scope

This report reruns and classifies prior HermiT-clean / HermiT-safe decisions under the current full local SOSA closure validation profile.

No mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

The current full local SOSA closure graph is built from:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

After loading, the graph removes:

```ttl
owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty .
sosa:hasSample rdf:type owl:InverseFunctionalProperty .
```

## Current Baseline

The current validation suite includes `tools/test_full_sosa_closure_hermit.py`, so ordinary validation now has both ELK instance-entailment coverage and full local SOSA closure HermiT consistency coverage.

Current expected baseline:

| Item | Result |
|---|---:|
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 68 |
| audit issues | 2 expected `sosa:Sensor` version-alignment issues only |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 75 |
| property-chain expectations | 5 |
| restriction expectations | 2 |
| active direct/property-chain/restriction mappings not covered | 0 |
| full SOSA closure HermiT | PASS |

The direct rerun command required for this report was:

```bash
python tools/test_full_sosa_closure_hermit.py --output /tmp/full-sosa-current.md
```

Result:

| Item | Result |
|---|---:|
| return code | 0 |
| triple count | 15768 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |

This confirms that all currently active mappings, including the previously added source-level domain/range axioms that remain active, are clean under the current full local SOSA closure.

## Audit Rule

This report applies the rule from `reports/prior-decision-audit-full-sosa-closure.md`:

- A prior reduced-M2 HermiT failure remains useful as evidence of a problem in at least one profile, but the explanation may change.
- A prior reduced-M2 HermiT-clean result does not prove full-SOSA-closure safety unless rerun or unless the current full baseline already includes the tested axioms.
- Current active mappings are collectively guarded by the new full SOSA closure HermiT check.
- Held-back candidate axioms still require direct full-closure retesting.
- ELK instance-entailment tests are coverage/regression checks, not full-closure HermiT consistency checks.

## Prior Decision Classification

| Report / decision family | Classification | Full-SOSA interpretation |
|---|---|---|
| `reports/full-sosa-closure-hermit-check.md` | A. Confirmed under current full SOSA closure | Current baseline is HermiT-clean with `owl:Nothing` count 0 and no unsats. |
| `reports/actuation-agent-property-mapping-deferral.md` | A. Confirmed under current full SOSA closure | Deferring both actuation-side CCO agent mappings cleared the full-closure `sosa:Actuator` / `sosa:Actuation` / `ssn-system:ActuationRange` cluster. |
| Current active 55 source-level domain/range additions from `reports/hermit-clean-source-domain-range-axioms.md` | A. Confirmed as part of current active baseline | The active subset is included in the current full-closure clean graph. |
| `sosa:madeByActuator rdfs:range sosa:Actuator` held back by `reports/hermit-clean-source-domain-range-axioms.md` | C. Superseded by full SOSA closure after paired agent deferral | The old reduced-M2 failure no longer reproduces in the current full-closure graph. Variant V1 below is HermiT-clean. |
| `reports/materialized-sosa-import-hermit-evaluation.md` | A. Confirmed / historical transition evidence | Correctly identified that materialized SOSA changed the baseline and implicated the paired actuation-side CCO agent mappings. |
| `reports/sosa-actuation-agent-unsat-explanation.md` | A. Confirmed / current explanation evidence | Its key conclusion remains supported: direct CCO agent mappings are not HermiT-safe in the full local SOSA closure. |
| `reports/madeByActuator-range-hermit-failure.md`, `reports/madeByActuator-range-redundancy-debug.md`, `reports/madeByActuator-range-minimal-reproduction.md`, `reports/madeByActuator-agent-mapping-adjustment-evaluation.md` | C. Superseded by full SOSA closure | Their reduced-M2 evidence remains historically useful, but the current full-closure rerun changes the practical conclusion for the source-level range axiom. |
| `reports/actuation-range-simplification-evaluation.md`, `reports/actuation-range-simplification-implementation.md` | A/B. Active state confirmed, original HermiT evidence reduced-M2 | The current simplified `ActuationRange` mapping is included in the full-closure clean baseline, but the original simplification tests should be read as reduced-M2 evidence. |
| `reports/system-property-mapping-simplification-evaluation.md`, `reports/system-property-direct-mapping-deferral.md` | A/B. Active state confirmed, original HermiT evidence reduced-M2 | The current `SystemProperty` deferral state is included in the full-closure clean baseline. |
| `reports/hermit-clean-baseline-after-deferrals.md` | C. Superseded | The old clean baseline omitted `imports/sosa.ttl`; the current full-closure baseline replaces it. |
| `reports/hermit-input-output-mapping-evaluation.md`, `reports/hermit-input-output-deferral-evaluation.md`, `reports/hermit-hasInput-reactivation-canary.md`, `reports/hermit-hasOutput-reactivation-canary.md`, `reports/input-output-reactivation-results.md` | B. Reduced-M2-only but still useful evidence | Failed canaries remain evidence of unsafe direct CCO mappings in at least one profile. Future reactivation/design work should use full closure. |
| `reports/hermit-observedProperty-deferral-evaluation.md`, `reports/hermit-observedProperty-reactivation-canary.md` | B. Reduced-M2-only but still useful evidence | Failed canary remains useful, but the observation/sensor explanation may change under materialized SOSA inverse context. |
| SSN Systems dependence reports: `reports/hermit-hasOperatingProperty-reactivation-canary.md`, `reports/hermit-hasSurvivalProperty-reactivation-canary.md`, `reports/hermit-hasSystemProperty-reactivation-canary.md`, `reports/ssn-systems-dependence-reactivation-results.md`, `reports/deferred-reactivation-results.md` | B. Reduced-M2-only but still useful evidence | Failed direct-dependence reactivation canaries remain useful. Future representation candidates should run under full closure. |
| `reports/reasoner-safe-replacement-mapping-review.md` and other ELK-oriented coverage reports | E. Not applicable as full-SOSA HermiT evidence | Useful for mapping coverage and regression expectations, but not full-closure consistency evidence. |
| Spreadsheet/TTL audit reports and policy reports | E. Not applicable to full-SOSA HermiT closure | Mostly unaffected unless a specific decision used imported SOSA axioms as mapping evidence. |

## Full-Closure Rerun Variants

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-rerun-prior-clean-decisions-full-sosa
```

Each variant used the current full local SOSA closure graph and standard cleanup.

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| V0 | current full SOSA closure baseline | `/tmp/ssn-to-bfo-rerun-prior-clean-decisions-full-sosa/V0.ttl` | 15768 | 0 | yes | 0 | 0 | clean |
| V1 | add `sosa:madeByActuator rdfs:range sosa:Actuator` | `/tmp/ssn-to-bfo-rerun-prior-clean-decisions-full-sosa/V1.ttl` | 15769 | 0 | yes | 0 | 0 | clean |
| V2 | re-add only `sosa:madeActuation rdfs:subPropertyOf cco:ont00001787` | `/tmp/ssn-to-bfo-rerun-prior-clean-decisions-full-sosa/V2.ttl` | 15769 | 1 | no | n/a | 3 | `sosa:Actuation`, `sosa:Actuator`, `ssn-system:ActuationRange` |
| V3 | re-add only `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` | `/tmp/ssn-to-bfo-rerun-prior-clean-decisions-full-sosa/V3.ttl` | 15769 | 1 | no | n/a | 3 | `sosa:Actuation`, `sosa:Actuator`, `ssn-system:ActuationRange` |
| V4 | re-add both actuation-side CCO agent mappings | `/tmp/ssn-to-bfo-rerun-prior-clean-decisions-full-sosa/V4.ttl` | 15770 | 1 | no | n/a | 3 | `sosa:Actuation`, `sosa:Actuator`, `ssn-system:ActuationRange` |
| V5 | re-add both actuation-side CCO agent mappings plus explicit `madeByActuator` range | `/tmp/ssn-to-bfo-rerun-prior-clean-decisions-full-sosa/V5.ttl` | 15771 | 1 | no | n/a | 3 | `sosa:Actuation`, `sosa:Actuator`, `ssn-system:ActuationRange` |
| V6 | other held-back source-level domain/range axiom | not run | n/a | n/a | n/a | n/a | n/a | No other held-back source-level domain/range axiom was identified in the prior source-domain/range reports. |

## Variant Interpretation

V0 confirms the current full local SOSA closure baseline is clean.

V1 is the most important rerun for source-level domain/range operationalization. The previously held-back source-level range axiom:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

is now HermiT-clean under the current full closure after the paired actuation-agent CCO mappings have been deferred.

V2 and V3 show that either old actuation-side CCO agent mapping is now individually unsafe if reintroduced into the current full closure:

```ttl
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

Each individual reactivation reproduces the same three unsatisfiable classes:

```text
sosa:Actuation
sosa:Actuator
ssn-system:ActuationRange
```

V4 confirms that re-adding both old actuation-side CCO agent mappings reproduces the previous full-closure failure.

V5 confirms that the explicit source-level range axiom does not change the paired-agent failure. The failing ingredient remains the old CCO agent mapping path, not the source-level `madeByActuator` range under the current profile.

## SOSA Inverse-Property Pair Review

The materialized `imports/sosa.ttl` asserts inverse relations for the following pairs. The table records active `SSN2BFO.ttl` mapping content for each side.

| Pair | SOSA inverse asserted | Active mapping side A | Active mapping side B | Both sides mapped to inverse target relations? | Risk finding |
|---|---|---|---|---|---|
| `madeActuation / madeByActuator` | yes | `madeActuation`: domain `sosa:Actuator`; range `sosa:Actuation` | `madeByActuator`: domain `sosa:Actuation` | no | Current baseline clean because both direct CCO agent mappings are deferred. Re-adding either old CCO agent mapping fails. |
| `madeObservation / madeBySensor` | yes | `madeObservation`: `subPropertyOf cco:ont00001787`; domain `sosa:Sensor`; range `sosa:Observation` | `madeBySensor`: `subPropertyOf cco:ont00001833`; domain `sosa:Observation`; range `sosa:Sensor` | yes: `cco:ont00001787` inverse `cco:ont00001833` | High-risk structural analog to actuation; currently covered by the clean full-closure baseline, but should be handled carefully in future changes. |
| `madeSampling / madeBySampler` | yes | `madeSampling`: `subPropertyOf cco:ont00001787`; domain `sosa:Sampler`; range `sosa:Sampling` | `madeBySampler`: `subPropertyOf cco:ont00001833`; domain `sosa:Sampling`; range `sosa:Sampler` | yes: `cco:ont00001787` inverse `cco:ont00001833` | High-risk structural analog to actuation; currently covered by the clean full-closure baseline. |
| `isActedOnBy / actsOnProperty` | yes | `isActedOnBy`: `subPropertyOf cco:ont00001886`; domain `sosa:ActuatableProperty`; range `sosa:Actuation` | `actsOnProperty`: `subPropertyOf cco:ont00001834`; domain `sosa:Actuation`; range `sosa:ActuatableProperty`; `rdf:type owl:ObjectProperty` | yes: `cco:ont00001886` inverse `cco:ont00001834` | High-risk because both sides map to inverse target relations; current baseline is clean. |
| `isHostedBy / hosts` | yes | `isHostedBy`: property chain over BFO realization/bearer path; `rdf:type owl:ObjectProperty` | `hosts`: property chain over BFO inheres-in/realized-in/participant path; `rdf:type owl:ObjectProperty` | no direct inverse target pair | Covered by current full-closure baseline; still watch because both sides have active complex mapping content. |
| `isObservedBy / observes` | yes | `isObservedBy`: domain `sosa:ObservableProperty`; range `sosa:Sensor` | `observes`: `subPropertyOf ssn:forProperty`; domain `sosa:Sensor`; range `sosa:ObservableProperty` | no direct inverse target pair | Covered by current full-closure baseline; not the same CCO inverse-agent pattern. |
| `isResultOf / hasResult` | yes | `isResultOf`: `subPropertyOf cco:ont00001816` | `hasResult`: `subPropertyOf cco:ont00001986` | yes: `cco:ont00001816` inverse `cco:ont00001986` | High-risk inverse target pair; current baseline is clean. |

No active mapping is currently suspect merely because the full-closure baseline passes. The table identifies future-analysis risk, not current unsatisfiability.

## ELK Distinction

`tools/test_elk_instance_mapping_entailments.py` is still best understood as an instance-entailment coverage check, not a full-closure consistency check. Its report text says it is not full OWL DL reasoning and not HermiT.

`tools/run_validation_suite.py` now includes both:

- ELK instance mapping entailment coverage; and
- the full local SOSA closure HermiT consistency check.

No prior ELK-based decision needs rerun simply because `imports/sosa.ttl` exists. The needed correction is interpretive: ELK coverage should not be cited as full-SOSA HermiT consistency evidence. Full-closure consistency is now guarded separately.

## Answers

Which prior decisions are confirmed under the current full SOSA closure?

- The current active mapping state after paired actuation-agent deferral.
- The current active source-level domain/range subset.
- The current simplified `ActuationRange` mapping state.
- The current deferred `SystemProperty` direct-mapping state.
- The full-closure baseline report and validation check.

Which prior reports should be read as reduced-M2-only?

- Earlier HermiT clean baselines, source-domain/range clean tests, Input/Output canaries, `observedProperty` canaries, SSN Systems dependence canaries, and pre-materialization `madeByActuator` diagnostics unless they explicitly included `imports/sosa.ttl`.

Which prior conclusions were superseded by materializing SOSA?

- The old explanation that the explicit `madeByActuator` range axiom itself was the practical blocker. Under the current full closure, V1 shows it is now HermiT-clean.

Are any active mappings still suspect after the full-closure guardrail passes?

- No active mapping is currently HermiT-suspect merely from these reruns. Some inverse-property pairs are high-risk for future analysis because both sides map to inverse target relations, but the active graph is clean.

Does explicit `madeByActuator` range now pass or fail under current full closure?

- It passes. V1 is HermiT-clean with return code 0 and no unsats.

Does re-adding either actuation-side CCO agent mapping individually pass or fail?

- Both fail individually. V2 and V3 each reproduce `sosa:Actuation`, `sosa:Actuator`, and `ssn-system:ActuationRange`.

Does re-adding both reproduce the previous failure?

- Yes. V4 reproduces the same three unsatisfiable classes.

Are there other SOSA inverse-property pairs that need focused analysis?

- Yes, especially `madeObservation` / `madeBySensor`, `madeSampling` / `madeBySampler`, `isActedOnBy` / `actsOnProperty`, and `isResultOf` / `hasResult`, because both sides currently map to inverse CCO/BFO target relations. They are covered by the current clean baseline but remain high-risk future-change areas.

## Recommendation

Recommend exactly one next branch:

```text
fix/add-madeByActuator-range-after-agent-deferral
```

Rationale: V1 directly shows that the previously held-back source-level axiom:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

is now HermiT-clean under the current full local SOSA closure after the paired CCO agent mappings were deferred. This is the narrowest directly supported mapping follow-up from the rerun. The branch should add only that source-level range axiom, update only the corresponding workbook row, regenerate affected reports, and preserve the full local SOSA closure HermiT check.

Do not reactivate either old actuation-side CCO agent mapping. V2 and V3 show each one still fails individually.

## Validation

Validation commands:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/rerun-prior-clean-decisions-full-sosa.md

git diff --check
```

Actual result after report creation:

```text
workflow_check.py --mode report-only: PASS
Validation suite: PASS
Full local SOSA closure HermiT check: PASS
Python compile check: PASS
Git whitespace check: PASS
Changed files not expected: none
Expected file present: reports/rerun-prior-clean-decisions-full-sosa.md
```
