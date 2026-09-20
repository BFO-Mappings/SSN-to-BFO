# COMS framework integration

The canonical primary-workbook production path now uses COMS for XLSX
extraction, resolution, semantic batching, RowID governance, and canonical
identity auditing. The compatibility projection supplies the existing
`ProcessedRow` and `WorkbookStats` interface to unchanged downstream SSN
policy, rendering, publication, and reporting code. Legacy-vs-COMS shadow
tests remain as independent migration evidence.

CI installs COMS commit
`f391a9201398dc0f9954f3cb08ffb0354a9e0f6d`, pinned in
`requirements/coms-integration.txt`, including the optional `xlsx` dependency.
The integration gate requires exact canonical payload and hash agreement for
all 105 governed rows. COMS rendering and product composition are not used.
Renderer equivalence has not been established, and no renderer cutover has
occurred.

The project-local integration layer contains a temporary mechanical projection
from audited COMS workbook rows into the existing legacy
`ProcessedRow` representation. It copies already-resolved expression trees,
ordered property chains, source kinds, and canonical identity values without
reparsing, re-resolving, or recomputing hashes. The legacy front half remains
available for non-primary inputs, SOSA/release consumers, and equivalence
testing. Renderer migration remains out of scope.

For `mappings/SSN2BFO-COMS.xlsx`, production `main()` calls the COMS-backed
wrapper before the unchanged disposition, product-membership, and legacy
renderer stages. Other workbook paths continue through the legacy front half.
The duplicate domain/range authoring rule now has one shared project authority
used by both paths; the temporary integration-local copy has been removed. The
approved cutover update changes only truthful generator provenance in the
maintained disposition and generation reports. The four ontology products and
all mapping/disposition semantics remain unchanged. The overall migration is
not complete: the compatibility projection and legacy comparison path remain
until a later cleanup milestone, and COMS compiler/document rendering is not
used.

For local framework development only, a sibling checkout may override the pin:

```bash
python -m pip install -e '../CommonOntologyMappingSpecification[xlsx]'
```

No local checkout path is part of the committed dependency configuration.
