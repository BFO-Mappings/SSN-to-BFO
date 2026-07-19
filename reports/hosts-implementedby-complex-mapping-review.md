# `sosa:hosts` and `ssn:implementedBy` Complex Mapping Review

This note reviews the remaining complex object-property mapping issues for `sosa:hosts` and `ssn:implementedBy`.

No TTL or spreadsheet changes are made by this note.

## Current inspection

### `sosa:hosts`

The spreadsheet row contains:

- `sosa:hosts owl:inverseOf sosa:isHostedBy`
- domain and range assertions
- a property-chain pattern for `sosa:hosts`
- a property-chain pattern for `sosa:isHostedBy`

The current TTL contains:

- `sosa:hosts rdf:type owl:ObjectProperty`

The audit policy already ignores inverse, domain, and range assertions. The remaining audit issues therefore come from the property-chain material.

### `ssn:implementedBy`

The spreadsheet row contains a property-chain pattern involving:

- inverse of `cco:prescribed_by`
- inverse of `cco:agent_in`

The spreadsheet reasoning states that if an entity implements a procedure, then there exists a process prescribed by that procedure in which the entity participates as an agent.

## Review

These rows should not be implemented as simple missing TTL subproperty assertions.

Both rows use property-chain material in the object position of `rdfs:subPropertyOf`, for example:

    some:property rdfs:subPropertyOf [
      owl:propertyChainAxiom ( ... )
    ] .

This is parser-sensitive and should not be treated as equivalent to a direct mapping such as:

    some:property rdfs:subPropertyOf bfo:some_relation .

OWL property chains normally define a property as a superproperty of a chain. They do not straightforwardly express that a named property is a subproperty of an anonymous property-chain expression in the way a simple audit comparison suggests.

## `sosa:hosts`

The spreadsheet reasoning treats hosting as role-mediated support realized in processes involving the hosted system.

That is a substantive modeling pattern, not a simple BFO/CCO relation replacement. It may require a named intermediate relation, a corrected property-chain direction, or a richer axiomatization.

Do not add the spreadsheet property-chain blank node to `SSN2BFO.ttl` mechanically.

## `ssn:implementedBy`

The spreadsheet reasoning treats implementation as involving a prescribed process in which the implementing entity participates as agent.

That is also a substantive existential/process-mediated pattern, not a simple direct subproperty mapping.

Do not add the spreadsheet property-chain blank node to `SSN2BFO.ttl` mechanically.

## Recommended follow-up

Treat the remaining audit issues for `sosa:hosts` and `ssn:implementedBy` as known complex modeling issues.

Before implementation, decide whether to:

1. revise the spreadsheet rows into valid asserted OWL property-chain axioms with the intended direction;
2. introduce named intermediate relations for the mediated patterns; or
3. mark these rows as explanatory/non-mechanical mappings outside the strict TTL reconciliation audit.

Until that decision is made, these rows should not be resolved by a TTL-only mechanical patch.
