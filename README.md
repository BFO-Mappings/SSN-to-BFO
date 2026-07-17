# SSN-to-BFO

The alignment in this repo follows and extends the method proposed in Prudhomme, Tim, Giacomo De Colle, Austin Liebers, Alec Sculley, Peihong “Karl” Xie, Sydney Cohen, and John Beverley. “A Semantic Approach to Mapping the Provenance Ontology to Basic Formal Ontology.” _Scientific Data_ 12, no. 1 (February 17, 2025): 282. https://doi.org/10.1038/s41597-025-04580-1.

## Two-track SSN/SOSA to BFO/CCO scaffold

This repository now includes scaffolded structure for two source ontology tracks:

- current SSN/SOSA: the current released SSN/SOSA ontology track.
- sosa-next: the forthcoming SOSA-only ontology track. This name remains temporary until the final release name or version is supplied.

Each track supports two direct-mapping deliverables:

- BFO direct mappings.
- CCO direct mappings.

## Mapping authority

`mappings/SSN2BFO-COMS.xlsx` is the sole editable mapping authority. Root-level `SSN2BFO.ttl` is the authoritative generated publication artifact; direct edits to it are prohibited because `make check-coms` regenerates, validates, and atomically replaces it from the workbook only after the candidate passes all checks.

`legacy/SSN2BFO-pre-COMS.ttl` is a frozen, byte-preserved snapshot of the manually maintained ontology that preceded COMS authority. It and `Current_SOSA-SSN to BFO-CCO.xlsx` are historical comparison sources, not release authorities. COMS is not required to reproduce every legacy axiom.

For historical investigation only, `make legacy-audit-write` compares those two pre-COMS sources. The frozen `tools/test_object_property_typing_probes.py` profile likewise targets the legacy ontology. Neither diagnostic is part of the default validation or release gate.

Historical spreadsheets remain preserved at the repository root:

- `Current_SOSA-SSN to BFO-CCO.xlsx`
- `FINAL_SOSA 2023 to BFO-CCO .xlsx`

### COMS row identity

Every governed row in `mappings/SSN2BFO-COMS.xlsx` has a persistent `coms:RowID` using the lowercase canonical UUIDv4 URN form `urn:uuid:xxxxxxxx-xxxx-4xxx-[89ab]xxx-xxxxxxxxxxxx`. The RowID identifies the mapping record and remains unchanged when a row moves or receives an intentional in-place correction. A separate canonical source-expression SHA-256 excludes row location and `coms:Reasoning`, so it detects logical mapping changes without treating rationale edits or row movement as identity changes.

RowIDs must never be reused. Deletion, retirement, replacement, splitting, and merging of governed rows remain prohibited until a governed lineage and retirement registry exists. Two active rows may not resolve to the same canonical authoritative axiom, even when their RowIDs, locations, or rationales differ. Run the focused identity and normal COMS checks with `make check-coms-row-identities`.

### COMS product dispositions

`reports/coms-product-dispositions.json` is generated evidence accounting for every governed row and canonical authoritative axiom across the integrated, alignment-core, strict-BFO-mapping, BFO-projection, and CCO-extension products. It is derived from COMS RowIDs, canonical expressions, and `config/publication-metadata.toml`; it is not an editable mapping authority.

The artifact classifies axioms as target-neutral, BFO-bearing, CCO-bearing, or mixed BFO/CCO and records the approved per-product status. CCO-bearing and mixed axioms remain explicitly deferred for strict BFO transformation and BFO projection because no transformation rule or weakened projection is approved. Run the focused nonmutating gate with `make check-coms-product-dispositions`.

### SSN/SOSA alignment core

`releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` is the maintained authoritative development artifact for the 29 target-neutral governed COMS axioms. It is generated from the same in-memory COMS identities and product dispositions as the integrated root, contains 15 domain and 14 range axioms, and imports no source, target, or project ontology. The integrated `SSN2BFO.ttl` remains the complete standalone authoritative product; the alignment core does not replace it.

Like every maintained ontology product, the development artifact emits the seven governed schema-3 development annotations for label, description, product type, development authority status, CC0 license, repository reference, and generated-file warning. Run its focused tests and the shared nonmutating transaction with `make check-alignment-core`.

### Strict BFO mapping

`releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` is the maintained authoritative development artifact for the 19 unchanged BFO-bearing governed COMS axioms. It imports only the alignment core, so the locally resolved project-module closure contains 48 governed axioms: 19 direct strict-BFO axioms plus 29 target-neutral core axioms. The 57 CCO-bearing or mixed mappings remain explicitly deferred because no transformation or weakened projection is approved.

The published strict graph contains no CCO or RO logical terms and does not import an external ontology. Validation reasons over an explicit, network-free pinned merged CCO/BFO closure that includes `imports/cco.ttl`; this validation dependency does not make CCO part of the published strict graph and is not mapping authority. The graph emits the seven governed development annotations; actual release selection/publication and transformation rules remain deferred. The old `releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl` file remains inactive, non-authoritative scaffolding pending complete modular-product migration. Run `make check-strict-bfo-mapping` for the focused tests and shared nonmutating transaction.

### BFO projection

`releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl` is a maintained authoritative development artifact that imports only the strict BFO mapping. It intentionally asserts zero direct projection axioms because no CCO-to-BFO transformation or weakened-consequence rule is approved. Its locally resolved project-module closure is therefore exactly the 48 governed axioms already provided by strict BFO and the alignment core: 19 through import and 29 transitively.

The direct nine-triple graph contains one ontology declaration, one strict-BFO import, and the seven governed development annotations; it contains zero logical mapping triples. It contains no source, BFO, CCO, or RO logical mapping content and is not an incomplete serialization. The BFO projection is the designated product for approved weaker but sound BFO consequences, but no direct projection axiom is currently approved. The generator reconciles all 105 product dispositions, leaving 25 CCO-bearing and 32 mixed axioms explicitly deferred, then reuses the same-transaction strict-BFO pinned merged CCO/BFO reasoning result only after proving exact closure equivalence. Future direct projection axioms require governed transformation rules and proof obligations. Actual release selection and publication remain deferred. Run `make check-bfo-projection` for the focused tests and shared nonmutating nine-output transaction.

### CCO extension

`releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` is the maintained authoritative development artifact for 57 unchanged governed COMS axioms: 25 CCO-bearing and 32 mixed BFO/CCO axioms. It imports only the strict BFO mapping, whose alignment-core import completes a 105-axiom project-module closure without directly duplicating either imported layer.

The published extension contains no RO terms, transformed mappings, weakened projections, or copied dependency declarations. Its fixed semantic validation uses the explicitly listed local source ontologies and the pinned merged CCO/BFO dependency `imports/cco.ttl`; neither CCO nor BFO is imported by the published extension. The graph emits the seven governed development annotations; actual release selection/publication and transformation rules remain deferred. The old `releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl` file remains inactive, non-authoritative scaffolding pending complete modular-product migration. Run `make check-cco-extension` for the focused tests and shared nonmutating transaction.

## Validation environment

`make check` is the canonical authoritative validation gate used both locally and by hosted CI. It validates the COMS workbook and authoritative root mapping, including freshness, source coverage, focused generator tests, example checks, HermiT consistency, Python compilation, whitespace, and repository cleanliness as currently implemented.

`requirements-validation.txt` declares the direct Python packages. `config/validation-toolchain.env` declares the supported Python, Java, and ROBOT versions together with the ROBOT release URL, checksum, and Java heap. `.github/workflows/test-mappings.yml` consumes those same declarations instead of maintaining an independent version list.

The validation commands do not automatically install Python or Java dependencies. Java 22 must already be installed and available on `PATH`. The ROBOT installer is an explicit bootstrap helper that verifies the JAR checksum on every invocation. By default it installs under ignored `build/lib/`; pass a custom installation directory as its first argument when needed.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-validation.txt
python -m pip check

robot_bin="$(tools/install_validation_robot.sh)"
export PATH="${robot_bin}:${PATH}"

java -version
robot --version
make check
```

### Publication metadata validation

`config/publication-metadata.toml` is the sole editable publication-metadata source. Schema version 3 governs the five product paths, stable ontology IRIs, release suffixes, English labels, lifecycle-neutral descriptions, CC0 license IRI, repository IRI, product-type IRIs, development and immutable-release authority statuses, and generated-file warning. Every maintained development ontology still deterministically emits exactly seven annotations in this order: `rdfs:label`, `dcterms:description`, `dcterms:type`, `adms:status`, `dcterms:license`, `rdfs:seeAlso`, and `rdfs:comment`. Labels, descriptions, and warnings use `@en`; the remaining values are IRIs.

Run the focused tests and development-mode validation with:

```bash
make check-publication-metadata
python tools/check_publication_metadata.py
```

Development mode validates and emits the governed static annotations without claiming immutable release identity. Formal rendering requires an explicit immutable context with a real `YYYY-MM-DD` release identifier and matching date, a `vYYYY-MM-DD` tag, and a full lowercase 40-hex source commit. The following checker invocation is illustrative synthetic input only; it validates context and version-IRI construction but does not build an ontology:

```bash
python tools/check_publication_metadata.py \
  --mode release \
  --release-id 2099-01-02 \
  --release-date 2099-01-02 \
  --git-tag v2099-01-02 \
  --source-commit 0123456789abcdef0123456789abcdef01234567
```

Formal renderers preserve each stable ontology IRI as the `owl:Ontology` subject, replace the development status with the immutable-release status, and add exactly `owl:versionIRI`, plain `owl:versionInfo`, and `dcterms:issued` as `xsd:date`. Modular imports use same-release version IRIs; the integrated root retains its four external imports. `make check-release-rendering` proves deterministic bytes, logical-graph preservation, exact closure counts, and independent HermiT consistency for all five synthetic formal products.

`tools/build_release.py` now builds a deterministic candidate package only at an explicit, absent output directory, and `tools/check_release.py validate --package-dir PATH` validates an existing package read-only. The builder requires an explicit release identifier, matching date and tag, full source-commit SHA, repository-relative approved notes file, and exact output directory; it never infers or overwrites them. Source-commit binding to a clean checkout is not implemented yet.

The package has exactly 13 regular files:

```text
<release-id>/
  LICENSE
  RELEASE-NOTES.md
  SHA256SUMS
  SSN2BFO.ttl
  catalog-v001.xml
  current-ssn-sosa/ssn-sosa-alignment-core.ttl
  current-ssn-sosa/ssn-sosa-bfo-mapping.ttl
  current-ssn-sosa/ssn-sosa-bfo-projection.ttl
  current-ssn-sosa/ssn-sosa-cco-extension.ttl
  evidence/coms-product-dispositions.json
  manifest.json
  sources/SSN2BFO-COMS.xlsx
  sources/publication-metadata.toml
```

Manifest schema version 1 records formal context, governed inputs and byte-affecting modules, product counts and hashes, pinned validation dependencies, stable toolchain evidence, independent validation outcomes, and the 11 non-manifest/non-checksum included files. `catalog-v001.xml` maps only the five immutable version IRIs to package-relative products. `SHA256SUMS` uses lowercase SHA-256, two spaces, and a normalized relative path for every regular file except itself; it includes `manifest.json`. External ontologies are not redistributed, so the package is offline-complete for project-module imports only.

Run `make check-release-package` for the synthetic package gate. No actual release package or archive is committed, no actual release identifier/date/notes have been selected, and no tag or GitHub release has been created. Clean-checkout rehearsal, deterministic archive generation, tag readiness, placeholder cleanup, persistent IRI deployment, creator/contributor governance, and publication remain later work.

The four new release files under `releases/` are placeholders until completed mapping content is inserted:

- `releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl`
- `releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl`
- `releases/sosa-next/sosa-bfo-directmappings.ttl`
- `releases/sosa-next/sosa-cco-directmappings.ttl`

Development editor placeholders live under `src/current-ssn-sosa/` and `src/sosa-next/`. Their per-track targets remain available as optional local scaffold workflows for artifact hygiene, but they are not the authoritative hosted CI or release gate and do not validate the COMS/root mapping authority. Hosted CI runs `make check`.

Run local validation with:

```bash
make -C src/current-ssn-sosa all
make -C src/sosa-next all
make -C src all
```

Release-file BFO projection from CCO mappings is not implemented in this migration. The authoritative root ontology is generated from the COMS workbook by `make check-coms`.

## Workflow artifacts and reports

The `all` targets remain the basic validation workflow for each track. They run reasoning over the editor ontology and the existing hygiene SPARQL checks. They do not generate release mappings and they do not evaluate mapping correctness.

Additional generated artifacts can be produced with:

```bash
make -C src reports
make -C src sssom
make -C src entailed-mappings
make -C src unmapped
make -C src artifacts
```

`reports` runs ROBOT report generation for both editor ontologies and writes TSV reports under each track's `build/artifacts/` directory.

`sssom` runs generic SSSOM-style CSV exports over authored TTL mappings for each track's BFO and CCO target deliverables. These exports are generated report artifacts, not release files.

`entailed-mappings` materializes derived TTL artifacts under each track's `build/artifacts/` directory. These generated files are not release mappings and should not be treated as authored mapping content.

`unmapped` is scaffolded but disabled by default. It exits successfully with a message until real source imports and final source namespace configuration are added.

Generated build artifacts are ignored by Git. The maintained BFO-projection module is import-only; projected or weakened mapping content from CCO mappings is not implemented. Root spreadsheets and the root `imports/` directory remain preserved; `SSN2BFO.ttl` is a maintained generated artifact.

## Current SSN/SOSA CCO mapping and BFO-only projection

Under this project's convention, a mapping file counts as a CCO direct mapping when its target vocabulary includes CCO terms, even when it also includes BFO terms, because CCO imports and extends BFO. A BFO direct mapping is BFO-only: its mapping targets should be BFO IRIs and not CCO IRIs.

The root `SSN2BFO.ttl` file is the authoritative generated current SSN/SOSA to CCO mapping. Edit `mappings/SSN2BFO-COMS.xlsx`, then run `make check-coms`; do not edit the Turtle file directly.

The current SSN/SOSA track includes a generated-artifact workflow for deriving a review-only BFO-only artifact from `SSN2BFO.ttl` and `imports/cco.ttl`:

```bash
make -C src/current-ssn-sosa derive-bfo-from-cco
make -C src derive-bfo-from-cco
```

The generated BFO-only artifact is written to `src/current-ssn-sosa/build/artifacts/current-ssn-sosa-bfo-only-generated.ttl`. It combines direct BFO-target mappings in the authoritative generated `SSN2BFO.ttl` with conservative BFO projections from direct named CCO targets that have explicit CCO to BFO superclass or superproperty paths in `imports/cco.ttl`.

The skipped-target report is written to `src/current-ssn-sosa/build/artifacts/current-ssn-sosa-bfo-only-skipped-cco-targets.csv`. CCO targets without explicit BFO paths are reported there rather than guessed.

This generated artifact is not a release file. The BFO release placeholder is not populated by this workflow. Complex blank-node expressions, restrictions, intersections, unions, property chains, labels, comments, definitions, natural-language notes, and mapping justifications are skipped. No `sosa-next` projection is implemented yet.

## Example validation

Current SSN/SOSA example instance data lives under `src/current-ssn-sosa/examples/sosa-instance-data/`. These files are example data, not ontology imports, and they are not currently imported into the editor ontology.

Run the current-track parse check with:

```bash
make -C src/current-ssn-sosa validate-examples
```

Or through the root dispatcher:

```bash
make -C src validate-examples
```

This target uses ROBOT `convert` to parse-check every `.ttl` file under `src/current-ssn-sosa/examples/` and writes temporary generated output under `src/current-ssn-sosa/build/artifacts/`. It is not part of `all`.

## License

Except for identified third-party material, project-authored content in this repository is made available under CC0 1.0 Universal, as set out in `LICENSE`. The CC0 dedication applies only to project-authored content directly asserted in the generated products. It does not apply to ontology content obtained through imports, referenced as a dependency, or used only for validation; those third-party resources retain their own notices and terms. Annotating a project ontology with the CC0 IRI does not relicense its import closure or validation dependencies.

Files under `imports/` retain their original licenses, rights statements, and notices. This includes CCO material carrying its BSD 3-Clause/CUBRC terms and SSN/SOSA material carrying applicable W3C/OGC terms.

Source example data under `src/current-ssn-sosa/examples/` may contain third-party W3C/OGC material and retains its applicable original terms and notices. Any other incorporated third-party material remains governed by its original license and notices.

Users redistributing third-party files should preserve their embedded or accompanying notices.
