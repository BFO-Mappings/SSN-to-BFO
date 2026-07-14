#!/usr/bin/env python3
"""Atomically validate and refresh the spreadsheet-driven COMS candidate.

The default mode is ``--update``: generate and validate all products in a
temporary directory, then replace maintained outputs only after every check
passes. ``--check-only`` performs the same validation without rewriting
maintained outputs and fails when they are stale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

try:
    import openpyxl
except ModuleNotFoundError:  # pragma: no cover - runtime dependency guard
    openpyxl = None

try:
    from rdflib import Graph
except ModuleNotFoundError:  # pragma: no cover - runtime dependency guard
    Graph = None


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"
GENERATOR = REPO_ROOT / "tools/generate_mapping_from_coms.py"
CACHE_DIR = REPO_ROOT / ".cache/coms"
LAST_SUCCESS = CACHE_DIR / "last-success.json"
LAST_FAILURE = CACHE_DIR / "last-failure.log"

MAINTAINED_OUTPUTS = {
    "candidate": REPO_ROOT / "generated/SSN2BFO-from-COMS.ttl",
    "generation_report": REPO_ROOT / "reports/coms-generation-validation.md",
    "coverage_report": REPO_ROOT / "reports/coms-source-term-coverage.md",
    "diff_report": REPO_ROOT / "reports/coms-generated-vs-current-mapping-diff.md",
}

METADATA_LABELS = {
    "workbook SHA-256": "workbook_sha256",
    "generator SHA-256": "generator_sha256",
    "generation timestamp (UTC)": "generation_timestamp",
    "generated candidate SHA-256": "generated_candidate_sha256",
}


class CheckFailure(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def emit(message: str, log: list[str]) -> None:
    print(message, flush=True)
    log.append(message)


def verify_workbook(log: list[str]) -> str:
    emit("[1/11] Verifying workbook exists and opens", log)
    if not WORKBOOK.is_file():
        raise CheckFailure(f"missing workbook: {relative(WORKBOOK)}")
    if openpyxl is None:
        raise CheckFailure("missing dependency: openpyxl is required to inspect the COMS workbook")
    try:
        workbook = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=False)
        sheet_names = workbook.sheetnames
        workbook.close()
    except Exception as exc:
        raise CheckFailure(f"workbook cannot be opened: {type(exc).__name__}: {exc}") from exc
    if not sheet_names:
        raise CheckFailure("workbook contains no worksheets")
    workbook_hash = sha256_file(WORKBOOK)
    emit(f"Workbook worksheets: {', '.join(sheet_names)}", log)
    emit(f"Workbook SHA-256: {workbook_hash}", log)
    return workbook_hash


def compile_generator(log: list[str]) -> str:
    emit("[2/11] Compiling COMS generator", log)
    try:
        py_compile.compile(str(GENERATOR), doraise=True)
    except py_compile.PyCompileError as exc:
        raise CheckFailure(f"generator compile failed: {exc.msg}") from exc
    generator_hash = sha256_file(GENERATOR)
    emit(f"Generator SHA-256: {generator_hash}", log)
    return generator_hash


def run_command(label: str, command: list[str], log: list[str]) -> subprocess.CompletedProcess[str]:
    emit(label, log)
    emit("$ " + " ".join(command), log)
    proc = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.stdout:
        for line in proc.stdout.rstrip().splitlines():
            emit(line, log)
    if proc.stderr:
        for line in proc.stderr.rstrip().splitlines():
            emit(line, log)
    if proc.returncode != 0:
        raise CheckFailure(f"{label} failed with return code {proc.returncode}")
    return proc


def transaction_paths(transaction_dir: Path) -> dict[str, Path]:
    return {
        "candidate": transaction_dir / "generated/SSN2BFO-from-COMS.ttl",
        "generation_report": transaction_dir / "reports/coms-generation-validation.md",
        "coverage_report": transaction_dir / "reports/coms-source-term-coverage.md",
        "diff_report": transaction_dir / "reports/coms-generated-vs-current-mapping-diff.md",
        "summary": transaction_dir / "summary.json",
        "hermit": transaction_dir / "hermit",
    }


def run_generator(paths: dict[str, Path], log: list[str]) -> None:
    emit("[3/11] Running generator and spreadsheet-row validation in a temporary transaction", log)
    command = [
        sys.executable,
        relative(GENERATOR),
        "--input",
        relative(WORKBOOK),
        "--output",
        str(paths["candidate"]),
        "--report",
        str(paths["generation_report"]),
        "--coverage-report",
        str(paths["coverage_report"]),
        "--diff-report",
        str(paths["diff_report"]),
        "--tmp-dir",
        str(paths["hermit"]),
        "--report-workbook-path",
        relative(WORKBOOK),
        "--report-output-path",
        relative(MAINTAINED_OUTPUTS["candidate"]),
        "--summary-json",
        str(paths["summary"]),
    ]
    try:
        run_command("COMS generator", command, log)
    except CheckFailure:
        if paths["generation_report"].is_file():
            emit("--- temporary generation report ---", log)
            for line in paths["generation_report"].read_text(encoding="utf-8").splitlines():
                emit(line, log)
        raise


def load_summary(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckFailure(f"cannot read generator summary {path}: {exc}") from exc


def validate_temporary_outputs(
    paths: dict[str, Path],
    workbook_hash: str,
    generator_hash: str,
    log: list[str],
) -> dict[str, object]:
    emit("[4/11] Confirming row validation completed without malformed or unresolved mappings", log)
    required = [*MAINTAINED_OUTPUTS, "summary"]
    missing = [name for name in required if not paths[name].is_file() or paths[name].stat().st_size == 0]
    if missing:
        raise CheckFailure("missing required temporary outputs: " + ", ".join(missing))

    summary = load_summary(paths["summary"])
    if summary.get("status") != "PASS":
        raise CheckFailure(f"generator summary status is {summary.get('status')!r}, expected 'PASS'")
    if summary.get("workbook_sha256") != workbook_hash:
        raise CheckFailure("generator summary workbook hash does not match the checked input")
    if summary.get("generator_sha256") != generator_hash:
        raise CheckFailure("generator summary generator hash does not match the compiled generator")

    emit("[5/11] Confirming maintained SPARQL source-term coverage checks ran", log)
    coverage = summary.get("source_term_coverage")
    if not isinstance(coverage, dict):
        raise CheckFailure("generator summary is missing source-term coverage results")
    if not isinstance(coverage.get("query_source_count"), int) or coverage["query_source_count"] <= 0:
        raise CheckFailure("source-term coverage query returned no source terms")
    if not isinstance(coverage.get("query_unmapped_count"), int):
        raise CheckFailure("unmapped-source-term query count is missing")
    emit(
        "Coverage query: PASS "
        f"({coverage['query_source_count']} source terms; {coverage['query_unmapped_count']} unmapped)",
        log,
    )

    emit("[6/11] Parsing temporary generated candidate TTL", log)
    if Graph is None:
        raise CheckFailure("missing dependency: rdflib is required to parse the generated candidate")
    graph = Graph()
    try:
        graph.parse(paths["candidate"], format="turtle")
    except Exception as exc:
        raise CheckFailure(f"generated candidate parse failed: {type(exc).__name__}: {exc}") from exc
    expected_triples = summary.get("generated_ontology_triple_count")
    if expected_triples != len(graph):
        raise CheckFailure(
            f"generated triple-count mismatch: parsed {len(graph)}, summary recorded {expected_triples}"
        )
    candidate_hash = sha256_file(paths["candidate"])
    if summary.get("generated_candidate_sha256") != candidate_hash:
        raise CheckFailure("generated candidate hash does not match generator summary")
    emit(f"Generated candidate parse: PASS ({len(graph)} triples)", log)

    emit("[7-9/11] Confirming candidate closure cleanup and HermiT result", log)
    if summary.get("hermit_return_code") != 0 or summary.get("hermit_result") != "PASS":
        raise CheckFailure(
            f"candidate HermiT failed: return={summary.get('hermit_return_code')}, "
            f"result={summary.get('hermit_result')}"
        )
    if summary.get("owl_nothing_count") != 0:
        raise CheckFailure(f"candidate closure has owl:Nothing count {summary.get('owl_nothing_count')}")
    if summary.get("named_unsat_count") != 0 or summary.get("named_unsat_set"):
        raise CheckFailure(f"candidate closure has named unsatisfiable classes: {summary.get('named_unsat_set')}")
    emit(
        "Candidate HermiT: PASS "
        f"({summary.get('candidate_closure_triple_count')} closure triples; no named unsats)",
        log,
    )

    emit("[10/11] Confirming required reports and freshness metadata", log)
    metadata = read_report_metadata(paths["generation_report"])
    expected_metadata = {
        "workbook_sha256": workbook_hash,
        "generator_sha256": generator_hash,
        "generated_candidate_sha256": candidate_hash,
    }
    for key, expected in expected_metadata.items():
        if metadata.get(key) != expected:
            raise CheckFailure(f"temporary generation report {key} mismatch")
    if not metadata.get("generation_timestamp"):
        raise CheckFailure("temporary generation report lacks generation timestamp")
    for path in (paths["generation_report"], paths["coverage_report"], paths["diff_report"]):
        assert_no_trailing_whitespace(path)
    return summary


def read_report_metadata(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2:
            continue
        key = METADATA_LABELS.get(cells[0])
        if key:
            metadata[key] = cells[1]
    return metadata


def assert_no_trailing_whitespace(path: Path) -> None:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.rstrip(" \t") != line:
            raise CheckFailure(f"trailing whitespace in temporary output {path}:{number}")


def freshness_errors(workbook_hash: str, generator_hash: str) -> list[str]:
    errors: list[str] = []
    for name, path in MAINTAINED_OUTPUTS.items():
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing required maintained output: {relative(path)}")
    if errors:
        return errors

    metadata = read_report_metadata(MAINTAINED_OUTPUTS["generation_report"])
    for key in METADATA_LABELS.values():
        if key not in metadata:
            errors.append(f"generation report is missing source metadata: {key}")
    if metadata.get("workbook_sha256") != workbook_hash:
        errors.append("workbook hash differs from the generated report")
    if metadata.get("generator_sha256") != generator_hash:
        errors.append("generator hash differs from the generated report")
    candidate_hash = sha256_file(MAINTAINED_OUTPUTS["candidate"])
    if metadata.get("generated_candidate_sha256") != candidate_hash:
        errors.append("generated candidate hash differs from the generated report")
    return errors


def normalized_generation_report(path: Path) -> str:
    dynamic_prefixes = ("| generation timestamp (UTC) |", "- Runtime seconds:")
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not line.startswith(dynamic_prefixes)
    ]
    return "\n".join(lines)


def output_differences(paths: dict[str, Path]) -> list[str]:
    differences: list[str] = []
    for name in ("candidate", "coverage_report", "diff_report"):
        current = MAINTAINED_OUTPUTS[name]
        if not current.is_file() or current.read_bytes() != paths[name].read_bytes():
            differences.append(name)
    current_report = MAINTAINED_OUTPUTS["generation_report"]
    if (
        not current_report.is_file()
        or normalized_generation_report(current_report)
        != normalized_generation_report(paths["generation_report"])
    ):
        differences.append("generation_report")
    return differences


def git_diff_check(log: list[str], label: str) -> None:
    emit("[11/11] Running git diff --check", log)
    run_command(label, ["git", "diff", "--check"], log)


def replace_outputs_atomically(paths: dict[str, Path], transaction_dir: Path, log: list[str]) -> None:
    backup_dir = transaction_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backups: dict[str, Path] = {}
    originally_missing: set[str] = set()
    for name, destination in MAINTAINED_OUTPUTS.items():
        if destination.exists():
            backup = backup_dir / name
            shutil.copy2(destination, backup)
            backups[name] = backup
        else:
            originally_missing.add(name)

    emit("All temporary checks passed; atomically replacing maintained COMS outputs", log)
    try:
        for name, destination in MAINTAINED_OUTPUTS.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(paths[name], destination)
        git_diff_check(log, "Post-update git whitespace check")
    except Exception:
        emit("Post-update validation failed; restoring last known-good outputs", log)
        for name, destination in MAINTAINED_OUTPUTS.items():
            if name in backups:
                os.replace(backups[name], destination)
            elif name in originally_missing and destination.exists():
                destination.unlink()
        raise


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def record_success(summary: dict[str, object], workbook_hash: str, generator_hash: str) -> None:
    coverage = summary.get("source_term_coverage")
    assert isinstance(coverage, dict)
    payload = {
        "workbook_path": relative(WORKBOOK),
        "workbook_sha256": workbook_hash,
        "generator_sha256": generator_hash,
        "generated_candidate_sha256": summary.get("generated_candidate_sha256"),
        "timestamp": utc_now(),
        "generated_ontology_triple_count": summary.get("generated_ontology_triple_count"),
        "candidate_closure_triple_count": summary.get("candidate_closure_triple_count"),
        "hermit_result": summary.get("hermit_result"),
        "source_term_counts": {
            "mapped_classes": coverage.get("mapped_classes"),
            "unmapped_classes": coverage.get("unmapped_classes"),
            "mapped_object_properties": coverage.get("mapped_object_properties"),
            "unmapped_object_properties": coverage.get("unmapped_object_properties"),
            "explicitly_listed_blank_mappings": coverage.get("explicitly_listed_blank_mappings"),
            "source_terms_absent_from_spreadsheet": coverage.get("source_terms_absent_from_spreadsheet"),
        },
    }
    write_json_atomic(LAST_SUCCESS, payload)


def write_failure_log(mode: str, log: list[str], exc: BaseException) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    content = [
        "COMS mapping quality-check failure",
        f"timestamp: {utc_now()}",
        f"mode: {mode}",
        f"exception: {type(exc).__name__}: {exc}",
        "",
        "Command log:",
        *log,
        "",
        "Traceback:",
        traceback.format_exc(),
    ]
    LAST_FAILURE.write_text("\n".join(content), encoding="utf-8")


def print_status() -> int:
    workbook_hash = sha256_file(WORKBOOK) if WORKBOOK.is_file() else "missing"
    generator_hash = sha256_file(GENERATOR) if GENERATOR.is_file() else "missing"
    errors: list[str] = []
    if not WORKBOOK.is_file():
        errors.append(f"missing workbook: {relative(WORKBOOK)}")
    if not GENERATOR.is_file():
        errors.append(f"missing generator: {relative(GENERATOR)}")
    if not errors:
        errors.extend(freshness_errors(workbook_hash, generator_hash))
    print(f"Workbook: {relative(WORKBOOK)}")
    print(f"Current workbook SHA-256: {workbook_hash}")
    if LAST_SUCCESS.is_file():
        try:
            success = json.loads(LAST_SUCCESS.read_text(encoding="utf-8"))
            print(f"Last successful SHA-256: {success.get('workbook_sha256', 'unknown')}")
            print(f"Last successful check: {success.get('timestamp', 'unknown')}")
        except json.JSONDecodeError:
            print("Last-success metadata: invalid JSON")
    else:
        print("Last-success metadata: not present")
    print(f"Generated artifacts current: {'yes' if not errors else 'no'}")
    for error in errors:
        print(f"- {error}")
    print(f"Last failure log: {relative(LAST_FAILURE) if LAST_FAILURE.is_file() else 'none'}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check-only",
        action="store_true",
        help="Validate freshness and quality without rewriting maintained outputs.",
    )
    mode.add_argument(
        "--update",
        action="store_true",
        help="Validate temporary products and atomically refresh maintained outputs (the default).",
    )
    mode.add_argument(
        "--status",
        action="store_true",
        help="Print workbook/artifact freshness and last-success status without running validation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.status:
        return print_status()

    mode = "check-only" if args.check_only else "update"
    started = time.perf_counter()
    log: list[str] = [f"COMS quality check started: {utc_now()}", f"Mode: {mode}"]
    transaction_dir: Path | None = None
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        workbook_hash = verify_workbook(log)
        generator_hash = compile_generator(log)
        current_freshness_errors = freshness_errors(workbook_hash, generator_hash)
        if args.check_only and current_freshness_errors:
            raise CheckFailure("stale COMS outputs: " + "; ".join(current_freshness_errors))
        if current_freshness_errors:
            emit("Maintained outputs are stale and will be refreshed after temporary validation:", log)
            for error in current_freshness_errors:
                emit(f"- {error}", log)

        transaction_dir = Path(tempfile.mkdtemp(prefix="run-", dir=CACHE_DIR))
        paths = transaction_paths(transaction_dir)
        run_generator(paths, log)
        summary = validate_temporary_outputs(paths, workbook_hash, generator_hash, log)
        git_diff_check(log, "Pre-update git whitespace check")

        differences = output_differences(paths)
        if args.check_only:
            if differences:
                raise CheckFailure(
                    "maintained outputs differ from freshly validated temporary products: "
                    + ", ".join(differences)
                )
            emit("Check-only mode: maintained outputs are fresh; no tracked files were rewritten", log)
        elif differences or current_freshness_errors:
            replace_outputs_atomically(paths, transaction_dir, log)
        else:
            emit("Maintained outputs already match; no tracked files were rewritten", log)

        record_success(summary, workbook_hash, generator_hash)
        elapsed = time.perf_counter() - started
        emit(f"COMS quality check: PASS ({elapsed:.2f} seconds)", log)
        emit(f"Last-success metadata: {relative(LAST_SUCCESS)}", log)
        return 0
    except Exception as exc:
        write_failure_log(mode, log, exc)
        print(f"COMS quality check: FAIL ({exc})", file=sys.stderr, flush=True)
        print(f"Failure log: {relative(LAST_FAILURE)}", file=sys.stderr, flush=True)
        return 1
    finally:
        if transaction_dir is not None:
            shutil.rmtree(transaction_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
