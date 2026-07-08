# Input/Output CCO Mapping Rationale Cleanup

## Scope

This report documents a narrow rationale cleanup for the former CCO direct property mapping candidates for `ssn:hasInput` and `ssn:hasOutput`.

No ontology logic was added. No source-level domain/range axioms, SWRL rules, SPARQL rules, or COMS rule artifacts were added.

## Provenance

Before commit `8e12261`, workbook `Common OPs` rows 9 and 10 had active CCO mapping cells:

- `ssn:hasInput` was mapped to `subPropertyOf cco:has_input`.
- `ssn:hasOutput` was mapped to `subPropertyOf cco:has_output`.

Commit `8e12261` cleared the active OWL mapping cells `E9` and `E10` and introduced temporary deferral rationale language for those mappings.

The `D9` and `D10` language describing the relations as being in the same sense as CCO `hasInput`/`hasOutput` predated commit `8e12261`.

## Current Decision

The old direct CCO property mappings are removed/rejected as intended mappings.

`ssn:hasInput` and `ssn:hasOutput` remain source SSN relations between procedures and their inputs or outputs.

No active CCO property mapping is asserted for either relation.

## TTL Comment Changes

In `SSN2BFO.ttl`, only non-logical comments were updated.

| Source term | Previous comment | New comment |
| --- | --- | --- |
| `ssn:hasInput` | `Direct OWL property mapping deferred pending HermiT-safe rule/COMS treatment.` | `Prior direct CCO property mapping removed; no active CCO mapping is asserted.` |
| `ssn:hasOutput` | `Direct OWL property mapping deferred pending HermiT-safe rule/COMS treatment.` | `Prior direct CCO property mapping removed; no active CCO mapping is asserted.` |

No `rdfs:subPropertyOf` assertion was added for `ssn:hasInput` or `ssn:hasOutput`.

## Workbook Changes

Only `Current_SOSA-SSN to BFO-CCO.xlsx`, sheet `Common OPs`, rows 9 and 10 were updated.

| Cell | New value |
| --- | --- |
| `D9` | `If a procedure hasInput y, then y is an input to that procedure.` |
| `E9` | empty |
| `F9` | `Prior direct CCO mapping to cco:has_input is removed/rejected. The source relation is retained as an SSN relation between a Procedure and its Input; no active CCO property mapping is asserted.` |
| `D10` | `If a procedure hasOutput y, then y is an output of that procedure.` |
| `E10` | empty |
| `F10` | `Prior direct CCO mapping to cco:has_output is removed/rejected. The source relation is retained as an SSN relation between a Procedure and its Output; no active CCO property mapping is asserted.` |

Cells `A9`, `B9`, `C9`, `A10`, `B10`, and `C10` were left unchanged.

## Validation Expectations

Because this cleanup changes only TTL comments and workbook rationale/non-mapping cells:

- Logical mapping counts should remain unchanged.
- The mapping audit should remain at only the two expected `sosa:Sensor` version-alignment issues.
- The HermiT-clean baseline should be unaffected.
