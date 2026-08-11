# Validation and Release Engineering

## Canonical validation

`make check` is the authoritative local and hosted-CI validation gate.

It includes:

- Turtle parsing
- COMS row-identity validation
- product-disposition validation
- modular-product tests
- SOSA-next maintained-product tests
- SOSA-next catalog consumer-stack tests
- SOSA-2023 publication-metadata, formal-rendering, manifest, and package tests
- publication-metadata validation
- formal release-context and rendering tests
- release-package, archive, and rehearsal tests
- COMS freshness and candidate validation
- instance-data smoke tests
- ELK entailment tests
- full local SOSA-closure HermiT consistency
- Python compilation
- whitespace and repository-cleanliness checks

## Validation environment

`requirements/validation.txt` declares direct Python packages.

`config/validation-toolchain.env` declares the supported Python, Java, and ROBOT versions, the ROBOT release URL and checksum, and the Java heap configuration. Hosted CI consumes these declarations rather than maintaining an independent version list.

The validation commands do not install Python or Java automatically. Java 22 must already be available on `PATH`.

The ROBOT bootstrap helper verifies its JAR checksum on every invocation:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements/validation.txt
python -m pip check

robot_bin="$(tools/install_validation_robot.sh)"
export PATH="${robot_bin}:${PATH}"

java -version
robot --version
make check
```

## Dependency and catalog policy

The current SSN/SOSA COMS transaction does not require a development XML
catalog. It explicitly loads pinned local dependencies under `imports/` and
resolves maintained current-track project imports through governed local paths.

The SOSA-next development track has a separate governed catalog at
`src/sosa-next/catalog-v001.xml`. It resolves 14 local targets:

- eight byte-pinned upstream SOSA files;
- one governed local source-declaration overlay;
- the governed merged CCO/BFO dependency;
- Integrated, BFO Mapping, and CCO Extension;
- the SOSA-next editor shell.

`config/sosa-source-version.toml` is the machine-readable authority for the
approved source identity
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`, the full upstream W3C
commit, the eight upstream source-file hashes, and the separately governed
overlay.

The Integrated Mapping imports the five governed dependency IRIs required for
its complete-consumer function: SOSA root, SOSA Systems, SOSA Sampling, the
source-declaration overlay, and merged CCO/BFO. The modular BFO Mapping is
import-free, while the CCO Extension imports only the BFO Mapping. The editor
imports only Integrated.

Catalog resolution keeps all of those imports local during development and
testing. The BFO and CCO modular products remain independently resolvable.

`imports/cco.ttl` remains the governed flattened merged CCO/BFO dependency. It
is not a mapping authority or a manually maintained mapping product.

The XML catalog inside a formal current-track release package is a different
artifact. It maps exactly the four immutable current-track same-release version
IRIs to package-relative products. The SOSA-next development catalog is not
copied into that package.

## SOSA-2023 validation

The SOSA-2023 workbook, maintained development products, formal rendering,
manifest authority, and deterministic package engine have separate focused
gates:

```bash
make check-sosa-source-version
make check-product-role-policy
make check-sosa-release-scope
make check-sosa-next
make check-sosa-next-products
make check-sosa-next-consumer-stack
make check-sosa-2023-publication-rendering
make check-sosa-2023-release-manifest
make check-sosa-2023-package
```

`make check-sosa-source-version` validates the approved immutable source
identity, exact source and overlay hashes, root SOSA edition version IRI, and
overlay binding to the approved full upstream commit. It performs no network
resolution.

`make check-product-role-policy` validates the uniform five-role product
taxonomy and the rule that a role is materialized only for direct logical
content or a distinct consumer function.

`make check-sosa-release-scope` validates the separate source-version package
boundary and its materialized target: Integrated, BFO Mapping, and CCO
Extension. Alignment Core and BFO Projection remain governed omitted roles.

`make check-sosa-next` validates the 119 governed workbook rows, 45 active
mappings, 26 deferred mappings, 48 explicitly unmapped rows, canonical
identity, and a clean HermiT result for the integrated active mapping.

`make check-sosa-next-products` independently rebuilds Integrated, BFO Mapping,
and CCO Extension; requires byte-identical candidate builds; validates exact
hashes and triple counts; verifies that the 273-triple BFO+CCO modular logical
union is isomorphic to the 273-logical-triple Integrated Mapping; checks
transactional rollback; requires the retired Alignment Core artifact to remain
absent; and requires zero named unsatisfiable classes in all three reasoning
profiles.

The fixed development reasoning closures contain:

- 15,127 triples for Integrated;
- 15,011 triples for BFO Mapping;
- 15,135 triples for CCO Extension.

`make check-sosa-next-consumer-stack` resolves every development catalog target
locally, parses all dependency and project entries, verifies the exact
Integrated and modular import boundaries, loads the 290-triple editor project
closure, and confirms that BFO Mapping and CCO Extension remain independently
resolvable.

`make check-sosa-2023-publication-rendering` validates the separate SOSA-2023
publication-metadata authority and renders all three formal products twice
under a fixed synthetic release context. It requires exact stable and version
IRIs, exact formal import boundaries, preservation of the development logical
graphs, byte-identical independent renders, and the locked synthetic formal
byte contract:

- Integrated: 273 logical triples, 288 total triples,
  SHA-256 `81694ddfc0a7587c2d83517f0fc69449a25dc31ae68571b0a63f48aa5ca10aae`;
- Strict BFO Mapping: 157 logical triples, 168 total triples,
  SHA-256 `c88cb347742a15fc003cafe2e167f7f784cc4a70653720c11f1e6247e6a3096c`;
- CCO Extension: 116 logical triples, 128 total triples,
  SHA-256 `bc356b515e29a21d74865101661fe1d81f2da33f86b31bf4c497109e8f9b202b`.

The formal Integrated product imports the official SOSA root, Systems, and
Sampling IRIs plus merged CCO/BFO. The local source-declaration overlay remains
governed source/validation evidence but is not a published ontology import.
Formal BFO Mapping is import-free. Formal CCO Extension imports the same-release
formal BFO Mapping version IRI.

`make check-sosa-2023-release-manifest` validates the separate SOSA-2023
schema-v1 manifest authority. The canonical evidence model records 31 governed
inputs, including the package runtime, builder, and checker as byte-affecting
non-packaged inputs; four formal external dependencies; the exact three-product
formal inventory; fixed HermiT closure counts of 15,130 / 15,014 / 15,141; and
an 11-member included-file evidence inventory.

The Sampling dependency evidence records the ontology identity actually
declared by the pinned file, `http://www.w3.org/ns/sosa/sam/`. This is
deliberately distinct from the formal Integrated import
`http://www.w3.org/ns/sosa/sampling/`.

`make check-sosa-2023-package` runs the package-runtime and package-construction
regressions. The production surfaces are
`tools/sosa_2023_release_runtime.py`, `tools/sosa_2023_build_release.py`, and
`tools/sosa_2023_check_release.py`; they remain separate from the current-track
release engine.

A complete synthetic SOSA-2023 package contains exactly 13 regular files:

```text
<release-id>/
  LICENSE
  RELEASE-NOTES.md
  SHA256SUMS
  catalog-v001.xml
  manifest.json
  sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda/
    sosa-bfo-mapping.ttl
    sosa-cco-extension.ttl
    sosa-integrated.ttl
  sources/
    SOSA-2023-to-BFO-COMS.xlsx
    product-role-policy.toml
    sosa-2023-publication-metadata.toml
    sosa-release-scope.toml
    sosa-source-version.toml
```

The manifest evidences 11 package members. `manifest.json` and `SHA256SUMS`
are excluded from the manifest's included-file records to avoid circularity.
`SHA256SUMS` covers the other 12 files and excludes itself.

Package construction renders from the copied package inputs, generates the
canonical three-entry same-release catalog, performs fixed-closure HermiT
validation, constructs two independent complete packages, and requires all 13
files to be byte-identical before retaining a candidate. The read-only checker
recomputes product, input, dependency, catalog, checksum, validation-environment,
and included-file evidence and can independently reconstruct a complete package.
The full reconstruction regression requires 13/13 byte identity while preserving
the original package bytes and mtimes.

`release-notes/SOSA-2023-SYNTHETIC-2099-01-02.md` is a deterministic test
fixture only. Package tests create only temporary synthetic packages; they do
not create a tag, GitHub release, release archive, persistent-IRI deployment,
or actual publication.

These gates are included in `make check` and hosted CI. SOSA-2023 deterministic
archive authority, isolated release rehearsal, and actual publication remain
later milestones.

## Publication metadata

Publication metadata is track-specific.

`config/publication-metadata.toml` remains the sole editable metadata authority
for the current four-product formal-release track.

`config/sosa-2023-publication-metadata.toml` is the separate metadata authority
for the three-product SOSA-2023 formal target. Its canonical product order is
Integrated, Strict BFO Mapping, and CCO Extension. Its stable ontology IRIs and
release-IRI suffixes use the approved immutable source-version identity
`sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`; formal ontology headers
contain no `sosa-next` or `/development/` identity.

The common metadata loader defaults to the current-track product order for
backward compatibility and accepts an explicit canonical product order for a
separate governed track. Existing current-track metadata bytes and formal
rendering remain unchanged.

Current-track development-mode validation remains:

```bash
make check-publication-metadata
python tools/check_publication_metadata.py
```

SOSA-2023 publication metadata and rendering are validated together by:

```bash
make check-sosa-2023-publication-rendering
```

Formal rendering requires a complete release context:

- a real `YYYY-MM-DD` release identifier;
- the matching release date;
- a `vYYYY-MM-DD` Git tag;
- a full lowercase 40-hex source commit.

Both formal rendering systems preserve stable ontology IRIs, use the
immutable-release authority status, add `owl:versionIRI`, plain
`owl:versionInfo`, and `dcterms:issued` as `xsd:date`, and preserve the
development logical graph.

The SOSA-2023 renderer remains a pure in-memory rendering capability. The
separate SOSA-2023 package engine invokes that renderer from copied package
inputs and is validated independently by `make check-sosa-2023-package`. The
current-track release machinery remains separate and unchanged.

## Current-track release package

`tools/build_release.py` builds a deterministic current-track candidate package only at an explicit absent output directory.

`tools/check_release.py validate --package-dir PATH` validates an existing package read-only.

A formal package contains exactly 12 regular files:

```text
<release-id>/
  LICENSE
  RELEASE-NOTES.md
  SHA256SUMS
  SSN2BFO.ttl
  catalog-v001.xml
  current-ssn-sosa/ssn-sosa-alignment-core.ttl
  current-ssn-sosa/ssn-sosa-bfo-mapping.ttl
  current-ssn-sosa/ssn-sosa-cco-extension.ttl
  evidence/coms-product-dispositions.json
  manifest.json
  sources/SSN2BFO-COMS.xlsx
  sources/publication-metadata.toml
```

The manifest records the formal release context, governed inputs, byte-affecting modules, product counts and hashes, validation dependencies, stable toolchain evidence, and independent validation outcomes.

External ontologies are not redistributed. The package is offline-complete for project-module imports only.

## Deterministic archive

`tools/release_archive.py` constructs and validates a raw, uncompressed POSIX USTAR archive.

The archive uses:

- fixed member order
- fixed canonical metadata
- zero member modification times
- canonical octal numeric fields
- zero-filled file-record padding
- exactly two final zero-filled 512-byte EOF records
- no additional record padding

The lowercase SHA-256 sidecar remains outside the archive.

Focused validation:

```bash
make check-release-archive
```

## Release rehearsal

`tools/rehearse_release.py` verifies a release from two isolated detached clones of the exact requested commit with Python socket access blocked.

The rehearsal compares:

- complete package bytes
- canonical manifests
- archives
- checksum sidecars

The tool does not change the invoking checkout, create a tag, upload an asset, create a GitHub release, or deploy an ontology.

Focused validation:

```bash
make check-release-rehearsal
```

A real retained release output is produced only through an explicit external absent output directory after the isolated proof passes.

## Published release

The first governed release is:

- Tag: `v2026-07-18`
- Source commit: `221c65ab27b59ae701f2ed73a98cb9e79d77b750`
- Release page: <https://github.com/BFO-Mappings/SSN-to-BFO/releases/tag/v2026-07-18>

No release package or archive is committed to the repository. The deterministic archive and checksum sidecar are distributed as release assets.

`release-notes/SYNTHETIC-2099-01-02.md` remains a deterministic release-engineering fixture. It is not an actual release announcement or release identity.

## Example validation

Current example instance data is under:

```text
src/current-ssn-sosa/examples/sosa-instance-data/
```

The files are example data, not ontology imports, mapping authorities, or maintained-product inputs.

Run:

```bash
make -C src/current-ssn-sosa validate-examples
```

or:

```bash
make -C src validate-examples
```

The checks parse every current-track Turtle example and write only temporary output beneath `src/current-ssn-sosa/build/artifacts/`.
