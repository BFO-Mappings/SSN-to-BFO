# SOSA Actuation Agent Unsat Explanation

## Scope

This report explains the full local SOSA closure HermiT inconsistency involving:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

No mappings, workbook rows, imports, examples, tools, or generated/release artifacts were edited. Temporary files were written under:

```text
/tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation
```

All HermiT variants used the full local SOSA closure graph:

```text
imports/cco.ttl
imports/sosa.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

Then each graph removed:

```text
all owl:imports triples
sosa:isSampleOf rdf:type owl:FunctionalProperty
sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

## Direct Explanation Extraction

ROBOT explanation support is available:

```bash
robot explain --help
```

The local ROBOT command supports `--mode unsatisfiability`, but it does not accept a class IRI as the value of `--unsatisfiable`. This attempted individual-class command failed:

```bash
robot explain \
  --input /tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation/B0_full_sosa_baseline.ttl \
  --reasoner HermiT \
  --mode unsatisfiability \
  --unsatisfiable http://www.w3.org/ns/sosa/Actuator \
  --max 1 \
  --explanation /tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation/explain-actuator.md \
  --output /tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation/explain-actuator.ttl
```

Error summary:

```text
ILLEGAL UNSATISFIABLE ARGUMENT ERROR
Must have either a valid --unsatisfiable option: all, root, most_general, random:n
```

Supported fallback explanation commands succeeded:

```bash
robot explain \
  --input /tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation/B0_full_sosa_baseline.ttl \
  --reasoner HermiT \
  --mode unsatisfiability \
  --unsatisfiable all \
  --max 1 \
  --explanation /tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation/explain-all.md \
  --output /tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation/explain-all.ttl
```

Additional supported commands with `--unsatisfiable root` and `--unsatisfiable random:1` also succeeded.

Important caution: the Markdown explanations were useful, but the explanation ontology outputs were nearly full-graph modules rather than compact minimal reproducer ontologies. For example, `explain-all.ttl` contained 15760 triples, while the full baseline variant contained 15770 triples.

## Explanation Axiom Cluster

The ROBOT explanation for the three unsatisfiable classes repeatedly used this practical cluster:

- `sosa:Actuation` equivalent to `cco:ont00000228` and `sosa:actsOnProperty some sosa:ActuatableProperty`.
- `sosa:Actuation` source restrictions:
  - `sosa:madeByActuator only sosa:Actuator`
  - `sosa:madeByActuator exactly 1 owl:Thing`
- `sosa:Actuator` source and mapping context:
  - `sosa:Actuator subClassOf ssn:System`
  - active BFO/CCO mapping to `bfo:BFO_0000040` and bearer/realization/agent-in actuation context
  - `cco:ont00001787 some sosa:Actuation`
- Actuation-side CCO property mappings:
  - `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833`
  - `cco:ont00001833 rdfs:subPropertyOf bfo:BFO_0000057`
  - `sosa:madeActuation rdfs:subPropertyOf cco:ont00001787`
  - `cco:ont00001787 rdfs:subPropertyOf bfo:BFO_0000056`
- CCO/BFO inverse and parent context:
  - `cco:ont00001787 owl:inverseOf cco:ont00001833`
  - `bfo:BFO_0000054 owl:inverseOf bfo:BFO_0000055`
  - `bfo:BFO_0000196 owl:inverseOf bfo:BFO_0000197`
- Hosting/property-chain context:
  - `bfo:BFO_0000056 o bfo:BFO_0000055 o bfo:BFO_0000197 subPropertyOf sosa:isHostedBy`
  - `bfo:BFO_0000196 o bfo:BFO_0000054 o bfo:BFO_0000057 subPropertyOf sosa:hosts`
  - `sosa:hosts owl:inverseOf sosa:isHostedBy`
- BFO disjointness:
  - continuant disjoint with occurrent
  - independent continuant disjoint with specifically dependent continuant

For `ssn-system:ActuationRange`, the explanation additionally used the active `ActuationRange` class expression:

```text
function
and has realization some
  (sosa:Actuation
   and has output some specifically dependent continuant
   and prescribed by some Artifact Function Specification)
```

This makes `ActuationRange` a downstream member of the cluster: removing its mapping removes `ActuationRange` from the unsat set but leaves `sosa:Actuator` and `sosa:Actuation` unsatisfiable.

## HermiT Variant Results

Command shape:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

All graph paths use the prefix:

```text
/tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation/
```

| Variant | Graph file | Temporary edit | Triples | Return | Output | `owl:Nothing` | Unsats | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| A | `A_full_sosa_baseline.ttl` | none | 15770 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B | `B_remove_both_sosa_agent_mappings.ttl` | remove both `madeActuation -> agent_in` and `madeByActuator -> has_agent` | 15768 | 0 | yes | 0 | 0 | clean |
| C | `C_remove_cco_agent_inverse.ttl` | remove `cco:ont00001787 owl:inverseOf cco:ont00001833` | 15769 | 1 | no | n/a | 3 | same 3 |
| D | `D_remove_has_agent_parent_path.ttl` | remove `cco:ont00001833 rdfs:subPropertyOf bfo:BFO_0000057` | 15769 | 1 | no | n/a | 3 | same 3 |
| E | `E_remove_agent_in_parent_path.ttl` | remove `cco:ont00001787 rdfs:subPropertyOf bfo:BFO_0000056` | 15769 | 1 | no | n/a | 3 | same 3 |
| F | `F_remove_both_parent_paths.ttl` | remove both CCO/BFO parent paths | 15768 | 0 | yes | 0 | 0 | clean |
| G | `G_keep_only_madeActuation_route_inverse_blocked.ttl` | remove `madeByActuator -> has_agent` and CCO inverse; keep `madeActuation -> agent_in` | 15768 | 1 | no | n/a | 3 | same 3 |
| H | `H_keep_only_madeByActuator_route_inverse_blocked.ttl` | remove `madeActuation -> agent_in` and CCO inverse; keep `madeByActuator -> has_agent` | 15768 | 1 | no | n/a | 3 | same 3 |
| I | `I_remove_sosa_object_property_declarations.ttl` | remove SOSA `owl:ObjectProperty` declarations for both actuation properties | 15768 | 1 | no | n/a | 3 | same 3 |
| J | `J_remove_source_actuation_actuator_restrictions.ttl` | remove source restrictions using `madeByActuator` / `madeActuation` | 15758 | 0 | yes | 0 | 0 | clean |
| K1 | `K1_precise_remove_actuation_mapping.ttl` | remove active `sosa:Actuation` CCO planned-act mapping only | 15760 | 1 | no | n/a | 3 | same 3 |
| K2 | `K2_precise_remove_actuator_mapping.ttl` | remove active `sosa:Actuator` BFO/CCO class mapping only | 15746 | 0 | yes | 0 | 0 | clean |
| K3 | `K3_precise_remove_both_actuation_actuator_mappings.ttl` | remove both active Actuation/Actuator class mappings | 15736 | 0 | yes | 0 | 0 | clean |
| L | `L_precise_remove_actuation_range_mapping.ttl` | remove active `ssn-system:ActuationRange` BFO/CCO class mapping only | 15742 | 1 | no | n/a | 2 | `sosa:Actuator`, `sosa:Actuation` |

The sample simplicity blockers did not reappear in any variant.

## Exact High-Impact Removals

Variant B removed exactly:

```ttl
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

Variant F removed exactly:

```ttl
cco:ont00001833 rdfs:subPropertyOf bfo:BFO_0000057 .
cco:ont00001787 rdfs:subPropertyOf bfo:BFO_0000056 .
```

Variant J removed the three source restrictions directly coupling the source classes to the actuation properties:

```text
sosa:Actuation subClassOf madeByActuator only sosa:Actuator
sosa:Actuation subClassOf madeByActuator exactly 1 owl:Thing
sosa:Actuator subClassOf madeActuation only sosa:Actuation
```

Variant K2 removed only the active `sosa:Actuator` BFO/CCO class-expression mapping:

```text
sosa:Actuator subClassOf
  bfo:BFO_0000040
  and bfo:BFO_0000196 some
      (bfo:BFO_0000017 and bfo:BFO_0000054 some sosa:Actuation)
  and cco:ont00001787 some sosa:Actuation
```

Variant L removed the active `ssn-system:ActuationRange` BFO/CCO mapping. It did not clear `sosa:Actuator` or `sosa:Actuation`, which supports treating `ActuationRange` as downstream rather than the root cause.

## Parent And Inverse Reconstruction

The CCO parent/inverse context is:

```ttl
cco:ont00001787 rdfs:label "agent in" ;
    rdfs:subPropertyOf bfo:BFO_0000056 ;
    owl:inverseOf cco:ont00001833 .

cco:ont00001833 rdfs:label "has agent" ;
    rdfs:subPropertyOf bfo:BFO_0000057 .
```

`bfo:BFO_0000056` is `participates in`; `bfo:BFO_0000057` is `has participant`; those BFO properties are inverse directions.

Removing the CCO inverse axiom alone does not clear the inconsistency. More importantly, variants G and H show that either route is sufficient when the CCO inverse reconstruction is blocked:

- Keeping only `sosa:madeActuation -> cco:agent_in` still fails.
- Keeping only `sosa:madeByActuator -> cco:has_agent` still fails.

That means the failure is not merely that one source mapping reconstructs the other through CCO inverse semantics. Instead, either actuation-side route can reach the BFO participant/participates-in machinery strongly enough to participate in the same class-level contradiction, given the source restrictions and active `sosa:Actuator` class mapping.

This explains why removing only one of the two SOSA-to-CCO mappings does not clear the full-closure inconsistency. Removing both cuts both participant routes. Removing both CCO/BFO parent paths also cuts both participant routes while leaving the direct SOSA-to-CCO mappings in place.

## Minimal Reproducer Attempt

A hand-built focused graph was created at:

```text
/tmp/ssn-to-bfo-sosa-actuation-agent-unsat-explanation/minimal-candidate.ttl
```

It included 131 triples from the visible ROBOT explanation skeleton:

- `sosa:madeActuation`
- `sosa:madeByActuator`
- `sosa:Actuator`
- `sosa:Actuation`
- immediate `cco:agent_in` / `cco:has_agent` parent paths
- relevant source restrictions
- active Actuator and Actuation class mapping shapes
- relevant BFO disjointness, inverse properties, and property-chain axioms

Result:

| Graph | Triples | Return | Reasoned output | `owl:Nothing` | Result |
|---|---:|---:|---|---:|---|
| `minimal-candidate.ttl` | 131 | 0 | yes | 0 | clean |

So the hand-built explanation skeleton did not reproduce the unsats. The missing support is likely additional BFO/CCO superclass, domain/range, or property-chain context not captured in the first compact approximation. The smallest failing graphs tested in this branch remain full-closure variants with narrow removals, while the most useful explanation artifact is the ROBOT Markdown proof rather than its near-full ontology module.

## Interpretation

The issue is not caused by explicit:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

In the full local SOSA closure, the graph is already inconsistent before that axiom is added.

The issue is not caused by the SOSA inverse axiom alone. Earlier materialization testing showed that removing the SOSA inverse alone did not clear the cluster, and this report shows that removing the CCO inverse alone also does not clear it.

The issue is not caused by only one of the two actuation-side CCO agent mappings in isolation. Variants G and H show each remaining route can still fail when the other route and CCO inverse reconstruction are blocked.

The strongest practical explanation currently found is a mixed cluster:

1. SOSA source restrictions require `Actuation` to have exactly one `madeByActuator` value, and all such values are `Actuator`; `Actuator` values are restricted through `madeActuation`.
2. The active `sosa:Actuator` class mapping makes Actuator a material entity with realization/agent-in Actuation commitments.
3. The active actuation-side property mappings send `madeByActuator` and/or `madeActuation` into CCO/BFO participant paths.
4. BFO/CCO property chains and disjointness then force incompatible continuant/occurrent or independent-continuant/specific-dependent-continuant classifications.
5. `ssn-system:ActuationRange` becomes unsatisfiable because its active mapping realizes in `sosa:Actuation`; removing that mapping leaves the two-class Actuator/Actuation core.

`ssn-system:ActuationRange` is downstream, not the root cause.

## Recommendation

Recommend exactly one next step:

```text
fix/defer-actuation-agent-property-mappings
```

That branch should temporarily defer both active direct property mappings together:

```ttl
sosa:madeActuation rdfs:subPropertyOf cco:ont00001787 .
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

The rationale should be narrow: the direct CCO/BFO participant representation is not HermiT-safe in the full local SOSA closure. This does not prove the intended agent semantics are invalid. It means the active OWL representation should be deferred pending a HermiT-safe replacement, likely source-level typing and/or a reviewed rule/COMS treatment.

Do not treat `ssn-system:ActuationRange` as the fix target for this cluster.
