# SSN-to-BFO

The alignment in this repo follows and extends the method proposed in Prudhomme, Tim, Giacomo De Colle, Austin Liebers, Alec Sculley, Peihong “Karl” Xie, Sydney Cohen, and John Beverley. “A Semantic Approach to Mapping the Provenance Ontology to Basic Formal Ontology.” _Scientific Data_ 12, no. 1 (February 17, 2025): 282. https://doi.org/10.1038/s41597-025-04580-1.

## Maintained products and inactive source scaffolding

The current SSN/SOSA track is represented by the integrated ontology and four maintained modular products generated from governed COMS. The former current-track editor and direct-mapping scaffold has been retired; it is not an alias or compatibility layer for the maintained products.

The separate `sosa-next` scaffold is intentionally retained but inactive. Its temporary name, editor source, catalog, and two release shells do not participate in current generation, validation, package construction, or publication.

## Mapping authority

`mappings/SSN2BFO-COMS.xlsx` is the sole editable mapping authority. Root-level `SSN2BFO.ttl` is the authoritative generated publication artifact; direct edits to it are prohibited because `make check-coms` regenerates, validates, and atomically replaces it from the workbook only after the candidate passes all checks.

`legacy/SSN2BFO-pre-COMS.ttl` is a frozen, byte-preserved snapshot of the manually maintained ontology that preceded COMS authority. It and `legacy/workbooks/Current_SOSA-SSN to BFO-CCO.xlsx` are historical comparison sources, not release authorities. COMS is not required to reproduce every legacy axiom.

For historical investigation only, `make legacy-audit-write` compares those two pre-COMS sources. The frozen `tools/test_object_property_typing_probes.py` profile likewise targets the legacy ontology. Neither diagnostic is part of the default validation or release gate.

Historical spreadsheets are preserved under `legacy/workbooks/`:

- `legacy/workbooks/Current_SOSA-SSN to BFO-CCO.xlsx`
- `legacy/workbooks/FINAL_SOSA 2023 to BFO-CCO .xlsx`

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

The published strict graph contains no CCO or RO logical terms and does not import an external ontology. Validation reasons over an explicit, network-free pinned merged CCO/BFO closure that includes `imports/cco.ttl`; this validation dependency does not make CCO part of the published strict graph and is not mapping authority. The graph emits the seven governed development annotations; actual release selection/publication and transformation rules remain deferred. Run `make check-strict-bfo-mapping` for the focused tests and shared nonmutating transaction.

### BFO projection

`releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl` is a maintained authoritative development artifact that imports only the strict BFO mapping. It intentionally asserts zero direct projection axioms because no CCO-to-BFO transformation or weakened-consequence rule is approved. Its locally resolved project-module closure is therefore exactly the 48 governed axioms already provided by strict BFO and the alignment core: 19 through import and 29 transitively.

The direct nine-triple graph contains one ontology declaration, one strict-BFO import, and the seven governed development annotations; it contains zero logical mapping triples. It contains no source, BFO, CCO, or RO logical mapping content and is not an incomplete serialization. The BFO projection is the designated product for approved weaker but sound BFO consequences, but no direct projection axiom is currently approved. The generator reconciles all 105 product dispositions, leaving 25 CCO-bearing and 32 mixed axioms explicitly deferred, then reuses the same-transaction strict-BFO pinned merged CCO/BFO reasoning result only after proving exact closure equivalence. Future direct projection axioms require governed transformation rules and proof obligations. Actual release selection and publication remain deferred. Run `make check-bfo-projection` for the focused tests and shared nonmutating nine-output transaction.

### CCO extension

`releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` is the maintained authoritative development artifact for 57 unchanged governed COMS axioms: 25 CCO-bearing and 32 mixed BFO/CCO axioms. It imports only the strict BFO mapping, whose alignment-core import completes a 105-axiom project-module closure without directly duplicating either imported layer.

The published extension contains no RO terms, transformed mappings, weakened projections, or copied dependency declarations. Its fixed semantic validation uses the explicitly listed local source ontologies and the pinned merged CCO/BFO dependency `imports/cco.ttl`; neither CCO nor BFO is imported by the published extension. The graph emits the seven governed development annotations; actual release selection/publication and transformation rules remain deferred. Run `make check-cco-extension` for the focused tests and shared nonmutating transaction.

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

`tools/build_release.py` builds a deterministic candidate package only at an explicit, absent output directory, and `tools/check_release.py validate --package-dir PATH` validates an existing package read-only. The builder requires an explicit release identifier, matching date and tag, full source-commit SHA, repository-relative approved notes file, and exact output directory; it never infers or overwrites them.

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

`tools/build_release.py` remains the authoritative package builder and `tools/check_release.py` remains the authoritative package checker. `tools/release_archive.py` deterministically constructs and validates the package archive as raw, uncompressed POSIX USTAR bytes: fixed member order and metadata, zero member mtimes, zero-filled file-record padding, and exactly two final all-zero 512-byte EOF records with no additional record padding. Canonical numeric fields use seven zero-padded ASCII octal digits followed by NUL for mode, uid, gid, device major, and device minor; eleven zero-padded ASCII octal digits followed by NUL for size and mtime; and six zero-padded ASCII octal digits, NUL, then ASCII space for checksum. The checksum calculation treats all eight checksum-field bytes as ASCII spaces. Base-256, signed, space-terminated, non-octal, overflowing, and other noncanonical encodings are rejected. The external `build --output-dir ABSOLUTE_PATH` operation stages and validates the archive plus sidecar as one private pair, then publishes their absent containing directory with one no-replace atomic rename; it never exposes a one-file pair. Its lowercase SHA-256 sidecar is outside the archive. `tools/rehearse_release.py verify` requires the requested full commit to equal an unchanged clean invoking `HEAD`, then builds and validates two isolated local detached clones from that exact commit with Python socket access blocked. It compares their complete 13-file packages, canonical manifests, archives, and sidecars, then retains no artifact. Rehearsal `build --output-dir ABSOLUTE_PATH` performs the same proof before one final no-replace atomic creation of an absent external directory; a published output is never cleanup-owned. It never changes the invoking checkout, creates a tag, uploads, creates a GitHub release, or deploys anything. Run `make check-release-archive` and `make check-release-rehearsal` for focused gates; a full real two-clone rehearsal remains an explicit, slower command after these tools and the committed synthetic fixture are committed.

No release package or archive is committed to the repository. The first governed GitHub release, `v2026-07-18`, was published from commit `221c65ab27b59ae701f2ed73a98cb9e79d77b750`; its deterministic archive and checksum sidecar are distributed as release assets rather than tracked repository files. Persistent IRI deployment and creator/contributor governance remain later work.

`release-notes/SYNTHETIC-2099-01-02.md` is a committed deterministic release-engineering fixture for package and post-commit rehearsal validation only. It is not an actual release announcement and does not select a real identity, tag, upload, GitHub release, or deployment.

## Development dependencies and source scaffolding

COMS is the sole editable mapping authority. The current maintained modules replace the retired editor, direct-mapping shells, and ungoverned hierarchy-projection analysis. No development XML catalog is required: validation explicitly loads the five pinned local Turtle dependencies under `imports/` and resolves project-module imports through governed local paths.

`imports/cco.ttl` is a full flattened merged CCO/BFO validation dependency, not a placeholder and not an editable mapping source. The `sosa-next` editor, catalog, and release shells remain intact as inactive lifecycle scaffolding; only its own optional local targets consume them. The source dispatcher retains those `sosa-next` targets and current example validation, but current product generation and release construction remain rooted in COMS and the maintained products.

The XML catalog inside a formal 13-file release package is different from a development catalog. It is generated by the package builder, maps exactly the five immutable same-release version IRIs to package-relative products, and is byte-governed by package validation. This cleanup introduces no old-path compatibility promise, redirect, or persistent-IRI deployment. No actual release has occurred.

## Example validation

Current SSN/SOSA example instance data lives under `src/current-ssn-sosa/examples/sosa-instance-data/`. These files are example data, not ontology imports, mapping authorities, or maintained product inputs.

Run the current-track parse check with:

```bash
make -C src/current-ssn-sosa validate-examples
```

Or through the root dispatcher:

```bash
make -C src validate-examples
```

This target uses ROBOT `convert` to parse-check every `.ttl` file under `src/current-ssn-sosa/examples/` and writes temporary generated output under `src/current-ssn-sosa/build/artifacts/`. The source-level default remains the retained inactive `sosa-next` workflow; current examples are invoked explicitly through `validate-examples`.

## License

Except for identified third-party material, project-authored content in this repository is made available under CC0 1.0 Universal, as set out in `LICENSE`. The CC0 dedication applies only to project-authored content directly asserted in the generated products. It does not apply to ontology content obtained through imports, referenced as a dependency, or used only for validation; those third-party resources retain their own notices and terms. Annotating a project ontology with the CC0 IRI does not relicense its import closure or validation dependencies.

Files under `imports/` retain their original licenses, rights statements, and notices. This includes CCO material carrying its BSD 3-Clause/CUBRC terms and SSN/SOSA material carrying applicable W3C/OGC terms.

Source example data under `src/current-ssn-sosa/examples/` may contain third-party W3C/OGC material and retains its applicable original terms and notices. Any other incorporated third-party material remains governed by its original license and notices.

Users redistributing third-party files should preserve their embedded or accompanying notices.
