# HermiT Canary: `ssn:hasOutput` Reactivation

## Scope

This report evaluates, in temporary HermiT graphs only, whether reactivating the deferred direct property mapping:

```ttl
<http://www.w3.org/ns/ssn/hasOutput> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001986> .
```

would preserve the current HermiT-clean M2 baseline.

This is a report-only canary. It does not reactivate the mapping in `SSN2BFO.ttl` and does not modify the spreadsheet.

Context reports:

- `reports/deferred-mapping-reactivation-plan.md`
- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/hermit-input-output-deferral-evaluation.md`
- `reports/hermit-input-output-mapping-evaluation.md`
- `reports/hermit-hasInput-reactivation-canary.md`
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

## Prior `hasInput` Canary

`reports/hermit-hasInput-reactivation-canary.md` found:

| Check | Result |
| --- | --- |
| baseline | clean |
| `hasInput` canary return code | 1 |
| `hasInput` canary unsat count | 1 |
| `hasInput` canary unsat set | `ssn:Input` |

Therefore, `ssn:hasInput -> cco:ont00001921` remains deferred.

## Candidate Reactivation

The exact candidate triple tested was:

```ttl
<http://www.w3.org/ns/ssn/hasOutput> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001986> .
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
| A baseline | `/tmp/ssn-to-bfo-hermit-hasOutput-reactivation-canary/A_baseline.ttl` | no | 15474 | 0 | yes | 0 | 0 | clean | no |
| B canary | `/tmp/ssn-to-bfo-hermit-hasOutput-reactivation-canary/B_canary_reactivate_hasOutput.ttl` | yes | 15475 | 1 | no | n/a | 1 | `ssn:Output` | no |

Variant A confirms the current clean baseline. Variant B reintroduces exactly one unsatisfiable class:

```text
ssn:Output
```

No sample simplicity blocker reappeared in either variant.

## Interpretation

The canary is not HermiT-clean. Reactivating:

```ttl
<http://www.w3.org/ns/ssn/hasOutput> rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001986> .
```

from the clean baseline reintroduces `ssn:Output` as an unsatisfiable class.

This is consistent with the earlier Input/Output diagnostic and deferral reports:

- `reports/hermit-input-output-mapping-evaluation.md` found that removing `ssn:hasOutput` removes `ssn:Output`;
- `reports/hermit-input-output-deferral-evaluation.md` found that deferring `ssn:hasInput` and `ssn:hasOutput` removed the Input/Output pair from the full M2 unsat set;
- `reports/hermit-hasInput-reactivation-canary.md` found that reactivating the parallel `ssn:hasInput` mapping reintroduced `ssn:Input`;
- the issue was characterized as a mixed interaction involving source restrictions around `Procedure`, `Input`, `Output`, `hasInput`, and `hasOutput`, active input/output property mappings, and the `sosa:Procedure` class-expression mapping context.

This result does not prove that the intended `ssn:hasOutput` semantics are invalid. It shows that the direct OWL `rdfs:subPropertyOf cco:ont00001986` representation is not HermiT-safe in the current merged full-OWL profile.

## Recommendation

Keep `ssn:hasOutput -> cco:ont00001986` deferred for now.

Because both individual Input/Output canaries failed, both direct property mappings should remain deferred unless a new HermiT-safe OWL representation or rule/COMS architecture is proposed:

- `ssn:hasInput -> cco:ont00001921`
- `ssn:hasOutput -> cco:ont00001986`

## Suggested Next Branch

Recommended next branch:

```text
review/summarize-input-output-reactivation-results
```

That branch should summarize the paired Input/Output canary outcomes and recommend whether the next deferred area should move to `sosa:observedProperty` or another candidate from the reactivation plan.
