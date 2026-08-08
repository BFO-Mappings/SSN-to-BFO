# Product-Role Inclusion Policy

## Decision

Every governed SSN-to-BFO mapping track uses the same five product roles:

1. Integrated;
2. Alignment Core;
3. BFO Mapping;
4. BFO Projection;
5. CCO Extension.

Uniformity applies to the role taxonomy and inclusion criteria, not to the
number of ontology files materialized for every track.

A role is materialized only when it has either:

1. direct product-specific logical content; or
2. a distinct documented consumer function that is not supplied merely by
   loading another materialized product.

An empty ontology used only to reserve an import boundary, namespace, future
slot, or visually uniform architecture does not satisfy the inclusion rule.

The machine-readable authority is:

`config/product-role-policy.toml`

## Role criteria

### Integrated

Integrated may be materialized when it provides a distinct complete consumer
entry point, including the governed dependency-loading behavior of the track.

Its justification is therefore consumer function rather than mere duplication
of the modular logical union.

### Alignment Core

Alignment Core is materialized only when the track contains direct
target-neutral alignment axioms assigned to that role.

A zero-direct-axiom alignment shell is not sufficient.

### BFO Mapping

BFO Mapping is materialized when the track contains direct governed BFO-bearing
mapping axioms assigned to that role.

The canonical machine key remains `strict_bfo_mapping`.

### BFO Projection

BFO Projection is materialized only when at least one approved weakened but
sound BFO consequence is assigned directly to that role.

Importing the strict BFO mapping without adding a projection consequence does
not provide a distinct consumer function and is not sufficient for formal
publication.

### CCO Extension

CCO Extension is materialized when the track contains direct governed
CCO-bearing or mixed BFO/CCO axioms assigned to that role.

## Current SSN/SOSA target inventory

The next official current-track release targets:

1. Integrated;
2. Alignment Core;
3. BFO Mapping;
4. CCO Extension.

BFO Projection is omitted because no direct weakened projection axiom is
currently approved and its import-only closure is already supplied by the
strict BFO mapping.

The existing maintained import-only BFO-projection artifact remains in the
repository until a separate implementation migration removes it from current
generation and formal-release machinery. This policy changes publication
intent before changing maintained bytes.

## SOSA 2023 source-version target inventory

For
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`,
the formal target inventory is:

1. Integrated;
2. BFO Mapping;
3. CCO Extension.

Alignment Core is omitted because the current governed mapping contains no
direct target-neutral alignment axiom.

BFO Projection is omitted because no weakened BFO consequence is approved.

Integrated is included because it is intended to provide the distinct complete
consumer entry point for the source-version track, including governed source
and target dependency loading. The exact implementation and formal rendering
of that entry point remains a later milestone.

The currently maintained three-product development set is not changed by this
policy-only milestone. Its empty Alignment Core remains temporarily until the
subsequent generation migration.

## Relationship to prior decisions

This policy supersedes only the product-inventory portions of:

- `reports/publication-product-and-import-policy.md`; and
- `reports/sosa-release-package-scope-decision.md`.

It does not supersede:

- the COMS mapping authorities;
- strict-versus-weakened mapping semantics;
- the approved SOSA source identity;
- the decision to keep the SOSA source-version track in a separate package;
- the use of `strict_bfo_mapping` as the canonical machine key.

## Migration rule

Governance is changed before implementation.

A subsequent implementation milestone must:

- remove the current import-only BFO Projection from formal publication
  metadata, manifest/schema inventories, package/catalog/archive inventories,
  reasoning-result inventories, release notes, and maintained generation if no
  development-only reason remains;
- add a SOSA-2023 Integrated product with a distinct complete-consumer role;
- retire the zero-direct-axiom SOSA-2023 Alignment Core and remove the
  BFO-mapping import edge to it;
- update the SOSA-2023 editor/catalog consumer stack accordingly;
- preserve all governed mapping axioms and mapping dispositions;
- prove byte changes are exactly those required by the product-role migration.

No ontology-product bytes are changed by this policy milestone itself.
