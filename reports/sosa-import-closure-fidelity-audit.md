# SOSA Import Closure Fidelity Audit

## Scope

This report audits whether the reduced M2-style HermiT graphs used in prior diagnostics omitted the indirect SOSA import that Protégé loads through `imports/ssn.ttl`.

No ontology mappings, workbook rows, imports, examples, generated artifacts, or existing reports were edited. Temporary files were written only under:

```text
/tmp/ssn-to-bfo-sosa-import-closure-fidelity-audit
```

Current branch and commit context:

```text
branch: review/audit-sosa-import-closure-fidelity
commit: 6611c6e
commit subject: Merge pull request #139 from BFO-Mappings/review/update-madeByActuator-agent-diagnostics
```

## Import Structure

`SSN2BFO.ttl` directly imports:

```ttl
<http://www.sks.ai/SSN2BFO/>
    owl:imports <http://www.w3.org/ns/ssn/> ,
                <http://www.w3.org/ns/ssn/systems/> ,
                <https://www.commoncoreontologies.org/2024-11-06/CommonCoreOntologiesMerged> .
```

The local import files then chain as follows:

```ttl
<http://www.w3.org/ns/ssn/> owl:imports sosa: .
<http://www.w3.org/ns/ssn/systems/> owl:imports ssn: .
```

Local materialization status:

- `imports/cco.ttl` exists.
- `imports/ssn.ttl` exists.
- `imports/ssn-systems.ttl` exists.
- `imports/sosa.ttl` does not exist.
- No local `imports/sosa.rdf`, `imports/sosa.owl`, or similarly named SOSA materialization was found.
- `imports/catalog-v001.xml` is only a folder-repository catalog and does not map `http://www.w3.org/ns/sosa/` to a local file.

Therefore the prior reduced M2 graph did not include a separately materialized SOSA ontology. It included only SOSA-namespaced assertions physically present in `imports/ssn.ttl`, `imports/ssn-systems.ttl`, and `SSN2BFO.ttl`.

## Graph Profiles

All local HermiT graphs were built from:

```text
imports/cco.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

The established cleanup was then applied:

```text
remove all owl:imports triples
remove sosa:isSampleOf rdf:type owl:FunctionalProperty
remove sosa:hasSample rdf:type owl:InverseFunctionalProperty
```

Profile A is the current reduced M2 graph.

Profile B is the intended Protégé-style closure with the materialized indirect SOSA import included. This profile could not be reproduced locally because no local materialized SOSA source file is available and this audit did not download/export SOSA.

Profile C is Profile A plus the targeted inverse probe:

```ttl
sosa:madeByActuator owl:inverseOf sosa:madeActuation .
```

This proxy tests one suspected missing SOSA import axiom without claiming to reproduce the full remote SOSA ontology.

## Axiom Presence Inspection

| Axiom or restriction | Profile A reduced M2 | Profile B Protégé-style closure | Profile C inverse probe |
|---|---:|---:|---:|
| `sosa:madeByActuator owl:inverseOf sosa:madeActuation` | absent | not locally testable | present |
| `sosa:madeActuation owl:inverseOf sosa:madeByActuator` | absent | not locally testable | absent |
| `sosa:madeActuation rdfs:domain sosa:Actuator` | present | not locally testable | present |
| `sosa:madeActuation rdfs:range sosa:Actuation` | present | not locally testable | present |
| `sosa:madeByActuator rdfs:domain sosa:Actuation` | present | not locally testable | present |
| `sosa:madeByActuator rdfs:range sosa:Actuator` | absent | not locally testable | absent |
| `sosa:Actuation subClassOf madeByActuator only Actuator` | present | not locally testable | present |
| `sosa:Actuator subClassOf madeActuation only Actuation` | present | not locally testable | present |

The `madeActuation` source-level domain/range axioms and the active `madeByActuator` domain axiom are present in `SSN2BFO.ttl`. The `Actuation` and `Actuator` all-values restrictions are present in `imports/ssn.ttl`. The reduced graph lacks the inverse axiom between `madeByActuator` and `madeActuation`.

## HermiT Results

ROBOT/HermiT command shape:

```bash
robot reason --reasoner HermiT --input <variant.ttl> --output <variant-reasoned.ttl>
```

| Variant | Graph path | Temporary edit | Triples | Return | Reasoned output | `owl:Nothing` count | Unsat count | Unsat set |
|---|---|---|---:|---:|---|---:|---:|---|
| A baseline | `/tmp/ssn-to-bfo-sosa-import-closure-fidelity-audit/A_baseline.ttl` | none | 15510 | 0 | yes | 0 | 0 | clean |
| A + explicit range | `/tmp/ssn-to-bfo-sosa-import-closure-fidelity-audit/A_plus_range.ttl` | add `sosa:madeByActuator rdfs:range sosa:Actuator` | 15511 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| A + inverse | `/tmp/ssn-to-bfo-sosa-import-closure-fidelity-audit/A_plus_inverse.ttl` | add `sosa:madeByActuator owl:inverseOf sosa:madeActuation` | 15511 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| A + inverse + range | `/tmp/ssn-to-bfo-sosa-import-closure-fidelity-audit/A_plus_inverse_and_range.ttl` | add both inverse and explicit range | 15512 | 1 | no | n/a | 3 | `sosa:Actuator`, `sosa:Actuation`, `ssn-system:ActuationRange` |
| B baseline | n/a | materialized SOSA import unavailable locally | n/a | n/a | n/a | n/a | n/a | skipped |
| B + explicit range | n/a | materialized SOSA import unavailable locally | n/a | n/a | n/a | n/a | n/a | skipped |

The sample simplicity blockers did not reappear in any tested Profile A variant.

## Interpretation

The reduced M2 diagnostics did omit the materialized indirect SOSA import that Protégé reports loading through:

```ttl
imports/ssn.ttl owl:imports sosa:
```

Because the prior manual graph construction loaded only `imports/cco.ttl`, `imports/ssn.ttl`, `imports/ssn-systems.ttl`, and `SSN2BFO.ttl`, then removed all `owl:imports` triples, it did not follow the indirect `sosa:` import. The reduced graph is therefore not the same as a full Protégé import closure.

The reduced graph is not devoid of SOSA content. It already contains several SOSA axioms copied into `imports/ssn.ttl` or asserted by `SSN2BFO.ttl`, including:

- `sosa:madeByActuator rdfs:domain sosa:Actuation`
- `sosa:madeActuation rdfs:domain sosa:Actuator`
- `sosa:madeActuation rdfs:range sosa:Actuation`
- `sosa:Actuation subClassOf madeByActuator only Actuator`
- `sosa:Actuator subClassOf madeActuation only Actuation`

But it does not contain:

```ttl
sosa:madeByActuator owl:inverseOf sosa:madeActuation .
```

Profile C shows that adding just this targeted inverse axiom to the reduced graph is HermiT-significant. It reproduces the same three-class cluster as the explicit range axiom:

```text
sosa:Actuator
sosa:Actuation
ssn-system:ActuationRange
```

This means the missing import-closure content is not merely documentary for the `madeByActuator` area. If the materialized SOSA ontology contains the `madeByActuator` / `madeActuation` inverse axiom, then prior madeByActuator diagnostics were limited to the reduced M2 graph and should be read with that limitation.

This audit cannot locally confirm every axiom present in Protégé's full SOSA import closure because the repo currently has no materialized SOSA source file and this branch did not download or export one. However, it does confirm a fidelity gap in the reduced graph construction: an indirect import exists, is removed rather than followed, and at least one plausible missing SOSA axiom changes the HermiT result.

## Recommendation

Before continuing madeByActuator conflict analysis, add or otherwise provide a local materialized SOSA import source, for example:

```text
imports/sosa.ttl
```

Then update the diagnostic graph construction so M2-style HermiT runs can choose explicitly between:

- reduced local mapping graph;
- full local import closure matching Protégé;
- targeted proxy variants.

Prior madeByActuator reports should receive a correction or limitation note saying their conclusions apply to the reduced M2 graph unless they explicitly included a materialized SOSA import closure.

Do not add or change mappings based only on this audit. The next branch should first establish a faithful local SOSA import closure and rerun the `madeByActuator` range/inverse diagnostics against that closure.
