# HermiT Canary: `ssn-system:hasSystemProperty` Reactivation

## Scope

This is a report-only canary evaluation for reactivating exactly one currently deferred mapping:

```ttl
<http://www.w3.org/ns/ssn/systems/hasSystemProperty> rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
```

No repo ontology file, spreadsheet file, import, example, existing report, tool, generated artifact, release artifact, or mapping file was edited. The candidate triple was added only to a temporary HermiT graph.

Context reports:

- `reports/deferred-mapping-reactivation-plan.md`
- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/hermit-hasOperatingProperty-reactivation-canary.md`
- `reports/hermit-hasSurvivalProperty-reactivation-canary.md`
- `reports/hermit-hasProperty-domain-range-architecture.md`

## Current Baseline

The current stable baseline is the cumulative HermiT-clean state after the merged deferrals.

| Baseline check | Current result |
| --- | ---: |
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 71 |
| audit issues | 2 |
| expected `sosa:Sensor` version-alignment issues | 2 |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 77 |
| property-chain expectations | 5 |
| restriction expectations | 2 |
| active direct mappings not covered | 0 |
| active property-chain mappings not covered | 0 |
| active restriction mappings not covered | 0 |
| HermiT M2 baseline | clean under established cleanup conditions |

The established HermiT M2 cleanup conditions are:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

The active repo state still defers `ssn-system:hasSystemProperty` in `SSN2BFO.ttl`:

```text
SSN2BFO.ttl lines 203-204
```

The corresponding workbook row is:

```text
Current_SOSA-SSN to BFO-CCO.xlsx
System Capability row 14
```

That row preserves the intended semantics: if system capability `x` has system property `y`, then `y` specifically depends on `x`.

The two immediately prior SSN Systems dependence canaries also failed:

| Prior canary | Candidate | Result |
| --- | --- | --- |
| `reports/hermit-hasOperatingProperty-reactivation-canary.md` | `ssn-system:hasOperatingProperty -> bfo:BFO_0000194` | not HermiT-clean; reintroduced `ssn-system:OperatingProperty`, `ssn-system:OperatingPowerRange`, `ssn-system:MaintenanceSchedule` |
| `reports/hermit-hasSurvivalProperty-reactivation-canary.md` | `ssn-system:hasSurvivalProperty -> bfo:BFO_0000194` | not HermiT-clean; reintroduced `ssn-system:BatteryLifetime`, `ssn-system:SystemLifetime`, `ssn-system:SurvivalProperty` |

## Candidate Reactivation

Candidate tested in the temporary graph only:

```ttl
<http://www.w3.org/ns/ssn/systems/hasSystemProperty> rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
```

This report did not reactivate the mapping in `SSN2BFO.ttl` or the spreadsheet.

## HermiT M2 Before / After Canary

Both variants were built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

For both variants, the temporary graph preparation removed:

```text
all owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty
sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

HermiT command shape:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

| Variant | Temporary graph | Candidate triple added? | Triple count | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Unsat set | Sample simplicity blocker |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- | --- |
| A baseline | `/tmp/ssn-to-bfo-hermit-hasSystemProperty-reactivation-canary/A_baseline.ttl` | no | 15474 | 0 | yes | 0 | 0 | clean | no |
| B canary | `/tmp/ssn-to-bfo-hermit-hasSystemProperty-reactivation-canary/B_canary_reactivate_hasSystemProperty.ttl` | yes | 15475 | 1 | no | n/a | 13 | `ssn-system:Latency`, `ssn-system:Accuracy`, `ssn-system:Precision`, `ssn-system:Sensitivity`, `ssn-system:SystemProperty`, `ssn-system:ResponseTime`, `ssn-system:Resolution`, `ssn-system:Selectivity`, `ssn-system:MeasurementRange`, `ssn-system:Frequency`, `ssn-system:DetectionLimit`, `ssn-system:ActuationRange`, `ssn-system:Drift` | no |

The canary reactivation does not preserve HermiT cleanliness.

## Interpretation

Adding only:

```ttl
<http://www.w3.org/ns/ssn/systems/hasSystemProperty> rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
```

to the current clean M2 baseline reintroduces 13 unsatisfiable SSN Systems classes:

```text
ssn-system:Latency
ssn-system:Accuracy
ssn-system:Precision
ssn-system:Sensitivity
ssn-system:SystemProperty
ssn-system:ResponseTime
ssn-system:Resolution
ssn-system:Selectivity
ssn-system:MeasurementRange
ssn-system:Frequency
ssn-system:DetectionLimit
ssn-system:ActuationRange
ssn-system:Drift
```

This means the mapping should remain deferred for now.

All three SSN Systems direct dependence mappings to `bfo:BFO_0000194` have now failed individual HermiT reactivation canaries:

```text
ssn-system:hasOperatingProperty -> bfo:BFO_0000194
ssn-system:hasSurvivalProperty -> bfo:BFO_0000194
ssn-system:hasSystemProperty -> bfo:BFO_0000194
```

This does not prove that the intended dependence semantics are invalid. It shows that direct OWL `rdfs:subPropertyOf bfo:BFO_0000194` representations are not HermiT-safe for these three mappings in the current merged full-OWL profile.

The intended dependence semantics should remain documented and should be treated as candidates for HermiT-safe OWL redesign or rule/COMS treatment.

## Recommendation

Do not create a mapping-change branch to reactivate `ssn-system:hasSystemProperty -> bfo:BFO_0000194` at this time.

Recommended next branch:

```text
review/summarize-ssn-systems-dependence-reactivation-results
```

That branch should summarize the three failed canaries together and recommend keeping the three selected SSN Systems direct dependence mappings deferred unless a new HermiT-safe OWL representation or rule/COMS architecture is proposed and tested in temporary graphs first.
