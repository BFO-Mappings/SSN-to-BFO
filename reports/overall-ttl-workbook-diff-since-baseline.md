# Overall TTL / Workbook Diff Since Baseline

## Scope

This report compares the current `HEAD` against the cleanup-sequence baseline:

```text
8d34254a5a4b323a150c30e91110b18dc5583e3c
```

Compared files:

```text
SSN2BFO.ttl
Current_SOSA-SSN to BFO-CCO.xlsx
```

No ontology mappings, workbook rows, imports, tools, examples, generated/release artifacts, or existing reports were edited.

Temporary comparison files were written under:

```text
/tmp/ssn-to-bfo-overall-ttl-workbook-diff
```

## Metadata

| Item | Value |
|---|---|
| BASE SHA | `8d34254a5a4b323a150c30e91110b18dc5583e3c` |
| BASE subject | `Merge pull request #23 from BFO-Mappings/feature/validate-current-examples` |
| first cleanup-sequence commit after BASE | `0419809df8f1956bdb0f988b4f8d7e761c2c23b9` / `Add mapping consistency audit tooling` |
| HEAD SHA | `d514094eece7ed7c4c0183f395d2fe4f4fc854bf` |
| HEAD subject | `Merge pull request #159 from BFO-Mappings/review/release-readiness-current-ssn-sosa` |
| current branch | `review/overall-ttl-workbook-diff` |
| `SSN2BFO.ttl` existed at BASE | yes |
| `Current_SOSA-SSN to BFO-CCO.xlsx` existed at BASE | yes |

Raw git diff stat for the two compared files:

```text
Current_SOSA-SSN to BFO-CCO.xlsx | Bin 27453 -> 26859 bytes
SSN2BFO.ttl                      | 309 +++++++++++++++++++--------------------
2 files changed, 148 insertions(+), 161 deletions(-)
```

For `SSN2BFO.ttl`, the line-diff scale is moderate: 309 changed lines. The workbook is a binary `.xlsx`, so the useful comparison is the cell-level diff below rather than raw Git binary output.

## TTL Diff

The BASE TTL was extracted with:

```bash
git show 8d34254a5a4b323a150c30e91110b18dc5583e3c:SSN2BFO.ttl \
  > /tmp/ssn-to-bfo-overall-ttl-workbook-diff/base-SSN2BFO.ttl
```

Both BASE and HEAD parsed successfully with `rdflib`.

| TTL graph item | BASE | HEAD | Change |
|---|---:|---:|---:|
| total triples | 1172 | 1115 | -57 |
| canonical graph-diff added triples | n/a | 196 | n/a |
| canonical graph-diff removed triples | 253 | n/a | n/a |
| `rdfs:subPropertyOf` triples | 28 | 21 | -7 |
| `rdfs:domain` triples | 0 | 31 | +31 |
| `rdfs:range` triples | 0 | 31 | +31 |
| `rdfs:subClassOf` triples | 32 | 31 | -1 |
| `owl:propertyChainAxiom` triples | 3 | 5 | +2 |

The added/removed graph-diff counts include blank-node class-expression rewrites. They are useful as a scale measure, but subject-level grouping is more readable than a raw triple dump.

### Added TTL Subjects

Largest non-blank-node added subject groups:

| Subject | Added triples | Main examples |
|---|---:|---|
| `ssn:implementedBy` | 4 | object-property typing, source-level domain/range, property chain |
| `sosa:observes` | 3 | domain `sosa:Sensor`, range `sosa:ObservableProperty`, `subPropertyOf ssn:forProperty` |
| `ssn:hasSubSystem` | 3 | domain/range `ssn:System`, `subPropertyOf bfo:BFO_0000178` |
| `sosa:actsOnProperty` | 2 | domain `sosa:Actuation`, range `sosa:ActuatableProperty` |
| `sosa:madeActuation` | 2 | domain `sosa:Actuator`, range `sosa:Actuation` |
| `sosa:madeByActuator` | 2 | domain `sosa:Actuation`, range `sosa:Actuator` |
| `sosa:observedProperty` | 2 | domain `sosa:Observation`, range `sosa:ObservableProperty` |
| `ssn-system:hasOperatingProperty` | 2 | domain `OperatingRange`, range `OperatingProperty` |
| `ssn-system:hasSurvivalProperty` | 2 | domain `SurvivalRange`, range `SurvivalProperty` |
| `ssn-system:hasSystemProperty` | 2 | domain `SystemCapability`, range `SystemProperty` |

### Removed TTL Subjects

Largest non-blank-node removed subject groups:

| Subject | Removed triples | Main examples |
|---|---:|---|
| `ssn-system:BatteryLifetime` | 2 | class typing / class-expression mapping removed |
| `ssn-system:MeasurementRange` | 2 | class typing / class-expression mapping removed |
| `sosa:hasFeatureOfInterest` | 1 | removed direct `subPropertyOf cco:ont00001921` |
| `sosa:isFeatureOfInterestOf` | 1 | removed direct `subPropertyOf cco:ont00001841` |
| `sosa:madeActuation` | 1 | removed direct `subPropertyOf cco:ont00001787` |
| `sosa:madeByActuator` | 1 | removed direct `subPropertyOf cco:ont00001833` |
| `sosa:observedProperty` | 1 | removed direct `subPropertyOf cco:ont00001921` |
| `ssn:hasInput` | 1 | removed direct `subPropertyOf cco:ont00001921` |
| `ssn:hasOutput` | 1 | removed direct `subPropertyOf cco:ont00001986` |
| `ssn-system:hasOperatingProperty` | 1 | removed direct `subPropertyOf bfo:BFO_0000195` |
| `ssn-system:hasSurvivalProperty` | 1 | removed direct `subPropertyOf bfo:BFO_0000195` |
| `ssn-system:hasSystemProperty` | 1 | removed direct `subPropertyOf bfo:BFO_0000195` |

### Source Domain/Range Additions

BASE had no `rdfs:domain` or `rdfs:range` triples in `SSN2BFO.ttl`. HEAD has 31 domain and 31 range triples.

Important added source-level domain/range groups include:

| Source property | HEAD source-level typing |
|---|---|
| `sosa:actsOnProperty` | domain `sosa:Actuation`; range `sosa:ActuatableProperty` |
| `sosa:isActedOnBy` | domain `sosa:ActuatableProperty`; range `sosa:Actuation` |
| `sosa:madeActuation` | domain `sosa:Actuator`; range `sosa:Actuation` |
| `sosa:madeByActuator` | domain `sosa:Actuation`; range `sosa:Actuator` |
| `sosa:madeObservation` | domain `sosa:Sensor`; range `sosa:Observation` |
| `sosa:madeBySensor` | domain `sosa:Observation`; range `sosa:Sensor` |
| `sosa:madeSampling` | domain `sosa:Sampler`; range `sosa:Sampling` |
| `sosa:madeBySampler` | domain `sosa:Sampling`; range `sosa:Sampler` |
| `sosa:observedProperty` | domain `sosa:Observation`; range `sosa:ObservableProperty` |
| `sosa:observes` | domain `sosa:Sensor`; range `sosa:ObservableProperty` |
| `ssn:hasInput` | domain `sosa:Procedure`; range `ssn:Input` |
| `ssn:hasOutput` | domain `sosa:Procedure`; range `ssn:Output` |
| `ssn-system:hasOperatingProperty` | domain `OperatingRange`; range `OperatingProperty` |
| `ssn-system:hasSurvivalProperty` | domain `SurvivalRange`; range `SurvivalProperty` |
| `ssn-system:hasSystemProperty` | domain `SystemCapability`; range `SystemProperty` |

These additions are source-level operationalization, not BFO/CCO domain/range shortcuts.

### Important Mapping-Level TTL Changes

| Area | BASE state | HEAD state | Interpretation |
|---|---|---|---|
| actuation-side CCO agent mappings | `sosa:madeActuation subPropertyOf cco:ont00001787`; `sosa:madeByActuator subPropertyOf cco:ont00001833` | both direct CCO agent mappings removed; source domain/range active | HermiT/full-closure safety change. Paired CCO agent mappings were unsafe under full local SOSA closure. |
| `sosa:madeByActuator` range | absent | `sosa:madeByActuator rdfs:range sosa:Actuator` | Source-level fidelity addition made safe after agent mapping deferral. |
| `ssn:hasInput` / `ssn:hasOutput` | direct CCO mappings to `cco:has_input` / `cco:has_output` | direct CCO mappings removed; source domain/range active | Old direct CCO mappings rejected/removed; source SSN relation retained. |
| `sosa:observedProperty` | domain/range plus direct CCO `has_input` mapping | source domain/range only | Direct CCO mapping removed for HermiT safety; observed-property semantics remain source-level. |
| SSN Systems dependence properties | direct subproperty mappings to BFO dependence target | source domain/range only | Direct BFO dependence subproperty mappings deferred; source-level operationalization retained. |
| `ssn-system:SystemProperty` | direct class-expression mapping with `prescribed_by` branch | source class retained; direct class-expression mapping removed | Over-specific class-expression mapping deferred; broader typing inherited through `ssn:Property`. |
| `ssn-system:ActuationRange` | class expression included `cco:affects some bfo:ProcessProfile` branch | simplified class expression without that branch | HermiT-clean simplification of an overstrong/suspicious branch. |
| `sosa:Sensor` | active blank-node subclass expression | active blank-node subclass expression remains | Sensor is still intentionally version-misaligned with workbook row 18; current mismatch is documented as expected. |
| imports/source profile | `SSN2BFO.ttl` import declarations not materially changed in this file diff | same direct import shape in TTL | The important validation profile change, materialized `imports/sosa.ttl` plus full local SOSA closure HermiT check, is outside the two compared files. |

Active mapping assertion count from the current audit tool:

| Snapshot | `ttl_candidate_mapping_assertions` |
|---|---:|
| BASE | 73 |
| HEAD | 68 |

## Workbook Diff

The BASE workbook was extracted with:

```bash
git show 8d34254a5a4b323a150c30e91110b18dc5583e3c:'Current_SOSA-SSN to BFO-CCO.xlsx' \
  > /tmp/ssn-to-bfo-overall-ttl-workbook-diff/base-workbook.xlsx
```

The workbook comparison used `openpyxl`, normalized cell values to strings, and ignored workbook metadata.

| Workbook item | BASE | HEAD |
|---|---:|---:|
| sheets added | 0 | 0 |
| sheets removed | 0 | 0 |
| non-empty cells added | n/a | 0 |
| non-empty cells removed | 8 | n/a |
| non-empty cells changed | n/a | 79 |

Changed row count by sheet:

| Sheet | Changed rows |
|---|---:|
| `Common Classes` | 3 |
| `Common DPs` | 2 |
| `Common OPs` | 30 |
| `Sample Relationship` | 2 |
| `System Capability` | 11 |

### Important Workbook Row / Cell Changes

| Sheet | Row | Source term | Changed cells | Summary |
|---|---:|---|---|---|
| `Common OPs` | 9 | `ssn:hasInput` | `D9`, `E9`, `F9` | Direct `subPropertyOf cco:has_input` replaced by source-level domain/range; rationale now says prior direct CCO mapping is removed/rejected. |
| `Common OPs` | 10 | `ssn:hasOutput` | `D10`, `E10`, `F10` | Direct `subPropertyOf cco:has_output` replaced by source-level domain/range; rationale now says prior direct CCO mapping is removed/rejected. |
| `Common OPs` | 27 | `sosa:madeActuation` | `E27`, `F27` | Direct `subPropertyOf cco:agent_in` replaced by source-level domain/range; rationale documents paired actuation-agent deferral. |
| `Common OPs` | 28 | `sosa:madeByActuator` | `E28`, `F28` | Source-level domain/range and inverse note recorded; direct CCO has-agent mapping remains deferred. |
| `Common OPs` | 33 | `sosa:observedProperty` | `E33`, `F33` | Direct `cco:has_input` mapping removed; source-level domain/range retained with rationale. |
| `System Capability` | 3 | `ssn-system:ActuationRange` | `D3`, `E3`, `F3` | Class expression simplified by removing the overstrong `affects some ProcessProfile` branch. |
| `System Capability` | 9 | `ssn-system:hasOperatingProperty` | `E9`, `F9` | Direct BFO dependence mapping replaced by source-level domain/range; rationale says BFO dependence entailment is not active OWL. |
| `System Capability` | 11 | `ssn-system:hasSurvivalProperty` | `E11`, `F11` | Direct BFO dependence mapping replaced by source-level domain/range; rationale says BFO dependence entailment is not active OWL. |
| `System Capability` | 14 | `ssn-system:hasSystemProperty` | `E14`, `F14` | Direct BFO dependence mapping replaced by source-level domain/range; rationale says BFO dependence entailment is not active OWL. |
| `System Capability` | 29 | `ssn-system:SurvivalRange` | `E29`, `F29` | Active class-expression mapping cleared; rationale documents HermiT-driven deferral. |
| `System Capability` | 32 | `ssn-system:SystemProperty` | `D32`, `E32`, `F32` | Direct class-expression mapping cleared; rationale says broader target is inherited via `ssn:Property` and `prescribed_by` branch was over-specific. |

Other `Common OPs` rows were updated to record source-level domain/range operationalization, inverse-side mapping documentation, or audit-alignment rationale. `Common Classes` updates include Sampler/Actuator/Procedure mapping cleanup. `Common DPs` and `Sample Relationship` changes are audit/documentation cleanup rather than new active release blockers.

`Common Classes` row 18 for `sosa:Sensor` is not resolved by this diff. It remains intentionally version-aligned differently from the active TTL mapping.

## Mapping Audit Comparison

The current `tools/compare_mappings.py` worked against both the extracted BASE files and the current HEAD files.

BASE command:

```bash
python tools/compare_mappings.py \
  --ttl /tmp/ssn-to-bfo-overall-ttl-workbook-diff/base-SSN2BFO.ttl \
  --spreadsheet /tmp/ssn-to-bfo-overall-ttl-workbook-diff/base-workbook.xlsx \
  --output-md /tmp/ssn-to-bfo-overall-ttl-workbook-diff/base-audit.md \
  --output-csv /tmp/ssn-to-bfo-overall-ttl-workbook-diff/base-audit.csv
```

HEAD command:

```bash
python tools/compare_mappings.py \
  --ttl SSN2BFO.ttl \
  --spreadsheet "Current_SOSA-SSN to BFO-CCO.xlsx" \
  --output-md /tmp/ssn-to-bfo-overall-ttl-workbook-diff/head-audit.md \
  --output-csv /tmp/ssn-to-bfo-overall-ttl-workbook-diff/head-audit.csv
```

| Audit item | BASE | HEAD | Change |
|---|---:|---:|---:|
| inspected sheets | 5 | 5 | 0 |
| spreadsheet rows | 93 | 93 | 0 |
| `ttl_candidate_mapping_assertions` | 73 | 68 | -5 |
| total audit issues | 37 | 2 | -35 |
| `missing_in_spreadsheet` | 15 | 1 | -14 |
| `missing_in_ttl` | 16 | 1 | -15 |
| `target_mismatch` | 4 | 0 | -4 |
| `needs_human_review` | 1 | 0 | -1 |
| `prefix_or_iri_issue` | 1 | 0 | -1 |

HEAD audit issues are only the known expected `sosa:Sensor` version-alignment issues:

```text
ISSUE-0001 missing_in_spreadsheet:
sosa:Sensor => bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Observation; cco:ont00001787

ISSUE-0002 missing_in_ttl:
Common Classes row 18:
sosa:Sensor => bfo:BFO_0000040; bfo:BFO_0000196; cco:ont00000569
```

## Current Validation Baseline

Command run:

```bash
python tools/run_validation_suite.py
```

Current result:

| Check / count | HEAD result |
|---|---:|
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 68 |
| mapping audit issues | 2 expected `sosa:Sensor` issues |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 75 |
| property-chain expectations | 5 |
| restriction expectations | 2 |
| uncovered active direct mappings | 0 |
| uncovered active property-chain mappings | 0 |
| uncovered active restriction mappings | 0 |
| full local SOSA closure HermiT triple count | 15769 |
| HermiT return code | 0 |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |

## Interpretation

### Biggest TTL Changes

The largest TTL changes are:

1. addition of source-level `rdfs:domain` / `rdfs:range` operationalization across SOSA/SSN/SSN Systems properties;
2. removal or deferral of direct CCO/BFO property mappings that were unsafe under HermiT diagnostics;
3. simplification or deferral of overstrong class-expression mappings in the SSN Systems area;
4. addition of a few direct/property-chain mappings that were reviewed and made audit-covered, such as `ssn:hasSubSystem`, `ssn:implementedBy`, and `sosa:observes`;
5. preservation of the active `sosa:Sensor` TTL mapping while documenting the workbook mismatch as intentional.

### Biggest Workbook Changes

The workbook changes are concentrated in `Common OPs` and `System Capability`:

- many object-property rows now record source-level domain/range operationalization;
- old direct CCO/BFO mappings now have rationale saying they are removed, rejected, or deferred;
- SSN Systems rows were updated to separate source-level typing from inactive BFO dependence entailments;
- `SystemProperty`, `SurvivalRange`, and selected system-property class-expression rows were cleared or simplified;
- the `sosa:Sensor` workbook mismatch remains intentionally unresolved.

### Active Mapping Changes

Changes affecting active mappings include:

- direct actuation-side CCO agent mappings were removed;
- direct input/output CCO mappings were removed/rejected;
- direct `observedProperty -> cco:has_input` was removed;
- direct SSN Systems dependence subproperty mappings were removed/deferred;
- source-level domain/range axioms were added;
- `sosa:madeByActuator rdfs:range sosa:Actuator` was added after the CCO agent mappings were deferred;
- several class-expression mappings were simplified or deferred.

### Documentation / Rationale-Only Changes

Many workbook `F` cell changes are rationale-only. These explain why a mapping is active, source-level only, rejected, or deferred. Examples include:

- `ssn:hasInput` and `ssn:hasOutput` rationale now says the prior direct CCO mappings are removed/rejected;
- actuation-agent rows now explain the paired HermiT-safety deferral;
- SSN Systems property rows now state that BFO dependence entailment is not active OWL;
- `SystemProperty` rationale now explains inherited broader typing and the over-specific `prescribed_by` branch.

### Source-Level Fidelity Changes

Source-level fidelity improved materially through the 62 active source-level domain/range triples now present in HEAD. These encode source ontology typing for properties without adding BFO/CCO domain/range shortcuts.

### HermiT / Full-Closure Safety Changes

The cleanup sequence made the current graph materially safer for full-OWL reasoning:

- unsafe direct CCO/BFO property mappings were removed or deferred;
- `imports/sosa.ttl` was materialized outside this two-file diff, changing the effective validation profile;
- the validation suite now includes full local SOSA closure HermiT;
- current HEAD is HermiT-clean under full local SOSA closure with unsat count 0.

### Audit / Tooling Alignment Changes

The mapping audit moved from 37 BASE issues to 2 HEAD issues. The two remaining issues are intentionally documented expected `sosa:Sensor` version-alignment issues.

### Known Differences Intentionally Unresolved

The main intentionally unresolved difference is `sosa:Sensor`:

- TTL keeps the current explicit local CCO-compatible subclass expression;
- workbook row 18 remains forward-looking / latest-CCO-oriented and points to `cco:Sensor`;
- both tested Sensor variants were HermiT-clean, so this is a version/modeling-policy issue rather than a current consistency failure.

Other intended limitations remain documented:

- deferred actuation-side CCO agent mappings;
- rejected input/output CCO direct mappings;
- deferred `sosa:observedProperty` direct CCO mapping;
- deferred SSN Systems BFO dependence entailments.

### Release Readiness

The current state is materially safer and more release-ready than BASE because:

- validation now includes parse, mapping audit, instance smoke tests, ELK entailment coverage, and full local SOSA closure HermiT;
- active mapping expectations are covered with zero uncovered active mappings in the ELK test profile;
- the full local SOSA closure is HermiT-clean;
- audit noise dropped from 37 issues to 2 expected issues;
- known limitations are documented rather than hidden in mismatched TTL/workbook state.

This does not mean tracked release artifacts are populated. Release-readiness still depends on preparing `releases/current-ssn-sosa` artifacts or explicitly releasing `SSN2BFO.ttl` as the source artifact with notes.

## Validation

Required validation commands:

```bash
rm -f catalog-v001.xml

python tools/workflow_check.py --mode report-only \
  --expected-file reports/overall-ttl-workbook-diff-since-baseline.md

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
- Expected changed file set: only `reports/overall-ttl-workbook-diff-since-baseline.md`.
