# COMS Automatic Validation Setup

## Watched Input

The watcher monitors only `mappings/SSN2BFO-COMS.xlsx`. It compares SHA-256 content hashes, so modification-time changes without byte changes do not trigger duplicate checks. Excel lock files such as `mappings/~$SSN2BFO-COMS.xlsx` are not watched.

## Start And Stop

Start the watcher from the repository root:

```bash
make watch-coms
```

The watcher runs one check immediately at startup, polls approximately once per second, and waits until a changed workbook hash has remained stable for at least 1.5 seconds before checking it. Press `Ctrl+C` to stop it cleanly.

The watcher must remain running to react immediately to workbook saves. It continues after a failed check and waits for the next distinct workbook content hash.

## Run Once

Run the complete quality pipeline once and atomically update maintained outputs:

```bash
make check-coms
```

Equivalent direct commands are:

```bash
python tools/check_coms_mapping.py
python tools/check_coms_mapping.py --update
```

The default mode is `--update`. For a non-mutating freshness and quality gate, use:

```bash
python tools/check_coms_mapping.py --check-only
```

`--check-only` fails when the workbook hash, generator hash, candidate hash, maintained reports, or regenerated semantic products do not match. It does not rewrite tracked artifacts. The ordinary validation suite invokes this mode.

Current local status is available with:

```bash
make coms-status
```

## Checks Performed

Each complete check:

1. Opens the workbook and records its SHA-256.
2. Compiles `tools/generate_mapping_from_coms.py`.
3. Runs the existing generator against temporary outputs.
4. Uses the generator's established validation for allowed predicates, source and target resolution, class/property compatibility, exact label-to-IRI resolution, Manchester expressions, property chains, duplicates, contradictions, and explicit blank mappings.
5. Runs the maintained SPARQL source inventory and unmapped-term coverage queries.
6. Parses the temporary generated candidate.
7. Builds the full local candidate closure from CCO, SOSA, SOSA Sampling, SSN, SSN Systems, and the generated candidate.
8. Applies the established import and SOSA functional/inverse-functional cleanup.
9. Runs HermiT and requires zero `owl:Nothing` and zero unexpected named unsatisfiable classes.
10. Requires all generated reports and validates hash-based source metadata.
11. Runs `git diff --check`.

The generated validation report records the workbook SHA-256, generator-file SHA-256, UTC generation timestamp, and generated-candidate SHA-256. Freshness never relies on timestamps alone.

## Last-Known-Good Outputs

Generation and validation happen under `.cache/coms/`. The maintained files are replaced only after all temporary checks pass:

- `generated/SSN2BFO-from-COMS.ttl`
- `reports/coms-generation-validation.md`
- `reports/coms-source-term-coverage.md`
- `reports/coms-generated-vs-current-mapping-diff.md`

Each replacement is atomic. If any check fails, the maintained last-known-good files remain unchanged. A post-replacement whitespace failure also triggers rollback from temporary backups.

The last successful result is stored in `.cache/coms/last-success.json`. Detailed failure output is written to `.cache/coms/last-failure.log`. The `.cache/coms/` directory is ignored and must not be committed.

## Enforcement

`make watch-coms` provides immediate local feedback while the workbook is being edited. `make check-coms` remains the manual, pre-PR, and CI enforcement command. `python tools/run_validation_suite.py` also runs the non-mutating `--check-only` gate so stale or invalid COMS artifacts cannot pass ordinary repository validation.
