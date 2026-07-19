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

## Additional CCO/Participant/Encoding Diagnostics

This update adds focused diagnostics to distinguish whether the reducer behavior is specific to `cco:ont00001833`, inherited BFO participant commitments, inverse `agent_in` context, `rdfs:range` encoding, or property typing.

The same M2 graph construction was used:

- parse `imports/cco.ttl`;
- parse `imports/ssn.ttl`;
- parse `imports/ssn-systems.ttl`;
- parse `SSN2BFO.ttl`;
- remove all `owl:imports` triples;
- remove `sosa:isSampleOf rdf:type owl:FunctionalProperty`;
- remove `sosa:hasSample rdf:type owl:InverseFunctionalProperty`.

Temporary files were written under:

```text
/tmp/ssn-to-bfo-madeByActuator-agent-mapping-adjustment-evaluation-update
```

No additional variant reintroduced the sample simplicity blocker.

### Variant Results G-L

| Variant | Graph path | Temporary edit | Triples | Return | Reasoned output | `owl:Nothing` | Unsat set | Result |
| --- | --- | --- | ---:| ---:| --- | ---:| --- | --- |
| G | `/tmp/ssn-to-bfo-madeByActuator-agent-mapping-adjustment-evaluation-update/G-parent-participant-plus-range.ttl` | Remove `madeByActuator -> cco:has_agent`; add `madeByActuator -> bfo:has_participant`; add explicit `madeByActuator range Actuator` | 15,511 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | fails |
| H | `/tmp/ssn-to-bfo-madeByActuator-agent-mapping-adjustment-evaluation-update/H-parent-domain-range-commitments-plus-range.ttl` | Remove `madeByActuator -> cco:has_agent`; add explicit range; manually add BFO `has_participant` domain and range commitments to `madeByActuator` without adding a subproperty axiom | 15,512 | 0 | yes | 0 | none | clean |
| I | `/tmp/ssn-to-bfo-madeByActuator-agent-mapping-adjustment-evaluation-update/I-remove-agent-in-context-plus-range.ttl` | Keep `madeByActuator -> cco:has_agent`; add explicit range; remove logical `cco:agent_in` context | 15,505 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | fails |
| J | `/tmp/ssn-to-bfo-madeByActuator-agent-mapping-adjustment-evaluation-update/J-global-universal-range-encoding.ttl` | Do not add `rdfs:range`; instead add `owl:Thing subClassOf (madeByActuator only Actuator)`; keep `madeByActuator -> cco:has_agent` | 15,514 | 0 | yes | 0 | none | clean |
| K | `/tmp/ssn-to-bfo-madeByActuator-agent-mapping-adjustment-evaluation-update/K-object-property-type-plus-range.ttl` | Add `madeByActuator rdf:type owl:ObjectProperty`; add explicit range; keep `madeByActuator -> cco:has_agent` | 15,512 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | fails |
| L | `/tmp/ssn-to-bfo-madeByActuator-agent-mapping-adjustment-evaluation-update/L-documentation-baseline-no-range.ttl` | Documentation control; no explicit range and no temporary edit | 15,510 | 0 | yes | 0 | none | clean |

### Variant H Parent Commitments

Variant H did not add the full subproperty axiom to BFO `has participant`. It copied only the parent-level domain/range commitments inherited from `bfo:BFO_0000057`:

```ttl
sosa:madeByActuator rdfs:domain bfo:BFO_0000015 .
sosa:madeByActuator rdfs:range  [
  owl:unionOf (
    bfo:BFO_0000020
    bfo:BFO_0000031
    [
      owl:intersectionOf (
        bfo:BFO_0000004
        [ owl:complementOf bfo:BFO_0000006 ]
      )
    ]
  )
] .
```

Together with the explicit source-level range:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

this was HermiT-clean. Therefore the inherited BFO `has participant` domain/range constraints alone are not enough to reproduce the failure.

### Variant I Removed Agent-In Logical Axioms

Variant I removed these logical triples involving `cco:ont00001787`:

```ttl
cco:ont00001787 rdf:type owl:ObjectProperty .
cco:ont00001787 rdfs:subPropertyOf bfo:BFO_0000056 .
cco:ont00001787 owl:inverseOf cco:ont00001833 .
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeObservation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeSampling rdfs:subPropertyOf cco:ont00001787 .
```

The failure still reproduced. Therefore the explicit-range failure does not require the active `agent_in` inverse/property context.

### Variant L CCO/BFO Documentation

The active CCO/BFO property context inspected for `has_agent` is:

```ttl
cco:ont00001833 rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf bfo:BFO_0000057 ;
    rdfs:label "has agent" ;
    skos:definition "x has_agent y iff x is an instance of Process and y is an instance of Agent, such that y is causally active in x." .

cco:ont00001787 rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf bfo:BFO_0000056 ;
    owl:inverseOf cco:ont00001833 ;
    rdfs:label "agent in" ;
    skos:definition "x agent_in y iff y is an instance of Process and x is an instance of Agent, such that x is causally active in y." .

bfo:BFO_0000057 rdf:type owl:ObjectProperty ;
    rdfs:domain bfo:BFO_0000015 ;
    rdfs:range [
      owl:unionOf (
        bfo:BFO_0000020
        bfo:BFO_0000031
        [
          owl:intersectionOf (
            bfo:BFO_0000004
            [ owl:complementOf bfo:BFO_0000006 ]
          )
        ]
      )
    ] ;
    rdfs:label "has participant" .

bfo:BFO_0000056 rdf:type owl:ObjectProperty ;
    owl:inverseOf bfo:BFO_0000057 ;
    rdfs:domain [
      owl:unionOf (
        bfo:BFO_0000020
        bfo:BFO_0000031
        [
          owl:intersectionOf (
            bfo:BFO_0000004
            [ owl:complementOf bfo:BFO_0000006 ]
          )
        ]
      )
    ] ;
    rdfs:range bfo:BFO_0000015 ;
    rdfs:label "participates in" .
```

No additional property characteristics, such as functionality, transitivity, or symmetry, were found for `cco:has_agent` in the inspected active context.

## Design Assessment

### Does The Explicit Range Failure Still Reproduce?

Yes. Variant B reproduces:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

Variant G shows that replacing `cco:has_agent` with parent `bfo:has_participant` still reproduces the same failure. Therefore the failure is not specific to `cco:ont00001833` as a named CCO property.

### Does Removing `madeByActuator -> has_agent` Unblock The Explicit Range Axiom?

Yes. Variant D is HermiT-clean after removing:

```ttl
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

and adding:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The additional diagnostics refine the meaning of this reducer. Removing `madeByActuator -> has_agent` works because it removes the active participant subproperty path. Variant G shows that adding that participant path back through `bfo:has_participant` is enough to fail again.

### Is `madeByActuator -> has_agent` The Best-Supported Reducer?

Yes, as a practical reducer, but not as a complete root-cause explanation. Prior reports already identified it as a strong reducer, and this report confirms:

- the current baseline remains clean if it is removed;
- the explicit range axiom becomes clean if it is removed;
- source-level domain/range-only remains clean.

The new variants show that the risky pattern is broader than the CCO `has_agent` name itself:

- `madeByActuator -> bfo:has_participant` plus explicit `rdfs:range` also fails.
- parent-level BFO domain/range commitments copied directly onto `madeByActuator` are clean.
- removing `agent_in` inverse/property context does not clear the failure.

This does not prove `madeByActuator -> has_agent` is semantically invalid. It shows that the active OWL participant subproperty path is not compatible with the explicit source-level `rdfs:range` axiom in the current merged full-OWL profile.

### Are Inherited Parent Commitments Alone Enough?

No. Variant H copied the parent BFO `has participant` domain and range commitments directly onto `madeByActuator` without adding a subproperty axiom to `has_participant`, and the graph was HermiT-clean.

This means the failure is not explained by the inherited BFO participant domain/range constraints alone.

### Does Removing Agent-In / Inverse Context Clear The Failure?

No. Variant I removed the logical `cco:agent_in` context, including its inverse link to `has_agent` and the active `madeActuation` / `madeObservation` / `madeSampling` subproperty links to `agent_in`. The graph still failed with the same three unsatisfiable classes.

This means the explicit-range failure does not require the inverse `agent_in` side.

### Does Universal Restriction Encoding Behave Like `rdfs:range`?

No. Variant J kept the current `madeByActuator -> has_agent` mapping but encoded the range-like commitment as:

```ttl
owl:Thing rdfs:subClassOf [
  owl:onProperty sosa:madeByActuator ;
  owl:allValuesFrom sosa:Actuator
] .
```

That variant was HermiT-clean, while the explicit `rdfs:range` encoding fails.

In OWL modeling terms these are closely related ways to express global range-like behavior, so this difference should be treated cautiously. In the ROBOT/HermiT workflow used here, however, the explicit `rdfs:range` / `ObjectPropertyRange` encoding behaves differently from the global universal-restriction encoding.

### Does Explicit `owl:ObjectProperty` Typing Change Anything?

No. Variant K added:

```ttl
sosa:madeByActuator rdf:type owl:ObjectProperty .
```

alongside the explicit range axiom and retained `madeByActuator -> has_agent`. It failed with the same unsatisfiable classes. Property typing is not the relevant difference.

### Is Source-Level Domain/Range-Only The Best HermiT-Safe OWL Operationalization?

Among the variants tested here, yes.

The source-level-only candidate preserves the local SOSA typing:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation ;
                    rdfs:range sosa:Actuator .
```

and avoids the CCO/BFO participant subproperty propagation that triggers the explicit-range failure.

### Is There A HermiT-Safe CCO/BFO Participant Alternative?

No HermiT-safe CCO/BFO participant-property alternative was identified in this report.

The inverse-side attempt failed because it is effectively equivalent to reintroducing the `has_agent` commitment through:

```text
madeByActuator inverseOf madeActuation
madeActuation subPropertyOf agent_in
agent_in inverseOf has_agent
```

Variant G also shows that replacing `has_agent` with the parent `has_participant` relation is not a safe replacement.

## Recommendation

Do not make a final mapping-change solely from the original reducer result.

The updated diagnostics still support this practical conclusion:

```text
Do not add sosa:madeByActuator rdfs:range sosa:Actuator while
sosa:madeByActuator remains an active subproperty of cco:has_agent
or bfo:has_participant.
```

They also refine the likely issue:

- it is not specific to the CCO `has_agent` IRI alone;
- it is not caused by inherited BFO participant domain/range commitments alone;
- it is not cleared by removing inverse `agent_in` context;
- it is sensitive to `rdfs:range` / `ObjectPropertyRange` encoding, because the global universal restriction encoding did not fail;
- explicit `owl:ObjectProperty` typing does not change the outcome.

The previous candidate branch remains plausible as a fix-evaluation branch, but should be framed narrowly as an evaluation, not as a final semantic correction:

```text
fix/defer-madeByActuator-agent-mapping-add-range
```

If pursued, that branch should:

- remove/defer the active `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` mapping;
- add the source-level range axiom `sosa:madeByActuator rdfs:range sosa:Actuator`;
- preserve the active domain axiom `sosa:madeByActuator rdfs:domain sosa:Actuation`;
- update the `Common OPs` row for `sosa:madeByActuator`;
- regenerate the mapping audit and ELK entailment report if needed;
- run HermiT M2 validation under the established cleanup conditions.

Do not claim that `madeByActuator -> has_agent` is semantically wrong. The better statement is:

```text
The direct active CCO has-agent mapping is plausible, but it is not HermiT-safe with the explicit source-level rdfs:range axiom in the current integrated OWL profile.
```

If a CCO-level agent semantics is still desired, it should be redesigned and tested in temporary HermiT graphs before being added as active OWL.

A narrower report-only follow-up may be useful before any final mapping-change branch:

```text
review/evaluate-madeByActuator-range-encoding-options
```

That follow-up should compare explicit `rdfs:range`, global universal restriction, and any other HermiT-safe encoding candidates under the current participant-mapping context.
