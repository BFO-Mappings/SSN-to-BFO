# Product Architecture

## Maintained current-track products

The current SSN/SOSA track consists of one integrated ontology and four maintained modular products generated from governed COMS.

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

### BFO projection

Path:

```text
releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl
```

The BFO projection imports only the strict BFO mapping. It currently asserts zero direct projection axioms because no governed CCO-to-BFO transformation or weakened-consequence rule has been approved.

Its project-module closure is therefore the same 48 governed axioms supplied by the strict BFO mapping and alignment core.

Future projection axioms require governed transformation rules and explicit proof obligations.

Focused validation:

```bash
make check-bfo-projection
```

### CCO extension

Path:

```text
releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl
```

The CCO extension directly asserts 57 governed axioms:

- 25 CCO-bearing axioms
- 32 mixed BFO/CCO axioms

It imports only the strict BFO mapping, whose alignment-core import completes the 105-axiom project-module closure without duplicating either imported layer.

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
BFO projection

alignment core
      ↑
strict BFO mapping
      ↑
CCO extension
```

The integrated ontology is a separate complete product rather than the root of this modular import chain.

## Development metadata

`config/publication-metadata.toml` governs the five product paths, stable ontology IRIs, release suffixes, labels, descriptions, product types, license, repository reference, authority statuses, and generated-file warning.

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
make check-sosa-next
make check-sosa-next-products
make check-sosa-next-consumer-stack
```

The SOSA-next products are not yet formal-release products. Current release
metadata, manifest, package, archive, and rehearsal tooling remain authoritative
only for the five-product current SSN/SOSA track. Formal publication is blocked
until the temporary `sosa-next` path and ontology-IRI component is replaced by
an approved source-version identity and the release machinery is deliberately
extended.

The earlier `reports/publication-product-and-import-policy.md` records the
pre-activation lifecycle policy. For the implemented SOSA-next development
track, `reports/sosa-next-product-contract.md` is the controlling product
contract.
