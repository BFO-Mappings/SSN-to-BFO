# Sample Relationship Provisional Mapping Note

This note records the provisional implementation of the `Sample Relationship` mappings.

## Status

The `Sample Relationship` mappings have been implemented to support instance-data testing.

They remain provisional and require close review before being treated as release-quality or authoritative BFO/CCO mappings.

## Implemented rows

The implemented material covers:

- `sampling:RelationshipNature`
- `sampling:SampleRelationship`
- the `sampling:relatedSample` restriction
- the `sampling:natureOfRelationship` restriction

## Modeling rationale

The SOSA sample-relationship pattern appears to represent relation-like content through classes and class restrictions.

For testing, `sampling:SampleRelationship` is treated as a reified descriptive/information-content structure about a relationship involving samples, and `sampling:RelationshipNature` is treated as descriptive/information content identifying the nature of that relationship.

The class restrictions are retained as SOSA structural constraints needed for instance-data testing.

## Close-review warning

This implementation should receive close modeling review.

A later BFO/CCO treatment may need to revise these mappings if the sample-relationship pattern is better analyzed as a relation, relational quality, information artifact, process-mediated structure, or some other BFO/CCO pattern.
