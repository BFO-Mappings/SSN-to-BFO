# HermiT Canary: `sosa:observedProperty` Reactivation

## Scope

This report evaluates, in temporary HermiT graphs only, whether reactivating the deferred direct property mapping:

```ttl
<http://www.w3.org/ns/sosa/observedProperty> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001921> .
```

would preserve the current HermiT-clean M2 baseline.

This is a report-only canary. It does not reactivate the mapping in `SSN2BFO.ttl` and does not modify the spreadsheet.

Context reports:

- `reports/deferred-mapping-reactivation-plan.md`
- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/hermit-observedProperty-deferral-evaluation.md`
- `reports/hermit-observation-sensor-stimulus-deferral-evaluation.md`
- `reports/input-output-reactivation-results.md`
- `reports/ssn-systems-dependence-reactivation-results.md`

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

The current M2 baseline is expected to be HermiT-clean with `owl:Nothing` count 0 and no unsatisfiable classes.

## Prior Deferral Evidence

`reports/hermit-observedProperty-deferral-evaluation.md` found:

| State | HermiT result |
| --- | --- |
| before deferral | 3 unsats: `sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus` |
| after deferral | HermiT-clean |

Therefore, `sosa:observedProperty -> cco:ont00001921` remains deferred in the repository.

## Candidate Reactivation

The exact candidate triple tested was:

```ttl
<http://www.w3.org/ns/sosa/observedProperty> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001921> .
```

The candidate was added only to the temporary Variant B graph. It remains deferred in the repository.

## HermiT M2 Before / After Canary

Both variants were built from:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Both variants applied the established cleanup conditions listed above.

HermiT command form:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

| Variant | Temporary graph | Candidate triple added | Triple count | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Unsat set | Sample simplicity blocker |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- | --- |
| A baseline | `/tmp/ssn-to-bfo-hermit-observedProperty-reactivation-canary/A_baseline.ttl` | no | 15474 | 0 | yes | 0 | 0 | clean | no |
| B canary | `/tmp/ssn-to-bfo-hermit-observedProperty-reactivation-canary/B_canary_reactivate_observedProperty.ttl` | yes | 15475 | 1 | no | n/a | 3 | `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus` | no |

Variant A confirms the current clean baseline. Variant B reintroduces the Observation / Sensor / Stimulus HermiT cluster:

```text
sosa:Sensor
sosa:Observation
ssn:Stimulus
```

No sample simplicity blocker reappeared in either variant.

## Interpretation

The canary is not HermiT-clean. Reactivating:

```ttl
<http://www.w3.org/ns/sosa/observedProperty> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001921> .
```

from the clean baseline reintroduces the three-class Observation / Sensor / Stimulus cluster.

This is consistent with the earlier Observation / Sensor / Stimulus diagnostics:

- `reports/hermit-observation-sensor-stimulus-deferral-evaluation.md` identified `sosa:observedProperty` as a narrow one-triple reducer for the final trio;
- `reports/hermit-observedProperty-deferral-evaluation.md` found that deferring only this direct property mapping made the full M2 graph HermiT-clean;
- the deferral evidence did not prove the mapping semantically wrong, but it did show that this direct OWL representation is a high-impact HermiT interaction point.

This canary likewise does not prove that the intended `sosa:observedProperty` semantics are invalid. It shows that the direct OWL `rdfs:subPropertyOf cco:ont00001921` representation is not HermiT-safe in the current merged full-OWL profile.

## Recommendation

Keep `sosa:observedProperty -> cco:ont00001921` deferred for now.

Future work should avoid reactivating this direct property mapping unless a new HermiT-safe OWL representation or rule/COMS architecture is proposed and tested first in temporary HermiT graphs.

## Suggested Next Branch

Recommended next branch:

```text
review/summarize-deferred-reactivation-results
```

That branch should summarize the failed reactivation canaries for:

- the three SSN Systems dependence mappings to `bfo:BFO_0000194`;
- `ssn:hasInput -> cco:ont00001921`;
- `ssn:hasOutput -> cco:ont00001986`;
- `sosa:observedProperty -> cco:ont00001921`.
