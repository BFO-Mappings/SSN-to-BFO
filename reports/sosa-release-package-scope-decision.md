# SOSA Formal Package-Scope Decision

## Decision

The approved SOSA source-version track will be published as a separate formal
release package rather than combined with the current SSN/SOSA formal package.

The package contains exactly three ontology products, in this canonical order:

1. alignment core;
2. BFO mapping;
3. CCO extension.

No integrated ontology and no BFO-projection product are approved for this
formal source-version package.

The canonical machine product keys are:

1. `alignment_core`;
2. `strict_bfo_mapping`;
3. `cco_extension`.

`BFO mapping` remains the human-facing product name; `strict_bfo_mapping` is
the canonical machine key already used by the maintained SOSA-next generator
and the existing formal manifest vocabulary.

The machine-readable authority for this decision is:

`config/sosa-release-scope.toml`

## Source-version track

The package scope applies to the approved source identity:

`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`

The temporary `sosa-next` component remains the development alias. Future
formal package paths and stable track-specific ontology IRIs must use the
approved source identity rather than the development alias.

## Rationale

The current formal-release machinery is an exact contract for the existing
SSN/SOSA track. It defines and validates:

- exactly five formal products;
- a fixed five-product manifest order;
- exactly five product-specific HermiT results;
- exactly 13 package files;
- exactly 17 archive members;
- a package catalog for exactly five same-release product IRIs;
- the `current-ssn-sosa/` package directory;
- release-note requirements that include the current BFO-projection notice;
- rehearsal fixtures that require `current-ssn-sosa`, `evidence`, and `sources`.

The schema-1 manifest regression suite explicitly rejects a sixth product.

Combining the new three-product source-version track with that package would
therefore require changing the semantics of the existing formal package
authority, not merely adding a parallel release track.

A separate package preserves the current package contract exactly while
allowing the source-version package to define its own:

- three-product publication metadata;
- manifest/schema authority;
- package-relative catalog;
- evidence inventory;
- archive member inventory;
- release notes;
- deterministic rehearsal.

## Current-track preservation rule

The existing current SSN/SOSA formal-release machinery remains unchanged.

The source-version package must be implemented through separate track-specific
authorities or explicit generalized infrastructure whose current-track behavior
and bytes remain exactly preserved.

No source-version product may be inserted into the existing five-product
current package inventory.

## Formal product inventory

The formal source-version package inherits the maintained three-product
partition:

| Product | Formal package status |
| --- | --- |
| Alignment core | included |
| BFO mapping | included |
| CCO extension | included |
| Integrated ontology | excluded |
| BFO projection | excluded |

An additional ontology product requires a separate governance decision before
it can enter the formal package contract.

## Consequence for future implementation

The next formal-release milestone is to define track-specific publication
metadata and formal rendering for the separate source-version package.

That work must use the approved source identity as the formal track component
and must not modify the current five-product publication metadata or package
contract merely to accommodate the new package.

## Non-goals

This decision does not:

- build the source-version formal package;
- modify current formal-release metadata;
- modify the current manifest schema or Python manifest model;
- modify current package construction or validation;
- modify current archive construction or validation;
- modify current release rehearsal;
- rename maintained `sosa-next` development artifacts;
- publish a release, tag, archive, or persistent-IRI deployment.
