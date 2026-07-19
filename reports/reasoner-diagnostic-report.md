# Reasoner Diagnostic Report

This report records the reasoner diagnostics performed after instance-data smoke testing.

## Scope

The diagnostics used temporary no-imports merged files under `/tmp/ssn-to-bfo-reasoner-test`.

The tests were not committed as generated ontology artifacts.

## Initial reasoner findings

The initial ROBOT/ELK reasoner test over the merged imports and `SSN2BFO.ttl` reported two unsatisfiable classes:

- `ssn-system:BatteryLifetime`
- `ssn-system:MeasurementRange`

Additional isolation showed that these unsatisfiabilities were mapping-induced or mapping-amplified rather than failures of the example instance data.

A further diagnostic showed that after removing the direct `BatteryLifetime` and `MeasurementRange` mapping blocks, the remaining unsatisfiable-property behavior was driven by the `ssn:hasProperty` dual mapping.

## Deferred mappings

The following mappings were deferred to establish a reasoner-testable baseline:

- `ssn:hasProperty`
- `ssn-system:BatteryLifetime`
- `ssn-system:MeasurementRange`

## ELK result after deferral

After deferring those mappings and creating a temporary no-imports merged file, ELK produced a reasoned output.

The reasoned output contained:

- entities typed `owl:Nothing`: 0

This establishes an ELK-clean baseline for the current mapping file.

## HermiT result

A HermiT diagnostic was also run using a temporary reasoner-profile file that removed the SSN `hasSample` inverse-functional simplicity blocker.

HermiT still reported broader full-OWL unsatisfiability, including classes such as:

- `sosa:Observation`
- `sosa:Sensor`
- `ssn:Input`
- `ssn:Output`
- `ssn:Stimulus`
- multiple `ssn-system:*` classes

This means HermiT/full OWL DL reasoning is not yet clean.

## Interpretation

The current PR establishes an ELK-clean reasoner-testable baseline after deferring the three identified unsafe mappings.

It does not claim that the full merged ontology is HermiT-clean.

HermiT/full OWL DL support should be handled as a separate reasoner-profile and modeling-hygiene task.
