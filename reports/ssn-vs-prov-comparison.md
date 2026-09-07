# SSN-to-BFO and PROV-to-BFO Comparative Audit

## Scope

This report compares the engineering, governance, release, validation, and
mapping-expression approaches used in:

- `BFO-Mappings/SSN-to-BFO`
- `BFO-Mappings/PROV-to-BFO`

The audit was conducted against:

- SSN-to-BFO commit
  `2106dbfaa89af9db3bd9a362315ed37df1f65ee0`
- PROV-to-BFO commit
  `c60847a4b838d25972d899731c0f6bb83716181d`
- PROV-to-BFO release tag `v2025-01-19`

The audit was read-only with respect to PROV-to-BFO. Temporary syntax repairs
were applied only in memory where necessary to inspect the intended RDF graph.

## Executive assessment

SSN-to-BFO is substantially stronger in artifact validity, mapping governance,
traceability, automated validation, deterministic generation, and release
reproducibility.

PROV-to-BFO contains useful design ideas that should inform a reusable COMS
framework, particularly:

- first-class SWRL mappings;
- a separate RO mapping product;
- explicit consumer example artifacts;
- conceptual diagrams;
- documentation of known source and target ontology inconsistencies.

However, the PROV-to-BFO products depend on OWLAPI-specific parsing and
reconstruction behavior that is not reproduced by all RDF toolchains.
Protégé, ROBOT, and OWLAPI reconstruct the intended annotated axioms, while
RDFLib rejects two original files and does not independently reconstruct the
main axiom triples. This is principally an interoperability and portability
concern rather than an absence of operational mappings in the project
toolchain.

## Repository baselines

| Metric | SSN-to-BFO | PROV-to-BFO |
| --- | ---: | ---: |
| Commits | 411 | 194 |
| Tracked files | 233 | 70 |
| Python tools | 21 | 0 |
| Python tests | 15 | 0 |
| Turtle files | 30 | 31 |
| Markdown files | 129 | 4 |
| Workbooks | 4 | 0 |
| GitHub Actions workflows | 1 | 1 |
| Latest audited release | `v2026-07-18` | `v2025-01-19` |

Repository size alone is not a quality measure. It does show that SSN-to-BFO
contains a substantially larger governance, validation, and release-engineering
surface.

## Artifact validity

### SSN-to-BFO

All five maintained ontology products parsed successfully with RDFLib's Turtle
parser:

1. integrated mapping;
2. alignment core;
3. strict BFO mapping;
4. BFO projection;
5. CCO extension.

### PROV-to-BFO

Parser behavior differs by toolchain.

RDFLib rejected two original products:

- `prov-bfo-directmappings.ttl`;
- `prov-cco-directmappings.ttl`.

The constructs associated with the RDFLib failures were:

- use of `:x` and `:y` without an explicit default-prefix declaration;
- use of `xsd:boolean` without an explicit `xsd:` declaration;
- multiline comments represented using ordinary quoted literals.

However, ROBOT 1.9.7 and its OWLAPI parser accepted all three original,
unmodified PROV products:

- `prov-bfo-directmappings.ttl`;
- `prov-cco-directmappings.ttl`;
- `prov-ro-directmappings.ttl`.

ROBOT then reserialized all three products as Turtle that RDFLib could parse.

The appropriate conclusion is therefore not that the PROV mappings are absent
or unusable. The products are usable in Protégé, ROBOT, and OWLAPI, but their
serialization is not portable across all RDF parsers. A future governed build
should emit a canonical representation accepted consistently by both OWLAPI
and strict RDF-native consumers.
## Mapping assertion audit

### SSN-to-BFO

The SSN products contain explicit mapping triples in their serialized RDF:

| Product | Asserted governed mapping axioms |
| --- | ---: |
| Alignment core | 29 |
| Strict BFO mapping | 19 |
| CCO extension | 57 |
| Integrated governed total | 105 |

The integrated product contains class mappings, relation mappings, domains,
ranges, and property chains that are directly visible in the RDF graph.

### PROV-to-BFO

The original PROV serializations represent intended mappings primarily through
`owl:Axiom` structures. In an RDFLib graph produced after applying only the
minimal syntax repairs required by RDFLib, the corresponding main mapping
triples were not present:

| Product | `owl:Axiom` records | Main triples visible in repaired RDFLib graph |
| --- | ---: | ---: |
| BFO | 27 | 0 |
| CCO | 33 | 0 |
| RO | 25 | 0 |
| **Total** | **85** | **0** |

This did not mean that the axioms were absent from the OWLAPI structural
ontology.

ROBOT 1.9.7 accepted the original files and reconstructed every annotated
axiom:

| Product | Annotated axioms | OWLAPI-reconstructed axioms | SWRL rules |
| --- | ---: | ---: | ---: |
| BFO | 27 | 27 | 8 |
| CCO | 33 | 33 | 6 |
| RO | 25 | 25 | 0 |
| **Total** | **85** | **85** | **14** |

After ROBOT/OWLAPI reserialization, the corresponding main mapping triples
were present in the resulting Turtle.

The intended PROV OWL, SKOS, and RO mappings are therefore operational in the
Protégé/OWLAPI toolchain. The material issue is that the raw RDF graph and the
OWLAPI structural ontology do not present the same mapping assertions to every
consumer.

A reusable COMS framework should detect and eliminate this ambiguity by
producing a canonical annotated-axiom serialization that:

1. is accepted by both OWLAPI and strict RDF parsers;
2. includes the corresponding main mapping triples;
3. round-trips without changing the structural OWL axioms;
4. preserves axiom annotations and explanatory metadata.

## Mapping-expression comparison

### SSN-to-BFO

The current governed mapping language supports:

- `rdfs:subClassOf`;
- `owl:equivalentClass`;
- `rdfs:subPropertyOf`;
- domains;
- ranges;
- OWL property chains;
- complex class expressions;
- explicit blank or deferred mappings.

SWRL support is planned but is not currently part of the generated product
language.

### PROV-to-BFO

OWLAPI reconstruction identified:

- 27 annotated BFO-oriented OWL mapping axioms;
- 33 annotated CCO-oriented OWL or SKOS mapping axioms;
- 25 annotated RO-oriented mapping axioms;
- 8 BFO-oriented SWRL rules;
- 6 CCO-oriented SWRL rules.

The SWRL rules demonstrate legitimate requirements for conditional mappings.
Examples include interpreting `prov:atLocation` differently depending on
whether its subject is an activity, instantaneous event, entity, or agent.

PROV-to-BFO is therefore stronger than SSN-to-BFO in one important expression
category: it already uses SWRL to represent mappings that would be misleading
as unconditional property subsumptions.

Generalized COMS should support SWRL as a first-class governed expression type
rather than treating rules as unmanaged Turtle text. It should also support
annotated OWL and SKOS mappings while ensuring that their canonical RDF
serialization is portable across toolchains.
## Product architecture

### SSN-to-BFO

SSN-to-BFO uses a layered architecture:

1. target-neutral alignment core;
2. strict BFO mapping;
3. BFO projection;
4. CCO extension;
5. integrated consumer product.

This architecture distinguishes target-neutral source alignment from
target-specific mappings and makes product disposition explicit.

### PROV-to-BFO

PROV-to-BFO uses parallel target products:

- BFO direct mappings;
- CCO direct mappings;
- RO direct mappings.

An editor ontology imports the three products together with PROV modules,
examples, BFO, CCO, and extracted RO content.

Neither architecture should be hard-coded into reusable COMS. The reusable
framework must permit arbitrary declarative product graphs, including both
layered and parallel products.

## Continuous integration

### SSN-to-BFO

The current SSN workflow runs the canonical validation suite through
`make check`. Its current architecture includes:

- exact maintained-product parsing;
- generation freshness checks;
- governed-axiom reconciliation;
- product-disposition reconciliation;
- publication metadata validation;
- import and catalog validation;
- reasoner checks;
- focused Python tests;
- deterministic release-package validation.

### PROV-to-BFO

The PROV workflow runs only on pull requests targeting `main` and invokes:

- `make -C src reason-edit`;
- `make -C src test-edit`.

Both targets operate on the editor ontology. Local catalogs redirect its
GitHub `main` imports to the mapping products in the checkout.

ROBOT and OWLAPI accept the original mapping files and reconstruct their
annotated axioms. The successful CI result is therefore consistent with the
behavior of the configured toolchain and does not show that the mappings were
ignored.

Remaining CI and release-governance weaknesses include:

- release PR #39 had no reported checks;
- no push or tag-triggered release gate was observed;
- release products are not independently tested with a second RDF parser;
- `config.FAIL_ON_TEST_FAILURES := false`;
- `config.REPORT_FAIL_ON := none`;
- release targets are not invoked by CI;
- the workflow uploads `build/artifacts/`, while the Makefile writes under
  `src/build/artifacts/`;
- ROBOT 1.9.5 is downloaded without a governed checksum;
- the cache key is not derived from a dependency declaration.

A July 2025 workflow failure was caused by deprecated
`actions/upload-artifact@v3`, not by an ontology defect. After upgrading the
action, the OWLAPI-based ontology checks succeeded, although no artifacts were
uploaded because of the path mismatch.

## Import and publication architecture

SSN-to-BFO separates stable ontology IRIs, release identity, pinned validation
dependencies, local catalogs, package manifests, and release archive members.

PROV-to-BFO uses GitHub raw `main` URLs as ontology IRIs and as imports in its
editor and example ontologies. Some target-product imports are pinned to
`v2025-01-19`, but the overall editor assembly remains dependent on mutable
branch content.

This makes historical reconstruction and reproducible validation more
difficult.

## Traceability and governance

### SSN-to-BFO

The COMS workbook is the authoritative editable mapping source. Mapping rows
receive persistent RowIDs and canonical expression hashes. Generated products,
product dispositions, reports, manifests, and release artifacts can be
reconciled to governed source records.

### PROV-to-BFO

Mappings are manually represented in Turtle. No authoritative tabular mapping
source, persistent mapping identifier scheme, canonical expression hash, or
generated-product reconciliation mechanism was found.

The `owl:Axiom` structures contain useful labels and explanatory comments.
OWLAPI reconstructs all 85 intended mapping axioms from those structures.
However, no automated cross-parser check verifies that the serialized RDF is
portable or that OWLAPI reserialization preserves the intended axiom set.

## PROV-to-BFO strengths worth retaining

The following PROV practices should inform future work:

1. SWRL rules for conditional mappings that cannot be represented faithfully
   as unconditional OWL subproperty assertions.
2. An independently consumable RO product.
3. A concrete consumer example ontology.
4. Diagrams explaining conceptual mappings.
5. A dedicated inconsistencies document.
6. Rich mapping comments explaining modeling rationale.
7. SPARQL queries for candidate mappings, unmapped terms, reports, and
   deductive comparison.
8. Import extraction to reduce unnecessary reasoner closure size.

These practices should be migrated into governed and reproducible mechanisms
rather than copied together with the current portability and release-engineering
weaknesses.

## SSN-to-BFO strengths

SSN-to-BFO is stronger in:

1. strict artifact validity;
2. assertion-bearing mappings;
3. authoritative mapping-source governance;
4. row-level identity and traceability;
5. explicit handling of deferred and unmapped rows;
6. product-disposition accounting;
7. target-neutral and target-specific product separation;
8. transactional generation;
9. deterministic serialization;
10. focused reasoner and instance tests;
11. publication metadata;
12. release manifests and checksums;
13. isolated release rehearsal;
14. release-byte validation;
15. branch and tag governance.

## Source-ontology-driven differences

Not every difference represents a project weakness.

PROV includes several relations whose correct BFO or CCO interpretation depends
on the types of their arguments. Conditional SWRL rules may therefore be a
natural fit for parts of the PROV alignment.

SSN/SOSA contains a broad sensor, observation, sampling, actuation, deployment,
system, and system-property architecture. Its product split reflects the
different amounts of content supportable by BFO alone and by the broader CCO
stack.

These ontology-driven differences should remain in project adapters and
project-specific mapping policies.

## Reusable COMS implications

Generalized COMS should provide the following mandatory capabilities:

1. validation of every maintained and distributed ontology product with both
   an OWLAPI parser and a strict RDF-native parser;
2. validation of the exact bytes packaged for release;
3. cross-parser reconciliation of structural OWL axioms and serialized RDF
   triples;
4. canonical reserialization of annotated axioms with corresponding main
   triples;
5. separate counts for OWL axioms, SKOS mappings, SWRL rules, and explanatory
   annotation records;
6. SWRL as a governed mapping-expression type;
7. explicit SWRL variable declarations and prefix validation;
8. arbitrary source and target vocabulary profiles;
9. arbitrary layered or parallel product definitions;
10. arbitrary target vocabularies, including BFO, CCO, RO, and future targets;
11. configurable editor and consumer-example artifacts;
12. configurable import and catalog policies;
13. prohibition or explicit authorization of mutable branch imports;
14. project-specific reasoner and competency-test profiles;
15. deterministic generation and archive construction;
16. release manifests, checksums, and clean-clone rehearsal;
17. failure of CI and release creation when advertised products are invalid;
18. synthetic framework fixtures independent of SSN and PROV;
19. external integration fixtures for both SSN-to-BFO and PROV-to-BFO.


## Overall conclusion

SSN-to-BFO currently provides the stronger engineering and governance model.

PROV-to-BFO provides useful semantic and workflow ideas, especially its SWRL
rules, RO mappings, examples, and explanatory materials. Those ideas should be
incorporated into generalized COMS.

The current PROV release artifacts should not be used as the implementation
basis for the reusable framework. They should instead become a second
integration case used to prove that the extracted framework supports:

- conditional SWRL mappings;
- multiple target ontologies;
- parallel product architectures;
- annotated mapping rationale;
- and consumer examples.

The reusable framework should first preserve SSN-to-BFO behavior exactly, then
use PROV-to-BFO migration as the test that the framework is genuinely general.
