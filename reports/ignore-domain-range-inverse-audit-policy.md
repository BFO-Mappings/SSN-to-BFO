# Ignore Domain, Range, and Inverse Assertions in Mapping Audit

This note records an audit-policy decision for `tools/compare_mappings.py`.

No TTL, spreadsheet, or tool changes are made by this note.

## Decision

The mapping consistency audit should ignore schema/context axioms when computing mapping reconciliation issues.

Ignored assertion types should include:

- `rdfs:domain`
- `rdfs:range`
- `schema:domainIncludes`
- `schema:rangeIncludes`
- `owl:inverseOf`

These assertions may remain in the spreadsheet `OWL Axiom` cells as documentation, schema context, or lightweight SOSA/SSN axiomatization, but they should not generate `missing_in_ttl`, `missing_in_spreadsheet`, `relation_mismatch`, or `target_mismatch` findings.

## Rationale

The audit is intended to reconcile source-to-target mapping assertions between `SSN2BFO.ttl` and `Current_SOSA-SSN to BFO-CCO.xlsx`.

Domain, range, domainIncludes, rangeIncludes, and inverseOf axioms do not by themselves assert a BFO/CCO mapping target. They describe schema constraints, relation metadata, or relation pairing.

Counting them as required mapping assertions creates noise in the audit and makes the remaining issue counts misleading.

## Consequence

A future tool update should restrict comparison to substantive mapping predicates such as:

- `rdfs:subClassOf`
- `owl:equivalentClass`
- `rdfs:subPropertyOf`
- `owl:propertyChainAxiom`

and should exclude domain/range/inverse-style predicates from expected spreadsheet assertions and TTL candidate mapping assertions.

## Follow-up

After the audit tool is updated, rerun the mapping comparison and then resume the sample property-chain spreadsheet PR.
