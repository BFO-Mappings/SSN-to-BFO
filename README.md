# SSN-to-BFO

SSN-to-BFO provides governed mappings from SSN/SOSA to Basic Formal Ontology (BFO) and the Common Core Ontologies (CCO). The alignment follows and extends the method presented in Prudhomme et al., “[A Semantic Approach to Mapping the Provenance Ontology to Basic Formal Ontology](https://doi.org/10.1038/s41597-025-04580-1),” _Scientific Data_ 12 (2025): 282.

## Mapping authority

COMS is the sole editable mapping authority. Mapping changes must be made in:

- `mappings/SSN2BFO-COMS.xlsx`

Root-level `SSN2BFO.ttl` is the authoritative generated integrated ontology and must not be edited directly. Historical pre-COMS ontology and workbook sources are preserved under `legacy/` for comparison only.

See [Mapping Governance](docs/MAPPING-GOVERNANCE.md) for RowID rules, historical-source treatment, product dispositions, and editing constraints.

## Maintained products

| Product | Path | Purpose |
| --- | --- | --- |
| Integrated mapping | `SSN2BFO.ttl` | Complete governed COMS axiom set |
| Alignment core | `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` | Target-neutral SSN/SOSA alignment axioms |
| Strict BFO mapping | `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` | Governed BFO-bearing axioms |
| BFO projection | `releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl` | Approved weaker BFO consequences; currently no direct projection axioms |
| CCO extension | `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` | Governed CCO-bearing and mixed BFO/CCO axioms |

See [Product Architecture](docs/PRODUCT-ARCHITECTURE.md) for product boundaries, imports, counts, and inactive source scaffolding.

## Validation

`make check` is the canonical local and hosted-CI validation gate.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-validation.txt
python -m pip check

robot_bin="$(tools/install_validation_robot.sh)"
export PATH="${robot_bin}:${PATH}"

make check
```

Java 22 and ROBOT must be available. No development XML catalog is required; validation resolves the pinned local dependencies and project modules directly.

Focused deterministic release checks use `tools/release_archive.py` and `tools/rehearse_release.py` through:

```bash
make check-release-archive
make check-release-rehearsal
```

See [Validation and Release Engineering](docs/VALIDATION-AND-RELEASES.md) for the toolchain, publication metadata, package format, deterministic archive rules, rehearsal process, and example validation.

## Current release

The first governed GitHub release is [`v2026-07-18`](https://github.com/BFO-Mappings/SSN-to-BFO/releases/tag/v2026-07-18), published from commit `221c65ab27b59ae701f2ed73a98cb9e79d77b750`.

Release packages and checksum sidecars are distributed as GitHub release assets rather than committed repository files.

## Development

Repository workflow and contribution guidance:

- [Contributing](CONTRIBUTING.md)
- [Branching Policy](BRANCHING.md)
- [Agent Instructions](AGENTS.md)

Routine changes follow:

```text
feature/* -> dev -> stage -> main
```

## License

Project-authored content is dedicated under [CC0 1.0 Universal](LICENSE), except for identified third-party material. Imported, referenced, validation-only, and example materials retain their original terms. See [Licensing](docs/LICENSING.md) for the scope and redistribution guidance.
