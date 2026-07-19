# HermiT `sosa:observedProperty` Deferral Evaluation

## Scope

This is an evaluation-branch report for temporarily deferring only the active direct property mapping:

```ttl
sosa:observedProperty rdfs:subPropertyOf cco:ont00001921 .
```

This branch does not claim that the mapping is semantically wrong. It measures the validation and HermiT impact of a narrow one-triple deferral recommended by `reports/hermit-observation-sensor-stimulus-deferral-evaluation.md`.

Temporary HermiT files were written only under:

```text
/tmp/ssn-to-bfo-hermit-observedProperty-deferral-evaluation
```

## Temporary Repo Edits

### TTL

In `SSN2BFO.ttl`, the active logical assertion was removed:

```ttl
<http://www.w3.org/ns/sosa/observedProperty> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001921> .
```

It was replaced with the non-logical note:

```ttl
# Direct OWL property mapping deferred pending HermiT-safe rule/COMS treatment.
```

No adjacent mapping was intentionally edited.

### Spreadsheet

In `Current_SOSA-SSN to BFO-CCO.xlsx`, sheet `Common OPs`, row 33:

| Cell | Before | After |
| --- | --- | --- |
| `E33` | `sosa:observedProperty rdfs:domain sosa:Observation .` plus `rdfs:range ssn:Property .` and `rdfs:subPropertyOf cco:has_input .` | cleared |
| `F33` | rationale for mapping `sosa:observedProperty` to `cco:has_input` | updated to state that intended semantics remain, the active OWL direct property mapping is temporarily deferred because HermiT diagnostics identify it as a narrow one-triple reducer for the remaining Observation / Sensor / Stimulus cluster, this does not prove semantic invalidity, and future representation should be reviewed for HermiT-safe OWL or rule/COMS treatment |

The source term/source IRI cells were preserved.

## Adjacent Mapping Check

The following adjacent mappings remain active in `SSN2BFO.ttl`:

| Source | Current active logical mapping status |
| --- | --- |
| `sosa:Sensor` | active `rdfs:subClassOf` class-expression mapping remains |
| `sosa:Observation` | active `rdfs:subClassOf` class-expression mapping remains |
| `sosa:hosts` | active `owl:propertyChainAxiom` remains |
| `sosa:madeBySensor` | active `rdfs:subPropertyOf cco:ont00001833` remains |
| `sosa:observes` | active `rdfs:subPropertyOf ssn:forProperty` remains |
| `sosa:madeObservation` | active `rdfs:subPropertyOf cco:ont00001787` remains |
| `sosa:observedProperty` | no active direct logical mapping remains |

Already-deferred Input/Output and SSN Systems mappings were not edited.

## Mapping Audit Result

The canonical mapping audit was regenerated with:

```bash
make audit-write
```

Result:

```text
inspected_sheets=5
spreadsheet_rows=93
ttl_candidate_mapping_assertions=71
issues=2
missing_in_spreadsheet=1
missing_in_ttl=1
```

The only remaining audit issues are the known `sosa:Sensor` version-alignment issues:

| Issue | Category | Source |
| --- | --- | --- |
| `ISSUE-0001` | `missing_in_spreadsheet` | `sosa:Sensor` |
| `ISSUE-0002` | `missing_in_ttl` | `sosa:Sensor`, `Common Classes` row 18 |

No new unexpected audit issue appeared.

## ELK Entailment Result

`reports/elk-instance-mapping-entailments.md` was regenerated with:

```bash
python tools/test_elk_instance_mapping_entailments.py --output reports/elk-instance-mapping-entailments.md
```

Result after deferral:

```text
Example files tested: 16
ROBOT pass/fail: 16/0
Total direct class expectations checked: 6
Total direct property expectations checked: 77
Total property-chain expectations checked: 5
Total restriction expectations checked: 2
Total expectation failures: 0
Active direct mappings not covered by instance data: 0
Active property-chain mappings not covered by instance data: 0
Active restriction mappings not covered by instance data: 0
Summary: PASS
```

Expectation count changes:

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| direct property mappings in `SSN2BFO.ttl` | 24 | 23 | -1 |
| direct class expectations checked | 6 | 6 | 0 |
| direct property expectations checked | 110 | 77 | -33 |
| property-chain expectations checked | 5 | 5 | 0 |
| restriction expectations checked | 2 | 2 | 0 |
| expected direct/property-chain ABox target assertions | 121 | 88 | -33 |
| expectation failures | 0 | 0 | 0 |
| active direct mappings not covered | 0 | 0 | 0 |

The decrease is expected because synthetic fixtures previously exercised `sosa:observedProperty` instances that no longer have an active direct mapping target.

## HermiT Full M2 Before / After

For each HermiT variant, the temporary graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Then these cleanup steps were applied:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

The HermiT command shape was:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

| Variant | Mapping graph | Triples | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Unsat set | Sample simplicity blocker |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- | --- |
| before | branch `HEAD` copy of `SSN2BFO.ttl` before this deferral | 15475 | 1 | no | n/a | 3 | `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus` | no |
| after | current edited `SSN2BFO.ttl` | 15474 | 0 | yes | 0 | 0 | clean | no |

The expected remaining HermiT trio disappeared after only the `sosa:observedProperty` direct property mapping was deferred. No new HermiT issue appeared in this M2 check.

## Standard Validation

The standard validation workflow was run with this branch shape:

```bash
python tools/workflow_check.py --mode mapping-change \
  --expected-file SSN2BFO.ttl \
  --expected-file "Current_SOSA-SSN to BFO-CCO.xlsx" \
  --expected-file reports/elk-instance-mapping-entailments.md \
  --expected-file reports/mapping-consistency-audit.md \
  --expected-file reports/hermit-observedProperty-deferral-evaluation.md
```

Result:

```text
Validation suite: PASS
Python compile check: PASS
Git whitespace check: PASS
```

The workflow confirmed:

- mapping audit remains at two known `sosa:Sensor` issues;
- instance smoke test passes;
- ELK instance entailment test passes;
- Python compile check passes;
- `git diff --check` passes;
- no active direct mappings are uncovered by instance data;
- changed files are limited to the expected mapping-change scope.

## Evaluation Assessment

This temporary deferral is a strong HermiT result:

- it is a one-triple direct property mapping deferral;
- it clears the remaining full M2 HermiT Observation / Sensor / Stimulus cluster;
- it leaves adjacent class, property, and property-chain mappings active;
- the standard ELK-oriented mapping validation remains expected to pass;
- the mapping audit still shows only the known `sosa:Sensor` version-alignment issues.

The result still does not prove that the `sosa:observedProperty` mapping is semantically wrong. Reconstruction work in the prior diagnostic showed the cluster is mixed and requires broader context. The deferral should therefore be described as HermiT-safe and conservative, not as a semantic correction.

## Recommendation

This evaluation supports a final fix branch that defers the active OWL direct property mapping for:

```ttl
sosa:observedProperty rdfs:subPropertyOf cco:ont00001921 .
```

The final branch should:

- keep `sosa:Sensor`, `sosa:Observation`, `sosa:hosts`, `sosa:madeBySensor`, `sosa:observes`, and `sosa:madeObservation` unchanged;
- preserve the spreadsheet source term/source IRI row;
- retain a concise rationale that intended semantics remain but active OWL mapping is deferred pending HermiT-safe OWL or rule/COMS treatment;
- regenerate the mapping audit and ELK entailment report;
- avoid overclaiming semantic invalidity.
