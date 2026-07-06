# HermiT Source-vs-Mapping Isolation

## Scope

This report isolates whether the current HermiT/full OWL DL unsatisfiability is already present in the local source/import profile or appears after adding `SSN2BFO.ttl`.

This is a diagnostic-only report. No ontology mappings, spreadsheet files, imports, source examples, generated artifacts, release artifacts, or existing reports were modified.

The prior baseline report is `reports/hermit-profile-diagnostic-baseline.md`. That baseline showed that the source/import-plus-mapping graph fails HermiT on a `sosa:hasSample` / `sosa:isSampleOf` simplicity blocker until the sample functional-property cleanup is applied, after which HermiT reports 24 unsatisfiable classes.

## Temporary files and method

Temporary working directory:

- `/tmp/ssn-to-bfo-hermit-source-vs-mapping`

All variants were built with `rdflib`, written to `/tmp`, and reasoned with ROBOT/HermiT. All variants removed `owl:imports` triples from the temporary merged graph.

Source/import-only inputs:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`

Source/import-plus-mapping inputs:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Sample simplicity cleanup, when applied:

- Removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`
- Removed `sosa:hasSample rdf:type owl:InverseFunctionalProperty`

Temporary variant files:

- S1: `/tmp/ssn-to-bfo-hermit-source-vs-mapping/S1-source-only-no-cleanup.ttl`
- S2: `/tmp/ssn-to-bfo-hermit-source-vs-mapping/S2-source-only-sample-cleanup.ttl`
- M1: `/tmp/ssn-to-bfo-hermit-source-vs-mapping/M1-source-plus-mapping-no-cleanup.ttl`
- M2: `/tmp/ssn-to-bfo-hermit-source-vs-mapping/M2-source-plus-mapping-sample-cleanup.ttl`

Captured output files:

- S1 stdout: `/tmp/ssn-to-bfo-hermit-source-vs-mapping/S1-source-only-no-cleanup.stdout.txt`
- S2 stdout: `/tmp/ssn-to-bfo-hermit-source-vs-mapping/S2-source-only-sample-cleanup.stdout.txt`
- M1 stdout: `/tmp/ssn-to-bfo-hermit-source-vs-mapping/M1-source-plus-mapping-no-cleanup.stdout.txt`
- M2 stdout: `/tmp/ssn-to-bfo-hermit-source-vs-mapping/M2-source-plus-mapping-sample-cleanup.stdout.txt`

## Tool versions

- ROBOT: `ROBOT version 1.9.7`
- Java:

```text
java version "22.0.2" 2024-07-16
Java(TM) SE Runtime Environment (build 22.0.2+9-70)
Java HotSpot(TM) 64-Bit Server VM (build 22.0.2+9-70, mixed mode, sharing)
```

## Variant summary table

| Variant | Inputs | Cleanup removals | Triples | Return code | Reasoned output | `owl:Nothing` count | Major result |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| S1 | Source/import only | Removed 2 `owl:imports` triples. | 14487 | 0 | yes | 0 | Clean by return code and `owl:Nothing`, with OWLAPI parser warnings and one parse-warning line for `sosa:isSampleOf rdf:type owl:FunctionalProperty`. |
| S2 | Source/import only | Removed 2 `owl:imports`; removed both sample functional-property assertions. | 14485 | 0 | yes | 0 | Clean by return code and `owl:Nothing`, with OWLAPI parser warnings. |
| M1 | Source/import plus `SSN2BFO.ttl` | Removed 5 `owl:imports` triples. | 15519 | 1 | no | n/a | Simplicity/profile blocker involving non-simple inverse of `sosa:hasSample`. |
| M2 | Source/import plus `SSN2BFO.ttl` | Removed 5 `owl:imports`; removed both sample functional-property assertions. | 15517 | 1 | no | n/a | HermiT reports 24 unsatisfiable classes. |

No variant reported unsatisfiable object properties or data properties in the captured output.

## Source/import-only results

### S1: source/import profile only, no mapping

Input files:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`

Cleanup:

- Removed 2 `owl:imports` triples.

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-source-vs-mapping/S1-source-only-no-cleanup.ttl --output /tmp/ssn-to-bfo-hermit-source-vs-mapping/S1-source-only-no-cleanup-reasoned.ttl
```

Result:

- Return code: `0`
- Reasoned output produced: yes
- `owl:Nothing` count in reasoned output: `0`
- Unsatisfiable classes reported: none
- Unsatisfiable properties reported: none

Useful output snippet:

```text
Input ontology contains 1 triple(s) that could not be parsed:
 - <http://www.w3.org/ns/sosa/isSampleOf> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#FunctionalProperty>.
```

Assessment:

- The source/import-only graph did not fail HermiT and did not produce `owl:Nothing` entities.
- HermiT/OWLAPI emitted parser warnings, including the `sosa:isSampleOf` functional-property parse-warning line, but ROBOT returned `0` and wrote a reasoned output.

### S2: source/import profile only, sample simplicity cleanup

Input files:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`

Cleanup:

- Removed 2 `owl:imports` triples.
- Removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`.
- Removed `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-source-vs-mapping/S2-source-only-sample-cleanup.ttl --output /tmp/ssn-to-bfo-hermit-source-vs-mapping/S2-source-only-sample-cleanup-reasoned.ttl
```

Result:

- Return code: `0`
- Reasoned output produced: yes
- `owl:Nothing` count in reasoned output: `0`
- Unsatisfiable classes reported: none
- Unsatisfiable properties reported: none

Assessment:

- After the sample functional-property cleanup, the source/import-only profile is HermiT-clean in this no-imports merged test.
- The source/import-only profile does not explain the 24-class unsatisfiability reported for the source-plus-mapping graph.

## Source/import-plus-mapping results

### M1: source/import profile plus mapping, no cleanup

Input files:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Cleanup:

- Removed 5 `owl:imports` triples.

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-source-vs-mapping/M1-source-plus-mapping-no-cleanup.ttl --output /tmp/ssn-to-bfo-hermit-source-vs-mapping/M1-source-plus-mapping-no-cleanup-reasoned.ttl
```

Result:

- Return code: `1`
- Reasoned output produced: no
- `owl:Nothing` count: not available
- Unsatisfiable classes reported: none, because HermiT stopped at the profile blocker.
- Unsatisfiable properties reported: none

Useful output snippet:

```text
Input ontology contains 1 triple(s) that could not be parsed:
 - <http://www.w3.org/ns/sosa/isSampleOf> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#FunctionalProperty>.

Non-simple property 'ObjectInverseOf(<http://www.w3.org/ns/sosa/hasSample>)' or its inverse appears in the cardinality restriction 'ObjectMaxCardinality(1 ObjectInverseOf(<http://www.w3.org/ns/sosa/hasSample>) owl:Thing)'.
```

Assessment:

- Adding `SSN2BFO.ttl` changes the no-cleanup HermiT status from source-only success to a hard simplicity/profile failure.
- This points to a mapping-profile interaction involving `sosa:hasSample`, not merely a source/import-only failure.

### M2: source/import profile plus mapping, sample simplicity cleanup

Input files:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Cleanup:

- Removed 5 `owl:imports` triples.
- Removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`.
- Removed `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-source-vs-mapping/M2-source-plus-mapping-sample-cleanup.ttl --output /tmp/ssn-to-bfo-hermit-source-vs-mapping/M2-source-plus-mapping-sample-cleanup-reasoned.ttl
```

Result:

- Return code: `1`
- Reasoned output produced: no
- `owl:Nothing` count: not available
- Unsatisfiable properties reported: none
- Unsatisfiable classes reported: 24

Useful output snippet:

```text
There are 24 unsatisfiable classes in the ontology.
```

## Comparison of unsatisfiable entity sets

S2, the source/import-only graph after sample simplicity cleanup, reported no unsatisfiable classes.

M2, the source/import-plus-mapping graph after the same cleanup, reported these 24 unsatisfiable classes:

| IRI | Local label if available | Present in S2 | Present in M2 |
| --- | --- | --- | --- |
| `http://www.w3.org/ns/sosa/Observation` |  | no | yes |
| `http://www.w3.org/ns/sosa/Sensor` |  | no | yes |
| `http://www.w3.org/ns/ssn/Input` | Input | no | yes |
| `http://www.w3.org/ns/ssn/Output` | Output | no | yes |
| `http://www.w3.org/ns/ssn/Stimulus` | Stimulus | no | yes |
| `http://www.w3.org/ns/ssn/systems/Accuracy` | Accuracy | no | yes |
| `http://www.w3.org/ns/ssn/systems/ActuationRange` | Actuation Range | no | yes |
| `http://www.w3.org/ns/ssn/systems/BatteryLifetime` | Battery Lifetime | no | yes |
| `http://www.w3.org/ns/ssn/systems/DetectionLimit` | Detection Limit | no | yes |
| `http://www.w3.org/ns/ssn/systems/Drift` | Drift | no | yes |
| `http://www.w3.org/ns/ssn/systems/Frequency` | Frequency | no | yes |
| `http://www.w3.org/ns/ssn/systems/Latency` | Latency | no | yes |
| `http://www.w3.org/ns/ssn/systems/MaintenanceSchedule` | Maintenance Schedule | no | yes |
| `http://www.w3.org/ns/ssn/systems/MeasurementRange` | Measurement Range | no | yes |
| `http://www.w3.org/ns/ssn/systems/OperatingPowerRange` | Operating Power Range | no | yes |
| `http://www.w3.org/ns/ssn/systems/OperatingProperty` | Operating Property | no | yes |
| `http://www.w3.org/ns/ssn/systems/Precision` | Precision | no | yes |
| `http://www.w3.org/ns/ssn/systems/Resolution` | Resolution | no | yes |
| `http://www.w3.org/ns/ssn/systems/ResponseTime` | Response Time | no | yes |
| `http://www.w3.org/ns/ssn/systems/Selectivity` | Selectivity | no | yes |
| `http://www.w3.org/ns/ssn/systems/Sensitivity` | Sensitivity | no | yes |
| `http://www.w3.org/ns/ssn/systems/SurvivalProperty` | Survival Property | no | yes |
| `http://www.w3.org/ns/ssn/systems/SystemLifetime` | System Lifetime | no | yes |
| `http://www.w3.org/ns/ssn/systems/SystemProperty` | System Property | no | yes |

Set comparison:

- Source/import-only unsatisfiable classes after cleanup: `0`
- Source/import-plus-mapping unsatisfiable classes after cleanup: `24`
- Classes already unsatisfiable without `SSN2BFO.ttl`: `0`
- Classes appearing only after `SSN2BFO.ttl` is added: `24`
- Adding `SSN2BFO.ttl` increases the unsatisfiable-class set from none to 24 in this HermiT profile test.

## Assessment

Likely source/import profile issue:

- The source/import-only profile emits OWLAPI parser messages in both S1 and S2.
- S1 also reports that `sosa:isSampleOf rdf:type owl:FunctionalProperty` could not be parsed, but ROBOT/HermiT still returns `0`, writes a reasoned output, and produces `owl:Nothing` count `0`.
- The source/import-only profile is therefore noisy but not unsatisfiable in this test.

Likely mapping-introduced or mapping-amplified issue:

- M1 fails on a `sosa:hasSample` non-simple-property/cardinality interaction that does not make S1 fail.
- M2 reports 24 unsatisfiable classes after the same cleanup under which S2 is clean.
- These results indicate that the current HermiT unsatisfiability is introduced or amplified when `SSN2BFO.ttl` is added to the source/import profile.

Not yet isolated:

- This report does not identify the minimal conflicting mapping axioms.
- This report does not compute HermiT explanations.
- This report does not determine whether each of the 24 unsatisfiable classes has the same root cause.
- This report does not decide whether the right repair belongs in mapping axioms, source-profile projection, or a separate HermiT-compatible profile.

## Recommendation

- Keep HermiT cleanup separate from the ELK validation suite.
- Use the current ELK validation suite as the near-term mapping regression baseline.
- Treat the 24 M2-only unsatisfiable classes as mapping-introduced or mapping-amplified until explanation-driven diagnostics prove otherwise.
- If HermiT cleanup proceeds, address the M2 classes in narrow branches, one cluster at a time, starting from a cleanup variant equivalent to S2/M2 so the `sosa:hasSample` simplicity blocker does not mask class-unsatisfiability diagnostics.
- Do not change mappings in this diagnostic branch.
