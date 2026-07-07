# Deferred Mapping Reactivation Plan

## Scope

This is a report-only plan for evaluating whether any currently deferred active OWL mappings can be safely reactivated one at a time after the current HermiT-clean M2 baseline.

No ontology mappings, spreadsheet files, imports, examples, generated release artifacts, existing reports, or tools were edited for this plan.

Repository context at report generation:

| Field | Value |
| --- | --- |
| Branch | `review/deferred-mapping-reactivation-plan` |
| Commit | `327ac206413b94ac9e8e566ae0fad5866d1cf289` |
| Worktree before report | clean |

Primary inputs:

- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/hermit-observedProperty-deferral-evaluation.md`
- `reports/hermit-input-output-deferral-evaluation.md`
- `reports/hermit-input-output-mapping-evaluation.md`
- `reports/hermit-survival-range-deferral-evaluation.md`
- `reports/hermit-survival-range-sosa-context-explanation.md`
- `reports/hermit-survival-property-minimal-conflict-extraction.md`
- `reports/hermit-survival-property-source-restriction-explanation.md`
- `reports/hermit-remaining-unsat-isolation.md`
- `reports/hermit-hasProperty-domain-range-architecture.md`
- `SSN2BFO.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`

## Current Stable Baseline

The current stable baseline is the HermiT-clean state documented in `reports/hermit-clean-baseline-after-deferrals.md`.

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

The remaining audit issues are separate from HermiT cleanliness:

| Issue | Category | Source |
| --- | --- | --- |
| `ISSUE-0001` | `missing_in_spreadsheet` | `sosa:Sensor` |
| `ISSUE-0002` | `missing_in_ttl` | `sosa:Sensor`, `Common Classes` row 18 |

## Deferred Mapping Inventory

The following inventory lists currently deferred active OWL mappings. "Deferred" means the mapping's intended semantics remain documented, but the active OWL logical assertion is not currently present in `SSN2BFO.ttl`.

| Source term | Deferred target or expression | Kind | TTL location | Spreadsheet row | Why deferred | Known HermiT effect | Intended semantics remain? | Likely future representation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ssn-system:hasOperatingProperty` | `bfo:BFO_0000194` / specifically depended on by | direct property mapping | `SSN2BFO.ttl` lines 183-184 | `System Capability` row 9 | Selected SSN Systems direct BFO dependence mappings reduced satisfiability in the merged full-OWL profile. | In `hermit-hasProperty-domain-range-architecture`, removing the selected BFO dependence mappings reduced the M2 unsat count from 24 to 8; the operating-property contribution was part of that selected group. | yes; if operating range `x` has operating property `y`, then `y` specifically depends on `x` | rule/COMS note preferred unless one-at-a-time OWL reactivation is HermiT-clean |
| `ssn-system:hasSurvivalProperty` | `bfo:BFO_0000194` / specifically depended on by | direct property mapping | `SSN2BFO.ttl` lines 191-192 | `System Capability` row 11 | Same selected SSN Systems direct BFO dependence mapping risk as above. | Same selected-group reducer; also adjacent to the SurvivalProperty / BatteryLifetime / SystemLifetime source-restriction cluster. | yes; if survival range `x` has survival property `y`, then `y` specifically depends on `x` | rule/COMS note preferred unless one-at-a-time OWL reactivation is HermiT-clean |
| `ssn-system:hasSystemProperty` | `bfo:BFO_0000194` / specifically depended on by | direct property mapping | `SSN2BFO.ttl` lines 203-204 | `System Capability` row 14 | High-impact HermiT interaction involving `hasSystemProperty`, imported source restrictions, and the BFO dependence domain/range package. | Prior diagnostics found removing only this mapping reduced 24 unsats to 11; tested OWL alternatives did not improve beyond no logical mapping. | yes; if capability `x` has system property `y`, then `y` specifically depends on `x` | rule/COMS architecture preferred; OWL reactivation is high risk |
| `ssn-system:SurvivalRange` | class-expression mapping summarizing a survival-oriented system range/capability profile, including function/realization-style target context | direct class-expression mapping | `SSN2BFO.ttl` lines 1117-1119 | `System Capability` row 29 | Identified as a high-impact dependency in the mixed `ssn:hasProperty` / `hasSurvivalProperty` / non-sample `sosa:` context. | Deferral removed the SSN Systems trio from full M2 and made the B2 systems-only reproduction HermiT-clean; before full M2 had 8 unsats, after deferral left only the then-known core five-class cluster. | yes; SurvivalRange remains a survival-oriented system range/capability profile | further analysis or HermiT-safe OWL redesign; possible rule/COMS documentation |
| `ssn:hasInput` | `cco:ont00001921` / has input | direct property mapping | `SSN2BFO.ttl` lines 154-155 | `Common OPs` row 9 | One-class HermiT reducer for `ssn:Input` in a mixed source-restriction / `sosa:Procedure` context. | Deferral removed `ssn:Input` from the M2 unsat set; paired deferral with `ssn:hasOutput` reduced the five-class core cluster to Observation / Sensor / Stimulus. | yes; `ssn:hasInput` relates procedures to their inputs | further analysis; possible rule/COMS treatment; OWL only if reactivation is clean |
| `ssn:hasOutput` | `cco:ont00001986` / has output | direct property mapping | `SSN2BFO.ttl` lines 158-160 | `Common OPs` row 10 | One-class HermiT reducer for `ssn:Output` in the same mixed source-restriction / `sosa:Procedure` context. | Deferral removed `ssn:Output` from the M2 unsat set; paired deferral with `ssn:hasInput` reduced the five-class core cluster to Observation / Sensor / Stimulus. | yes; `ssn:hasOutput` relates procedures to their outputs | further analysis; possible rule/COMS treatment; OWL only if reactivation is clean |
| `sosa:observedProperty` | `cco:ont00001921` / has input | direct property mapping | `SSN2BFO.ttl` lines 127-128 | `Common OPs` row 33 | Narrow one-triple reducer for the final Observation / Sensor / Stimulus HermiT cluster. | Before deferral: 3 unsats (`sosa:Observation`, `sosa:Sensor`, `ssn:Stimulus`); after deferral: HermiT-clean with `owl:Nothing` count 0. | yes; `observedProperty` relates an observation to the observed property | further analysis; possible rule/COMS treatment; OWL reactivation likely high risk because it directly cleared the final cluster |

## Reactivation Discipline

Future reactivation evaluations should use this discipline:

1. Start every reactivation branch from current `tests`.
2. Reactivate only one deferred mapping at a time unless a prior report explicitly justifies a grouped test.
3. Use a dedicated branch for each reactivation evaluation.
4. Restore the exact TTL logical assertion being tested.
5. Restore or update the corresponding spreadsheet OWL axiom cell so the audit remains source-consistent.
6. Regenerate expected reports only:
   - `reports/mapping-consistency-audit.md`
   - `reports/mapping-consistency-audit.csv` if changed
   - `reports/elk-instance-mapping-entailments.md` if active mapping expectations change
   - one new evaluation report for the branch
7. Run standard validation.
8. Run HermiT M2 with the same graph construction and cleanup conditions as `reports/hermit-clean-baseline-after-deferrals.md`.
9. If reactivation reintroduces unsatisfiable classes, revert the reactivation in that branch and document the result as report-only.
10. If reactivation is HermiT-clean and validation-clean, it can be proposed as a final mapping reactivation PR.
11. Do not overclaim semantic invalidity from HermiT failure. HermiT failure shows an unsafe full-OWL interaction in the current profile, not necessarily that the intended mapping is conceptually wrong.

## Recommended Reactivation Order

Recommended order:

| Order | Candidate | Why here | Expected risk |
| ---: | --- | --- | --- |
| 1 | `ssn-system:hasOperatingProperty -> bfo:BFO_0000194` | Direct one-triple property mapping; useful canary for SSN Systems dependence reactivation; semantically local to OperatingRange. | medium |
| 2 | `ssn-system:hasSurvivalProperty -> bfo:BFO_0000194` | Direct one-triple property mapping, but closer to the prior SurvivalProperty / SurvivalRange cluster. | medium-high |
| 3 | `ssn-system:hasSystemProperty -> bfo:BFO_0000194` | Direct one-triple property mapping, but prior diagnostics found it was the largest individual reducer among SSN Systems property mappings. | high |
| 4 | SSN Systems dependence group: the three mappings above together | Only if each individual mapping is HermiT-clean. This tests whether pairwise/group interaction reappears. | high |
| 5 | `ssn:hasInput -> cco:ont00001921` | Direct property mapping; independent one-class reducer for `ssn:Input`; test after SSN Systems canaries. | high |
| 6 | `ssn:hasOutput -> cco:ont00001986` | Direct property mapping; independent one-class reducer for `ssn:Output`. | high |
| 7 | Optional Input/Output pair | Only if both individual Input/Output reactivations are HermiT-clean. | high |
| 8 | `sosa:observedProperty -> cco:ont00001921` | Narrow one-triple mapping, but it directly cleared the final Observation / Sensor / Stimulus cluster and is likely to reintroduce it. | high |
| 9 | `ssn-system:SurvivalRange` class-expression mapping | Structurally complex class-expression mapping tied to broader SSN Systems and non-sample SOSA context. Evaluate last. | very high |

This order keeps narrow direct property mappings first, but does not treat all direct property mappings as equal. The SSN Systems dependence mappings are first because they can be tested as simple canaries and may reveal whether the current clean baseline changed their behavior. `sosa:observedProperty` is also one triple, but prior evidence is especially direct: deferring it cleared the final remaining HermiT cluster. `ssn-system:SurvivalRange` is last because it is not a one-triple direct property mapping and prior extraction work tied it to broader mixed context.

## Future Branch Checklist

Use this checklist for each future reactivation branch.

| Item | Required entry |
| --- | --- |
| Branch name | `review/evaluate-reactivate-<source-term>-mapping` or similar |
| Exact mapping | State the one deferred mapping being reactivated |
| TTL edit | Restore the exact logical assertion or class-expression mapping in `SSN2BFO.ttl` |
| Spreadsheet edit | Restore/update the corresponding OWL Axiom cell and rationale in `Current_SOSA-SSN to BFO-CCO.xlsx` |
| Reports to regenerate | mapping audit; ELK entailment report if active expectations change; one new HermiT evaluation report |
| HermiT before/after | Run current clean baseline before and reactivated graph after; record triple count, return code, reasoned output, `owl:Nothing`, unsat count, unsat set, and sample simplicity blocker status |
| Validation command | `python tools/run_validation_suite.py` or `make validate`; use `--write-reports` only when canonical reports intentionally change |
| Workflow check | `python tools/workflow_check.py --mode mapping-change --expected-file ...` |
| Decision criteria | HermiT-clean, validation-clean, audit has no unexpected issues, and active mapping expectations remain covered |

If the reactivation fails HermiT:

- revert the TTL and spreadsheet reactivation in that branch;
- keep only a report documenting the failed reactivation test;
- do not merge the active mapping change;
- do not claim the mapping semantics are wrong solely from HermiT failure.

If the reactivation passes:

- keep the restored mapping and spreadsheet row;
- keep regenerated reports;
- document the HermiT-clean result;
- propose a final reactivation PR for human review.

## First Recommended Branch

First recommended evaluation branch:

```text
review/evaluate-reactivate-hasOperatingProperty-mapping
```

Exact mapping to reactivate:

```ttl
ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

Why first:

- it is a one-triple direct property mapping;
- it is one of the selected SSN Systems dependence mappings, but not the previously largest individual reducer;
- it is a good canary for whether any selected SSN Systems dependence mapping can return safely under the current HermiT-clean baseline;
- its intended semantics remain documented in `System Capability` row 9.

Expected changed-file set for the first evaluation:

```text
SSN2BFO.ttl
Current_SOSA-SSN to BFO-CCO.xlsx
reports/mapping-consistency-audit.md
reports/mapping-consistency-audit.csv        # only if changed
reports/elk-instance-mapping-entailments.md  # if active expectations change
reports/hermit-hasOperatingProperty-reactivation-evaluation.md
```

Suggested decision rule:

- If reactivation is HermiT-clean and standard validation remains clean, consider a final reactivation PR.
- If it reintroduces any unsat class, revert the active reactivation and keep a report-only failed reactivation note.
