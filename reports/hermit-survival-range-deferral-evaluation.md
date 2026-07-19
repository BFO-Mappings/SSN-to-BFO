# HermiT SurvivalRange Deferral Evaluation

## Scope

This is an evaluation report for temporarily deferring only the active `ssn-system:SurvivalRange` OWL class-expression mapping.

This is not a final semantic correction claim. The goal was to quantify validation and HermiT impact before deciding whether a final fix branch should defer this mapping.

Temporary HermiT files were written under:

```text
/tmp/ssn-to-bfo-survival-range-deferral-evaluation
```

## Temporary Repo Changes Evaluated

### TTL Change

In `SSN2BFO.ttl`, the active logical class-expression mapping for `ssn-system:SurvivalRange` was deferred.

Before, `ssn-system:SurvivalRange` had an active `rdfs:subClassOf` class expression equivalent in summary to:

```text
subClassOf bfo:Function
  and bfo:has_realization some
    (bfo:Process
     and cco:caused_by some
       (bfo:Process
        and bfo:realizes some
          (cco:Affordance
           and cco:prescribed_by some cco:ArtifactDesign)))
```

After, the block is only:

```ttl
<http://www.w3.org/ns/ssn/systems/SurvivalRange> rdf:type owl:Class .
# Direct OWL class mapping deferred pending HermiT-safe rule/COMS treatment.
```

No other SSN Systems class mapping was edited.

### Spreadsheet Change

Workbook:

```text
Current_SOSA-SSN to BFO-CCO.xlsx
```

Sheet and row:

```text
System Capability row 29
source term: ssn-system:SurvivalRange
```

Cell changes verified against `HEAD`:

| Cell | Before | After |
| --- | --- | --- |
| `System Capability!E29` | `subClassOf bfo:Function and bfo:has_realization some (bfo:Process and cco:caused_by some (bfo:Process and bfo:realizes some (cco:Affordance and cco:prescribed_by some cco:ArtifactDesign)))` | blank |
| `System Capability!F29` | Existing rationale for modeling `SurvivalRange` as a function | Temporary deferral rationale noting that intended semantics remain, HermiT diagnostics identify `SurvivalRange` as high-impact in the mixed `ssn:hasProperty` / `hasSurvivalProperty` / non-sample `sosa:` context, the evaluation does not prove semantic wrongness, and future representation should be reviewed for HermiT-safe OWL or rule/COMS treatment |

The workbook value comparison found exactly these two value changes.

## Mapping Audit Result

The mapping audit was regenerated with:

```bash
python tools/compare_mappings.py --ttl SSN2BFO.ttl --spreadsheet "Current_SOSA-SSN to BFO-CCO.xlsx" --output-md reports/mapping-consistency-audit.md --output-csv reports/mapping-consistency-audit.csv
```

Result:

```text
inspected_sheets=5
spreadsheet_rows=93
ttl_candidate_mapping_assertions=74
issues=2
missing_in_spreadsheet=1
missing_in_ttl=1
```

The two remaining issues are still the known expected `sosa:Sensor` version-alignment issues:

| Issue | Category | Source term | Notes |
| --- | --- | --- | --- |
| `ISSUE-0001` | `missing_in_spreadsheet` | `sosa:Sensor` | extra TTL mapping relative to spreadsheet |
| `ISSUE-0002` | `missing_in_ttl` | `sosa:Sensor` | spreadsheet row at `Common Classes` row 18 |

No new audit issues appeared.

The total TTL candidate mapping assertion count changed from 75 before the deferral to 74 after the deferral.

## ELK Instance Entailment Result

The ELK instance mapping entailment report was regenerated with:

```bash
python tools/test_elk_instance_mapping_entailments.py --output reports/elk-instance-mapping-entailments.md
```

Result:

```text
Example files tested: 16
ROBOT pass/fail: 16/0
Total direct class expectations checked: 6
Total direct property expectations checked: 112
Total property-chain expectations checked: 5
Total restriction expectations checked: 2
Total expectation failures: 0
Active direct mappings not covered by instance data: 0
Active property-chain mappings not covered by instance data: 0
Active restriction mappings not covered by instance data: 0
Summary: PASS
```

The removed `SurvivalRange` mapping was a blank-node class-expression mapping, not one of the direct named class mappings checked by the ELK instance entailment script.

Expectation count comparison:

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Direct named class mappings discovered | 4 | 4 | 0 |
| Direct named property mappings discovered | 26 | 26 | 0 |
| Direct class expectations checked | 6 | 6 | 0 |
| Direct property expectations checked | 112 | 112 | 0 |
| Property-chain expectations checked | 5 | 5 | 0 |
| Restriction expectations checked | 2 | 2 | 0 |
| Active direct mappings not covered | 0 | 0 | 0 |

## Standard Validation Results

The canonical report-writing validation suite was run:

```bash
python tools/run_validation_suite.py --write-reports
```

Result: PASS.

The default temporary-output validation suite was also run:

```bash
python tools/run_validation_suite.py
```

Result: PASS.

Both validation-suite runs recognized the expected two `sosa:Sensor` audit issues and reported no audit drift.

## HermiT Setup

For each HermiT variant, a temporary no-imports graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

The graph was then cleaned by removing:

```text
all owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty
sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

Reasoning command form:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

```text
ROBOT version 1.9.7
java version "22.0.2" 2024-07-16
```

The before-deferral variants used `HEAD:SSN2BFO.ttl`. The after-deferral variants used the working-tree `SSN2BFO.ttl`.

## HermiT Before/After Results

| Variant | Mapping state | Temporary graph | Triples | Return code | Reasoned output | `owl:Nothing` count | Sample simplicity blocker | Unsat count | Unsat classes |
| --- | --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| Before full M2 | `SurvivalRange` mapping active | full M2 cleanup graph | 15514 | 1 | no | n/a | no | 8 | `ssn-system:BatteryLifetime`, `ssn-system:SystemLifetime`, `ssn:Output`, `sosa:Sensor`, `ssn-system:SurvivalProperty`, `sosa:Observation`, `ssn:Stimulus`, `ssn:Input` |
| Before B2 systems-only | `SurvivalRange` mapping active | B2 targeted core reducer subjects removed | 15477 | 1 | no | n/a | no | 3 | `ssn-system:BatteryLifetime`, `ssn-system:SystemLifetime`, `ssn-system:SurvivalProperty` |
| After full M2 | `SurvivalRange` mapping deferred | full M2 cleanup graph | 15477 | 1 | no | n/a | no | 5 | `ssn:Output`, `sosa:Sensor`, `sosa:Observation`, `ssn:Stimulus`, `ssn:Input` |
| After B2 systems-only | `SurvivalRange` mapping deferred | B2 targeted core reducer subjects removed | 15440 | 0 | yes | 0 | no | 0 | none |

The after-deferral full M2 graph still has the known core SOSA/SSN five-class HermiT cluster, but the SSN Systems trio is removed.

The after-deferral B2 systems-only graph is HermiT-clean.

No new HermiT issue appeared in these variants.

## Deferred BFO Dependence Property Mapping Cross-Check

The already-deferred direct BFO dependence property mappings remain inactive after this evaluation:

| Mapping check | Active after deferral? |
| --- | --- |
| `ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194` | No |
| `ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194` | No |
| `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194` | No |

This evaluation does not reopen those property mappings.

## Assessment

The temporary deferral looks promising as a HermiT-focused final fix candidate:

- It removes the SSN Systems trio from the full M2 HermiT baseline.
- It makes the B2 systems-only reproduction HermiT-clean.
- It does not create new mapping-audit issues.
- It does not reduce ELK instance mapping coverage.
- It does not uncover any active direct mapping coverage gap.
- It leaves the already-deferred `BFO_0000194` property mappings inactive.

The result should still be read carefully. This evaluation shows that the active `SurvivalRange` OWL class-expression mapping is a high-impact dependency in the current full-OWL profile. It does not prove that the intended `SurvivalRange` semantics are wrong.

## Recommendation

This temporary deferral supports a final narrow fix branch, provided the final branch keeps the same scope:

- defer only the active `ssn-system:SurvivalRange` OWL class-expression mapping;
- update only the corresponding spreadsheet row;
- preserve the intended semantics as deferred review/rule/COMS work;
- do not alter comparable SSN Systems class mappings in the same branch;
- keep the core SOSA/SSN five-class HermiT cluster separate.

More explanation work may still be useful before designing a replacement mapping, especially to isolate the distributed non-sample `sosa:` mapping context involved in the mixed interaction.
