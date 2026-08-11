# SOSA-next Product Contract

## Status

This document defines the development-product contract for the governed
forthcoming SOSA mapping. Its initial maintained implementation is generated
by `tools/generate_sosa_next_products.py` and validated by the focused
SOSA-next product checker and repository validation suite. It does not
publish a formal release.

The approved immutable source-version identity is
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`, governed by `config/sosa-source-version.toml`. The
temporary term `sosa-next` remains the development alias only. A formal release
must replace it in track-specific package paths and ontology IRIs with the
approved identity. No formal production path or ontology IRI may retain
`sosa-next`.

## Authoritative inputs

The maintained products are generated from:

- `mappings/SOSA-next-to-BFO-COMS.xlsx`, as the sole editable mapping source;
- `config/sosa-source-version.toml`, as the machine-readable source-version
  authority;
- the pinned SOSA-next source closure under `src/sosa-next/imports/`;
- `src/sosa-next/catalog-v001.xml`;
- repository-governed BFO and CCO imports;
- the canonical COMS row-identity and expression-processing machinery.

The former files

- `releases/sosa-next/sosa-bfo-directmappings.ttl`; and
- `releases/sosa-next/sosa-cco-directmappings.ttl`

were inactive scaffolds, not mapping authorities. They are retired only after
their generated replacements pass the maintained-product gates.

## Governed baseline

The initial product implementation must preserve this exact workbook
classification:

| Measure | Required value |
|---|---:|
| Governed rows | 119 |
| Unique RowIDs | 119 |
| Active mappings | 45 |
| Deferred mappings | 26 |
| Explicitly unmapped rows | 48 |
| Malformed rows | 0 |
| Canonical authoritative axioms | 45 |
| Named unsatisfiable classes | 0 |

Deferred and explicitly unmapped rows are governed evidence but contribute no
direct ontology axiom.

## Maintained development products

The implemented SOSA-next development set consists of exactly three
materialized ontology products and follows the uniform product-role policy.

### Integrated

Development path:

`releases/sosa-next/sosa-integrated.ttl`

Development ontology IRI:

`http://www.sks.ai/SSN2BFO/development/sosa-next/integrated`

Contract:

- directly contains all 45 active canonical authoritative mapping axioms;
- contains 273 logical triples and 286 total triples;
- imports exactly the governed SOSA root, SOSA Systems, SOSA Sampling,
  source-declaration overlay, and merged CCO/BFO dependency IRIs;
- provides the distinct complete consumer entry point for the track;
- contains exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

Required SHA-256:

`7ce45659e4d84ac089ae90c3279fa46d169d763ec487c34cb3c533eb0e6c197c`

### BFO Mapping

Development path:

`releases/sosa-next/sosa-bfo-mapping.ttl`

Development ontology IRI:

`http://www.sks.ai/SSN2BFO/development/sosa-next/bfo-mapping`

Contract:

- directly contains the 21 BFO-bearing authoritative axioms that contain no
  CCO term;
- contains 157 logical triples and 165 total triples;
- imports no project or external ontology;
- does not transform, weaken, or strengthen a governed authoritative axiom;
- contains exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

Required SHA-256:

`67bb58ea543e654ace41c0d1a393b2a3f92426c693f5100f0aa3ba35f3b005d2`

### CCO Extension

Development path:

`releases/sosa-next/sosa-cco-extension.ttl`

Development ontology IRI:

`http://www.sks.ai/SSN2BFO/development/sosa-next/cco-extension`

Contract:

- directly contains the 24 CCO-bearing and mixed BFO/CCO authoritative axioms;
- contains 116 logical triples and 125 total triples;
- imports only the SOSA-next BFO Mapping;
- does not transform, weaken, or strengthen a governed authoritative axiom;
- contains exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

Required SHA-256:

`e65e96f15a55e19fc43be8dbda6e56351ef40bbd6e0fa9368a240e83c5d6bb69`

## Implemented development import graph

The complete-consumer graph is:

```text
editor shell
  -> Integrated
       -> governed SOSA/BFO/CCO dependencies
```

The modular project graph is:

```text
CCO Extension
  -> BFO Mapping
```

The BFO Mapping has no import. The CCO Extension imports only the BFO Mapping.
The Integrated Mapping imports no project product.

The catalog resolves all three maintained products, the editor shell, the
governed pinned SOSA source modules and declaration overlay, and the merged
CCO/BFO dependency.

The editor-plus-Integrated project closure contains exactly 290 distinct
triples.

## Axiom accounting

The Integrated product directly contains all 45 active authoritative axioms.

The modular partition is pairwise disjoint:

1. 21 BFO-bearing axioms without CCO terms -> BFO Mapping;
2. 24 CCO-bearing or mixed BFO/CCO axioms -> CCO Extension.

There are currently zero target-neutral authoritative axioms, so Alignment Core
has no direct logical content and is not materialized.

The BFO Mapping plus CCO Extension logical union contains 273 triples and is
isomorphic to the Integrated Mapping's 273 logical triples.

A row's product classification is derived from its canonical authoritative
axiom rather than lexical matching against workbook cell text.

## Omitted product roles

### Alignment Core

Alignment Core remains a governed role but is not materialized because the
current governed mapping has zero direct target-neutral axioms. The former
zero-axiom development shell has been retired.

### BFO Projection

BFO Projection remains a governed role but is not materialized because no
weakened or transformed BFO consequence has been approved as a separate
governed product axiom.

A BFO Projection may be introduced only through a separate policy change that
identifies approved consequences, records their relationships to authoritative
axioms, proves entailment, and adds exact reconstruction and reasoning tests.

## Formal target under the uniform product-role policy

The implemented development materialization now matches the SOSA-2023 formal
target inventory:

1. Integrated;
2. BFO Mapping;
3. CCO Extension.

Alignment Core and BFO Projection remain governed omitted roles.

Formal package publication remains a later phase, but formal publication
metadata and pure ontology rendering are now implemented. Formal stable
ontology IRIs and version-IRI suffixes use the approved immutable source-version
identity and contain no `sosa-next` development alias.

## Generation architecture

The implementation uses the dedicated SOSA-next generation adapter:

`tools/generate_sosa_next_products.py`

The adapter reuses pure COMS, canonical-identity, product-classification,
modular-rendering, and publication-header functions without changing the
current-SOSA generator contract.

Generation is transactional: it builds and validates independent candidates,
requires byte-identical results, validates the three reasoning profiles, and
atomically replaces the maintained products only after every gate passes.
Temporary COMS resolver configuration is restored after both success and
failure.

## Canonical serialization and metadata

Each maintained product must use deterministic UTF-8 Turtle with:

- a fixed prefix order;
- a canonical ontology header;
- stable ordering of direct axioms;
- stable blank-node and RDF-list rendering;
- exactly one final newline;
- no local absolute paths;
- no timestamp or environment-dependent bytes.

Development metadata must use the repository's existing publication vocabulary
and product-type IRIs. Formal-release-only metadata, including
`owl:versionIRI`, must not appear in maintained development artifacts.

The separate formal publication authority is
`config/sosa-2023-publication-metadata.toml`. The pure formal renderer preserves
the development logical graphs while replacing development ontology identity
with the approved immutable stable identity and adding formal status,
`owl:versionIRI`, `owl:versionInfo`, and `dcterms:issued`.

Formal Integrated imports the official SOSA root, Systems, Sampling, and merged
CCO/BFO IRIs. The source-declaration overlay remains governed source and
validation evidence but is not a published formal import. Formal BFO Mapping
is import-free. Formal CCO Extension imports the same-release formal BFO
Mapping version IRI.

Under the synthetic `2099-01-02` release context, the exact formal hashes are:

- Integrated:
  `81694ddfc0a7587c2d83517f0fc69449a25dc31ae68571b0a63f48aa5ca10aae`;
- BFO Mapping:
  `c88cb347742a15fc003cafe2e167f7f784cc4a70653720c11f1e6247e6a3096c`;
- CCO Extension:
  `bc356b515e29a21d74865101661fe1d81f2da33f86b31bf4c497109e8f9b202b`.

## Validation closures

Reasoning validation assembles temporary fixed closures; closure triples are
not serialized into maintained products.

Required reasoning profiles are:

- Integrated plus the governed pinned SOSA and merged CCO/BFO dependencies:
  15,127 closure triples;
- BFO Mapping plus the governed pinned SOSA and merged CCO/BFO dependencies:
  15,011 closure triples;
- CCO Extension plus BFO Mapping and the governed pinned SOSA and merged
  CCO/BFO dependencies: 15,135 closure triples.

Each profile must complete successfully with return code 0, produce reasoned
output, and contain zero named unsatisfiable classes.

## Implemented migration surface

The product-role migration updates only the development surfaces required to
materialize the approved roles:

- `tools/generate_sosa_next_products.py`;
- the focused SOSA-next product checker and tests;
- `releases/sosa-next/sosa-integrated.ttl`;
- `releases/sosa-next/sosa-bfo-mapping.ttl`;
- `releases/sosa-next/sosa-cco-extension.ttl`;
- retirement of `releases/sosa-next/sosa-alignment-core.ttl`;
- `src/sosa-next/catalog-v001.xml`;
- `src/sosa-next/sosa-mappings-edit.ttl`;
- the catalog consumer-stack tests;
- development and governance documentation.

The SOSA-2023 release manifest, deterministic package engine, and separate
deterministic archive authority are now implemented independently from this
maintained-development surface. Isolated release rehearsal and actual
publication remain deferred.

## Acceptance gates

The maintained product-role implementation must satisfy all of the following:

1. the governed workbook remains 119 rows with 119 unique RowIDs;
2. all 45 active mappings produce 45 canonical authoritative axioms;
3. all 26 deferred rows produce no direct axiom;
4. all 48 explicitly unmapped rows produce no direct axiom;
5. Integrated directly contains all 45 authoritative axioms;
6. BFO Mapping directly contains exactly 21 BFO-bearing axioms;
7. CCO Extension directly contains exactly 24 CCO-bearing or mixed axioms;
8. the BFO+CCO modular logical union contains 273 triples and is isomorphic
   to Integrated's 273 logical triples;
9. two independent builds produce byte-identical maintained products;
10. the exact product hashes and triple counts are asserted by focused tests;
11. the three reasoning closures are exactly 15,127, 15,011, and 15,135
    triples and have zero named unsatisfiable classes;
12. `releases/sosa-next/sosa-alignment-core.ttl` is absent;
13. the editor imports Integrated and its local project closure contains
    exactly 290 distinct triples;
14. the BFO Mapping has no import and the CCO Extension imports only BFO
    Mapping;
15. the approved source-version authority validates and all pinned SOSA source
    bytes remain unchanged;
16. the four retained current SSN/SOSA products remain byte-identical;
17. temporary COMS resolver configuration is restored after success and
    failure;
18. checker-only mode changes no tracked file;
19. the full repository validation suite passes.

The preserved current SSN/SOSA hashes are:

| Product | Required SHA-256 |
|---|---|
| `SSN2BFO.ttl` | `c31997d7e7b8c5e0bffd3f23a4597ab4be80786978462fefe800c4c7a5dc0c11` |
| `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` | `17695ef17379924449153b2c92ffaed6b57d497a1b2d1e854f584614cebec770` |
| `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` | `676b31620df10db5c26c46bcc44b2dfd5939d606b16e0fa8a910926e8497c3af` |
| `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` | `2908f89648d42dc928f7225056216f1cbf3bcdc79de1bcf770b40a017a5e9bf5` |

Earlier versions of this contract also recorded the former current-track
BFO-Projection hash. That row is historical evidence only: the current-track
product-role migration intentionally retired that import-only artifact while
preserving the four retained current products.

## Formal-release transition

Publication metadata, pure formal ontology rendering, the separate
SOSA-2023 release-manifest/schema authority, deterministic package
construction, canonical package catalog, checksums, and read-only package
validation are implemented.

The schema-v1 manifest contract governs the exact three-product inventory,
immutable formal identities and package paths, formal import graph,
source/development evidence, validation environment, 31 governed inputs, four
external dependency records, an 11-member included-file evidence inventory,
and product-specific HermiT closure counts of 15,130 / 15,014 / 15,141.

The package runtime, builder, and checker are themselves governed as
byte-affecting non-packaged manifest inputs. They remain separate from the
current-track release engine.

The complete SOSA-2023 package contains 13 regular files and 12 checksum
entries. Its catalog maps exactly the three same-release formal version IRIs.
Construction requires two byte-identical complete builds. Read-only validation
can reconstruct the package from its copied workbook and publication metadata
and requires 13/13 byte identity without mutating the retained package.

The pinned Sampling dependency declares
`http://www.w3.org/ns/sosa/sam/`; the formal Integrated product separately
imports `http://www.w3.org/ns/sosa/sampling/`.

`release-notes/SOSA-2023-SYNTHETIC-2099-01-02.md` is a deterministic
package-engineering fixture, not a release announcement or publication
decision.

The deterministic archive authority now binds the 13-file package to a
canonical 16-member raw POSIX USTAR stream. Its external asset filename includes
the full immutable source-version identity, while the internal archive root uses
`SOSA-2023-<release-id>/` so all governed member names fit the canonical
100-byte raw-USTAR name field. The fixed synthetic real-package contract is
146,432 archive bytes, 140 sidecar bytes, and SHA-256
`d0cd2ffc14b7e67ae0656e5519de8226170e57fac8e27cf33f5dd4ad7f644ffc`.

Remaining formal-release integration work is:

- add isolated release rehearsal and archive equivalence checks;
- approve actual release notes and an actual release context;
- perform the final release rehearsal before publication and persistent-IRI
  deployment.

No formal SOSA-2023 package or archive is committed to the repository, and no
tag, GitHub release, or persistent-IRI deployment is created by this archive
authority milestone. Focused tests create only temporary synthetic package,
archive, and sidecar outputs.

## Non-goals

This contract does not:

- resolve any deferred mapping;
- activate datatype-property mappings;
- alter the pinned SOSA-next source ontologies;
- modify current-SOSA mappings or products;
- publish a formal SOSA-next release;
- populate the obsolete direct-mapping scaffold files manually;
- approve a BFO projection;
- treat the W3C SOSA–BFO alignment as independent validation evidence.
