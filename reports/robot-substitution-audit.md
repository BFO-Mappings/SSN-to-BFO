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

### Property-chain generation pilot

The five governed property-chain rows are now covered by a separate read-only
pilot in `tools/robot_property_chain_generation_pilot.py`.

The pilot:

1. selects the five canonical `property_chain` rows produced from the unchanged
   COMS workbook;
2. emits deterministic OWL Functional Syntax using the already-resolved member
   and super-property IRIs;
3. invokes `robot convert --strict` to parse and serialize the temporary
   ontology;
4. canonicalizes ROBOT's RDF property-chain structures through the existing
   graph-to-axiom comparison machinery;
5. compares the result with the authoritative COMS axiom identities.

Results:

| Measure | Result |
| --- | ---: |
| Governed COMS rows | 105 |
| Attempted property-chain rows | 5 |
| Expected canonical axioms | 5 |
| ROBOT canonical axioms | 5 |
| Missing axioms | 0 |
| Extra axioms | 0 |
| Mismatched axioms | 0 |
| Declared object properties | 17 |
| Pilot summary | PASS |

The generated Functional Syntax is byte-deterministic across separate runs and
different Python hash seeds. ROBOT outputs are graph-isomorphic across runs.

Combined with the normalized Template pilot, ROBOT now independently
reconstructs all 105 governed COMS axioms exactly:

- 100 non-chain axioms through normalized ROBOT Template input;
- 5 property-chain axioms through normalized OWL Functional Syntax;
- 0 overlapping backend axioms;
- 0 missing, extra, or mismatched canonical axioms.

The permanent combined gate is implemented by:

- `tools/robot_reconstruction_validation.py`, which provides shared workbook
  loading, canonical extraction, ROBOT resolution, and comparison helpers;
- `tools/validate_robot_reconstruction.py`, which runs both reconstruction
  backends and requires exact 105-of-105 canonical equality;
- `tests/test_robot_reconstruction_validation.py`, which locks the combined
  result, deterministic normalized inputs, and non-modification of maintained
  ontology products;
- `tools/run_validation_suite.py`, which runs the focused tests and complete
  reconstruction check as authoritative validation steps.

The current Python generator remains authoritative, and all five maintained
ontology products remain unchanged.

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

Direct substitution of the current RDFLib closure builders with `robot merge`
was tested and rejected for the governed SSN/SOSA source and validation
closures. The pilot evaluated ROBOT 1.9.7 against the exact union behavior of
both `build_fixed_source_closure` and `build_fixed_validation_closure`.

The strict merge failed because OWLAPI reported 32 RDF triples that it could
not parse, including ordinary domain and range statements and anonymous
`owl:unionOf` structures.

The non-strict direct merge returned success but reported one unparsed anonymous
`owl:unionOf` triple and expanded imported vocabulary. Against the Python
alignment-core closure, it produced:

- 1,421 raw triples versus 1,214;
- 1,390 logical triples versus 1,164;
- 27 Python-only and 253 ROBOT-only logical triples;
- 107 supported canonical axioms versus 72;
- one missing and 36 extra canonical axioms.

The missing canonical axiom was:

`ObjectPropertyDomain(<http://www.w3.org/ns/ssn/systems/inCondition> ObjectUnionOf(<http://www.w3.org/ns/ssn/systems/OperatingRange> <http://www.w3.org/ns/ssn/systems/SurvivalRange> <http://www.w3.org/ns/ssn/systems/SystemCapability>))`

Using `--collapse-import-closure false` produced 1,197 triples, zero
`owl:imports` triples, one ontology declaration, and 145 triples involving SKOS
IRIs. It still reported the unparsed union triple and did not reproduce the
Python closure.

A further sanitized-input test removed all `owl:imports` statements from
temporary copies before ROBOT loaded the five inputs. ROBOT still reported the
unparsed union triple, 17 OWLAPI entity-recognition errors, and an unparsed
`sosa:isSampleOf rdf:type owl:FunctionalProperty` statement. The result was
also non-equivalent:

- 1,181 raw triples versus 1,214;
- 1,150 logical triples versus 1,164;
- 1,068 shared, 96 Python-only, and 82 ROBOT-only logical triples;
- 88 supported canonical axioms versus 72;
- one missing and 17 extra canonical axioms;
- 145 triples involving SKOS IRIs.

The same `ssn-system:inCondition` union-domain axiom was missing. The 17 extra
canonical axioms were synthetic subclass axioms targeting
`http://org.semanticweb.owlapi/error#Error1` through
`http://org.semanticweb.owlapi/error#Error17`.

The difference is therefore semantic, not merely serialization-level.

The current RDFLib closure builders must remain authoritative for:

- exact offline RDF graph union;
- import-edge removal without import expansion;
- preservation of RDF structures not accepted cleanly by OWLAPI;
- project-specific cleanup triples;
- governed closure triple-count baselines.

ROBOT remains appropriate for reasoning over the Python-built closure, but not
for constructing the current fixed source or validation closures.

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
| Full source closure | Python builds the exact RDF closure and applies cleanup; ROBOT reasons over the resulting closure |
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
| Current SSN/SOSA closure merge and import-edge removal | 0–10% |
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

## Implementation status and next steps

### Phase 1: report-only validation — complete

- recorded the 70-of-100 unchanged Template baseline;
- implemented normalized ROBOT Template reconstruction;
- proved exact canonical equality for all 100 non-chain axioms;
- preserved the authoritative Python generation path.

### Phase 2: consolidate reasoning — complete

- introduced one configured ROBOT/HermiT execution adapter;
- migrated the five generator reasoning wrappers;
- preserved public wrapper signatures, report semantics, and temporary
  filenames;
- passed direct old-versus-new equivalence and the full validation suite.

### Phase 3: independent ROBOT reconstruction — complete

- implemented normalized Template reconstruction for 100 non-chain axioms;
- implemented normalized Functional Syntax reconstruction for 5 property-chain
  axioms;
- introduced a permanent combined 105-of-105 validation gate;
- required zero overlap, missing, extra, or mismatched canonical axioms;
- kept the current Python generator authoritative;
- left all five maintained ontology products unchanged.

### Phase 4: production-generation evaluation — intentionally deferred

ROBOT will remain an independent validation oracle unless a future controlled
experiment proves that production use would:

1. remove a meaningful amount of custom Python;
2. preserve COMS RowID-level diagnostics;
3. preserve atomic failure and rollback behavior;
4. preserve deterministic maintained and release artifact bytes;
5. simplify the total architecture rather than add another production-critical
   intermediate layer.

### Phase 5: standardize other ROBOT operations — future work

Closure merging has been evaluated and rejected for the current governed
SSN/SOSA fixed-closure paths because ROBOT does not preserve the exact RDF or
canonical axiom set.

Potential candidates remain:

- query and verify;
- semantic diff;
- import extraction;
- retained example validation.

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

- **Python:** identity, policy, reconciliation, exact RDF closure construction,
  deterministic publication, and release governance;
- **ROBOT:** OWL parsing, construction, conversion, reasoning, querying,
  verification, extraction, semantic diffing, and filtering where the input is
  OWLAPI-compatible; merging is not approved for the current governed closure
  paths.

This boundary preserves the strongest features of the current SSN-to-BFO
architecture while reducing duplicated ontology-processing code.
