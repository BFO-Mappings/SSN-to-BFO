# Mapping Governance

## Authoritative source

`mappings/SSN2BFO-COMS.xlsx` is the sole editable source of governed mapping assertions.

Root-level `SSN2BFO.ttl` and the maintained modular products are generated artifacts. Direct edits are prohibited. `make check-coms` regenerates and validates candidates in a temporary transaction and replaces maintained outputs only after all checks pass.

Only governed COMS content is authoritative. The generator does not treat explanatory documents, historical workbooks, or the pre-COMS ontology as competing mapping authorities.

## Historical sources

The manually maintained ontology that preceded COMS authority is frozen at:

- `legacy/SSN2BFO-pre-COMS.ttl`

Historical workbooks are preserved at:

- `legacy/workbooks/Current_SOSA-SSN to BFO-CCO.xlsx`
- `legacy/workbooks/FINAL_SOSA 2023 to BFO-CCO .xlsx`

These files are evidence for historical comparison, not release authorities. COMS is not required to reproduce every legacy axiom.

For historical investigation only, `make legacy-audit-write` compares the frozen ontology with `legacy/workbooks/Current_SOSA-SSN to BFO-CCO.xlsx`. The frozen `tools/test_object_property_typing_probes.py` profile also targets the legacy ontology. Neither diagnostic is part of the default release gate.

## COMS row identity

Every governed row has a persistent `coms:RowID` in lowercase canonical UUIDv4 URN form:

```text
urn:uuid:xxxxxxxx-xxxx-4xxx-[89ab]xxx-xxxxxxxxxxxx
```

A RowID identifies the mapping record and remains unchanged when the row moves or receives an intentional in-place correction.

A separate canonical source-expression SHA-256 excludes row location and `coms:Reasoning`. It detects logical mapping changes without treating rationale edits or row movement as identity changes.

Current governance rules are:

- RowIDs must never be reused.
- Two active rows may not resolve to the same canonical authoritative axiom.
- Deletion, retirement, replacement, splitting, and merging remain prohibited until a governed lineage and retirement registry is implemented.
- Row position is not identity.
- Rationale text is not logical identity.

Run:

```bash
make check-coms-row-identities
```

## Product dispositions

`reports/coms-product-dispositions.json` accounts for every governed row and canonical authoritative axiom across the maintained products.

It is generated from:

- COMS RowIDs and canonical source expressions
- `config/publication-metadata.toml`
- governed product-classification rules

It is generated evidence, not an editable mapping source.

Axioms are classified as:

- target-neutral
- BFO-bearing
- CCO-bearing
- mixed BFO/CCO

The disposition record identifies whether each axiom is included directly, supplied through a project-module import, or explicitly deferred for a product.

CCO-bearing and mixed axioms remain deferred from strict BFO transformation or direct BFO projection unless a governed transformation rule or weakened-consequence rule is approved.

Run:

```bash
make check-coms-product-dispositions
```

## Editing and validation rules

When changing mappings:

1. Edit `mappings/SSN2BFO-COMS.xlsx`.
2. Preserve existing RowIDs for in-place corrections.
3. Do not edit generated ontology products directly.
4. Run the focused COMS checks.
5. Run `make check` before opening a pull request.
6. Treat historical files and reports as evidence, not assertion-bearing inputs.

Generated reports may document decisions and validation outcomes, but they do not supersede COMS.
