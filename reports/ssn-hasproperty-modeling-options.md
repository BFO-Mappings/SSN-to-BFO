# `ssn:hasProperty` Modeling Options

## Scope

This report is a focused local review of the deferred `ssn:hasProperty` mapping. It does not address `ssn-system:BatteryLifetime`, `ssn-system:MeasurementRange`, SampleRelationship, or HermiT/full OWL DL cleanup except where prior reports mention them as context for the `ssn:hasProperty` deferral.

No ontology, spreadsheet, import, generated, or existing report files were changed for this review. Temporary ELK test files were written only under `/tmp/ssn-to-bfo-hasproperty-options`.

## Files Inspected

- `SSN2BFO.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `imports/cco.ttl`
- `reports/reasoner-diagnostic-report.md`
- `reports/reasoner-unsafe-system-mapping-deferral.md`
- `reports/reasoner-safe-replacement-mapping-review.md`
- `reports/mapping-consistency-audit.md`
- `reports/remaining-audit-disposition.md`

Local search was performed for:

- `hasProperty`
- `isPropertyOf`
- `hasSystemProperty`
- `hasSystemCapability`
- `hasOperatingRange`
- `hasSurvivalRange`
- `ssn:Property`
- `SystemProperty`
- `SurvivalProperty`

## Current Status

### `SSN2BFO.ttl`

There is no active direct mapping for `ssn:hasProperty` in the current `SSN2BFO.ttl`.

The current mapping file does contain narrower SSN Systems subproperty mappings:

| SSN Systems property | Current target in `SSN2BFO.ttl` |
| --- | --- |
| `ssn-system:hasOperatingProperty` | `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on |
| `ssn-system:hasOperatingRange` | `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of |
| `ssn-system:hasSurvivalProperty` | `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on |
| `ssn-system:hasSurvivalRange` | `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of |
| `ssn-system:hasSystemCapability` | `rdfs:subPropertyOf bfo:BFO_0000196` / bearer of |
| `ssn-system:hasSystemProperty` | `rdfs:subPropertyOf bfo:BFO_0000195` / specifically depends on |

These narrower mappings are part of the current baseline tested below.

### Spreadsheet

In `Current_SOSA-SSN to BFO-CCO.xlsx`, sheet `Common OPs`, row 11:

- IRI: `ssn:hasProperty`
- Definition: "Relation between an entity and a Property of that entity."
- BFO definition: "A relation between a bfo:Continuant and a bfo:SpecificallyDependentContinuant, or between a bfo:Occurrent and a bfo:ProcessProfile."
- Natural language OWL: if an entity has_property an `ssn:Property`, then that property either inheres in that entity or is an occurrent part of the relevant process.
- OWL Axiom: blank.
- Reasoning: deferred after ELK testing; the prior dual mapping to `bfo:bearer_of` and `bfo:has_occurrent_part` made `ssn:hasProperty` unsatisfiable under ELK.

The spreadsheet row for `ssn:isPropertyOf`, sheet `Common OPs`, row 23, remains an inverse row:

```turtle
ssn:isPropertyOf owl:inverseOf ssn:hasProperty .
```

The audit report lists both `ssn:hasProperty` and `ssn:isPropertyOf` among skipped or partially parsed rows with no parsed expected assertions.

## Source Ontology Evidence

### `imports/ssn.ttl`

`ssn:hasProperty` is declared as an `owl:ObjectProperty` and has:

```turtle
ssn:hasProperty owl:inverseOf ssn:isPropertyOf ;
  rdfs:comment "Relation between an entity and a Property of that entity."@en ;
  rdfs:label "has property"@en ;
  skos:definition "Relation between an entity and a Property of that entity."@en .
```

No explicit `rdfs:domain` or `rdfs:range` triple is asserted directly on `ssn:hasProperty` in the inspected source block.

`ssn:isPropertyOf` is separately declared as an `owl:ObjectProperty` with:

```turtle
rdfs:comment "Relation between a Property and the entity it belongs to."@en ;
rdfs:label "is property of"@en ;
skos:definition "Relation between a Property and the entity it belongs to."@en .
```

`sosa:FeatureOfInterest` uses `ssn:hasProperty` in restrictions:

```turtle
sosa:FeatureOfInterest rdfs:subClassOf [
  owl:onProperty ssn:hasProperty ;
  owl:allValuesFrom ssn:Property
] ,
[
  owl:onProperty ssn:hasProperty ;
  owl:minCardinality "1"^^xsd:nonNegativeInteger
] .
```

`ssn:Property` is defined as:

```turtle
ssn:Property rdf:type owl:Class ;
  rdfs:subClassOf [
    owl:onProperty ssn:isPropertyOf ;
    owl:allValuesFrom sosa:FeatureOfInterest
  ] ;
  rdfs:comment "A quality of an entity. An aspect of an entity that is intrinsic to and cannot exist without the entity."@en ;
  rdfs:label "Property"@en .
```

### `imports/ssn-systems.ttl`

SSN Systems declares six subproperties of `ssn:hasProperty`:

| Property | Source definition summary |
| --- | --- |
| `ssn-system:hasOperatingProperty` | OperatingRange to OperatingProperty. |
| `ssn-system:hasOperatingRange` | System to OperatingRange. |
| `ssn-system:hasSurvivalProperty` | SurvivalRange to SurvivalProperty. |
| `ssn-system:hasSurvivalRange` | System to SurvivalRange. |
| `ssn-system:hasSystemCapability` | System to SystemCapability. |
| `ssn-system:hasSystemProperty` | SystemCapability to SystemProperty. |

This is the strongest local reason not to map broad `ssn:hasProperty` directly: every SSN Systems subproperty inherits any active superproperty mapping placed on `ssn:hasProperty`.

## Local BFO/CCO Evidence

The local CCO import includes the relevant BFO relations:

| IRI | Label | Local domain/range evidence |
| --- | --- | --- |
| `bfo:BFO_0000196` | bearer of | Domain: independent continuant excluding spatial region. Range: specifically dependent continuant. |
| `bfo:BFO_0000197` | inheres in | Inverse of bearer-of style relation; subproperty of `bfo:BFO_0000195`; domain specifically dependent continuant; range independent continuant excluding spatial region. |
| `bfo:BFO_0000195` | specifically depends on | Domain: specifically dependent continuant. Range: specifically dependent continuant or independent continuant excluding spatial region. |
| `bfo:BFO_0000117` | has occurrent part | Domain: occurrent. Range: occurrent. |

The local CCO import also includes aggregate-specific alternatives such as `cco:ont00001907` / "aggregate has quality" and `cco:ont00001956` / "aggregate has disposition". These are not good candidates for broad `ssn:hasProperty`, because their domains are object aggregates and their definitions do not cover the broad SSN relation between an entity and a property of that entity.

`bfo:BFO_0000144` / "Process Profile" is locally available as a class and supports the process-profile reading in the spreadsheet notes. However, it is not itself a replacement object property for `ssn:hasProperty`.

## Prior Unsafe Mapping

The prior unsafe mapping is recoverable from the spreadsheet reasoning cell and deferral reports as a dual subproperty mapping:

```turtle
ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000196 .
ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000117 .
```

The deferral report states that the prior dual mapping to `bfo:bearer_of` and `bfo:has_occurrent_part` made `ssn:hasProperty` unsatisfiable under ELK. The reasoner diagnostic report states that after removing the direct `BatteryLifetime` and `MeasurementRange` blocks, remaining unsatisfiable-property behavior was driven by the `ssn:hasProperty` dual mapping.

## Why The Dual Mapping Was Unsafe

The dual mapping makes one broad SSN property a subproperty of two relations with incompatible BFO typing behavior:

- `bfo:BFO_0000196` / bearer of: subject is an independent continuant, object is a specifically dependent continuant.
- `bfo:BFO_0000117` / has occurrent part: subject and object are occurrents.

Because SSN Systems declares multiple subproperties of `ssn:hasProperty`, the superproperty mapping is inherited by those narrower relations. Several of those narrower relations already have local mappings to `bfo:BFO_0000195` or `bfo:BFO_0000196` in `SSN2BFO.ttl`. Adding a broad superproperty mapping therefore forces inherited domain/range commitments across the SSN Systems property family, rather than affecting only the generic `ssn:hasProperty` row.

The ELK variant tests below confirm that even a single broad active mapping on `ssn:hasProperty` is not reasoner-safe in the current local graph.

## ELK Variant Tests

### Temporary Test Setup

Temporary files were created under:

```text
/tmp/ssn-to-bfo-hasproperty-options
```

The temporary merged graph was built from:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

The merge script removed:

- all `owl:imports` triples;
- `sosa:isSampleOf rdf:type owl:FunctionalProperty`.

ROBOT version:

```text
ROBOT version 1.9.7
```

ROBOT command pattern:

```bash
robot reason --reasoner ELK --input /tmp/ssn-to-bfo-hasproperty-options/<variant>.ttl --output /tmp/ssn-to-bfo-hasproperty-options/<variant>-reasoned.ttl
```

All ROBOT runs emitted OWLAPI parser warnings of the form `Entity not properly recognized, missing triples in input? http://org.semanticweb.owlapi/error#ErrorN for type Class`. The baseline run still completed successfully and produced a reasoned output. The failed variants reported unsatisfiable properties and did not produce reasoned outputs suitable for counting `owl:Nothing` entities.

### Test Results

| Variant | Added mapping | ROBOT status | `owl:Nothing` count in reasoned output | ELK result |
| --- | --- | ---: | ---: | --- |
| Baseline | none | 0 | 0 | ELK-clean for this test. |
| Bearer-only | `ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000196 .` | 1 | Not available; ROBOT failed before reasoned output. | Not ELK-clean. |
| Occurrent-only | `ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000117 .` | 1 | Not available; ROBOT failed before reasoned output. | Not ELK-clean. |
| Dual diagnostic | both bearer-only and occurrent-only mappings | 1 | Not available; ROBOT failed before reasoned output. | Not ELK-clean. |

Failed variant details:

| Variant | ROBOT-reported unsatisfiable properties |
| --- | --- |
| Bearer-only | `ssn-system:hasOperatingProperty`, `ssn-system:hasSurvivalProperty`, `ssn-system:hasSystemProperty` |
| Occurrent-only | `ssn-system:hasSystemCapability`, `ssn-system:hasOperatingProperty`, `ssn-system:hasSurvivalProperty`, `ssn-system:hasOperatingRange`, `ssn-system:hasSurvivalRange`, `ssn-system:hasSystemProperty` |
| Dual diagnostic | `ssn-system:hasSystemCapability`, `ssn:hasProperty`, `ssn-system:hasOperatingProperty`, `ssn-system:hasSurvivalProperty`, `ssn-system:hasOperatingRange`, `ssn-system:hasSurvivalRange`, `ssn-system:hasSystemProperty` |

## Candidate Options

Ranked from safest to riskiest:

| Rank | Option | Form | Local support | Active logical change? | ELK testing required? | ELK evidence | Recommendation |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | Keep no active direct mapping for `ssn:hasProperty`. | no active mapping | Supported by the current TTL, cleared spreadsheet OWL axiom, audit skip, and ELK-clean baseline. | No | No new test required beyond normal validation. | Baseline status 0; `owl:Nothing` count 0. | Recommended. |
| 2 | Add annotation-only documentation explaining why `ssn:hasProperty` remains deferred. | annotation-only | Supported by spreadsheet reasoning and deferral reports. | No logical change | Not expected to affect ELK; normal validation still prudent if placed in TTL. | Not separately tested because it would not add a logical axiom. | Acceptable if documentation is desired. |
| 3 | Preserve the current split mapping of narrower SSN Systems properties instead of mapping `ssn:hasProperty` itself. | subproperty mapping of narrower SSN Systems properties | Already present in `SSN2BFO.ttl`; source ontology provides narrower relation definitions. | No, if only preserving current state. Yes, if expanding/changing it. | Required for any future additions or changes. | Current baseline with these mappings is ELK-clean. | Recommended as the current reasoner-safe pattern; do not extend mechanically. |
| 4 | Map `ssn:hasProperty` only to `bfo:BFO_0000196` / bearer of. | `rdfs:subPropertyOf` named property | Partially matches continuant-to-dependent-continuant readings. | Yes | Yes | Failed: 3 unsatisfiable SSN Systems properties. | Not recommended. |
| 5 | Map `ssn:hasProperty` only to `bfo:BFO_0000117` / has occurrent part. | `rdfs:subPropertyOf` named property | Partially matches process-profile readings. | Yes | Yes | Failed: 6 unsatisfiable SSN Systems properties. | Not recommended. |
| 6 | Map both bearer-of and has-occurrent-part on `ssn:hasProperty`. | broader redesign / out of scope | Recoverable as the prior unsafe mapping. | Yes | Yes | Failed: 7 unsatisfiable properties including `ssn:hasProperty`. | Not recommended; confirms the prior unsafe pattern. |
| 7 | Map inverse `ssn:isPropertyOf` to `bfo:BFO_0000197` / inheres in. | `rdfs:subPropertyOf` named property | Locally available inverse-style BFO relation. | Yes | Yes | Not separately tested; this is not independent of the bearer-of reading and would likely inherit the same modeling problem through `owl:inverseOf`. | Not recommended without a separate review. |
| 8 | Use CCO aggregate-specific relations such as `cco:ont00001907` / aggregate has quality or `cco:ont00001956` / aggregate has disposition. | broader redesign / out of scope | Local labels exist, but domains are object aggregates and definitions are aggregate-specific. | Yes | Yes | Not tested; source support is inadequate. | Not recommended. |

## Conservative Conclusion

There is no narrow active replacement for generic `ssn:hasProperty` that is supported by the inspected local sources and remains ELK-clean in the tested variants.

The reasoner-safe path is:

- keep `ssn:hasProperty` with no active direct BFO/CCO subproperty mapping;
- allow annotation-only documentation if needed;
- preserve the existing narrower SSN Systems subproperty mappings as the current local split pattern;
- require ELK testing before any future active logical change to `ssn:hasProperty`, `ssn:isPropertyOf`, or inherited SSN Systems subproperty mappings.

Do not reintroduce the prior dual mapping.
