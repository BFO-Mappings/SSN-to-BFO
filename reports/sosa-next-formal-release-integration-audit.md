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
formal package paths are now governed separately by the SOSA-2023 manifest and
package-construction authority.

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

The separate SOSA-2023 manifest model and JSON schema now define the deliberate source-version product inventory. Governed evidence includes:

- workbook identity and SHA-256;
- all pinned source-file identities and SHA-256 values;
- generator, checker, canonicalization, and publication modules;
- development and formal product hashes;
- exact direct-axiom and triple counts;
- project import counts;
- product-specific reasoning results;
- catalog-consumption validation;
- toolchain identity.

The current-track formal-release authority remains manifest schema version 2 and is unchanged. SOSA-2023 now has the separate authority `config/sosa-2023-release-manifest-schema-v1.json`, implemented by `tools/sosa_2023_release_manifest.py`. This preserves the separate-package publication model rather than inserting SOSA-2023 into the current-track manifest inventory.

Implemented manifest evidence now fixes:

- product order: Integrated, Strict BFO Mapping, CCO Extension;
- formal fixed-closure HermiT counts: 15,130 / 15,014 / 15,141;
- 31 governed input-evidence records, including the package runtime, builder,
  and checker as byte-affecting non-packaged inputs;
- four external formal dependency records;
- an 11-member included-file evidence inventory;
- immutable source-version formal package paths with no `sosa-next` identity;
- preservation of the current manifest schema-v2 and current release tooling.

The Sampling dependency record uses the ontology identity declared by the
pinned file, `http://www.w3.org/ns/sosa/sam/`. The formal Integrated product
continues to import `http://www.w3.org/ns/sosa/sampling/`; dependency evidence
and formal import identity are deliberately distinct.

The package-construction layer is now implemented by
`tools/sosa_2023_release_runtime.py`, `tools/sosa_2023_build_release.py`, and
`tools/sosa_2023_check_release.py`. It remains separate from the current-track
package engine.

### Package layout — implemented

The canonical SOSA-2023 package contains exactly 13 regular files:

- license;
- SOSA-2023 synthetic/approved release notes;
- `SHA256SUMS`;
- the three formal ontology products;
- a three-entry package-relative formal catalog;
- canonical `manifest.json`;
- the governed SOSA-2023 COMS workbook;
- product-role policy;
- SOSA-2023 publication metadata;
- release-scope policy;
- immutable source-version evidence.

The manifest included-file inventory contains 11 members. `manifest.json` and
`SHA256SUMS` are excluded from that inventory to avoid circular evidence.
`SHA256SUMS` covers exactly the other 12 files and excludes itself.

External dependencies are recorded by exact identity, path, hash, and byte
size; they are not redistributed as package members.

Package construction performs two independent complete builds under the same
formal release context, runs the three fixed HermiT profiles for each build,
and requires all 13 package files to be byte-identical before publication of a
candidate output directory.

The read-only checker validates layout, copied inputs, same-input formal
reconstruction, manifest evidence, dependency evidence, validation environment,
catalog bytes, checksums, development-artifact nonmutation, and local-path
leakage. Full reconstruction must reproduce all 13 files byte-for-byte while
leaving the retained package bytes and mtimes unchanged.

### Package catalog — implemented

The package catalog maps exactly the three formal same-release version IRIs to
the three package-relative products. It contains no development IRIs,
`sosa-next` identity, remote dependency redirects, or editor-shell entry.

### Archive — implemented

The separate deterministic archive authority is implemented by
`tools/sosa_2023_release_archive.py` with permanent regression coverage in
`tests/test_sosa_2023_release_archive.py`.

The canonical archive is a raw uncompressed POSIX USTAR stream with exactly 16
members: the archive root, two package directories, and the complete 13-file
SOSA-2023 package. It preserves the existing release-engine invariants:

- deterministic explicit member order independent of package traversal;
- fixed file and directory modes;
- zero uid, gid, device identifiers, and modification times;
- canonical octal numeric fields and header checksums;
- zero-filled file-record padding;
- exactly two terminal zero-filled 512-byte EOF records with no trailing data;
- rejection of duplicate, reordered, unsafe, special-type, or noncanonical
  members;
- an exact lowercase external SHA-256 sidecar;
- no-replace atomic publication of the complete archive/sidecar pair.

The external asset filename includes the complete immutable source-version
identity:
`SSN2BFO-sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda-<release-id>.tar`.
This prevents collision with the current-track
`SSN2BFO-<release-id>.tar` asset. The internal archive root is the shorter
`SOSA-2023-<release-id>/`; this keeps all raw-USTAR names within the 100-byte
name field while the formal ontology members themselves retain the complete
immutable track identity.

The real-package synthetic contract requires two independent archive
constructions from the same actual 13-file package to be byte-identical, with
a canonical 140-byte checksum sidecar. Validation is read-only and leaves the
package, archive, and sidecar unchanged.

The package manifest intentionally records the actual validation environment,
including Python and Java runtime identity. Therefore complete package bytes,
the resulting whole-archive SHA-256, and potentially the padded archive size
are environment-specific evidence rather than a cross-environment fixed-byte
contract.

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

The focused hosted/local package regression now constructs only the fixed
synthetic SOSA-2023 package in temporary storage, validates its fixed HermiT
closures, and exercises full read-only reconstruction. It does not retain or
publish a real release artifact.

The separate formal release-rehearsal authority is now implemented by
`tools/sosa_2023_rehearse_release.py`, with focused regression coverage in
`tests/test_sosa_2023_release_rehearsal.py`. It binds the requested source
commit to the clean invoking HEAD, creates two isolated detached local clones,
blocks Python socket access during package and archive phases, rechecks
candidate checkout integrity after every phase, and independently builds and
validates the complete package and archive in both candidates. Rehearsal
requires byte-identical complete packages, equal parsed manifest models, and
byte-identical archives and sidecars before any output can be retained.

Verify mode retains no release output. Build mode removes the isolated
candidate roots before publication and can retain output only at an explicit
absent external destination through atomic no-replace publication. The
rehearsal does not approve a real release context or release notes and does not
create a tag, GitHub release, upload, or persistent-IRI deployment.

## Recommended implementation sequence

1. **Completed:** define track-specific SOSA-2023 publication metadata.
2. **Completed:** implement deterministic formal rendering and same-release
   project-import rewriting.
3. **Completed:** add a source-version manifest/schema authority and exact evidence
   model.
4. **Completed:** implement separate-package construction and read-only validation.
5. **Completed:** implement the canonical package catalog and checksum inventory.
6. **Completed:** implement the separate package's deterministic archive authority.
7. **Completed:** add isolated release rehearsal and archive equivalence checks.
8. **Finally:** approve a real release context and release notes, perform the final real rehearsal, and publish.

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
