# SOSA-next Maintained Development Products

## Status

The SOSA-next track is a governed maintained development track for the
forthcoming SOSA source. It is generated from
`mappings/SOSA-next-to-BFO-COMS.xlsx`.

The temporary name `sosa-next` identifies the development track. It is not an
approved formal source-version identity and must not appear in a formal release
path or ontology IRI.

## Products

| Product | Path | Ontology IRI |
| --- | --- | --- |
| Alignment core | `releases/sosa-next/sosa-alignment-core.ttl` | `http://www.sks.ai/SSN2BFO/development/sosa-next/alignment-core` |
| BFO mapping | `releases/sosa-next/sosa-bfo-mapping.ttl` | `http://www.sks.ai/SSN2BFO/development/sosa-next/bfo-mapping` |
| CCO extension | `releases/sosa-next/sosa-cco-extension.ttl` | `http://www.sks.ai/SSN2BFO/development/sosa-next/cco-extension` |

The project import chain is:

```text
CCO extension
  owl:imports -> BFO mapping
    owl:imports -> alignment core
```

The alignment core currently asserts no target-neutral mapping axiom but
provides the stable import boundary required by the product contract.

The initial product set has no integrated ontology and no BFO-projection
product.

## Consumer loading

For the complete project mapping stack, load the CCO extension. Its project
imports provide the BFO mapping and alignment core transitively.

For development use in Protégé or another catalog-aware ontology editor, load:

```text
src/sosa-next/sosa-mappings-edit.ttl
```

with:

```text
src/sosa-next/catalog-v001.xml
```

The editor imports only the CCO extension.

The catalog also resolves the pinned forthcoming-SOSA source files and the
governed merged CCO/BFO validation dependency. Those external source and target
ontologies are not imported by the maintained project products. A consumer
that requires their declarations or full semantics must load the applicable
dependencies separately.

## Validation

Run:

```bash
make check-sosa-next
make check-sosa-next-products
make check-sosa-next-consumer-stack
```

The product checker enforces:

- 119 governed rows and 119 unique RowIDs;
- 45 active canonical authoritative axioms;
- 26 deferred rows with no direct axiom;
- 48 explicitly unmapped rows with no direct axiom;
- exact product partitioning;
- deterministic byte-identical independent builds;
- canonical metadata and project import boundaries;
- exact product hashes and triple counts;
- a 273-triple modular logical union;
- zero named unsatisfiable classes in all reasoning profiles;
- current-track byte preservation.

The consumer-stack checker enforces:

- 14 unique local catalog mappings;
- parseable catalog targets;
- the exact editor-to-product import closure;
- 303 distinct triples in the local editor project stack;
- no external dependency import from a maintained project product.

## Formal-release status

These products are not part of the current formal release package. Current
release metadata, manifest, package, archive, and rehearsal tooling remains
specific to the current five-product SSN/SOSA track.

See:

- `reports/sosa-next-product-contract.md`
- `reports/sosa-next-formal-release-integration-audit.md`
