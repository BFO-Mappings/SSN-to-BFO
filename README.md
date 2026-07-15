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

Generated build artifacts are ignored by Git. Release-file BFO projection from CCO mappings is not implemented. Root spreadsheets and the root `imports/` directory remain preserved; `SSN2BFO.ttl` is a maintained generated artifact.

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

Except for identified third-party material, project-authored content in this repository is made available under CC0 1.0 Universal, as set out in `LICENSE`. The CC0 dedication applies only to rights controlled by the project's licensor and does not relicense third-party material.

Files under `imports/` retain their original licenses, rights statements, and notices. This includes CCO material carrying its BSD 3-Clause/CUBRC terms and SSN/SOSA material carrying applicable W3C/OGC terms.

Source example data under `src/current-ssn-sosa/examples/` may contain third-party W3C/OGC material and retains its applicable original terms and notices. Any other incorporated third-party material remains governed by its original license and notices.

Users redistributing third-party files should preserve their embedded or accompanying notices.
