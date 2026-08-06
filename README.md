# SSN-to-BFO

SSN-to-BFO provides OWL mappings from the W3C/OGC Semantic Sensor Network Ontology and SOSA to Basic Formal Ontology (BFO) and the Common Core Ontologies (CCO).

The project follows and extends the mapping method introduced in [Prudhomme et al. (2025)](https://doi.org/10.1038/s41597-025-04580-1).

## Use the mapping

For most applications, use `SSN2BFO.ttl` from the [latest release](https://github.com/BFO-Mappings/SSN-to-BFO/releases/latest).

Load it as an OWL ontology in Protégé, ROBOT, a triplestore, or another RDF/OWL application. Your environment must also resolve the applicable SSN/SOSA, BFO, and CCO dependencies, which are not redistributed in the release archive.

For reproducible use, prefer the tagged release assets rather than files from an active development branch.

## Available products

| Product | File | Use when |
| --- | --- | --- |
| Integrated mapping | `SSN2BFO.ttl` | You want the complete SSN/SOSA-to-BFO/CCO mapping |
| Strict BFO mapping | `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` | You want the governed BFO mapping without CCO-bearing axioms |
| CCO extension | `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` | You want the modular BFO and CCO mapping stack |
| Alignment core | `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` | You want the target-neutral SSN/SOSA alignment layer |
| BFO projection | `releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl` | You need the designated projection layer; it currently adds no direct mapping axioms |

See [Product Architecture](docs/PRODUCT-ARCHITECTURE.md) for the relationships among these products.

## SOSA-next maintained development products

The repository also maintains a governed development track for the forthcoming
SOSA source. These products are generated from
`mappings/SOSA-next-to-BFO-COMS.xlsx`:

| Product | File | Use when |
| --- | --- | --- |
| SOSA-next alignment core | `releases/sosa-next/sosa-alignment-core.ttl` | You need the import-free target-neutral project layer |
| SOSA-next BFO mapping | `releases/sosa-next/sosa-bfo-mapping.ttl` | You need the governed BFO-bearing mappings |
| SOSA-next CCO extension | `releases/sosa-next/sosa-cco-extension.ttl` | You need the complete layered SOSA-next project stack |

The project import chain is:

```text
SOSA-next CCO extension
  -> SOSA-next BFO mapping
    -> SOSA-next alignment core
```

For development use in an ontology editor, load
`src/sosa-next/sosa-mappings-edit.ttl` with
`src/sosa-next/catalog-v001.xml`. The editor imports the CCO extension and
obtains the other project modules transitively. External SOSA, BFO, and CCO
dependencies remain separate consumer or validation inputs.

These files are maintained authoritative development artifacts, but they are
not part of the current formal release. The temporary `sosa-next` identity must
be replaced by the approved source-version identity before formal publication.

Focused development validation:

```bash
make check-sosa-next
make check-sosa-next-products
make check-sosa-next-consumer-stack
```

See [SOSA-next Development Products](src/sosa-next/docs/README.md) and the
[formal-release integration audit](reports/sosa-next-formal-release-integration-audit.md).

## Release

The current governed release is [`v2026-07-18`](https://github.com/BFO-Mappings/SSN-to-BFO/releases/tag/v2026-07-18).

The release provides:

- the integrated and modular ontology files
- release notes
- a manifest and checksums
- a catalog for resolving the packaged project modules

## Documentation

- [Product Architecture](docs/PRODUCT-ARCHITECTURE.md)
- [Mapping Governance](docs/MAPPING-GOVERNANCE.md)
- [Validation and Release Engineering](docs/VALIDATION-AND-RELEASES.md)
- [Licensing](docs/LICENSING.md)
- [Contributing](.github/CONTRIBUTING.md)

## License

Project-authored content is dedicated under [CC0 1.0 Universal](LICENSE), except for identified third-party material. Third-party ontologies, dependencies, and example data retain their original terms and notices.
