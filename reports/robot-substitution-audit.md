# ROBOT Substitution Audit for SSN-to-BFO

## Purpose

This report assesses how much of the current SSN-to-BFO implementation that is
not already performed by ROBOT could reasonably be moved to ROBOT.

The audit distinguishes:

1. operations ROBOT can replace directly;
2. operations that should use ROBOT beneath a thin Python governance layer;
3. operations that should remain custom Python;
4. opportunities to remove duplicated or obsolete implementation paths.

The audit was conducted on branch `review/robot-substitution-audit`. No
repository files were modified during the analysis.

## Executive conclusion

ROBOT can take over a substantial share of the ontology-processing layer, but
it should not replace the COMS governance and release layer.

The strongest substitution opportunities are:

- OWL axiom parsing and construction;
- ontology conversion and parse validation;
- closure assembly;
- axiom removal and filtering;
- HermiT and ELK invocation;
- SPARQL query and verification;
- ontology-level semantic diffs;
- some import and module extraction.

The following should remain custom Python:

- authoritative workbook interpretation;
- persistent RowIDs;
- canonical expression construction and hashing;
- product-disposition accounting;
- product-selection policy;
- deterministic custom rendering;
- exact-byte freshness checks;
- transactional replacement and rollback;
- release manifests, checksums, and deterministic archives;
- clean-clone release rehearsal;
- Git and GitHub governance;
- evidence-rich Markdown and JSON reports.

A realistic target is not to eliminate Python. It is to make Python responsible
for governance and policy while ROBOT performs generic OWL operations.

## Current implementation size

The current `tools/*.py` surface contains approximately 21,150 lines.

The largest modules are:

| File | Lines |
| --- | ---: |
| `tools/generate_mapping_from_coms.py` | 3,976 |
| `tools/modular_products.py` | 2,632 |
| `tools/check_coms_mapping.py` | 1,514 |
| `tools/rehearse_release.py` | 1,401 |
| `tools/product_dispositions.py` | 1,279 |
| `tools/publication_metadata.py` | 1,193 |
| `tools/test_elk_instance_mapping_entailments.py` | 1,190 |
| `tools/build_release.py` | 1,163 |
| `tools/compare_mappings.py` | 1,160 |

Most of this code is not generic RDF manipulation. It implements governance,
policy, reporting, deterministic publication, and release controls.

## Existing ROBOT use

The repository already uses ROBOT for:

- HermiT reasoning;
- ELK consistency gates;
- example parse validation;
- controlled release reasoning;
- some ontology conversion.

ROBOT is still invoked through several separate Python wrappers.

The older retained example-validation Makefile previously downloaded ROBOT
1.9.5 independently. It now delegates to
`tools/install_validation_robot.sh`, so example validation uses the governed
ROBOT 1.9.7 version, checksum, and Java heap configuration.

## Mapping-axiom generation

### Governed mapping set

The current COMS disposition evidence contains 105 governed mapping axioms:

| Mapping type | Rows |
| --- | ---: |
| Class mapping | 44 |
| Object-property mapping | 25 |
| Domain | 16 |
| Range | 15 |
| Property chain | 5 |
| **Total** | **105** |

The canonical target shapes are:

| Target shape | Rows |
| --- | ---: |
| Named IRI | 55 |
| Intersection | 36 |
| Union | 9 |
| Property chain | 5 |

### Direct ROBOT Template pilot

A temporary, read-only `robot template` pilot attempted the 100 non-chain rows
using their existing authoritative lexical targets.

Results:

| Mapping type | Attempted | Emitted unchanged | Failed |
| --- | ---: | ---: | ---: |
| Class mapping | 44 | 14 | 30 |
| Object-property mapping | 25 | 25 | 0 |
| Domain | 16 | 16 | 0 |
| Range | 15 | 15 | 0 |
| **Total** | **100** | **70** | **30** |

This proves that:

- all object-property mappings worked unchanged;
- all domains worked unchanged;
- all ranges worked unchanged;
- 14 class mappings worked unchanged;
- 30 complex class mappings failed with Manchester parse errors.

The failures were not caused by unsupported logical structures. They arose
because the COMS lexical expressions use project-specific CURIE-like names for
properties inside Manchester expressions. ROBOT Template requires those
properties to be resolvable by its Manchester parser.

### Normalized ROBOT Template pilot

The normalized pilot is now implemented as a read-only comparison path in
`tools/robot_template_generation_pilot.py`.

The existing COMS generator continues to resolve workbook expressions into
structured expression nodes and canonical full IRIs. The pilot then produces:

- deterministic temporary labels for every class and object property used in
  a class expression;
- a generated resolver ontology containing those labels;
- a generated ROBOT Template TSV using the temporary labels;
- a ROBOT-generated comparison ontology;
- an exact canonical-axiom comparison against the authoritative COMS
  identities.

Temporary labels are required because ROBOT 1.9.7 does not accept full class or
property IRIs inside Manchester restriction expressions. These labels are
generated implementation details and do not appear in the COMS workbook or any
maintained ontology product.

Results:

| Measure | Result |
| --- | ---: |
| Governed COMS rows | 105 |
| Attempted non-chain rows | 100 |
| Excluded property-chain rows | 5 |
| Expected canonical axioms | 100 |
| ROBOT canonical axioms | 100 |
| Missing axioms | 0 |
| Extra axioms | 0 |
| Mismatched axioms | 0 |
| Resolver entities | 82 |
| Pilot summary | PASS |

The generated resolver ontology and normalized template are byte-deterministic
across separate runs and different Python hash seeds. The five maintained
ontology products remain unchanged because the current Python generator remains
authoritative during this phase.

### Property chains

The five property chains are not covered by the documented Template pilot.

Options include:

1. retain current Python chain emission initially;
2. produce them as canonical OWL Functional Syntax and let ROBOT parse and
   serialize them;
3. generate controlled RDF list structures and merge them through ROBOT;
4. use a narrowly governed SPARQL construction step.

The safest initial architecture is to retain the five current chain mappings
until exact cross-tool equivalence is demonstrated.

## Recommended generation architecture

```text
COMS workbook
    ↓
Python workbook governance and expression resolution
    ↓
Python emits normalized ROBOT input
    ↓
ROBOT constructs or parses OWL axioms
    ↓
Python reconciles ROBOT output with canonical COMS axioms
    ↓
Python applies product dispositions and release policy
```

Python remains authoritative for mapping identity and governance. ROBOT becomes
the OWL construction and validation engine.

## Reasoning and closure construction

The current generator contains five separate HermiT wrappers:

- `run_candidate_hermit`;
- `run_alignment_core_hermit`;
- `run_strict_bfo_hermit`;
- `run_cco_extension_hermit`;
- `run_bfo_projection_hermit`.

Together, these functions span approximately 400 lines. Additional reasoning
wrappers exist for:

- full SOSA closure validation;
- object-property typing probes;
- ELK instance gates;
- release-package reasoning.

These should be consolidated into one configured ROBOT runner.

A generic reasoning profile should declare:

- product or closure inputs;
- catalog;
- configured removals;
- reasoner;
- output path;
- expected consistency;
- expected or prohibited unsatisfiable classes;
- whether materialized output is required;
- report label.

Python should continue interpreting the result and producing project-specific
evidence.

## Direct ROBOT substitution candidates

### Parse and conversion

Current custom or repeated RDF parsing can often be replaced or supplemented by
`robot convert`.

Recommended uses:

- parse every maintained ontology product;
- normalize temporary ontology syntax;
- independently verify generated Functional Syntax;
- provide a second parser alongside RDFLib.

### Merge and closure assembly

Repeated RDFLib loops that load and copy triples from several files are good
candidates for `robot merge`.

Python should still decide:

- which files belong in a closure;
- import-collapse policy;
- catalog selection;
- project-specific cleanup.

### Remove and filter

Several tools remove profile blockers or selected declarations in Python.

Potential ROBOT uses:

- `robot remove`;
- `robot filter`;
- configured term or axiom selection.

Custom Python remains appropriate when removal depends on complex project
semantics rather than a declarative selection.

### Query and verify

Good ROBOT candidates include:

- source-term coverage queries;
- unmapped-term queries;
- structural violation queries;
- forbidden-vocabulary checks;
- import-policy checks;
- some product-profile checks.

Use:

- `robot query` for informational result sets;
- `robot verify` for queries whose returned rows are validation failures.

### Semantic diff

`robot diff` can compare OWL ontologies while ignoring irrelevant
serialization differences.

Potential uses:

- current generated product versus ROBOT-generated comparison product;
- pre- and post-refactor semantic equivalence;
- product-architecture migration checks.

The current canonical COMS axiom comparison should remain the authoritative
row-level governance check.

### Import or module extraction

ROBOT extraction is a candidate for reducing retained import closures and
reasoner inputs.

This should supplement, not replace:

- pinned dependency governance;
- exact dependency hashes;
- catalog validation;
- release manifest accounting.

## Hybrid candidates

These should use ROBOT internally but retain Python control:

| Current capability | Recommended boundary |
| --- | --- |
| Product HermiT checks | ROBOT reasons; Python defines profile and interprets result |
| Full source closure | ROBOT merges/removes/reasons; Python defines exact closure |
| Typing probes | Python generates probes; ROBOT reasons over each probe |
| ELK instance gate | ROBOT checks consistency; Python retains deterministic expected-entailment checks |
| Source-term coverage | ROBOT query; Python reconciles results to governed rows |
| Modular-product validation | ROBOT handles general OWL checks; Python retains product policy |
| Legacy comparison | ROBOT semantic diff where useful; Python retains workbook-aware comparison |
| Publication metadata | ROBOT may annotate; Python remains authoritative for metadata policy and order |

## Capabilities that should remain custom

### COMS governance

- authoritative-column policy;
- workbook validation;
- RowID validation;
- canonical source expressions;
- canonical axiom identities;
- expression hashes;
- duplicate governed-axiom detection;
- explicit blank and deferred semantics.

### Product governance

- target classification;
- product-selection rules;
- per-row product dispositions;
- emitted/imported/transitive/deferred accounting;
- reconciliation of every governed row with every product.

### Deterministic publication

- stable prefix order;
- deterministic custom Turtle formatting;
- exact metadata placement;
- exact generated notices;
- exact-byte freshness checks;
- generated-report hashes.

### Release engineering

- verified toolchain declaration;
- release context;
- manifest generation;
- checksums;
- deterministic USTAR archive construction;
- atomic replacement;
- rollback;
- clean-clone release rehearsal;
- network isolation;
- release-note validation.

ROBOT can support ontology operations within these processes but cannot replace
their governance responsibilities.

## Estimated substitution potential

The following estimates distinguish OWL-operation coverage from total
repository-code reduction.

| Area | Estimated ROBOT coverage |
| --- | ---: |
| Mapping-axiom emission | 67% proven unchanged; 95% plausible after normalization |
| Parsing and conversion | 70–100% |
| Closure merge and removal | 60–90% |
| Reasoner invocation | 90–100% |
| SPARQL querying and verification | 60–100% |
| Product construction | 30–60% |
| Product validation | 20–50% |
| Instance and probe testing | 15–35% |
| COMS governance | 0–10% |
| Release engineering | 0–10% |
| Entire Python tool surface | approximately 15–25% |

A reasonable code-reduction target is approximately 3,000–5,000 lines, subject
to proof through narrow pilots. The greater benefit may be consistency and
reduced maintenance rather than raw line-count reduction.

## Recommended implementation sequence

### Phase 1: report-only validation

1. Commit this audit without changing production behavior.
2. Record the 70-of-100 unchanged Template baseline.
3. Add an exact Python-normalized class-expression pilot.
4. Compare ROBOT output with canonical COMS axiom identities.

### Phase 2: consolidate reasoning

1. Create one generic ROBOT reasoning adapter.
2. Express product-specific reasoning as configuration.
3. Migrate the five generator HermiT wrappers.
4. Preserve report text and expected result semantics.
5. Run the full current validation suite.

### Phase 3: add independent ROBOT generation

1. Emit normalized ROBOT inputs from governed COMS rows.
2. Generate a comparison ontology.
3. Canonicalize ROBOT output.
4. Require exact canonical-axiom equality with the current generator.
5. Keep the current generator authoritative during this phase.

### Phase 4: evaluate production generation

Only after exact equivalence is stable:

1. decide whether ROBOT should become the primary OWL axiom constructor;
2. retain Python governance and product selection;
3. preserve deterministic published bytes or explicitly govern a new rendering
   version;
4. avoid changing release artifacts merely to reduce implementation size.

### Phase 5: standardize other ROBOT operations

- merge and closure assembly;
- query and verify;
- semantic diff;
- import extraction;
- the retained example-validation Makefile.

## Completed immediate cleanup

`src/current-ssn-sosa/Makefile` now uses the repository-governed ROBOT installer
instead of downloading ROBOT 1.9.5 independently.

Both supported invocation paths were verified successfully:

- `make -C src/current-ssn-sosa validate-examples`;
- `make -C src validate-examples`.

All 11 retained Turtle examples parsed successfully using governed ROBOT 1.9.7.

## Final assessment

ROBOT can perform most generic ontology manipulation currently embedded in
Python, and it can likely construct almost all governed OWL mapping axioms after
a small Python normalization step.

ROBOT should not become the COMS governance engine.

The recommended division of responsibility is:

- **Python:** identity, policy, reconciliation, deterministic publication, and
  release governance;
- **ROBOT:** OWL parsing, construction, conversion, merging, filtering,
  reasoning, querying, verification, extraction, and semantic diffing.

This boundary preserves the strongest features of the current SSN-to-BFO
architecture while reducing duplicated ontology-processing code.
