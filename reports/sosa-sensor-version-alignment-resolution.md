# SOSA Sensor Version-Alignment Resolution Analysis

## Scope

This report analyzes the remaining two expected mapping-audit issues for:

```text
sosa:Sensor
```

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

The goal is to decide whether the mismatch should be resolved by updating the workbook, updating the TTL, replacing both with a revised mapping, documenting an intentional deferral, or preserving expected-issue handling for now.

## Current Baseline

Command run:

```bash
python tools/run_validation_suite.py
```

Result:

| Check / count | Current result |
|---|---:|
| validation suite status | PASS |
| `ttl_candidate_mapping_assertions` | 68 |
| mapping audit issues | 2 |
| `missing_in_spreadsheet` | 1 |
| `missing_in_ttl` | 1 |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 75 |
| ELK property-chain expectations | 5 |
| ELK restriction expectations | 2 |
| uncovered active direct mappings | 0 |
| uncovered active property-chain mappings | 0 |
| uncovered active restriction mappings | 0 |
| full local SOSA closure HermiT | PASS |
| full local SOSA closure triple count | 15769 |
| full local SOSA closure `owl:Nothing` count | 0 |
| full local SOSA closure unsat count | 0 |
| full local SOSA closure unsat set | clean |

The only current mapping-audit issues are the two expected `sosa:Sensor` version-alignment issues.

## Current Sensor Context

### Source Definition

`imports/sosa.ttl` defines `sosa:Sensor` with the SOSA text:

```text
Device, agent (including humans), or software (simulation) involved in, or implementing, a Procedure. Sensors respond to a stimulus, e.g., a change in the environment, or input data composed from the results of prior Observations, and generate a Result. Sensors can be hosted by Platforms.
```

`imports/ssn.ttl` adds source restrictions:

```text
sosa:Sensor rdfs:subClassOf ssn:System
sosa:Sensor rdfs:subClassOf (sosa:madeObservation only sosa:Observation)
sosa:Sensor rdfs:subClassOf (sosa:observes only sosa:ObservableProperty)
sosa:Sensor rdfs:subClassOf (ssn:detects only ssn:Stimulus)
sosa:Sensor rdfs:subClassOf (ssn:implements min 1)
```

`imports/ssn-systems.ttl` also refers to `sosa:Sensor` in measurement/detection property restrictions, including `ssn-system:DetectionLimit` and `ssn-system:MeasurementRange` source contexts.

### Current Active TTL Mapping

`SSN2BFO.ttl` currently maps `sosa:Sensor` as a subclass expression:

```ttl
sosa:Sensor rdfs:subClassOf [
  owl:intersectionOf (
    bfo:BFO_0000040
    [ owl:onProperty bfo:BFO_0000196 ;
      owl:someValuesFrom [
        owl:intersectionOf (
          bfo:BFO_0000017
          [ owl:onProperty bfo:BFO_0000054 ;
            owl:someValuesFrom sosa:Observation
          ]
        )
      ]
    ]
    [ owl:onProperty cco:ont00001787 ;
      owl:someValuesFrom sosa:Observation
    ]
  )
] .
```

In compact terms, the TTL says every `sosa:Sensor` is:

```text
bfo:MaterialEntity
and bearer_of some (bfo:RealizableEntity and has_realization some sosa:Observation)
and cco:agent_in some sosa:Observation
```

This is an active intended current-CCO-compatible mapping and is full-local-SOSA-closure HermiT-clean.

### Workbook Row

Workbook row:

```text
Current_SOSA-SSN to BFO-CCO.xlsx
Common Classes row 18
```

Current row contents:

| Cell | Value summary |
|---|---|
| `A18` | `sosa:Sensor` |
| `B18` | SOSA source definition for Sensor |
| `C18` | `A bfo:MaterialEntity that bears a Sensor Function or a Sensor Role; equivalently, a cco:Sensor.` |
| `D18` | `An individual is a sosa:Sensor if and only if it is a cco:Sensor...` |
| `E18` | `equivalentTo cco:Sensor [ = bfo:MaterialEntity and (bfo:bearer_of some (cco:'Sensor Function' or cco:'Sensor Role')) ]` |
| `F18` | Says the row was updated from `subClassOf` to `equivalentTo`, aligned with `cco:Sensor (ont00000569)` in the latest CCO release. |

The audit parser treats the row as an expected `owl:equivalentClass` assertion involving `cco:ont00000569`, with target summary:

```text
bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569
```

### Local CCO Evidence

The current local `imports/cco.ttl` defines:

```ttl
cco:ont00000569 rdf:type owl:Class ;
  rdfs:subClassOf cco:ont00000736 ;
  rdfs:label "Sensor" ;
  skos:definition "A Transducer that is designed to convert incoming energy into a output signal which reliably corresponds to changes in that energy." .
```

`cco:ont00000736` is locally labeled `Transducer` and is a material-artifact class. The local import does not define `cco:ont00000569` as an equivalent class expression for:

```text
bfo:MaterialEntity and bearer_of some (Sensor Function or Sensor Role)
```

The local import contains `Sensor Artifact Function` (`cco:ont00001241`), but no local label match for `Sensor Role`. Therefore, the bracketed expansion in workbook `E18` is not exactly reconstructable from the current local CCO import as an authoritative active OWL expression.

### Prior Report Context

Prior reports already treated this as a version-targeted discrepancy:

- `reports/sensor-upcoming-cco-version-target-review.md` says the spreadsheet targets an upcoming CCO version and recommends deferring a TTL update until the relevant CCO version is imported or a future-version mapping track is created.
- `reports/sampler-sensor-class-mapping-reconciliation-review.md` says the spreadsheet `sosa:Sensor` equivalence is stronger than what is directly visible in the local CCO import.
- `reports/current-full-sosa-baseline-summary.md` identifies these as the only known remaining issues and recommends this review branch.

## Exact Audit Issues

### ISSUE-0001: `missing_in_spreadsheet`

Audit row:

```text
ISSUE-0001
category: missing_in_spreadsheet
source: sosa:Sensor
TTL predicate: rdfs:subClassOf
TTL target summary:
  bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054;
  bfo:BFO_0000196; sosa:Observation; cco:ont00001787
TTL line: 615
```

This issue is produced by the current active `SSN2BFO.ttl` subclass expression for `sosa:Sensor`.

Assessment:

| Question | Answer |
|---|---|
| Are these active intended mappings? | Yes, for the current local CCO import profile. |
| Are they HermiT-safe under full local SOSA closure? | Yes. V0 baseline and V1 removal confirm no current unsat dependency. |
| Are they supported by current source/mapping rationale? | Broadly yes: SOSA describes sensors as devices/agents involved in observations; source restrictions connect Sensors to Observations, madeObservation, observes, detects, and implements. |
| Should they be added to the workbook? | Not mechanically. Adding the current TTL expression to row 18 would contradict the workbook’s explicit latest-CCO `equivalentTo cco:Sensor` intent unless row 18 is intentionally retargeted to the current local CCO import. |
| Should they be removed/deferred from TTL? | Not now. They are active, HermiT-clean, and better aligned with the current local CCO import than the workbook’s forward-looking equivalence. |

### ISSUE-0002: `missing_in_ttl`

Audit row:

```text
ISSUE-0002
category: missing_in_ttl
sheet: Common Classes
spreadsheet row: 18
source: sosa:Sensor
spreadsheet relation: owl:equivalentClass
spreadsheet target summary:
  bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569
```

This issue is produced by workbook `Common Classes` row 18, especially cells `C18`, `D18`, `E18`, and `F18`.

Assessment:

| Question | Answer |
|---|---|
| Is the workbook mapping still intended? | It appears intended as a future/latest-CCO target, not as a current-local-CCO mapping. |
| Is it superseded by the current TTL mapping? | For the current local import profile, yes in practice. As a future target, no. |
| Is it HermiT-safe if tested directly? | Yes, the parsed canonical assertion `sosa:Sensor owl:equivalentClass cco:ont00000569` was HermiT-clean both on top of and in place of the current TTL expression. |
| Should TTL be updated now? | No. HermiT safety is not enough; the local CCO import does not support the workbook’s stronger equivalence claim as an authoritative current mapping. |
| Should the workbook row be revised/cleared now? | Not in a mapping-change branch unless the project decides the workbook should target only the currently imported CCO version. |

## HermiT Variants

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-sosa-sensor-version-alignment-resolution
```

All variants used the full local SOSA closure graph:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Cleanup:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| V0 | Current full closure baseline | `/tmp/ssn-to-bfo-sosa-sensor-version-alignment-resolution/V0-baseline.ttl` | 15769 | 0 | yes | 0 | 0 | clean |
| V1 | Remove current active `SSN2BFO.ttl` `sosa:Sensor` class-expression mapping | `/tmp/ssn-to-bfo-sosa-sensor-version-alignment-resolution/V1-remove-current-ttl-sensor-mapping.ttl` | 15745 | 0 | yes | 0 | 0 | clean |
| V2 | Add parsed workbook mapping on top of current TTL mapping: `sosa:Sensor owl:equivalentClass cco:ont00000569` | `/tmp/ssn-to-bfo-sosa-sensor-version-alignment-resolution/V2-add-workbook-equivalence-on-top.ttl` | 15770 | 0 | yes | 0 | 0 | clean |
| V3 | Replace current TTL Sensor expression with parsed workbook mapping: `sosa:Sensor owl:equivalentClass cco:ont00000569` | `/tmp/ssn-to-bfo-sosa-sensor-version-alignment-resolution/V3-replace-ttl-with-workbook-equivalence.ttl` | 15746 | 0 | yes | 0 | 0 | clean |
| V4 | Not run | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| V5 | Not run | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

V4 was not needed because V2 and V3 were HermiT-clean, so there was no failing workbook-only commitment to minimize.

V5 was not needed because V2 and V3 were HermiT-clean, so no compatibility debugging by adding TTL-only commitments one at a time was required.

These results show that both the current TTL mapping and the parsed workbook equivalence are HermiT-safe under the full local SOSA closure. They do not establish that the workbook equivalence is semantically authoritative for the currently imported CCO version.

## ELK / Instance Coverage

`reports/elk-instance-mapping-entailments.md` does not currently include a direct `sosa:Sensor` class expectation.

`tools/test_elk_instance_mapping_entailments.py` extracts direct class mappings only from named `rdfs:subClassOf` triples:

```python
for source, _, target in graph.triples((None, RDFS.subClassOf, None)):
    if source_term(source) and isinstance(target, URIRef):
        class_mappings.append(DirectMapping("class", source, target))
```

The current `sosa:Sensor` TTL mapping is a blank-node class expression, so it is outside the ELK direct-class expectation list. A named `owl:equivalentClass cco:ont00000569` assertion is also outside the current direct-class extraction logic.

Therefore:

- `sosa:Sensor` is not currently covered by ELK instance mapping expectations.
- Changing the Sensor mapping may not affect ELK direct class expectation counts unless the tooling is expanded or the change introduces named `rdfs:subClassOf` assertions.
- The current evidence is mainly mapping-audit/version-alignment evidence plus HermiT full-closure safety, not ELK coverage evidence.

## Resolution Options

### Option A: Update Workbook To Match Current TTL

This would revise `Common Classes` row 18 to describe the current explicit TTL subclass expression:

```text
sosa:Sensor subclassOf
  bfo:MaterialEntity
  and bearer_of some (RealizableEntity and has_realization some sosa:Observation)
  and agent_in some sosa:Observation
```

Pros:

- Aligns workbook with the current active TTL and current local CCO import.
- Would remove both current audit issues after regenerating the mapping audit.
- Low HermiT risk because the current active TTL mapping is already full-closure clean.

Cons:

- It would discard or weaken the workbook’s explicit latest-CCO/future-version intent.
- It would contradict prior notes saying not to weaken the spreadsheet row merely to match current TTL.
- It may be premature if the project expects a future CCO import where `cco:Sensor` has stronger equivalence semantics.

Risk: low technical risk, medium governance/version-target risk.

### Option B: Update TTL To Match Workbook

This would replace or augment the TTL with:

```ttl
sosa:Sensor owl:equivalentClass cco:ont00000569 .
```

Pros:

- HermiT variants V2 and V3 were clean.
- Aligns the TTL with workbook row 18.
- Would remove the current audit mismatch after regenerating reports.

Cons:

- The current local CCO import defines `cco:ont00000569` as `Sensor`, subclass of `Transducer`; it does not locally define the stronger workbook expansion.
- The workbook row says it is aligned with the latest CCO release, while the repo currently imports a CCO file that does not expose that stronger definition.
- It would make the active TTL depend on a version-target claim not visible in the imported ontology.

Risk: low HermiT risk, high semantic/version-authority risk.

### Option C: Revise Both To A New Sensor Mapping

This could mean a new expression that combines current SOSA-specific observation/agent semantics with an explicit `cco:Sensor` relationship.

Pros:

- Could eventually reconcile current local CCO, workbook intent, and SOSA-specific source semantics.
- Could remove the audit issue with a more explicit authoritative mapping.

Cons:

- No current report establishes the exact revised expression as the right semantic target.
- A hybrid mapping could overcommit if `cco:Sensor` remains only a `Transducer` in the local import.
- This would require a dedicated modeling branch, not a mechanical audit cleanup.

Risk: unknown until separately designed and tested.

### Option D: Explicitly Defer Sensor Alignment

This would leave both `SSN2BFO.ttl` and the workbook unchanged, preserve the expected-issue handling, and add a clear deferral note or policy record that the mismatch is version-targeted.

Pros:

- Matches prior reports that identify the Sensor row as upcoming-CCO / next-version targeted.
- Avoids prematurely changing either the current-local-CCO TTL mapping or the future-facing workbook row.
- Preserves the current validation baseline, including full local SOSA closure HermiT cleanliness.

Cons:

- The mapping audit will continue to report two expected `sosa:Sensor` issues.
- Human reviewers must continue recognizing these as expected until the CCO version target is resolved.

Risk: lowest mapping risk; continued audit-noise cost.

## Recommendation

Recommended next branch:

```text
docs/document-sensor-version-alignment-deferral
```

Recommended decision:

- Do not change `SSN2BFO.ttl` yet.
- Do not change `Current_SOSA-SSN to BFO-CCO.xlsx` yet.
- Keep the current expected-issue handling for the two `sosa:Sensor` audit issues.
- Document the mismatch as an intentional version-targeted deferral until either:
  - the repository imports the CCO version that supports the workbook’s stronger `cco:Sensor` equivalence; or
  - the project explicitly decides that the workbook should target only the currently imported CCO version.

After that documentation branch, the next mapping-change branch should depend on the project decision:

- If current-local-CCO alignment is chosen, update workbook row 18 to match the current TTL-style subclass expression.
- If latest/future-CCO alignment is chosen after importing the relevant CCO version, update TTL to match the authoritative `cco:Sensor` target.

Current expected-issue handling should not be removed until a mapping-change branch actually aligns the workbook and TTL. No HermiT or ELK report regeneration is needed for the documentation-only deferral branch. A future mapping-change branch would need to regenerate the mapping audit and rerun the full validation suite.

## Validation

Validation commands for this report:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/sosa-sensor-version-alignment-resolution.md

git diff --check
```

Result: PASS.

Workflow-check summary:

- Validation suite: PASS.
- Full local SOSA closure HermiT check: PASS.
- Python compile check: PASS.
- Git whitespace check: PASS.
- Expected changed file set: only `reports/sosa-sensor-version-alignment-resolution.md`.
