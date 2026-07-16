# COMS Automatic Validation Setup

## Watched Input

The watcher monitors only `mappings/SSN2BFO-COMS.xlsx`. It compares SHA-256 content hashes, so modification-time changes without byte changes do not trigger duplicate checks. Excel lock files such as `mappings/~$SSN2BFO-COMS.xlsx` are not watched.

## Start And Stop

Start the watcher from the repository root:

```bash
make watch-coms
```

The watcher runs one check immediately at startup, polls approximately once per second, and waits until a changed workbook hash has remained stable for at least 1.5 seconds before checking it. Press `Ctrl+C` to stop it cleanly.

The watcher must remain running to react immediately to workbook saves. It continues after a failed check and waits for the next distinct workbook content hash.

## Run Once

Run the complete quality pipeline once and atomically update maintained outputs:

```bash
make check-coms
```

Equivalent direct commands are:

```bash
python tools/check_coms_mapping.py
python tools/check_coms_mapping.py --update
```

The default mode is `--update`. For a non-mutating freshness and quality gate, use:

```bash
python tools/check_coms_mapping.py --check-only
```

`--check-only` fails when the workbook hash, generator or identity/disposition module hashes, publication-metadata hash, authoritative ontology hash, maintained reports, or regenerated semantic products do not match. It does not rewrite tracked artifacts. The ordinary validation suite invokes this mode.

Current local status is available with:

```bash
make coms-status
```

## Publication Metadata

`config/publication-metadata.toml` is the sole governed publication-metadata source. Schema version 2 validates the exact approved global values and the canonical five-product order, paths, ontology IRIs, release suffixes, labels, descriptions, and product-type IRIs. The loader rejects missing or unknown tables and fields, unsafe paths, malformed IRIs, duplicate identities, noncanonical text, and deferred creator, contributor, provenance, dependency, hash, tag, commit, and release-date fields.

Development validation checks the governed license, repository, generated warning, `adms:status` predicate, and maintained-authoritative-development status without claiming a formal release identity. The existing release identifier and version-IRI helpers remain separately testable, but formal release metadata is not stored in the maintained development TOML.

The COMS freshness transaction hashes the metadata source, so a metadata edit makes generated evidence stale until the normal transaction succeeds. Schema-2 values are validated governance only in this change: ontology RDF metadata emission remains deferred to the next implementation PR, and all maintained TTL bytes must remain unchanged.

## Mapping And Property-Typing Rows

Mapping rows use class or relation-mapping predicates such as `rdfs:subClassOf`, `owl:equivalentClass`, `rdfs:subPropertyOf`, `owl:equivalentProperty`, and `owl:propertyChainAxiom`. These rows determine whether a source class or object property is counted as mapped by the source-term coverage report.

Object-property typing rows use:

```text
sosa:hasFeatureOfInterest | rdfs:domain | (sosa:Observation or sosa:Actuation or sosa:Sampling)
sosa:hasFeatureOfInterest | rdfs:range | sosa:FeatureOfInterest
```

For `rdfs:domain` and `rdfs:range`, the subject must resolve to a declared source object property and the target is parsed by the same Manchester class-expression parser used for class mappings. Named classes, intersections, unions, and existential restrictions are supported. The generated ontology uses the standard RDF/OWL domain or range triple, with an OWL class-expression blank node when the target is complex.

A property may have a relation mapping, one domain row, and one range row. Domain/range rows are local typing axioms and do not by themselves make the property relation-mapped, but they do cover the property for source-term coverage and exclude it from the unmapped object-property set. Such properties remain reported separately as listed only in domain/range property-typing rows. At most one populated domain row and one populated range row are allowed per property. Multiple OWL domain or range axioms are conjunctive, so alternatives must be combined in one target with Manchester `or`.

## Checks Performed

Each complete check:

1. Opens the workbook and records its SHA-256.
2. Compiles `tools/generate_mapping_from_coms.py`.
3. Runs the existing generator against temporary outputs.
4. Uses the generator's established validation for allowed predicates, source and target resolution, class/property compatibility, exact label-to-IRI resolution, Manchester expressions, domain/range property typing, property chains, duplicates, contradictions, and explicit blank mappings.
5. Runs the maintained SPARQL source inventory and unmapped-term coverage queries.
6. Parses the temporary generated candidate.
7. Builds the full local candidate closure from CCO, SOSA, SOSA Sampling, SSN, SSN Systems, and the generated candidate.
8. Applies the established import and SOSA functional/inverse-functional cleanup.
9. Runs HermiT and requires zero `owl:Nothing` and zero unexpected named unsatisfiable classes.
10. Requires all generated reports and validates hash-based source metadata.
11. Derives and reconciles all per-product row and canonical-axiom dispositions, including target-vocabulary categories and canonical JSON serialization.
12. Generates and validates the import-free 29-axiom SSN/SOSA alignment core, including root reconciliation and a fixed local source-ontology HermiT closure.
13. Generates and validates the 19-axiom strict BFO mapping, its sole alignment-core import, the 48-axiom project-module closure, and the explicit network-free pinned merged CCO/BFO HermiT closure.
14. Generates and validates the 57-axiom CCO extension, its sole strict-BFO import, the complete 105-axiom project-module closure, and the explicit network-free pinned merged CCO/BFO HermiT closure.
15. Reconciles all 105 BFO-projection dispositions, generates the intentional zero-direct-axiom import-only module, validates its 48-axiom strict/core project closure, and reuses the same-transaction strict-BFO reasoning result after exact closure-equivalence validation.
16. Runs `git diff --check`.

The generated validation report records the workbook SHA-256, generator-file SHA-256, UTC generation timestamp, maintained ontology path, and generated ontology SHA-256. Freshness never relies on timestamps alone.

## Last-Known-Good Outputs

Generation and validation happen under `.cache/coms/`. The maintained files are replaced only after all temporary checks pass:

- `SSN2BFO.ttl`
- `reports/coms-generation-validation.md`
- `reports/coms-source-term-coverage.md`
- `reports/coms-vs-pre-coms-legacy-diff.md`
- `reports/coms-product-dispositions.json`
- `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl`
- `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl`
- `releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl`
- `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl`

Each replacement is atomic. If any check fails, the maintained last-known-good files remain unchanged. A post-replacement whitespace failure also triggers rollback from temporary backups.

The product-disposition JSON is generated evidence rather than an editable mapping source. The alignment core, strict BFO mapping, import-only BFO projection, and CCO extension are maintained authoritative development artifacts, not frozen formal releases. The strict graph imports only the alignment core, the projection and CCO extension each import only the strict graph, and the projection intentionally asserts zero direct axioms while 57 CCO-bearing or mixed dispositions remain deferred. `imports/cco.ttl` is used solely in pinned merged CCO/BFO validation closures and is not a published modular-product import. All artifacts are published in one nine-output transaction, so no maintained output can become newer or older than its disposition accounting or selected modular content.

`SSN2BFO.ttl` is the authoritative generated publication artifact. `mappings/SSN2BFO-COMS.xlsx` is its sole editable mapping source, and `legacy/SSN2BFO-pre-COMS.ttl` is used only as the frozen informational comparison baseline.

The last successful result is stored in `.cache/coms/last-success.json`. Detailed failure output is written to `.cache/coms/last-failure.log`. The `.cache/coms/` directory is ignored and must not be committed.

## Enforcement

`make watch-coms` provides immediate local feedback while the workbook is being edited. `make check-coms` remains the manual, pre-PR, and CI enforcement command. `python tools/run_validation_suite.py` also runs the non-mutating `--check-only` gate so stale or invalid COMS artifacts cannot pass ordinary repository validation.
