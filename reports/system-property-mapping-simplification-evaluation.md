# `ssn-system:SystemProperty` Mapping Simplification Evaluation

## Scope

This report evaluates temporary HermiT-only simplifications of the active `ssn-system:SystemProperty` mapping. It does not edit `SSN2BFO.ttl`, the workbook, imports, examples, tools, generated artifacts, release artifacts, or existing reports.

This report does not add:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The `madeByActuator` range variants are included only as secondary controls to check whether `SystemProperty` simplification affects that separate issue.

## Current Baseline

Current branch:

```text
review/evaluate-system-property-mapping-simplification
```

Current commit:

```text
2490c89
```

Current stable baseline:

| Check | Baseline |
|---|---:|
| validation suite | PASS |
| `ttl_candidate_mapping_assertions` | 71 |
| audit issues | 2 expected `sosa:Sensor` version-alignment issues only |
| ELK direct class expectations | 6 |
| ELK direct property expectations | 77 |
| ELK property-chain expectations | 5 |
| ELK restriction expectations | 2 |
| active direct/property-chain/restriction mappings not covered | 0 |
| current HermiT M2 baseline under established cleanup | clean |

## Current `SystemProperty` Mapping

The active `SSN2BFO.ttl` mapping is:

```ttl
ssn-system:SystemProperty
  rdfs:subClassOf [
    owl:intersectionOf (
      [ owl:unionOf (
          bfo:BFO_0000020
          bfo:BFO_0000144
        ) ]
      [ owl:onProperty cco:ont00001920 ;
        owl:someValuesFrom cco:ont00000118 ]
    )
  ] .
```

In shorthand:

```text
(specifically dependent continuant or Process Profile)
and prescribed_by some Artifact Function Specification
```

Relevant local labels:

| IRI | Label |
|---|---|
| `bfo:BFO_0000020` | specifically dependent continuant |
| `bfo:BFO_0000144` | Process Profile |
| `cco:ont00001920` | prescribed by |
| `cco:ont00000118` | Artifact Function Specification |

The workbook row is `System Capability` row 32:

| Cell | Current value summary |
|---|---|
| `A32` | `ssn-system:SystemProperty` |
| `B32` | Source definition: an identifiable and observable characteristic representing the system's ability to operate its primary purpose |
| `C32` | BFO definition: specifically dependent continuant or process profile characterizing system performance as prescribed by a functional specification |
| `D32` | Natural-language OWL includes SDC-or-ProcessProfile plus prescribed by AFS |
| `E32` | `subClassOf (bfo:SpecificallyDependentContinuant or bfo:ProcessProfile) and cco:prescribed_by some cco:ArtifactFunctionSpecification` |
| `F32` | Rationale says the properties are determined by functional design intent |

## Source Context

The imported `imports/ssn-systems.ttl` source context defines:

```ttl
ssn-system:SystemProperty
  rdfs:subClassOf
    ssn:Property ,
    [ owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
      owl:allValuesFrom ssn-system:SystemCapability ] ,
    [ owl:onProperty [ owl:inverseOf ssn-system:hasSystemProperty ] ;
      owl:minCardinality 1 ] .
```

The relevant subclasses inspected in the source ontology are subclasses of `ssn-system:SystemProperty`, including:

```text
ssn-system:Accuracy
ssn-system:ActuationRange
ssn-system:DetectionLimit
ssn-system:Drift
ssn-system:Frequency
ssn-system:Latency
ssn-system:MeasurementRange
ssn-system:Precision
ssn-system:Resolution
ssn-system:ResponseTime
ssn-system:Selectivity
ssn-system:Sensitivity
```

The source context for `ssn-system:SystemProperty` does not assert an artifact-function-specification prescription requirement. The `prescribed_by some ArtifactFunctionSpecification` branch is therefore a mapping-side modeling commitment, supported by workbook rationale rather than by the imported source axioms.

## Inherited Union Evidence

The broader union target appears to be inherited without the direct `SystemProperty` mapping.

The source ontology states:

```ttl
ssn-system:SystemProperty rdfs:subClassOf ssn:Property .
```

The active mapping for `ssn:Property` states:

```ttl
ssn:Property
  owl:equivalentClass [
    owl:unionOf (
      bfo:BFO_0000020
      bfo:BFO_0000144
    )
  ] .
```

Therefore, even if the direct `ssn-system:SystemProperty` mapping is removed, the current graph should still entail:

```text
SystemProperty subclassOf (specifically dependent continuant or Process Profile)
```

The probe test below confirms that expectation.

## HermiT Method

Temporary files were written only under:

```text
/tmp/ssn-to-bfo-system-property-mapping-simplification
```

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

Each variant was run with:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

Tool versions:

| Tool | Version |
|---|---|
| ROBOT | 1.9.7 |
| Java | 22.0.2 |

No variant reintroduced the sample simplicity blocker.

## Candidate Variants

| Candidate | Temporary edit |
|---|---|
| A | Remove only the `prescribed_by some ArtifactFunctionSpecification` branch, leaving `SystemProperty subclassOf (SDC or ProcessProfile)` |
| B | Remove the active direct `SystemProperty` class-expression mapping entirely, relying on source `SystemProperty subclassOf ssn:Property` and active `ssn:Property` mapping |
| C | Current mapping plus explicit `sosa:madeByActuator rdfs:range sosa:Actuator` |
| D | Candidate A plus explicit `sosa:madeByActuator rdfs:range sosa:Actuator` |
| E | Candidate B plus explicit `sosa:madeByActuator rdfs:range sosa:Actuator` |

## Variant Results

| Variant | Temporary edit | Graph path | Triples | Return | Reasoned output | `owl:Nothing` | Unsat set |
|---|---|---|---:|---:|---|---:|---|
| A0 | Current baseline | `/tmp/ssn-to-bfo-system-property-mapping-simplification/A0-baseline-current.ttl` | 15526 | 0 | yes | 0 | none |
| A | Union-only simplification | `/tmp/ssn-to-bfo-system-property-mapping-simplification/A-candidate-union-only.ttl` | 15517 | 0 | yes | 0 | none |
| B | Remove direct `SystemProperty` mapping | `/tmp/ssn-to-bfo-system-property-mapping-simplification/B-remove-SystemProperty-mapping.ttl` | 15510 | 0 | yes | 0 | none |
| C | Current mapping plus explicit `madeByActuator` range | `/tmp/ssn-to-bfo-system-property-mapping-simplification/C-current-plus-madeByActuator-range.ttl` | 15527 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| D | Candidate A plus explicit `madeByActuator` range | `/tmp/ssn-to-bfo-system-property-mapping-simplification/D-union-only-plus-madeByActuator-range.ttl` | 15518 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |
| E | Candidate B plus explicit `madeByActuator` range | `/tmp/ssn-to-bfo-system-property-mapping-simplification/E-remove-SystemProperty-plus-madeByActuator-range.ttl` | 15511 | 1 | no | n/a | `sosa:Actuator`; `sosa:Actuation`; `ssn-system:ActuationRange` |

Candidate A and Candidate B are both HermiT-clean. Neither changes the separate `madeByActuator` range failure.

## Entailment Probe

To test whether the union target remains entailed without the direct `SystemProperty` mapping, the diagnostic added a temporary probe class equivalent to:

```text
SystemProperty and not (specifically dependent continuant or Process Profile)
```

Probe results:

| Probe | Temporary edit | Triples | Return | Reasoned output | Unsat set |
|---|---|---:|---:|---|---|
| P1 | Baseline plus non-union probe | 15542 | 1 | no | `SystemPropertyNonUnionProbeBaseline` |
| P2 | Remove direct `SystemProperty` mapping plus non-union probe | 15526 | 1 | no | `SystemPropertyNonUnionProbeNoDirectMapping` |

The P2 result shows that the graph still entails the SDC-or-ProcessProfile union for `SystemProperty` without the direct `SystemProperty` mapping. The entailment follows from:

```text
SystemProperty subclassOf ssn:Property
ssn:Property equivalentTo (SDC or ProcessProfile)
```

## Interpretation

### Is the current mapping HermiT-clean?

Yes. The current baseline is HermiT-clean.

### Is the `prescribed_by some ArtifactFunctionSpecification` branch over-specific?

Yes, relative to the imported source axioms. The source `SystemProperty` commitments identify `SystemProperty` as an `ssn:Property` tied to `SystemCapability` through inverse `hasSystemProperty` restrictions. They do not assert that every `SystemProperty` is prescribed by an artifact function specification.

The branch may reflect a plausible design-intent modeling rationale, but it is stronger than the imported source context and is not needed for the inherited SDC-or-ProcessProfile classification.

### Is Candidate A HermiT-clean?

Yes. Candidate A is HermiT-clean with return code 0 and `owl:Nothing` count 0.

Candidate A removes the over-specific prescription branch while retaining an explicit direct assertion of the inherited union.

### Is Candidate B HermiT-clean?

Yes. Candidate B is HermiT-clean with return code 0 and `owl:Nothing` count 0.

Candidate B is better supported than Candidate A because the SDC-or-ProcessProfile union is already entailed through `ssn:Property`. Candidate B avoids a redundant direct mapping and removes the over-specific prescription branch entirely.

### Does either candidate affect the `madeByActuator` range issue?

No. Candidate C, D, and E all fail with the same unsat set:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

Therefore simplifying or removing the direct `SystemProperty` mapping should not be presented as a fix for the `madeByActuator` range issue.

## Recommendation

Recommend a future mapping-change branch:

```text
fix/defer-system-property-direct-class-mapping
```

That branch should remove the direct active `ssn-system:SystemProperty` class-expression mapping from `SSN2BFO.ttl` and update `System Capability` row 32 in the workbook to say:

- `SystemProperty` remains source-defined as a subclass of `ssn:Property`;
- the SDC-or-ProcessProfile classification is inherited through the active `ssn:Property` mapping;
- no direct `prescribed_by some ArtifactFunctionSpecification` axiom is asserted for `SystemProperty`;
- this change does not add or fix `sosa:madeByActuator rdfs:range sosa:Actuator`.

Do not add the explicit `madeByActuator` range axiom in that branch. The range issue remains a separate mixed-context problem.
