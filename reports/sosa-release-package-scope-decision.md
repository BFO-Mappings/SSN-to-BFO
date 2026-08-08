# SOSA Formal Package-Scope Decision

## Current status

The package-boundary portion of this decision remains approved:

The governed SOSA source-version track will be published as a separate formal
package rather than inserted into the current SSN/SOSA package.

The original fixed three-product inventory from this decision is superseded by:

`reports/product-role-inclusion-policy.md`

and its machine-readable authority:

`config/product-role-policy.toml`

## Source-version track

The package applies to:

`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`

The temporary `sosa-next` component remains a development alias and must not
become the formal track identity.

## Why the separate-package boundary remains

The existing current-track release system was built around a single track.
The SOSA source-version mapping has its own immutable upstream-source identity,
mapping dispositions, product inventory, evidence, and eventual package
catalog.

Keeping the track in a separate package preserves explicit provenance and
prevents one package manifest from conflating mappings against different source
snapshots.

The separate-package decision does not require every track to publish the same
number of ontology products.

## Superseded inventory decision

The earlier version of this decision required:

- Alignment Core;
- BFO Mapping;
- CCO Extension;

and excluded Integrated and BFO Projection.

That fixed inventory is superseded.

All tracks now use the uniform five-role taxonomy governed by
`config/product-role-policy.toml`.

For the current SOSA source-version state, the formal target inventory is:

1. Integrated;
2. BFO Mapping;
3. CCO Extension.

Alignment Core is omitted while it has no direct target-neutral mapping axiom.

BFO Projection is omitted while it has no approved weakened BFO consequence.

## Current-track consequence

The earlier requirement that the current five-product formal package remain
unchanged is also superseded.

Before the next official current-track release, its formal inventory must be
migrated to the uniform product-role policy. The current import-only BFO
Projection is therefore not approved for that future formal package unless a
direct weakened projection consequence is approved before release.

This governance change does not itself alter current product bytes or formal
release machinery.

## Next implementation milestones

Implementation should proceed separately:

1. migrate maintained/current formal machinery to the role policy;
2. migrate the SOSA-2023 maintained product set;
3. define source-version publication metadata and formal rendering;
4. implement its separate manifest, package, catalog, archive, and rehearsal.

No ontology bytes are changed by this decision record.
