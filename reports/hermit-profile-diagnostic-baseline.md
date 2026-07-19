# HermiT Profile Diagnostic Baseline

## Scope

This report documents the current HermiT/full OWL DL diagnostic baseline for the local SSN-to-BFO mapping profile. It is diagnostic only. No ontology mappings, spreadsheet files, imports, source examples, generated artifacts, release artifacts, or existing reports were modified.

The ELK mapping and instance-entailment validation profile remains the near-term regression baseline. This report only records what happens when the current merged mapping profile is tested with ROBOT/HermiT.

## Inputs and temporary files

Temporary working directory:

- `/tmp/ssn-to-bfo-hermit-profile-diagnostic`

Merged input files:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Graph preparation:

- Parsed and merged the input files with `rdflib`.
- Removed all `owl:imports` triples from each temporary variant.
- Wrote all variant TTL files under `/tmp/ssn-to-bfo-hermit-profile-diagnostic`.
- Did not modify repository files.

Temporary variant files:

- Variant A: `/tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-a-current-no-imports.ttl`
- Variant B: `/tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-b-remove-isSampleOf-functional.ttl`
- Variant C: `/tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-c-remove-hasSample-inverse-functional.ttl`

Captured ROBOT output:

- Variant A stdout: `/tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-a-current-no-imports.stdout.txt`
- Variant B stdout: `/tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-b-remove-isSampleOf-functional.stdout.txt`
- Variant C stdout: `/tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-c-remove-hasSample-inverse-functional.stdout.txt`

Variant D was not required for this baseline because Variant C produced useful HermiT unsatisfiable-class diagnostics. No Variant D result is included as part of the baseline.

## Tool versions

- ROBOT: `ROBOT version 1.9.7`
- Java:

```text
java version "22.0.2" 2024-07-16
Java(TM) SE Runtime Environment (build 22.0.2+9-70)
Java HotSpot(TM) 64-Bit Server VM (build 22.0.2+9-70, mixed mode, sharing)
```

## Variant summary table

| Variant | Temporary graph preparation | Triples | Return code | Reasoned output produced | Major result |
| --- | --- | ---: | ---: | --- | --- |
| A | Remove only `owl:imports` triples. | 15519 | 1 | no | OWL profile/simplicity violation involving non-simple `sosa:hasSample` inverse/cardinality form. |
| B | Variant A plus remove `sosa:isSampleOf rdf:type owl:FunctionalProperty`. | 15518 | 1 | no | Same non-simple `sosa:hasSample` blocker remains. |
| C | Variant B plus remove `sosa:hasSample rdf:type owl:InverseFunctionalProperty`. | 15517 | 1 | no | HermiT reports 24 unsatisfiable classes. |

No variant produced a reasoned output file, so there were no parseable `owl:Nothing` assertions in reasoned output.

## Detailed results

### Variant A: current no-imports merged graph

Preparation:

- Removed 5 `owl:imports` triples.
- No functional-property cleanup.

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-a-current-no-imports.ttl --output /tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-a-current-no-imports-reasoned.ttl
```

Result:

- Return code: `1`
- Reasoned output produced: no
- Major category: OWL profile/simplicity violation; OWLAPI parser messages also appeared.

Useful ROBOT snippet:

```text
Input ontology contains 1 triple(s) that could not be parsed:
 - <http://www.w3.org/ns/sosa/isSampleOf> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#FunctionalProperty>.

Non-simple property 'ObjectInverseOf(<http://www.w3.org/ns/sosa/hasSample>)' or its inverse appears in the cardinality restriction 'ObjectMaxCardinality(1 ObjectInverseOf(<http://www.w3.org/ns/sosa/hasSample>) owl:Thing)'.
```

Interpretation:

- HermiT does not reach useful class-unsatisfiability reporting.
- The blocker is not an import-resolution failure; it is an OWL DL simplicity/profile issue involving `sosa:hasSample` / `sosa:isSampleOf`.

### Variant B: ELK-style functional-property cleanup

Preparation:

- Removed 5 `owl:imports` triples.
- Removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`.

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-b-remove-isSampleOf-functional.ttl --output /tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-b-remove-isSampleOf-functional-reasoned.ttl
```

Result:

- Return code: `1`
- Reasoned output produced: no
- Major category: OWL profile/simplicity violation; OWLAPI parser messages also appeared.

Useful ROBOT snippet:

```text
Non-simple property 'ObjectInverseOf(<http://www.w3.org/ns/sosa/hasSample>)' or its inverse appears in the cardinality restriction 'ObjectMaxCardinality(1 ObjectInverseOf(<http://www.w3.org/ns/sosa/hasSample>) owl:Thing)'.
```

Interpretation:

- Removing only `sosa:isSampleOf rdf:type owl:FunctionalProperty` is not enough for HermiT.
- The inverse-functional side of `sosa:hasSample` remains a simplicity/profile blocker.

### Variant C: HermiT simplicity-blocker cleanup

Preparation:

- Removed 5 `owl:imports` triples.
- Removed `sosa:isSampleOf rdf:type owl:FunctionalProperty`.
- Removed `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-c-remove-hasSample-inverse-functional.ttl --output /tmp/ssn-to-bfo-hermit-profile-diagnostic/variant-c-remove-hasSample-inverse-functional-reasoned.ttl
```

Result:

- Return code: `1`
- Reasoned output produced: no
- Major category: unsatisfiable classes; OWLAPI parser messages also appeared.

Useful ROBOT snippet:

```text
There are 24 unsatisfiable classes in the ontology.
```

Interpretation:

- Variant C gets past the sample functional/inverse-functional simplicity blocker far enough for HermiT to report class unsatisfiability.
- ROBOT still returns nonzero and does not write a reasoned output.
- This variant is the useful current HermiT diagnostic baseline.

## Entities typed owl:Nothing

No variant produced a reasoned output file, so no `owl:Nothing` triples were available to parse.

## HermiT-reported unsatisfiable entities

Variant C reported 24 unsatisfiable classes:

| IRI | Local label if available |
| --- | --- |
| `http://www.w3.org/ns/ssn/Output` | Output |
| `http://www.w3.org/ns/ssn/systems/Latency` | Latency |
| `http://www.w3.org/ns/ssn/systems/Precision` | Precision |
| `http://www.w3.org/ns/sosa/Observation` |  |
| `http://www.w3.org/ns/ssn/systems/Sensitivity` | Sensitivity |
| `http://www.w3.org/ns/ssn/Input` | Input |
| `http://www.w3.org/ns/ssn/systems/SystemProperty` | System Property |
| `http://www.w3.org/ns/ssn/systems/ResponseTime` | Response Time |
| `http://www.w3.org/ns/sosa/Sensor` |  |
| `http://www.w3.org/ns/ssn/systems/Selectivity` | Selectivity |
| `http://www.w3.org/ns/ssn/systems/MeasurementRange` | Measurement Range |
| `http://www.w3.org/ns/ssn/systems/OperatingProperty` | Operating Property |
| `http://www.w3.org/ns/ssn/systems/DetectionLimit` | Detection Limit |
| `http://www.w3.org/ns/ssn/systems/Accuracy` | Accuracy |
| `http://www.w3.org/ns/ssn/systems/OperatingPowerRange` | Operating Power Range |
| `http://www.w3.org/ns/ssn/systems/BatteryLifetime` | Battery Lifetime |
| `http://www.w3.org/ns/ssn/systems/SystemLifetime` | System Lifetime |
| `http://www.w3.org/ns/ssn/systems/Resolution` | Resolution |
| `http://www.w3.org/ns/ssn/systems/Frequency` | Frequency |
| `http://www.w3.org/ns/ssn/systems/SurvivalProperty` | Survival Property |
| `http://www.w3.org/ns/ssn/systems/MaintenanceSchedule` | Maintenance Schedule |
| `http://www.w3.org/ns/ssn/systems/ActuationRange` | Actuation Range |
| `http://www.w3.org/ns/ssn/systems/Drift` | Drift |
| `http://www.w3.org/ns/ssn/Stimulus` | Stimulus |

No unsatisfiable object properties or data properties were separately reported in the captured ROBOT output.

## Assessment

What appears to be a profile/import/source-ontology issue:

- Variants A and B are blocked by an OWL DL simplicity/profile issue around `sosa:hasSample` / `sosa:isSampleOf`.
- The immediate functional-property assertions are source-ontology assertions from the merged SSN/SOSA input profile.
- The repeated OWLAPI `error#Error` parser messages appear in all variants. They are diagnostic noise or secondary parsing/profile messages here; Variant C still reaches HermiT unsatisfiable-class reporting after the sample functional-property cleanup.

What appears possibly mapping-amplified:

- The `sosa:hasSample` simplicity problem is likely an interaction between source functional/inverse-functional sample properties and property-chain usage in the merged mapping profile. This report does not isolate which side should change.
- Variant C's 24 unsatisfiable classes include core SOSA/SSN classes and many SSN Systems classes. That pattern suggests the full OWL DL profile remains dirty even after the sample simplicity blocker is removed.
- Some unsatisfiability may be amplified by SSN2BFO mappings, but this run did not compute explanations and does not identify minimal conflicting axiom sets.

What cannot be concluded from this diagnostic:

- This report does not prove which ontology axiom or mapping axiom is wrong.
- This report does not distinguish source-ontology design constraints from mapping-introduced contradictions.
- This report does not evaluate HermiT repairs.
- This report does not contradict the current ELK validation suite; ELK and HermiT are testing different reasoning profiles.

## Recommendation

- Do not mix HermiT/full OWL DL cleanup with ELK mapping and instance-entailment regression work.
- Treat HermiT/full OWL DL cleanup as a separate modeling/profile task with explanation-driven diagnostics.
- Keep the current ELK validation suite as the near-term regression baseline for mapping work.
- If HermiT cleanup is pursued, start by separating profile/simplicity blockers from true unsatisfiable-class explanations, then isolate minimal conflicting axiom sets for the Variant C unsatisfiable classes.
