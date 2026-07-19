# Sample Representation Property Chains Review

This note reviews the remaining TTL-only property-chain assertions for `sosa:hasSample` and `sosa:isSampleOf`.

No TTL or spreadsheet changes are made by this note.

## Current audit pattern

The TTL contains property-chain axioms for:

- `sosa:hasSample`
- `sosa:isSampleOf`

The spreadsheet currently contains:

- for `sosa:hasSample`: domain and range axioms only;
- for `sosa:isSampleOf`: an inverse-property axiom only.

Accordingly, the audit reports the TTL property chains as `missing_in_spreadsheet`.

## TTL assertions reviewed

### `sosa:hasSample`

Current TTL:

`owl:propertyChainAxiom ( cco:ont00001873 BFO_0000084 )`

This appears to encode a representational chain from a feature of interest through representation to the sample that carries or realizes the relevant representational content.

### `sosa:isSampleOf`

Current TTL:

`owl:propertyChainAxiom ( BFO_0000101 cco:ont00001938 )`

This appears to encode the inverse representational chain from a sample, through carried representational content, to the entity represented.

## Spreadsheet evidence

The spreadsheet `sosa:hasSample` row does not currently assert the property chain in the `OWL Axiom` cell.

However, the spreadsheet reasoning says that "Sample of" is fundamentally representational and that the mapping is a conservative upper mapping to that representational pattern.

The spreadsheet `sosa:isSampleOf` row is documented as the inverse of `sosa:hasSample`.

## Review finding

The TTL property chains should not be treated as arbitrary stale TTL assertions.

They appear to implement the representational interpretation already described in the spreadsheet reasoning, but that interpretation is not yet represented explicitly in the spreadsheet `OWL Axiom` cells.

## Decision

Defer mechanical TTL removal.

The next decision should be whether the spreadsheet should explicitly document the representational property-chain axioms, or whether the project wants to keep only lightweight domain/range and inverse axioms for sample relations.

## Recommended follow-up

Do not edit `SSN2BFO.ttl` yet.

Recommended next step:

1. Confirm whether the sample-as-representation model is intended to be machine-asserted.
2. If yes, create a spreadsheet-only PR documenting the property-chain axioms in the `OWL Axiom` cells for `sosa:hasSample` and `sosa:isSampleOf`.
3. If no, create a TTL-removal PR removing the property-chain axioms from `SSN2BFO.ttl`.
