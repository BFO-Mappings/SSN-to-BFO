# COMS framework integration

The initial COMS framework integration is shadow-only. Tests run the primary
workbook through COMS extraction, resolution, semantic batching, and canonical
identity auditing, then compare the result with the existing production path.
The production generator, product policy, rendering, publication, and release
machinery remain legacy-backed.

CI installs COMS commit
`f391a9201398dc0f9954f3cb08ffb0354a9e0f6d`, pinned in
`requirements/coms-integration.txt`, including the optional `xlsx` dependency.
The integration gate requires exact canonical payload and hash agreement for
all 105 governed rows. COMS rendering and product composition are not used.
Renderer equivalence has not been established, and no production cutover has
occurred.

The project-local integration layer now also contains a temporary mechanical
projection from audited COMS workbook rows into the existing legacy
`ProcessedRow` representation. It copies already-resolved expression trees,
ordered property chains, source kinds, and canonical identity values without
reparsing, re-resolving, or recomputing hashes. Production remains
legacy-backed, renderer migration remains out of scope, and the one-time
provenance-report update reserved for the eventual production cutover has not
occurred.

A COMS-backed primary-workbook processing wrapper now exercises extraction,
RowID preflight, semantic batching, compatibility projection, retained SSN
authoring checks, and legacy `WorkbookStats` reproduction without writing
outputs. It is verified equivalent to the legacy semantic front half, but it is
not yet authoritative: production `main()` still uses the legacy path, and
Commit 3 will perform the authority switch. The compatibility projection and
the integration-local duplicate domain/range policy mirror are temporary;
Commit 3 must consolidate the latter with the legacy inline rule into one
shared project-policy authority. COMS renderer migration remains out of scope,
and disposition-provenance bytes have not changed.

For local framework development only, a sibling checkout may override the pin:

```bash
python -m pip install -e '../CommonOntologyMappingSpecification[xlsx]'
```

No local checkout path is part of the committed dependency configuration.
