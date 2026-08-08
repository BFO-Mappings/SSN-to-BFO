# SOSA-next Maintained Development Products

## Status

The SOSA-next track is a governed maintained development track for the
forthcoming SOSA source. It is generated from
`mappings/SOSA-next-to-BFO-COMS.xlsx`.

The approved immutable source-version identity is
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`, governed by `config/sosa-source-version.toml` and bound
to W3C upstream commit `af425a0454ec00512a5ebfa2873fe35a077f5fda`. The temporary name `sosa-next`
remains the development alias used by the current development paths and ontology
IRIs. It must not be used as the track identity in a future formal release.

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
make check-sosa-source-version
make check-product-role-policy
make check-sosa-release-scope
make check-sosa-next
make check-sosa-next-products
make check-sosa-next-consumer-stack
```

The source-version checker enforces the approved source identity, exact hashes
for all eight upstream files and the local declaration overlay, the root SOSA
edition version IRI, and the overlay's binding to the approved upstream commit.

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

These maintained development products have not yet been migrated to the
uniform product-role policy. The formal SOSA-2023 target inventory is
Integrated, BFO Mapping, and CCO Extension. The current zero-direct-axiom
Alignment Core is temporary and is scheduled for retirement during the
generation migration; BFO Projection remains omitted until a weakened
consequence is approved. The source-version package remains separate, and
formal paths and ontology IRIs must use the approved immutable source identity
rather than the `sosa-next` development alias.

See:

- `reports/sosa-source-version-identity-decision.md`
- `reports/sosa-release-package-scope-decision.md`
- `reports/sosa-next-product-contract.md`
- `reports/sosa-next-formal-release-integration-audit.md`
