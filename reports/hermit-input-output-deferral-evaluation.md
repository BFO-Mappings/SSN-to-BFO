# HermiT Input/Output Deferral Evaluation

## Scope

This is an evaluation-only report for temporarily deferring the active direct OWL property mappings for:

```text
ssn:hasInput
ssn:hasOutput
```

This branch does not claim that either mapping is semantically wrong. It evaluates whether deferring the direct OWL `rdfs:subPropertyOf` assertions removes the `ssn:Input` / `ssn:Output` HermiT subcluster while preserving the current ELK validation baseline.

Temporary HermiT files were written only under:

```text
/tmp/ssn-to-bfo-hermit-input-output-deferral-evaluation
```

## Decision Source

The immediate source report is:

```text
reports/hermit-input-output-mapping-evaluation.md
```

That report found:

- full M2 before this evaluation had five HermiT unsats:
  - `sosa:Observation`
  - `sosa:Sensor`
  - `ssn:Input`
  - `ssn:Output`
  - `ssn:Stimulus`
- `ssn:Input` and `ssn:Output` are independent from the Observation/Sensor/Stimulus cluster;
- removing `ssn:hasInput` removes `ssn:Input`;
- removing `ssn:hasOutput` removes `ssn:Output`;
- the `ssn:Input` / `ssn:Output` class mappings are not strongly implicated;
- the issue appears to be a mixed full-OWL interaction involving source restrictions, active `ssn:hasInput` / `ssn:hasOutput` mappings to CCO process-domain input/output properties, and active `sosa:Procedure` class-expression mapping.

## Temporary Repo Edits Evaluated

### TTL Edits

In `SSN2BFO.ttl`, the following active logical property mappings were deferred:

```ttl
<http://www.w3.org/ns/ssn/hasInput> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001921> .
<http://www.w3.org/ns/ssn/hasOutput> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001986> .
```

The resulting local TTL leaves short non-logical comments:

```ttl
###  http://www.w3.org/ns/ssn/hasInput
# Direct OWL property mapping deferred pending HermiT-safe rule/COMS treatment.

###  http://www.w3.org/ns/ssn/hasOutput
<http://www.w3.org/ns/ssn/hasOutput> rdf:type owl:ObjectProperty .
# Direct OWL property mapping deferred pending HermiT-safe rule/COMS treatment.
```

The `ssn:Input` and `ssn:Output` class mappings remain active. The `sosa:Procedure` mapping remains active. No Observation/Sensor/Stimulus mapping was changed.

### Spreadsheet Edits

Only the `Common OPs` rows for `ssn:hasInput` and `ssn:hasOutput` were updated.

Exact value changes compared with `HEAD`:

| Cell | Before | After |
| --- | --- | --- |
| `Common OPs!E9` | `subPropertyOf cco:has_input` | blank |
| `Common OPs!F9` | prior rationale for active direct mapping | deferral rationale for `ssn:hasInput` |
| `Common OPs!E10` | `subPropertyOf cco:has_output` | blank |
| `Common OPs!F10` | prior rationale for active direct mapping | deferral rationale for `ssn:hasOutput` |

The new rationale states that the intended procedure-to-input/output semantics remain, that the active OWL direct property mapping is temporarily deferred because HermiT diagnostics identify it as a one-class reducer in the mixed source-restriction / `sosa:Procedure` context, that this does not prove semantic invalidity, and that future representation should be reviewed for HermiT-safe OWL or rule/COMS treatment.

## Mapping Counts

Direct named `rdfs:subPropertyOf` mappings in `SSN2BFO.ttl`:

| State | Count |
| --- | ---: |
| Before deferral (`HEAD:SSN2BFO.ttl`) | 26 |
| After deferral | 24 |

The two removed active direct property mappings are exactly:

```text
ssn:hasInput -> cco:ont00001921
ssn:hasOutput -> cco:ont00001986
```

Direct named `rdfs:subClassOf` mappings stayed unchanged at 4.

## Mapping Audit Result

Command:

```bash
make audit-write
```

Result:

```text
inspected_sheets=5
spreadsheet_rows=93
ttl_candidate_mapping_assertions=72
issues=2
missing_in_spreadsheet=1
missing_in_ttl=1
```

The canonical mapping audit still reports only the known expected `sosa:Sensor` version-alignment issues:

```text
ISSUE-0001 missing_in_spreadsheet sosa:Sensor
ISSUE-0002 missing_in_ttl Common Classes row 18 sosa:Sensor
```

No unexpected audit issue appeared after deferring `ssn:hasInput` and `ssn:hasOutput` consistently in both TTL and spreadsheet.

## ELK Instance Entailment Result

Command:

```bash
python tools/test_elk_instance_mapping_entailments.py --output reports/elk-instance-mapping-entailments.md
```

Result:

```text
Example files tested: 16
ROBOT pass/fail: 16/0
Total direct class expectations checked: 6
Total direct property expectations checked: 110
Total property-chain expectations checked: 5
Total restriction expectations checked: 2
Total expectation failures: 0
Active direct mappings not covered by instance data: 0
Active property-chain mappings not covered by instance data: 0
Active restriction mappings not covered by instance data: 0
Summary: PASS
```

ELK expectation count changes:

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Direct class expectations checked | 6 | 6 | 0 |
| Direct property expectations checked | 112 | 110 | -2 |
| Property-chain expectations checked | 5 | 5 | 0 |
| Restriction expectations checked | 2 | 2 | 0 |
| Expectation failures | 0 | 0 | 0 |
| Active direct mappings not covered | 0 | 0 | 0 |

The two fewer direct property expectations correspond to the deferred `ssn:hasInput` and `ssn:hasOutput` direct mappings.

## HermiT Setup

For both before and after variants, the temporary M2-style graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Then the following cleanup was applied:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

Command shape:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

The before variant used `HEAD:SSN2BFO.ttl`. The after variant used the current working-tree `SSN2BFO.ttl`.

## HermiT Before/After

| Variant | Mapping source | Triples | Return code | Reasoned output? | `owl:Nothing` count | Sample blocker? | Unsat count | Unsat set |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| Before | `HEAD:SSN2BFO.ttl` | 15477 | 1 | no | n/a | no | 5 | `sosa:Observation`, `sosa:Sensor`, `ssn:Input`, `ssn:Output`, `ssn:Stimulus` |
| After | working-tree `SSN2BFO.ttl` | 15475 | 1 | no | n/a | no | 3 | `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |

The HermiT after-deferral result removes both `ssn:Input` and `ssn:Output` from the full M2 unsat set. No new HermiT unsatisfiable class appeared. The remaining unsats are exactly the previously separated Observation/Sensor/Stimulus trio.

## Targeted Input/Output Before/After

| Class | Before full M2 | After deferral |
| --- | --- | --- |
| `ssn:Input` | unsatisfiable | absent from unsat set |
| `ssn:Output` | unsatisfiable | absent from unsat set |

The `ssn:Input` and `ssn:Output` class mappings remain active:

```ttl
<http://www.w3.org/ns/ssn/Input> rdfs:subClassOf <https://www.commoncoreontologies.org/ont00000958> .
<http://www.w3.org/ns/ssn/Output> rdfs:subClassOf <https://www.commoncoreontologies.org/ont00000958> .
```

This supports the prior finding that the class mappings themselves are not the direct high-impact reducers in the current full-OWL profile.

## Standard Validation

Command:

```bash
python tools/run_validation_suite.py
```

Result:

```text
Validation suite: PASS
```

The suite used temporary report outputs by default and passed:

- Turtle parse check;
- mapping consistency audit;
- expected audit issue summary;
- instance-data smoke test;
- ELK instance mapping entailment test;
- Python compile check;
- `git diff --check`.

## Assessment

The temporary deferral behaves as expected:

- direct property mapping count drops by 2;
- ELK direct property expectations drop by 2;
- the mapping audit remains at the expected two `sosa:Sensor` version-alignment issues;
- all ELK instance entailment checks pass;
- full M2 HermiT drops from five unsats to the Observation/Sensor/Stimulus trio;
- `ssn:Input` and `ssn:Output` disappear from the HermiT unsat set;
- no new HermiT issue appears.

This is promising as a final fix candidate for the Input/Output pair, but it does not prove that the intended `hasInput` / `hasOutput` semantics are wrong. It shows that the direct active OWL subproperty mappings are HermiT-risky in the current mixed source-restriction / `sosa:Procedure` context.

## Recommendation

This temporary deferral supports a narrow final fix branch for the Input/Output pair.

Recommended final-fix shape:

- defer `ssn:hasInput -> cco:ont00001921`;
- defer `ssn:hasOutput -> cco:ont00001986`;
- keep `ssn:Input` and `ssn:Output` class mappings active;
- keep `sosa:Procedure` unchanged in that branch;
- document intended `hasInput` / `hasOutput` semantics for future HermiT-safe OWL or rule/COMS treatment;
- keep the Observation/Sensor/Stimulus cluster as a separate modeling task.

Do not infer from this evaluation that the source ontology, the CCO input/output relations, or the intended procedure-to-input/output semantics are wrong.
