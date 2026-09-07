# Reusable COMS Capability Inventory

## Purpose

This report identifies which capabilities in SSN-to-BFO should become reusable
across ontology-mapping projects and which responsibilities must remain in
project-specific configuration or adapters.

The boundary is informed by:

- the current SSN-to-BFO implementation;
- the SSN-to-BFO and PROV-to-BFO comparative audit;
- direct testing of PROV products with RDFLib and ROBOT/OWLAPI.

No production code should be extracted until this boundary is approved.

## Design objective

The reusable framework should support projects that differ in:

- source ontologies;
- target ontologies;
- mapping-expression types;
- product architectures;
- validation profiles;
- reasoners;
- publication metadata;
- package layouts;
- release policies.

The framework must not hard-code assumptions specific to:

- SSN or SOSA;
- PROV;
- BFO;
- CCO;
- RO;
- the current SSN five-product architecture;
- the current PROV three-product architecture.

## Recommended architectural boundary

A future implementation should expose these conceptual layers:

```text
COMS framework
├── configuration
├── governed mapping records
├── expression parsing and canonicalization
├── product selection and disposition
├── deterministic compilation and serialization
├── validation and cross-parser reconciliation
├── publication metadata
├── release packaging
└── project adapters
```

A possible Python package structure is:

```text
coms/
├── core/
│   ├── row_identity.py
│   ├── canonicalization.py
│   ├── records.py
│   └── expressions.py
├── config/
│   ├── model.py
│   ├── loader.py
│   └── validation.py
├── compilation/
│   ├── workbook.py
│   ├── compiler.py
│   ├── serializer.py
│   └── transaction.py
├── products/
│   ├── graph.py
│   ├── selection.py
│   ├── dispositions.py
│   └── reconciliation.py
├── validation/
│   ├── rdf.py
│   ├── owlapi.py
│   ├── roundtrip.py
│   ├── imports.py
│   ├── swrl.py
│   ├── reasoners.py
│   └── suite.py
├── publication/
│   ├── metadata.py
│   ├── release_context.py
│   ├── manifest.py
│   ├── package.py
│   ├── archive.py
│   └── rehearsal.py
└── cli/
    ├── compile.py
    ├── validate.py
    ├── package.py
    └── rehearse.py
```

This is a capability boundary, not a required initial file layout.

## Reusable core capabilities

### Persistent mapping identity

Current source:

- `tools/coms_row_identity.py`

Reusable responsibilities:

- persistent RowID validation;
- canonical expression construction;
- expression hashing;
- canonicalization-version declaration;
- mapping-type identification;
- deterministic identity across workbook edits.

Recommended treatment:

- copy with minimal initial change;
- preserve the current canonicalization version;
- separate RowID and expression functions only after equivalent tests exist.

### Governed mapping records

The framework should define a project-neutral mapping record containing:

- RowID;
- workbook location;
- source expression;
- mapping predicate or expression type;
- target expression;
- canonical expression;
- expression hash;
- referenced IRIs;
- assertion classification;
- explanatory metadata;
- product dispositions.

The record must distinguish:

1. an assertion-bearing mapping;
2. an explanatory annotation;
3. a deferred mapping;
4. an explicitly unmapped source term;
5. a project-specific transformation request.

### Workbook processing

Reusable responsibilities:

- load a configured workbook;
- select configured sheets;
- validate required columns;
- distinguish assertion-bearing and documentation-only columns;
- normalize lexical forms;
- reject duplicate RowIDs;
- reject duplicate canonical expressions where prohibited;
- retain precise row locations for diagnostics;
- emit structured governed records.

Project-specific responsibilities:

- workbook path;
- sheet names;
- column bindings;
- allowed mapping types;
- explicit-blank conventions;
- source and target vocabulary policies.

## Mapping-expression model

### Initial expression types

The reusable framework should support:

- `rdfs:subClassOf`;
- `owl:equivalentClass`;
- `rdfs:subPropertyOf`;
- `owl:equivalentProperty`;
- domain;
- range;
- OWL property chain;
- complex OWL class expression;
- explicit blank or explicitly unmapped record.

### Required extension types

The PROV comparison establishes requirements for:

- SWRL rules;
- SKOS mapping assertions;
- annotated OWL axioms;
- annotated SKOS assertions;
- project-specific transformation rules.

### Annotated-axiom handling

The framework must not assume that raw RDF triples and an OWLAPI structural
ontology expose identical axiom sets.

Direct testing found that:

- RDFLib rejected two original PROV products;
- RDFLib did not reconstruct main triples from repaired `owl:Axiom` structures;
- ROBOT/OWLAPI accepted all original PROV products;
- OWLAPI reconstructed all 85 annotated mappings;
- OWLAPI reserialization emitted the corresponding main triples.

The framework should therefore provide canonical annotated-axiom generation
that:

1. emits the main mapping triple;
2. emits the corresponding `owl:Axiom` annotation structure;
3. preserves complex blank-node targets;
4. round-trips through OWLAPI without changing the structural axiom set;
5. parses successfully with a strict RDF-native parser;
6. preserves labels, comments, and mapping rationale.

This is a portability requirement, not evidence that the current PROV mappings
are semantically absent in Protégé or OWLAPI.

### SWRL support

SWRL should be a first-class governed expression rather than unmanaged Turtle.

Each governed SWRL rule should contain:

- persistent rule identity;
- canonical body;
- canonical head;
- declared variables;
- atom types;
- source predicates and classes;
- target predicates and classes;
- explanatory metadata;
- product disposition;
- reasoner-compatibility declaration;
- deterministic serialization.

Validation should include:

- required namespace declarations;
- declared variables;
- valid RDF lists;
- permitted atom types;
- complete body and head;
- deterministic variable naming;
- canonical rule hashing;
- OWLAPI round-trip preservation.

## Project configuration

Recommended top-level configuration objects:

```text
ProjectConfig
WorkbookProfile
VocabularyProfile
ExpressionProfile
ProductGraph
ValidationProfile
PublicationProfile
ReleaseLayout
```

### ProjectConfig

Recommended fields:

- project key;
- project title;
- repository root;
- authoritative mapping source;
- primary output;
- generated warning;
- configuration schema version.

### WorkbookProfile

Recommended fields:

- workbook path;
- sheet selectors;
- header bindings;
- required columns;
- optional columns;
- documentation-only columns;
- RowID column;
- allowed expression types;
- explicit-blank representation.

### VocabularyProfile

The framework should permit any number of source and target vocabularies.

Recommended fields:

- vocabulary key;
- role: source, target, structural, or annotation;
- namespace IRIs;
- prefixes;
- ontology IRI;
- version IRI;
- validation dependency;
- catalog mapping;
- permitted products;
- prohibited products.

BFO, CCO, and RO must be configurations, not built-in universal categories.

### ExpressionProfile

Recommended fields:

- allowed OWL predicates;
- allowed SKOS predicates;
- SWRL enabled or disabled;
- supported complex-expression grammar;
- annotation policies;
- transformation registry;
- canonicalization version.

### ProductGraph

A product definition should include:

- product key;
- output path;
- stable ontology IRI;
- release IRI pattern;
- product type;
- imports;
- product dependencies;
- inclusion policy;
- permitted vocabularies;
- prohibited vocabularies;
- serialization profile;
- validation profile;
- package role.

The product graph must support:

- layered products, as in SSN-to-BFO;
- parallel target products, as in PROV-to-BFO;
- integrated products;
- editor ontologies;
- consumer examples;
- validation-only products.

### ValidationProfile

Recommended fields:

- RDF parser checks;
- OWLAPI parser checks;
- structural-axiom round-trip checks;
- annotation preservation checks;
- exact product list;
- import-policy validation;
- catalog validation;
- allowed mutable imports;
- reasoners;
- expected consistency;
- permitted unsatisfiable classes;
- positive entailment tests;
- negative entailment tests;
- SWRL validation;
- fixed-count policies;
- project-specific validation commands.

### PublicationProfile

Recommended fields:

- project title;
- stable ontology IRIs;
- version-IRI policy;
- release identifier format;
- repository IRI;
- license IRI;
- creator and contributor metadata;
- development status;
- product labels;
- product descriptions.

### ReleaseLayout

Recommended fields:

- archive prefix;
- package members;
- source artifacts;
- evidence artifacts;
- product artifacts;
- manifest path;
- checksum path;
- release-notes path;
- required release-note sections.

## Product-disposition framework

Current sources:

- `tools/product_dispositions.py`;
- parts of `tools/modular_products.py`.

Reusable responsibilities:

- assign governed records to products;
- record whether an expression is emitted;
- record whether support is supplied through import;
- record transitive provision;
- record deferral;
- record non-applicability;
- reconcile source records with generated products;
- produce deterministic disposition evidence.

Recommended generic model:

```text
ExpressionDisposition
├── record_id
├── product_key
├── status
├── reason_code
├── transformation_rule
├── emitted_expression
└── evidence
```

Project-specific configuration should define:

- target categories;
- product keys;
- reason codes;
- transformation rules;
- product-selection policies.

The following current assumptions must not become framework constants:

- `bfo_bearing`;
- `cco_bearing`;
- `mixed_bfo_cco`;
- SSN/SOSA namespaces;
- fixed BFO and CCO namespaces;
- the current five-product disposition matrix.

## Compilation and serialization

Current sources:

- `tools/generate_mapping_from_coms.py`;
- `tools/modular_products.py`;
- `tools/check_coms_mapping.py`.

Reusable responsibilities:

- compile governed records into RDF and OWL products;
- select configured expressions for each product;
- serialize deterministically;
- calculate hashes;
- write validation evidence;
- replace maintained outputs transactionally;
- restore prior outputs on failure;
- validate output freshness.

Project-specific responsibilities:

- source and target namespaces;
- product-selection policies;
- import graphs;
- ontology IRIs;
- prefix order;
- section headings;
- expected counts;
- project-specific transformations.

Recommended extraction sequence:

1. retain the current generator as the SSN reference implementation;
2. extract pure RowID and expression functions;
3. extract workbook parsing;
4. extract generic product assembly;
5. replace constants with loaded configuration;
6. move SSN product policy into an adapter;
7. prove byte-identical SSN outputs;
8. migrate a second project only after equivalence is established.

## Validation framework

### Mandatory generic checks

The reusable framework should provide:

- parsing with an RDF-native parser;
- parsing with OWLAPI;
- structural-axiom comparison across parsers;
- OWLAPI reserialization and round-trip validation;
- exact-byte freshness validation;
- RowID uniqueness;
- canonical-expression uniqueness;
- expression-hash validation;
- product-disposition reconciliation;
- import graph validation;
- catalog validation;
- mutable-import policy validation;
- deterministic serialization validation;
- publication metadata validation;
- release-package reconciliation;
- checksum validation.

### Reasoner validation

Reasoner execution should be configured per project and product.

The framework should support:

- one or more reasoners;
- configured import closures;
- expected consistency;
- permitted or prohibited unsatisfiable classes;
- positive entailment tests;
- negative entailment tests;
- instance-data tests;
- fixed closure counts where justified.

HermiT, ELK, or any other reasoner should be configuration choices, not
hard-coded framework assumptions.

Fixed triple counts should be optional validation baselines rather than
framework constants.

## Publication and release framework

Current reusable candidates:

- `tools/publication_metadata.py`;
- `tools/check_publication_metadata.py`;
- `tools/release_context.py`;
- `tools/release_manifest.py`;
- `tools/build_release.py`;
- `tools/check_release.py`;
- `tools/release_archive.py`;
- `tools/rehearse_release.py`.

Reusable mechanisms:

- release-context validation;
- publication-metadata validation;
- manifest generation;
- dependency inventory;
- exact file hashes;
- deterministic package construction;
- deterministic USTAR archives;
- clean-clone release rehearsal;
- network-isolation guards;
- archive-member validation;
- transactional package replacement.

Project-specific content to configure:

- product order;
- dependency keys;
- package paths;
- archive prefix;
- release-note sections;
- ontology IRIs;
- expected closure counts;
- development-output paths;
- project-specific environment-variable names.

## Current-file classification

| Current file | Classification | Initial treatment |
| --- | --- | --- |
| `tools/coms_row_identity.py` | Reusable core | Copy with minimal change |
| `tools/release_context.py` | Reusable core | Copy unchanged initially |
| `tools/check_publication_metadata.py` | Reusable mechanism | Configure paths |
| `tools/publication_metadata.py` | Reusable after configuration | Remove fixed products and imports |
| `tools/product_dispositions.py` | Framework plus SSN policy | Split mechanism from policy |
| `tools/release_manifest.py` | Framework plus release schema | Replace fixed product and dependency lists |
| `tools/release_archive.py` | Reusable after configuration | Configure prefix and members |
| `tools/rehearse_release.py` | Reusable after configuration | Generalize paths and environment names |
| `tools/build_release.py` | Framework plus SSN layout | Split package engine from project layout |
| `tools/check_release.py` | Framework plus SSN layout | Configure package expectations |
| `tools/generate_mapping_from_coms.py` | Compiler plus extensive SSN policy | Extract incrementally |
| `tools/check_coms_mapping.py` | Transaction engine plus SSN checks | Extract transaction mechanism |
| `tools/modular_products.py` | Product engine plus extensive SSN policy | Redesign around declarative products |
| `tools/run_validation_suite.py` | Generic runner plus SSN suite | Configure command registry |
| `tools/watch_coms_mapping.py` | Generic watcher plus SSN paths | Configure inputs and outputs |
| `tools/workflow_check.py` | SSN workflow policy | Keep in SSN adapter initially |
| `tools/compare_mappings.py` | Potential reusable audit | Review separately |
| SSN reasoner scripts | SSN integration validation | Keep outside framework |
| SSN product tests | SSN integration validation | Keep outside framework |
| SSN instance fixtures | SSN project fixtures | Keep outside framework |

## SSN-to-BFO adapter

The SSN adapter should retain:

- SSN/SOSA namespaces;
- current source import graph;
- BFO and CCO target classifications;
- alignment-core policy;
- strict-BFO policy;
- BFO-projection policy;
- CCO-extension policy;
- integrated-product policy;
- current product IRIs and paths;
- SSN-specific closure counts;
- SSN-specific reasoner tests;
- SSN instance fixtures;
- SSN-specific deferred-mapping rules;
- current publication metadata;
- current release layout.

The first extracted framework must reproduce current SSN products byte-for-byte.

## PROV-to-BFO integration case

PROV should become the second integration case after SSN behavior is preserved.

A PROV adapter would require:

- PROV source namespaces;
- BFO, CCO, and RO targets;
- parallel product definitions;
- annotated OWL axioms;
- annotated SKOS assertions;
- SWRL rules;
- consumer examples;
- editor ontology support;
- import extraction;
- PROV-specific reasoner tests.

Migration should preserve the intended 85 OWLAPI-reconstructed mappings and 14
SWRL rules while emitting a canonical serialization accepted consistently by
OWLAPI and RDF-native parsers.

## Test architecture

### Framework unit tests

Use synthetic namespaces and synthetic workbook fixtures to test:

- RowID behavior;
- canonicalization;
- workbook parsing;
- every expression type;
- annotated-axiom generation;
- SWRL generation;
- product assignment;
- deterministic serialization;
- cross-parser round trips;
- product reconciliation;
- manifest generation;
- archive construction;
- transaction rollback.

Framework unit tests must not depend on SSN, SOSA, PROV, BFO, CCO, or RO.

### SSN integration tests

Continue to test:

- byte identity of existing products;
- current governed counts;
- current disposition evidence;
- reasoner safety;
- instance entailments;
- deterministic release packages.

### PROV integration tests

Eventually test:

- preservation of the 85 reconstructed mappings;
- preservation of the 14 SWRL rules;
- BFO, CCO, and RO products;
- annotation preservation;
- consumer examples;
- pinned imports;
- strict RDF parsing;
- OWLAPI parsing;
- OWLAPI round-trip equivalence.

## Repository strategy

Recommended initial strategy:

1. create a separate reusable repository;
2. copy mechanisms rather than immediately sharing runtime dependencies;
3. retain SSN-to-BFO as the reference implementation;
4. develop synthetic framework fixtures;
5. reproduce SSN outputs exactly;
6. migrate PROV as the second adapter;
7. only then decide whether projects should consume a shared package directly.

This avoids destabilizing the published SSN project during extraction.

## Candidate repository names

Reasonable candidates include:

- `BFO-Mappings/COMS`;
- `BFO-Mappings/COMS-Core`;
- `BFO-Mappings/COMS-Framework`.

`COMS` is the clearest name if the repository will be the canonical
implementation rather than only an internal library.

## Extraction phases

### Phase 1: inventory and fixtures

- approve this capability boundary;
- create synthetic workbook fixtures;
- capture current SSN output hashes;
- capture current validation behavior;
- define the configuration schema.

### Phase 2: low-risk core extraction

- copy RowID and canonicalization code;
- copy release-context code;
- create generic configuration loading;
- create framework unit tests.

### Phase 3: publication and release extraction

- generalize publication metadata;
- generalize manifest generation;
- generalize package and archive layout;
- generalize release rehearsal.

### Phase 4: compiler extraction

- extract workbook parsing;
- extract the mapping-expression model;
- extract deterministic serialization;
- extract the transaction engine;
- preserve SSN output byte identity.

### Phase 5: product architecture extraction

- introduce declarative product graphs;
- move SSN product policy into an adapter;
- move vocabulary classification into configuration;
- preserve product-disposition evidence.

### Phase 6: cross-parser support

- implement annotated-axiom canonicalization;
- implement RDF and OWLAPI validation;
- implement structural-axiom round-trip comparison;
- implement governed SWRL expressions.

### Phase 7: PROV integration

- preserve the intended PROV mapping set;
- configure parallel BFO, CCO, and RO products;
- emit portable annotated axioms;
- add consumer-example validation;
- establish deterministic PROV releases.

## Acceptance criteria

The reusable framework should not be considered complete until:

1. framework tests use no project-specific ontology;
2. SSN-to-BFO output bytes remain unchanged;
3. all SSN validation and release checks pass;
4. product architecture is declarative;
5. source and target vocabularies are configurable;
6. SWRL is a governed expression type;
7. annotated axioms round-trip between RDF and OWLAPI;
8. canonical products parse in both RDFLib and OWLAPI;
9. a PROV adapter preserves all intended mappings and rules;
10. both projects rehearse deterministic releases from clean clones;
11. no project-specific constants remain in framework modules.
