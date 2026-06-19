# SSN-to-BFO

The alignment in this repo follows and extends the method proposed in Prudhomme, Tim, Giacomo De Colle, Austin Liebers, Alec Sculley, Peihong “Karl” Xie, Sydney Cohen, and John Beverley. “A Semantic Approach to Mapping the Provenance Ontology to Basic Formal Ontology.” _Scientific Data_ 12, no. 1 (February 17, 2025): 282. https://doi.org/10.1038/s41597-025-04580-1.

## Two-track SSN/SOSA to BFO/CCO scaffold

This repository now includes scaffolded structure for two source ontology tracks:

- current SSN/SOSA: the current released SSN/SOSA ontology track.
- sosa-next: the forthcoming SOSA-only ontology track. This name remains temporary until the final release name or version is supplied.

Each track supports two direct-mapping deliverables:

- BFO direct mappings.
- CCO direct mappings.

The existing root-level `SSN2BFO.ttl` file is preserved as legacy/current mapping content. It has not been moved, split, normalized, revised, or overwritten by this scaffold migration.

The existing spreadsheets remain preserved at the repository root:

- `Current_SOSA-SSN to BFO-CCO.xlsx`
- `FINAL_SOSA 2023 to BFO-CCO .xlsx`

The four new release files under `releases/` are placeholders until completed mapping content is inserted:

- `releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl`
- `releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl`
- `releases/sosa-next/sosa-bfo-directmappings.ttl`
- `releases/sosa-next/sosa-cco-directmappings.ttl`

Development editor placeholders live under `src/current-ssn-sosa/` and `src/sosa-next/`. The per-track validation workflow currently checks artifact hygiene only: minimal ontology declarations, expected temporary IRI bases, and absence of source-template leakage. It does not check mapping correctness.

Run local validation with:

```bash
make -C src/current-ssn-sosa all
make -C src/sosa-next all
make -C src all
```

BFO projection from CCO mappings is not implemented in this migration. Spreadsheet-to-TTL conversion is also not implemented in this migration.

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

Generated report and artifact files are ignored by Git. Spreadsheet-to-TTL conversion is not implemented. BFO projection from CCO mappings is not implemented. The existing `SSN2BFO.ttl`, root spreadsheets, and root `imports/` directory remain preserved.

