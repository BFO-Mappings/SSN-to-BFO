# Sampler / Sensor Class Mapping Reconciliation Review

This note reviews the current `sosa:Sampler` and `sosa:Sensor` class-mapping discrepancies between `SSN2BFO.ttl` and `Current_SOSA-SSN to BFO-CCO.xlsx`.

No TTL or spreadsheet changes are made by this note.

## Current audit pattern

Both rows show paired discrepancies:

- a TTL-only `rdfs:subClassOf` assertion; and
- a spreadsheet-only `owl:equivalentClass` assertion.

This indicates that the issue is not a simple extra TTL assertion. It is a possible replacement of older TTL class restrictions with newer spreadsheet class equivalence mappings.

## `sosa:Sampler`

Current TTL:

- `sosa:Sampler rdfs:subClassOf ...`
- includes `bfo:MaterialEntity`;
- includes `bfo:bearer_of some (bfo:RealizableEntity and (bfo:BFO_0000054 some sosa:Sampling))`;
- includes `cco:agent_in some sosa:Sampling`.

Current spreadsheet:

- `equivalentTo bfo:MaterialEntity and ...`
- uses `bfo:RealizableEntity and (bfo:realizes some sosa:Sampling)`;
- includes `cco:agent_in some sosa:Sampling`.

Review finding:

The spreadsheet `OWL Axiom` appears to use the wrong BFO relation direction for the realizable entity. A realizable entity is realized in a process. The spreadsheet reasoning also says the sampler bears a realizable entity "realized in a sampling process." That reasoning aligns with `BFO_0000054`, not `BFO_0000055`.

Recommended follow-up:

Do not update the TTL to the spreadsheet Sampler axiom as written. First review whether the spreadsheet `OWL Axiom` should be corrected from `bfo:realizes some sosa:Sampling` to the appropriate realized-in relation. After that, separately decide whether the mapping should remain `subClassOf` or become `equivalentTo`.

## `sosa:Sensor`

Current TTL:

- `sosa:Sensor rdfs:subClassOf ...`
- includes `bfo:MaterialEntity`;
- includes `bfo:bearer_of some (bfo:RealizableEntity and (bfo:BFO_0000054 some sosa:Observation))`;
- includes `cco:agent_in some sosa:Observation`.

Current spreadsheet:

- `equivalentTo cco:Sensor`;
- the spreadsheet reasoning states that this was updated from `subClassOf` to `equivalentTo` to align with the latest CCO `Sensor` class.

Review finding:

This is a substantive modeling change rather than a mechanical audit cleanup. The current TTL preserves SOSA-specific observation/agent restrictions. The spreadsheet instead maps `sosa:Sensor` directly to `cco:Sensor`.

Recommended follow-up:

Review the local imported CCO definition of `cco:Sensor` before changing the TTL. If `cco:Sensor` is accepted as extensionally equivalent to `sosa:Sensor`, then replace the old TTL subclass expression with the spreadsheet equivalent-class mapping. If not, retain a more specific SOSA restriction or document why the spreadsheet equivalence is too strong.

## Local CCO evidence checked

After this review note was opened, local `imports/cco.ttl` was inspected.

For the Sampler issue, the local import confirms that:

- `BFO_0000054` is inverse of `BFO_0000055`;
- `BFO_0000054` has the alternate label `realized in`;
- `BFO_0000055` is labeled `realizes`;
- `BFO_0000055` has process-to-realizable-entity direction.

This supports the concern that the spreadsheet Sampler `OWL Axiom` uses the wrong relation direction when it says a `bfo:RealizableEntity` `bfo:realizes` some `sosa:Sampling`.

For the Sensor issue, the local import shows `cco:ont00000569` as `Sensor`, subclassed under `cco:ont00000736`, with a definition of a transducer designed to convert incoming energy into an output signal corresponding to changes in that energy. The inspected local import did not show `cco:Sensor` as an explicit equivalent class expression to a material entity bearing a `Sensor Function` or `Sensor Role`.

This makes the spreadsheet Sensor equivalence claim stronger than what is directly visible in the local CCO import. Do not replace the TTL `sosa:Sensor` subclass expression with `equivalentTo cco:Sensor` until the intended CCO semantics are confirmed from the governing CCO source or an explicit project decision is recorded.

## Recommended implementation sequence

1. Create a spreadsheet-review or spreadsheet-fix PR for the apparent Sampler relation-direction issue, if confirmed.
2. Separately decide whether `sosa:Sampler` should be `equivalentTo` or only `subClassOf` the material-entity / bearer / agent-in expression.
3. Review the imported CCO `Sensor` definition.
4. Only after those decisions, create a TTL implementation PR for `sosa:Sampler` and/or `sosa:Sensor`.
