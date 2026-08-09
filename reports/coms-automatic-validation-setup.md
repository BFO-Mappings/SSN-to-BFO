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

`config/publication-metadata.toml` is the sole governed publication-metadata source. Schema version 4 validates the exact approved global values, both authority-status IRIs, and the canonical four-product materialized order, paths, ontology IRIs, release suffixes, labels, descriptions, and product-type IRIs. The separate product-role policy retains the uniform five-role taxonomy, including non-materialized `bfo_projection`. The loader rejects missing or unknown tables and fields, unsafe paths, malformed IRIs, duplicate identities, and noncanonical text.

Development validation checks the governed license, repository, generated warning, `adms:status` predicate, and maintained-authoritative-development status without claiming a formal release identity. A separate frozen formal context validates exact `YYYY-MM-DD` identifier/date values, `vYYYY-MM-DD` tag form, and a full lowercase commit SHA without consulting Git or the clock. Actual context values are not stored in the maintained TOML.

The COMS freshness transaction hashes the metadata source, so a metadata edit makes all generated evidence stale until the normal transaction succeeds. The development transaction loads schema-4 metadata once and deterministically emits the same ordered seven-predicate development metadata model in the integrated root and all three maintained modular products: `rdfs:label`, `dcterms:description`, `dcterms:type`, `adms:status`, `dcterms:license`, `rdfs:seeAlso`, and `rdfs:comment`. Exact RDF term kinds, `@en` tags, ontology subjects, imports, and the absence of release-only fields are validated before publication.

`make check-release-rendering` runs the release-context, formal-rendering, publication-metadata, generator, and modular-product regressions. For the clearly synthetic `2099-01-02` context, formal rendering keeps stable ontology subjects, substitutes the immutable-release status, appends `owl:versionIRI`, plain `owl:versionInfo`, and typed `dcterms:issued`, and rewrites only project imports to same-release version IRIs. It independently reasons over all four materialized formal products; BFO Projection is reconciled as a governed zero-direct-axiom role but is not rendered. The check does not create a dated directory, package, manifest, archive, tag, or published release.

`make check-release-package` runs the release-manifest and package tests plus the release-context and formal-rendering preservation regressions. `tools/build_release.py` creates a deterministic candidate only at an explicit absent temporary output path, and `tools/check_release.py validate --package-dir PATH` independently checks it read-only. The exact 12-file layout contains the four materialized formal TTLs, version-IRI-only OASIS catalog, schema-2 canonical manifest, `SHA256SUMS`, approved release notes, project license, governed workbook and metadata, and product-disposition evidence. External ontology dependencies are recorded by identity and hash but are not redistributed, so only project-module imports resolve wholly inside the package.

The manifest excludes itself and `SHA256SUMS` from `included_files`; `SHA256SUMS` includes `manifest.json` and excludes only itself, with lowercase hashes, two spaces, lexicographic relative paths, and one final newline. Fixed inputs and context reproduce all 12 package files byte-for-byte across fresh processes. Package output is never overwritten.

`make check-release-archive` runs the raw-USTAR archive regressions and `make check-release-rehearsal` runs the clean-checkout rehearsal regressions. `tools/build_release.py` remains the package authority and `tools/check_release.py` remains the package-check authority. `tools/release_archive.py` emits raw uncompressed POSIX USTAR bytes with fixed member order and metadata, zero member mtimes, zero file-record padding, and exactly two final all-zero 512-byte EOF records followed immediately by EOF. Its numeric fields are canonical: mode, uid, gid, device major, and device minor use seven zero-padded ASCII octal digits plus NUL; size and mtime use eleven zero-padded ASCII octal digits plus NUL; checksum uses six zero-padded ASCII octal digits, NUL, and ASCII space, while checksum calculation substitutes ASCII spaces for all eight checksum-field bytes. Base-256, signed, space-terminated, non-octal, overflowing, and any other noncanonical encodings are rejected. The standalone archive `build --output-dir` operation creates and validates both external evidence files in one private staging directory and publishes only their complete absent containing directory through one no-replace rename; its lowercase `SSN2BFO-<release-id>.tar.sha256` sidecar remains outside the archive. `tools/rehearse_release.py verify` binds an explicit lowercase 40-character commit to an unchanged clean invoking `HEAD`, makes two isolated local detached clones, and runs the committed builder, checker, archive candidate builder, and archive validator in each clone. It blocks Python socket resolution through temporary `sitecustomize.py`, compares complete package/manifest/archive/sidecar bytes, and removes all candidates. Rehearsal `build --output-dir` performs that same proof before one final no-replace atomic creation of an absent external output directory; a successfully published directory is never cleanup-owned. This remains explicit, slower rehearsal tooling: it does not choose actual release identity or finalized notes, create a tag, upload, create a GitHub release, modify source scaffolding, or deploy persistent IRIs.

`release-notes/SYNTHETIC-2099-01-02.md` is the committed deterministic fixture used for synthetic package and later post-commit rehearsal checks. It remains a read-only test input, not an actual release announcement or publication decision.

## Placeholder And Catalog Migration

COMS is the sole editable mapping authority, and the integrated ontology plus three maintained modular products replace the former current-track editor, direct-mapping shells, import-only BFO Projection artifact, and ungoverned hierarchy-projection analysis. Those obsolete paths and their active Make targets are retired rather than preserved as aliases, wrappers, diagnostics, or compatibility promises.

The current SSN/SOSA COMS transaction requires no development XML catalog: it explicitly loads its pinned local dependencies and resolves maintained current-track project imports through governed local paths. `imports/cco.ttl` remains a full flattened merged CCO/BFO validation dependency, not a placeholder.

The SOSA-next track is separately active as a maintained development track. `src/sosa-next/catalog-v001.xml` resolves its pinned source closure, merged CCO/BFO dependency, Integrated Mapping, BFO Mapping, CCO Extension, and editor shell. The editor imports Integrated; the modular CCO Extension imports only BFO Mapping; BFO Mapping is import-free. The SOSA-next generator and checker enforce deterministic products, exact import boundaries, a 273-triple Integrated mapping graph isomorphic to the BFO+CCO modular union, product-specific reasoning closures of 15,127, 15,011, and 15,135 triples, and a 290-triple catalog-resolved editor project stack. This development activation does not add SOSA-next products to the current formal package or release machinery.

The catalog generated inside a formal release package is unaffected: it remains package-relative, maps exactly the four immutable version IRIs in governed materialized-product order, and is byte-validated with the rest of the 12-file package. This migration does not configure redirects, deploy persistent IRIs, choose an actual release identity, or publish a release.

Formal direct totals are integrated 1,117, alignment core 64, strict BFO 137, and CCO extension 936. The formal fixed closures contain 15,907 triples for the integrated product, 1,217 for the alignment core, 14,994 for strict BFO, and 15,929 for the CCO extension. These increases over development rendering reflect the three formal release-identity triples added per rendered product, together with same-release project import substitution.

Development direct triple partitions are checked independently: integrated `1 + 4 + 7 + 1102 = 1114`, alignment core `1 + 0 + 7 + 53 = 61`, strict BFO `1 + 1 + 7 + 125 = 134`, and CCO extension `1 + 1 + 7 + 924 = 933`, where the terms are ontology declaration, imports, metadata annotations, and governed/structural logical triples. Development fixed-closure counts are 15,904 for the integrated candidate, 1,214 for the alignment core, 14,988 for strict BFO, and 15,920 for the CCO extension.

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
6. Parses the temporary generated candidate and validates its exact seven development annotations separately from its 1 declaration, 4 imports, and 1,102 logical triples.
7. Builds the full local candidate closure from CCO, SOSA, SOSA Sampling, SSN, SSN Systems, and the generated candidate.
8. Applies the established import and SOSA functional/inverse-functional cleanup.
9. Runs HermiT and requires zero `owl:Nothing` and zero unexpected named unsatisfiable classes.
10. Requires all generated reports and validates hash-based source metadata.
11. Derives and reconciles all per-product row and canonical-axiom dispositions, including target-vocabulary categories and canonical JSON serialization.
12. Generates and validates the import-free 29-axiom SSN/SOSA alignment core, its exact seven annotations, root reconciliation, and a 1,214-triple fixed local source-ontology HermiT closure.
13. Generates and validates the 19-axiom strict BFO mapping, its exact seven annotations, sole alignment-core import, 48-axiom project-module closure, and 14,988-triple network-free pinned merged CCO/BFO HermiT closure.
14. Generates and validates the 55-axiom CCO extension, its exact seven annotations, sole strict-BFO import, complete 103-axiom project-module closure, and 15,920-triple network-free pinned merged CCO/BFO HermiT closure.
15. Reconciles all 105 BFO-projection dispositions, requires zero selected direct projection axioms, and confirms that the role is not materialized while no weakened consequence is approved.
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
- `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl`

Each replacement is atomic. If any check fails, the maintained last-known-good files remain unchanged. A post-replacement whitespace failure also triggers rollback from temporary backups.

The product-disposition JSON is generated evidence rather than an editable mapping source. The alignment core, strict BFO mapping, and CCO extension are maintained authoritative development artifacts, not frozen formal releases. The strict graph imports only the alignment core, and the CCO extension imports only the strict graph. BFO Projection remains a governed disposition role with zero selected direct axioms, but no projection ontology is generated or maintained while that state persists. `imports/cco.ttl` is used solely in pinned merged CCO/BFO validation closures and is not a published modular-product import. All maintained COMS artifacts are published in one eight-output transaction, so no maintained output can become newer or older than its disposition accounting or selected modular content.

`SSN2BFO.ttl` is the authoritative generated publication artifact. `mappings/SSN2BFO-COMS.xlsx` is its sole editable mapping source, and `legacy/SSN2BFO-pre-COMS.ttl` is used only as the frozen informational comparison baseline.

The last successful result is stored in `.cache/coms/last-success.json`. Detailed failure output is written to `.cache/coms/last-failure.log`. The `.cache/coms/` directory is ignored and must not be committed.

## Enforcement

`make watch-coms` provides immediate local feedback while the workbook is being edited. `make check-coms` remains the manual, pre-PR, and CI enforcement command. `python tools/run_validation_suite.py` also runs the non-mutating `--check-only` gate so stale or invalid COMS artifacts cannot pass ordinary repository validation.
