# HermiT Clean Baseline After Deferrals

## Context

This report documents the current cumulative HermiT-clean baseline after the merged mapping deferrals.

Repository context at report generation:

| Field | Value |
| --- | --- |
| Branch | `review/document-hermit-clean-baseline` |
| Commit | `ea55ac43cbf54473542c46ad64aaae560a158ece` |
| Report file | `reports/hermit-clean-baseline-after-deferrals.md` |

Before this report was created, the working tree was clean.

## Standard Validation Baseline

The standard validation suite was run with:

```bash
python tools/run_validation_suite.py
```

Result:

```text
Validation suite: PASS
```

Current validation baseline:

| Check | Current result |
| --- | ---: |
| TTL candidate mapping assertions | 71 |
| audit issues | 2 |
| `missing_in_spreadsheet` | 1 |
| `missing_in_ttl` | 1 |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 77 |
| property-chain expectations | 5 |
| restriction expectations | 2 |
| expectation failures | 0 |
| active direct mappings not covered | 0 |
| active property-chain mappings not covered | 0 |
| active restriction mappings not covered | 0 |

The only mapping-audit issues are the expected `sosa:Sensor` version-alignment issues:

| Issue | Category | Source |
| --- | --- | --- |
| `ISSUE-0001` | `missing_in_spreadsheet` | `sosa:Sensor` |
| `ISSUE-0002` | `missing_in_ttl` | `sosa:Sensor`, `Common Classes` row 18 |

These audit issues are separate from HermiT cleanliness.

## Current Deferred OWL Mappings

The following mappings are currently deferred as active OWL mappings. They are not active logical `rdfs:subPropertyOf` or class-expression mappings in `SSN2BFO.ttl`.

| Deferred mapping | Current status |
| --- | --- |
| `ssn-system:hasOperatingProperty -> bfo:BFO_0000194` | inactive; direct OWL mapping deferred |
| `ssn-system:hasSurvivalProperty -> bfo:BFO_0000194` | inactive; direct OWL mapping deferred |
| `ssn-system:hasSystemProperty -> bfo:BFO_0000194` | inactive; direct OWL mapping deferred |
| `ssn-system:SurvivalRange` class-expression mapping | inactive; direct OWL class mapping deferred |
| `ssn:hasInput -> cco:ont00001921` | inactive; direct OWL property mapping deferred |
| `ssn:hasOutput -> cco:ont00001986` | inactive; direct OWL property mapping deferred |
| `sosa:observedProperty -> cco:ont00001921` | inactive; direct OWL property mapping deferred |

The corresponding TTL areas contain short non-logical deferral comments. The source/import property hierarchy in `imports/` was not modified by these deferrals.

## HermiT M2 Clean-Baseline Test

The HermiT M2 test graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Temporary graph preparation:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

The temporary graph was written to:

```text
/tmp/ssn-to-bfo-hermit-clean-baseline-after-deferrals/m2-clean-baseline.ttl
```

The reasoned output path was:

```text
/tmp/ssn-to-bfo-hermit-clean-baseline-after-deferrals/m2-clean-baseline-reasoned.ttl
```

Command:

```bash
robot reason --reasoner HermiT --input /tmp/ssn-to-bfo-hermit-clean-baseline-after-deferrals/m2-clean-baseline.ttl --output /tmp/ssn-to-bfo-hermit-clean-baseline-after-deferrals/m2-clean-baseline-reasoned.ttl
```

Result:

| Field | Result |
| --- | --- |
| triple count before reasoning | 15474 |
| HermiT return code | 0 |
| reasoned output produced | yes |
| `owl:Nothing` count | 0 |
| unsat count | 0 |
| unsat set | clean |
| sample simplicity blocker reappeared | no |

This is the expected clean result for the current cumulative deferral baseline.

## Interpretation

This report shows that the current M2-style integration graph is HermiT-clean under the established cleanup conditions:

- `owl:imports` triples removed from the temporary merged graph;
- `sosa:isSampleOf rdf:type owl:FunctionalProperty` removed from the temporary graph;
- `sosa:hasSample rdf:type owl:InverseFunctionalProperty` removed from the temporary graph.

It does not prove that all deferred mappings were semantically wrong. It also does not replace future OWL, rule, or COMS modeling review for the intended semantics behind the deferred mappings.

The value of this report is narrower: it provides a clean, reproducible HermiT baseline for future mapping changes.

## Recommended Discipline

Future mapping additions should preserve this HermiT-clean baseline.

Any reactivation of a deferred mapping should be evaluated one at a time with the same M2 HermiT setup before being treated as safe for the full-OWL profile.

The remaining `sosa:Sensor` mapping-audit version-alignment issues should continue to be handled separately from HermiT cleanliness.
