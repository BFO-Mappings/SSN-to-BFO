# Product Architecture

## Maintained current-track products

The current SSN/SOSA track consists of one integrated ontology and three maintained modular products generated from governed COMS.

### Integrated mapping

Path:

```text
SSN2BFO.ttl
```

The integrated mapping directly asserts the complete governed COMS axiom set and remains the complete standalone authoritative project product.

It imports the governed external dependencies required by the integrated ontology.

### Alignment core

Path:

```text
releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl
```

The alignment core contains the 29 target-neutral governed axioms:

- 15 domain axioms
- 14 range axioms

It imports no source, target, or project ontology. It does not replace the integrated mapping.

Focused validation:

```bash
make check-alignment-core
```

### Strict BFO mapping

Path:

```text
releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl
```

The strict BFO mapping directly asserts 19 unchanged BFO-bearing governed axioms and imports only the alignment core.

Its project-module closure contains:

- 19 direct strict-BFO axioms
- 29 target-neutral alignment-core axioms

The published graph contains no CCO or RO logical terms. Validation reasons over the pinned local merged CCO/BFO dependency without making that dependency part of the published strict graph.

Focused validation:

```bash
make check-strict-bfo-mapping
```

### BFO Projection role

BFO Projection remains one of the five product roles, but it is not currently
materialized as an ontology product.

The role is reserved for weakened but sound BFO consequences approved through
governed transformation policy. Its current approved direct-axiom count is
zero. An import-only ontology does not provide a distinct consumer function,
because loading the strict BFO mapping already supplies the same project-module
closure.

The former import-only BFO Projection ontology has therefore been retired from
maintained generation, formal rendering, package construction, and release
validation. Role reconciliation remains governed through
`reports/coms-product-dispositions.json` and tested by
`tests/test_bfo_projection.py`.

A future BFO Projection ontology may be materialized only when at least one
approved weakened consequence is assigned directly to the role and the
product-role inclusion policy is satisfied.

### CCO extension

Path:

```text
releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl
```

The CCO extension directly asserts 55 governed axioms:

- 25 CCO-bearing axioms
- 30 mixed BFO/CCO axioms

It imports only the strict BFO mapping, whose alignment-core import completes the 103-axiom project-module closure without duplicating either imported layer.

The published extension contains no RO terms, transformed mappings, weakened projections, or copied dependency declarations.

Focused validation:

```bash
make check-cco-extension
```

## Product import structure

```text
alignment core
      ↑
strict BFO mapping
      ↑
CCO extension
```

The integrated ontology is a separate complete product rather than the root of this modular import chain.

## Development metadata

`config/publication-metadata.toml` governs the four materialized product paths, stable ontology IRIs, release suffixes, labels, descriptions, product types, license, repository reference, authority statuses, and generated-file warning. The separate product-role policy governs all five product roles, including non-materialized `bfo_projection`.

Development artifacts emit exactly seven governed annotations:

1. `rdfs:label`
2. `dcterms:description`
3. `dcterms:type`
4. `adms:status`
5. `dcterms:license`
6. `rdfs:seeAlso`
7. `rdfs:comment`

Formal release rendering retains the stable ontology IRI, replaces the development authority status with the immutable-release status, and adds the governed formal release identity.

## Retired current-track scaffolding

The former current-track editor, direct-mapping shells,
development catalog, and ungoverned hierarchy-projection analysis have been
retired.

## SOSA-next maintained development track

The separate SOSA-next track is an active maintained development track whose
sole editable mapping authority is `mappings/SOSA-next-to-BFO-COMS.xlsx`.

Its approved immutable source-version identity is
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`.
`config/sosa-source-version.toml` is the machine-readable source authority.
The `sosa-next` component remains only the development alias for current
development paths and ontology IRIs.

The uniform product-role migration is complete. The track materializes exactly
three ontology products:

| Product | Path | Direct axioms | Logical triples | Total triples |
| --- | --- | ---: | ---: | ---: |
| Integrated | `releases/sosa-next/sosa-integrated.ttl` | 45 | 273 | 286 |
| BFO Mapping | `releases/sosa-next/sosa-bfo-mapping.ttl` | 21 | 157 | 165 |
| CCO Extension | `releases/sosa-next/sosa-cco-extension.ttl` | 24 | 116 | 125 |

The Integrated Mapping is the distinct complete consumer entry point. It
directly asserts all 45 canonical authoritative axioms and imports exactly the
governed SOSA root, SOSA Systems, SOSA Sampling, source-declaration overlay,
and merged CCO/BFO dependency.

The modular project graph is independent of that complete entry point:

```text
SOSA-next CCO Extension
          |
          v
SOSA-next BFO Mapping
```

The BFO Mapping imports no ontology. The CCO Extension imports only the BFO
Mapping. Their logical union contains 273 triples and is isomorphic to the
Integrated Mapping's 273 logical triples.

The editor shell imports only the Integrated Mapping:

```text
SOSA-next editor shell
          |
          v
SOSA-next Integrated Mapping
```

The resulting local editor project closure contains 290 distinct triples.
`src/sosa-next/catalog-v001.xml` contains 14 local mappings covering the
governed source and target dependencies, all three maintained products, and
the editor shell. The BFO Mapping and CCO Extension remain independently
catalog-resolvable modular products.

Alignment Core remains a governed role but is non-materialized because the
current SOSA-2023 mapping has zero target-neutral authoritative axioms. BFO
Projection likewise remains governed but non-materialized because no approved
weakened-but-sound BFO consequence exists.

The maintained product hashes are:

| Product | SHA-256 |
| --- | --- |
| Integrated | `7ce45659e4d84ac089ae90c3279fa46d169d763ec487c34cb3c533eb0e6c197c` |
| BFO Mapping | `67bb58ea543e654ace41c0d1a393b2a3f92426c693f5100f0aa3ba35f3b005d2` |
| CCO Extension | `e65e96f15a55e19fc43be8dbda6e56351ef40bbd6e0fa9368a240e83c5d6bb69` |

The source-version track remains a separate future formal package, but its
publication-metadata and formal-rendering layers are now implemented.

`config/sosa-2023-publication-metadata.toml` governs the three formal product
identities. Formal stable ontology IRIs and date-based version-IRI suffixes use
the immutable source identity
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`; no formal ontology header
retains the `sosa-next` development alias.

The pure formal renderer preserves the three development logical graphs and
uses this formal import graph:

```text
Formal Integrated
  -> SOSA
  -> SOSA Systems
  -> SOSA Sampling
  -> merged CCO/BFO

Formal CCO Extension
  -> same-release Formal BFO Mapping

Formal BFO Mapping
  -> no ontology import
```

The development-only source-declaration overlay remains governed source and
validation evidence but is deliberately not a published formal import.

Under the fixed synthetic `2099-01-02` release context, the formal bytes are
locked at:

| Product | Logical triples | Total triples | SHA-256 |
| --- | ---: | ---: | --- |
| Integrated | 273 | 288 | `81694ddfc0a7587c2d83517f0fc69449a25dc31ae68571b0a63f48aa5ca10aae` |
| BFO Mapping | 157 | 168 | `c88cb347742a15fc003cafe2e167f7f784cc4a70653720c11f1e6247e6a3096c` |
| CCO Extension | 116 | 128 | `bc356b515e29a21d74865101661fe1d81f2da33f86b31bf4c497109e8f9b202b` |

Package paths, manifest/schema evidence, package catalog, archive, release
notes, rehearsal, and actual publication remain future formal-package work.

Focused validation:

```bash
make check-sosa-source-version
make check-product-role-policy
make check-sosa-release-scope
make check-sosa-next
make check-sosa-next-products
make check-sosa-next-consumer-stack
make check-sosa-2023-publication-rendering
```

For the development and formal-rendering contract, see
`reports/sosa-next-product-contract.md`.
