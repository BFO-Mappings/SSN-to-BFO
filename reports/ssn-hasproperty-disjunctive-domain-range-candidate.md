# `ssn:hasProperty` Disjunctive Domain/Range Candidate

## Scope

This report evaluates one local candidate strategy for the deferred `ssn:hasProperty` mapping:

1. `ssn:hasProperty rdfs:subPropertyOf owl:topObjectProperty`.
2. A disjunctive domain: continuant OR occurrent.
3. A disjunctive range: specifically dependent continuant OR process profile.

This was a temporary local modeling test only. No ontology files, spreadsheet files, imports, generated artifacts, or existing reports were modified. Temporary files were written under:

```text
/tmp/ssn-to-bfo-hasproperty-disjunctive-domain-range
```

## Proposed TTL Pattern

The candidate logical pattern is:

```turtle
ssn:hasProperty
  rdfs:subPropertyOf owl:topObjectProperty ;
  rdfs:domain [
    a owl:Class ;
    owl:unionOf (
      bfo:BFO_0000002
      bfo:BFO_0000003
    )
  ] ;
  rdfs:range [
    a owl:Class ;
    owl:unionOf (
      bfo:BFO_0000020
      bfo:BFO_0000144
    )
  ] .
```

Variant A tested only the `owl:topObjectProperty` subproperty axiom. Variant B tested the full pattern. Variant C tested only the disjunctive domain/range axioms.

## Verified Local BFO Labels

The expected BFO identifiers were checked against `imports/cco.ttl` before use:

| CURIE | Local label | Role in candidate |
| --- | --- | --- |
| `bfo:BFO_0000002` | continuant | Domain disjunct. |
| `bfo:BFO_0000003` | occurrent | Domain disjunct. |
| `bfo:BFO_0000020` | specifically dependent continuant | Range disjunct. |
| `bfo:BFO_0000144` | Process Profile | Range disjunct. |

## Difference From Prior Unsafe Mappings

The prior unsafe mapping used direct subproperty assertions to two BFO relations:

```turtle
ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000196 .
ssn:hasProperty rdfs:subPropertyOf bfo:BFO_0000117 .
```

Those targets are:

- `bfo:BFO_0000196` / bearer of
- `bfo:BFO_0000117` / has occurrent part

That pattern made `ssn:hasProperty` and/or inherited SSN Systems subproperties unsatisfiable under ELK in previous tests. The candidate tested here is different because it does not make `ssn:hasProperty` a subproperty of either BFO relation. Instead, it tries to describe a broader allowable subject/object typing pattern using domain and range unions.

The difference matters, but it does not make the candidate automatically safe. Global domain/range axioms still apply to all uses of `ssn:hasProperty`; through SSN Systems subproperties, they may also affect `hasOperatingRange`, `hasSurvivalRange`, `hasSystemCapability`, `hasSystemProperty`, and related subproperties.

## Temporary Test Setup

The temporary no-imports merged graph was built from:

- `imports/cco.ttl`
- `imports/ssn.ttl`
- `imports/ssn-systems.ttl`
- `SSN2BFO.ttl`

The temporary graph removed:

- all `owl:imports` triples;
- `sosa:isSampleOf rdf:type owl:FunctionalProperty`.

Tooling:

```text
ROBOT version 1.9.7
rdflib 7.6.0
```

ROBOT command pattern:

```bash
robot reason --reasoner ELK --input /tmp/ssn-to-bfo-hasproperty-disjunctive-domain-range/<variant>.ttl --output /tmp/ssn-to-bfo-hasproperty-disjunctive-domain-range/<variant>-reasoned.ttl
```

All ROBOT runs emitted the same OWLAPI parser errors:

```text
Entity not properly recognized, missing triples in input? http://org.semanticweb.owlapi/error#ErrorN for type Class
```

These messages also appeared in the baseline run. No ROBOT log contained a specific warning mentioning `owl:unionOf`, unsupported disjunction, or an OWL EL profile violation.

## ELK Results

| Variant | Added axioms | ROBOT status | Reasoned output produced? | `owl:Nothing` count | ELK-clean? | Meaningfulness caveat |
| --- | --- | ---: | --- | ---: | --- | --- |
| Baseline | None. | 0 | Yes | 0 | Yes | Baseline check only. |
| Variant A | `ssn:hasProperty rdfs:subPropertyOf owl:topObjectProperty .` | 0 | Yes | 0 | Yes | This is effectively a no-op mapping to the top object property. |
| Variant B | Top object property plus disjunctive domain/range. | 0 | Yes | 0 | Superficially yes | Weak evidence: `owl:unionOf` is outside OWL EL, so ELK is not sufficient to validate the disjunctive semantics. |
| Variant C | Disjunctive domain/range only. | 0 | Yes | 0 | Superficially yes | Weak evidence for the same `owl:unionOf` reason. |

## Is ELK Sufficient For This Candidate?

No. ELK is useful for detecting whether this candidate immediately breaks the current ELK profile, and it did not report unsatisfiable entities for Variants A, B, or C. However, the meaningful part of Variants B and C is the use of `owl:unionOf` in domain and range class expressions.

Because disjunction is outside OWL EL, a successful ELK run should not be treated as full validation of the candidate semantics. The result only says that ROBOT/ELK completed and did not produce `owl:Nothing` entities in this temporary profile. It does not prove that the disjunctive domain/range modeling is semantically correct, sufficiently enforced, or safe under a fuller OWL profile.

## Mapping Audit Parser Assessment

The current audit parser in `tools/compare_mappings.py` is unlikely to compare this pattern cleanly if placed in the spreadsheet `OWL Axiom` cell.

Parser observations:

- `rdfs:domain` and `rdfs:range` are not included in `MAPPING_PREDICATES`.
- The parser treats spreadsheet rows as governed assertions mainly through predicates such as `rdfs:subClassOf`, `rdfs:subPropertyOf`, `owl:equivalentClass`, `owl:equivalentProperty`, selected SKOS mapping predicates, `rdfs:seeAlso`, and `owl:propertyChainAxiom`.
- A probe using the parser showed:
  - Variant A-style text parses as one expected assertion: `rdfs:subPropertyOf owl:topObjectProperty`.
  - Variant B-style text also parses only that one expected assertion; the domain/range union axioms are ignored for expected-assertion comparison.
  - Variant C-style text parses as zero expected assertions.
- TTL extraction also treats structural OWL/RDF/RDFS namespaces conservatively. A TTL-side `rdfs:subPropertyOf owl:topObjectProperty` assertion is likely to compare awkwardly because the spreadsheet side retains `owl:topObjectProperty` as a target token, while TTL target collection filters structural namespace targets.

So the current audit model would likely need enhancement before it could usefully govern or compare the disjunctive domain/range pattern.

## Risks

### Global Domain/Range Inference

`rdfs:domain` and `rdfs:range` apply globally. Any use of `ssn:hasProperty` can cause subject/object typing inferences. This is not limited to the intended explanatory cases.

### Propagation Through SSN Systems Subproperties

`imports/ssn-systems.ttl` declares several properties as subproperties of `ssn:hasProperty`, including:

- `ssn-system:hasOperatingProperty`
- `ssn-system:hasOperatingRange`
- `ssn-system:hasSurvivalProperty`
- `ssn-system:hasSurvivalRange`
- `ssn-system:hasSystemCapability`
- `ssn-system:hasSystemProperty`

Domain/range behavior on `ssn:hasProperty` may affect uses of those narrower properties through property hierarchy reasoning.

### Use Of OWL Disjunction

The candidate depends on `owl:unionOf`, which is outside OWL EL. ELK completion with zero `owl:Nothing` entities is therefore not enough to validate the intended disjunctive semantics.

### Audit Model Mismatch

The current mapping audit is not designed to compare domain/range union patterns as governed mapping assertions. Variant C would likely be skipped as no parsed expected assertions, and Variant B would likely reduce to the top-object-property subproperty assertion.

### Low Mapping Value Of `owl:topObjectProperty`

`rdfs:subPropertyOf owl:topObjectProperty` is reasoner-safe in this test, but it is also close to a tautology for object properties. It does not provide a meaningful BFO/CCO alignment.

## Recommendation Options

| Option | Assessment |
| --- | --- |
| Commit now | Not recommended. The candidate is either a no-op (`owl:topObjectProperty`) or depends on disjunction that ELK does not adequately validate. |
| Keep as report-only candidate | Recommended. The test is useful evidence, especially showing that the pattern does not immediately break ELK, but it should remain review-only. |
| Reject | Reasonable for Variant A as a mapping, because it adds almost no semantic value. Premature for the disjunctive domain/range idea if a future full-OWL profile review wants to revisit it. |
| Defer until full OWL/HermiT profile cleanup | Recommended for any active disjunctive domain/range version. |

## Final Recommendation

Keep this as a report-only candidate. Do not commit the proposed `ssn:hasProperty` disjunctive domain/range mapping to `SSN2BFO.ttl` now.

Variant A is ELK-clean but too weak to be a useful mapping. Variants B and C are also ELK-clean in the temporary test, but their central semantics depend on `owl:unionOf`, so ELK is not a sufficient validator. The current audit parser would also not govern the pattern well.

The conservative path is to keep `ssn:hasProperty` deferred as an active logical mapping and revisit this candidate only after a fuller OWL profile and audit-parser strategy exists for domain/range disjunctions.
