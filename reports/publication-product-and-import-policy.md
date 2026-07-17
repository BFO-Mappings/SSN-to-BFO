# SSN-to-BFO Publication Product and Import Policy

## 1. Executive Recommendation

Adopt four generated modular products alongside, not in place of, the independently generated integrated root. `mappings/SSN2BFO-COMS.xlsx` remains the sole editable mapping authority. Product identity, import relationships, mapping strength, release versioning, current-projection retirement, and the inactive `sosa-next` lifecycle are approved by this policy rather than left as implementation choices.

| Product | File | Stable ontology IRI | Authority and lifecycle status |
|---|---|---|---|
| Integrated authoritative product | `SSN2BFO.ttl` | `http://www.sks.ai/SSN2BFO/` | **Maintained authoritative development artifact.** It remains the complete standalone integrated publication and must not become an import wrapper. |
| Alignment core | `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` | `http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core` | **Maintained authoritative development artifact.** It contains the 29 target-neutral governed axioms. |
| Strict BFO mapping | `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` | `http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping` | **Maintained authoritative development artifact.** It contains the 19 current BFO-bearing axioms unchanged. |
| BFO projection | `releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl` | `http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-projection` | **Maintained authoritative development artifact.** It is the designated product for approved weaker but sound BFO consequences, imports the strict BFO mapping, and currently asserts no direct projection axiom. |
| CCO extension | `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` | `http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension` | **Maintained authoritative development artifact.** It adds the 25 CCO-bearing and 32 mixed BFO/CCO axioms and imports the strict BFO mapping. |
| Current simple BFO projection | `src/current-ssn-sosa/build/artifacts/current-ssn-sosa-bfo-only-generated.ttl` | None | **Review-only; publication workflow to be retired.** It is not the approved BFO projection product. |
| RO module | No approved path | None | **Deferred.** It remains outside the approved product set pending a focused applicability review. |
| `sosa-next` modules | Existing `releases/sosa-next/` placeholders | None approved | **Inactive lifecycle scaffolding.** They remain outside current generation, CI, release, and completeness accounting. |
| Future SWRL/rule module | No approved path | None | **Deferred.** It requires a separately governed rule-policy decision. |

The approved project-module import graph is acyclic. Arrows point from an importing product to the project module it imports:

```text
alignment core
      ^
      |
strict BFO mapping
   ^             ^
   |             |
CCO extension  BFO projection
```

The alignment core imports nothing. The strict BFO mapping imports only the alignment core. The CCO extension and BFO projection each import only the strict BFO mapping; they do not import one another.

`SSN2BFO.ttl` is generated independently from the same COMS authority. It retains every approved COMS mapping/typing axiom in its own graph, retains its approved dependency-bearing source and CCO imports, and imports none of the modular products.

## 2. Baseline and Evidence

### Repository baselines

| Repository | Path | Branch | Exact SHA | Role |
|---|---|---|---|---|
| SSN-to-BFO | `/Users/alecsculley/Documents/GitHub/SSN-to-BFO` | `review/define-publication-products` | `398ebd3533a24755466b26931836a3a9399c42c5` | Controlling source for this recommendation. |
| PROV-to-BFO | `/Users/alecsculley/Documents/GitHub/PROV-to-BFO` | `main` | `c60847a4b838d25972d899731c0f6bb83716181d` | Comparative design evidence only. |

The SSN worktree was clean before the original report was created. The PROV tracked worktree was unchanged; its pre-existing untracked `src/imports/PROV/catalog-v001.xml` is local comparison state and is not credited as out-of-the-box reproducibility.

### Commands and analyses

The review used only local checked-out content. Principal checks were:

```text
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all

RDFLib strict Turtle parse and graph inspection of:
  SSN2BFO.ttl
  the current review-only BFO projection
  PROV-to-BFO/prov-{bfo,cco,ro}-directmappings.ttl

RDF traversal of every source-subject mapping/typing axiom in SSN2BFO.ttl
inspection of reports/coms-generation-validation.md
inspection of mappings/SSN2BFO-COMS.xlsx through the maintained generation report
inspection of src/current-ssn-sosa/Makefile and its projection queries
inspection and row count of the projection exclusions CSV
inspection of all four releases/ placeholders
```

No mappings, reasoner inputs, products, maintained COMS reports, or build artifacts were regenerated. This policy establishes transformation categories and proof obligations, but it does not approve a transformation for any individual COMS row.

### Current integrated-product evidence

`SSN2BFO.ttl` strictly parses as 1,117 RDF triples. It contains one ontology declaration and all 105 governed source mapping or typing axioms represented by active COMS rows. Its direct imports are:

- `http://www.w3.org/ns/sosa/sampling/`
- `http://www.w3.org/ns/ssn/`
- `http://www.w3.org/ns/ssn/systems/`
- `https://www.commoncoreontologies.org/2024-11-06/CommonCoreOntologiesMerged`

The 105 axioms partition exactly once by target vocabulary reachable from each asserted axiom object:

| Category | Count | Meaning |
|---|---:|---|
| Target-neutral | 29 | Source-only targets/expressions plus RDF/RDFS/OWL structural vocabulary; no BFO, CCO, or third target vocabulary. |
| BFO-bearing | 19 | Contains BFO terms and no CCO terms. |
| CCO-bearing | 25 | Contains CCO terms and no BFO terms. |
| Mixed BFO/CCO | 32 | Contains both BFO and CCO terms. |
| **Total** | **105** | Exact partition of current governed axioms. |

The target-neutral category consists of 26 source-only axioms and three additional source expressions using source terms and RDF/OWL class/list structure:

- `sosa:hasFeatureOfInterest rdfs:domain`
- `sosa:isFeatureOfInterestOf rdfs:range`
- `ssn-system:inCondition rdfs:domain`

Those expressions contain no genuine third target vocabulary. They are source-only union/class structures and must not be described as BFO or CCO mappings.

Complexity is material to product design:

| Complex-expression category | Count |
|---|---:|
| Target-neutral complex axioms | 3 |
| BFO-bearing complex axioms | 10 |
| CCO-bearing complex axioms | 5 |
| Mixed BFO/CCO complex axioms | 32 |
| **All complex mapping/typing axioms** | **50** |
| **Complex axioms containing CCO** | **37** |

### Review-only projection evidence

The existing projection contains 22 RDF triples: four `rdfs:subClassOf` and 18 `rdfs:subPropertyOf` assertions. It has no ontology declaration, imports, complex expressions, or `owl:equivalentClass` assertions. Its exclusions CSV has one header plus seven data rows, all named CCO property targets lacking an explicit BFO superproperty path. That report does not account for the 50 complex root axioms, including the 37 complex axioms containing CCO.

### PROV comparison and limitations

PROV's separation of BFO, CCO, and RO publication concepts is useful architectural evidence. Its current files are not semantic or serialization templates for SSN:

- `prov-bfo-directmappings.ttl` fails strict Turtle parsing at the SWRL-variable section because the required default prefix is unbound.
- `prov-cco-directmappings.ttl` fails strict Turtle parsing because a quoted `rdfs:comment` spans physical lines as an invalid Turtle string literal.
- `prov-ro-directmappings.ttl` strictly parses to 232 triples but contains zero asserted mapping axioms under the mapping predicates reviewed here.
- The RO file contains 25 resources typed `owl:Axiom`; none has its `owl:annotatedSource`, `owl:annotatedProperty`, and `owl:annotatedTarget` triple asserted in the graph.
- An `owl:Axiom` annotation record does not itself assert the annotated axiom.
- The pre-existing untracked PROV catalog is not tracked reproducibility evidence.

These defects do not argue against modular publication. They establish stronger requirements for SSN: strict syntax, actual asserted axioms, complete disposition accounting, fixed local validation, and deterministic generation.

### Review limitations

- This is an approved architecture policy, not implementation or a release-readiness declaration.
- The 105-way partition is syntactic by vocabulary presence; it does not approve any particular CCO-to-BFO transformation.
- This original policy review did not itself implement transformation rules, row dispositions, a release manifest, or a catalog; current implementation status is recorded in the later sections below.
- External registry, DOI, hosted-release, and branch-protection state were not examined.
- Stable product identities, import structure, transformation categories, versioning, projection retirement, and `sosa-next` lifecycle are settled here; the remaining implementation choices are listed in section 11.

## 3. Product Taxonomy

### 3.1 Integrated authoritative product

**File:** `SSN2BFO.ttl`

**Stable ontology IRI:** `http://www.sks.ai/SSN2BFO/`

Policy:

- It remains the complete standalone representation of all approved COMS mapping semantics. "Standalone" means its mapping/typing axioms are asserted in its own graph; it does not mean dependency-free.
- It is generated directly from `mappings/SSN2BFO-COMS.xlsx` and remains the authoritative production publication artifact.
- It may contain source, BFO, and CCO terms, including mixed expressions.
- It retains approved dependency-bearing source and CCO imports.
- It imports none of the project modules and must not become a wrapper around them.
- Its path and stable ontology IRI remain backward-compatible.
- Modular generation must not remove or weaken an approved root axiom.
- It remains subject to temporary validation, content-based freshness, HermiT, atomic replacement, last-known-good preservation, and rollback.

### 3.2 Alignment core

**File:** `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl`

**Stable ontology IRI:** `http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core`

"Alignment core" is the approved name:

- "Mapping core" would incorrectly imply that the 29 axioms map SSN/SOSA to BFO or CCO.
- "Source-typing core" is too narrow because the set includes governed source relation structure as well as domain/range typing.
- "Alignment core" identifies a shared governed layer without assigning it to a target ontology.

Policy:

- Generate exactly the 29 current target-neutral axioms from COMS.
- Import nothing.
- Reference source IRIs without importing external source ontologies.
- Declare exactly its own ontology IRI and generated metadata.
- Do not copy source class/property declarations into it.
- Contain only the 29 governed logical axioms plus generated nonlogical metadata.
- Serve as a shared production module once implemented, not as a substitute for the integrated root or a target-specific mapping product.

### 3.3 Strict BFO mapping

**File:** `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl`

**Stable ontology IRI:** `http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping`

Policy:

- Generate it directly from COMS and governed transformation policy.
- Import only the alignment core.
- Assert the 19 current BFO-bearing axioms unchanged.
- Include future mappings directly governed as strict BFO mappings.
- Include a transformed CCO-bearing or mixed mapping only when the transformation is demonstrated to preserve the complete original semantics without weakening under the fixed, pinned dependency closure.
- Preserve full axiom form and logical force. An `owl:equivalentClass` mapping may not become `rdfs:subClassOf` in this product.
- Exclude merely sound but less specific BFO consequences; those belong only in the BFO projection.
- Permit source, BFO, RDF/RDFS/OWL, and approved metadata vocabulary; prohibit CCO and RO IRIs in logical axioms.
- Preserve complex expressions when they are strict BFO mappings rather than flattening them into named-term assertions.
- Assert actual OWL/RDF mapping axioms. `owl:Axiom` annotations may supplement assertions but never replace them.
- Account deterministically for unchanged, lossless, excluded, deferred, and inapplicable rows.

`ssn-sosa-bfo-directmappings.ttl` is not the intended production filename. The existing placeholder may remain unchanged until implementation, but it must be deliberately renamed/replaced with `ssn-sosa-bfo-mapping.ttl` before first production publication.

### 3.4 BFO projection

**File:** `releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl`

**Stable ontology IRI:** `http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-projection`

Policy:

- Generate it from COMS dispositions plus approved, machine-governed transformation rules.
- Import only the strict BFO mapping.
- Treat it as the designated product for approved weaker but sound BFO consequences derived from richer CCO-bearing or mixed mappings.
- No direct projection axiom is currently approved, so the maintained product is intentionally import-only and policy-complete.
- Add no transformed or weakened consequence unless a later governed transformation rule and its proof obligations are approved.
- Prohibit CCO and RO IRIs in its added logical axioms.
- Trace every added assertion to the stable COMS row identifier and authoritative source expression.
- Identify each added assertion explicitly as a weakened projection, never as an equivalence-preserving or strict mapping.
- Record pinned dependency identities, transformation rule, logical justification, and positive/negative regression tests.
- Assert each projected axiom as an actual OWL/RDF axiom; annotations alone do not create a projection.

Its current import closure contains the alignment core and every strict BFO mapping. Because no direct projection axiom is approved, it currently adds no weakened BFO consequence; this zero-direct-axiom state is intentional rather than incomplete serialization.

A later release process may materialize this import closure as one standalone consumer file. Such a file is a generated packaging artifact, not a new mapping authority or independently editable product source.

### 3.5 CCO extension

**File:** `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl`

**Stable ontology IRI:** `http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension`

Policy:

- Generate it directly from COMS.
- Import only the strict BFO mapping.
- Receive the alignment core transitively through the strict BFO mapping rather than importing it directly.
- Add the 25 CCO-bearing and 32 mixed BFO/CCO axioms unchanged.
- Do not import the BFO projection, so weakened consequences do not enter the CCO product closure.
- Permit BFO terms because CCO extends BFO and every mixed axiom necessarily uses both vocabularies.
- Describe the product as a CCO extension/profile, not a graph containing only CCO IRIs.
- Assert actual mapping/typing axioms; annotations may supplement but never replace assertions.

`ssn-sosa-cco-directmappings.ttl` is not the intended production filename. The existing placeholder may remain until implementation, but it must be deliberately renamed/replaced with `ssn-sosa-cco-extension.ttl` before first production publication.

### 3.6 RO product

RO is deferred and is not part of the currently approved publication set. A focused semantic review must first determine whether SSN/SOSA concepts have useful, nonredundant RO mappings and whether a separate product benefits consumers. No RO workbook rows, imports, generator branches, release files, or completeness requirements should be added merely to mimic PROV.

### 3.7 `sosa-next` products

`src/sosa-next/` and `releases/sosa-next/` remain explicitly inactive lifecycle scaffolding. They must not enter current product generation, authoritative hosted CI, release assembly, mapping coverage, completeness accounting, or formal publication. Section 9 defines the approved activation and later removal conditions.

## 4. Import Policy

### Alternatives considered

| Alternative | Advantages | Risks | Decision |
|---|---|---|---|
| A. Import-free mapping modules that reference external IRIs | Small, selective, and no automatic remote dependency closure. | Project-module reuse would require consumers to assemble every layer manually. | Applied to external SSN/SOSA, BFO, CCO, and RO dependencies, but not between project modules. |
| B. Each module imports corresponding external source and target ontologies | Convenient one-file dependency loading. | Mutable remote resolution, repeated closures, higher loading cost, duplicate imports, and weaker offline reproducibility. | Rejected for modular products. |
| C. Layered project modules import only other project modules; the integrated root remains the dependency-bearing consumer profile | Acyclic reuse, small modules, explicit mapping strength, deterministic composition, and one complete integrated artifact. | Requires maintained catalogs, explicit validation closures, and clear consumer documentation. | **Approved.** |

### Approved project-module graph

The exact import policy is:

- Alignment core imports nothing.
- Strict BFO mapping imports only the alignment core.
- BFO projection imports only the strict BFO mapping.
- CCO extension imports only the strict BFO mapping.
- CCO extension does not import the alignment core directly.
- BFO projection does not import the CCO extension.
- CCO extension does not import the BFO projection.
- Modular products do not import external SSN/SOSA, BFO, CCO, or RO ontologies.
- Modular products reference those external IRIs without loading mutable remote closures.
- `SSN2BFO.ttl` imports none of the modular products and retains its approved dependency-bearing source and CCO imports.

| Product | Project imports in development generation | External ontology imports |
|---|---|---|
| Alignment core | None | None |
| Strict BFO mapping | Stable alignment-core ontology IRI only | None |
| BFO projection | Stable strict-BFO-mapping ontology IRI only | None |
| CCO extension | Stable strict-BFO-mapping ontology IRI only | None |
| Integrated root | None | Its approved source and CCO dependency imports |

Formal release modules must preserve the same graph while importing the corresponding same-release immutable project-module version IRI. Development generation uses stable project ontology IRIs and does not claim an immutable release version.

Validation must load fixed local source and target ontologies explicitly. Maintained catalogs may map stable and release IRIs to tracked local files for offline resolution. Validation and release must not rely on an untracked catalog or a mutable remote response.

Operational requirements:

- Keep the graph acyclic: alignment core <- strict BFO mapping <- {CCO extension, BFO projection}.
- Prevent duplicate direct core imports from either leaf.
- Validate each module alone for syntax, vocabulary, and accounting, and in its fixed intended closure for logic.
- Resolve formal release imports to immutable same-release module bytes.
- Record fixed source/target identities and hashes in generated metadata and manifests.
- Do not duplicate governed source axioms across modular files. The integrated root is the intentional independent serialization because it remains the complete standalone product.

## 5. Complete COMS Row-Disposition Policy

Every active or explicitly blank/deferred COMS row must receive a deterministic disposition for every product. Generation must fail if any row lacks a disposition. Domain/range typing rows remain typing-only for relation-mapping coverage even when emitted in a product.

### Required machine-readable fields

At minimum, each record must include:

- stable COMS row identifier and current worksheet/row location;
- source subject;
- authoritative COMS predicate and target expression;
- source-expression hash so row movement does not silently alter identity;
- mapping type: class, object-property, property chain, domain, range, typing-only, or future rule;
- per-product disposition;
- emitted/generated axiom identifier or canonical expression, when applicable;
- transformation-rule identifier, when applicable;
- pinned source, BFO, and CCO dependency identities used by a transformation;
- classification: unchanged, lossless, weakened, unsupported, deferred, or not applicable;
- logical justification or verified entailment;
- receiving product;
- positive and negative regression-test identifiers;
- exclusion/deferment reason;
- available `coms:Reasoning` rationale;
- generator, transformation-policy, and metadata-source versions.

### Required disposition vocabulary

The data model must support at least:

- emitted in alignment core;
- emitted unchanged in strict BFO mapping;
- emitted as an approved lossless transformation in strict BFO mapping;
- provided through imported strict BFO mapping;
- emitted as an explicitly weakened consequence in BFO projection;
- emitted unchanged in CCO extension;
- emitted unchanged in integrated root;
- provided transitively through an imported project module;
- excluded from strict BFO mapping with reason;
- excluded from BFO projection with reason;
- unsupported or unproven transformation;
- deferred;
- typing-only;
- future governed rule/SWRL module;
- not applicable to a product.

"Typing-only" is a mapping-type/accounting classification and may coexist with an emitted or imported disposition; it must not inflate relation-mapping coverage.

### Initial disposition expectation

| Current category | Alignment core | Strict BFO mapping | BFO projection | CCO extension | Integrated root |
|---|---|---|---|---|---|
| 29 target-neutral | Emit unchanged | Provided through imported core | Provided transitively through strict BFO/core | Provided transitively through strict BFO/core | Emit unchanged |
| 19 BFO-bearing | Not applicable | Emit unchanged | Provided through imported strict BFO mapping | Provided through imported strict BFO mapping | Emit unchanged |
| 25 CCO-bearing | Not applicable | Emit only an approved lossless BFO transformation; otherwise exclude/defer with reason | Emit an approved weakened BFO consequence, receive any lossless result through strict BFO, or exclude/defer with reason | Emit authoritative axiom unchanged | Emit authoritative axiom unchanged |
| 32 mixed BFO/CCO | Not applicable | Emit only an approved lossless BFO transformation; otherwise exclude/defer with reason | Emit an approved weakened BFO consequence, receive any lossless result through strict BFO, or exclude/defer with reason | Emit authoritative axiom unchanged | Emit authoritative axiom unchanged |

This table is the approved default, not approval of a transformation for any row. The 105 authoritative axioms remain accounted as 29 + 19 + 25 + 32. Lossless BFO transformations and weakened BFO projections are additional derived dispositions tied to the originating row; they do not replace the unchanged CCO/mixed axiom in the CCO extension or integrated root.

No omission may be inferred from absence, and no generator may silently drop an expression it cannot serialize. A row without an approved transformation must be explicitly excluded or deferred for the strict BFO mapping and BFO projection.

The disposition source must not become a second editable mapping authority. Mechanical category assignments derive from COMS. Transformation rules reside in a separately governed, machine-readable policy source linked to stable COMS row identifiers.

## 6. Complex-Expression and Transformation Policy

Complex mappings must be serialized as faithful OWL/RDF structures and must not be flattened into misleading named-term mappings.

- **Intersections:** preserve every conjunct and grouping in unchanged/lossless mappings.
- **Unions:** preserve one `owl:unionOf` expression. Multiple superclass, domain, or range axioms are generally conjunctive and are not a substitute for a union.
- **Existential restrictions:** preserve the property, quantifier, filler, and nesting unless an approved proof classifies a changed expression.
- **Inverse-property expressions:** preserve direction and inverse structure in authoritative mappings.
- **Property chains:** preserve ordered chain members and asserted superproperty. A list annotation without `owl:propertyChainAxiom` is not an assertion.
- **Source-only domain/range typing:** place the three complex source-only expressions and other target-neutral typing axioms in the alignment core; do not market them as BFO or CCO mappings.
- **Mixed BFO/CCO expressions:** keep them unchanged in the CCO extension and integrated root.
- **Future SWRL rules:** keep them outside the approved products until a governed rule policy defines their source representation, module boundary, safety/profile constraints, and inference tests.

### Transformation classes

A transformation is **lossless** only when:

- the BFO-only expression and authoritative COMS expression mutually entail one another under the fixed, pinned approved dependency closure;
- the complete axiom form, direction, quantification, and logical force are preserved;
- regression tests demonstrate the intended equivalence; and
- it is recorded as an approved lossless transformation.

Lossless transformations may enter the strict BFO mapping.

A transformation is a **weaker but sound consequence** only when:

- the authoritative COMS axiom entails the BFO-only result under the fixed, pinned closure;
- the reverse entailment does not hold or is not claimed;
- the consequence is explicitly labeled as weakened; and
- positive and negative tests demonstrate its intended boundary.

Weaker consequences belong only in the BFO projection. They must never be presented as strict mappings or equivalence-preserving transformations.

A transformation is **unsupported or unproven** when the required entailment has not been demonstrated, when it changes axiom force without an approved projection classification, or when it depends on an unapproved/mutable inference path. Such a row is excluded or deferred.

Superclass or superproperty reachability alone may identify a candidate weaker consequence. It never establishes equivalence, automatically authorizes publication, or permits choosing an arbitrary "nearest" BFO term. A reasoner-clean result is not proof of semantic preservation or sound weakening.

### Governed positive candidates

Potentially valid positive monotonic transformations may include:

- replacing a term by an entailed superclass inside an intersection;
- replacing a disjunct by an entailed superclass;
- weakening an existential filler;
- weakening an existential property to an entailed superproperty.

Each is permitted only when a machine-governed rule applies and the complete resulting entailment has been demonstrated. The context can change whether a local replacement is sound; no textual substitution rule is sufficient.

Do not generically transform:

- complements or negations;
- cardinality restrictions;
- universal restrictions;
- disjointness;
- inverse-property expressions;
- property-chain members;
- incomparable target alternatives;
- conditions encoded in restrictions;
- SWRL rules.

Every approved transformation record must include:

- stable COMS row identifier;
- authoritative source expression;
- pinned CCO and BFO dependency identities;
- transformation-rule identifier;
- resulting BFO expression;
- classification as lossless or weakened;
- logical justification or verified entailment;
- receiving product;
- positive and negative regression tests.

An `owl:equivalentClass` mapping may become `rdfs:subClassOf` only as an intentional weakened projection in the BFO projection, never as a strict BFO mapping.

## 7. Product Metadata and Versioning Policy

### Stable product identities

| Product | Stable ontology IRI |
|---|---|
| Integrated root | `http://www.sks.ai/SSN2BFO/` |
| Alignment core | `http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core` |
| Strict BFO mapping | `http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping` |
| BFO projection | `http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-projection` |
| CCO extension | `http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension` |

These stable IRIs identify product lines. This decision does not itself create or reuse an immutable version IRI.

### Formal release identity

Use date-based immutable release identifiers:

- `YYYY-MM-DD`

Use corresponding Git tags:

- `vYYYY-MM-DD`

Same-day revision suffixes are not approved in the current schema. A formal context also supplies the identical canonical release date and an exact 40-character lowercase hexadecimal source commit; these values are explicit inputs and are never inferred from the clock, branch, `HEAD`, tag state, or a remote.

Formal release version IRIs are:

| Product | Version IRI form |
|---|---|
| Integrated root | `http://www.sks.ai/SSN2BFO/releases/<version>/integrated` |
| Alignment core | `http://www.sks.ai/SSN2BFO/releases/<version>/current-ssn-sosa/alignment-core` |
| Strict BFO mapping | `http://www.sks.ai/SSN2BFO/releases/<version>/current-ssn-sosa/bfo-mapping` |
| BFO projection | `http://www.sks.ai/SSN2BFO/releases/<version>/current-ssn-sosa/bfo-projection` |
| CCO extension | `http://www.sks.ai/SSN2BFO/releases/<version>/current-ssn-sosa/cco-extension` |

A version IRI must never identify different bytes.

Development generation retains each stable ontology IRI and does not claim a new immutable release version IRI. It remains authoritative development output without pretending to be a frozen formal release.

Formal release generation:

- receives an explicit approved release identifier;
- replaces the development authority status with `http://www.sks.ai/SSN2BFO/authority-status/immutable-authoritative-release`;
- emits `owl:versionIRI`, plain language-neutral `owl:versionInfo`, and `dcterms:issued` typed as `xsd:date`;
- uses same-release immutable project-module imports while preserving the integrated root's four external imports;
- validates the complete product set;
- freezes exact candidate artifact bytes in an explicitly requested package operation; and
- creates no Git tag in the current rendering implementation.

### Candidate release package

The deterministic package builder accepts only an explicit formal context, repository-relative approved release notes, and absent output directory. It builds and validates in a temporary sibling before atomic publication and never updates the nine maintained development outputs. The package is candidate tooling: it does not prove that the source commit matches a clean checkout and does not create an archive, Git tag, GitHub release, or deployed persistent IRI.

A candidate package contains exactly 13 regular files: five formal ontology products, `catalog-v001.xml`, `manifest.json`, `SHA256SUMS`, `RELEASE-NOTES.md`, `LICENSE`, the COMS workbook, publication-metadata TOML, and product-disposition evidence. It contains no third-party ontology, development report, coverage report, legacy report, placeholder, source snapshot, archive, or inactive-track product. The package is offline-complete for its project-module imports; external integrated-root imports remain documented pinned dependencies and are not redistributed.

Manifest schema version 1 uses canonical UTF-8 JSON and records the explicit formal context, governed inputs and byte-affecting modules, products, pinned dependencies, stable validation environment, computed validation outcomes, and 11 included files other than the manifest and checksum list. It does not hash itself or `SHA256SUMS`. The checksum list includes `manifest.json`, excludes only itself, and uses lowercase SHA-256 plus two spaces and a normalized relative path in lexicographic order. The canonical OASIS catalog maps only the five same-release immutable version IRIs to package-relative TTL files.

### Governed metadata source

`config/publication-metadata.toml` is the sole governed and editable publication-metadata source. Schema version 3 is parsed with standard-library `tomllib`, rejects unknown keys, and governs these global values:

| Field | Governed value |
|---|---|
| Project title | `SSN-to-BFO` |
| Default language | `en` |
| Release IRI base | `http://www.sks.ai/SSN2BFO/releases` |
| License IRI | `https://creativecommons.org/publicdomain/zero/1.0/` |
| Repository IRI | `https://github.com/BFO-Mappings/SSN-to-BFO` |
| Generated warning | `Generated from governed COMS and publication metadata; do not edit this ontology directly.` |
| Development authority-status predicate | `http://www.w3.org/ns/adms#status` |
| Development authority-status value | `http://www.sks.ai/SSN2BFO/authority-status/maintained-authoritative-development` |
| Formal release authority-status value | `http://www.sks.ai/SSN2BFO/authority-status/immutable-authoritative-release` |

The five product records remain in canonical order and govern the existing path, stable ontology IRI, release suffix, and these publication values:

| Product | Label | Lifecycle-neutral description | Product-type IRI |
|---|---|---|---|
| Integrated | SSN-to-BFO Integrated Mapping | Directly asserts the complete governed COMS axiom set for the SSN/SOSA alignment with BFO and CCO. | `http://www.sks.ai/SSN2BFO/product-type/integrated` |
| Alignment core | SSN/SOSA Alignment Core | Directly asserts the governed target-neutral SSN/SOSA alignment axioms shared by the modular products and imports no ontology. | `http://www.sks.ai/SSN2BFO/product-type/alignment-core` |
| Strict BFO mapping | SSN/SOSA Strict BFO Mapping | Directly asserts governed BFO-bearing axioms without weakening and imports the SSN/SOSA alignment core. | `http://www.sks.ai/SSN2BFO/product-type/strict-bfo-mapping` |
| BFO projection | SSN/SOSA BFO Projection | Imports the strict BFO mapping and is the designated product for approved weaker but sound BFO consequences; no direct projection axiom is currently approved. | `http://www.sks.ai/SSN2BFO/product-type/bfo-projection` |
| CCO extension | SSN/SOSA CCO Extension | Directly asserts governed CCO-bearing and mixed BFO/CCO axioms unchanged and imports the strict BFO mapping. | `http://www.sks.ai/SSN2BFO/product-type/cco-extension` |

The product-type IRIs are controlled `dcterms:type` values. They do not require declaration triples or a separate vocabulary ontology. The development authority status uses `adms:status` with the governed maintained-authoritative-development IRI. Descriptions remain lifecycle-neutral and do not repeat that status.

Schema version 3 governs and validates exactly seven development annotations on each maintained ontology subject, in canonical order: `rdfs:label`, `dcterms:description`, `dcterms:type`, `adms:status`, `dcterms:license`, `rdfs:seeAlso`, and `rdfs:comment`. Labels, descriptions, and warnings are language-tagged with the governed default `en`; product type, status, license, and repository objects are IRIs. The integrated and modular emitters consume one shared immutable metadata model loaded once per nine-output transaction. The exact metadata set is validated separately from declarations, imports, and governed/structural logical triples.

With a complete validated formal context, the same renderer retains those seven predicates, substitutes the formal authority status, and appends exactly `owl:versionIRI`, plain `owl:versionInfo`, and `dcterms:issued` as `xsd:date`. Stable ontology subjects do not change. Alignment core has no project import; strict BFO imports the same-release alignment-core version IRI; BFO projection and CCO extension import the same-release strict-BFO version IRI; and the integrated root keeps its existing ordered external imports.

Development serialization is deterministic and preserves the existing generated-file Turtle comments in addition to the machine-readable warning. Metadata prefix and ontology-header ordering are explicit, and stripping the ontology declaration, approved project imports, and exact seven annotations must reproduce the governed logical graph. Metadata is never counted as a governed axiom, mapping triple, structural expression triple, projection axiom, or copied declaration.

Creator and contributor governance, ORCIDs, agents, provenance RDF, source and dependency RDF, local validation paths in RDF, workbook or generator provenance RDF, source-commit and tag RDF, clean-checkout source binding, deterministic archives, tagging, and GitHub publication remain deferred. Package manifests may record dependency and artifact hashes as non-RDF evidence. Local filesystem paths and hashes must never be emitted as ontology RDF identifiers or publication metadata. Contributor metadata must not be inferred automatically from Git authors.

Development artifacts use stable ontology IRIs and the governed development authority status. They do not claim `owl:versionIRI`, `owl:versionInfo`, `dcterms:issued`, a release date, a Git tag, or frozen artifact identity. Formal rendering and candidate packaging are separate explicit operations and do not alter the nine maintained development outputs. No actual release context or notes have been selected, and no package has been committed or published.

### License scope

The CC0 dedication applies only to project-authored content directly asserted in the generated products. It does not apply to ontology content obtained through imports, referenced as a dependency, or used only for validation; those third-party resources retain their own notices and terms.

Annotating a project ontology with the governed CC0 IRI does not relicense its import closure or any validation dependency.

Formal release reproducibility must connect:

- release identifier;
- Git tag;
- exact commit SHA;
- workbook SHA-256;
- generator SHA-256;
- artifact SHA-256 values;
- source ontology hashes or version identities;
- BFO and CCO dependency identities;
- product-disposition report hashes.

Release validation must fail when:

- configured version and Git tag disagree;
- one version IRI identifies different bytes;
- generated artifacts are stale;
- recorded hashes do not match released files.

## 8. Validation and Release Gates

Every production product must satisfy all applicable gates before atomic publication:

1. Strict Turtle parsing.
2. Exactly the expected `owl:Ontology` declaration and approved stable ontology IRI.
3. In formal release mode, the correct immutable `owl:versionIRI`, `owl:versionInfo`, release identifier, and same-release import IRIs.
4. Product-specific permitted-vocabulary audit:
   - alignment core logical axioms: source and RDF/RDFS/OWL terms only; no BFO, CCO, or RO terms;
   - strict BFO mapping logical axioms: source, BFO, and RDF/RDFS/OWL terms only; no CCO or RO terms;
   - BFO projection added logical axioms: source, BFO, and RDF/RDFS/OWL terms only; no CCO or RO terms;
   - CCO extension logical axioms: source, CCO, BFO, and RDF/RDFS/OWL terms; no RO terms;
   - integrated root: only approved source/BFO/CCO/dependency vocabularies.
5. Actual asserted mapping/typing axioms. An `owl:Axiom` record is not counted unless its annotated axiom is asserted.
6. Complete COMS row accounting with no unknown, missing, or silently dropped row.
7. Canonical semantic comparison between generated axioms and unchanged/lossless/weakened dispositions.
8. HermiT consistency over the appropriate fixed local closure.
9. Zero named unsatisfiable classes.
10. Source/example entailment checks where a product is intended to support those examples.
11. Deterministic serialization and regeneration from fixed COMS, transformation-policy, and metadata inputs.
12. Workbook, generator, transformation-policy, metadata-source, and product freshness hashes.
13. Temporary generation and validation before any maintained file is replaced.
14. Atomic replacement of the complete maintained product/report set.
15. Rollback to the previous complete set after any publication failure.
16. `git diff --check`, clean-tree validation, and hosted execution of the canonical gate.
17. Generated metadata and release-manifest validation.

Layered-product gates additionally require:

- the exact acyclic graph alignment core <- strict BFO mapping <- {CCO extension, BFO projection};
- no external source/target ontology imports in modular products;
- no direct alignment-core import from CCO extension or BFO projection;
- no import edge between CCO extension and BFO projection;
- offline resolution through maintained local artifacts/catalogs;
- exact resolution of intended stable development or immutable release module IRIs;
- BFO projection closure containing alignment core, strict BFO mappings, and approved weakened consequences;
- CCO extension closure containing alignment core, strict BFO mappings, and unchanged CCO/mixed mappings, but no BFO projection;
- all 105 integrated-root mapping/typing axioms accounted unchanged across alignment core + strict BFO mapping + CCO extension;
- separate accounting for lossless transformation results and weakened projection consequences;
- annotation-to-assertion integrity checks;
- positive and negative tests for every governed transformation rule;
- proof that no strict mapping is merely a weakened consequence.

Formal release gates additionally require:

- exact `YYYY-MM-DD` release identifier/date and matching `vYYYY-MM-DD` Git tag;
- version IRIs under `http://www.sks.ai/SSN2BFO/releases/<version>/`;
- immutable artifact and manifest hashes;
- same-release project-module import resolution;
- failure when a version/tag/hash relationship is inconsistent.

The existing COMS safeguards remain mandatory: temporary validation, content-based freshness, atomic publication, last-known-good preservation, and rollback. Multi-product generation must be one transaction so root and modules cannot represent different workbook, policy, or metadata versions.

## 9. Existing Placeholder and Inactive-Track Disposition

### Current SSN/SOSA placeholders

The existing files:

- `releases/current-ssn-sosa/ssn-sosa-bfo-directmappings.ttl`
- `releases/current-ssn-sosa/ssn-sosa-cco-directmappings.ttl`

may remain unchanged until implementation. They must not be manually populated or published as the approved products.

Before first production publication, implementation must deliberately replace/rename them to:

- `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl`
- `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl`

The alignment-core and BFO-projection paths must be created only by the governed generator, not as manually maintained shells. Catalogs, documentation, expected-file policies, and consumers must move to the approved names in the same implementation transaction. Placeholder replacement/renaming occurs atomically only after the complete generated product set passes all gates.

No `directmappings` filename is an intended current-track production identity.

### `sosa-next` lifecycle

Retain:

- `src/sosa-next/`
- `releases/sosa-next/sosa-bfo-directmappings.ttl`
- `releases/sosa-next/sosa-cco-directmappings.ttl`

as explicitly inactive lifecycle scaffolding for now. Do not populate them merely to make the scaffold appear complete. They are excluded from current product generation, authoritative hosted CI, release assembly, mapping coverage, product completeness accounting, and formal publication.

Activate the track only after:

1. A stable next-version SOSA or SSN/SOSA source is identified.
2. Source files, ontology IRIs, and version identity are fixed.
3. The project explicitly adopts that source version.
4. A mapping authority is established for that source version.
5. Product scope is defined.
6. Import/dependency policy is approved.
7. Examples and validation fixtures exist.
8. Coverage accounting is implemented.
9. Metadata and versioning are approved.
10. The track is deliberately added to authoritative CI.

Replace the temporary name `sosa-next` with the actual source-version identity before publication. No production path or ontology IRI may retain "next."

Do not remove the scaffold during current product work. After current modular products are implemented, review removal separately. Remove it only when no stable next-version source is expected during the foreseeable development cycle and the scaffold causes meaningful maintainer or consumer confusion. Removal must be a dedicated cleanup PR.

## 10. Current Review-Only Projection

`src/current-ssn-sosa/build/artifacts/current-ssn-sosa-bfo-only-generated.ttl` remains review-only until the governed COMS products replace it. It cannot be promoted because:

- it produces only 22 simple assertions while the root has 50 complex mapping/typing axioms;
- it omits complex mappings and property chains;
- its seven-row exclusion report covers only named CCO property targets without BFO paths and does not account for every omitted COMS row;
- it turns some `owl:equivalentClass` mappings into weaker `rdfs:subClassOf` consequences;
- it has no ontology declaration, stable product IRI, imports, release metadata, or authority declaration;
- it is an ignored build artifact rather than a transactionally maintained output;
- it uses the old independent ROBOT 1.9.5 installation path;
- it has no governed transformation rules, proof obligations, or positive/negative tests.

After the governed alignment core, strict BFO mapping, BFO projection, and CCO extension exist:

1. Retire `make -C src/current-ssn-sosa derive-bfo-from-cco` as a publication workflow.
2. Stop treating `current-ssn-sosa-bfo-only-generated.ttl` as a prospective release artifact.
3. Replace its publication role with the COMS-generated strict BFO mapping and BFO projection.

Preserve the underlying named-target hierarchy analysis only if maintainers find it useful. If retained:

- rename the target to a diagnostic name such as `suggest-bfo-projection-candidates`;
- emit CSV or Markdown candidate-report output, not an ontology product;
- identify results as possible weaker consequences rather than approved mappings;
- require human semantic review and an approved transformation rule before publication;
- use the declared validation toolchain;
- keep it outside release gates unless a later candidate-analysis policy explicitly governs it.

Candidate analysis must never write directly into the production BFO projection module.

## 11. Decisions Required Before Implementation

### Approved policy, not open implementation choices

The following decisions are settled by this report and must not be reopened as incidental engineering choices:

1. Product names, paths, and stable `sks.ai` ontology IRIs in sections 1 and 7.
2. The layered import graph alignment core <- strict BFO mapping <- {CCO extension, BFO projection}.
3. Separation of strict BFO mappings from weakened BFO projections.
4. Lossless, weakened, and unsupported transformation categories and proof obligations.
5. Date-based release identifiers, `v<version>` tags, and immutable release version IRI forms.
6. Retirement of the current simple projection as a publication workflow, with optional retention only as candidate analysis.
7. Retention of `sosa-next` as inactive scaffolding under the activation/removal policy in section 9.

RO applicability and SWRL/rule-module governance remain separate future policy reviews, not implementation choices for the approved current products.

### Remaining engineering decisions

Implementation must still specify:

1. Machine-readable product-disposition schema and governed file location.
2. Stable COMS row-key mechanism resilient to worksheet row movement.
3. Transformation-rule serialization and proof/result representation.
4. Clean-checkout source-commit binding and deterministic archive construction around the implemented manifest/package format.
5. Multi-product temporary-generation, validation, atomic replacement, and rollback transaction design.
6. Persistent deployment and stable-IRI catalog migration beyond the package-local version-IRI catalog.
7. Module-specific fixed HermiT closures and example suites.
8. Canonical integrated-versus-modular semantic reconciliation.
9. Placeholder rename/migration mechanics for tracked paths and downstream references.
10. Whether an optional materialized standalone BFO-projection closure is needed as a packaging artifact.
11. Diagnostic candidate-report schema if the old hierarchy analysis is retained.

These choices may refine implementation mechanics but may not alter approved product identity, import direction, mapping strength, transformation classification, version policy, or lifecycle boundaries.

## 12. Recommended Implementation Sequence

Use narrow branches/PRs in this order:

1. **Record approved policy:** commit this report without changing mappings or products.
2. **Implement governed metadata/versioning:** add `config/publication-metadata.toml`, parse it with Python 3.12 `tomllib`, and enforce release/tag/version/hash rules.
3. **Implement stable row identity and disposition model:** account for every COMS row in every product.
4. **Add governed transformation rules and reports:** represent proof obligations, pinned dependencies, classifications, and tests.
5. **Generate alignment core:** emit and validate the 29 target-neutral axioms under the approved identity and import-free policy.
6. **Generate strict BFO mapping:** emit the 19 unchanged BFO-bearing axioms plus only approved lossless transformations; import the alignment core.
7. **Generate BFO projection:** import the strict BFO mapping and add only approved weaker consequences.
8. **Generate CCO extension:** import the strict BFO mapping and emit the 25 CCO-bearing plus 32 mixed axioms unchanged.
9. **Add modular and reconciliation gates:** test imports, vocabularies, accounting, HermiT, transformations, freshness, rollback, metadata, and integrated-versus-modular semantics.
10. **Replace placeholders atomically:** rename/remove old current-track `directmappings` shells only after every product passes.
11. **Retire or rename old projection workflow:** preserve only governed candidate analysis if it remains useful.
12. **Add consumer documentation and examples:** explain integrated, strict BFO, projected BFO, and CCO loading.
13. **Keep later scopes separate:** RO applicability, SWRL governance, and `sosa-next` activation remain separate work.

No implementation step may change the COMS workbook merely to simplify product generation.

## 13. Final Acceptance Checklist

- [ ] COMS remains the sole editable mapping authority.
- [ ] `SSN2BFO.ttl` remains the complete standalone authoritative integrated product at `http://www.sks.ai/SSN2BFO/`.
- [ ] `SSN2BFO.ttl` asserts every approved COMS mapping/typing axiom and imports no modular product.
- [ ] The alignment core is generated at `releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl` with stable IRI `http://www.sks.ai/SSN2BFO/current-ssn-sosa/alignment-core`.
- [ ] The strict BFO mapping is generated at `releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl` with stable IRI `http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-mapping`.
- [ ] The BFO projection is generated at `releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl` with stable IRI `http://www.sks.ai/SSN2BFO/current-ssn-sosa/bfo-projection`.
- [ ] The CCO extension is generated at `releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl` with stable IRI `http://www.sks.ai/SSN2BFO/current-ssn-sosa/cco-extension`.
- [ ] The import graph is alignment core <- strict BFO mapping <- {CCO extension, BFO projection}, with no cycles or extra module edges.
- [ ] Modular products import no external SSN/SOSA, BFO, CCO, or RO ontology.
- [ ] The alignment core contains the 29 governed target-neutral axioms and no BFO/CCO/RO logical terms.
- [ ] The strict BFO mapping contains the 19 unchanged BFO-bearing axioms and only approved lossless transformations.
- [ ] Strict BFO logical axioms contain no CCO or RO terms.
- [ ] Merely weaker consequences are absent from the strict BFO mapping.
- [ ] BFO projection added logical axioms contain no CCO or RO terms.
- [ ] BFO projection metadata and dispositions identify every added axiom as weakened.
- [ ] BFO projection closure contains the alignment core, strict BFO mappings, and approved weakened consequences.
- [ ] CCO extension contains the 25 CCO-bearing and 32 mixed axioms unchanged.
- [ ] CCO extension imports strict BFO mapping rather than BFO projection and therefore excludes the weakened projection closure.
- [ ] Every COMS row has a stable identifier, authoritative expression, and deterministic disposition for every product.
- [ ] Every transformation records pinned dependencies, rule identity, justification, receiving product, and positive/negative tests.
- [ ] No row or complex expression is silently omitted or flattened.
- [ ] Formal releases use `YYYY-MM-DD`, matching `vYYYY-MM-DD` tags, and immutable version IRIs under `http://www.sks.ai/SSN2BFO/releases/<version>/`.
- [ ] No version IRI is reused for different bytes.
- [x] Development metadata is generated from `config/publication-metadata.toml`, parsed with standard-library `tomllib`, and is not hand-edited into products.
- [ ] Development generation does not claim an immutable release version IRI.
- [ ] Every production file strictly parses and contains its asserted axioms; annotation-only pseudo-mappings fail validation.
- [ ] Product-specific vocabulary and import audits pass.
- [ ] Fixed-closure HermiT returns 0 with zero named unsatisfiable classes for every applicable product/profile.
- [ ] Integrated and modular governed semantics reconcile, with lossless and weakened derived axioms reported separately.
- [ ] Generation is deterministic, fresh, temporary-first, atomic, rollback-capable, clean-tree checked, and hosted-CI enforced.
- [ ] Current `directmappings` placeholders are deliberately renamed/replaced only after all gates pass.
- [ ] The old 22-triple projection workflow is retired from publication or renamed as non-product candidate analysis.
- [ ] Candidate analysis cannot write into the production BFO projection.
- [ ] `sosa-next` remains inactive and excluded until all activation conditions are approved.
- [ ] RO and future SWRL/rule products remain outside the approved current product set.

Final policy conclusions:

1. Root `SSN2BFO.ttl` remains the complete standalone authoritative product.
2. The 29 target-neutral axioms form the shared alignment core.
3. The 19 BFO-bearing axioms are the initial unweakened strict BFO mapping content.
4. Approved lossless transformations may enter the strict BFO mapping; weaker but sound consequences belong only in the BFO projection.
5. The BFO projection imports the strict BFO mapping and supplies the complete projected BFO consumer closure without entering the CCO extension closure.
6. The 25 CCO-bearing plus 32 mixed axioms belong unchanged in the CCO extension unless COMS itself changes.
7. The current 22-triple projection is not a production release and its publication workflow will be retired after replacement.
8. No COMS row may be silently omitted from any product accounting.
9. PROV's modular idea is useful, but its current release serialization and annotation mechanics are not templates to copy.
10. RO and `sosa-next` products are not part of the current approved product set.
