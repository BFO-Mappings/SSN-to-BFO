# SOSA Sensor Version-Alignment Deferral

## Scope

This report documents why the two remaining `sosa:Sensor` mapping-audit issues are intentionally preserved for now.

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

Controlling prior report:

```text
reports/sosa-sensor-version-alignment-resolution.md
```

## Current State

The current tests-branch baseline is clean except for the two expected `sosa:Sensor` mapping-audit issues.

| Check / count | Current result |
|---|---:|
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 68 |
| mapping audit issues | 2 expected `sosa:Sensor` version-alignment issues |
| `missing_in_spreadsheet` | 1 |
| `missing_in_ttl` | 1 |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 75 |
| property-chain expectations | 5 |
| restriction expectations | 2 |
| uncovered active mappings | 0 |
| full local SOSA closure HermiT | PASS |
| full local SOSA closure unsat count | 0 |

The expected audit issues are:

```text
ISSUE-0001 missing_in_spreadsheet:
sosa:Sensor => bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Observation; cco:ont00001787

ISSUE-0002 missing_in_ttl:
Common Classes row 18:
sosa:Sensor => bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569
```

`sosa:Sensor` is not involved in any current HermiT unsatisfiable class set. The full local SOSA closure HermiT check is clean, and prior temporary variants showed both the current TTL mapping and the parsed workbook equivalence are HermiT-clean under the full local SOSA closure.

`sosa:Sensor` is also not currently covered by ELK direct class expectations. The current Sensor TTL mapping is a blank-node class expression, and the ELK direct-class extraction covers named `rdfs:subClassOf` targets rather than this expression shape.

## Current TTL Sensor Mapping

`SSN2BFO.ttl` currently keeps an explicit local CCO-compatible class expression for `sosa:Sensor`.

In compact form, the active TTL mapping says that a `sosa:Sensor` is a material entity that bears a realizable entity realized in an Observation, and that is agent-in some Observation. The prior report records the active expression as an `rdfs:subClassOf` blank-node class expression using:

```text
bfo:BFO_0000040
bfo:BFO_0000196
bfo:BFO_0000017
bfo:BFO_0000054
sosa:Observation
cco:ont00001787
```

This current TTL mapping is HermiT-clean under the full local SOSA closure. It is also aligned with the currently imported local CCO profile more directly than the workbook's forward-looking `cco:Sensor` equivalence.

This report does not claim that the current TTL expression is the final preferred Sensor mapping. It records only that it is the active, HermiT-clean mapping in the current local import profile.

## Workbook Sensor Mapping

The workbook row is:

```text
Current_SOSA-SSN to BFO-CCO.xlsx
Common Classes row 18
```

That row records a forward-looking `equivalentClass` / `equivalentTo` style mapping from `sosa:Sensor` to `cco:Sensor`, represented by the audit as a target summary involving:

```text
bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569
```

The row reflects a latest-CCO or target-version mapping direction. It is not currently asserted in `SSN2BFO.ttl`.

The current local `imports/cco.ttl` contains `cco:ont00000569` labeled `Sensor`, but the prior report found that the local import does not expose the workbook's stronger equivalent-class expansion as an authoritative current-local-CCO expression. That makes the workbook row useful as target-version intent, but not enough by itself to justify changing the active TTL mapping immediately.

## Why This Is Intentionally Deferred

The two audit issues are intentionally preserved because the TTL and workbook are aligned to different CCO/version/modeling assumptions.

The current TTL uses an explicit local CCO-compatible class expression. The workbook row is forward-looking and latest-CCO-oriented, recording an equivalence to `cco:Sensor`.

The prior report tested the important HermiT cases:

| Variant | Result |
|---|---|
| Current full local SOSA closure baseline | HermiT-clean |
| Remove current TTL `sosa:Sensor` class-expression mapping | HermiT-clean |
| Add parsed workbook `sosa:Sensor owl:equivalentClass cco:ont00000569` on top of current TTL mapping | HermiT-clean |
| Replace current TTL expression with parsed workbook equivalence | HermiT-clean |

Therefore the mismatch is not an immediate consistency problem. Changing either side now would choose a version/modeling target prematurely:

- updating the workbook to match the TTL would discard or weaken the workbook's latest-CCO direction;
- updating the TTL to match the workbook would assert a target-version equivalence that is not fully supported by the current local CCO import;
- revising both would require a dedicated Sensor modeling decision rather than a mechanical audit cleanup.

Preserving the expected issue is preferable until the project decides whether to:

1. update the local CCO imports or otherwise target the latest CCO profile;
2. retarget the workbook to the currently imported local CCO profile;
3. replace both the current TTL expression and workbook row with a revised Sensor mapping.

## Expected Issue Handling

The two `sosa:Sensor` audit issues should remain recognized expected issues for now.

They should not be treated as unexpected validation failures while this deferral is active. They should be revisited before release or when the project settles the CCO target-version policy for Sensor mappings.

The expected issue handling should be removed only after a future branch aligns `SSN2BFO.ttl` and `Current_SOSA-SSN to BFO-CCO.xlsx` consistently.

## Exit Criteria

This deferral can be resolved when all of the following are true:

1. The project has decided the CCO target version for `sosa:Sensor`.
2. The availability and intended IRI of `cco:Sensor` are confirmed in the local or target CCO import.
3. The project chooses whether `SSN2BFO.ttl` should use an equivalence to `cco:Sensor` or retain an explicit class-expression mapping.
4. The workbook and TTL are updated consistently.
5. The mapping audit expected-issue handling is removed after the mismatch is resolved.
6. The full local SOSA closure HermiT check remains clean.
7. ELK and mapping reports are regenerated if the chosen resolution affects them.

## Recommendation

Recommended next step:

```text
review/settle-sensor-cco-version-target
```

No immediate mapping change is recommended. Keep the current expected issue handling and revisit this only when the CCO target-version policy is settled.

## Validation

Validation commands for this report:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/sosa-sensor-version-alignment-deferral.md

git diff --check
```

Result: PASS.

Workflow-check summary:

- Validation suite: PASS.
- Mapping audit: PASS with only the two recognized expected `sosa:Sensor` version-alignment issues.
- Full local SOSA closure HermiT check: PASS.
- Python compile check: PASS.
- Git whitespace check: PASS.
- Expected changed file set: only `reports/sosa-sensor-version-alignment-deferral.md`.
