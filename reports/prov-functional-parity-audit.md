# PROV-to-BFO Functional Parity Audit

## 1. Executive Conclusion

SSN-to-BFO does **not** currently have overall functional parity with PROV-to-BFO. SSN-to-BFO has the stronger operational core: COMS is a single editable authority; generation is deterministic; workbook, generator, and artifact hashes are checked; publication is transactional with rollback; source coverage is a failing gate; and the full local closure is explicitly checked for named unsatisfiable classes. Those strengths should be preserved.

Parity nevertheless fails in several material areas. The unequivocal immediate repository-control defect is hosted CI: it validates two placeholder editor tracks instead of running the authoritative `make check` or `make check-coms` gate (`CI-02`, `CI-03`, `CI-04`, `RELEASE-05`). Separately, the absence of a production BFO-only product and completed consumer-selectable target products (`MAP-01`, `RELEASE-06`) blocks a claim of complete PROV functional parity; it does **not** imply that the existing mixed authoritative root ontology is logically invalid. License approval and publication/version metadata are public-release governance and maturity gaps, not all immediate repository-control failures.

Capability-matrix totals (99 findings):

| Status | Count |
|---|---:|
| PARITY | 12 |
| SSN STRONGER | 35 |
| PARTIAL | 18 |
| MISSING | 13 |
| NOT APPLICABLE | 5 |
| PROV PLACEHOLDER | 9 |
| UNVERIFIED | 7 |

Recalculated finding IDs:

- **MISSING (13):** `MAP-01`, `ONTO-02`, `CI-02`, `CI-03`, `CI-04`, `RELEASE-02`, `RELEASE-06`, `FAIR-02`, `FAIR-03`, `FAIR-04`, `FAIR-06`, `ADD-02`, `ADD-05`.
- **PARTIAL (18):** `AUTH-04`, `MAP-06`, `MAP-07`, `ONTO-03`, `ONTO-04`, `DEP-01`, `DEP-03`, `DEP-05`, `EXAMPLE-02`, `METHOD-01`, `METHOD-02`, `METHOD-03`, `RELEASE-01`, `RELEASE-05`, `FAIR-05`, `DEV-01`, `ADD-01`, `ADD-04`.
- **UNVERIFIED (7):** `MAP-03`, `BUILD-04`, `BUILD-05`, `QUERY-03`, `CI-05`, `RELEASE-04`, `ADD-03`.
- **NOT APPLICABLE (5):** `MAP-04`, `BUILD-06`, `EXAMPLE-05`, `QUERY-06`, `EXAMPLE-06`.
- **PROV PLACEHOLDER (9):** `BUILD-08`, `BUILD-09`, `BUILD-10`, `QUERY-07`, `RELEASE-07`, `PLACE-01`, `PLACE-02`, `PLACE-03`, `PLACE-04`.

The matrix consolidates into **13 distinct confirmed implementation packages**, **6 policy/applicability decisions**, and **2 unverified PROV capabilities requiring confirmation**; matrix-row counts are not project counts. Public release additionally requires a license decision (`FAIR-02`), while version/tag/version-IRI maturity (`RELEASE-02`, `ONTO-03`) and machine-readable publication metadata (`FAIR-04`, `ONTO-02`) require explicit policy and implementation. The highest-value nonblocking improvements are per-example HermiT validation (`EXAMPLE-02`), a lossless COMS-derived SSSOM-compatible export (`MAP-06`), and richer active methods and reuse material. Simple candidate discovery and deductive-impact analysis remain valuable possibilities, but the audited PROV checkout did not establish them as reproducible current capabilities.

## 2. Baselines and Method

### Fixed baselines

| Repository | Path | Recorded branch | Recorded SHA | Observed result |
|---|---|---|---|---|
| SSN-to-BFO | `/Users/alecsculley/Documents/GitHub/SSN-to-BFO` | `review/prov-functional-parity` | `96e31055c9c90f4989fac1ff0589f8a2de939680` | Exact match; initial tree clean |
| PROV-to-BFO | `/Users/alecsculley/Documents/GitHub/PROV-to-BFO` | `main` | `c60847a4b838d25972d899731c0f6bb83716181d` | Exact match; one pre-existing untracked generated `src/imports/PROV/catalog-v001.xml` |

The repositories were not fetched, pulled, switched, rebased, installed into, committed, pushed, or otherwise updated. Repository files and the SHAs above are the controlling evidence. In path citations below, `SSN/` and `PROV/` mean the two fixed repository roots.

### Inspection performed

The audit inventoried tracked and untracked files, file types, branches/tags already present locally, recent local history, all Makefiles and target declarations, `.github/workflows`, Python and shell tools, SPARQL files, mapping and editor ontologies, catalogs, vendored imports, examples/fixtures, maintained and historical reports, release files, README/metadata files, and dependency declarations. `rg`, `find`, `git ls-tree`, `git log`, `git tag`, `git diff`, `nl`, and `sed` were used to trace operational references and distinguish active behavior from snapshots or placeholders.

### Runtime commands run

Substantive runtime checks were:

```text
git branch --show-current
git rev-parse HEAD
git status --short

make -n -C src reason-edit test-edit all build-release SSSOM candidates \
  candidates-complex unmapped entailed-mappings deductive-diff prep-cco \
  count-prov-terms count-example-instances extract-imports \
  output-release-filepath output-release-name clean

python -c "from rdflib import Graph; Graph().parse(<ontology>, format='turtle')"
robot convert --input <PROV-release-or-editor-file> --output /tmp/<file>
robot convert --input <PROV-release-file> --format ttl --output /tmp/<file>
robot reason --catalog catalog-v001.xml --reasoner HermiT \
  --input <PROV-release-file> --output /tmp/<file>

python tools/run_validation_suite.py \
  --tmp-dir /tmp/ssn-prov-functional-parity-audit

make all ROBOT_FILE=/usr/local/bin/robot \
  "ROBOT=robot --catalog catalog-v001.xml"
# run separately in SSN/src/current-ssn-sosa and SSN/src/sosa-next
```

The installed runtime was ROBOT 1.9.7 and Java 22.0.2. PROV's Makefile would download ROBOT 1.9.5 if its local jar were absent (`PROV/src/Makefile:168-170`); no download was allowed or attempted. SSN's full suite took 51.08 seconds. Its two CI-track `all` targets each took 1.17 seconds with the system ROBOT override.

### Commands not run and limitations

- `make -C PROV/src reason-edit` and `test-edit` were not run. The editor imports six source ontologies that are absent from `PROV/src/catalog-v001.xml` (`PROV/src/prov-mappings-edit.ttl:20-25`), and ROBOT attempted network resolution during a safe conversion probe. Network use was prohibited.
- `make -C PROV/src all` was not run. Its dry run reached `No rule to make target 'mappings', needed by 'all'` (`PROV/src/Makefile:121`), in addition to the remote-import issue.
- PROV custom targets requiring the full editor closure (`SSSOM`, candidates, unmapped, entailed mappings, counts, and deductive diff) were not rerun because doing so faithfully requires the unresolved remote source imports. Their recipes and checked-in 2025 artifacts were inspected; the artifacts were treated as historical evidence only, not proof of reproducible current behavior. Simple candidate discovery and deductive diff therefore remain `UNVERIFIED`; complex candidate discovery is separately a `PROV PLACEHOLDER` because its query contains the defective `rdfs:subClassO` predicate.
- PROV `prep-cco` was not run because its configured `../MergedAllCoreOntology-v1.4-2023-04-07.ttl` input does not exist (`PROV/src/Makefile:102-106`).
- PROV `build-release`, `clean`, `extract-imports`, and report-writing targets were not run because they write/delete repository paths and were unnecessary for a report-only audit. `build-release` is expressly documented as inactive (`PROV/src/Makefile:119-121`; `PROV/README.md:87-90`).
- SSN `make check-coms` update mode and `--write-reports` were not run because `--check-only` performs the complete temporary candidate generation, SPARQL coverage, parse, closure, and HermiT transaction without rewriting maintained outputs. The focused tests exercised atomic replacement and rollback.
- GitHub branch-protection rules, required-check settings, hosted Actions runs, Zenodo content, and GitHub release assets are external state and were not queried. Related findings are `UNVERIFIED` where local evidence is insufficient.
- This is a repository-engineering audit, not a review of the substantive adequacy of either ontology's individual mapping decisions.

### End-state validation

- `git diff --check`: PASS in both repositories.
- SSN-to-BFO final status: only `?? reports/prov-functional-parity-audit.md`; no staged files.
- PROV-to-BFO final tracked state: unchanged; no staged files.
- No audit-created caches, Office lock files, temporary reasoner files, or generated build outputs remain in SSN-to-BFO.
- `PROV/src/imports/PROV/catalog-v001.xml` remains the same pre-existing untracked generated catalog observed at audit start. It is local comparison state, is not credited as an out-of-the-box PROV capability, and leaves any command dependent on it locally contingent or unverified. Removing it would conflict with the instruction that the comparison repository remain unchanged and that the report be the only permitted repository change. Consequently, the requested “no untracked catalog” end state could not be met without violating the stricter scope constraint.

## 3. Repository Capability Inventory

### PROV-to-BFO

- Three manually maintained root publication modules: BFO, CCO, and RO direct mappings (`PROV/prov-*-directmappings.ttl`), with labels, version IRIs, contributors, CC0 metadata, provenance, and per-axiom comments/SSSOM annotations.
- One imported editor graph (`PROV/src/prov-mappings-edit.ttl`) combining publication modules, PROV/PROV-extension ontologies, BFO/RO/CCO, and 15 canonical example files; example 4 is deliberately excluded with an explicit inconsistency note.
- ROBOT/Make recipes declare HermiT, query verification, report generation, SSSOM export, simple/complex superproperty candidates, unmapped terms, entailed mappings, deductive diff, counts, and RO subset extraction (`PROV/src/Makefile`). These are not uniformly operational: simple candidates and deductive diff were not reproduced from tracked inputs, and the complex candidate query is defective.
- Eight top-level SPARQL files included by the `test-edit` wildcard, one construct query for deductive diff, and one unintegrated PROV-DC example transform.
- A PR workflow that runs HermiT and ROBOT verify against the editor graph (`PROV/.github/workflows/test-mappings.yml`). Query violations do not fail because `config.FAIL_ON_TEST_FAILURES := false`.
- Vendored BFO, CCO, RO, examples, and an extracted RO module. The catalog resolves mapping modules, dependencies, and examples, but not the six PROV source ontology imports.
- Checked-in analysis artifacts last updated at commit `5731eaf` (2025-01-18), documentation diagrams/inconsistency notes, an example-usage ontology, CC0 `LICENSE`, and `CITATION.cff` with a Zenodo DOI.
- The default `all`, `prep-cco`, `reason-release`, `test-release`, `report-release`, `output-release-version`, and `explain-release` surfaces depend on undefined, missing, or normally absent inputs or contain no-op scaffolding; they are classified as placeholders rather than functioning capabilities.

### SSN-to-BFO

- `SSN/mappings/SSN2BFO-COMS.xlsx` is the sole editable authority. `SSN/SSN2BFO.ttl` is the generated authoritative publication, and `SSN/legacy/SSN2BFO-pre-COMS.ttl` is a frozen comparison baseline (`SSN/README.md:17-23`).
- A deterministic workbook generator with exact source/entity resolution, exact label fallback, Manchester intersections/unions/existentials, property chains, domain/range typing rows, duplicate checks, normalized-expression reporting, semantic legacy comparison, and SPARQL source coverage (`SSN/tools/generate_mapping_from_coms.py`).
- A transactional one-shot checker and SHA-256 watcher with temporary validation, freshness checks, backup/rollback, atomic replacement, last-success metadata, and failure logs (`SSN/tools/check_coms_mapping.py`; `SSN/tools/watch_coms_mapping.py`).
- A standard local suite that parses the publication, runs 22 generator/transaction tests, performs the full COMS check-only transaction, tests 11 source examples, runs ELK over 16 source/fixture graphs, runs full-closure HermiT, compiles Python, and runs `git diff --check` (`SSN/tools/run_validation_suite.py`).
- Fully local CCO, SOSA, SOSA Sampling, SSN, and SSN Systems inputs used to construct a 15,905-triple no-imports HermiT graph with two explicit source-axiom cleanups.
- Human-readable generation, source-coverage, and pre-COMS comparison reports; optional machine-readable transaction JSON; 44 mapped classes, 30 relation-mapped object properties, 17 properties covered only by typing rows, and zero uncovered source terms at the baseline.
- Two ROBOT/Make source-track scaffolds. The current and forthcoming release files/editor files are explicit placeholders. Their default CI behavior is ontology hygiene only, not validation of the COMS authority (`SSN/README.md:30-51`).
- A review-only BFO projection, current examples/fixtures, workflow scope checker, PR/merge helpers, and legacy diagnostics. No repository license, citation file, version tag, or rich ontology publication metadata is present.

## 4. Capability Matrix

Totals in section 1 count only the rows in this matrix. Similar names are not treated as proof; statuses reflect observed enforcement and runtime behavior.

| ID | Capability | PROV evidence | SSN evidence | Status | Material difference | Recommended action |
|---|---|---|---|---|---|---|
| AUTH-01 | Authoritative mapping source | Three root TTL files are edited directly; editor imports them (`PROV/README.md:87-90`; `PROV/src/prov-mappings-edit.ttl:14-16`). | Workbook is sole editable authority; root TTL is generated (`SSN/README.md:17-23`). | SSN STRONGER | SSN has one structured authority and separates the legacy snapshot. | Preserve COMS authority. |
| AUTH-02 | Unauthorized direct-edit detection | No release hash/freshness guard. | Candidate hash in report must match root; generated-file comment forbids edits (`SSN/tools/check_coms_mapping.py:300-320`). | SSN STRONGER | Direct TTL edits fail freshness. | Preserve. |
| AUTH-03 | Reproducibility/freshness | Version IRIs exist, but current BFO bytes differ from tag `v2025-01-19`; no check. | Workbook, generator, and root hashes are enforced; output is regenerated in a temporary transaction. | SSN STRONGER | SSN detects stale source, generator, and output. | Preserve. |
| AUTH-04 | Mapping rationale at source and publication | Per-axiom comments and SSSOM fields are in publication TTL. | `coms:Reasoning` remains in workbook and is deliberately not emitted (`SSN/reports/coms-generation-validation.md:131-136`). | PARTIAL | Rationale is authoritative but unavailable to publication consumers. | Consider a separate generated provenance artifact without weakening COMS. |
| MAP-01 | Production BFO direct mapping | `PROV/prov-bfo-directmappings.ttl` is the documented production file. | Root is mixed BFO/CCO; BFO-only projection is review-only and skips complex expressions; BFO release is a 9-line placeholder (`SSN/README.md:73-90`). | MISSING | No production BFO-only publication. | Promote a validated generated BFO projection only after defining complex-expression policy. |
| MAP-02 | Production CCO direct mapping | `PROV/prov-cco-directmappings.ttl`, importing the BFO mapping. | Authoritative root contains BFO/CCO targets and directly imports CCO. | PARITY | Packaging differs, but a usable CCO-dependent mapping publication exists. | Clarify product naming and dependency profile. |
| MAP-03 | Production RO direct mapping | `PROV/prov-ro-directmappings.ttl`. | No RO mapping source, generator path, import, or release. | UNVERIFIED | Applicability of a separate SSN/SOSA-to-RO product has not been established. | Perform a focused ontology-specific applicability review before any RO implementation. |
| MAP-04 | Source/version-specific tracks | PROV editor covers PROV-O plus AQ, Dictionary, Links, Inverses, and DC. | Current SSN/SOSA is the active authority; `sosa-next` is intentional lifecycle scaffolding with no stable authoritative next-version source mapping in scope. | NOT APPLICABLE | Active tracks are covered; completion of an inactive future track is not a current parity requirement. | Retain clear lifecycle-scaffold labeling; assess mappings only when a stable next source becomes authoritative. |
| MAP-05 | Release versus review boundary | Root releases vs `src/prov-mappings-edit.ttl`. | Root generated authority vs legacy, review-only projection, and placeholder tracks. | PARITY | Both distinguish publication from editor/review artifacts. | Keep terminology explicit. |
| MAP-06 | SSSOM export | Active `SSSOM` target and checked-in 76-row CSV; simple mappings only. | Per-track export targets query placeholder editors; no export from COMS/root. | PARTIAL | SSN columns are SSSOM-like, but no authoritative lossless-accounted export exists. | Generate from COMS only rows representable without semantic loss, plus an exclusions/accounting report for every omitted row; call it formal SSSOM only after pinned-spec conformance. |
| MAP-07 | Materialized entailed mapping artifact | `entailed-mappings` reasons and annotates a generated TTL; checked-in snapshot exists. | Equivalent target operates only on placeholder editors; root HermiT output is temporary validation data. | PARTIAL | No authoritative COMS-derived entailed review artifact. | Add an optional temporary/report artifact from root, not a second authority. |
| ONTO-01 | Deterministic ontology construction | Publication files are manual; optional release recipe uses date metadata. | Generator sorts/normalizes RDF and root hash is stable. | SSN STRONGER | SSN publication is reproducible from structured source. | Preserve deterministic serialization. |
| ONTO-02 | Rich ontology metadata | Labels, contributors, license, provenance, `seeAlso`, and version IRIs on all releases. | Root ontology has its IRI and imports only. | MISSING | Publication lacks basic descriptive/reuse metadata. | Generate metadata from maintained configuration/workbook fields. |
| ONTO-03 | Ontology and version IRIs | Stable ontology IRIs and `v2025-01-19` version IRIs, though BFO bytes changed after tag. | Stable ontology IRI; no version IRI/versionInfo. | PARTIAL | No SSN version identity. | Add version policy and generated version IRI before release. |
| ONTO-04 | Import/dependency packaging | BFO release import-free; CCO/RO import BFO mapping; editor carries dependencies. | Root imports SSN, Systems, Sampling, and CCO. | PARTIAL | SSN has one dependency-heavy product and no import-minimal direct module. | Document intended consumer profile; address through BFO/CCO release design. |
| ONTO-05 | Prefix and entity resolution | Manual prefixes; ROBOT accepts releases, but RDFLib rejects BFO's unbound `:` and CCO's multiline string. | Strict Turtle parses; direct CURIE then unique exact-label resolution; normalized forms reported. | SSN STRONGER | SSN is parser-portable and resolution failures are explicit. | Preserve; add cross-parser checks to PROV separately. |
| ONTO-06 | Generated-file notice/publication path | Files are manually edited and have no generated notice. | Root comment identifies workbook source and prohibits direct edits. | SSN STRONGER | Publication ownership is unambiguous. | Preserve. |
| DEP-01 | Pinned ontology dependency versions | Versioned BFO, RO, CCO and PROV IRIs; current CCO 2024-11-06. | CCO version IRI pinned; local SOSA/SSN bytes fixed but publication imports include unversioned W3C IRIs. | PARTIAL | Reproducible local bytes exist, but source version identity is weaker. | Record source file hashes/version IRIs in generated metadata. |
| DEP-02 | Vendored validation closure | BFO/CCO/RO/examples vendored; six PROV source ontologies remain remote. | All five closure inputs are local and explicitly loaded. | SSN STRONGER | SSN's active HermiT closure is offline-reproducible. | Preserve. |
| DEP-03 | Protégé/ROBOT catalogs | `PROV/src/catalog-v001.xml` maps releases, BFO/CCO/RO, and examples, not source PROV ontologies. | Active Python closure bypasses catalogs; root `imports/catalog-v001.xml` is empty and track catalogs point to placeholders. | PARTIAL | SSN command-line reproducibility is strong, but editor/catalog reuse is weak. | Add a maintained root catalog for publication imports without changing closure code. |
| DEP-04 | No mutable remote dependency during validation | Editor HermiT depends on remote W3C source imports. | Checker materializes local files and removes import triples. | SSN STRONGER | SSN validates fixed bytes only. | Preserve. |
| DEP-05 | Declared/bootstrapable tool dependencies | Make pins/downloads ROBOT 1.9.5; no general manifest. | Track Makefiles pin ROBOT 1.9.5, but active Python/ROBOT stack has no requirements/environment manifest. | PARTIAL | SSN's active pipeline depends on undeclared `rdflib`, `openpyxl`, and ROBOT. | Add a pinned environment/requirements declaration; do not auto-install during checks. |
| BUILD-01 | One-shot authoritative build/check | Default `all` is broken by undefined `mappings`; component targets exist. | `make check-coms` runs generation and complete transactional validation. | SSN STRONGER | SSN has a reliable one-shot authority command. | Preserve. |
| BUILD-02 | Recursive/module dispatch | Single PROV source pipeline. | `SSN/src/Makefile` dispatches two tracks and artifact families. | SSN STRONGER | SSN offers additional modular orchestration, though tracks are placeholders. | Do not confuse scaffold success with publication validation. |
| BUILD-03 | Clean target | Removes `src/build/artifacts` and an optional local release build. | Dispatcher cleans both track artifact directories. | PARITY | Both clean generated Make artifacts. | Keep publication/cache cleanup separate. |
| BUILD-04 | Simple candidate superproperty discovery | `candidates` declares a domain/range compatibility query and a checked-in TSV, but could not be reproduced from tracked/offline-resolvable inputs. | No authoritative equivalent. | UNVERIFIED | Historical output and a recipe do not establish current reproducibility. | Verify the PROV target from a clean tracked checkout before treating a corresponding SSN report as a confirmed parity gap. |
| BUILD-05 | Deductive source-ontology diff | `deductive-diff` declares a before/after source-entailment comparison and has a checked-in historical result, but was not reproducible in this audit. | No equivalent. | UNVERIFIED | A historical “Ontologies are identical” result and unexecuted target do not prove current functionality. | Verify the PROV target from a clean tracked checkout before deciding whether to port it. |
| BUILD-06 | Extract only referenced RO terms | `extract-imports` builds an RO subset for tractability. | No RO dependency/deliverable. | NOT APPLICABLE | Mechanism is specific to PROV's RO product; SSN's current dependencies are already locally materialized. | Revisit only if the ontology-specific review approves an RO product. |
| BUILD-07 | Source/example accounting | Dedicated count targets and TSVs. | Coverage report counts source terms; smoke/ELK reports count examples and expectations. | PARITY | Different reports provide materially equivalent accounting. | None. |
| BUILD-08 | Default `make -C src all` | Depends on undefined `mappings`; dry run fails. | No parity obligation to copy a broken aggregate. | PROV PLACEHOLDER | Advertised default is not operational. | Fix in PROV; do not emulate. |
| BUILD-09 | `prep-cco` | Configured input is absent. | No equivalent needed. | PROV PLACEHOLDER | Recipe cannot run from checkout. | Retire or repair in PROV. |
| BUILD-10 | `output-release-version` | Declared phony but has no recipe; implemented target is `output-release-name`. | Track targets expose release names/filepaths. | PROV PLACEHOLDER | Version-output surface is a typo/no-op. | Fix naming in PROV only. |
| VALID-01 | Strict RDF/Turtle parsing | ROBOT converts all releases; RDFLib fails BFO and CCO source syntax. | RDFLib parse is first standard-suite gate and passed. | SSN STRONGER | PROV depends on OWLAPI/Rio leniency; SSN is portable. | Keep strict parser gate. |
| VALID-02 | HermiT consistency | CI calls HermiT on editor; direct local release modules returned 0 in audit. Full editor run was offline-blocked. | Candidate and full local closure HermiT returned 0. | PARITY | Both implement HermiT consistency, although only SSN was fully reproduced locally. | Preserve; make PROV closure offline. |
| VALID-03 | Named unsatisfiable classes | No explicit count/set report. | Explicit `owl:Nothing` and named-unsat extraction; zero required. | SSN STRONGER | SSN fails satisfiability defects beyond global inconsistency. | Preserve. |
| VALID-04 | Explicit closure construction | Editor relies on OWL imports and remote resolution. | Six local graphs are merged explicitly; report records 15,905 triples. | SSN STRONGER | Inputs and graph size are auditable. | Preserve. |
| VALID-05 | Imported-axiom cleanup | No cleanup in editor reason target; individual removal only in artifact targets. | Removes all imports plus two documented SOSA simplicity blockers. | SSN STRONGER | Domain-specific cleanup is explicit and tested. | Preserve and keep documented. |
| VALID-06 | SPARQL validation gate | `test-edit` runs all top-level queries with `--fail-on-violation false`. | Coverage queries are part of generator success; malformed/unsupported rows are fatal. | SSN STRONGER | PROV query output is informational; SSN coverage is enforced. | Preserve. |
| VALID-07 | ELK validation | ELK appears only in inactive release-build rule. | 16 example/fixture graphs run through ELK and fail on reasoner/output/`owl:Nothing`/expectation errors. | SSN STRONGER | SSN has active reasoner diversity. | Preserve while documenting materialization limitations. |
| VALID-08 | Validation failure gates | HermiT fails CI; query/report thresholds are permissive. | Local suite short-circuits on every substantive failure. | SSN STRONGER | SSN local gate is broader and stricter. | Wire the same gate into CI (`CI-02`). |
| EXAMPLE-01 | Canonical example corpus | 16 local PROV files; 15 imported into editor. | 11 current SSN/SOSA examples plus five synthetic regression fixtures. | PARITY | Domain-adjusted example corpora exist and are exercised. | Keep source examples distinguished from fixtures. |
| EXAMPLE-02 | Full-DL example-data consistency | Editor HermiT graph includes the 15 examples. | Examples run ELK; HermiT closure excludes examples. | PARTIAL | SSN lacks HermiT consistency over example ABoxes. | Run HermiT separately per example by default with per-file diagnostics; merge only declared coexisting scenario groups, and add a controlled contradictory fixture. |
| EXAMPLE-03 | Expected entailments | PROV checks consistency but no explicit per-example target assertions. | 90 local direct/property-chain expectations checked; zero failures. | SSN STRONGER | SSN tests mapping behavior, not only consistency. | Preserve and improve ROBOT materialization observability. |
| EXAMPLE-04 | Negative/regression tests | No focused test harness. | 22 generator/transaction tests cover malformed targets, wrong kinds, duplicates, coverage classes, freshness, atomicity, and rollback. | SSN STRONGER | SSN has executable negative cases. | Preserve. |
| EXAMPLE-05 | Source-version example coverage | Current PROV-O/extensions represented; one known-bad source example excluded explicitly. | Current authoritative SSN/SOSA track has examples; `sosa-next/examples` is intentional lifecycle scaffolding for no stable active next-version source. | NOT APPLICABLE | Example completeness is assessed for active source tracks only. | Add next-version examples only when a stable next source and mapping authority enter scope. |
| QUERY-01 | Source class/property inventory | `count-prov-terms.rq` includes classes/object/functional properties but produces duplicate-type rows. | Maintained SPARQL returns exactly nondeprecated named source classes/object properties. | SSN STRONGER | SSN inventory semantics match the mapping scope precisely. | Preserve. |
| QUERY-02 | Unmapped-term detection | Entailment/inverse/property-chain/SWRL-aware query; target materializes HermiT first; CI does not fail on rows. | Direct spreadsheet coverage query, separate mapped/typing-only/blank/absent categories, zero uncovered, failing transaction. | SSN STRONGER | PROV query is semantically broader; SSN accounting and enforcement are stronger. | Consider inverse-aware expansion only if COMS gains inverse/SWRL predicates. |
| QUERY-03 | Simple domain/range mapping candidates | A dedicated simple query and checked-in TSV exist, but execution against a tracked/reproducible closure was not verified. | Domain/range rows are validated, but no candidate discovery. | UNVERIFIED | The PROV analysis is plausible but locally contingent; historical output is insufficient proof. | Verify PROV clean-checkout execution, then add a review-only local report if confirmed useful. |
| QUERY-04 | Unsupported/invalid mapping detection | No row schema; mapping predicates are manually authored. | Allowed predicates, class/property compatibility, exact resolution, Manchester/property-chain syntax, and contradictions are fatal. | SSN STRONGER | SSN enforces mapping-form methodology. | Preserve. |
| QUERY-05 | Automatic query execution/reporting | All eight top-level PROV queries run under `verify`; custom outputs are separate targets and checked-in snapshots can become stale. | Two authoritative coverage queries always run and reports are atomically maintained; track hygiene queries run in CI. | PARITY | PROV has more analyses; SSN has stronger freshness/enforcement for its active queries. | Add missing analyses without weakening the transaction. |
| QUERY-06 | PROV-DC creator transformation | `PROV/src/examples/prov-dc-creator.rq` is an unreferenced domain-specific example transform. | No counterpart. | NOT APPLICABLE | It demonstrates a PROV-DC conversion, not mapping-repository infrastructure. | None. |
| QUERY-07 | Complex domain/range candidate discovery | `candidate-superproperties-complex.rq` uses nonexistent `rdfs:subClassO`, so the declared analysis is materially defective. | No counterpart. | PROV PLACEHOLDER | A query file and historical TSV do not establish a correct current capability. | Correct and reproduce the PROV query before considering any SSN parity requirement. |
| COV-01 | Class coverage | Unmapped query plus empty 2025 CSV; no maintained current summary. | 44 mapped, zero unmapped, source query and report enforced. | SSN STRONGER | SSN count is current, categorized, and gating. | Preserve. |
| COV-02 | Object-property coverage | Query recognizes direct, inherited, inverse, chain, and SWRL routes. | 30 relation-mapped, 17 typing-only, zero uncovered; typing rows do not inflate mapped count. | SSN STRONGER | SSN has clearer accounting; PROV has broader entailment patterns. | Preserve classification. |
| COV-03 | Annotation/datatype-property scope | Scope statement/query targets classes and object properties. | Source query explicitly excludes annotation/datatype properties and individuals. | PARITY | Both intentionally scope coverage to classes/object properties. | Document any future extension separately. |
| COV-04 | Intentionally unmapped/deferred terms | No structured blank/deferred state; objective is complete coverage. | Blank mappings are supported and reported; current workbook has none. | SSN STRONGER | Deferral can be explicit without emitting axioms. | Preserve. |
| COV-05 | Human/machine-readable accounting | CSV/TSV artifacts. | Maintained Markdown plus transaction summary JSON and cache metadata. | PARITY | Both support machine and human review through different artifacts. | Consider maintaining a stable JSON summary for CI artifact use. |
| METHOD-01 | Formal methodology checks | Unmapped and candidate queries encode coverage/domain-range heuristics; non-failing in CI, and candidate reproducibility remains unverified. | Structural/schema/logic checks are strict, but no candidate-superproperty or deductive-impact methodology. | PARTIAL | Each covers a different subset of methodology, with some PROV analyses not yet reproducibly confirmed. | Verify PROV analyses first; add only confirmed, useful review checks. |
| METHOD-02 | Complex mapping expression support | Restrictions, unions, SWRL, and one property chain are manually encoded. | Manchester intersections/unions/existentials and property chains are generated; SWRL unsupported. | PARTIAL | SSN safely supports most class complexity but not rule mappings. | Decide whether a constrained rule representation is genuinely needed. |
| METHOD-03 | Mapping provenance/justification | Publication carries comments, labels, SKOS commentary, and manual-curation SSSOM export. | Workbook carries `coms:Reasoning`; generated ontology intentionally omits it. | PARTIAL | Source provenance exists but publication provenance does not. | Generate a companion provenance/report artifact if consumers need it. |
| METHOD-04 | Blank/deferred/excluded treatment | Known-bad example is commented out; no mapping-row state model. | Explicit blank rows are valid, nonblocking, reported, and not emitted. | SSN STRONGER | SSN makes nondecisions auditable. | Preserve. |
| CI-01 | Pull-request trigger | PRs to `main`. | PRs to `main`, `dev`, and `tests`; manual dispatch also available. | PARITY | Both have PR CI; trigger breadth differs. | Align branches with current governance. |
| CI-02 | Authoritative mapping validation in CI | HermiT runs on the actual editor importing root mapping modules. | Workflow runs placeholder current/sosa-next editors, not COMS/root. | MISSING | The authoritative SSN mapping can change without CI reasoning it. | Replace/add a job running `make check` or `python tools/run_validation_suite.py`. |
| CI-03 | Generated-artifact freshness in CI | Not applicable to manual PROV releases. | Local freshness gate exists but workflow never invokes it. | MISSING | Stale or directly edited root can pass hosted CI. | Run `check_coms_mapping.py --check-only` in CI. |
| CI-04 | Local/CI gate equivalence | CI uses the same `reason-edit`/`test-edit` components documented for local use. | Local `make check` is comprehensive; CI runs unrelated scaffold checks. | MISSING | Green CI does not mean the authoritative local gate passed. | Make CI call the canonical local command. |
| CI-05 | Required checks/branch protection | Not stored in repository. | Not stored in repository. | UNVERIFIED | Hosted protection state cannot be inferred from workflow YAML. | Verify in GitHub settings during release review. |
| RELEASE-01 | Release assembly | Root releases are manually maintained; optional builder is inactive. | Root is transactionally generated and validated, but target-specific release placeholders remain empty. | PARTIAL | SSN assembly is safer for one mixed product but incomplete for direct modules. | Keep root generation; define product set. |
| RELEASE-02 | Versioned artifacts and tags | Local tags and version IRIs exist; current BFO bytes postdate its version tag. | No tags/version IRIs/versionInfo. | MISSING | SSN cannot identify immutable release bytes. | Add semantic/date versioning and generate version IRIs. |
| RELEASE-03 | Changelog and checksums | Neither repository has a changelog/checksum manifest. | Same. | PARITY | PROV provides no capability to port. | Add later as a shared release improvement. |
| RELEASE-04 | Hosted release assets | Local PROV tags and Zenodo DOI are visible; hosted assets not inspected. | No local tags; hosted state not inspected. | UNVERIFIED | External release contents were outside fixed checkout evidence. | Verify manually without changing this audit. |
| RELEASE-05 | Validation before release | PR workflow reasons the actual editor, but query violations are informational. | Strong local gate exists, but CI does not run it. | PARTIAL | SSN is stronger locally and weaker at hosted enforcement. | Resolve `CI-02` before release. |
| RELEASE-06 | Separate production target modules | BFO, CCO, and RO root modules are documented production artifacts. | One mixed root artifact; four target-track files are placeholders. | MISSING | Completed consumer-selectable target-specific production profiles are absent. | Implement only products approved by product policy; do not assume RO applicability. |
| RELEASE-07 | Automated PROV release build | `build-release` exists, but README says TTL releases are not built and `all` omits it. | No obligation to mimic inactive automation. | PROV PLACEHOLDER | Recipe is scaffolding, not current release behavior. | Do not use as parity requirement. |
| FAIR-01 | README/usage instructions | Production files, examples, methods, testing, release, and citation documented. | Authority, commands, tracks, projection, and examples documented. | PARITY | Both provide operational entry points. | Tighten SSN release terminology after product decisions. |
| FAIR-02 | Repository license | CC0 `LICENSE`; ontology metadata repeats license. | No license file or ontology license predicate. | MISSING | Reuse terms are undefined. | Add approved license and generated ontology license metadata. |
| FAIR-03 | Citation metadata | `CITATION.cff`, article DOI, Zenodo DOI, ORCIDs. | README cites the article only. | MISSING | No machine-readable citation or repository DOI. | Add `CITATION.cff` and approved repository identifier. |
| FAIR-04 | Machine-readable ontology metadata | Labels, version IRIs, contributors, license, provenance, and links. | Only ontology IRI/imports. | MISSING | Publication is not self-describing. | Generate metadata; do not hand-edit root. |
| FAIR-05 | Methods/diagram/example documentation | Dedicated diagrams, inconsistency explanation, canonical examples, and example-usage ontology. | README, reports, example README/data; no equivalent methods diagrams or simple consumer ontology. | PARTIAL | Operational reports are strong; reusable explanatory material is thinner. | Add concise active methodology and usage examples. |
| FAIR-06 | Contributor metadata | Release TTL and citation list contributors. | No contributor metadata in publication or citation file. | MISSING | Authorship is not machine-readable. | Generate from a maintained metadata source. |
| SAFE-01 | Temporary generation before publication | Most PROV custom targets write directly to `src/build/artifacts`; releases manual. | Candidate and all reports are checked in a transaction directory first. | SSN STRONGER | Failed generation cannot partially publish. | Preserve. |
| SAFE-02 | Atomic replacement and rollback | None. | `os.replace` publication with backups and rollback after post-update failure; tested. | SSN STRONGER | Last root/report set is restored on failure. | Preserve. |
| SAFE-03 | Last-known-good/failure state | None. | Ignored `last-success.json` and detailed `last-failure.log`; watcher continues. | SSN STRONGER | Operators retain good artifacts and diagnostics. | Preserve. |
| SAFE-04 | Clean-tree/workflow scope checks | CI/Make do not inspect changed-file scope. | `git diff --check`, status targets, `workflow_check.py`, expected files, and report/mapping modes. | SSN STRONGER | Accidental artifacts and scope drift are surfaced. | Preserve; modernize mapping-change expected set separately. |
| SAFE-05 | Stale artifact detection | Checked-in analysis artifacts have no freshness metadata and are older than current release changes. | Source/generator/candidate hashes enforced; reports replaced together. | SSN STRONGER | Maintained output freshness is content-based. | Preserve. |
| SAFE-06 | Accidental artifact protection | `build/lib` ignored, but `src/build/artifacts` are tracked and generated catalog noise was present. | Build artifacts, caches, temp files, and lock-style outputs are ignored/cleaned; root catalogs are tracked intentionally. | SSN STRONGER | SSN has narrower artifact hygiene. | Keep final cleanup checks. |
| DEV-01 | Branch/contribution guidance | Local release/feature branches and PR workflow; no `CONTRIBUTING`. | Many review/mapping/validation branch conventions and helpers; no `CONTRIBUTING`. | PARTIAL | SSN practice is visible in refs/tools but not documented as policy. | Add concise contribution/branch guidance. |
| DEV-02 | PR/merge helpers | No helper scripts. | Dirty-tree guard, protected-branch refusal, human gate, PR helper, merge confirmation, post-merge check. | SSN STRONGER | SSN operationalizes review safety. | Preserve; review hard-coded `tests` base separately. |
| DEV-03 | Workflow scope checks | None. | `workflow_check.py` inventories staged/unstaged/untracked files and expected paths. | SSN STRONGER | Review scope is executable. | Preserve. |
| DEV-04 | Report-only versus mapping-change workflows | No distinction. | Explicit modes and Human Review Summary. | SSN STRONGER | Report-only audits can be constrained. | Preserve. |
| ADD-01 | SKOS mapping commentary | CCO mapping includes SKOS commentary. | No SKOS mapping output; rationale remains in workbook/report. | PARTIAL | Consumer-facing weak/related mappings are absent. | Decide whether report-only commentary is sufficient. |
| ADD-02 | SWRL rule mapping support | BFO/CCO modules use SWRL for conditional relation mappings. | COMS predicate language has no SWRL; one SPARQL rule file is unreferenced and not a publication mechanism. | MISSING | Intended future conditional mappings cannot yet be governed or generated; SWRL provides conditional entailments, not ordinary OWL equivalence. | When prioritized, govern rules in COMS or a companion source, generate a separately validated rule module if preferable, and require positive and negative inference tests. |
| ADD-03 | Deductive-impact regression artifact | `deductive-diff` and a checked-in historical “Ontologies are identical” snapshot exist, but current reproducibility was not established. | None. | UNVERIFIED | Historical output is not proof of a current regression capability. | Same clean-checkout verification as `BUILD-05`; port only if confirmed. |
| ADD-04 | Mapping diagrams and inconsistency explanation | `PROV/src/docs/Diagrams.md`, `Inconsistencies.md`, and six images. | Historical reports are extensive, but no concise active equivalent. | PARTIAL | Knowledge exists but is fragmented and often historical. | Create a small active methods/known-cleanups document. |
| ADD-05 | Consumer example-import ontology | `PROV/example-usage/example-ontology-full-imports.ttl` demonstrates integration. | Example data and tests exist, but no minimal consumer import ontology. | MISSING | Reusers lack an executable import example. | Add a small, versioned usage example after release packaging is settled. |
| PLACE-01 | `explain-release` target | Variable assignment exists, but only `explain-edit` depends on `explain`; target is a no-op. | No parity obligation. | PROV PLACEHOLDER | Not an operational PROV capability. | Fix or remove in PROV. |
| PLACE-02 | `reason-release` target | Delegates to HermiT over normally absent `src/prov-bfo-directmappings.ttl`. | No parity obligation to copy a target lacking its tracked input. | PROV PLACEHOLDER | It does not run from the audited checkout without first creating an inactive local release build. | Repair/document reproducible prerequisites in PROV before crediting it. |
| PLACE-03 | `test-release` target | Delegates to verify over normally absent `src/prov-bfo-directmappings.ttl`. | No parity obligation to copy a target lacking its tracked input. | PROV PLACEHOLDER | It is contingent on an inactive, normally absent release/build artifact. | Repair/document reproducible prerequisites in PROV before crediting it. |
| PLACE-04 | `report-release` target | Delegates to ROBOT report over normally absent `src/prov-bfo-directmappings.ttl`. | No parity obligation to copy a target lacking its tracked input. | PROV PLACEHOLDER | It is contingent on an inactive, normally absent release/build artifact. | Repair/document reproducible prerequisites in PROV before crediting it. |
| EXAMPLE-06 | PROV example 4 exclusion | Excluded because it is inconsistent with PROV-O itself (`PROV/src/prov-mappings-edit.ttl:39`). | No counterpart required. | NOT APPLICABLE | This is a source-dataset exception, not reusable infrastructure. | Document equivalent source exceptions only if encountered. |

## 5. Complete PROV Make-Target Crosswalk

`PROV/src/Makefile` is the only PROV Makefile. The table includes user-facing aliases, reusable targets, file targets, and broken prerequisites that affect observed behavior. Directory and ROBOT-jar creation rules are infrastructure, not separately counted as capabilities.

| PROV target | Actual behavior, prerequisites, outputs | SSN equivalent | Status |
|---|---|---|---|
| `SSSOM` | `robot relax` + `SSSOM-mappings.rq`; writes `src/build/artifacts/prov-bfo-mappings.sssom.csv`; requires editor/ROBOT. | Track `sssom-bfo`/`sssom-cco`, but they read placeholder editors. | PARTIAL |
| `candidates` | Declares a simple domain/range candidate query and TSV output, but was not reproduced because the tracked catalog omits source PROV imports. The checked-in TSV is historical evidence only. | None. | UNVERIFIED |
| `candidates-complex` | Declares a complex candidate query and TSV output. The query contains defective `rdfs:subClassO` at line 23. | None. | PROV PLACEHOLDER |
| `unmapped` | Removes individuals, HermiT-materializes selected axioms, runs `unmapped-terms.rq`; writes query output under artifacts. | COMS SPARQL coverage and maintained report. | SSN STRONGER |
| `entailed-mappings` | Removes individuals, HermiT-materializes five axiom families, merges three releases, removes external/import ontology axioms, annotates, writes TTL. | Placeholder-track equivalent only; root reasoned graph is temporary. | PARTIAL |
| `deductive-diff` | Declares mapped/source reasoning, PROV-only construction, and ROBOT diff, but was not reproduced from tracked inputs; its checked-in result is historical. | None. | UNVERIFIED |
| `prep-cco` | Removes individuals from a configured CCO v1.4 file. Configured input is absent. | Not needed for current local CCO closure. | PROV PLACEHOLDER |
| `count-prov-terms` | Runs term-count SELECT; writes `prov-count.tsv`. | COMS source coverage report. | PARITY |
| `count-example-instances` | Runs instance-count SELECT; writes TSV. | Smoke/ELK report counts. | PARITY |
| `all` | Depends on `reason-edit test-edit mappings`; `mappings` has no rule, so aggregate fails. | Root `make check` and track dispatcher `make -C src all`. | PROV PLACEHOLDER |
| `build-release` | Depends on file target `src/prov-bfo-directmappings.ttl`; omitted from `all`; documentation says releases are edited directly. | Root generated transaction. | PROV PLACEHOLDER |
| `reason-edit` | Sets editor input and delegates to `reason`. | Root full-closure HermiT plus placeholder track `reason-edit`. | SSN STRONGER |
| `reason-release` | Sets normally absent `src/prov-bfo-directmappings.ttl` input and delegates to `reason`; it cannot run from the audited checkout without the inactive build product. | Root HermiT via COMS checker. | PROV PLACEHOLDER |
| `test-edit` | Sets editor input and delegates to `verify`; all eight top-level queries, non-failing violations. | COMS coverage/generator checks; track hygiene verify. | SSN STRONGER |
| `test-release` | Sets normally absent local built-release input and delegates to `verify`; it cannot run from the audited checkout without the inactive build product. | Root check-only transaction. | PROV PLACEHOLDER |
| `report-edit` | ROBOT report to editor TSV with `fail-on none`. | Track `report-edit`; canonical COMS reports are richer. | PARITY |
| `report-release` | Declares a ROBOT report over the normally absent local built-release input. | No generic root ROBOT report; generated validation report exists. | PROV PLACEHOLDER |
| `explain-edit` | HermiT inconsistency explanation to repository-root-relative `inconsistency-explanation.md`. | Track explain targets; full suite reports reasoner output but no automatic explanation. | PARITY |
| `explain-release` | Only receives a target-specific variable; no dependency/recipe. | None required. | PROV PLACEHOLDER |
| `output-release-filepath` | Prints `prov-bfo-directmappings.ttl` (relative to `src`). | Track `output-release-filepaths`; root path is fixed. | PARITY |
| `output-release-name` | Prints timestamped release name. | Both track Makefiles print timestamped names. | PARITY |
| `output-release-version` | Declared `.PHONY` but no recipe; succeeds as no-op. | No need to copy. | PROV PLACEHOLDER |
| `clean` | Deletes `src/build/artifacts` and local built-release file after a nonempty-dir guard. | `make -C src clean` recursively deletes track artifacts. | PARITY |
| `prov-bfo-directmappings.ttl` file rule | Removes imports/individuals from editor, reasons with ELK, annotates date/version, writes under `src`; inactive. | COMS writes root authority after HermiT. | PROV PLACEHOLDER |
| `imports/RO-imports-extracted.txt` file rule | Removes old import line with `sed`, queries referenced RO IRIs, strips header; writes repo temp files during recipe. | Not applicable without RO target. | NOT APPLICABLE |
| `extract-imports` | ROBOT subset extraction from vendored full RO to maintained extracted TTL. | Not applicable to current dependency set. | NOT APPLICABLE |
| `reason` | Reusable ROBOT HermiT command over `TEST_INPUT`. | `test_full_sosa_closure_hermit.py`/generator HermiT. | PARITY |
| `explain` | Reusable ROBOT HermiT inconsistency explanation. Not declared phony. | Track explain targets only. | PARITY |
| `verify` | Reusable ROBOT verify over wildcard top-level queries; `fail-on-violation false`. | COMS SPARQL/generator checks fail transaction; track verify remains non-failing. | SSN STRONGER |
| `report` | Reusable ROBOT report; `fail-on none`, print 10. | Track report target and richer COMS reports. | PARITY |
| `mappings` | Referenced by `all`, never defined. | No equivalent needed. | PROV PLACEHOLDER |
| Required-directory rules | Create artifact/library/source/query/report paths; duplicate `build/artifacts` warning is emitted. | Equivalent track directory rules. | PARITY |
| `../build/lib/robot.jar` | Downloads ROBOT 1.9.5 via curl if missing. | Track Makefiles use the same pin/cache pattern; active COMS checker expects `robot` on PATH. | PARTIAL |

## 6. Validation and Reasoning Crosswalk

### PROV graph and criteria

`reason-edit` asks ROBOT/HermiT to load `PROV/src/prov-mappings-edit.ttl`. The editor imports three mapping modules; PROV-O, AQ, Dictionary, Links, Inverses, and DC; BFO core; the extracted RO subset; CCO; ten numbered examples (1-3 and 5-11), `other-examples`, and four extension examples. Example 4 is locally present but intentionally excluded because the source example conflicts with PROV-O's own domain/disjointness axioms.

The checked-in `PROV/src/catalog-v001.xml` resolves all mapping modules, BFO/CCO/RO, and all imported examples. It does **not** resolve the six PROV source ontologies. Therefore the exact editor closure is network-dependent. The untracked `PROV/src/imports/PROV/catalog-v001.xml` is local comparison state and is not credited as a tracked import-resolution capability. Direct release-module HermiT checks run during this audit with the tracked catalog returned 0 and produced zero named `owl:Nothing` subclasses/equivalences:

| Module | ROBOT/HermiT return | Reasoned triples | Named unsats observed |
|---|---:|---:|---:|
| `prov-bfo-directmappings.ttl` | 0 | 544 | 0 |
| `prov-cco-directmappings.ttl` | 0 | 556 | 0 |
| `prov-ro-directmappings.ttl` | 0 | 284 | 0 |

These are module checks, not substitutes for the unrun editor closure. ROBOT accepted and normalized all three publication files. RDFLib parsed RO (232 source triples) but rejected BFO at line 319 for an unbound default prefix and CCO at line 315 for a newline in a quoted string. ROBOT's normalized forms contained 9/4/1 subclass, 3/5/0 equivalent-class, 15/19/24 subproperty, and 0/1/0 property-chain axioms for BFO/CCO/RO respectively.

`test-edit` runs every `PROV/src/sparql/*.rq` query with ROBOT verify, but `config.FAIL_ON_TEST_FAILURES := false`; query rows are reports, not a gate. ROBOT report is similarly configured `fail-on none`. HermiT inconsistency remains the only material CI failure criterion visible in PROV.

### SSN graph and criteria

The authoritative candidate/full closure is explicitly built from:

```text
imports/cco.ttl
imports/sosa.ttl
imports/sosa-sampling.ttl
imports/ssn.ttl
imports/ssn-systems.ttl
SSN2BFO.ttl
```

All `owl:imports` triples are removed, as are:

```ttl
sosa:isSampleOf rdf:type owl:FunctionalProperty .
sosa:hasSample rdf:type owl:InverseFunctionalProperty .
```

The audit run parsed 1,117 generated mapping triples, built a 15,905-triple closure, returned 0 from HermiT, produced reasoned output, and found zero `owl:Nothing`/named unsatisfiable classes. The COMS report records 105 active axiom rows: 44 class mappings, 25 object-property mapping rows, 16 domain rows, 15 range rows, and five property chains.

The lightweight smoke test loaded CCO, SSN, SSN Systems, root mappings, and each of 11 source examples; all parsed/passed its RDFS-style and SampleRelationship checks. Its list of source property uses without a direct/chain mapping is informational and does not fail. The ELK test used the same mapping basis plus 11 source examples and five synthetic fixtures. All 16 reasoner runs passed with zero `owl:Nothing` entities; local deterministic checks passed six class, 80 property, and four chain expectations. ROBOT/ELK itself materialized none of those 90 expected ABox assertions, a limitation explicitly reported rather than hidden. The HermiT closure test does not include example ABoxes.

### Crosswalk conclusion

SSN is stronger for fixed local closure construction, strict parsing, explicit cleanup, named-unsat detection, reasoner diversity, and expected-entailment tests. PROV retains one material advantage: its intended editor HermiT graph includes canonical example ABoxes, giving a full-DL example consistency check when remote imports resolve. That is the basis for `EXAMPLE-02: PARTIAL`, not a request to copy PROV-specific examples.

## 7. SPARQL and Coverage Crosswalk

### Active PROV queries

All files directly under `PROV/src/sparql/` are automatically passed to `test-edit` by `QUERIES = $(wildcard ...)`; “automatic” below therefore means informational ROBOT verify unless a separate target is shown.

| Query | Purpose | Input | Output | Automatic? | SSN equivalent/gap |
|---|---|---|---|---|---|
| `SSSOM-mappings.rq` | Export simple direct mappings with manual-curation justification. | Editor graph, relaxed by dedicated target. | SSSOM CSV; 76 checked-in data rows. | Yes in verify; dedicated `SSSOM`. | COMS has structured rows but no authoritative export (`MAP-06`). |
| `candidate-superproperties.rq` | Find simple object-property candidates from domain/range hierarchy. | Editor closure whose source imports are not resolved by the tracked catalog. | Historical candidate TSV; six checked-in data rows. | Declared in verify and `candidates`, but current execution was not reproduced. | `UNVERIFIED` (`QUERY-03`); the query also contains `?otherdomain` case mismatch in one filter branch. |
| `candidate-superproperties-complex.rq` | Intended to include equivalent/union domain/range candidates. | Editor closure whose source imports are not resolved by the tracked catalog. | Historical candidate TSV; 202 checked-in data rows. | Declared in verify and `candidates-complex`, but materially defective. | `PROV PLACEHOLDER` (`QUERY-07`): nonexistent `rdfs:subClassO` prevents credit as a correct capability. |
| `count-example-instances.rq` | List/count blank or named individuals and types. | Editor graph with examples. | TSV; 311 checked-in data rows. | Yes; dedicated count target. | Smoke/ELK report counts. |
| `count-prov-terms.rq` | Inventory PROV class/object/functional terms. | Editor graph. | TSV; 157 checked-in data rows. | Yes; dedicated count target. | `source-classes-and-object-properties.rq` is more scope-specific. |
| `get-imported-terms.rq` | Select referenced RO IRIs for subset extraction. | Temporary editor without prior extracted import. | Text term list. | Yes in verify; file/extract targets. | Not applicable unless RO product is added. |
| `unmapped-terms.rq` | Find unmapped classes/properties after direct, transitive, inverse, chain, and SWRL checks. | HermiT-materialized editor for dedicated target. | Query output; checked-in CSV is empty. | Yes; dedicated `unmapped`. | COMS coverage is stricter/accounted but not inference/SWRL-aware. |
| `unsubsumed-object-properties.rq` | Find object properties without a superproperty in their defining ontology. | Editor graph. | Verify artifact only. | Yes through wildcard; no dedicated target. | No equivalent methodology report. |
| `construct/prov-triples.rq` | Construct only PROV-to-PROV triples for deductive diff. | Old/new reasoned graphs dependent on unresolved source imports. | Recipe declares two temporary TTLs and a diff; checked-in result is historical. | Only `deductive-diff`; current execution was not reproduced. | `UNVERIFIED` (`BUILD-05`, `ADD-03`). |

`PROV/src/examples/prov-dc-creator.rq` has no Make/workflow/documentation reference and is classified as an inactive, PROV-specific example, not an active quality-control query.

### Active SSN queries

| Query | Purpose | Input | Output | Automatic? | PROV equivalent/gap |
|---|---|---|---|---|---|
| `queries/source-classes-and-object-properties.rq` | Inventory nondeprecated named classes/object properties defined by four source ontologies. | Locally materialized source graph. | Generator coverage sets/report. | Always in COMS transaction. | More precise counterpart to `count-prov-terms.rq`. |
| `queries/unmapped-source-terms.rq` | Select uncovered terms from a generated coverage graph. | Coverage RDF graph encoding mapped, blank, typing-only, and absent states. | Maintained Markdown and summary JSON. | Always; uncovered terms fail generation. | Stronger enforcement than PROV's informational query. |
| `src/*/sparql/artifact-metadata.rq` | Detect wrong editor ontology IRI. | Placeholder editor. | ROBOT verify artifact. | Yes in track CI. | Scaffold hygiene only. |
| `src/*/sparql/no-template-leakage.rq` | Detect copied template IRIs. | Placeholder editor. | ROBOT verify artifact. | Yes in track CI. | Scaffold hygiene only. |
| `src/*/sparql/export/sssom-{bfo,cco}-mappings.rq` | Export simple track mappings by target namespace. | Placeholder editor. | CSV under ignored track build directory. | Dedicated targets only. | Not authoritative. |
| `src/*/sparql/report/unmapped-terms.rq` | Track-specific unmapped terms. | Placeholder editor. | CSV. | Dedicated target, deliberately disabled. | Not authoritative. |
| `src/current-ssn-sosa/sparql/construct/derive-bfo-from-cco.rq` | Conservatively project named CCO targets to BFO. | Root mapping + local CCO. | Review-only TTL. | Dedicated target. | Functional analogue to target-specific packaging, but incomplete. |
| `src/current-ssn-sosa/sparql/report/unprojectable-cco-targets.rq` | List skipped CCO targets. | Same merged graph. | CSV. | Dedicated target. | Makes projection loss explicit. |

`SSN/rules/ssn-hasproperty-conditional-mapping.rq` and generic `src/*/sparql/export/sssom-mappings.rq` files have no active tool/Make/workflow reference. They are not counted as implemented capabilities.

## 8. CI and Release Crosswalk

| Area | PROV behavior | SSN behavior | Conclusion |
|---|---|---|---|
| Trigger | PR to `main`. | PR to `main`, `dev`, `tests`; manual dispatch. | Trigger parity. |
| Mapping input under test | Actual editor imports all three root releases. | Placeholder editors/releases under `src/`; COMS workbook/root absent. | Immediate repository-control blocker in SSN. |
| Reasoning | HermiT `reason-edit`; job fails on command failure. | HermiT over placeholder editor in each track. | SSN CI does not prove authoritative consistency. |
| Queries | Eight top-level queries; `fail-on-violation false`. | Two hygiene queries per placeholder; `fail-on-violation false`. | Neither query workflow is a strong hosted gate; SSN local COMS gate is strong but omitted. |
| Freshness | Not applicable to manual release files; no version-tag freshness check. | Hash freshness exists locally but is absent from CI. | `CI-03: MISSING`. |
| Artifacts | Uploads `build/artifacts/`; path matches PROV source build. | Uploads `src/**/build/artifacts/`; placeholder outputs only. | SSN uploads no COMS validation report generated by the job. |
| Dependency cache | ROBOT jar cache, constant key. | Same constant-key pattern for track ROBOT jar. | Equivalent and weakly invalidated. |
| Local/CI equivalence | CI runs documented component targets. | CI omits canonical root validation. | `CI-04: MISSING`. |
| Release publication | Three root production TTLs; local tags; no automated assembly. | One generated root authority; target release files placeholders; no tags/version IRI. | SSN has safer generation but incomplete release engineering. |
| Release metadata | CC0, contributors, provenance, labels, version IRIs, citation/DOI. | None beyond ontology IRI/imports and generated comment. | Material FAIR/release gap. |

PROV's publication metadata is not fully fresh: `prov-bfo-directmappings.ttl` changed after `v2025-01-19` while retaining that version IRI. This does not erase the capability; it demonstrates why SSN should implement version metadata through its generator and enforce its relationship to immutable release bytes.

## 9. Relevant Gaps

### A. Immediate repository-control blockers

| IDs | Impact | Exact missing behavior | Smallest implementation | Likely files | Proposed validation |
|---|---|---|---|---|---|
| `CI-02`, `CI-03`, `CI-04`, `RELEASE-05` | A stale, directly edited, or logically invalid authoritative root could receive green hosted CI. | The workflow does not call COMS freshness, generator tests, candidate closure HermiT, or the canonical local gate. | Add one hosted job that runs `make check` against the COMS/root authority and preserves useful failure artifacts. | `.github/workflows/test-mappings.yml`; dependency declaration as needed | Current baseline passes; intentionally stale root, generator mismatch, malformed workbook fixture, and named-unsat fixture each fail. |

These four findings are the unequivocal immediate defect. They are one implementation package, not four independent projects.

### B. Blockers to claiming full functional parity

| IDs | Impact | Exact missing behavior | Smallest implementation | Likely files | Proposed validation |
|---|---|---|---|---|---|
| `MAP-01`, `RELEASE-06` | Consumers cannot select a production BFO-only mapping comparable to PROV's checked-in product set. | The BFO projection is review-only, skips complex expressions, and is not a production publication artifact. | Decide product and projection policy, then generate a validated BFO product transactionally with explicit accounting for unprojectable expressions. | Generator/checker, Makefile, product path, reports/tests/docs | Parse, HermiT, target-vocabulary audit, complete COMS-row accounting, freshness, atomic replacement, rollback. |
| `RELEASE-01`, `ONTO-04`, `RELEASE-06` | The mixed root is the only completed production dependency profile. | Consumer-selectable target-specific production packaging and import policy are incomplete. | Define which products are authoritative and how they import or project shared mappings; implement only the approved set. | Product policy, generator/checker, Makefile, README, tests | Per-product parse/import/closure/entailment tests and cross-product accounting. |

These gaps block a claim of complete PROV parity, but they do not make the current mixed authoritative `SSN2BFO.ttl` logically invalid. A separate RO product is not assumed: `MAP-03` remains `UNVERIFIED` pending an ontology-specific applicability review.

### C. Public-release governance and maturity gaps

| IDs | Impact | Exact missing behavior | Smallest implementation | Likely files | Proposed validation |
|---|---|---|---|---|---|
| `FAIR-02` | Public reuse terms are undefined and may block an approved official public release. | No repository license or generated ontology license statement. | Obtain an explicit license decision; add the approved license and reference it from generated metadata. | Governance record, `LICENSE`, metadata configuration/generator, README | Human approval plus exact license-reference assertions; this is not a generator-only decision. |
| `RELEASE-02`, `ONTO-03` | Published bytes lack an immutable release identity. | No tag/version policy, generated version IRI, or version info. | Approve a versioning policy and generate metadata from a maintained release parameter. | Policy/config, generator, root output, README/release process | Tag, artifact hash, version IRI, and version info must agree. |
| `FAIR-04`, `ONTO-02` | The ontology is not sufficiently self-describing for publication discovery and reuse. | Label, license, contributors, provenance, and publication links are absent. | Approve a metadata vocabulary/source and emit it deterministically through the generator. | Metadata config, generator/tests, README | RDF assertion tests, deterministic regeneration, freshness. |
| `FAIR-03`, `FAIR-06` | Citation and contributor discovery are weak. | No `CITATION.cff` or generated contributor metadata. | Add reviewed citation/contributor data after governance approval and feed publication fields through generation. | `CITATION.cff`, metadata config, generator, README | CFF validation when available plus RDF assertion tests. |

These findings concern public-release governance and maturity. They should not be described as though each were an immediate repository-control failure.

### High priority

| IDs | Impact | Exact missing behavior | Smallest implementation | Likely files | Proposed validation |
|---|---|---|---|---|---|
| `DEP-05` | A fresh environment lacks a declared reproducible Python/ROBOT stack for the authoritative gate. | No pinned/declarative active environment covers `rdflib`, `openpyxl`, ROBOT, and Java expectations. | Add a pinned dependency/environment declaration and setup documentation without auto-installing during checks. | `pyproject.toml`/requirements/environment file, README, CI | Clean declared environment runs compile, tests, and `make check`. |
| `EXAMPLE-02` | ELK may miss full-DL inconsistencies caused only with example ABoxes. | HermiT closure excludes examples. | Run HermiT separately for each example by default. Merge only explicitly declared scenario groups whose ABoxes are intended to coexist; never indiscriminately merge all examples. | New/extended validation tool, suite, report | Per-file diagnostics, declared-group tests, all current examples clean, and one controlled contradictory fixture fails. |
| `MAP-06` | Downstream mapping tools lack an authoritative, loss-accounted simple mapping export. | Existing SSSOM targets read placeholders rather than COMS and do not account for semantically complex rows. | Derive only mappings representable without semantic loss; put every other row in a companion exclusions/accounting report. | Generator/checker, export/report paths, tests/docs | Every COMS row appears in the export or exclusions report; exclusions record source term, COMS row ID, mapping type, authoritative expression, reason, and available rationale. |

The `MAP-06` derivative must not flatten restrictions, intersections/unions, property chains, domain/range typing patterns, or future SWRL rules into misleading simple rows. COMS remains the sole editable authority. The artifact should be called formal SSSOM only after conformance to a pinned SSSOM specification is validated.

### Medium priority

| IDs | Impact | Exact missing behavior | Smallest implementation | Likely files | Proposed validation |
|---|---|---|---|---|---|
| `AUTH-04`, `METHOD-03`, `ADD-01` | Publication consumers cannot inspect rationale and qualified/weak commentary. | `coms:Reasoning` is workbook/report-only. | Generate a companion provenance/justification report or annotation module without adding it to the core logical closure by default. | Generator/reports/tests/docs | Every published mapping traces to its source row and rationale; core semantic triples remain unchanged. |
| `DEP-03` | Protégé/editor use may resolve mutable remote imports even though the active Python closure is local. | No maintained root catalog maps all publication imports to fixed local files. | Add a maintained publication catalog without changing explicit closure construction. | `imports/catalog-v001.xml`, docs/tests | ROBOT/OWLAPI offline import load from tracked files. |
| `MAP-07` | No shareable COMS-derived reasoned review artifact exists. | Reasoned output is temporary validation data. | Add an optional generated review artifact, never a mapping authority or required release product. | Tool/Make/docs | Determinism, provenance, and HermiT parity with authoritative root. |
| `FAIR-05`, `DEV-01`, `ADD-04`, `ADD-05` | Methods, contribution rules, and consumer onboarding require reading historical reports or code. | No concise active methods/cleanup rationale, contribution guide, or minimal import example. | Add active methods and contribution guidance plus a small consumer-use ontology after product policy is settled. | `docs/`, `CONTRIBUTING.md`, `example-usage/`, README | Documentation review; parse example and check its expected entailments. |
| `ADD-02` | Conditional mapping cases cannot enter the governed generated pipeline. | COMS has no rule representation; the unreferenced SPARQL rule is not authority or publication. | When prioritized, define a COMS-governed or clearly governed companion rule source and generate a separately validated rule module if preferable. | Mapping policy/source, generator/module, tests/docs | Positive and negative inference tests, source-to-rule traceability, freshness, and core/module separation. |

SWRL expresses conditional mapping entailments, not ordinary `owl:equivalentClass` or `owl:equivalentProperty` equivalence. It is a planned methodology enhancement, not automatically a blocker for the next release unless that release explicitly scopes in the relevant conditional mappings.

### Unverified or applicability-dependent analyses

| IDs | Classification | Evidence issue | Next decision |
|---|---|---|---|
| `BUILD-04`, `QUERY-03` | Unverified PROV capability | Simple candidate discovery has a recipe and historical TSV, but was not executed against tracked/reproducible inputs. | Reproduce from a clean tracked PROV checkout; only then decide whether to implement a review-only SSN report. |
| `BUILD-05`, `ADD-03` | Unverified PROV capability | Deductive diff has a recipe and historical result, but current source closure could not be resolved offline. | Reproduce from a clean tracked PROV checkout before calling it a confirmed parity gap. |
| `MAP-03` | Ontology-specific applicability decision | PROV publishes RO mappings, but that does not establish that a separate SSN/SOSA-to-RO product is appropriate. | Conduct a focused RO applicability review before any workbook, import, generator, or product change. |

Complex candidate discovery is not in this verification queue: `QUERY-07` is a `PROV PLACEHOLDER` because `candidate-superproperties-complex.rq` currently uses defective `rdfs:subClassO`.

### Low priority shared improvements

| IDs | Impact | Smallest implementation | Proposed validation |
|---|---|---|---|
| `COV-05` | Machine-readable summary is transaction-local/ignored. | Optionally publish deterministic JSON after defining a consumer need and stable schema. | Hash freshness and schema test. |
| `RELEASE-03` | Neither repository provides change/checksum manifests. | Add changelog/checksums after version policy. | Verify checksums against immutable release bytes. |

### Consolidated work-package crosswalk

The matrix contains 99 findings, but findings are evidence units, not separate repository projects. The confirmed gaps consolidate into **13 distinct implementation packages**:

| Package | Capability IDs resolved together | Narrow deliverable |
|---|---|---|
| `IMP-01` Authoritative CI | `CI-02`, `CI-03`, `CI-04`, `RELEASE-05` | Hosted workflow runs the canonical COMS/root gate. |
| `IMP-02` Active environment | `DEP-05` | Pinned/declarative Python, ROBOT, and Java environment. |
| `IMP-03` Publication/version metadata | `ONTO-02`, `ONTO-03`, `FAIR-02`, `FAIR-04` | Deterministic generated metadata, including the approved license reference, after policy approval. |
| `IMP-04` Product packaging framework | `RELEASE-01`, `RELEASE-06`, `ONTO-04` | Governed transactional generation/validation for approved products. |
| `IMP-05` Production BFO-only product | `MAP-01` | Completed BFO product with projection/exclusion accounting. |
| `IMP-06` Per-example HermiT | `EXAMPLE-02` | Isolated full-DL checks, declared scenario groups, contradictory fixture. |
| `IMP-07` Loss-accounted SSSOM-compatible export | `MAP-06` | COMS-derived simple export plus complete exclusions report. |
| `IMP-08` Citation/contributor metadata | `FAIR-03`, `FAIR-06` | Reviewed CFF and generated contributor metadata. |
| `IMP-09` Methods, contribution, and reuse docs | `FAIR-05`, `DEV-01`, `ADD-04`, `ADD-05` | Active methods/cleanup note, contribution guide, consumer-use example. |
| `IMP-10` Mapping rationale/provenance | `AUTH-04`, `METHOD-03`, `ADD-01` | COMS-traceable companion rationale/provenance artifact. |
| `IMP-11` Publication catalog | `DEP-03` | Tracked offline catalog for publication imports. |
| `IMP-12` Optional reasoned review artifact | `MAP-07` | Non-authoritative COMS-derived reasoned review output. |
| `IMP-13` Governed rule support | `ADD-02` | Generated, traceable rule module with positive/negative tests when prioritized. |

Implementation depends on **6 policy/applicability decisions**, some of which share capability IDs with later code packages:

| Decision | Capability IDs | Required decision |
|---|---|---|
| `DEC-01` License | `FAIR-02` | Approve repository and ontology reuse terms. |
| `DEC-02` Product/import policy | `MAP-01`, `RELEASE-01`, `RELEASE-06`, `ONTO-04` | Define authoritative product set, projection rules, and import profiles. |
| `DEC-03` Version/metadata policy | `ONTO-02`, `ONTO-03`, `FAIR-04` | Define version identifiers, tags, metadata source, and publication fields. |
| `DEC-04` Rationale publication policy | `AUTH-04`, `METHOD-03`, `ADD-01` | Choose report versus annotation module and its logical status. |
| `DEC-05` RO applicability | `MAP-03` | Decide whether any separate SSN/SOSA-to-RO product is ontology-appropriate. |
| `DEC-06` Rule governance | `ADD-02` | Define rule source, module boundary, validation, and release scope. |

There are **2 unverified PROV capability packages**, neither yet a confirmed SSN implementation obligation:

| Verification | Capability IDs | Confirmation required |
|---|---|---|
| `VER-01` Simple candidate discovery | `BUILD-04`, `QUERY-03` | Execute successfully from a clean checkout using tracked or explicitly documented reproducible inputs. |
| `VER-02` Deductive diff | `BUILD-05`, `ADD-03` | Reproduce the current before/after analysis from a clean tracked checkout. |

## 10. Capabilities Correctly Not Ported

### NOT APPLICABLE

- `MAP-04`: current SSN/SOSA is the active authoritative source track. `sosa-next` is intentional lifecycle scaffolding, and no stable authoritative next-version mapping is presently in scope. Structural multi-track support is separately credited as `BUILD-02: SSN STRONGER`.
- `BUILD-06`: PROV's referenced-RO subset extraction exists because PROV publishes an RO mapping and wants a tractable editor closure. SSN's current authoritative product does not import RO and fully materializes its active inputs locally. The mechanism becomes applicable only if an ontology-specific review approves an RO deliverable; that applicability remains `MAP-03: UNVERIFIED`.
- `EXAMPLE-05`: the active SSN/SOSA track has examples. An example corpus is not required for the inactive `sosa-next` lifecycle scaffold before a stable source and authoritative mappings exist.
- `QUERY-06`: `prov-dc-creator.rq` is a PROV-DC-specific example transformation with no operational references. It is not a general mapping QA facility.
- `EXAMPLE-06`: exclusion of PROV example 4 is a defensible source-data exception documented inline. SSN should not manufacture an analogous exclusion; it should document one only if its own source examples require it.

### PROV PLACEHOLDER

- `BUILD-08`: default `all` cannot complete because `mappings` has no rule.
- `BUILD-09`: `prep-cco` names a missing CCO v1.4 input.
- `BUILD-10`: `output-release-version` is declared but has no recipe; `output-release-name` is the actual implementation.
- `QUERY-07`: complex candidate discovery uses defective `rdfs:subClassO`; its historical TSV does not make the query materially correct or reproducible.
- `RELEASE-07`: `build-release` and its file rule exist, but the Makefile and README explicitly say releases are edited directly and omit the target from `all`.
- `PLACE-01`: `explain-release` receives a variable but never delegates to `explain`.
- `PLACE-02`, `PLACE-03`, `PLACE-04`: `reason-release`, `test-release`, and `report-release` depend on the normally absent `PROV/src/prov-bfo-directmappings.ttl` build input. They were not operational from the audited checkout using tracked or explicitly documented reproducible inputs.

These surfaces are not parity requirements. They also must not be used as evidence of a superior functioning PROV release pipeline. This does not discount the genuinely existing checked-in PROV root production mapping artifacts, which are assessed separately.

## 11. SSN-to-BFO Capabilities Beyond PROV

- Single COMS authority with exact four-column schema, explicit blank mappings, exact label-to-IRI resolution, and class/property predicate compatibility.
- Deterministic Manchester parsing/serialization with normalized expression and RDF/OWL forms visible per row.
- Separate accounting for relation mappings versus domain/range typing-only coverage; complete current 44-class/47-property source inventory.
- Temporary end-to-end generation followed by parse, SPARQL, HermiT, named-unsat, report-presence, hash, and whitespace checks before atomic publication.
- Backup/rollback of the root ontology and all maintained reports, plus last-success and failure-log state.
- SHA-256 watcher with startup check, debounce, duplicate suppression, and failure recovery.
- Frozen pre-COMS comparison baseline and semantic comparison that does not force legacy reproduction.
- Explicit full local closure construction and documented removal of the two SOSA sample simplicity blockers.
- ELK plus local ABox expectation checks for direct class/property and named property-chain mappings.
- Focused negative tests for malformed expressions, wrong subject kinds, duplicate domain/range rows, coverage classification, freshness, root authority, temporary validation order, atomic replacement, and rollback.
- Executable human workflow scope checks, report-only/mapping-change modes, expected-file review, PR dirty-tree protection, and a typed human merge confirmation.

Parity work must not weaken any of these controls. In particular, no new release product should bypass COMS, write before validation, omit freshness, or make legacy equality a gate.

## 12. Recommended Implementation Sequence

1. **Authoritative hosted CI gate**: make the workflow run the canonical nonmutating COMS/root suite and upload useful temporary failure reports (`IMP-01`).
2. **Approved repository license**: obtain the governance decision before adding license files or ontology assertions (`DEC-01`).
3. **Pinned/declarative active dependency environment**: declare Python, ROBOT, and Java requirements used by the authoritative gate (`IMP-02`).
4. **Publication-product and import-policy decision**: define authoritative products, projection semantics, and import profiles without presupposing an RO product (`DEC-02`).
5. **Versioning and generated metadata policy**: define tag/version-IRI relationships and maintained metadata sources (`DEC-03`).
6. **Production BFO-only product**: generate, account for, validate, and publish the approved BFO product transactionally (`IMP-04`, `IMP-05`).
7. **Per-example HermiT validation**: reason over each example independently by default; merge only explicitly declared coexisting scenarios and retain per-file diagnostics (`IMP-06`).
8. **Verified simple candidate-property reporting**: first reproduce PROV's simple target from tracked inputs, then implement a review-only SSN report if confirmed (`VER-01`).
9. **Deductive-diff verification**: reproduce PROV from a clean tracked checkout before deciding whether any SSN port is warranted (`VER-02`).
10. **COMS-derived lossless SSSOM-compatible export**: emit only losslessly representable rows and a complete exclusions/accounting report; validate pinned-spec conformance before using the formal SSSOM label (`IMP-07`).
11. **Citation, contributor, methods, contribution, and consumer-use material**: implement reviewed publication metadata and active reuse guidance (`IMP-08`, `IMP-09`, with `DEC-04`/`IMP-10` where rationale publication is approved).
12. **Separate RO-product applicability review**: decide ontology-specific relevance before any RO workbook, import, or product implementation (`DEC-05`).
13. **Governed SWRL/rule-mapping design and implementation when prioritized**: define authority/module policy first, then generate and validate conditional rules with positive and negative tests (`DEC-06`, `IMP-13`).

Each branch should remain narrow and should avoid mapping-content changes unless its stated purpose is a separately reviewed mapping decision. RO implementation does not precede its applicability review. SWRL is not required for the next release unless that release scope explicitly includes conditional mappings.

## 13. Final Parity Checklist

- [ ] Hosted CI runs the authoritative COMS/root validation command.
- [ ] CI fails on stale workbook/generator/root hashes and missing maintained outputs.
- [ ] CI HermiT result is 0 with zero named unsatisfiable classes.
- [ ] A production BFO-only artifact exists or is explicitly ruled out with a defensible scope decision.
- [ ] RO applicability receives a focused ontology-specific review; implementation occurs only if approved.
- [ ] Consumer-selectable publication products and import policies are documented.
- [ ] Root and release artifacts carry generated label, version IRI, license, contributor, and provenance metadata.
- [ ] Repository has an approved license and machine-readable citation metadata.
- [ ] Release tags/version IRIs identify exact immutable bytes.
- [ ] PROV simple candidate discovery is reproduced from tracked inputs; if confirmed and adopted, SSN provides a review-only local report.
- [ ] PROV deductive diff is reproduced from a clean tracked checkout before any SSN port decision.
- [ ] Each current source example receives a separate HermiT consistency check by default, with merged checks limited to declared coexisting scenarios and a controlled contradictory fixture.
- [ ] Direct/property-chain expected entailments remain covered and passing.
- [ ] COMS-derived SSSOM-compatible export includes only losslessly representable mappings; every excluded row is accounted for, and formal SSSOM naming follows pinned-spec validation.
- [ ] All source classes and object properties remain accounted for, with mapping and typing-only rows distinguished.
- [ ] Any rationale/provenance export remains traceable to COMS and does not alter core semantics.
- [ ] Generation remains temporary, atomic, rollback-capable, and freshness-checked.
- [ ] Local validation and hosted CI invoke the same authoritative gate.
- [ ] No placeholder track is represented as a completed release.
- [ ] Inactive `sosa-next` lifecycle scaffolding is not treated as a missing active mapping/example track.
- [ ] Conditional SWRL/rule mappings, if release-scoped, are governed, generated, modular where appropriate, and tested positively and negatively.
- [ ] No historical report or legacy ontology is promoted back to mapping authority.
