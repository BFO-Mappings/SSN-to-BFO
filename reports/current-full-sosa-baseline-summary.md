# Current Full SOSA Baseline Summary

## Current Validation Baseline

This report summarizes the current validated baseline after materializing the local SOSA import, adding the full local SOSA closure HermiT validation check, deferring unsafe actuation-side CCO agent mappings, adding the source-level `sosa:madeByActuator` range axiom, and completing the current SOSA inverse-property-pair audit.

Validation command:

```bash
python tools/run_validation_suite.py
```

Result:

| Check / count | Current result |
|---|---:|
| validation suite status | PASS |
| `ttl_candidate_mapping_assertions` | 68 |
| mapping audit issues | 2 |
| mapping audit `missing_in_spreadsheet` | 1 |
| mapping audit `missing_in_ttl` | 1 |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 75 |
| ELK property-chain expectations | 5 |
| ELK restriction expectations | 2 |
| ELK expectation failures | 0 |
| uncovered active direct mappings | 0 |
| uncovered active property-chain mappings | 0 |
| uncovered active restriction mappings | 0 |

The two mapping audit issues are the known expected `sosa:Sensor` version-alignment issues:

```text
ISSUE-0001 missing_in_spreadsheet sosa:Sensor
ISSUE-0002 missing_in_ttl Common Classes row 18 sosa:Sensor
```

The validation suite also passed:

- Turtle parse check.
- Mapping consistency audit.
- Audit issue summary.
- Instance-data smoke test.
- ELK instance mapping entailment test.
- Full local SOSA closure HermiT check.
- Python compile check.
- Git whitespace check.

## Full Local SOSA Closure Profile

The full local SOSA closure HermiT profile loads:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Then it removes:

```ttl
owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty .
sosa:hasSample rdf:type owl:InverseFunctionalProperty .
```

Current full-closure HermiT result from `tools/run_validation_suite.py`:

| Item | Result |
|---|---:|
| triple count | 15769 |
| HermiT return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |
| full local SOSA closure HermiT status | PASS |

This is now the primary HermiT consistency guardrail for active mappings.

## Main Corrections Made

The current baseline reflects these main corrections and guardrails:

1. `imports/sosa.ttl` is now materialized locally, so diagnostics and validation can use the same local full SOSA closure profile instead of the older reduced M2 graph that omitted the indirect SOSA import.
2. `tools/test_full_sosa_closure_hermit.py` and the validation suite now protect the full local SOSA closure baseline.
3. The unsafe paired actuation-side CCO agent mappings remain deferred:

```ttl
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

4. Source-level typing remains active for the actuation pair, including:

```ttl
sosa:madeActuation rdfs:domain sosa:Actuator .
sosa:madeActuation rdfs:range sosa:Actuation .
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeByActuator rdfs:range sosa:Actuator .
```

5. The explicit `sosa:madeByActuator rdfs:range sosa:Actuator .` axiom is now active and HermiT-clean after the paired CCO agent mappings were deferred.

These corrections do not claim the intended actuation-agent semantics are invalid. They show that the old direct CCO property mapping form was not HermiT-safe together under the full local SOSA closure profile.

## SOSA Inverse-Property Audit Status

The current inverse-property-pair audit is complete for the selected SOSA pairs.

| Pair | Current status |
|---|---|
| `sosa:madeActuation` / `sosa:madeByActuator` | Already mitigated. Direct CCO agent mappings are deferred; source-level domain/range typing is active and full-closure clean. |
| `sosa:madeObservation` / `sosa:madeBySensor` | Focused full-closure analysis completed. Active state is HermiT-clean; no mapping change recommended. |
| `sosa:madeSampling` / `sosa:madeBySampler` | Focused full-closure analysis completed. Active state is HermiT-clean; no mapping change recommended. |
| `sosa:isActedOnBy` / `sosa:actsOnProperty` | Focused full-closure analysis completed. Active state is HermiT-clean; no mapping change recommended. |
| `sosa:isResultOf` / `sosa:hasResult` | Focused full-closure analysis completed. Active state is HermiT-clean; no mapping change recommended. |
| `sosa:isHostedBy` / `sosa:hosts` | Focused full-closure analysis completed. Active state is HermiT-clean; no mapping change recommended. |
| `sosa:isObservedBy` / `sosa:observes` | Focused full-closure analysis completed. Active state is HermiT-clean; no mapping change recommended. |

The audit supports closing the current inverse-property-pair review cycle. Future changes to these pairs should still be tested under the full local SOSA closure HermiT check before being merged.

## ELK Distinction

The ELK instance-entailment report remains a coverage and regression check for active mapping expectations. It is not a substitute for full local SOSA closure HermiT consistency.

Current ELK coverage result:

```text
Example files tested: 16
ROBOT pass/fail: 16/0
Total direct class expectations checked: 6
Total direct property expectations checked: 75
Total property-chain expectations checked: 5
Total restriction expectations checked: 2
Total expectation failures: 0
Active direct mappings not covered by instance data: 0
Active property-chain mappings not covered by instance data: 0
Active restriction mappings not covered by instance data: 0
Summary: PASS
```

The current validation suite now has both:

- ELK instance-entailment coverage; and
- full local SOSA closure HermiT consistency.

Consistency claims in this baseline rely on the full local SOSA closure HermiT result.

## Known Remaining Issues

The only current mapping audit issues are the two expected `sosa:Sensor` version-alignment issues:

| Issue type | Count | Scope |
|---|---:|---|
| `missing_in_spreadsheet` | 1 | `sosa:Sensor` |
| `missing_in_ttl` | 1 | `Common Classes` row 18, `sosa:Sensor` |

These issues are separate from HermiT cleanliness. The current full local SOSA closure is HermiT-clean with unsat count 0.

## Recommended Next Step

Recommended next branch:

```text
review/resolve-sosa-sensor-version-alignment
```

Purpose: resolve or document the remaining `sosa:Sensor` spreadsheet/TTL version-alignment gap while preserving the current validation baseline:

- validation suite PASS;
- ELK expectations covered with zero failures;
- full local SOSA closure HermiT PASS;
- unsat set clean.

## Validation

Validation commands for this report:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/current-full-sosa-baseline-summary.md

git diff --check
```

Result: PASS.

Workflow-check summary:

- Validation suite: PASS.
- Full local SOSA closure HermiT check: PASS.
- Python compile check: PASS.
- Git whitespace check: PASS.
- Expected changed file set: only `reports/current-full-sosa-baseline-summary.md`.
