# `sosa:madeByActuator` Range Encoding Options

## Scope

This report evaluates active OWL encoding options for the `sosa:madeByActuator` range behavior.

This is report-only. It does not edit `SSN2BFO.ttl`, the workbook, imports, examples, tools, generated artifacts, release artifacts, or any ontology mapping file.

Temporary files were written under:

```text
/tmp/ssn-to-bfo-madeByActuator-range-encoding-options
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

Relevant prior reports:

- `reports/madeByActuator-range-hermit-failure.md`
- `reports/madeByActuator-range-redundancy-debug.md`
- `reports/madeByActuator-range-minimal-reproduction.md`
- `reports/madeByActuator-agent-mapping-adjustment-evaluation.md`

Prior diagnostics found that:

- `sosa:madeByActuator rdfs:domain sosa:Actuation` is active and HermiT-clean.
- `sosa:madeByActuator rdfs:range sosa:Actuator` is not active.
- `sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833` is active.
- `cco:ont00001833` is `has agent`.
- The current baseline appears to entail effective `madeByActuator` range behavior through the active domain axiom plus the imported `sosa:Actuation` all-values restriction.
- Adding the explicit `rdfs:range sosa:Actuator` axiom still fails HermiT.
- A prior test showed that encoding the range behavior as a global universal restriction was HermiT-clean with the current `madeByActuator -> cco:has_agent` mapping.

## Source And Mapping Context

### Current `madeByActuator` Mapping

Current active TTL:

```ttl
<http://www.w3.org/ns/sosa/madeByActuator>
    rdfs:domain <http://www.w3.org/ns/sosa/Actuation> ;
    rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001833> .
```

The explicit source-level range axiom is absent:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

### Related `madeActuation` Mapping

Current active TTL:

```ttl
<http://www.w3.org/ns/sosa/madeActuation>
    rdfs:domain <http://www.w3.org/ns/sosa/Actuator> ;
    rdfs:range <http://www.w3.org/ns/sosa/Actuation> ;
    rdfs:subPropertyOf <https://www.commoncoreontologies.org/ont00001787> .
```

`cco:ont00001787` is `agent in`, inverse of `cco:ont00001833` in `imports/cco.ttl`.

### Source Restriction Already Present

The imported source ontology already contains:

```ttl
sosa:Actuation rdfs:subClassOf [
    owl:onProperty sosa:madeByActuator ;
    owl:allValuesFrom sosa:Actuator
] .
```

Together with:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation .
```

this gives effective range-like behavior for uses of `madeByActuator`: any subject of `madeByActuator` is typed as `sosa:Actuation`, and `sosa:Actuation` allows only `sosa:Actuator` fillers for that property.

### Workbook Context

Workbook rows inspected:

| Sheet | Row | Source term | Relevant content |
| --- | ---:| --- | --- |
| `Common Classes` | 3 | `sosa:Actuation` | mapped to `cco:PlannedAct and (sosa:actsOnProperty some sosa:ActuatableProperty)` |
| `Common Classes` | 4 | `sosa:Actuator` | mapped as material entity with bearer/realization and `cco:agent_in some sosa:Actuation` |
| `Common OPs` | 27 | `sosa:madeActuation` | domain `sosa:Actuator`, range `sosa:Actuation`, subproperty of `cco:agent_in` |
| `Common OPs` | 28 | `sosa:madeByActuator` | domain `sosa:Actuation`; workbook text notes inverse of `madeActuation`; active CCO `has_agent` mapping remains |

## Encoding Note

In OWL terms, an object-property range axiom:

```text
ObjectPropertyRange(P C)
```

is closely related to:

```text
SubClassOf(owl:Thing ObjectAllValuesFrom(P C))
```

Therefore, one would normally expect explicit `rdfs:range sosa:Actuator` and a global universal restriction over `madeByActuator` to behave the same. The observed HermiT results do not behave that way in this integrated ROBOT/HermiT profile. That difference is the practical encoding concern evaluated here.

## HermiT Method

Every temporary graph was built from:

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

Each run used:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

No variant reintroduced the sample simplicity blocker.

## Variant Results

| Variant | Graph path | Temporary edit | Triples | Return | Reasoned output | `owl:Nothing` | Unsat set | Result |
| --- | --- | --- | ---:| ---:| --- | ---:| --- | --- |
| A | `/tmp/ssn-to-bfo-madeByActuator-range-encoding-options/A-baseline.ttl` | current graph; no explicit range axiom | 15,510 | 0 | yes | 0 | none | clean |
| B | `/tmp/ssn-to-bfo-madeByActuator-range-encoding-options/B-explicit-range.ttl` | add `sosa:madeByActuator rdfs:range sosa:Actuator` | 15,511 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | fails |
| C | `/tmp/ssn-to-bfo-madeByActuator-range-encoding-options/C-global-universal.ttl` | add `owl:Thing subClassOf (madeByActuator only Actuator)`; no `rdfs:range`; keep `madeByActuator -> cco:has_agent` | 15,514 | 0 | yes | 0 | none | clean |
| D | `/tmp/ssn-to-bfo-madeByActuator-range-encoding-options/D-scoped-universal-duplicate.ttl` | add duplicate `sosa:Actuation subClassOf (madeByActuator only Actuator)` | 15,514 | 0 | yes | 0 | none | clean |
| E | `/tmp/ssn-to-bfo-madeByActuator-range-encoding-options/E-remove-has-agent-plus-range.ttl` | remove `madeByActuator -> cco:has_agent`; add explicit range | 15,510 | 0 | yes | 0 | none | clean |
| F | `/tmp/ssn-to-bfo-madeByActuator-range-encoding-options/F-parent-participant-global-universal.ttl` | remove `madeByActuator -> cco:has_agent`; add `madeByActuator -> bfo:has_participant`; add global universal restriction; no `rdfs:range` | 15,514 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | fails |
| G | `/tmp/ssn-to-bfo-madeByActuator-range-encoding-options/G-parent-participant-explicit-range.ttl` | remove `madeByActuator -> cco:has_agent`; add `madeByActuator -> bfo:has_participant`; add explicit range | 15,511 | 1 | no | n/a | `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | fails |

## Scoped Universal Restriction Result

The scoped universal restriction tested in Variant D is already present in the imported source ontology:

```ttl
sosa:Actuation rdfs:subClassOf [
    owl:onProperty sosa:madeByActuator ;
    owl:allValuesFrom sosa:Actuator
] .
```

Adding a duplicate blank-node restriction was HermiT-clean but adds no new semantic content beyond the imported source axiom. Therefore it is not a useful active mapping addition.

## Probe Results

The baseline range-behavior probes were repeated with fresh probe classes:

| Probe context | Probe | Triples | Return | Reasoned output | Unsat set | Interpretation |
| --- | --- | ---:| ---:| --- | --- | --- |
| Baseline | `madeByActuator some owl:Thing` | 15,515 | 0 | yes | none | satisfiable |
| Baseline | `madeByActuator some sosa:Actuator` | 15,515 | 0 | yes | none | satisfiable |
| Baseline | `madeByActuator some (not sosa:Actuator)` | 15,517 | 1 | no | `probe:P-baseline-NonActuatorProbe` | unsatisfiable |
| Variant C | `madeByActuator some owl:Thing` | 15,519 | 0 | yes | none | satisfiable |
| Variant C | `madeByActuator some sosa:Actuator` | 15,519 | 0 | yes | none | satisfiable |
| Variant C | `madeByActuator some (not sosa:Actuator)` | 15,521 | 1 | no | `probe:P-C-global-universal-NonActuatorProbe` | unsatisfiable |
| Variant F | `madeByActuator some owl:Thing` | 15,519 | 1 | no | `probe:P-F-parent-participant-global-universal-ThingProbe`; `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | context already failing |
| Variant F | `madeByActuator some sosa:Actuator` | 15,519 | 1 | no | `probe:P-F-parent-participant-global-universal-ActuatorProbe`; `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | context already failing |
| Variant F | `madeByActuator some (not sosa:Actuator)` | 15,521 | 1 | no | `probe:P-F-parent-participant-global-universal-NonActuatorProbe`; `sosa:Actuation`; `sosa:Actuator`; `ssn-system:ActuationRange` | context already failing |

The baseline probes confirm the effective range behavior:

- `madeByActuator some owl:Thing` is satisfiable;
- `madeByActuator some sosa:Actuator` is satisfiable;
- `madeByActuator some (not sosa:Actuator)` is unsatisfiable.

Variant C preserves the same probe behavior while remaining HermiT-clean.

Variant F is already inconsistent for the named class cluster, so its probe results do not isolate additional range behavior.

## Interpretation

### Is The Current Baseline HermiT-Clean?

Yes. Variant A is HermiT-clean with the current active mapping:

```ttl
sosa:madeByActuator rdfs:domain sosa:Actuation ;
                    rdfs:subPropertyOf cco:ont00001833 .
```

and without an explicit `rdfs:range` axiom.

### Does Explicit `rdfs:range` Still Fail?

Yes. Variant B reproduces:

```text
sosa:Actuation
sosa:Actuator
ssn-system:ActuationRange
```

Therefore the explicit `rdfs:range` axiom remains unsafe in the current profile.

### Does Global Universal Restriction Remain HermiT-Clean?

Yes, with the current `madeByActuator -> cco:has_agent` mapping. Variant C is HermiT-clean and preserves the expected probe behavior.

However, this does not mean the global universal encoding is always safe with every participant mapping. Variant F shows that replacing `cco:has_agent` with direct parent `bfo:has_participant` and adding the global universal restriction fails.

### Does Scoped Universal Restriction Add Anything?

No. The scoped universal restriction:

```ttl
sosa:Actuation rdfs:subClassOf [
  owl:onProperty sosa:madeByActuator ;
  owl:allValuesFrom sosa:Actuator
] .
```

is already present in `imports/ssn.ttl`. Adding a duplicate restriction is HermiT-clean but redundant.

### Is Source-Level Domain/Range-Only Clean If `has_agent` Is Removed?

Yes. Variant E is HermiT-clean after removing:

```ttl
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

and adding:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

This remains a viable option if the project decides to drop the active CCO `has_agent` mapping for `madeByActuator`.

### Does Parent Participant Mapping Fail Only With Explicit `rdfs:range`?

No. It fails with both tested range-like encodings:

- Variant F: `madeByActuator -> bfo:has_participant` plus global universal restriction fails.
- Variant G: `madeByActuator -> bfo:has_participant` plus explicit `rdfs:range` fails.

This is stricter than the current `cco:has_agent` result, where global universal restriction is clean but explicit `rdfs:range` fails.

### Best Characterization

The issue is mixed:

- It is not only a CCO `has_agent` issue, because direct parent `bfo:has_participant` also fails.
- It is not only inherited BFO participant domain/range, because earlier diagnostics showed copied parent domain/range commitments alone were clean.
- It is not only inverse `agent_in` context, because removing that context did not clear the failure in the prior report.
- It is partly an encoding issue, because current `cco:has_agent` plus global universal restriction is clean while current `cco:has_agent` plus explicit `rdfs:range` fails.
- It is also sensitive to which participant path is active, because direct `bfo:has_participant` plus global universal restriction fails.

## Encoding Options Assessment

| Option | HermiT result | Assessment |
| --- | --- | --- |
| Current baseline, no explicit range | clean | safest current option; effective range behavior already entailed |
| Explicit `rdfs:range sosa:Actuator` with current `has_agent` | fails | do not add |
| Global universal restriction with current `has_agent` | clean | possible documentation encoding, but redundant with current effective behavior |
| Scoped universal restriction on `sosa:Actuation` | clean but already present | no active mapping change needed |
| Remove `has_agent` and add explicit source-level range | clean | viable only if the project wants to drop the active CCO `has_agent` mapping |
| Direct parent `bfo:has_participant` plus global universal | fails | not a safe replacement |
| Direct parent `bfo:has_participant` plus explicit range | fails | not a safe replacement |

## Recommendation

Do not add:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

The safest active OWL option is to keep the current baseline unchanged, because:

- it is HermiT-clean;
- the effective range behavior is already entailed by active domain plus imported source restriction;
- the scoped universal restriction is already present in `imports/ssn.ttl`;
- explicit `rdfs:range` still fails.

If explicit documentation of the range behavior is needed in `SSN2BFO.ttl`, the global universal restriction form is the only tested encoding that remained HermiT-clean with the current `madeByActuator -> cco:has_agent` mapping:

```ttl
owl:Thing rdfs:subClassOf [
  owl:onProperty sosa:madeByActuator ;
  owl:allValuesFrom sosa:Actuator
] .
```

However, because that behavior is already entailed, this report does not recommend a mapping-change branch solely to add it.

If the project wants an explicit source-level `rdfs:range` axiom specifically, the tested safe path is to remove/defer:

```ttl
sosa:madeByActuator rdfs:subPropertyOf cco:ont00001833 .
```

and then add:

```ttl
sosa:madeByActuator rdfs:range sosa:Actuator .
```

That is a larger modeling decision because it drops the active CCO `has_agent` mapping for `madeByActuator`.

Recommended next step:

```text
No active mapping change unless there is a concrete documentation or downstream-tooling need for an explicit range-like axiom.
```

If such a need appears, the next branch should be an evaluation/fix branch for adding the global universal restriction, not the explicit `rdfs:range` axiom.
