# System Property Process Profile Scope Review

## Scope

This is a read-only review of whether `ssn-system:SystemProperty` can include process profiles, and whether that affects the current active mapping:

```turtle
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194 .
```

No ontology files, spreadsheet files, imports, generated artifacts, or existing reports were edited. This report is the only new artifact.

## Files Inspected

- `SSN2BFO.ttl`
- `Current_SOSA-SSN to BFO-CCO.xlsx`
- `imports/ssn-systems.ttl`
- `imports/ssn.ttl`
- `imports/cco.ttl`
- `reports/ssn-hasproperty-modeling-options.md`
- `reports/ssn-hasproperty-disjunctive-domain-range-candidate.md`
- `reports/ssn-hasproperty-rule-mapping-artifact.md`
- `reports/ssn-systems-property-split-mapping-review.md`

Local searches covered:

- `SystemProperty`
- `hasSystemProperty`
- `Process Profile`
- `BFO_0000144`
- `process profile`
- `OperatingProperty`
- `SurvivalProperty`

## Current Active Mapping

In the current working tree, `SSN2BFO.ttl` maps:

| Source relation | Current active target |
| --- | --- |
| `ssn-system:hasOperatingProperty` | `rdfs:subPropertyOf bfo:BFO_0000194` / specifically depended on by |
| `ssn-system:hasSurvivalProperty` | `rdfs:subPropertyOf bfo:BFO_0000194` / specifically depended on by |
| `ssn-system:hasSystemProperty` | `rdfs:subPropertyOf bfo:BFO_0000194` / specifically depended on by |

The specific mapping under review is:

```turtle
<http://www.w3.org/ns/ssn/systems/hasSystemProperty>
  rdfs:subPropertyOf <http://purl.obolibrary.org/obo/BFO_0000194> .
```

## Source Ontology Evidence

### `ssn-system:hasSystemProperty`

`imports/ssn-systems.ttl` defines `ssn-system:hasSystemProperty` as an object property, a subproperty of `ssn:hasProperty`, with the source definition:

> Relation from an SystemCapability of a System to a SystemProperty describing the capabilities of the System.

The source relation therefore has the pattern:

```text
SystemCapability -> SystemProperty
```

### `ssn-system:SystemCapability`

`ssn-system:SystemCapability` is a subclass of `ssn:Property`. The source ontology gives it a restriction:

```turtle
owl:onProperty ssn-system:hasSystemProperty ;
owl:allValuesFrom ssn-system:SystemProperty
```

The local source text describes normal measurement, actuation, and sampling properties of a system under specified conditions. The source ontology does not explicitly classify `SystemCapability` as `bfo:BFO_0000144` / Process Profile.

### `ssn-system:SystemProperty`

`ssn-system:SystemProperty` is a subclass of `ssn:Property`. The source ontology gives it restrictions using the inverse of `ssn-system:hasSystemProperty`:

```turtle
owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
owl:allValuesFrom ssn-system:SystemCapability
```

and:

```turtle
owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
owl:minCardinality "1"^^xsd:nonNegativeInteger
```

The local source definition is:

> An identifiable and observable characteristic that represents the System's ability to operate its primary purpose: a Sensor to make Observations, an Actuator to make Actuations, or a Sampler to make Samplings.

This source block does not mention `Process Profile`, `bfo:BFO_0000144`, or an occurrent-part pattern.

### `ssn:Property`

`imports/ssn.ttl` defines `ssn:Property` as:

> A quality of an entity. An aspect of an entity that is intrinsic to and cannot exist without the entity.

It also restricts `ssn:isPropertyOf` values to `sosa:FeatureOfInterest`. The source definition again reads like a dependent-property abstraction, not an explicit BFO process-profile classification.

## Local BFO Evidence

The relevant BFO identifiers in `imports/cco.ttl` are:

| IRI | Label | Local constraints relevant here |
| --- | --- | --- |
| `bfo:BFO_0000194` | specifically depended on by | inverse of `bfo:BFO_0000195`; range is `bfo:BFO_0000020` / specifically dependent continuant |
| `bfo:BFO_0000195` | specifically depends on | domain is `bfo:BFO_0000020`; definition is SDC dependence |
| `bfo:BFO_0000144` | Process Profile | subclass of `bfo:BFO_0000003` / occurrent |
| `bfo:BFO_0000117` | has occurrent part | domain and range are `bfo:BFO_0000003` / occurrent |

This matters because `bfo:BFO_0000194` directly supports a dependence pattern where the object of the constructed relation is a specifically dependent continuant. It does not directly support an object that is a process profile.

## Spreadsheet Evidence

The spreadsheet contains two different kinds of evidence:

1. The relation row for `ssn-system:hasSystemProperty`.
2. The class row for `ssn-system:SystemProperty`.

### Relation Row

On `System Capability` row 14, the spreadsheet currently maps:

```text
ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:specifically_depended_on_by .
```

The rationale says the source relation runs from system capability `x` to system property `y`, while the intended dependence runs from `y` specifically depending on `x`; therefore the object property maps to `bfo:specifically_depended_on_by` / `BFO_0000194`.

This row is SDC-like. It treats `y` as something that specifically depends on `x`.

### Class Row

On `System Capability` row 32, the spreadsheet maps `ssn-system:SystemProperty` more broadly:

```text
subClassOf (bfo:SpecificallyDependentContinuant or bfo:ProcessProfile)
and cco:prescribed_by some cco:ArtifactFunctionSpecification
```

The row says `SystemProperty` is treated as either a specifically dependent continuant or a process profile.

This is the main local evidence that process-profile `SystemProperty` cases may be in scope at the mapping layer, even though the source ontology itself does not explicitly classify `SystemProperty` as a process profile.

### Related Spreadsheet Rows

The same sheet gives additional context:

| Row | Term | Spreadsheet treatment |
| ---: | --- | --- |
| 13 in `Common Classes` | `ssn:Property` | equivalent to specifically dependent continuant or process profile |
| 20 in `System Capability` | `ssn-system:OperatingProperty` | specifically dependent continuant or process profile |
| 21 in `System Capability` | `ssn-system:OperatingRange` | specifically dependent continuant or process profile |
| 28 in `System Capability` | `ssn-system:SurvivalProperty` | function, with realizations |
| 29 in `System Capability` | `ssn-system:SurvivalRange` | function, with realizations |
| 30 in `System Capability` | `ssn-system:SystemCapability` | specifically dependent continuant or process profile |
| 32 in `System Capability` | `ssn-system:SystemProperty` | specifically dependent continuant or process profile |

So the process-profile concern is not visible in the source ontology, but it is visible in the spreadsheet's BFO interpretation for `ssn:Property`, `SystemCapability`, `SystemProperty`, `OperatingRange`, and `OperatingProperty`.

## Existing Report Evidence

The `ssn:hasProperty` modeling reports establish a generic conditional pattern:

- If the subject is an independent continuant and the object is a specifically dependent continuant, the intended materialized relation is `bfo:BFO_0000196` / bearer of.
- If the subject is an occurrent and the object is a process profile, the intended materialized relation is `bfo:BFO_0000117` / has occurrent part.

The SPARQL rule artifact report says the rule can consume direct `ssn:hasProperty` assertions or predicates explicitly classified under `ssn:hasProperty`. Since `ssn-system:hasSystemProperty` is a subproperty of `ssn:hasProperty`, it could be consumed by that rule architecture if the input graph includes the relevant subproperty hierarchy and typing.

The disjunctive domain/range candidate report warns that global domain/range approximations on `ssn:hasProperty` can propagate through SSN Systems subproperties.

The earlier `ssn-systems-property-split-mapping-review.md` should be treated as prior context, not current mapping state. Its current-target rows predate the recent directionality corrections from `BFO_0000195` to `BFO_0000194`. Its useful surviving point is that `hasSystemProperty` has the source pattern `SystemCapability -> SystemProperty`; however, it did not settle the new question of whether spreadsheet-level process-profile cases should be considered in scope for `SystemProperty`.

## Answers

### 1. What does the local source ontology say `SystemProperty` is?

The local source ontology says `ssn-system:SystemProperty` is an `ssn:Property` and an identifiable, observable characteristic representing a system's ability to operate its primary purpose. It also says a `SystemProperty` is linked back to at least one `SystemCapability` through the inverse of `ssn-system:hasSystemProperty`.

The source ontology does not explicitly identify `SystemProperty` as a BFO specifically dependent continuant, function, process profile, or occurrent.

### 2. Does the local source evidence explicitly classify `SystemProperty` or its subclasses as process profiles?

No. In `imports/ssn-systems.ttl`, local source evidence does not explicitly classify `SystemProperty`, `OperatingProperty`, or `SurvivalProperty` as `bfo:BFO_0000144` / Process Profile. The term `Process Profile` appears in the local CCO import and in mapping reports/spreadsheet rows, not as a source-ontology superclass for `ssn-system:SystemProperty`.

### 3. Does the spreadsheet or existing reports suggest any `SystemProperty` cases are process profiles?

Yes, but at the mapping layer rather than the source-ontology layer.

The spreadsheet row for `ssn-system:SystemProperty` says it is either a specifically dependent continuant or a process profile. The spreadsheet row for generic `ssn:Property` also uses a specifically-dependent-continuant-or-process-profile pattern.

The existing `ssn:hasProperty` reports support a generic process-profile branch for `ssn:hasProperty`-style relations. They do not prove that any particular `SystemProperty` individual is a process profile, but they do show that the mapping project has been considering process-profile cases for property-like terms.

### 4. Is the current `hasSystemProperty -> BFO_0000194` mapping valid only for SDC-like system properties?

Yes. The current direct OWL subproperty mapping is valid only for the SDC-like reading where:

```text
x ssn-system:hasSystemProperty y
```

means:

```text
y specifically depends on x
```

and where `y` is a specifically dependent continuant. That is exactly what `bfo:BFO_0000194` / specifically depended on by represents from `x` to `y`.

If `y` is instead a process profile, then `bfo:BFO_0000194` is too narrow because its local range is `bfo:BFO_0000020` / specifically dependent continuant. If `x` is also treated as a process profile, the domain side becomes questionable too, because `bfo:BFO_0000194` is not an occurrent-to-occurrent relation.

### 5. If process-profile cases are in scope, does `hasSystemProperty` have the same conditional-pattern problem as generic `ssn:hasProperty`?

Potentially yes.

If `SystemCapability -> SystemProperty` can include both SDC-like and process-profile cases, then one fixed direct OWL subproperty mapping to `bfo:BFO_0000194` cannot cover all cases. The SDC-like case and process-profile case would need different treatment, just as generic `ssn:hasProperty` does.

This report does not assert that a process-profile mapping is correct for `hasSystemProperty`. It only notes that, if process-profile `SystemProperty` cases are intentionally in scope, the current direct OWL mapping is conditional rather than globally valid.

### 6. Should the current active OWL mapping remain, be marked for review, or be deferred in favor of a rule/COMS artifact?

Conservative recommendation: mark the current active OWL mapping for review.

Do not defer or remove it based on this report alone, because the local source ontology does not explicitly classify `SystemProperty` as a process profile. The active `BFO_0000194` mapping is coherent for SDC-like `SystemProperty` cases and aligns with the current spreadsheet relation row for `hasSystemProperty`.

However, the spreadsheet class row for `SystemProperty` explicitly includes process profiles. If human review confirms that process-profile `SystemProperty` values are truly in scope for `ssn-system:hasSystemProperty`, then this direct OWL subproperty mapping should be deferred or moved behind a rule/COMS pattern rather than treated as a globally valid mapping.

Recommended status:

```text
keep active for now, but mark for review
```

Review question:

```text
Is `ssn-system:hasSystemProperty` intended to cover only SDC-like SystemProperty values, or both SDC-like and process-profile SystemProperty values?
```

### 7. Does this concern also affect `hasOperatingProperty` or `hasSurvivalProperty`, or only `hasSystemProperty`?

It does not appear to affect only `hasSystemProperty`.

`hasOperatingProperty` has a similar concern because the spreadsheet class rows for both `OperatingRange` and `OperatingProperty` include the specifically-dependent-continuant-or-process-profile pattern. The current direct `BFO_0000194` mapping for `hasOperatingProperty` is therefore also valid only for the SDC-like reading unless process-profile cases are ruled out for that relation.

`hasSurvivalProperty` is different in the current spreadsheet. The source ontology does not explicitly classify `SurvivalProperty` as a process profile, and the spreadsheet maps `SurvivalProperty` and `SurvivalRange` as functions with realizations, not as process profiles. That means this specific process-profile concern is weaker for `hasSurvivalProperty`. It may still need separate review because a direct `BFO_0000194` mapping expects a specifically dependent continuant object, but the issue is not the same process-profile scope issue identified for `SystemProperty` and `OperatingProperty`.

## Final Recommendation

Do not change `SSN2BFO.ttl` from this review alone.

The current `ssn-system:hasSystemProperty rdfs:subPropertyOf bfo:BFO_0000194` mapping should be marked for human modeling review. It is defensible for SDC-like `SystemProperty` cases, but the spreadsheet's `SystemProperty` class row broadens the class to include process profiles. If that broadening is intentional for this relation, then `hasSystemProperty` should be handled like a conditional `ssn:hasProperty`-style mapping through a rule/COMS artifact rather than as one global OWL subproperty mapping.

The same follow-up question should be asked for `hasOperatingProperty`. The process-profile concern is less direct for `hasSurvivalProperty` based on the current spreadsheet evidence.
