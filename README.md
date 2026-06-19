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

