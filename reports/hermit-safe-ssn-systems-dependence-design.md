# HermiT-Safe SSN Systems Dependence Design

## Scope

This report evaluates replacement-representation options for the deferred SSN Systems dependence mappings:

```ttl
ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

The report is diagnostic and report-only. It does not edit `SSN2BFO.ttl`, the spreadsheet, imports, examples, tools, generated artifacts, or any ontology mapping file.

Controlling inputs:

- `reports/hermit-clean-baseline-after-deferrals.md`
- `reports/deferred-reactivation-results.md`
- `reports/ssn-systems-dependence-reactivation-results.md`
- `reports/hermit-hasOperatingProperty-reactivation-canary.md`
- `reports/hermit-hasSurvivalProperty-reactivation-canary.md`
- `reports/hermit-hasSystemProperty-reactivation-canary.md`
- `reports/hermit-hasProperty-domain-range-architecture.md`

## Current Stable Baseline

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

## Problem Statement

The old direct OWL mappings to `bfo:BFO_0000194` failed individual HermiT reactivation canaries:

| Mapping | Result | Unsats |
| --- | --- | --- |
| `ssn-system:hasOperatingProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:OperatingProperty`, `ssn-system:OperatingPowerRange`, `ssn-system:MaintenanceSchedule` |
| `ssn-system:hasSurvivalProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:BatteryLifetime`, `ssn-system:SystemLifetime`, `ssn-system:SurvivalProperty` |
| `ssn-system:hasSystemProperty -> bfo:BFO_0000194` | not HermiT-clean | `ssn-system:Latency`, `ssn-system:Accuracy`, `ssn-system:Precision`, `ssn-system:Sensitivity`, `ssn-system:SystemProperty`, `ssn-system:ResponseTime`, `ssn-system:Resolution`, `ssn-system:Selectivity`, `ssn-system:MeasurementRange`, `ssn-system:Frequency`, `ssn-system:DetectionLimit`, `ssn-system:ActuationRange`, `ssn-system:Drift` |

The intended semantics are still in scope:

```text
If range/capability x has property y, then y specifically depends on x.
```

The direct subproperty form has been treated as problematic in the current full-OWL profile. A proposed alternative is to test whether an inverse-property OWL expression can preserve the intended dependence direction while avoiding the HermiT unsatisfiability caused by the old direct representation.

Local BFO context from `imports/cco.ttl` records:

```text
bfo:BFO_0000194 = specifically depended on by
bfo:BFO_0000195 = specifically depends on
bfo:BFO_0000194 owl:inverseOf bfo:BFO_0000195
```

Modeling caution: in ordinary OWL semantics, `P rdfs:subPropertyOf [ owl:inverseOf bfo:BFO_0000194 ]` makes `P` a subproperty of the inverse of specifically depended on by, which is the specifically depends on direction. That syntax should be reviewed carefully before any final modeling branch. This report nevertheless tests it as the requested inverse-property candidate.

## Candidate Representations

### Candidate A: Current Deferred Baseline

Shape:

- no active BFO dependence mapping for the three SSN Systems property relations;
- intended semantics documented outside active OWL;
- rule/COMS treatment remains available.

HermiT result: clean, because this is the current baseline.

### Candidate B: Old Direct Mapping Control

Shape:

```ttl
ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

Result: not HermiT-clean. The individual canary reports already showed each direct reactivation fails. This report did not rerun the old direct control.

### Candidate C: Inverse-Property OWL Candidate

Shape tested in temporary graphs:

```ttl
<http://www.w3.org/ns/ssn/systems/hasOperatingProperty> rdfs:subPropertyOf [
  owl:inverseOf <http://purl.obolibrary.org/obo/BFO_0000194>
] .

<http://www.w3.org/ns/ssn/systems/hasSurvivalProperty> rdfs:subPropertyOf [
  owl:inverseOf <http://purl.obolibrary.org/obo/BFO_0000194>
] .

<http://www.w3.org/ns/ssn/systems/hasSystemProperty> rdfs:subPropertyOf [
  owl:inverseOf <http://purl.obolibrary.org/obo/BFO_0000194>
] .
```

This candidate was tested individually and as a group. It was not HermiT-clean in any tested variant.

### Candidate D: Annotation / Rule-Only Candidate

Shape:

- keep active OWL mappings deferred;
- document intended dependence semantics;
- implement inference outside active OWL through rule/COMS architecture.

HermiT result: clean by construction, because no new full-OWL dependence axiom is added.

Tradeoff: this preserves the clean OWL baseline but gives up direct OWL entailment of the intended BFO dependence assertion.

### Optional Candidate E: Local Bridge Relation

A local bridge relation could be introduced in a future design, but this report did not add one even in a temporary graph. A bridge property would need separate review because:

- an unconnected local bridge would not produce BFO dependence entailments by itself;
- connecting it to BFO dependence with active OWL axioms could reintroduce the same HermiT profile problem;
- rule/COMS treatment may be a cleaner way to use a bridge relation without forcing the active OWL profile to carry the entailment.

## HermiT Temporary Graph Setup

Each temporary graph was built from:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Each graph then removed:

- all `owl:imports` triples;
- `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Command form:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

## Variant Results

| Variant | Temporary graph | Candidate triples added | Triple count | Return code | Reasoned output | `owl:Nothing` count | Unsat count | Unsat set | Sample simplicity blocker |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- | --- |
| A baseline | `/tmp/ssn-to-bfo-hermit-safe-ssn-systems-dependence-design/A_baseline.ttl` | none | 15474 | 0 | yes | 0 | 0 | clean | no |
| C1 inverse `hasOperatingProperty` only | `/tmp/ssn-to-bfo-hermit-safe-ssn-systems-dependence-design/C1_inverse_hasOperatingProperty_only.ttl` | inverse-property candidate for `ssn-system:hasOperatingProperty` | 15476 | 1 | no | n/a | 3 | `ssn-system:OperatingProperty`, `ssn-system:OperatingPowerRange`, `ssn-system:MaintenanceSchedule` | no |
| C2 inverse `hasSurvivalProperty` only | `/tmp/ssn-to-bfo-hermit-safe-ssn-systems-dependence-design/C2_inverse_hasSurvivalProperty_only.ttl` | inverse-property candidate for `ssn-system:hasSurvivalProperty` | 15476 | 1 | no | n/a | 3 | `ssn-system:BatteryLifetime`, `ssn-system:SystemLifetime`, `ssn-system:SurvivalProperty` | no |
| C3 inverse `hasSystemProperty` only | `/tmp/ssn-to-bfo-hermit-safe-ssn-systems-dependence-design/C3_inverse_hasSystemProperty_only.ttl` | inverse-property candidate for `ssn-system:hasSystemProperty` | 15476 | 1 | no | n/a | 13 | `ssn-system:Latency`, `ssn-system:Accuracy`, `ssn-system:Precision`, `ssn-system:Sensitivity`, `ssn-system:ResponseTime`, `ssn-system:SystemProperty`, `ssn-system:Resolution`, `ssn-system:MeasurementRange`, `ssn-system:Frequency`, `ssn-system:Selectivity`, `ssn-system:DetectionLimit`, `ssn-system:ActuationRange`, `ssn-system:Drift` | no |
| C4 inverse all three | `/tmp/ssn-to-bfo-hermit-safe-ssn-systems-dependence-design/C4_inverse_all_three.ttl` | inverse-property candidates for all three relations | 15480 | 1 | no | n/a | 19 | `ssn-system:Latency`, `ssn-system:Accuracy`, `ssn-system:Precision`, `ssn-system:Sensitivity`, `ssn-system:OperatingPowerRange`, `ssn-system:BatteryLifetime`, `ssn-system:ResponseTime`, `ssn-system:SystemProperty`, `ssn-system:SystemLifetime`, `ssn-system:Resolution`, `ssn-system:Selectivity`, `ssn-system:Frequency`, `ssn-system:MeasurementRange`, `ssn-system:SurvivalProperty`, `ssn-system:OperatingProperty`, `ssn-system:DetectionLimit`, `ssn-system:MaintenanceSchedule`, `ssn-system:ActuationRange`, `ssn-system:Drift` | no |

## Evaluation

| Candidate | HermiT-clean? | Directional fit | Preserves clean baseline? | OWL mapping candidate? | Rule/COMS candidate? |
| --- | --- | --- | --- | --- | --- |
| A. Current deferred baseline | yes | preserves intent only as documentation/out-of-band semantics | yes | no active OWL entailment | yes |
| B. Old direct mapping | no | intended semantics remain, but representation failed HermiT canaries | no | no, not in current profile | possible replacement needed |
| C. Inverse-property OWL candidate | no | requires modeling review; syntax points to inverse of `BFO_0000194` | no | no, not HermiT-safe in tested form | possible replacement needed |
| D. Annotation/rule-only | yes by construction | can encode the intended flipped dependence outside OWL | yes | no active OWL entailment | yes |
| E. Local bridge relation | not tested | depends on bridge design | unknown | requires separate temporary-graph testing | possible |

The inverse-property candidate did not improve on the old direct mapping. It reintroduced the same individual unsat clusters for `hasOperatingProperty`, `hasSurvivalProperty`, and `hasSystemProperty`, and the grouped variant reintroduced the union of those SSN Systems clusters.

## Recommendation

Do not create a mapping-change branch for the tested inverse-property candidate.

Keep the three SSN Systems dependence mappings deferred for now:

```ttl
ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:BFO_0000194 .
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

The old direct representation failed, and the tested inverse-property representation also failed individually and as a group. Future work should therefore focus on rule/COMS treatment or a different redesigned OWL representation tested first in temporary HermiT graphs.

No branch such as `fix/use-inverse-dependence-for-ssn-systems-properties` is recommended from this result.

Recommended next step:

```text
review/design-rule-coms-ssn-systems-dependence-treatment
```

That branch should focus on documenting or designing the rule/COMS representation of the intended inference:

```text
If range/capability x has property y, then y specifically depends on x.
```

without adding active BFO dependence subproperty axioms to `SSN2BFO.ttl`.
