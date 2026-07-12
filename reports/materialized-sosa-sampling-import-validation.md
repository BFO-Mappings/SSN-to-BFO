# Materialized SOSA Sampling Import Validation

## File Identity

- Path: `imports/sosa-sampling.ttl`
- Repository status at inspection: untracked and not ignored.
- Turtle parse: PASS.
- Triple count: 35.
- Ontology IRI: `http://www.w3.org/ns/sosa/sampling/`.
- Imports:
  - `http://www.w3.org/2004/02/skos/core`
  - `http://www.w3.org/ns/sosa/`

Declared local terms:

- Classes:
  - `http://www.w3.org/ns/sosa/sampling/RelationshipNature`
  - `http://www.w3.org/ns/sosa/sampling/SampleRelationship`
- Object properties:
  - `http://www.w3.org/ns/sosa/sampling/hasSampleRelationship`
  - `http://www.w3.org/ns/sosa/sampling/natureOfRelationship`
  - `http://www.w3.org/ns/sosa/sampling/relatedSample`

## Repository Integration

`SSN2BFO.ttl` now directly imports `http://www.w3.org/ns/sosa/sampling/` while preserving the existing imports of:

- `http://www.w3.org/ns/ssn/`
- `http://www.w3.org/ns/ssn/systems/`
- `https://www.commoncoreontologies.org/2024-11-06/CommonCoreOntologiesMerged`

No `.gitignore` change was required. `imports/sosa-sampling.ttl` is versionable by normal Git tracking because `git check-ignore -v imports/sosa-sampling.ttl` returned no match.

## Validation-Profile Updates

Inspected tools:

- `tools/test_full_sosa_closure_hermit.py`: changed because it explicitly protects the full local SOSA closure HermiT baseline.
- `tools/test_object_property_typing_probes.py`: changed because its baseline and each probe explicitly load the full local SOSA closure.
- `tools/test_elk_instance_mapping_entailments.py`: inspected and left unchanged because it is intentionally scoped to active mappings in `SSN2BFO.ttl` and local example/fixture expectations, not the full imported source closure.
- `tools/test_instance_data.py`: inspected and left unchanged because it is an intentionally lightweight instance-data smoke test over mappings and examples, not a full OWL/import-closure profile.
- `tools/run_validation_suite.py`: inspected and left unchanged because it delegates the full-closure profiles to the two updated tools.
- `tools/compare_mappings.py`: inspected and left unchanged because its import-file use is for conservative spreadsheet/TTL mapping comparison and label resolution, not full SOSA closure reasoning.
- `tools/workflow_check.py`: inspected and left unchanged because it orchestrates workflow gates rather than building an ontology closure itself.

Full local closure file list after the change:

- `imports/cco.ttl`
- `imports/sosa.ttl`
- `imports/sosa-sampling.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

The updated full-closure tools preserve the existing cleanup behavior:

- remove all `owl:imports` triples after loading local files;
- remove `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- remove `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

## Formal-Semantics Note

The SOSA Sampling source uses `schema:domainIncludes` and `schema:rangeIncludes` as schema.org guidance annotations. It does not use formal `rdfs:domain` or `rdfs:range` commitments.

Observed counts in `imports/sosa-sampling.ttl`:

- `schema:domainIncludes`: 3.
- `schema:rangeIncludes`: 3.
- `rdfs:domain`: 0.
- `rdfs:range`: 0.

## SKOS Note

No local SKOS ontology materialization was found under `imports/` by:

```bash
find imports -maxdepth 1 \( -iname '*skos*.ttl' -o -iname '*skos*.rdf' -o -iname '*skos*.owl' \)
```

The local command-line closure now materializes SOSA Sampling itself, but not the imported SKOS ontology.

SOSA Sampling references SKOS in these source axioms:

- `RelationshipNature rdfs:subClassOf skos:Concept`.
- `skos:definition` annotations on the sampling properties and classes.
- `skos:example` annotations on `RelationshipNature`.

The absence of full SKOS axioms does not affect the current HermiT consistency check or object-property typing probes. The current checks do not depend on SKOS class hierarchy entailments or SKOS annotation-property declarations, and the imported sampling source contributes no formal `rdfs:domain` / `rdfs:range` axioms. This remains an import-closure limitation for later review, not a reason to alter mappings.

## Before/After Validation Results

Before this task, the maintained full-local-closure baseline was 15,729 triples.

After adding the local SOSA Sampling file to the full-closure inputs:

- Full-closure graph triple count: 15,762.
- Increase from prior baseline: +33 triples. The source file has 35 triples; the full-closure tools remove all loaded `owl:imports` triples, including the two imports from `imports/sosa-sampling.ttl`.
- HermiT return code: 0.
- `owl:Nothing` count: 0.
- Named unsat count/set: 0 / clean.
- Object-property typing-probe result: PASS.
  - Retained local basis: 22 domains and 0 ranges.
  - Probes specified: 62.
  - Probes tested: 62.
  - Expected-unsatisfiable probes passed: 62.
  - Satisfiable probes: 0.
  - Inconclusive probes: 0.
  - Unexpected ontology unsats: 0.
- Mapping-audit result: PASS.
  - `ttl_candidate_mapping_assertions`: 68.
  - Remaining audit issues: the two expected `sosa:Sensor` version-alignment issues.
- ELK instance entailments: PASS.
- Instance-data smoke test: PASS.
- Python compile check: PASS.
- `git diff --check`: PASS.

## Confirmation

- No mapping axioms were changed.
- The imported source axioms in `imports/sosa-sampling.ttl` were not edited.
- The workbook report `reports/workbook-mapping-changes-since-first-version.xlsx` was treated as pre-existing unrelated work and was not edited.
