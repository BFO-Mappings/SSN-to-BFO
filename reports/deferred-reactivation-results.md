# Deferred Reactivation Results

## Scope

This report summarizes the failed individual HermiT canaries for reactivating currently deferred direct OWL property mappings.

Controlling inputs:

- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/deferred-mapping-reactivation-plan.md`
- `reports/ssn-systems-dependence-reactivation-results.md`
- `reports/input-output-reactivation-results.md`
- `reports/hermit-observedProperty-reactivation-canary.md`
- `reports/hermit-observedProperty-deferral-evaluation.md`

This is a report-only summary. It does not reactivate any mapping and does not modify ontology or spreadsheet files.

## Current Stable Baseline

The current stable baseline remains:

| Check | Result |
| --- | --- |
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 71 |
| audit issues | 2 expected `sosa:Sensor` version-alignment issues only |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 77 |
| property-chain expectations | 5 |
| restriction expectations | 2 |
| active direct mappings not covered | 0 |
| active property-chain mappings not covered | 0 |
| active restriction mappings not covered | 0 |
| HermiT M2 baseline | clean under established cleanup conditions |

The established HermiT M2 cleanup conditions are:

- merge `imports/cco.ttl`, `imports/ssn.ttl`, `imports/ssn-systems.ttl`, and `SSN2BFO.ttl`;
- remove all `owl:imports` triples;
- remove `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- remove `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Under those conditions, the current M2 baseline is HermiT-clean with `owl:Nothing` count 0 and no reported unsatisfiable classes.

## Reactivation Canaries Tested

Each canary started from the current clean M2 baseline and added exactly one deferred direct property mapping in a temporary graph only.

| Candidate reactivation | Result | Unsatisfiable classes reintroduced |
| --- | --- | --- |
| `ssn-system:hasOperatingProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:OperatingProperty`, `ssn-system:OperatingPowerRange`, `ssn-system:MaintenanceSchedule` |
| `ssn-system:hasSurvivalProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:BatteryLifetime`, `ssn-system:SystemLifetime`, `ssn-system:SurvivalProperty` |
| `ssn-system:hasSystemProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:Latency`, `ssn-system:Accuracy`, `ssn-system:Precision`, `ssn-system:Sensitivity`, `ssn-system:SystemProperty`, `ssn-system:ResponseTime`, `ssn-system:Resolution`, `ssn-system:Selectivity`, `ssn-system:MeasurementRange`, `ssn-system:Frequency`, `ssn-system:DetectionLimit`, `ssn-system:ActuationRange`, `ssn-system:Drift` |
| `ssn:hasInput -> cco:ont00001921` | not HermiT-clean | `ssn:Input` |
| `ssn:hasOutput -> cco:ont00001986` | not HermiT-clean | `ssn:Output` |
| `sosa:observedProperty -> cco:ont00001921` | not HermiT-clean | `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus` |

## Interpretation

All individual reactivation canaries for the currently deferred direct OWL property mappings failed.

Therefore, the old direct `rdfs:subPropertyOf` representations should remain deferred:

```ttl
ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn:hasInput rdfs:subPropertyOf cco:ont00001921 .
ssn:hasOutput rdfs:subPropertyOf cco:ont00001986 .
sosa:observedProperty rdfs:subPropertyOf cco:ont00001921 .
```

This does not prove that the intended semantics are invalid. It shows that these direct OWL representations are not HermiT-safe in the current merged full-OWL profile.

The tested direct mappings covered three distinct families:

- SSN Systems dependence-style mappings to `bfo:BFO_0000194`;
- Input/Output mappings to CCO input/output properties;
- `sosa:observedProperty` as a narrow reducer for the Observation / Sensor / Stimulus cluster.

Because all individual reactivation canaries failed, future work should move from reactivation testing to replacement-design testing.

## Recommendation

Preserve the current HermiT-clean M2 baseline.

Do not reactivate any of the failed direct-property mappings without a new representation. A future branch should test candidate replacements in temporary graphs before editing `SSN2BFO.ttl` or the spreadsheet.

Replacement-design work should be separated by family:

1. SSN Systems dependence mappings.
2. Input/Output mappings.
3. `sosa:observedProperty`.

This separation keeps the modeling questions small enough to evaluate without mixing independent HermiT interaction clusters.

## Next Substantive Branch

Recommended next branch:

```text
review/design-hermit-safe-ssn-systems-dependence-representation
```

That branch should compare HermiT-safe alternatives for the intended dependence semantics of:

```text
ssn-system:hasOperatingProperty
ssn-system:hasSurvivalProperty
ssn-system:hasSystemProperty
```

It should not directly reactivate the old `rdfs:subPropertyOf bfo:BFO_0000194` mappings. Candidate representations should be tested first in temporary HermiT graphs, with the current clean M2 baseline used as the regression point.
