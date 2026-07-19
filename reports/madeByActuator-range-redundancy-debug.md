# `sosa:madeByActuator` Range Redundancy Debug

## Scope

This report debugs the apparent redundancy discrepancy around the held-back axiom:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

It is report-only. It does not edit `SSN2BFO.ttl`, the workbook, imports, examples, generated artifacts, tools, or existing reports.

Local context:

- Branch: `review/debug-madeByActuator-range-redundancy-discrepancy`
- Commit: `e3eb0b7`
- Temporary directory: `/tmp/ssn-to-bfo-madeByActuator-range-redundancy-debug`
- ROBOT: `ROBOT version 1.9.7`
- Java: `22.0.2`

## Current Baseline

The stable baseline remains:

- validation suite: PASS
- `ttl_candidate_mapping_assertions=71`
- audit issues: 2 expected `sosa:Sensor` version-alignment issues only
- ELK direct class expectations: 6
- ELK direct property expectations: 77
- property-chain expectations: 5
- restriction expectations: 2
- active direct/property-chain/restriction mappings not covered: 0
- current HermiT M2 baseline: clean under established cleanup conditions

The current baseline includes:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

The current baseline does not include:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

## Method

All variants used one shared graph-construction procedure:

1. Parse:

   ```text
   imports/cco.ttl
   imports/ssn.ttl
   imports/ssn-systems.ttl
   SSN2BFO.ttl
   ```

2. Remove:

   ```text
   all owl:imports triples
   sosa:isSampleOf rdf:type owl:FunctionalProperty
   sosa:hasSample rdf:type owl:InverseFunctionalProperty
   ```

3. Add only the variant-specific range axiom or probe class.

4. Run:

   ```bash
   robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
   ```

For the baseline graph:

- triple count: 15535
- `sosa:madeByActuator rdfs:domain sosa:Actuation`: present
- `sosa:madeByActuator rdfs:range sosa:Actuator`: absent
- source restriction present: `sosa:Actuation rdfs:subClassOf [ owl:onProperty sosa:madeByActuator ; owl:allValuesFrom sosa:Actuator ]`
- no variant reintroduced the sample simplicity blocker

The temporary graph construction did not pass a ROBOT `--catalog` option. The input graphs were no-imports serialized Turtle files.

## Variant Results

| Variant | Added content | Triples | Return | Reasoned output | `owl:Nothing` | Unsats | Result |
|---|---|---:|---:|---|---:|---:|---|
| A | none | 15535 | 0 | yes | 0 | 0 | clean |
| B | explicit `sosa:madeByActuator rdfs:range sosa:Actuator` | 15536 | 1 | no | n/a | 3 | fails |
| C | non-Actuator probe | 15542 | 1 | no | n/a | 1 | probe unsat |
| D | Thing probe | 15540 | 0 | yes | 0 | 0 | satisfiable |
| E | Actuator probe | 15540 | 0 | yes | 0 | 0 | satisfiable |
| F | explicit range plus non-Actuator probe | 15543 | 1 | no | n/a | 4 | fails |

Variant B unsatisfiable set:

```text
sosa:Actuation
sosa:Actuator
ssn-system:ActuationRange
```

Variant C unsatisfiable set:

```text
probe:MadeByActuatorNonActuatorProbe
```

Variant F unsatisfiable set:

```text
probe:MadeByActuatorNonActuatorProbe
sosa:Actuation
sosa:Actuator
ssn-system:ActuationRange
```

## Probe Definitions

Variant C added this fresh probe class:

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

Variant D added:

```text
sosa:madeByActuator some owl:Thing
```

Variant E added:

```text
sosa:madeByActuator some sosa:Actuator
```

Variants D and E were satisfiable. This means Variant C is not unsatisfiable merely because `sosa:madeByActuator` is unusable or empty.

## B/C Graph Comparison

An in-memory graph delta was used so serialized blank-node identifiers would not create false differences.

Variant B minus Variant A contains exactly one added triple:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

Variant C minus Variant A contains exactly the seven triples needed to define the non-Actuator probe class:

```ttl
probe:MadeByActuatorNonActuatorProbe rdf:type owl:Class .
probe:MadeByActuatorNonActuatorProbe owl:equivalentClass _:restriction .
_:restriction rdf:type owl:Restriction .
_:restriction owl:onProperty sosa:madeByActuator .
_:restriction owl:someValuesFrom _:notActuator .
_:notActuator rdf:type owl:Class .
_:notActuator owl:complementOf sosa:Actuator .
```

IRI checks:

- Variant B uses exactly `http://www.w3.org/ns/sosa/madeByActuator`.
- Variant B uses exactly `http://www.w3.org/ns/sosa/Actuator`.
- Variant C uses the same property and class IRIs in the probe.
- No malformed RDF list or probe blank-node shape was found.
- No duplicate or unintended named triples were identified.
- `sosa:madeByActuator rdf:type owl:ObjectProperty` is not explicitly present in A, B, or C, so an explicit object-property declaration is not a B/C difference.

## Direct Entailment Check

The baseline reasoned output did not materialize this explicit schema triple:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

That is not decisive: ROBOT/HermiT does not necessarily serialize all entailed schema axioms into the reasoned output.

An attempted ROBOT `explain --mode entailment` call for the `ObjectPropertyRange` axiom did not parse the axiom syntax accepted by this ROBOT invocation, so no direct range-axiom explanation was produced.

The indirect probe is therefore the operative entailment test in this report. Variant C shows that:

```text
sosa:madeByActuator some (not sosa:Actuator)
```

is unsatisfiable in the current baseline graph.

The ROBOT explanation for Variant C was small and direct:

```text
MadeByActuatorNonActuatorProbe EquivalentTo madeByActuator some not Actuator
madeByActuator Domain Actuation
Actuation SubClassOf madeByActuator only Actuator
```

This confirms the current baseline already entails the effective range behavior:

```text
if x sosa:madeByActuator y, then y rdf:type sosa:Actuator
```

## Explanation Extraction

ROBOT explanation extraction with `--unsatisfiable all --max 1` succeeded for both Variant B and Variant C.

### Variant C Probe Explanation

The probe explanation confirms the expected local entailment pattern:

```text
madeByActuator Domain Actuation
Actuation SubClassOf madeByActuator only Actuator
```

Together these make `madeByActuator some (not Actuator)` unsatisfiable.

### Variant B Explicit-Range Explanation

Variant B explanations for `sosa:Actuation`, `sosa:Actuator`, and `ssn-system:ActuationRange` used the explicit range axiom as an axiom in the unsatisfiability proof:

```text
madeByActuator Range Actuator
madeByActuator SubPropertyOf has agent
has agent SubPropertyOf has participant
Actuator SubClassOf material entity and bearer/realization/agent-in Actuation context
Actuation EquivalentTo Planned Act and actsOnProperty some ActuatableProperty
Actuation SubClassOf madeByActuator exactly 1 Thing
```

The explanation also referenced:

- CCO/BFO `affects` / `has participant` context
- disjointness between continuant and occurrent
- disjointness among independent continuant, specifically dependent continuant, and generically dependent continuant
- `sosa:Platform` / `sosa:hosts` / `ssn:System` mapping context
- the active `ssn-system:ActuationRange` class expression for the `ActuationRange` member of the cluster

This explains why the explicit range axiom participates in the failure, but it does not resolve why the semantically equivalent range behavior from Variant C does not already make the same named classes unsatisfiable in Variant A.

## Interpretation

This diagnostic lands in Case 3:

```text
B fails and C shows baseline range behavior.
```

The explicit range failure still reproduces in a fresh graph built from the same constructor as the probe variants:

```text
sosa:Actuation
sosa:Actuator
ssn-system:ActuationRange
```

The current baseline also already entails the effective range behavior, as shown by the non-Actuator probe:

```text
sosa:madeByActuator some (not sosa:Actuator)
```

being unsatisfiable.

Under OWL monotonicity, if the explicit `ObjectPropertyRange` axiom is truly entailed by the same graph, adding it should not make previously satisfiable named classes unsatisfiable. The fresh graph comparison rules out the easy explanations:

- not a stale temporary graph;
- not a wrong SOSA IRI;
- not a malformed probe;
- not an accidental large graph delta;
- not caused by `owl:imports`, because imports were removed before reasoning;
- not caused by a changed explicit `owl:ObjectProperty` declaration, because none is present in A, B, or C.

The remaining discrepancy appears to be in how the ROBOT/HermiT workflow handles the inferred range behavior when it is implicit through domain plus all-values restriction versus explicit as an `ObjectPropertyRange` axiom. The explicit axiom is used directly in Variant B explanations, while the implicit pattern is sufficient only to make the local non-Actuator probe unsatisfiable.

This report does not prove that the source-level range axiom is semantically wrong. It shows that the explicit range axiom is not currently safe to add, even though an equivalent range-like consequence appears to hold for the probe.

## Recommendation

Keep this explicit axiom held back for now:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The already-active domain axiom can remain active:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

Do not proceed directly to a mapping-change branch for the range axiom. The next step should be deeper explanation/minimal-reproduction work, preferably:

```text
review/minimize-madeByActuator-range-redundancy-discrepancy
```

That branch should build a small ontology containing only the axioms used in the Variant B and Variant C explanations, then compare:

- implicit range via domain plus all-values restriction;
- explicit `ObjectPropertyRange`;
- explicit `rdf:type owl:ObjectProperty`;
- HermiT versus another available OWL DL reasoner if locally available.

Only if the minimized reproduction shows the explicit axiom is safe, or identifies a narrow mapping adjustment that makes it safe, should the range axiom be reconsidered for an active mapping-change branch.
