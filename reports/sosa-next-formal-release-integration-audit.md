# SOSA-next Formal-Release Integration Audit

## Purpose

This audit identifies the remaining changes required to move the implemented
three-product SOSA-2023 development architecture into a deterministic formal
release.

The immutable source identity and product-role inventory are resolved. The
development product-role migration is also complete: Integrated, BFO Mapping,
and CCO Extension are materialized, while Alignment Core and BFO Projection
remain governed omitted roles.

This audit does not itself modify release metadata, manifest, package, archive,
rehearsal, or publication code.

## Current development baseline

The maintained development products are:

| Product | Path | Direct axioms | Logical triples | Total triples |
| --- | --- | ---: | ---: | ---: |
| Integrated | `releases/sosa-next/sosa-integrated.ttl` | 45 | 273 | 286 |
| BFO Mapping | `releases/sosa-next/sosa-bfo-mapping.ttl` | 21 | 157 | 165 |
| CCO Extension | `releases/sosa-next/sosa-cco-extension.ttl` | 24 | 116 | 125 |

Integrated directly contains all 45 canonical authoritative axioms. The BFO
Mapping plus CCO Extension modular union also contains 273 logical triples and
is isomorphic to Integrated.

The catalog-resolved editor closure is:

```text
editor
  -> Integrated
```

That local project stack contains 290 distinct triples.

Integrated imports the governed SOSA root, SOSA Systems, SOSA Sampling,
source-declaration overlay, and merged CCO/BFO dependency. The BFO Mapping has
no import. The CCO Extension imports only the BFO Mapping.

Alignment Core is non-materialized because there is no active target-neutral
axiom. BFO Projection is non-materialized because no weakened consequence is
approved.

## Resolved source-identity prerequisite

The approved immutable source-version identity is:

`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`

It denotes the Semantic Sensor Network Ontology - 2023 Edition source snapshot
pinned to the full W3C upstream commit:

`af425a0454ec00512a5ebfa2873fe35a077f5fda`

`config/sosa-source-version.toml` is the machine-readable authority. The
development alias remains `sosa-next`; current development paths and ontology
IRIs are intentionally not renamed by the source-identity milestone.

During future formal-release integration, the exact approved identity must
replace `sosa-next` in:

- track-specific package paths;
- stable ontology IRIs;
- formal version-IRI suffixes;
- catalog mappings;
- release notes and user documentation;
- manifest product records and source evidence.

Abbreviated commit identities are not permitted. This resolves the
source-identity selection prerequisite but does not itself perform any
formal-release integration.

## Current formal-release authority

The existing formal-release system remains specific to the current SSN/SOSA
track, but it now follows the uniform product-role policy:

- publication metadata defines four materialized current-track products:
  Integrated, Alignment Core, Strict BFO Mapping, and CCO Extension;
- BFO Projection remains governed but non-materialized;
- manifest schema version 2 and the Python release model require those four
  product records;
- package construction uses the four current-track product paths;
- the package contains 12 regular files;
- the package catalog maps four same-release version IRIs;
- the archive authority requires 16 members;
- release rehearsal rebuilds and compares the same package and archive twice.

The SOSA-2023 products must continue to be integrated as a separate formal
package rather than inserted into the current-track inventories piecemeal.

## Resolved package boundary and superseded fixed inventory

The track identity is resolved as
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`.

The source-version track remains a separate formal package.

The earlier fixed three-product inventory is superseded by the uniform
product-role policy in `config/product-role-policy.toml`.

The current SOSA-2023 formal target is:

- Integrated;
- BFO Mapping;
- CCO Extension.

Alignment Core is omitted while it has no direct target-neutral axiom.
BFO Projection is omitted while no weakened consequence is approved.

The current-track formal machinery already follows the same role policy. Its
four materialized products exclude BFO Projection, which remains governed but
non-materialized.

### Publication metadata — implemented

The repository now has a separate governed SOSA-2023 publication-metadata
authority at `config/sosa-2023-publication-metadata.toml`.

The common metadata loader remains backward-compatible with the current
four-product default inventory and can accept an explicit canonical product
order for another governed track. The SOSA-2023 authority contains exactly
Integrated, BFO Mapping, and CCO Extension, with stable ontology IRIs and
release-IRI suffixes rooted in the approved immutable source identity.

The metadata `path` fields identify the maintained development source products
used by the renderer; they are not formal package-relative paths. Canonical
package paths remain part of the separate package-construction milestone.

### Formal rendering — implemented

`tools/generate_sosa_next_products.py` now provides a pure in-memory
SOSA-2023 formal renderer. Under an explicit formal release context it:

- preserves the approved immutable stable ontology IRIs;
- adds date-based same-release version IRIs;
- substitutes immutable-release authority status;
- adds release date and version information;
- preserves each development logical graph;
- renders deterministic bytes independent of input order;
- prohibits `sosa-next` and `/development/` identities from formal ontology
  bytes;
- keeps formal BFO Mapping import-free;
- rewrites the CCO Extension project edge to the same-release formal BFO
  Mapping version IRI;
- publishes Integrated with the official SOSA root, Systems, Sampling, and
  merged CCO/BFO imports;
- keeps the local source-declaration overlay as governed validation/source
  evidence rather than a published ontology import.

The fixed synthetic `2099-01-02` byte contract is:

| Product | Logical triples | Total triples | SHA-256 |
| --- | ---: | ---: | --- |
| Integrated | 273 | 288 | `81694ddfc0a7587c2d83517f0fc69449a25dc31ae68571b0a63f48aa5ca10aae` |
| BFO Mapping | 157 | 168 | `c88cb347742a15fc003cafe2e167f7f784cc4a70653720c11f1e6247e6a3096c` |
| CCO Extension | 116 | 128 | `bc356b515e29a21d74865101661fe1d81f2da33f86b31bf4c497109e8f9b202b` |

These capabilities do not yet construct a formal package.

### Manifest and schema

The manifest model and JSON schema must gain a deliberate SOSA-source-version
product inventory. Required evidence includes:

- workbook identity and SHA-256;
- all pinned source-file identities and SHA-256 values;
- generator, checker, canonicalization, and publication modules;
- development and formal product hashes;
- exact direct-axiom and triple counts;
- project import counts;
- product-specific reasoning results;
- catalog-consumption validation;
- toolchain identity.

The current formal-release authority is manifest schema version 2. The SOSA-2023 package should either receive a deliberate schema revision or a separate schema authority rather than being inserted into the current-track inventory implicitly.

### Package layout

A formal package needs an explicit canonical layout. At minimum it requires:

- license;
- release notes;
- checksum inventory;
- the three formal ontology products;
- a package-relative project catalog;
- canonical manifest;
- governed SOSA-next COMS workbook;
- governed publication metadata;
- sufficient pinned-source evidence to identify the mapped source closure.

The project must decide whether pinned external ontology files are recorded
only by identity and hash, as in the current release, or redistributed when
their licenses permit. No dependency should be copied implicitly.

### Package catalog

The package catalog must map exactly the formal same-release version IRIs to
the three package-relative products. It must not contain:

- development IRIs;
- the temporary `sosa-next` identity;
- remote dependency redirects;
- the editor shell unless that shell is explicitly approved as a release
  artifact.

### Archive

Archive integration requires a new canonical member inventory, member count,
directory inventory, and test authority. Existing raw-USTAR invariants should
remain unchanged:

- deterministic member order;
- fixed metadata and zero timestamps;
- canonical octal fields;
- zero padding;
- exactly two terminal zero records;
- external lowercase SHA-256 sidecar.

### Release notes

The release-note template must describe:

- the approved SOSA source version;
- the three included products;
- consumer selection guidance;
- the project import graph;
- active, deferred, and explicitly unmapped counts;
- reasoning and catalog-consumption validation;
- known limitations;
- the inclusion and omission rationale for every product role;
- dependency and license scope;
- deterministic reproduction commands.

### Release rehearsal and CI

Rehearsal must build and validate two isolated copies of the new formal
package and archive from the same commit, with network access blocked, then
compare every retained byte. Hosted CI should validate development products
continuously but should not create a formal package without explicit release
context and approved release notes.

## Recommended implementation sequence

1. **Completed:** define track-specific SOSA-2023 publication metadata.
2. **Completed:** implement deterministic formal rendering and same-release
   project-import rewriting.
3. **Next:** add a source-version manifest/schema authority and exact evidence
   model.
4. **Then:** implement separate-package construction and read-only validation.
5. **Then:** implement the canonical package catalog.
6. **Then:** implement the separate package's deterministic archive authority.
7. **Then:** add release notes, rehearsal, and hosted-CI regressions.
8. **Finally:** run a release-context rehearsal before actual publication.

Each stage should preserve current-track release bytes and behavior.

## Acceptance criteria for a future formal-release PR

A future implementation is ready only when:

1. no formal track-specific package path, formal ontology IRI, package catalog entry, or release note retains `sosa-next`;
2. all formal products are deterministic across independent processes;
3. formal rendering preserves the development logical graphs;
4. same-release project imports resolve wholly inside the package;
5. external dependencies are identified and governed without accidental
   network resolution;
6. manifest, package, catalog, archive, and sidecar bytes are canonical;
7. two isolated rehearsals produce byte-identical results;
8. all product reasoning profiles have zero named unsatisfiable classes;
9. current-track governed mapping content remains unchanged while its formal product inventory is migrated explicitly to the shared role policy;
10. the formal package records the approved source-version authority and the
    release notes have been explicitly approved.

## Non-goals of the source-identity milestone

The source-identity milestone does not:

- rename the current `sosa-next` development paths or ontology IRIs;
- change `config/publication-metadata.toml`;
- change release manifest or schema code;
- change package, archive, or rehearsal code;
- add SOSA-next products to the current formal release;
- modify the SOSA-next workbook;
- resolve deferred or explicitly unmapped rows;
- publish a release or deploy persistent IRIs.
