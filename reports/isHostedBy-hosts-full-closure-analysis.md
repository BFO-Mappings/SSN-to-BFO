# IsHostedBy / Hosts Full-Closure Analysis

## Scope

This report is a focused, report-only analysis of the SOSA inverse-property pair:

```text
sosa:isHostedBy / sosa:hosts
```

It follows `reports/sosa-inverse-property-pairs-full-closure-analysis.md`, which classified this pair as medium-low risk. The pair deserves a focused check because both sides have active property-chain mappings and the materialized local SOSA import now contributes the `hosts` / `isHostedBy` inverse axiom.

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

## Full-Closure Method

All HermiT runs used the current full local SOSA closure graph built from:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

After loading, each graph removed:

```ttl
owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty .
sosa:hasSample rdf:type owl:InverseFunctionalProperty .
```

HermiT command pattern:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

## Baseline Confirmation

Command:

```bash
python tools/test_full_sosa_closure_hermit.py --output /tmp/full-sosa-current.md
```

Result:

| Item | Result |
|---|---:|
| triple count | 15769 |
| HermiT return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |

The current active full local SOSA closure is HermiT-clean.

## Pair Inventory

### SOSA Source Context

`imports/sosa.ttl` asserts the inverse relation on the `hosts` side:

```ttl
sosa:hosts owl:inverseOf sosa:isHostedBy .
```

It records source-level domain/range notes using `schema:domainIncludes` and `schema:rangeIncludes`:

| Property | SOSA source note |
|---|---|
| `sosa:hosts` | Platform -> Actuator / Platform / Sampler / Sensor |
| `sosa:isHostedBy` | Actuator / Platform / Sampler / Sensor -> Platform |

The materialized SOSA source file does not assert these notes as global `rdfs:domain` / `rdfs:range` axioms.

### SSN Source Context

`imports/ssn.ttl` contributes a source property-chain axiom for `sosa:hosts`:

```ttl
sosa:hosts owl:propertyChainAxiom ( ssn:inDeployment ssn:deployedSystem ) .
```

It also contains source restrictions connecting hosted systems and hosting platforms:

| Source class | Restriction pattern |
|---|---|
| `sosa:Platform` | `sosa:hosts only ssn:System` |
| `ssn:System` | `sosa:isHostedBy only sosa:Platform` |

These are source-context axioms, not the active BFO property-chain mappings from `SSN2BFO.ttl`.

### Active Mapping Context

`SSN2BFO.ttl` currently contains active property-chain mappings for both sides:

```ttl
sosa:hosts owl:propertyChainAxiom (
  bfo:BFO_0000196
  bfo:BFO_0000054
  bfo:BFO_0000057
) .

sosa:isHostedBy owl:propertyChainAxiom (
  bfo:BFO_0000056
  bfo:BFO_0000055
  bfo:BFO_0000197
) .
```

Local labels for the target BFO properties:

| BFO term | Local label |
|---|---|
| `bfo:BFO_0000196` | bearer of |
| `bfo:BFO_0000054` | has realization |
| `bfo:BFO_0000057` | has participant |
| `bfo:BFO_0000056` | participates in |
| `bfo:BFO_0000055` | realizes |
| `bfo:BFO_0000197` | inheres in |

The two active mapping chains are directionally paired: `hosts` uses the bearer/realization/participant path, while `isHostedBy` uses the inverse-side participates/realizes/inheres path.

### Related Class Mappings

Relevant active local class mappings are:

```text
sosa:Platform equivalentTo
  bfo:MaterialEntity
  and (sosa:hosts some ssn:System)

ssn:System equivalentTo
  bfo:MaterialEntity
  and (ssn:implements some sosa:Procedure)
```

The `sosa:Platform` mapping directly uses `sosa:hosts`. The `ssn:System` mapping does not directly use `sosa:isHostedBy`, although the imported source restriction does.

### Workbook Context

The corresponding workbook rows are in `Common OPs`:

| Row | Source term | Active OWL cell summary | Rationale summary |
|---:|---|---|---|
| 15 | `sosa:hosts` | `owl:propertyChainAxiom ( bfo:bearer_of bfo:has_realization bfo:has_participant )` | hosting as role-mediated support; domain/range intentionally excluded |
| 21 | `sosa:isHostedBy` | `owl:propertyChainAxiom ( bfo:participates_in bfo:realizes bfo:inheres_in )` | inverse-side role-mediated hosting pattern using named inverse BFO relations |

Relevant class rows are in `Common Classes`:

| Row | Source term | Active OWL cell summary |
|---:|---|---|
| 11 | `sosa:Platform` | `equivalentTo bfo:MaterialEntity and (sosa:hosts some ssn:System)` |
| 20 | `ssn:System` | `equivalentTo bfo:MaterialEntity and (ssn:implements some sosa:Procedure)` |

### Comparison Cases

Similarity to the mitigated `madeActuation` / `madeByActuator` pair:

- SOSA materializes an inverse relation between the two properties.
- Both sides have active local mapping commitments.
- Both sides touch BFO participant-style context through active mappings.

Differences from the mitigated actuation agent pair:

- The active hosting mappings are property chains, not direct `rdfs:subPropertyOf` mappings to an inverse CCO target pair.
- There is no direct `cco:agent_in` / `cco:has_agent` analogue.
- The current full local SOSA closure is already HermiT-clean with both hosting chains active.
- The source context points to `sosa:Platform` / `ssn:System`, not to the `sosa:Actuator` / `sosa:Actuation` / `ssn-system:ActuationRange` cluster.

Comparison to previously checked clean pairs:

- Like `madeObservation` / `madeBySensor`, `madeSampling` / `madeBySampler`, `isActedOnBy` / `actsOnProperty`, and `isResultOf` / `hasResult`, the current active state is full-closure HermiT-clean.
- Unlike `isResultOf` / `hasResult`, the hosting pair does not have direct inverse CCO output mappings.
- Unlike the agent pairs, the hosting pair uses BFO property chains to express role-mediated hosting rather than direct agent participation.

## Focused HermiT Variants

Temporary graphs were written under:

```text
/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean
```

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Unsat set | Sample blocker |
|---|---|---|---:|---:|---|---:|---:|---|---|
| V0 | Current full closure baseline | `/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean/V0-baseline.ttl` | 15769 | 0 | yes | 0 | 0 | clean | no |
| V1 | Remove active `SSN2BFO.ttl` BFO-chain mapping for `sosa:hosts` only | `/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean/V1-remove-hosts-mapping.ttl` | 15762 | 0 | yes | 0 | 0 | clean | no |
| V2 | Remove active `SSN2BFO.ttl` BFO-chain mapping for `sosa:isHostedBy` only | `/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean/V2-remove-isHostedBy-mapping.ttl` | 15762 | 0 | yes | 0 | 0 | clean | no |
| V3 | Remove both active hosting BFO-chain mappings | `/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean/V3-remove-both-hosting-mappings.ttl` | 15755 | 0 | yes | 0 | 0 | clean | no |
| V4 | Skipped: no exact source-supported `rdfs:domain` / `rdfs:range` candidate | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| V5 | Skipped: no missing workbook-proposed CCO/BFO mapping was found | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| V6 | Remove materialized SOSA inverse axiom `sosa:hosts owl:inverseOf sosa:isHostedBy` | `/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean/V6-remove-sosa-inverse.ttl` | 15768 | 0 | yes | 0 | 0 | clean | no |
| V7 | Remove source class restrictions involving `sosa:hosts` / `sosa:isHostedBy` | `/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean/V7-remove-source-hosting-restrictions.ttl` | 15761 | 0 | yes | 0 | 0 | clean | no |
| V8 | Remove active `sosa:Platform` class-expression mapping | `/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean/V8-remove-platform-class-mapping.ttl` | 15759 | 0 | yes | 0 | 0 | clean | no |
| V9 | Remove active `ssn:System` class-expression mapping | `/tmp/ssn-to-bfo-isHostedBy-hosts-full-closure-analysis-clean/V9-remove-system-class-mapping.ttl` | 15759 | 0 | yes | 0 | 0 | clean | no |

V1 and V2 removed only the active `SSN2BFO.ttl` BFO property-chain mapping for the relevant side. The source `sosa:hosts owl:propertyChainAxiom ( ssn:inDeployment ssn:deployedSystem )` from `imports/ssn.ttl` remained unless a variant explicitly addressed source context.

V4 was skipped because the imported SOSA source uses `schema:domainIncludes` / `schema:rangeIncludes`, not exact global `rdfs:domain` / `rdfs:range` axioms. The workbook also explicitly says that domain/range assertions are intentionally excluded from the `sosa:hosts` mapping row.

V5 was skipped because both sides already have active workbook and TTL property-chain mappings. No clear missing symmetric direct CCO/BFO mapping was found in the workbook or active TTL context.

V7 removed:

```text
sosa:Platform rdfs:subClassOf (sosa:hosts only ssn:System)
ssn:System rdfs:subClassOf (sosa:isHostedBy only sosa:Platform)
```

All executed variants were HermiT-clean.

## Interpretation

The current active `isHostedBy` / `hosts` pair is HermiT-clean under the full local SOSA closure.

The pair does have inverse-side coupling:

```text
sosa:hosts inverseOf sosa:isHostedBy
hosts chain:      bearer_of -> has_realization -> has_participant
isHostedBy chain: participates_in -> realizes -> inheres_in
```

However, this coupling is not the same pattern that caused the mitigated actuation-agent failure. The actuation failure involved two direct SOSA-to-CCO subproperty mappings to a CCO inverse agent pair, plus SOSA source restrictions and actuation/actuator class context. The hosting pair instead uses BFO property chains and remains clean with the materialized SOSA inverse, source restrictions, `sosa:Platform` mapping, and `ssn:System` mapping all active.

Removing either side of the active hosting chains, removing both chains, removing the SOSA inverse, removing source hosting restrictions, or removing the related class-expression mappings all preserved HermiT cleanliness. These are not reducers for a hidden unsatisfiable cluster because the baseline is already clean, but they confirm that none of these pieces is currently sitting at the edge of an observed inconsistency.

The platform/system hosting context does create modeling complexity because:

- `sosa:hosts` has both a source deployment chain and an active BFO role-realization-participant chain.
- `sosa:Platform` is locally defined using `sosa:hosts some ssn:System`.
- `ssn:System` has an imported source restriction using `sosa:isHostedBy only sosa:Platform`.

In the current full-closure profile, that complexity is HermiT-safe.

## Risk Classification

This pair can be downgraded from medium-low risk to low-to-medium documentation risk:

- Low risk for the current active graph: the full local SOSA closure baseline is clean, and focused variants did not reveal any active inconsistency.
- Medium documentation caution for future changes: adding direct CCO/BFO mappings, global domain/range axioms, or stronger class definitions around hosting should still be tested under the full local SOSA closure because the pair is inverse-linked and property-chain-heavy.

## Recommendation

No mapping change is warranted for `sosa:isHostedBy` / `sosa:hosts`.

Recommended next step: no further focused hosting-pair branch is needed. Keep relying on the full local SOSA closure HermiT validation check for future mapping changes, and test any future strengthening of hosting domain/range or direct CCO/BFO mappings in temporary full-closure graphs before editing `SSN2BFO.ttl`.

## Validation

Validation commands:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/isHostedBy-hosts-full-closure-analysis.md

git diff --check
```

Result: PASS.

Workflow-check summary:

- Validation suite: PASS.
- Full local SOSA closure HermiT check: PASS.
- Python compile check: PASS.
- Git whitespace check: PASS.
- Expected changed file set: only `reports/isHostedBy-hosts-full-closure-analysis.md`.
