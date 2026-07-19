# Remaining Missing-in-TTL Review

This note classifies the remaining `missing_in_ttl` assertions after the domain/range/inverse audit-policy update, sample property-chain documentation, and inverse-side direct mapping documentation.

No TTL or spreadsheet changes are made by this note.

## Current audit status

The current audit reports:

- `missing_in_ttl`: 15
- `missing_in_spreadsheet`: 1
- `relation_mismatch`: 0
- `target_mismatch`: 0

The one remaining `missing_in_spreadsheet` issue is the deferred `sosa:Sensor` upcoming-CCO version issue.

This note concerns the 15 `missing_in_ttl` issues.

## Classification

### A. Correct datatype-property placeholder rows — no action

- `sosa:hasSimpleResult rdfs:subPropertyOf owl:topDataProperty`
- `sosa:resultTime rdfs:subPropertyOf owl:topDataProperty`

Decision:

No TTL action is needed.

These rows are correct as spreadsheet datatype-property placeholders. They do not need to be implemented in `SSN2BFO.ttl` as BFO/CCO mapping assertions.

### B. Sample Relationship rows — no mapping action

- `sampling:RelationshipNature rdfs:subClassOf cco:ont00000958`
- `sampling:SampleRelationship rdfs:subClassOf cco:ont00000958`
- `sampling:SampleRelationship rdfs:subClassOf` restriction on `sampling:relatedSample`
- `sampling:SampleRelationship rdfs:subClassOf` restriction on `sampling:natureOfRelationship`

Decision:

No TTL action is needed.

These rows are not part of the current mapping reconciliation target. They should not be treated as required `SSN2BFO.ttl` mapping additions.

### C. Straightforward object-property mapping candidates

- `ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000196`
- `ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000117`
- `ssn:hasSubSystem rdfs:subPropertyOf bfo:BFO_0000178`
- `sosa:observes rdfs:subPropertyOf bfo:BFO_0000057`
- `sosa:usedProcedure rdfs:subPropertyOf cco:ont00001920`

Review finding:

These appear to be direct spreadsheet-governed object-property mappings. They are candidates for narrow TTL implementation PRs, subject to ordinary modeling review.

Recommended follow-up:

Review each row’s spreadsheet reasoning before applying. If accepted, implement in small TTL-only PRs.

### D. Complex property-chain / parser-sensitive mappings

- `sosa:hosts`, parsed as two `rdfs:subPropertyOf` expected assertions involving BFO relations, object-property structure, inverse, and property-chain content.
- `ssn:implementedBy`, parsed as a `rdfs:subPropertyOf` expected assertion involving inverse and property-chain content.

Review finding:

These are not straightforward single-triple mappings. The audit summaries include structural OWL tokens such as `owl:ObjectProperty`, `owl:inverseOf`, and `owl:propertyChainAxiom`, which means these rows need manual inspection before implementation.

Recommended follow-up:

Do not mechanically add these from the audit summary. Inspect the full spreadsheet `OWL Axiom` cells and decide whether they should become TTL property-chain axioms, be simplified, or be excluded from the audit comparison.

### E. Deferred version-targeted issue

- `sosa:Sensor owl:equivalentClass cco:Sensor`

Review finding:

This is already documented as an upcoming-CCO version-target issue.

Recommended follow-up:

Do not resolve against the current imported CCO version.

## Recommended implementation order

1. Take no TTL action for the datatype-property placeholder rows.
2. Take no TTL action for the Sample Relationship rows.
3. Handle straightforward object-property mappings in small TTL-only PRs, after row-level modeling review.
4. Review complex `sosa:hosts` and `ssn:implementedBy` property-chain rows manually before making any TTL changes.
5. Leave `sosa:Sensor` deferred until the appropriate CCO version is available or a next-version mapping track is created.
