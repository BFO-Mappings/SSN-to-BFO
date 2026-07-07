# HermiT Canary: `ssn-system:hasSurvivalProperty` Reactivation

## Scope

This is a report-only canary evaluation for reactivating exactly one currently deferred mapping:

```ttl
<http://www.w3.org/ns/ssn/systems/hasSurvivalProperty> rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
```

No repo ontology file, spreadsheet file, import, example, existing report, tool, generated artifact, release artifact, or mapping file was edited. The candidate triple was added only to a temporary HermiT graph.

Context reports:

- `reports/deferred-mapping-reactivation-plan.md`
- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/hermit-hasOperatingProperty-reactivation-canary.md`
- `reports/hermit-survival-property-source-restriction-explanation.md`
- `reports/hermit-survival-property-minimal-conflict-extraction.md`
- `reports/hermit-survival-range-deferral-evaluation.md`

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

The active repo state still defers `ssn-system:hasSurvivalProperty` in `SSN2BFO.ttl`:

```text
SSN2BFO.ttl lines 191-192
```

The corresponding workbook row is:

```text
Current_SOSA-SSN to BFO-CCO.xlsx
System Capability row 11
```

That row preserves the intended semantics: if survival range `x` has survival property `y`, then `y` specifically depends on `x`.

The immediately prior canary, `reports/hermit-hasOperatingProperty-reactivation-canary.md`, found that reactivating `ssn-system:hasOperatingProperty -> bfo:BFO_0000194` was not HermiT-safe. That canary reintroduced:

```text
ssn-system:OperatingProperty
ssn-system:OperatingPowerRange
ssn-system:MaintenanceSchedule
```

## Candidate Reactivation

Candidate tested in the temporary graph only:

```ttl
<http://www.w3.org/ns/ssn/systems/hasSurvivalProperty> rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
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
| A baseline | `/tmp/ssn-to-bfo-hermit-hasSurvivalProperty-reactivation-canary/A_baseline.ttl` | no | 15474 | 0 | yes | 0 | 0 | clean | no |
| B canary | `/tmp/ssn-to-bfo-hermit-hasSurvivalProperty-reactivation-canary/B_canary_reactivate_hasSurvivalProperty.ttl` | yes | 15475 | 1 | no | n/a | 3 | `ssn-system:BatteryLifetime`, `ssn-system:SystemLifetime`, `ssn-system:SurvivalProperty` | no |

The canary reactivation does not preserve HermiT cleanliness.

## Interpretation

Adding only:

```ttl
<http://www.w3.org/ns/ssn/systems/hasSurvivalProperty> rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
```

to the current clean M2 baseline reintroduces the same SSN Systems survival trio that earlier SurvivalProperty diagnostics isolated:

```text
ssn-system:BatteryLifetime
ssn-system:SystemLifetime
ssn-system:SurvivalProperty
```

This means the mapping should remain deferred for now.

This does not prove that the intended `hasSurvivalProperty` semantics are invalid. It only shows that the direct OWL `rdfs:subPropertyOf bfo:BFO_0000194` representation is not HermiT-safe in the current merged full-OWL profile.

Prior survival-property diagnostics showed that this area is entangled with:

- `BatteryLifetime` and `SystemLifetime` as source subclasses of `SurvivalProperty`;
- source restrictions around `hasSurvivalProperty`;
- the broader `SurvivalProperty` / `SurvivalRange` context;
- active SSN Systems class mapping context.

The intended semantics should continue to be documented and considered for HermiT-safe OWL redesign or rule/COMS treatment.

## Recommendation

Do not create a mapping-change branch to reactivate `ssn-system:hasSurvivalProperty -> bfo:BFO_0000194` at this time.

Because this is the second SSN Systems dependence canary to fail, the next step should be the next planned canary rather than a redundant failure-documentation branch.

Recommended next branch:

```text
review/evaluate-reactivate-hasSystemProperty-canary
```

That branch should test only:

```ttl
<http://www.w3.org/ns/ssn/systems/hasSystemProperty> rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
```

in a temporary graph against the same HermiT-clean baseline.
