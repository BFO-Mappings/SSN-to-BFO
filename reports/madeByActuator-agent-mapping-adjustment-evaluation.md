# `sosa:madeByActuator` Agent Mapping Adjustment Evaluation

## Scope

This report evaluates report-only design options for adjusting the active `sosa:madeByActuator` CCO property mapping.

No repository mapping file, workbook, import, example, generated artifact, release artifact, tool, or existing report was edited. Temporary files were written under:

```text
/tmp/ssn-to-bfo-madeByActuator-agent-mapping-adjustment-evaluation
```

## Current Baseline

Current stable baseline:

| Check | Result |
| --- | --- |
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 70 |
| audit issues | 2 expected `sosa:Sensor` version-alignment issues only |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 77 |
| ELK property-chain expectations | 5 |
| ELK restriction expectations | 2 |
| active direct mappings not covered | 0 |
| active property-chain mappings not covered | 0 |
| active restriction mappings not covered | 0 |
| current HermiT M2 baseline under established cleanup conditions | clean |

## Prior Context

The relevant prior reports are:

- `reports/madeByActuator-range-hermit-failure.md`
- `reports/madeByActuator-range-redundancy-debug.md`
- `reports/madeByActuator-range-minimal-reproduction.md`
- `reports/actuation-range-simplification-implementation.md`
- `reports/system-property-direct-mapping-deferral.md`

Those reports established that:

- `sosa:madeByActuator rdfs:domain sosa:Actuation` is active and HermiT-clean.
- `sosa:madeByActuator rdfs:range sosa:Actuator` remains held back.
- `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` is active.
- `cco:ont00001833` is locally labeled `has agent`.
- Adding the explicit range axiom still reproduces the `sosa:Actuator` / `sosa:Actuation` / `ssn-system:ActuationRange` failure.
- Removing `sosa:madeByActuator -> cco:has_agent` was a strong reducer in the explicit-range failure.
- After the `ActuationRange` simplification and `SystemProperty` direct mapping deferral, the issue remains separate from those SSN Systems cleanup branches.

## Current Mapping Context

### `sosa:madeByActuator`

Current active TTL mapping:

```ttl
###  http://www.w3.org/ns/sosa/madeByActuator
<http://www.w3.org/ns/sosa/madeByActuator> rdfs:domain <http://www.w3.org/ns/sosa/Actuation> ;
                                           rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001833> .
```

The held-back range axiom is not active:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

Workbook row:

| Sheet | Row | Source term | OWL axiom cell summary |
| --- | ---:| --- | --- |
| `Common OPs` | 28 | `sosa:madeByActuator` | domain `sosa:Actuation`; workbook also notes inverse of `sosa:madeActuation`; active CCO subproperty `cco:ont00001833` |

Important note: the workbook row describes `sosa:madeByActuator` as inverse of `sosa:madeActuation`, but no active `owl:inverseOf` axiom for this pair was found in `SSN2BFO.ttl`, `imports/ssn.ttl`, or `imports/ssn-systems.ttl`.

### `sosa:madeActuation`

Current active TTL mapping:

```ttl
###  http://www.w3.org/ns/sosa/madeActuation
<http://www.w3.org/ns/sosa/madeActuation> rdfs:domain <http://www.w3.org/ns/sosa/Actuator> ;
                                          rdfs:range <http://www.w3.org/ns/sosa/Actuation> ;
                                          rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001787> .
```

`cco:ont00001787` is locally labeled `agent in` and is inverse of `cco:ont00001833`.

Workbook row:

| Sheet | Row | Source term | OWL axiom cell summary |
| --- | ---:| --- | --- |
| `Common OPs` | 27 | `sosa:madeActuation` | domain `sosa:Actuator`; range `sosa:Actuation`; subproperty of `cco:agent_in` |

### CCO/BFO Target Context

Relevant target property context:

```ttl
cco:ont00001833 rdfs:subPropertyOf bfo:BFO_0000057 ;
                rdfs:label "has agent"@en .

cco:ont00001787 rdfs:subPropertyOf bfo:BFO_0000056 ;
                owl:inverseOf cco:ont00001833 ;
                rdfs:label "agent in"@en .

bfo:BFO_0000057 rdfs:domain bfo:BFO_0000015 ;
                rdfs:range [
                  owl:unionOf (
                    bfo:BFO_0000020
                    bfo:BFO_0000031
                    ...
                  )
                ] ;
                rdfs:label "has participant"@en .
```

The CCO mapping is semantically plausible: an actuation made by an actuator can be read as an actuation process having the actuator as its causally active agent. The issue is not that this reading is obviously wrong. The issue is that this direct OWL subproperty form is not HermiT-safe once the source-level range axiom is explicit in the current integrated profile.

## Source Context

Imported `imports/ssn.ttl` source context directly attached to these terms includes:

```ttl
sosa:madeByActuator rdfs:isDefinedBy sosa: .
sosa:madeActuation rdfs:isDefinedBy sosa: .
```

`sosa:usedProcedure` has source property-chain axioms using `sosa:madeByActuator`:

```ttl
sosa:usedProcedure owl:propertyChainAxiom (
  sosa:madeByActuator
  ssn:implements
) .
```

`sosa:Actuation` source restrictions include:

```ttl
sosa:Actuation rdfs:subClassOf [
  owl:onProperty sosa:madeByActuator ;
  owl:allValuesFrom sosa:Actuator
] ,
[
  owl:onProperty sosa:madeByActuator ;
  owl:cardinality "1"^^xsd:nonNegativeInteger
] .
```

`sosa:Actuator` source restrictions include:

```ttl
sosa:Actuator rdfs:subClassOf ssn:System ,
[
  owl:onProperty sosa:madeActuation ;
  owl:allValuesFrom sosa:Actuation
] ,
[
  owl:onProperty ssn:implements ;
  owl:minCardinality "1"^^xsd:nonNegativeInteger
] .
```

The imported source ontology already supplies a strong local pattern around actuation, actuator, and made-by relation. The mapping question is whether the CCO `has agent` subproperty commitment should be active OWL on `sosa:madeByActuator`.

## HermiT Method

Each temporary graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Then the graph removed:

```text
all owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty
sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

All variants used:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

The same graph-construction procedure was used for all variants.

## Variant Summary

| Variant | Temporary edit | Triples | Return | Reasoned output | `owl:Nothing` | Unsat set | Result |
| --- | --- | ---:| ---:| --- | ---:| --- | --- |
| A | Current baseline; no explicit range | 15,510 | 0 | yes | 0 | none | clean |
| B | Add explicit `sosa:madeByActuator rdfs:range sosa:Actuator` | 15,511 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` | fails |
| C | Remove only `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833`; no explicit range | 15,509 | 0 | yes | 0 | none | clean |
| D | Remove `madeByActuator -> has_agent`; add explicit `madeByActuator range Actuator` | 15,510 | 0 | yes | 0 | none | clean |
| E1 | Remove `madeByActuator -> has_agent`; add `madeByActuator owl:inverseOf madeActuation`; no explicit range | 15,510 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` | fails |
| E2 | Remove `madeByActuator -> has_agent`; add `madeByActuator owl:inverseOf madeActuation`; add explicit range | 15,511 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` | fails |
| F | Source-level-only `madeByActuator`: domain remains active, explicit range added, no CCO/BFO property mapping for `madeByActuator` | 15,510 | 0 | yes | 0 | none | clean |

No variant reintroduced the sample simplicity blocker.

## Variant Interpretation

### Variant A: Current Baseline

The current graph remains HermiT-clean with:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation ;
                    rdfs:subPropertyOf cco:ont00001833 .
```

and without the explicit range axiom.

### Variant B: Current Mapping Plus Explicit Range

Adding only:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

reproduces the known failure:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

This confirms that the explicit-range failure still exists after the `ActuationRange` simplification and `SystemProperty` direct mapping deferral.

### Variant C: Remove Only `madeByActuator -> has_agent`

Removing only:

```ttl
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

is HermiT-clean without adding the range axiom. This indicates that deferring the CCO property mapping alone is not itself harmful to the current clean baseline.

### Variant D/F: Source-Level Domain/Range Only

Removing `madeByActuator -> has_agent` and adding:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

is HermiT-clean.

Since the domain axiom is already active, this is the source-level-only operationalization for `madeByActuator`:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation ;
                    rdfs:range sosa:Actuator .
```

with no CCO/BFO property mapping for `sosa:madeByActuator`.

### Variant E: Inverse-Side Alternative

The inverse-side candidate is attractive because the workbook describes `madeByActuator` as inverse of `madeActuation`, and `madeActuation` is already mapped to `cco:agent_in`.

However, this candidate failed even without adding the explicit range axiom:

```ttl
sosa:madeByActuator owl:inverseOf sosa:madeActuation .
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
cco:ont00001787 owl:inverseOf cco:ont00001833 .
```

Together, those axioms effectively restore the `madeByActuator` to `has_agent` commitment through inverse-property reasoning. The failure set is the same three-class cluster:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

This means an OWL inverse bridge to the existing `madeActuation -> agent_in` mapping is not HermiT-safe in the current profile.

## Design Assessment

### Does The Explicit Range Failure Still Reproduce?

Yes. Variant B reproduces:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

### Does Removing `madeByActuator -> has_agent` Unblock The Explicit Range Axiom?

Yes. Variant D is HermiT-clean after removing:

```ttl
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

and adding:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

This is the strongest evidence in this report.

### Is `madeByActuator -> has_agent` The Best-Supported Reducer?

Yes, for this candidate adjustment question. Prior reports already identified it as a strong reducer, and this report confirms:

- the current baseline remains clean if it is removed;
- the explicit range axiom becomes clean if it is removed;
- source-level domain/range-only remains clean.

This does not prove `madeByActuator -> has_agent` is semantically invalid. It shows that the direct active OWL CCO property mapping is not compatible with adding the source-level range axiom in the current merged full-OWL profile.

### Is Source-Level Domain/Range-Only The Best HermiT-Safe OWL Operationalization?

Among the variants tested here, yes.

The source-level-only candidate preserves the local SOSA typing:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation ;
                    rdfs:range sosa:Actuator .
```

and avoids the CCO/BFO participant/agent propagation that triggers the explicit-range failure.

### Is There A HermiT-Safe CCO Alternative?

No HermiT-safe CCO alternative was identified in this report.

The inverse-side attempt failed because it is effectively equivalent to reintroducing the `has_agent` commitment through:

```text
madeByActuator inverseOf madeActuation
madeActuation subPropertyOf agent_in
agent_in inverseOf has_agent
```

This suggests that simply moving the CCO mapping to the inverse side is not a safe replacement.

## Recommendation

Recommend a future mapping-change branch:

```text
fix/defer-madeByActuator-agent-mapping-add-range
```

That branch should:

- remove/defer the active `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` mapping;
- add the source-level range axiom `sosa:madeByActuator rdfs:range sosa:Actuator`;
- preserve the active domain axiom `sosa:madeByActuator rdfs:domain sosa:Actuation`;
- update the `Common OPs` row for `sosa:madeByActuator`;
- regenerate the mapping audit and ELK entailment report if needed;
- run HermiT M2 validation under the established cleanup conditions.

Do not claim that `madeByActuator -> has_agent` is semantically wrong. The better statement is:

```text
The direct active CCO has-agent mapping is plausible, but it is not HermiT-safe with the source-level range axiom in the current integrated OWL profile.
```

If a CCO-level agent semantics is still desired, it should be redesigned and tested in temporary HermiT graphs before being added as active OWL.
