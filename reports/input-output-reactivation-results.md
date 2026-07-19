# Input/Output Reactivation Results

## Scope

This report summarizes the failed HermiT canary evaluations for reactivating the deferred direct Input/Output property mappings:

- `ssn:hasInput -> cco:ont00001921`
- `ssn:hasOutput -> cco:ont00001986`

Controlling inputs:

- `reports/hermit-hasInput-reactivation-canary.md`
- `reports/hermit-hasOutput-reactivation-canary.md`
- `reports/hermit-input-output-deferral-evaluation.md`
- `reports/hermit-input-output-mapping-evaluation.md`
- `reports/deferred-mapping-reactivation-plan.md`
- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/ssn-systems-dependence-reactivation-results.md`

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

Each canary started from the current clean M2 baseline and added exactly one deferred direct property mapping in a temporary graph only.

| Candidate reactivation | Result | Unsatisfiable classes reintroduced |
| --- | --- | --- |
| `ssn:hasInput -> cco:ont00001921` | not HermiT-clean | `ssn:Input` |
| `ssn:hasOutput -> cco:ont00001986` | not HermiT-clean | `ssn:Output` |

## Interpretation

Both individual Input/Output reactivation canaries failed. The two direct OWL `rdfs:subPropertyOf` mappings should remain deferred for now:

```ttl
ssn:hasInput rdfs:subPropertyOf cco:ont00001921 .
ssn:hasOutput rdfs:subPropertyOf cco:ont00001986 .
```

This does not prove that the intended input/output semantics are invalid. The intended semantics remain:

- `ssn:hasInput` relates a procedure to an input;
- `ssn:hasOutput` relates a procedure to an output.

The canaries show only that these direct OWL subproperty representations are not HermiT-safe in the current merged full-OWL profile.

This result is consistent with the earlier Input/Output diagnostics:

- `reports/hermit-input-output-mapping-evaluation.md` identified `ssn:hasInput` and `ssn:hasOutput` as independent one-class reducers;
- `reports/hermit-input-output-mapping-evaluation.md` found that removing `ssn:hasInput` removes `ssn:Input`, while removing `ssn:hasOutput` removes `ssn:Output`;
- `reports/hermit-input-output-deferral-evaluation.md` showed that deferring both mappings removed the Input/Output pair from the full M2 unsat set;
- the interaction was characterized as mixed source/mapping context involving source restrictions around `Procedure`, `Input`, `Output`, `hasInput`, and `hasOutput`, active input/output property mappings, and the `sosa:Procedure` class-expression mapping context.

The intended input/output semantics remain candidates for HermiT-safe OWL redesign or rule/COMS treatment.

## Recommendation

Keep both Input/Output direct property mappings deferred.

Do not test the two direct property mappings as a group unless a new representation is proposed. Each individual direct-property reactivation already failed from the clean baseline, so a grouped reactivation of the same direct representation would not be a useful next step.

Future work should focus on one of two paths:

- rule/COMS treatment for the intended input/output inference, keeping the active OWL profile clean;
- a redesigned OWL representation tested first in temporary HermiT graphs before any repo mapping change.

Future mapping work should preserve the current HermiT-clean M2 baseline.

## Next Deferred Mapping Area

The next canary area from `reports/deferred-mapping-reactivation-plan.md` should be:

```ttl
sosa:observedProperty rdfs:subPropertyOf cco:ont00001921 .
```

Recommended next branch:

```text
review/evaluate-reactivate-observedProperty-canary
```

That branch should remain report-only unless the temporary canary is HermiT-clean.
