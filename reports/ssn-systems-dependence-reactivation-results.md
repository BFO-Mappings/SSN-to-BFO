# SSN Systems Dependence Reactivation Results

## Scope

This report summarizes the three individual HermiT canary evaluations for reactivating deferred SSN Systems dependence mappings to `bfo:BFO_0000194` / specifically depended on by.

Controlling inputs:

- `reports/hermit-hasOperatingProperty-reactivation-canary.md`
- `reports/hermit-hasSurvivalProperty-reactivation-canary.md`
- `reports/hermit-hasSystemProperty-reactivation-canary.md`
- `reports/deferred-mapping-reactivation-plan.md`
- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/hermit-hasProperty-domain-range-architecture.md`

This is a report-only summary. It does not reactivate any mapping and does not modify ontology or spreadsheet files.

## Current Baseline

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

## Canaries Tested

Each canary started from the current clean M2 baseline and added exactly one deferred `rdfs:subPropertyOf bfo:BFO_0000194` mapping in a temporary graph only.

| Candidate reactivation | Result | Unsatisfiable classes reintroduced |
| --- | --- | --- |
| `ssn-system:hasOperatingProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:OperatingProperty`, `ssn-system:OperatingPowerRange`, `ssn-system:MaintenanceSchedule` |
| `ssn-system:hasSurvivalProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:BatteryLifetime`, `ssn-system:SystemLifetime`, `ssn-system:SurvivalProperty` |
| `ssn-system:hasSystemProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:Latency`, `ssn-system:Accuracy`, `ssn-system:Precision`, `ssn-system:Sensitivity`, `ssn-system:SystemProperty`, `ssn-system:ResponseTime`, `ssn-system:Resolution`, `ssn-system:Selectivity`, `ssn-system:MeasurementRange`, `ssn-system:Frequency`, `ssn-system:DetectionLimit`, `ssn-system:ActuationRange`, `ssn-system:Drift` |

## Interpretation

All three individual SSN Systems dependence reactivation canaries failed. In each case, adding back the direct OWL representation:

```ttl
?source rdfs:subPropertyOf bfo:BFO_0000194 .
```

reintroduced HermiT unsatisfiable classes into the current merged full-OWL profile.

Therefore, the three direct OWL `rdfs:subPropertyOf bfo:BFO_0000194` representations should remain deferred for now:

- `ssn-system:hasOperatingProperty -> bfo:BFO_0000194`
- `ssn-system:hasSurvivalProperty -> bfo:BFO_0000194`
- `ssn-system:hasSystemProperty -> bfo:BFO_0000194`

This does not prove that the intended dependence semantics are invalid. The intended semantics remain:

- if operating range `x` has operating property `y`, then `y` specifically depends on `x`;
- if survival range `x` has survival property `y`, then `y` specifically depends on `x`;
- if system capability `x` has system property `y`, then `y` specifically depends on `x`.

The canaries show only that the direct OWL subproperty representation to `bfo:BFO_0000194` is not HermiT-safe in the current merged full-OWL profile. These intended semantics remain candidates for HermiT-safe OWL redesign or rule/COMS treatment.

## Recommendation

Keep the three SSN Systems dependence mappings deferred.

Do not test the three direct `bfo:BFO_0000194` mappings as a group unless a new representation is proposed. Each individual direct-property reactivation already failed from the clean baseline, so a grouped reactivation of the same direct representation would not be a useful next step.

Future work should focus on one of two paths:

- rule/COMS treatment for the intended dependence inference, keeping the active OWL profile clean;
- a redesigned OWL representation tested first in temporary HermiT graphs before any repo mapping change.

Future mapping work should preserve the current HermiT-clean M2 baseline.

## Next Deferred Mapping Area

The next canary area from `reports/deferred-mapping-reactivation-plan.md` should be:

```ttl
ssn:hasInput rdfs:subPropertyOf cco:ont00001921 .
```

Recommended next branch:

```text
review/evaluate-reactivate-hasInput-canary
```

That branch should remain report-only unless the temporary canary is HermiT-clean.
