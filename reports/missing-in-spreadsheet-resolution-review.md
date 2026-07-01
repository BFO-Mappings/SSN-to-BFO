# Missing-in-Spreadsheet Mapping Assertions Review

This note reviews TTL mapping assertions present in `SSN2BFO.ttl` that are not currently documented in `Current_SOSA-SSN to BFO-CCO.xlsx`.

No TTL or spreadsheet changes are made by this review note.

## Review policy

For each issue, decide whether:

- **Document in spreadsheet**: the TTL assertion is correct and should be represented in the spreadsheet.
- **Remove from TTL**: the spreadsheet omission is intentional or the TTL assertion is wrong.
- **Defer**: the assertion requires modeling discussion before either file is changed.

## Issues

### ISSUE-0001: `sosa:Sampler`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subClassOf`
- TTL target: `bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Sampling; cco:ont00001787`
- TTL line: `470`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0002: `sosa:Sensor`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subClassOf`
- TTL target: `bfo:BFO_0000017; bfo:BFO_0000040; bfo:BFO_0000054; bfo:BFO_0000196; sosa:Observation; cco:ont00001787`
- TTL line: `509`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0003: `sosa:hasFeatureOfInterest`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `cco:ont00001921`
- TTL line: `59`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0004: `sosa:hasSample`

- Category: `missing_in_spreadsheet`
- TTL predicate: `owl:propertyChainAxiom`
- TTL target: `bfo:BFO_0000084; cco:ont00001873`
- TTL line: `67`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0005: `sosa:isActedOnBy`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `cco:ont00001886`
- TTL line: `77`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0006: `sosa:isFeatureOfInterestOf`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `cco:ont00001841`
- TTL line: `81`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0007: `sosa:isResultOf`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `cco:ont00001816`
- TTL line: `86`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0008: `sosa:isSampleOf`

- Category: `missing_in_spreadsheet`
- TTL predicate: `owl:propertyChainAxiom`
- TTL target: `bfo:BFO_0000101; cco:ont00001938`
- TTL line: `90`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0009: `sosa:madeByActuator`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `cco:ont00001833`
- TTL line: `100`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0010: `sosa:madeObservation`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `cco:ont00001787`
- TTL line: `112`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0011: `sosa:madeSampling`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `cco:ont00001787`
- TTL line: `116`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0012: `ssn:hasDeployment`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `bfo:BFO_0000056`
- TTL line: `138`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD

### ISSUE-0013: `ssn:inDeployment`

- Category: `missing_in_spreadsheet`
- TTL predicate: `rdfs:subPropertyOf`
- TTL target: `bfo:BFO_0000056`
- TTL line: `155`
- Spreadsheet sheet: ``
- Spreadsheet row: ``

Decision: **TBD**

Rationale:

- TBD
