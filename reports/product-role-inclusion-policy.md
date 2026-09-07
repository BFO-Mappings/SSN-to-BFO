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

The current-track implementation migration is complete. The former
import-only BFO-Projection artifact has been removed from maintained generation,
formal rendering, release packaging, archive construction, and maintained
ontology bytes. The `bfo_projection` role remains governed with zero approved
direct axioms and may be materialized later only if substantive weakened
consequences satisfy this policy.

## SOSA 2023 source-version target inventory

For
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`,
the materialized development and formal target inventory is:

1. Integrated;
2. BFO Mapping;
3. CCO Extension.

Alignment Core is omitted because the governed mapping contains no direct
target-neutral alignment axiom.

BFO Projection is omitted because no weakened BFO consequence is approved.

Integrated is materialized because it provides the distinct complete consumer
entry point for the source-version track, including governed source and target
dependency loading. It directly asserts all 45 authoritative mapping axioms.

The development generation migration is complete. The former zero-axiom
Alignment Core has been retired, the BFO Mapping no longer imports it, the
editor/catalog stack uses Integrated as its complete entry point, and the
three materialized products now match the uniform product-role policy.

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

## Migration status

Governance was changed before implementation.

The current SSN/SOSA migration is now complete:

- publication metadata contains four materialized products;
- formal rendering, manifests, packages, catalogs, archives, and reasoning
  inventories omit the zero-direct-axiom BFO Projection role;
- maintained COMS generation no longer writes a BFO-Projection ontology;
- `tests/test_bfo_projection.py` retains role/disposition reconciliation
  coverage without serialization, validation, or reasoning machinery;
- governed mapping axioms and dispositions are preserved.

The SOSA-2023 source-version product-role migration is also complete:

- the Integrated development product provides the distinct complete-consumer
  role and directly asserts all 45 authoritative axioms;
- the zero-direct-axiom Alignment Core is retired;
- the BFO Mapping has no project import;
- the CCO Extension imports only the BFO Mapping;
- the editor imports Integrated and the catalog resolves all three materialized
  products;
- all governed mapping axioms and mapping dispositions are preserved; and
- the current SSN/SOSA products and pinned SOSA source bytes remain unchanged.
