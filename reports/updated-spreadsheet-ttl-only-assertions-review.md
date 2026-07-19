# Updated Spreadsheet / TTL-Only Assertions Review

This note reviews the 13 remaining `missing_in_spreadsheet` issues after confirming that the audit tool reads expected spreadsheet assertions from the `IRI` and `OWL Axiom` columns, not from documentation columns.

No TTL or spreadsheet changes are made by this note.

## Finding

The 13 `missing_in_spreadsheet` issues are not isolated extra TTL assertions. Each reviewed source term also has a paired `missing_in_ttl` issue showing the assertion currently present in the spreadsheet `OWL Axiom` cell.

This indicates that the main reconciliation problem is stale or divergent TTL content relative to the updated spreadsheet, not audit overreach.

## Paired issue pattern

### Class mappings updated in spreadsheet

- `sosa:Sampler`
  - TTL-only: old `rdfs:subClassOf` expression.
  - Spreadsheet-only: current `owl:equivalentClass` expression.
  - Follow-up: review as a replacement of the old TTL class axiom with the updated spreadsheet class axiom, not as a simple removal.

- `sosa:Sensor`
  - TTL-only: old `rdfs:subClassOf` expression.
  - Spreadsheet-only: current `owl:equivalentClass` expression to `cco:Sensor`.
  - Follow-up: review as a replacement of the old TTL class axiom with the updated spreadsheet class axiom, not as a simple removal.

### Feature-of-interest input mappings apparently rejected by spreadsheet

- `sosa:hasFeatureOfInterest`
  - TTL-only: `rdfs:subPropertyOf cco:has_input`.
  - Spreadsheet-only: domain and range axioms.
  - Spreadsheet reasoning states that `sosa:hasFeatureOfInterest` is intentionally left standalone rather than mapped to `cco:has_input`.
  - Follow-up: likely TTL-removal candidate.

- `sosa:isFeatureOfInterestOf`
  - TTL-only: `rdfs:subPropertyOf cco:is_input_of`.
  - Spreadsheet-only: `owl:inverseOf sosa:hasFeatureOfInterest`.
  - Follow-up: review together with `sosa:hasFeatureOfInterest`; likely TTL-removal candidate if the standalone feature-of-interest policy is accepted.

### Sample relationship property-chain divergence

- `sosa:hasSample`
  - TTL-only: `owl:propertyChainAxiom`.
  - Spreadsheet-only: domain and range axioms.
  - Follow-up: defer for sample-as-representation modeling review.

- `sosa:isSampleOf`
  - TTL-only: `owl:propertyChainAxiom`.
  - Spreadsheet-only: `owl:inverseOf sosa:hasSample`.
  - Follow-up: defer for sample-as-representation modeling review.

### Inverse-side direct mapping divergence

The following rows have direct TTL subproperty mappings, while the spreadsheet currently records inverse-property axioms:

- `ssn:hasDeployment`
- `ssn:inDeployment`
- `sosa:isActedOnBy`
- `sosa:isResultOf`
- `sosa:madeByActuator`
- `sosa:madeObservation`
- `sosa:madeSampling`

Follow-up: make a policy decision before editing. The options are:

1. keep the TTL limited to spreadsheet-canonical asserted axioms, in which case these direct inverse-side subproperty assertions should be removed or replaced with the spreadsheet inverse axioms; or
2. allow explicit inverse-derived closure in the TTL, in which case the spreadsheet should explicitly document that policy.

## Recommended implementation order

Do not mechanically apply all 13 items.

Recommended sequence:

1. Create a narrow TTL-removal PR for the feature-of-interest input mappings.
2. Separately review and update the `sosa:Sampler` and `sosa:Sensor` class mappings.
3. Make a repository policy decision about inverse-derived direct mappings.
4. Defer `sosa:hasSample` and `sosa:isSampleOf` property-chain assertions until the sample representation model is settled.
