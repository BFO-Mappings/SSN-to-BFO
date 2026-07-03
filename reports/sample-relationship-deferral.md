# Sample Relationship Mapping Deferral

This note records the disposition of the remaining `Sample Relationship` mapping rows.

No TTL, spreadsheet, tool, or generated audit files are changed by this note.

## Current audit rows

The remaining `Sample Relationship` audit rows involve:

- `sampling:RelationshipNature`
- `sampling:SampleRelationship`
- restrictions involving `sampling:relatedSample`
- restrictions involving `sampling:natureOfRelationship`

## Review

These rows should not be treated as ordinary missing TTL mappings.

The sample relationship material appears to represent relation-like content through classes and class restrictions. In other words, the model seems to treat sample-to-sample relationship information as class-modeled structures rather than as ordinary object-property mappings.

That makes the BFO/CCO alignment non-mechanical. A direct patch to `SSN2BFO.ttl` could easily overcommit to an incorrect treatment of these entities as either relations, relational qualities, information artifacts, processes, or some other BFO/CCO category.

## Decision

Defer the `Sample Relationship` mappings.

These mappings still need to be completed, but they require a separate modeling pass focused on how SOSA's sample relationship pattern should be represented in BFO/CCO.

## Audit treatment

The remaining `Sample Relationship` audit rows are retained as known deferred substantive mapping issues.

They should not be interpreted as accidental omissions from the direct spreadsheet/TTL reconciliation cleanup.
