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

- directly contains all 46 active canonical authoritative mapping axioms;
- contains 268 logical triples and 281 total triples;
- imports exactly the governed SOSA root, SOSA Systems, SOSA Sampling,
  source-declaration overlay, and merged CCO/BFO dependency IRIs, with the target resolved from `src/sosa-next/imports/cco.ttl`;
- provides the distinct complete consumer entry point for the track;
- contains exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

Required SHA-256:

`fec0e53270b4b527798db6ff078371c1050eb8afb441440db09fbc17cf840520`

### BFO Mapping

Development path:

`releases/sosa-next/sosa-bfo-mapping.ttl`

Development ontology IRI:

`http://www.sks.ai/SSN2BFO/development/sosa-next/bfo-mapping`

Contract:

- directly contains the 21 BFO-bearing authoritative axioms that contain no
  CCO term;
- contains 151 logical triples and 159 total triples;
- imports no project or external ontology;
- does not transform, weaken, or strengthen a governed authoritative axiom;
- contains exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

Required SHA-256:

`e28dcdc2a261793b091f5c8d2e92b04a5e7c819659840e5c9ed622c444b22ad3`

### CCO Extension

Development path:

`releases/sosa-next/sosa-cco-extension.ttl`

Development ontology IRI:

`http://www.sks.ai/SSN2BFO/development/sosa-next/cco-extension`

Contract:

- directly contains the 25 CCO-bearing and mixed BFO/CCO authoritative axioms;
- contains 117 logical triples and 126 total triples;
- imports only the SOSA-next BFO Mapping;
- does not transform, weaken, or strengthen a governed authoritative axiom;
- contains exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

Required SHA-256:

`c61b07fae4aee044d7e627e7eaee94abca6503f0da96e8fe8bd8820c8e31d09a`

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

The editor-plus-Integrated project closure contains exactly 285 distinct
triples.

## Axiom accounting

The Integrated product directly contains all 46 active authoritative axioms.

The modular partition is pairwise disjoint:

1. 21 BFO-bearing axioms without CCO terms -> BFO Mapping;
2. 25 CCO-bearing or mixed BFO/CCO axioms -> CCO Extension.

There are currently zero target-neutral authoritative axioms, so Alignment Core
has no direct logical content and is not materialized.

The BFO Mapping plus CCO Extension logical union contains 268 triples and is
isomorphic to the Integrated Mapping's 268 logical triples.

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

Actual formal publication remains a later phase, while formal publication
metadata, pure ontology rendering, manifest/schema, deterministic package/archive construction, and rehearsal are now implemented. Formal stable
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
  `e2345d7e50ac871a535bd0f1e7e2c612181729b83d8d8bd7d5cb6d3976299a19`;
- BFO Mapping:
  `c4417989963590517a5636bf1d57ddc966199ab8273fee814b3d27fb159c0c96`;
- CCO Extension:
  `49dec6023bfdebac6c78c4f2b6b291ab74766c1816d146598f797dfb9295bc35`.

## Validation closures

Reasoning validation assembles temporary fixed closures; closure triples are
not serialized into maintained products.

Required reasoning profiles are:

- Integrated plus the governed pinned SOSA and merged CCO/BFO dependencies:
  15,231 closure triples;
- BFO Mapping plus the governed pinned SOSA and merged CCO/BFO dependencies:
  15,114 closure triples;
- CCO Extension plus BFO Mapping and the governed pinned SOSA and merged
  CCO/BFO dependencies: 15,239 closure triples.

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

The SOSA-2023 release manifest, deterministic package engine, separate
deterministic archive authority, and isolated release-rehearsal authority are
now implemented independently from this maintained-development surface.
Actual publication remains deferred. The rehearsal authority is
`tools/sosa_2023_rehearse_release.py`; it proves two isolated exact-commit
package-and-archive candidates equivalent before any retained build-mode output
can be atomically published.

## Acceptance gates

The maintained product-role implementation must satisfy all of the following:

1. the governed workbook remains 119 rows with 119 unique RowIDs;
2. all 46 active mappings produce 46 canonical authoritative axioms;
3. all 25 deferred rows produce no direct axiom;
4. all 48 explicitly unmapped rows produce no direct axiom;
5. Integrated directly contains all 46 authoritative axioms;
6. BFO Mapping directly contains exactly 21 BFO-bearing axioms;
7. CCO Extension directly contains exactly 25 CCO-bearing or mixed axioms;
8. the BFO+CCO modular logical union contains 268 triples and is isomorphic
   to Integrated's 268 logical triples;
9. two independent builds produce byte-identical maintained products;
10. the exact product hashes and triple counts are asserted by focused tests;
11. the three reasoning closures are exactly 15,231, 15,114, and 15,239
    triples and have zero named unsatisfiable classes;
12. `releases/sosa-next/sosa-alignment-core.ttl` is absent;
13. the editor imports Integrated and its local project closure contains
    exactly 285 distinct triples;
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
and product-specific HermiT closure counts of 15,234 / 15,117 / 15,245.

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
100-byte raw-USTAR name field. The synthetic real-package contract requires
two independent archives of the same complete package bytes to be identical
and uses a canonical 140-byte sidecar.

The package manifest records the actual validation environment, including
Python and Java runtime identity. Whole-package bytes and therefore the
whole-archive digest and potentially padded archive size are not fixed across
different validated environments.

Remaining formal-release integration work is:

- approve actual release notes and an actual release context;
- perform the final real release rehearsal against that approved context before
  publication and persistent-IRI deployment.

No formal SOSA-2023 package or archive is committed to the repository, and no
tag, GitHub release, or persistent-IRI deployment is created by this
release-rehearsal milestone. Verify mode retains no release output; focused
tests use temporary fixtures, and build mode requires an explicit absent
external destination after the isolated proof succeeds.

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
