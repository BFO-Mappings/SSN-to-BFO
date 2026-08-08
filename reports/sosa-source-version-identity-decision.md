# SOSA Source-Version Identity Decision

## Decision

The approved immutable project identity for the governed SOSA source snapshot
is:

`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`

The machine-readable authority for this decision is:

`config/sosa-source-version.toml`

The temporary component `sosa-next` remains the development alias used by the
current development paths and ontology IRIs. This decision does not rename
those development artifacts. During future formal-release integration,
`sosa-next` must be replaced by the approved identity above in every formal
track-specific path, ontology IRI, version-IRI suffix, catalog mapping,
manifest product record, release note, and source-evidence record.

## Source represented by the identity

The source is the Semantic Sensor Network Ontology - 2023 Edition, whose SOSA
root ontology uses the version IRI:

`http://www.w3.org/ns/sosa/2023/`

The repository pins eight upstream Turtle files from the W3C
`sdw-sosa-ssn` repository at the full upstream commit:

`af425a0454ec00512a5ebfa2873fe35a077f5fda`

The locally maintained declaration overlay is separately governed and is bound
to that same upstream commit.

## Provenance proof

The source-identity audit independently fetched the exact W3C commit and
compared the repository's eight pinned upstream files against all Turtle blobs
at that commit by SHA-256.

Each local upstream file had exactly one byte-identical match:

| Local file | Upstream path |
| --- | --- |
| `src/sosa-next/imports/sosa.ttl` | `ssn/rdf/ontology/core/sosa.ttl` |
| `src/sosa-next/imports/sosa-common.ttl` | `ssn/rdf/ontology/core/sosa-common.ttl` |
| `src/sosa-next/imports/sosa-observation.ttl` | `ssn/rdf/ontology/core/sosa-observation.ttl` |
| `src/sosa-next/imports/sosa-actuation.ttl` | `ssn/rdf/ontology/core/sosa-actuation.ttl` |
| `src/sosa-next/imports/sosa-sampling.ttl` | `ssn/rdf/ontology/core/sosa-sampling.ttl` |
| `src/sosa-next/imports/sosa-deprecated.ttl` | `ssn/rdf/ontology/core/sosa-deprecated.ttl` |
| `src/sosa-next/imports/sosa-system.ttl` | `ssn/rdf/ontology/extensions/sosa-system.ttl` |
| `src/sosa-next/imports/sample-relations.ttl` | `ssn/rdf/ontology/extensions/sample-relations.ttl` |

The repository therefore identifies a specific immutable upstream Git state,
rather than relying only on the broader `2023` edition label.

## Naming rationale

The bare component `sosa-2023` is not sufficiently precise for this project's
formal source identity because the governed mapping is tied to the bytes of a
specific upstream source snapshot.

The approved identity therefore combines:

1. the upstream edition family: `sosa-2023`; and
2. the complete lowercase 40-character upstream Git commit:
   `af425a0454ec00512a5ebfa2873fe35a077f5fda`.

The full commit is used rather than an abbreviated Git identifier so the
project identity does not depend on abbreviation length or future repository
growth.

## Authority and validation

`config/sosa-source-version.toml` is the sole machine-readable authority for:

- the approved source identity;
- the development alias;
- the edition label and SOSA edition version IRI;
- the upstream repository and full commit;
- the eight upstream local/upstream path pairs and SHA-256 values;
- the local declaration overlay, its SHA-256, its upstream binding, and its
  purpose.

Run:

```bash
make check-sosa-source-version
```

The source-version checker rejects noncanonical or abbreviated identities,
unexpected authority fields, unsafe source paths, source-file hash drift,
overlay hash drift, a root SOSA version-IRI mismatch, or an overlay that no
longer records the approved upstream commit.

The governed SOSA-next mapping checker derives its `SOURCE_FILES` and
`PINNED_SOURCE_SHA256` compatibility interfaces from this authority rather than
maintaining a second source-pin table.

## Formal-release consequence

The source-identity approval prerequisite recorded in
`reports/sosa-next-formal-release-integration-audit.md` is resolved.

The next unresolved formal-release architecture decision is whether the
approved source-version track is published as:

- a separate release package; or
- part of a combined package with the current SSN/SOSA track.

No choice between those publication models is made here.

## Non-goals

This decision does not:

- rename `src/sosa-next/` or `releases/sosa-next/`;
- change any maintained SOSA-next development ontology IRI;
- modify any pinned W3C source ontology;
- modify the local declaration overlay;
- change the governed SOSA-next workbook or mapping dispositions;
- change current-SOSA products;
- change formal-release metadata, manifest, package, archive, or rehearsal
  machinery;
- create a formal release, tag, deployment, or persistent-IRI redirect.
