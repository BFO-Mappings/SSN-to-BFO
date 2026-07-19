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

## Inactive source scaffolding

The former current-track editor, direct-mapping shells, development catalog, and ungoverned hierarchy-projection analysis have been retired.

The separate `sosa-next` scaffold remains intentionally retained but inactive. Its temporary editor source, catalog, release shells, and optional local targets do not participate in current generation, validation, package construction, or publication.

The inactive scaffold is not an alias or compatibility layer for the maintained current-track products.
