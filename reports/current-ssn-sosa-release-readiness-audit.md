# Current SSN/SOSA Release-Readiness Audit

## Scope

This report audits whether the current SSN/SOSA-to-BFO/CCO mapping is ready for use and release.

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

## Release Structure

The repository currently has two different layers that should not be conflated:

1. the active current mapping source and validation layer at the repository root; and
2. scaffolded release-track files under `src/` and `releases/`.

### Source-Of-Truth Files

The current source-of-truth files for the active mapping are:

| File / directory | Current role |
|---|---|
| `SSN2BFO.ttl` | Authored current SSN/SOSA-to-BFO/CCO mapping candidate. This is the populated active TTL mapping used by the validation suite. |
| `Current_SOSA-SSN to BFO-CCO.xlsx` | Workbook mapping documentation, rationale, and spreadsheet-side audit source. It is not fully aligned with the TTL for `sosa:Sensor`, by intentional version-alignment deferral. |
| `imports/cco.ttl`, `imports/sosa.ttl`, `imports/ssn.ttl`, `imports/ssn-systems.ttl` | Local import closure used by current validation and HermiT checks. |
| `tools/` | Current validation tooling, including mapping audit, ELK instance-entailment coverage, instance smoke tests, and full local SOSA closure HermiT. |
| `reports/` | Validation evidence, diagnostic history, and implementation reports. These are evidence and documentation, not release ontology artifacts. |

The workbook has five visible sheets:

```text
Common Classes
Common OPs
Common DPs
System Capability
Sample Relationship
```

### Generated Or Release-Track Files

The tracked release and scaffold files are:

| Path | Current role / readiness |
|---|---|
| `releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl` | Placeholder release file, not populated with the current mapping. |
| `releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl` | Placeholder release file, not populated with the current mapping. |
| `src/current-ssn-sosa/ssn-sosa-mappings-edit.ttl` | Placeholder editor ontology importing the two placeholder release files. |
| `src/current-ssn-sosa/build/artifacts/` | Ignored generated artifacts when `src` Make targets are run. Not release artifacts. |

The current release files are stale or incomplete relative to `SSN2BFO.ttl`. They contain only minimal ontology declarations and placeholder comments:

| File | Parsed triple count |
|---|---:|
| `SSN2BFO.ttl` | 1115 |
| `releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl` | 3 |
| `releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl` | 3 |
| `src/current-ssn-sosa/ssn-sosa-mappings-edit.ttl` | 5 |

The README explicitly states that the four release files under `releases/` are placeholders until completed mapping content is inserted. It also states that spreadsheet-to-TTL conversion is not implemented and that release-file BFO projection from CCO mappings is not implemented.

### Available Commands

Root validation commands:

```bash
make validate
make validate-write
make audit-write
make check
python tools/run_validation_suite.py
```

Track scaffold commands:

```bash
make -C src/current-ssn-sosa all
make -C src/current-ssn-sosa derive-bfo-from-cco
make -C src/current-ssn-sosa output-release-filepaths
make -C src/current-ssn-sosa output-release-name
```

`output-release-filepaths` reports the two tracked current release placeholders:

```text
../../releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl
../../releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl
```

`derive-bfo-from-cco` writes a review-only generated BFO projection under `src/current-ssn-sosa/build/artifacts/`. The README says that generated artifact is not a release file and does not populate the BFO release placeholder.

No tracked release notes or changelog convention was found. The current-track Makefile has a timestamped `config.RELEASE_NAME`, but no release-note file or versioned release metadata workflow appears to be implemented.

## Current Validation Baseline

Command run:

```bash
python tools/run_validation_suite.py
```

Result:

| Check / count | Current result |
|---|---:|
| validation suite status | PASS |
| `ttl_candidate_mapping_assertions` | 68 |
| mapping audit issues | 2 |
| `missing_in_spreadsheet` | 1 |
| `missing_in_ttl` | 1 |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 75 |
| property-chain expectations | 5 |
| restriction expectations | 2 |
| ELK expectation failures | 0 |
| uncovered active direct mappings | 0 |
| uncovered active property-chain mappings | 0 |
| uncovered active restriction mappings | 0 |
| instance-data smoke test | PASS |
| ELK instance mapping entailment test | PASS |
| full local SOSA closure HermiT check | PASS |
| full local SOSA closure triple count | 15769 |
| HermiT return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |

The only mapping-audit issues are the two recognized expected `sosa:Sensor` version-alignment issues:

```text
ISSUE-0001 missing_in_spreadsheet:
sosa:Sensor => bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Observation; cco:ont00001787

ISSUE-0002 missing_in_ttl:
Common Classes row 18:
sosa:Sensor => bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569
```

## Issue Classification

| Issue / decision | Classification | Release impact |
|---|---|---|
| Two expected `sosa:Sensor` version-alignment audit issues | C. Non-blocking expected issue | Not a source-mapping release blocker. Must be called out as a known limitation because TTL and workbook intentionally target different CCO/version assumptions for Sensor. |
| Deferred actuation-side CCO agent mappings: `sosa:madeActuation -> cco:agent_in`, `sosa:madeByActuator -> cco:has_agent` | B. Release note / documented limitation | Not a blocker after deferral. Source-level domain/range typing remains active, including `sosa:madeByActuator rdfs:range sosa:Actuator`; direct CCO agent mappings remain deferred for full-SOSA-closure HermiT safety. |
| Rejected `ssn:hasInput` / `ssn:hasOutput` direct CCO mappings | B. Release note / documented limitation | Not a blocker. The old CCO mappings are removed/rejected; source SSN relations remain. Release notes should not describe them as intended-but-deferred active mappings. |
| Deferred/rejected `sosa:observedProperty -> cco:has_input` direct mapping | B. Release note / documented limitation | Not a blocker. Direct CCO property mapping remains inactive because reactivation reintroduced the Observation / Sensor / Stimulus HermiT cluster. |
| SSN Systems dependence mappings to `bfo:BFO_0000194` | B. Release note / documented limitation | Not a blocker. The failed direct BFO dependence subproperty mappings remain deferred; source-level domain/range operationalization is active where added. |
| Prior reduced-M2-only HermiT reports | D. Already resolved / historical limitation | The project has added `imports/sosa.ttl` and a full local SOSA closure HermiT validation check. Older reduced-M2 clean results should be read as historical evidence, not as the current release guardrail. |
| Current inverse-property-pair audit | D. Already resolved | The selected SOSA inverse-property pairs have focused full-closure reports. Current active state is HermiT-clean; no mapping change is recommended from that audit. |
| `releases/current-ssn-sosa/*.ttl` artifacts | A. Release blocker | The tracked release files are placeholders and are not populated from the current source mapping. They are not ready for users as release artifacts. |
| Absence of release notes / known-limitations file | A. Release blocker for formal release | A release needs explicit notes documenting validation status, Sensor version deferral, deferred direct mappings, and the full-SOSA HermiT guardrail. |

## User-Facing Release Readiness

| Artifact | Can users rely on it now? | Assessment |
|---|---|---|
| `SSN2BFO.ttl` | Yes, as the current validated source mapping candidate. | It passes parse, mapping audit with only expected Sensor issues, ELK coverage, instance smoke tests, and full local SOSA closure HermiT. It still carries documented limitations around deferred direct mappings. |
| `Current_SOSA-SSN to BFO-CCO.xlsx` | Yes, as mapping documentation with caveats. | It documents source terms, rationale, and mapping rows, but it is intentionally not perfectly audit-aligned for `sosa:Sensor`. It should not be treated as a lossless generator for the current TTL. |
| `reports/` | Yes, as validation and decision evidence. | Reports document the current validation state, known limitations, and why certain mappings are deferred or rejected. Reports are not release ontology artifacts. |
| `releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl` | No. | Placeholder shell only; not populated with current BFO mapping content. |
| `releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl` | No. | Placeholder shell only; not populated with current CCO mapping content. |
| `src/current-ssn-sosa/ssn-sosa-mappings-edit.ttl` | No, not as the current mapping. | Placeholder editor ontology importing placeholder release files. |

Conclusion: the current source mapping is ready for controlled use as a validated source artifact, but the tracked release artifacts are not release-ready.

## Required Release-Preparation Tasks

Before treating the current mapping as ready for release, complete these tasks:

1. Decide the release target and branch policy: whether the release is cut from `tests`, `stage`, or `main`, and whether `SSN2BFO.ttl` remains the release source or is split into `releases/current-ssn-sosa` files.
2. Populate or regenerate `releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl` from the current validated source mapping, or explicitly document that `SSN2BFO.ttl` is the release artifact for this release.
3. Populate or regenerate `releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl`, or explicitly mark it out of scope if only the CCO-extending source mapping is being released.
4. Add release notes or a known-limitations report for the current SSN/SOSA release.
5. In the release notes, mention the intentional `sosa:Sensor` version-alignment deferral.
6. In the release notes, mention the deferred actuation-side CCO agent mappings and the active source-level domain/range replacement state.
7. In the release notes, mention that `ssn:hasInput`, `ssn:hasOutput`, and `sosa:observedProperty` direct CCO mappings are not active direct property mappings in this release.
8. In the release notes, mention that direct SSN Systems dependence mappings to `bfo:BFO_0000194` remain deferred and that source-level domain/range operationalization is active where implemented.
9. Reference the full local SOSA closure HermiT validation check as the current OWL consistency guardrail.
10. Rerun `python tools/run_validation_suite.py`.
11. Rerun report/workflow checks appropriate to the release-preparation branch.
12. If release files are populated, parse-check them and run any `src/current-ssn-sosa` scaffold checks needed for the release layout.
13. Only after artifacts, notes, and validation are clean, tag or publish according to the repo's chosen branch/release policy.

## Recommendation

Recommended next branch:

```text
release/prepare-current-ssn-sosa-artifacts
```

Rationale: the source mapping itself is validation-clean and usable with documented limitations, but the tracked release artifacts under `releases/current-ssn-sosa/` are still placeholders. A release-preparation branch should either populate those artifacts from the current validated source or explicitly redefine the release deliverable as `SSN2BFO.ttl` with release notes and known limitations.

No mapping change is recommended by this release-readiness audit.

## Validation

Validation commands for this report:

```bash
python tools/workflow_check.py --mode report-only \
  --expected-file reports/current-ssn-sosa-release-readiness-audit.md

git diff --check
```

Result: PASS.

Workflow-check summary:

- Validation suite: PASS.
- Mapping audit: PASS with only the two recognized expected `sosa:Sensor` version-alignment issues.
- ELK instance mapping entailment test: PASS.
- Full local SOSA closure HermiT check: PASS.
- Python compile check: PASS.
- Git whitespace check: PASS.
- Expected changed file set: only `reports/current-ssn-sosa-release-readiness-audit.md`.
