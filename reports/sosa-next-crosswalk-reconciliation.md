# SOSA-next Crosswalk Reconciliation Audit

**Status:** Preliminary, report-only comparison. No COMS mappings are changed by this audit.

## Evidence

- External workbook: `SOSA-SSN to BFO-CCO-RO.xlsx`
- External workbook SHA-256: `26458f43ceab78ce11fa99e86f34494bfd53f9bcafd96f3bb1ff7e7103900d61`
- Governed workbook: `mappings/SOSA-next-to-BFO-COMS.xlsx`
- Governed workbook SHA-256: `a753664eca2ce2bd4249fc2521f6043751b01a2d3e970e9b351a0dbfbb66c435`
- The external workbook remains outside the repository; the reports record its identity and provenance.

## External source basis

- **SOSA/SSN 2023:** w3c/sdw-sosa-ssn @ 929f9a8 (2026-07-16); core + system + sample-relations extensions.
- **BFO 2020:** BFO-ontology/BFO-2020, tag release-2024-01-29 (044490f), src/owl/bfo-core.owl.
- **CCO:** CommonCoreOntologies release/2.2 (010c998). Your release pins CCO 2024-11-06; the Tab 5 fix and the Tab 3 current-SOSA mapping were validated against your pins, not 2.2.
- **RO:** oborel/obo-relations, tag v2025-12-17 (13620e1).

- **Version-control implication:** The external BFO/CCO crosswalk was evaluated against the versions listed above. Any proposed mapping must be rechecked against the exact target versions pinned by this repository before adoption.

- **Held open in source workbook:** Two modeling points are deliberately left as your questions, not decided here: whether sosa:Sensor is equivalent to cco:Sensor, and whether every sosa:Observation must contain an act of observation. Both are flagged where they occur.

## Scope

- In scope: Tab 1, SOSA/SSN 2023 to BFO/CCO.
- Out of scope for this branch phase: the RO mappings and BFO/CCO-to-RO bridge.
- This audit compares evidence and records candidate dispositions; it does not automatically adopt axioms.

## Inventory summary

- External BFO/CCO rows: **115**
- Governed COMS rows: **119**
- Exact term matches: **110**
- Namespace-alias matches: **5**
- External rows unmatched to COMS: **0**
- COMS terms absent from the external crosswalk: **4**

### External verdicts

| Verdict | Count |
|---|---:|
| Decision needed (default in place) | 9 |
| Not DL-expressible | 8 |
| OK as-is | 62 |
| Semantic redesign | 26 |
| Syntactic repair | 10 |

### Governed COMS status

| Status | Count |
|---|---:|
| active | 61 |
| deferred | 9 |
| explicitly_unmapped | 49 |

### Crosswalk coverage of governed COMS

- The external crosswalk covers all **61 active mappings**.
- It covers **5 of the 9 reasoned deferrals**.
- It covers all **49 explicitly unmapped rows**.
- The four governed terms absent from the external crosswalk are themselves reasoned deferrals: `sosa:ActuatableProperty`, `sosa:Asset`, `sosa:ObservableProperty`, and `sosa:Result`.
- Accordingly, the external-row status inventory is **61 active / 5 deferred / 49 explicitly unmapped**, while the complete governed-workbook inventory remains **61 active / 9 deferred / 49 explicitly unmapped**.

## Priority review queue

| Term | External verdict | Current COMS status | Preliminary disposition |
|---|---|---|---|
| `sosa:Observation` | Decision needed (default in place) | active | human decision — determine required process-part commitment |
| `sosa:Sampler` | Syntactic repair | active | substantive review — proposed equivalence conflicts with prior project decision |
| `sosa:Sensor` | Syntactic repair | deferred | defer — resolve equivalence against the exact target CCO version |
| `sosa:endTime` | OK as-is | deferred | preserve datatype-property deferral pending repository-wide support |
| `sosa:hasProperty` | Not DL-expressible | explicitly_unmapped | preserve outside active OWL mapping pending rule/SHACL design |
| `sosa:hasSample` | OK as-is | explicitly_unmapped | review as SOSA-next relation; do not transfer the current-SOSA simplicity rationale |
| `sosa:hasSimpleResult` | OK as-is | deferred | preserve datatype-property deferral pending repository-wide support |
| `sosa:isSampleOf` | OK as-is | explicitly_unmapped | review as SOSA-next relation; do not transfer the current-SOSA simplicity rationale |
| `sosa:resultTime` | OK as-is | deferred | preserve datatype-property deferral pending repository-wide support |
| `sosa:startTime` | OK as-is | deferred | preserve datatype-property deferral pending repository-wide support |

## Reconciliation rules

1. Treat the external workbook as expert evidence, not as an executable mapping authority.
2. Verify every target term against the repository's exact pinned BFO and CCO versions.
3. Preserve the datatype-property deferrals until repository-wide datatype-property support exists.
4. Keep `sosa:Sensor` version-sensitive and deferred until the target CCO definition is pinned and reviewed.
5. Treat `sosa:Observation` and `sosa:Sampler` as substantive modeling decisions, not syntax repairs.
6. Do not transfer the current-SOSA sample-property simplicity rationale to SOSA-next.
7. Route non-DL representation intent to a separately governed rule, SHACL, or annotation layer.

## Unmatched inventory

- Every external BFO/CCO term matched a governed COMS term, directly or through an approved namespace alias.

### Governed COMS terms absent from external crosswalk

- `sosa:ActuatableProperty`
- `sosa:Asset`
- `sosa:ObservableProperty`
- `sosa:Result`

## Detailed matrix

The complete row-level comparison is recorded in `reports/sosa-next-crosswalk-reconciliation.csv`.

No mapping disposition in that CSV is final until reviewed against the pinned source and target ontologies.
