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
| Integrated | `releases/sosa-next/sosa-integrated.ttl` | `http://www.sks.ai/SSN2BFO/development/sosa-next/integrated` |
| BFO Mapping | `releases/sosa-next/sosa-bfo-mapping.ttl` | `http://www.sks.ai/SSN2BFO/development/sosa-next/bfo-mapping` |
| CCO Extension | `releases/sosa-next/sosa-cco-extension.ttl` | `http://www.sks.ai/SSN2BFO/development/sosa-next/cco-extension` |

The modular project graph is:

```text
CCO Extension
  owl:imports -> BFO Mapping
```

The BFO Mapping imports no project or external ontology.

The Integrated Mapping directly asserts all 46 governed mapping axioms and
imports the governed SOSA root, SOSA Systems, SOSA Sampling,
source-declaration overlay, and track-specific merged CCO/BFO dependency at `src/sosa-next/imports/cco.ttl`. It is the distinct
complete consumer entry point required by the product-role policy.

Alignment Core remains a governed role but is not materialized because no
target-neutral authoritative axiom is active. BFO Projection remains governed
but non-materialized because no weakened consequence is approved.

## Consumer loading

For the complete governed mapping and its governed external dependencies, load:

```text
releases/sosa-next/sosa-integrated.ttl
```

For modular use, load the BFO Mapping directly, or load the CCO Extension to
obtain the CCO-bearing layer over the BFO Mapping.

For development use in Protégé or another catalog-aware ontology editor, load:

```text
src/sosa-next/sosa-mappings-edit.ttl
```

with:

```text
src/sosa-next/catalog-v001.xml
```

The editor imports only the Integrated Mapping.

The catalog independently resolves Integrated, BFO Mapping, CCO Extension, the
pinned SOSA source files, the governed source-declaration overlay, and the
track-specific merged CCO/BFO dependency at `src/sosa-next/imports/cco.ttl`.

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

- 119 governed rows and 46 canonical authoritative axioms;
- exact deterministic bytes for Integrated, BFO Mapping, and CCO Extension;
- 268 logical triples in Integrated;
- an isomorphic 268-triple BFO+CCO modular union;
- exact reasoning closures of 15,231, 15,114, and 15,239 triples;
- zero named unsatisfiable classes;
- absence of the retired Alignment Core artifact;
- preservation of current SSN/SOSA and pinned SOSA source bytes.

The consumer-stack checker enforces:

- 14 unique local catalog mappings;
- parseable catalog targets;
- `editor -> Integrated` as the complete project closure;
- exactly 285 distinct triples in that editor project stack;
- exact Integrated external imports;
- import-free BFO Mapping;
- `CCO Extension -> BFO Mapping`;
- independent catalog resolution of all three materialized products.

## Formal-release status

The development product-role migration is complete and the materialized
development inventory now matches the formal SOSA-2023 target: Integrated,
BFO Mapping, and CCO Extension.

Alignment Core and BFO Projection remain governed omitted roles.

Formal publication is still a separate phase. The source-version package
remains separate, and formal paths and ontology IRIs must use
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda` rather than the
`sosa-next` development alias.

See:

- `reports/sosa-source-version-identity-decision.md`
- `reports/sosa-release-package-scope-decision.md`
- `reports/sosa-next-product-contract.md`
- `reports/sosa-next-formal-release-integration-audit.md`
