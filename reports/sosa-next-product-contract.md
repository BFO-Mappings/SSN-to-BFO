# SOSA-next Product Contract

## Status

This document defines the development-product contract for the governed
forthcoming SOSA mapping. Its initial maintained implementation is generated
by `tools/generate_sosa_next_products.py` and validated by the focused
SOSA-next product checker and repository validation suite. It does not
publish a formal release.

The temporary term `sosa-next` identifies the development track only. A formal
release must replace it in package paths and ontology IRIs with the approved
source-version identity. No production path or ontology IRI may retain
`sosa-next`.

## Authoritative inputs

The maintained products are generated from:

- `mappings/SOSA-next-to-BFO-COMS.xlsx`, as the sole editable mapping source;
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

The initial SOSA-next product set consists of exactly three maintained ontology
products.

### Alignment core

Development path:

`releases/sosa-next/sosa-alignment-core.ttl`

Development ontology IRI:

`http://www.sks.ai/SSN2BFO/development/sosa-next/alignment-core`

Contract:

- contains each active target-neutral axiom whose referenced logical
  vocabulary is confined to the governed SOSA source namespaces;
- contains no BFO-bearing or CCO-bearing mapping axiom;
- contains no `owl:imports` assertion;
- has exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

### BFO mapping

Development path:

`releases/sosa-next/sosa-bfo-mapping.ttl`

Development ontology IRI:

`http://www.sks.ai/SSN2BFO/development/sosa-next/bfo-mapping`

Contract:

- contains each active BFO-bearing axiom that contains no CCO term;
- imports only the SOSA-next alignment core;
- does not transform, weaken, or strengthen a governed authoritative axiom;
- has exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

Required project import:

`http://www.sks.ai/SSN2BFO/development/sosa-next/alignment-core`

### CCO extension

Development path:

`releases/sosa-next/sosa-cco-extension.ttl`

Development ontology IRI:

`http://www.sks.ai/SSN2BFO/development/sosa-next/cco-extension`

Contract:

- contains each active axiom that references a CCO term, including mixed
  BFO/CCO axioms;
- imports only the SOSA-next BFO mapping;
- does not duplicate a direct alignment-core or BFO-mapping axiom;
- does not transform, weaken, or strengthen a governed authoritative axiom;
- has exactly one `owl:Ontology` declaration;
- contains no `owl:versionIRI` in the maintained development artifact.

Required project import:

`http://www.sks.ai/SSN2BFO/development/sosa-next/bfo-mapping`

## Implemented development import graph

The maintained development import graph is:

- `sosa-cco-extension.ttl` imports `sosa-bfo-mapping.ttl`;
- `sosa-bfo-mapping.ttl` imports `sosa-alignment-core.ttl`;
- `sosa-alignment-core.ttl` imports no project ontology.

The editor shell imports only the CCO extension and therefore obtains the
BFO mapping and alignment core transitively. The maintained products do not
import external SOSA, BFO, or CCO ontologies; validation and consumers load
the governed source and target dependencies separately.

## Direct-axiom partition

Every one of the 45 active authoritative axioms must occur directly in exactly
one maintained product:

1. target-neutral source axiom → alignment core;
2. BFO-bearing axiom without a CCO term → BFO mapping;
3. CCO-bearing or mixed BFO/CCO axiom → CCO extension.

The three direct-axiom sets must be pairwise disjoint, and their union must
equal the complete active authoritative axiom set.

A row's product classification must be derived from its canonical
authoritative axiom rather than from lexical matching against the workbook
cell text.

## Excluded initial products

### Integrated ontology

The temporary `active-mappings.ttl` emitted by
`tools/check_sosa_next_mapping.py` remains a validation artifact. It is not a
maintained or published ontology product.

A consumer that needs the complete set of project mapping axioms can load the
CCO extension, which transitively imports the BFO mapping and alignment core.
These project products do not import the external SOSA, BFO, or CCO ontologies;
a consumer that needs a complete reasoning closure must load the governed source
and target dependencies separately.

### BFO projection

The initial SOSA-next product set contains no BFO-projection product. No
weakened or transformed BFO consequence has yet been approved as a separate
governed product axiom.

A BFO projection may be introduced only through a separate policy change that:

- identifies the approved consequence for each source RowID;
- records its relationship to the authoritative axiom;
- proves that the projected axiom is entailed;
- maintains a separate product and import boundary;
- adds exact reconstruction and reasoning tests.

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

## Validation closures

Reasoning validation may assemble temporary closures, but closure triples must
not be serialized into maintained products.

Required reasoning profiles:

- alignment core with the unmodified pinned SOSA-next source closure;
- BFO mapping with the alignment core, pinned SOSA-next source closure, and
  governed BFO validation closure;
- CCO extension with the BFO mapping, alignment core, pinned SOSA-next source
  closure, and governed merged CCO/BFO validation closure.

Every profile must complete successfully with zero named unsatisfiable classes.

## Required implementation surface

The product implementation PR is expected to add or update only the minimum
surface needed for:

- `tools/generate_sosa_next_products.py`;
- a focused SOSA-next product checker;
- focused SOSA-next modular-product tests;
- Makefile generation and check targets;
- the three generated maintained products;
- removal of the two obsolete direct-mapping scaffold files;
- documentation of the development import graph.

Release package, release manifest, release archive, and formal publication
integration are explicitly deferred.

## Acceptance gates

The first maintained-product implementation must satisfy all of the following:

1. the governed workbook remains 119 rows with 119 unique RowIDs;
2. all 45 active mappings produce 45 canonical authoritative axioms;
3. all 45 axioms are assigned directly to exactly one product;
4. all 26 deferred rows produce no direct axiom;
5. all 48 explicitly unmapped rows produce no direct axiom;
6. all three products have canonical ontology metadata and import boundaries;
7. two independent builds produce byte-identical products;
8. all product hashes and exact triple counts are asserted by focused tests;
9. all three reasoning profiles have zero named unsatisfiable classes;
10. the pinned SOSA-next source files remain byte-identical;
11. the current-SOSA maintained products remain byte-identical;
12. the current-SOSA generator and release tests remain unchanged in behavior;
13. temporary COMS resolver configuration is restored after success and
    failure;
14. no tracked file is changed in checker-only mode;
15. the full repository unit-test suite passes.

The current-SOSA byte-preservation gate must protect:

| Product | Required SHA-256 |
|---|---|
| `SSN2BFO.ttl` | `c31997d7e7b8c5e0bffd3f23a4597ab4be80786978462fefe800c4c7a5dc0c11` |
| `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` | `17695ef17379924449153b2c92ffaed6b57d497a1b2d1e854f584614cebec770` |
| `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` | `676b31620df10db5c26c46bcc44b2dfd5939d606b16e0fa8a910926e8497c3af` |
| `releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl` | `b5c1163eb6ab24c2e111e9e76c7b97acb20d897c9d1abc3daa555628206da5b0` |
| `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` | `2908f89648d42dc928f7225056216f1cbf3bcdc79de1bcf770b40a017a5e9bf5` |

## Formal-release transition

Formal release integration is a later phase. Before release:

- the approved SOSA source-version identity must replace `sosa-next` in package
  paths and ontology IRIs;
- release products must receive date-based version IRIs under
  `http://www.sks.ai/SSN2BFO/releases/<release-id>/`;
- the package catalog must resolve project and dependency imports offline;
- release manifests, checksums, archives, and rehearsal must be extended
  without changing the current-SOSA package contract;
- no placeholder or development ontology IRI may enter the formal archive.

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
