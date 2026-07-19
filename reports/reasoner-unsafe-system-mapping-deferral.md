# Reasoner-Unsafe Mapping Deferral

This note records the deferral of mappings found to be unsafe under ELK reasoner testing.

## Deferred mappings

The following mappings are deferred:

- `ssn:hasProperty`
- `ssn-system:BatteryLifetime`
- `ssn-system:MeasurementRange`

## Reasoner findings

ELK diagnostics showed that:

- the prior `ssn:hasProperty` dual mapping to `bfo:bearer_of` and `bfo:has_occurrent_part` made `ssn:hasProperty` unsatisfiable;
- the prior `ssn-system:BatteryLifetime` class mapping block made `ssn-system:BatteryLifetime` unsatisfiable;
- the prior `ssn-system:MeasurementRange` class mapping block made `ssn-system:MeasurementRange` unsatisfiable.

The failures are mapping-induced or mapping-amplified, not failures of the example instance data.

## Decision

Do not include these mappings in the current reasoner-testable mapping file.

These mappings require a separate modeling review before reintroduction.

## Rationale

The `ssn:hasProperty` mapping attempted to place a single SOSA/SSN property under two BFO relations with different domain/range behavior. This is too strong for reasoner-safe OWL alignment.

The `BatteryLifetime` and `MeasurementRange` mappings used large class expressions that became unsatisfiable when combined with SSN Systems and CCO/BFO constraints. These should be redesigned as reasoner-safe mappings rather than retained as direct class blocks.

## Audit treatment

The corresponding spreadsheet `OWL Axiom` cells are cleared so the mappings are not treated as active TTL omissions.

The spreadsheet reasoning cells retain the reasoner-safety rationale.

## Post-deferral reasoner result

After these mappings were deferred, ELK produced a reasoned output for the current merged mapping profile with no entities typed `owl:Nothing`.

A separate HermiT diagnostic still reported broader full-OWL unsatisfiability. HermiT/full OWL DL support remains a separate modeling/profile-review task and is not claimed as resolved by this deferral.
