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

The current SSN/SOSA COMS transaction does not require a
development XML catalog. It explicitly loads pinned local dependencies under
`imports/` and resolves maintained current-track project imports through
governed local paths.

The SOSA-next development track has a separate governed catalog at
`src/sosa-next/catalog-v001.xml`. It resolves:

- eight byte-pinned upstream SOSA files plus one governed local declaration
  overlay;
- the governed merged CCO/BFO validation dependency;
- the three maintained SOSA-next project products;
- the SOSA-next editor shell.

`config/sosa-source-version.toml` is the machine-readable authority for the
approved source identity `sosa-2023-af425a0454ec00512a5ebfa2873fe35a077f5fda`, the full upstream W3C commit,
the eight upstream source-file hashes, and the separately governed overlay.

The maintained SOSA-next project products import only other SOSA-next project
products. They do not import the external source or target dependencies
resolved by the catalog.

`imports/cco.ttl` remains a flattened merged CCO/BFO validation dependency. It
is not a placeholder, mapping authority, or serialized import of every
published product.

The XML catalog inside a formal current-track release package is a different
artifact. It maps exactly the five immutable same-release version IRIs to
package-relative products. The development SOSA-next catalog is not currently
copied into a formal package.

## SOSA-next development validation

The forthcoming-SOSA workbook and its three maintained products have separate
focused gates:

```bash
make check-sosa-source-version
make check-product-role-policy
make check-sosa-release-scope
make check-sosa-next
make check-sosa-next-products
make check-sosa-next-consumer-stack
```

`make check-sosa-source-version` validates the approved immutable source
identity, exact source and overlay hashes, root SOSA edition version IRI, and
overlay binding to the approved full upstream commit. It performs no network
resolution.

`make check-product-role-policy` validates the uniform five-role product
taxonomy and the rule that a role is materialized only for direct logical
content or a distinct consumer function.

`make check-sosa-release-scope` validates that the approved publication model
remains a separate source-version package, that its formal target inventory is
derived from the product-role policy, and that the current formal package is
marked pending migration to the same role policy before its next official
release.

`make check-sosa-next` depends on the source-version gate and validates the 119
governed workbook rows, 45 active
mappings, 26 deferred mappings, 48 explicitly unmapped rows, canonical
identity, and a clean HermiT result for the integrated active mapping.

`make check-sosa-next-products` independently rebuilds the three products,
requires byte-identical candidate builds, validates exact hashes and triple
counts, reconstructs the 273-triple logical graph, checks transactional
rollback behavior, and requires zero named unsatisfiable classes in all three
product-specific reasoning profiles.

`make check-sosa-next-consumer-stack` resolves every catalog target locally,
parses all dependency and project entries, verifies the exact project import
graph, loads the editor closure, and confirms that external dependencies remain
separate from the maintained project imports.

These checks are included in `make check` and hosted CI. They validate
maintained development artifacts only; they do not create a formal version
IRI, manifest, package, archive, tag, GitHub release, or persistent-IRI
deployment.

## Publication metadata

`config/publication-metadata.toml` is the sole editable publication-metadata source for the current four-product formal-release track. The uniform product-role policy separately governs five conceptual roles; `bfo_projection` is currently non-materialized.

Development-mode validation:

```bash
make check-publication-metadata
python tools/check_publication_metadata.py
```

Formal rendering requires:

- a real `YYYY-MM-DD` release identifier
- the matching release date
- a `vYYYY-MM-DD` Git tag
- a full lowercase 40-hex source commit

Formal renderers:

- preserve stable ontology IRIs
- use immutable-release authority status
- add `owl:versionIRI`
- add plain `owl:versionInfo`
- add `dcterms:issued` as `xsd:date`
- rewrite modular imports to same-release version IRIs

`make check-release-rendering` validates deterministic bytes, logical-graph preservation, closure counts, and independent HermiT consistency.

## Release package

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
