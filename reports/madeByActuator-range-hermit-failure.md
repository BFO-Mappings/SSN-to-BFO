# `sosa:madeByActuator` Range HermiT Diagnostic

## Scope

This report documents a focused HermiT diagnostic for the held-back source-level range axiom:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The report is diagnostic only. It does not edit `SSN2BFO.ttl`, the workbook, imports, source examples, tools, generated artifacts, or any existing report.

Current local context:

- Branch: `review/explain-madeByActuator-range-hermit-failure`
- Commit: `2beb95f`
- Temporary directory: `/tmp/ssn-to-bfo-madeByActuator-range-hermit-failure`
- ROBOT: `ROBOT version 1.9.7`
- Java: `22.0.2`

## Current Baseline

The current stable baseline, after the HermiT-clean source-level domain/range additions, is:

- validation suite: PASS
- `ttl_candidate_mapping_assertions=71`
- mapping audit issues: 2 expected `sosa:Sensor` version-alignment issues only
- ELK direct class expectations: 6
- ELK direct property expectations: 77
- property-chain expectations: 5
- restriction expectations: 2
- active direct/property-chain/restriction mappings not covered: 0
- current HermiT M2 baseline: clean under the established cleanup conditions

The active companion source-level domain axiom is present and HermiT-safe in the current baseline:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

The held-back range axiom remains absent from the active mapping:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

## Relevant Source And Mapping Context

### `sosa:madeByActuator`

Current active mapping-side assertions in `SSN2BFO.ttl`:

```ttl
sosa:madeByActuator
    rdfs:domain sosa:Actuation ;
    rdfs:subPropertyOf cco:ont00001833 .
```

The target property is:

```text
cco:ont00001833 = has agent
cco:ont00001833 rdfs:subPropertyOf bfo:BFO_0000057
bfo:BFO_0000057 = has participant
```

BFO `has participant` has domain `bfo:BFO_0000015` (`process`) and a broad participant range that includes continuants and related participant categories.

### `sosa:Actuation`

Imported `imports/ssn.ttl` source context directly attached to `sosa:Actuation` includes restrictions on:

- `sosa:actsOnProperty only sosa:ActuatableProperty`
- `sosa:hasFeatureOfInterest only sosa:FeatureOfInterest`
- `sosa:hasResult only sosa:Result`
- `sosa:madeByActuator only sosa:Actuator`
- `sosa:usedProcedure only sosa:Procedure`
- cardinality and minimum-cardinality commitments, including `sosa:madeByActuator` cardinality 1

Active mapping-side class expression in `SSN2BFO.ttl`:

```ttl
sosa:Actuation owl:equivalentClass [
  owl:intersectionOf (
    cco:ont00000228
    [ owl:onProperty sosa:actsOnProperty ;
      owl:someValuesFrom sosa:ActuatableProperty ]
  )
] .
```

Here `cco:ont00000228` is `Planned Act`, which is under CCO `Act` and therefore under BFO process context.

### `sosa:Actuator`

Imported `imports/ssn.ttl` source context directly attached to `sosa:Actuator` includes:

- `sosa:Actuator rdfs:subClassOf ssn:System`
- `sosa:madeActuation only sosa:Actuation`
- `ssn:forProperty only sosa:ActuatableProperty`
- `ssn:implements min 1`

Active mapping-side class expression in `SSN2BFO.ttl`:

```ttl
sosa:Actuator rdfs:subClassOf [
  owl:intersectionOf (
    bfo:BFO_0000040
    [ owl:onProperty bfo:BFO_0000196 ;
      owl:someValuesFrom [
        owl:intersectionOf (
          bfo:BFO_0000017
          [ owl:onProperty bfo:BFO_0000054 ;
            owl:someValuesFrom sosa:Actuation ]
        )
      ] ]
    [ owl:onProperty cco:ont00001787 ;
      owl:someValuesFrom sosa:Actuation ]
  )
] .
```

Relevant labels:

- `bfo:BFO_0000040` = material entity
- `bfo:BFO_0000196` = bearer of
- `bfo:BFO_0000017` = realizable entity
- `bfo:BFO_0000054` = has realization
- `cco:ont00001787` = agent in, inverse of `cco:ont00001833` (`has agent`)

### `ssn-system:ActuationRange`

Imported `imports/ssn-systems.ttl` source context directly attached to `ssn-system:ActuationRange` includes:

```ttl
ssn-system:ActuationRange
    rdfs:subClassOf ssn-system:SystemProperty ,
        [ owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
          owl:allValuesFrom [
            owl:onProperty [ owl:inverseOf ssn-system:hasSystemCapability ] ;
            owl:allValuesFrom sosa:Actuator
          ] ] .
```

Active mapping-side class expression in `SSN2BFO.ttl` maps `ssn-system:ActuationRange` as a BFO function with realization in an actuation-shaped process expression involving `sosa:Actuation`, output/affects alternatives, and a CCO prescription/specification pattern.

The already-deferred direct BFO dependence property mapping for `ssn-system:hasSystemProperty` remains inactive. The source-level domain/range axioms for `ssn-system:hasSystemProperty` remain active.

## HermiT Method

Every HermiT graph was built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

For every variant, the temporary graph removed:

```text
all owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty
sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

Each variant was run with:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

No variant reintroduced the sample simplicity blocker.

## Variant Summary

| Variant | Temporary edit | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Result |
|---|---:|---:|---:|---|---:|---:|---|
| A | Baseline current graph | 15535 | 0 | yes | 0 | 0 | clean |
| B | Add `sosa:madeByActuator rdfs:range sosa:Actuator` | 15536 | 1 | no | n/a | 3 | fails |
| C | B minus `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` | 15535 | 0 | yes | 0 | 0 | clean |
| D | B minus active `sosa:Actuator` mapping expression | 15512 | 0 | yes | 0 | 0 | clean |
| E | B minus active `sosa:Actuation` mapping expression | 15526 | 1 | no | n/a | 3 | fails |
| F | B minus active `ssn-system:ActuationRange` mapping expression | 15499 | 1 | no | n/a | 2 | partially reduced |
| G | B minus imported source `ssn-system:ActuationRange` package | 15521 | 1 | no | n/a | 3 | fails |
| H | B minus all three active class mappings for `Actuator`, `Actuation`, and `ActuationRange` | 15465 | 0 | yes | 0 | 0 | clean |
| I | B minus imported source `sosa:Actuation` package | 15494 | 0 | yes | 0 | 0 | clean |
| J | B minus imported source `sosa:Actuator` package | 15521 | 0 | yes | 0 | 0 | clean |

### Unsatisfiable Sets

Variant B, the held-back range axiom test, reported:

```text
sosa:Actuation
sosa:Actuator
ssn-system:ActuationRange
```

Variant F, removing only the active `ssn-system:ActuationRange` mapping expression, reported:

```text
sosa:Actuation
sosa:Actuator
```

All clean variants produced a reasoned output with `owl:Nothing` count 0.

## Range Entailment / Redundancy Probe

After the reducer variants above, an additional entailment probe checked whether the current baseline already entails the effective range behavior for `sosa:madeByActuator`.

The probe class was added only to a temporary copy of the current baseline:

```ttl
probe:MadeByActuatorNonActuatorProbe
    owl:equivalentClass [
        rdf:type owl:Restriction ;
        owl:onProperty sosa:madeByActuator ;
        owl:someValuesFrom [
            rdf:type owl:Class ;
            owl:complementOf sosa:Actuator
        ]
    ] .
```

HermiT result:

| Probe | Triples | Return | Reasoned output | Unsats | Result |
|---|---:|---:|---|---:|---|
| `sosa:madeByActuator some owl:Thing` | 15540 | 0 | yes | 0 | satisfiable |
| `sosa:madeByActuator some sosa:Actuator` | 15540 | 0 | yes | 0 | satisfiable |
| `sosa:madeByActuator some (not sosa:Actuator)` | 15542 | 1 | no | 1 | unsatisfiable |

The unsatisfiable probe class was:

```text
http://example.org/ssn-to-bfo/hermit-probe/MadeByActuatorNonActuatorProbe
```

This means the current baseline already entails the range behavior:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The result is not merely an empty-property artifact: `sosa:madeByActuator some owl:Thing` and `sosa:madeByActuator some sosa:Actuator` are both satisfiable in the same baseline.

The likely source of the entailed behavior is the combination of:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
sosa:Actuation rdfs:subClassOf [
    owl:onProperty sosa:madeByActuator ;
    owl:allValuesFrom sosa:Actuator
] .
```

Together, these imply that whenever `x sosa:madeByActuator y`, the subject `x` is an `sosa:Actuation`, and therefore every `sosa:madeByActuator` value of `x` is an `sosa:Actuator`.

This refines the diagnostic substantially: the explicit range axiom should be logically redundant in the current baseline. Therefore, the earlier temporary-graph failure after adding the explicit range axiom should be treated as a graph-construction or explanation-debug target, not as evidence that the range behavior itself is absent from the baseline or newly introduced by the explicit `rdfs:range` triple.

## Reducer Findings

### Property Mapping Dependency

Removing exactly this active property mapping clears the failure:

```ttl
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

This is the strongest reducer in the explicit-range test set. However, the redundancy probe above shows that the current baseline already entails the range behavior. Therefore this reducer should be read as identifying a high-impact interaction around the explicit range-axiom test graph, not as proof that the explicit range triple introduces wholly new `sosa:Actuator` typing.

### `sosa:Actuator` Mapping Dependency

Removing the active `sosa:Actuator` class expression also clears the failure. That class expression maps `Actuator` into material-entity, bearer-of, realization, and `agent in` context involving `sosa:Actuation`.

This indicates that the explicit-range failure involves the active `sosa:Actuator` mapping expression. Because the range behavior is already entailed in the baseline, this should be treated as an explanation-debug clue rather than a final causal explanation.

### `sosa:Actuation` Mapping Dependency

Removing only the active `sosa:Actuation` mapping expression does not clear the failure. The same three classes remain unsatisfiable.

This does not mean the `sosa:Actuation` mapping is irrelevant to the full modeling picture, but it was not a sufficient reducer in this test.

### `ssn-system:ActuationRange` Dependency

Removing the active `ssn-system:ActuationRange` mapping expression removes `ssn-system:ActuationRange` from the reported unsat set, but leaves:

```text
sosa:Actuation
sosa:Actuator
```

Removing the imported source package directly attached to `ssn-system:ActuationRange` does not reduce the failure. This suggests `ActuationRange` is a downstream member of the cluster, while the core conflict remains in the `madeByActuator` / `Actuator` / `Actuation` interaction.

### Source Context Dependency

Removing either imported source package clears the failure:

- source package for `sosa:Actuation`
- source package for `sosa:Actuator`

This confirms that the explicit-range failure appears in mixed source/mapping context. The redundancy probe prevents a stronger conclusion: the effective range behavior is already present, so the remaining question is why an explicit redundant range triple changes the HermiT outcome in the temporary test graph.

## Explanation Assessment

The held-back range axiom, when added explicitly to the temporary graph, fails in the current mapped context:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The range entailment probe shows that the current baseline already entails the effective range behavior. The explicit range triple should therefore be logically redundant. The observed failure depends on, or at least is cleared by removing, these tested ingredients:

1. The active property mapping:

   ```ttl
   sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
   ```

2. The active `sosa:Actuator` class-expression mapping.

3. Imported SOSA source restrictions around `sosa:Actuation`, `sosa:Actuator`, and `sosa:madeByActuator`.

The earlier working hypothesis was:

- The explicit range axiom globally classifies every `madeByActuator` object as `sosa:Actuator`.
- The same property is actively mapped to CCO `has agent`, a subproperty of BFO `has participant`.
- `sosa:Actuator` is mapped into material-entity plus `agent in` / realization context involving `sosa:Actuation`.
- Imported SOSA source axioms connect `sosa:Actuation` and `sosa:Actuator` through `madeByActuator`, `madeActuation`, and cardinality/all-values restrictions.
- `ssn-system:ActuationRange` is pulled into the reported cluster through its active class expression and source/mapping references to `sosa:Actuation` and `sosa:Actuator`.

The redundancy probe refines that hypothesis. Since the baseline already entails `madeByActuator` values are `sosa:Actuator`, the explicit range axiom should not add that semantic commitment. The current diagnostic therefore cannot conclude that the range behavior itself is the direct cause of the three-class failure. Instead, it identifies a discrepancy requiring graph-construction or explanation-debug follow-up.

The current active domain axiom is independently safe in the integrated graph:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

That domain axiom remains active in the current baseline, and Variant A confirms the current graph is HermiT-clean with it present. The probe also shows that this domain axiom, together with the imported `sosa:Actuation` all-values restriction, already provides the effective range behavior.

This diagnostic does not prove that the source-level range axiom is semantically wrong in SOSA terms. It also no longer supports the simpler conclusion that the explicit range axiom adds a new unsafe classification path. The more precise conclusion is that the current baseline already entails the range behavior, while the explicit redundant range triple still reproduced the earlier HermiT failure in the temporary graph. That discrepancy needs explanation tooling or graph-construction review before a final modeling decision.

## Recommendation

Keep this explicit axiom held back for now:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

Keep the already-added domain axiom active:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

Do not add the explicit range axiom until the redundancy discrepancy is understood. The next branch should focus on graph-construction and explanation debugging, not replacement design yet:

```text
review/debug-madeByActuator-range-redundancy-discrepancy
```

That branch should verify whether the explicit range-axiom failure is reproduced by an independently generated OWL file, inspect the HermiT explanation for the probe and the explicit-range failure, and determine why a logically redundant source-level range assertion changes the observed HermiT result.
