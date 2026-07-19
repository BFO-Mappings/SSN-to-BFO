# SSN Systems Property Split Mapping Review

## Scope

This report reviews the current active mappings for six narrower SSN Systems subproperties of `ssn:hasProperty`:

- `ssn-system:hasOperatingProperty`
- `ssn-system:hasOperatingRange`
- `ssn-system:hasSurvivalProperty`
- `ssn-system:hasSurvivalRange`
- `ssn-system:hasSystemCapability`
- `ssn-system:hasSystemProperty`

The core question is whether each narrower relation has a fixed BFO relation pattern that can remain an active OWL `rdfs:subPropertyOf` mapping, or whether it has the same mixed conditional-pattern problem as generic `ssn:hasProperty`.

No ontology, spreadsheet, import, generated, or existing report files were changed. Temporary ELK files were written only under `/tmp/ssn-to-bfo-systems-property-split-review`.

## Files Inspected

- `SSN2BFO.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `imports/cco.ttl`
- `reports/ssn-hasproperty-modeling-options.md`
- `reports/ssn-hasproperty-disjunctive-domain-range-candidate.md`
- `reports/ssn-hasproperty-rule-mapping-artifact.md`
- `rules/ssn-hasproperty-conditional-mapping.rq`
- `reports/reasoner-diagnostic-report.md`
- `reports/reasoner-unsafe-system-mapping-deferral.md`
- `reports/reasoner-safe-replacement-mapping-review.md`
- `reports/mapping-consistency-audit.md`
- `reports/remaining-audit-disposition.md`
- `reports/instance-data-smoke-test.md`

Local search covered:

- `hasOperatingProperty`
- `hasOperatingRange`
- `hasSurvivalProperty`
- `hasSurvivalRange`
- `hasSystemCapability`
- `hasSystemProperty`
- `OperatingProperty`
- `OperatingRange`
- `SurvivalProperty`
- `SurvivalRange`
- `SystemCapability`
- `SystemProperty`

## Current TTL Mappings

`SSN2BFO.ttl` currently maps the six SSN Systems properties as follows:

| Property | Current active TTL mapping |
| --- | --- |
| `ssn-system:hasOperatingProperty` | `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on |
| `ssn-system:hasOperatingRange` | `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of |
| `ssn-system:hasSurvivalProperty` | `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on |
| `ssn-system:hasSurvivalRange` | `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of |
| `ssn-system:hasSystemCapability` | `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of |
| `ssn-system:hasSystemProperty` | `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on |

Generic `ssn:hasProperty` remains unmapped in `SSN2BFO.ttl`.

## Spreadsheet Evidence

The six rows are all on the `System Capability` sheet of `Current_SOSA-SSN to BFO-CCO.xlsx`:

| Property | Sheet row | Spreadsheet OWL axiom | Spreadsheet rationale summary |
| --- | ---: | --- | --- |
| `ssn-system:hasOperatingProperty` | 9 | `ssn-system:hasOperatingProperty rdfs:subPropertyOf bfo:specifically_depends_on .` | OperatingProperty is described as a determinate refinement of an OperatingRange and as specifically depending on that range. |
| `ssn-system:hasOperatingRange` | 10 | `ssn-system:hasOperatingRange rdfs:subPropertyOf bfo:bearer_of .` | A System bears an operating-range specification that characterizes normal operating conditions. |
| `ssn-system:hasSurvivalProperty` | 11 | `ssn-system:hasSurvivalProperty rdfs:subPropertyOf bfo:specifically_depends_on .` | SurvivalProperty is described as refining or parameterizing a SurvivalRange. |
| `ssn-system:hasSurvivalRange` | 12 | `ssn-system:hasSurvivalRange rdfs:subPropertyOf bfo:bearer_of .` | A System bears a survival-range specification. |
| `ssn-system:hasSystemCapability` | 13 | `ssn-system:hasSystemCapability rdfs:subPropertyOf bfo:bearer_of .` | SystemCapability is modeled as a specifically dependent continuant inhering in the system. |
| `ssn-system:hasSystemProperty` | 14 | `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:specifically_depends_on .` | SystemProperty is described as a determinate refinement of a SystemCapability and as specifically depending on it. |

The spreadsheet supports the current split in broad outline. The three `bfo:BFO_0000195` rows still need careful directionality review because `specifically_depends_on` runs from the dependent entity to the dependence target.

## Source Ontology Evidence

`imports/ssn-systems.ttl` declares all six properties as `rdfs:subPropertyOf ssn:hasProperty`. None of the six has a direct `rdfs:domain` or `rdfs:range` triple in the inspected source or current `SSN2BFO.ttl`.

Expected subject/object patterns are recoverable from labels, definitions, and class restrictions:

| Property | Source label | Source definition/comment | Source subject/object pattern |
| --- | --- | --- | --- |
| `ssn-system:hasOperatingProperty` | has operating property | Relation from an OperatingRange of a System to an OperatingProperty describing the operating range of the System. | `OperatingRange -> OperatingProperty`; both are subclasses of `ssn:Property`. |
| `ssn-system:hasOperatingRange` | has operating range | Relation from a System to an OperatingRange describing the normal operating environment of the System. | `System -> OperatingRange`; `ssn:System` has all values from `OperatingRange`; `OperatingRange` has inverse all values from `System`. |
| `ssn-system:hasSurvivalProperty` | has survival property | Relation from a SurvivalRange of a System to a SurvivalProperty describing the survival range of the System. | `SurvivalRange -> SurvivalProperty`; both are subclasses of `ssn:Property`. |
| `ssn-system:hasSurvivalRange` | has survival range | Relation from a System to a SurvivalRange. | `System -> SurvivalRange`; `ssn:System` has all values from `SurvivalRange`; `SurvivalRange` has inverse all values from `System`. |
| `ssn-system:hasSystemCapability` | has system capability | Relation from a System to a SystemCapability describing the capabilities of the System under certain Conditions. | `System -> SystemCapability`; `ssn:System` has all values from `SystemCapability`; `SystemCapability` has inverse all values from `System`. |
| `ssn-system:hasSystemProperty` | has system property | Relation from a SystemCapability of a System to a SystemProperty describing the capabilities of the System. | `SystemCapability -> SystemProperty`; both are subclasses of `ssn:Property`. |

The source ontology therefore separates two patterns:

- System-to-range/capability: `System -> OperatingRange`, `System -> SurvivalRange`, `System -> SystemCapability`.
- Dependent-entity-to-dependent-entity refinement: `OperatingRange -> OperatingProperty`, `SurvivalRange -> SurvivalProperty`, `SystemCapability -> SystemProperty`.

## Local BFO Evidence

The current targets are local BFO object properties from `imports/cco.ttl`:

| IRI | Label | Directionality evidence |
| --- | --- | --- |
| `bfo:BFO_0000196` | bearer of | Domain is independent continuant excluding spatial region; range is specifically dependent continuant. Definition: `b bearer of c =Def c inheres in b`. Direction: bearer to dependent entity. |
| `bfo:BFO_0000195` | specifically depends on | Domain is specifically dependent continuant; range is specifically dependent continuant or independent continuant excluding spatial region. Direction: dependent entity to its dependence target. |

The directionality caution is decisive:

- `bearer_of` runs from bearer to specifically dependent continuant.
- `specifically_depends_on` runs from specifically dependent continuant to what it depends on.

## Per-Property Review

### `ssn-system:hasOperatingProperty`

- Current TTL mapping: `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on.
- Spreadsheet row: `System Capability` row 9.
- Source pattern: `OperatingRange -> OperatingProperty`.
- Directionality analysis: The source relation runs from a range-like dependent entity to another dependent entity that describes it. If `OperatingProperty` is the determinate refinement that depends on `OperatingRange`, then a direct `hasOperatingProperty subPropertyOf specifically_depends_on` is directionally reversed. If instead the intended model is that an OperatingRange depends on the OperatingProperty entries that parameterize it, the mapping could be directionally plausible. The current evidence does not fully settle that.
- Classification: semantically plausible but needs review.
- Reasoner status: appears ELK-safe in the current baseline.
- Semantic risk: medium. The risk is not the mixed continuant/occurrent problem of generic `ssn:hasProperty`; it is dependency direction and whether the `has...Property` relation should be a BFO dependence relation at all.
- Conservative recommendation: keep but mark for review. Do not replace mechanically. If human review confirms the object depends on the subject rather than the subject depends on the object, defer/remove the active OWL mapping and handle the richer pattern through a rule/COMS artifact.

### `ssn-system:hasOperatingRange`

- Current TTL mapping: `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of.
- Spreadsheet row: `System Capability` row 10.
- Source pattern: `System -> OperatingRange`.
- Directionality analysis: The source relation runs from a system to a range/specification-like dependent entity. This matches the BFO `bearer_of` direction if the System is an independent continuant and the OperatingRange is a specifically dependent continuant.
- Classification: fixed OWL-safe BFO pattern.
- Reasoner status: appears ELK-safe in the current baseline.
- Semantic risk: low to medium. ELK-clean does not prove that every SSN System is the right kind of independent continuant or that every OperatingRange is best treated as a specifically dependent continuant, but the direction is coherent with the spreadsheet and source restrictions.
- Conservative recommendation: keep as active OWL mapping.

### `ssn-system:hasSurvivalProperty`

- Current TTL mapping: `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on.
- Spreadsheet row: `System Capability` row 11.
- Source pattern: `SurvivalRange -> SurvivalProperty`.
- Directionality analysis: Like `hasOperatingProperty`, this runs from a range-like dependent entity to a more specific property. If `SurvivalProperty` depends on the `SurvivalRange`, the active direct mapping is directionally reversed. If the intended model is that the SurvivalRange depends on the SurvivalProperty entries that parameterize it, the mapping could be directionally plausible. The source text alone does not make that dependency direction explicit.
- Classification: semantically plausible but needs review.
- Reasoner status: appears ELK-safe in the current baseline.
- Semantic risk: medium. This does not appear to be the mixed conditional pattern of generic `ssn:hasProperty`, but the dependency direction needs human confirmation.
- Conservative recommendation: keep but mark for review. Do not replace mechanically.

### `ssn-system:hasSurvivalRange`

- Current TTL mapping: `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of.
- Spreadsheet row: `System Capability` row 12.
- Source pattern: `System -> SurvivalRange`.
- Directionality analysis: The relation runs from system to range/specification-like dependent entity. This matches `bearer_of` if the System bears the SurvivalRange as a specifically dependent continuant.
- Classification: fixed OWL-safe BFO pattern.
- Reasoner status: appears ELK-safe in the current baseline.
- Semantic risk: low to medium. The direction is coherent, but the exact metaphysics of treating SurvivalRange as a specifically dependent continuant should remain reviewable.
- Conservative recommendation: keep as active OWL mapping.

### `ssn-system:hasSystemCapability`

- Current TTL mapping: `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of.
- Spreadsheet row: `System Capability` row 13.
- Source pattern: `System -> SystemCapability`.
- Directionality analysis: The relation runs from system to capability. This is a fixed bearer-to-dependent-entity pattern if SystemCapability is modeled as a specifically dependent continuant inhering in the System.
- Classification: fixed OWL-safe BFO pattern.
- Reasoner status: appears ELK-safe in the current baseline.
- Semantic risk: low to medium. This is coherent with the spreadsheet, but capability modeling should remain reviewable because capabilities can be treated as dispositions/functions/specifications depending on modeling context.
- Conservative recommendation: keep as active OWL mapping.

### `ssn-system:hasSystemProperty`

- Current TTL mapping: `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on.
- Spreadsheet row: `System Capability` row 14.
- Source pattern: `SystemCapability -> SystemProperty`.
- Directionality analysis: The source relation runs from capability to property. The spreadsheet says SystemProperty is a determinate refinement of SystemCapability and specifically depends on it. If so, the direct active mapping is directionally reversed because it asserts `SystemCapability specifically_depends_on SystemProperty`. If the intended model is that the broader capability depends on its property parameters, the direction could be plausible, but this is not established by the source definition alone.
- Classification: semantically plausible but needs review.
- Reasoner status: appears ELK-safe in the current baseline.
- Semantic risk: medium to high among the six reviewed properties because the spreadsheet's natural-language explanation points strongly toward object-to-subject dependence while the active `rdfs:subPropertyOf` mapping enforces subject-to-object dependence.
- Conservative recommendation: keep but mark for review. If human review confirms the spreadsheet natural-language direction, defer/remove the active OWL mapping and represent the intended refinement relation through a rule/COMS artifact rather than a direct OWL subproperty mapping.

## ELK Baseline Check

An optional temporary ELK check was run under:

```text
/tmp/ssn-to-bfo-systems-property-split-review
```

Temporary merged graph inputs:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

Removed from the temporary graph:

- all `owl:imports` triples;
- `sosa:isSampleOf rdf:type owl:FunctionalProperty`.

Command pattern:

```bash
robot reason --reasoner ELK --input /tmp/ssn-to-bfo-systems-property-split-review/current-split-baseline.ttl --output /tmp/ssn-to-bfo-systems-property-split-review/current-split-baseline-reasoned.ttl
```

Result:

| Check | Result |
| --- | --- |
| ROBOT version | 1.9.7 |
| ROBOT status | 0 |
| `owl:Nothing` count | 0 |
| Notes | The same OWLAPI parser messages about `http://org.semanticweb.owlapi/error#ErrorN` appeared as in prior baseline runs. |

This supports the claim that the current split mappings sit inside the current ELK-clean baseline. It does not prove that every mapping is semantically correct.

## Classification Summary

| Property | Current target | Classification | Reasoner-safe? | Semantic risk | Recommendation |
| --- | --- | --- | --- | --- | --- |
| `ssn-system:hasOperatingProperty` | `bfo:BFO_0000195` | semantically plausible but needs review | Appears yes | Medium | Keep but mark for review. |
| `ssn-system:hasOperatingRange` | `bfo:BFO_0000196` | fixed OWL-safe BFO pattern | Appears yes | Low to medium | Keep as active OWL mapping. |
| `ssn-system:hasSurvivalProperty` | `bfo:BFO_0000195` | semantically plausible but needs review | Appears yes | Medium | Keep but mark for review. |
| `ssn-system:hasSurvivalRange` | `bfo:BFO_0000196` | fixed OWL-safe BFO pattern | Appears yes | Low to medium | Keep as active OWL mapping. |
| `ssn-system:hasSystemCapability` | `bfo:BFO_0000196` | fixed OWL-safe BFO pattern | Appears yes | Low to medium | Keep as active OWL mapping. |
| `ssn-system:hasSystemProperty` | `bfo:BFO_0000195` | semantically plausible but needs review | Appears yes | Medium to high | Keep but mark for review. |

None of the six reviewed properties appears to have the same mixed continuant-or-occurrent conditional-pattern problem as generic `ssn:hasProperty`. The problem for the three `bfo:BFO_0000195` mappings is narrower: dependency direction and whether a direct OWL subproperty assertion is the right representation for a refinement/parameterization relation.

## Final Recommendation

Keep the current split pattern unchanged for now.

The three `bearer_of` mappings are coherent fixed-pattern mappings and should remain active:

- `ssn-system:hasOperatingRange`
- `ssn-system:hasSurvivalRange`
- `ssn-system:hasSystemCapability`

The three `specifically_depends_on` mappings should remain for now only because they are part of the current ELK-clean baseline and are supported by the spreadsheet at the axiom level. They should be explicitly marked for human modeling review:

- `ssn-system:hasOperatingProperty`
- `ssn-system:hasSurvivalProperty`
- `ssn-system:hasSystemProperty`

If review confirms that their intended dependence direction is object-to-subject, they should not be repaired by forcing a new direct OWL subproperty mapping. They should be deferred or moved into the same rule/query plus later COMS annotation architecture now used for generic `ssn:hasProperty`.

Do not reintroduce a generic active mapping on `ssn:hasProperty`.
