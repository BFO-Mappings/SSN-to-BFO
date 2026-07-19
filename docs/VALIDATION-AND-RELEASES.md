# Validation and Release Engineering

## Canonical validation

`make check` is the authoritative local and hosted-CI validation gate.

It includes:

- Turtle parsing
- COMS row-identity validation
- product-disposition validation
- modular-product tests
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

No development XML catalog is required.

Validation explicitly loads the pinned local Turtle dependencies under `imports/` and resolves project-module imports through governed local paths.

`imports/cco.ttl` is a flattened merged CCO/BFO validation dependency. It is not a placeholder, mapping authority, or imported component of every published product.

The XML catalog inside a formal release package is different from a development catalog. It maps exactly the five immutable same-release version IRIs to package-relative products.

## Publication metadata

`config/publication-metadata.toml` is the sole editable publication-metadata source.

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

`tools/build_release.py` builds a deterministic candidate package only at an explicit absent output directory.

`tools/check_release.py validate --package-dir PATH` validates an existing package read-only.

A formal package contains exactly 13 regular files:

```text
<release-id>/
  LICENSE
  RELEASE-NOTES.md
  SHA256SUMS
  SSN2BFO.ttl
  catalog-v001.xml
  current-ssn-sosa/ssn-sosa-alignment-core.ttl
  current-ssn-sosa/ssn-sosa-bfo-mapping.ttl
  current-ssn-sosa/ssn-sosa-bfo-projection.ttl
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
