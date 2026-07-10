# `sosa:madeByActuator` Range After Agent Deferral

## Scope

This report documents the narrow mapping-change implementation recommended by:

```text
reports/rerun-prior-clean-decisions-full-sosa.md
```

The change adds the source-level range axiom for `sosa:madeByActuator` after the paired actuation-side CCO agent mappings were deferred and the full local SOSA closure HermiT rerun showed this source-level range axiom is clean.

No imports, examples, tools, release artifacts, or unrelated mappings were edited.

## TTL Change

Added to `SSN2BFO.ttl`:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The active `madeByActuator` source-level domain axiom remains:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

The resulting TTL block is:

```ttl
<http://www.w3.org/ns/sosa/madeByActuator>
    rdfs:domain <http://www.w3.org/ns/sosa/Actuation> ;
    rdfs:range <http://www.w3.org/ns/sosa/Actuator> .
```

## CCO Agent Mappings Remain Deferred

The failed actuation-side CCO agent mappings were not reintroduced:

```ttl
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

The local comments remain in the TTL near the actuation properties:

```text
Direct CCO agent-in property mapping deferred with madeByActuator pending HermiT-safe treatment.
Direct CCO has-agent property mapping deferred with madeActuation pending HermiT-safe treatment.
```

## Workbook Update

Updated workbook:

```text
Current_SOSA-SSN to BFO-CCO.xlsx
```

Changed row:

| Sheet | Row | Source term | Cell | Change |
|---|---:|---|---|---|
| `Common OPs` | 28 | `sosa:madeByActuator` | `E28` | Added `sosa:madeByActuator rdfs:range sosa:Actuator .` alongside the existing source-level domain and source inverse note. |
| `Common OPs` | 28 | `sosa:madeByActuator` | `F28` | Updated rationale to say the OWL operationalization now records source-level domain/range typing and that the direct CCO has-agent mapping remains deferred for full-SOSA-closure HermiT safety. |

Final `E28`:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:madeByActuator rdfs:range sosa:Actuator .
sosa:madeByActuator owl:inverseOf sosa:madeActuation .
```

Final `F28`:

```text
OWL operationalization now records source-level domain/range typing: domain sosa:Actuation and range sosa:Actuator. Direct CCO has-agent mapping remains deferred/removed as part of the paired actuation-agent deferral required for HermiT safety under the materialized SOSA import closure. This does not reject the intended agent semantics; future CCO/BFO agent representation should be reviewed for HermiT-safe OWL or rule/COMS treatment.
```

## Count Changes

| Count | Before | After | Change |
|---|---:|---:|---:|
| `ttl_candidate_mapping_assertions` | 68 | 68 | 0 |
| ELK direct property expectations | 75 | 75 | 0 |
| ELK direct class expectations | 6 | 6 | 0 |
| ELK property-chain expectations | 5 | 5 | 0 |
| ELK restriction expectations | 2 | 2 | 0 |

The source-level range axiom is outside the direct-property entailment expectation count used by `tools/test_elk_instance_mapping_entailments.py`.

## Mapping Audit

`make audit-write` passed after the TTL/workbook update:

```text
inspected_sheets=5
spreadsheet_rows=93
ttl_candidate_mapping_assertions=68
issues=2
missing_in_spreadsheet=1
missing_in_ttl=1
```

The two issues remain the known expected `sosa:Sensor` version-alignment issues.

`reports/mapping-consistency-audit.csv` changed because the audit was regenerated.

## ELK Report

`tools/test_elk_instance_mapping_entailments.py` passed:

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

The tracked `reports/elk-instance-mapping-entailments.md` file did not change.

## Full Local SOSA Closure HermiT Result

Command:

```bash
python tools/test_full_sosa_closure_hermit.py \
  --output reports/full-sosa-closure-hermit-check.md
```

Result:

| Item | Result |
|---|---:|
| graph path | `/tmp/ssn-to-bfo-full-sosa-closure-hermit-check/full-sosa-closure-hermit.ttl` |
| triple count before reasoning | 15769 |
| HermiT return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |

The tracked full-SOSA closure baseline report changed only by increasing the graph triple count from `15768` to `15769`.

## Validation

Commands:

```bash
python tools/test_full_sosa_closure_hermit.py \
  --output reports/full-sosa-closure-hermit-check.md

python tools/run_validation_suite.py

python tools/workflow_check.py --mode mapping-change \
  --expected-file SSN2BFO.ttl \
  --expected-file "Current_SOSA-SSN to BFO-CCO.xlsx" \
  --expected-file reports/madeByActuator-range-after-agent-deferral.md \
  --expected-file reports/mapping-consistency-audit.md \
  --expected-file reports/mapping-consistency-audit.csv \
  --expected-file reports/full-sosa-closure-hermit-check.md

git diff --check
```

Actual result after report creation:

```text
Full local SOSA closure HermiT check: PASS
Validation suite: PASS
Python compile check: PASS
Git whitespace check: PASS
git diff --check: PASS
```

`workflow_check.py --mode mapping-change` passed with all supplied expected files present and no unexpected changed files from the expected-file comparison. It also printed the generic mapping-change scope reminder because the requested new report name does not contain `hermit`; this is a workflow-helper warning, not a validation failure.

## Conclusion

The source-level `sosa:madeByActuator rdfs:range sosa:Actuator` axiom is now active and HermiT-clean under the current full local SOSA closure profile.

The old CCO agent / agent-in mappings remain deferred. This branch does not claim those CCO agent semantics are invalid; it only operationalizes the source-level SOSA range now that the direct CCO mappings are out of the active full-closure profile.
