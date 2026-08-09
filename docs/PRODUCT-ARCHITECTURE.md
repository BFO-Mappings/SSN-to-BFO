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

The separate SOSA-next track is now an active maintained development track,
not inactive scaffolding. Its sole editable mapping authority is
`mappings/SOSA-next-to-BFO-COMS.xlsx`.

Its approved immutable source-version identity is
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`. `config/sosa-source-version.toml` is the machine-readable
source authority. The existing `sosa-next` component remains only the
development alias and continues to identify the current development paths and
ontology IRIs until formal-release integration.

It consists of exactly three generated ontology products:

| Product | Path | Direct axioms | Total triples |
| --- | --- | ---: | ---: |
| Alignment core | `releases/sosa-next/sosa-alignment-core.ttl` | 0 | 8 |
| BFO mapping | `releases/sosa-next/sosa-bfo-mapping.ttl` | 21 | 166 |
| CCO extension | `releases/sosa-next/sosa-cco-extension.ttl` | 24 | 125 |

Their import graph is:

```text
SOSA-next alignment core
          ↑
SOSA-next BFO mapping
          ↑
SOSA-next CCO extension
          ↑
SOSA-next editor shell
```

The three maintained products contain 45 canonical authoritative axioms. Their
logical union has 273 triples and is isomorphic to the integrated active
mapping graph used during validation. The catalog-resolved editor stack,
including ontology metadata and project imports, contains 303 distinct
triples.

The alignment core imports no project or external ontology. The BFO mapping
imports only the alignment core. The CCO extension imports only the BFO
mapping. The editor shell imports only the CCO extension. External SOSA, BFO,
and CCO dependencies are resolved separately by consumers or assembled only
in temporary validation closures; their triples are not serialized into the
maintained project products.

The initial SOSA-next product set intentionally has no integrated ontology and
no BFO-projection product. Those products require separate consumer and
governance justification rather than automatic duplication of the current
SSN/SOSA architecture.

Focused validation:

```bash
make check-sosa-source-version
make check-sosa-next
make check-sosa-next-products
make check-sosa-next-consumer-stack
```

The maintained SOSA-next development products have not yet been migrated to
the uniform product-role policy. All mapping tracks use the same five product
roles, but a role is materialized only for direct product-specific logical
content or a distinct consumer function.

The current-track implementation now follows the uniform product-role policy.
Its materialized products are Integrated, Alignment Core, BFO Mapping, and CCO
Extension. BFO Projection remains a governed role but is omitted because no
weakened BFO consequence is currently approved, and the former import-only
ontology has been retired.

The SOSA-2023 formal target is Integrated, BFO Mapping, and CCO Extension. Its
current zero-direct-axiom Alignment Core is scheduled for retirement, and BFO
Projection remains omitted until a weakened consequence is approved. The
source-version track remains a separate package and uses
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda` as its formal track
identity.

The earlier `reports/publication-product-and-import-policy.md` records the
pre-activation lifecycle policy. For the implemented SOSA-next development
track, `reports/sosa-next-product-contract.md` is the controlling product
contract.
