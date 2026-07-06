#!/usr/bin/env python3
"""Run the standard local validation suite for SSN-to-BFO mapping work."""

from __future__ import annotations

import argparse
import csv
import shlex
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TMP_DIR = Path("/tmp/ssn-to-bfo-validation-suite")
EXPECTED_AUDIT_COUNTS = Counter({"missing_in_spreadsheet": 1, "missing_in_ttl": 1})
EXPECTED_AUDIT_TOTAL = 2
EXPECTED_AUDIT_SOURCE_TERM = "sosa:Sensor"
EXPECTED_AUDIT_SOURCE_IRI = "http://www.w3.org/ns/sosa/Sensor"


@dataclass
class StepResult:
    name: str
    passed: bool
    detail: str = ""


def command_text(command: list[str]) -> str:
    return shlex.join(command)


def run_command(name: str, command: list[str]) -> StepResult:
    print(f"\n==> {name}")
    print(f"$ {command_text(command)}")
    proc = subprocess.run(command, cwd=REPO_ROOT)
    passed = proc.returncode == 0
    status = "PASS" if passed else f"FAIL ({proc.returncode})"
    print(f"{name}: {status}")
    return StepResult(name=name, passed=passed, detail=status)


def parse_ttl_check() -> StepResult:
    code = (
        "from rdflib import Graph; "
        "Graph().parse('SSN2BFO.ttl', format='turtle'); "
        "print('SSN2BFO.ttl parse OK')"
    )
    return run_command("Turtle parse check", [sys.executable, "-c", code])


def run_mapping_audit(output_md: Path, output_csv: Path) -> StepResult:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "tools/compare_mappings.py",
        "--ttl",
        "SSN2BFO.ttl",
        "--spreadsheet",
        "Current_SOSA-SSN to BFO-CCO.xlsx",
        "--output-md",
        str(output_md),
        "--output-csv",
        str(output_csv),
    ]
    return run_command("Mapping consistency audit", command)


def audit_summary(csv_path: Path, allow_drift: bool) -> StepResult:
    print("\n==> Audit issue summary")
    print(f"Reading {csv_path}")
    if not csv_path.exists():
        detail = f"missing audit CSV: {csv_path}"
        print(f"Audit issue summary: FAIL ({detail})")
        return StepResult("Audit issue summary", False, detail)

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    counts = Counter(row.get("category", "") for row in rows)
    print(f"total issues: {len(rows)}")
    for category, count in sorted(counts.items()):
        print(f"{category}: {count}")
    for row in rows:
        print(
            " ".join(
                [
                    row.get("issue_id", ""),
                    row.get("category", ""),
                    row.get("sheet", ""),
                    row.get("spreadsheet_row", ""),
                    row.get("source_term", ""),
                    "=>",
                    row.get("spreadsheet_target") or row.get("ttl_target") or "",
                ]
            )
        )

    expected_shape = len(rows) == EXPECTED_AUDIT_TOTAL and counts == EXPECTED_AUDIT_COUNTS
    expected_sensor_rows = all(
        row.get("source_term") == EXPECTED_AUDIT_SOURCE_TERM
        and row.get("source_iri") == EXPECTED_AUDIT_SOURCE_IRI
        for row in rows
    )
    if expected_shape and expected_sensor_rows:
        detail = "recognized expected two sosa:Sensor version-alignment issues"
        print(f"Audit issue summary: PASS ({detail})")
        return StepResult("Audit issue summary", True, detail)

    detail = (
        "audit issue shape differs from expected "
        f"{dict(EXPECTED_AUDIT_COUNTS)} / total {EXPECTED_AUDIT_TOTAL}"
    )
    if allow_drift:
        print(f"Audit issue summary: PASS with --allow-audit-drift ({detail})")
        return StepResult("Audit issue summary", True, detail)

    print(f"Audit issue summary: FAIL ({detail})")
    return StepResult("Audit issue summary", False, detail)


def compile_check() -> StepResult:
    return run_command(
        "Python compile check",
        [
            sys.executable,
            "-m",
            "py_compile",
            "tools/run_validation_suite.py",
            "tools/test_elk_instance_mapping_entailments.py",
            "tools/test_instance_data.py",
            "tools/compare_mappings.py",
        ],
    )


def print_summary(results: list[StepResult], report_paths: dict[str, Path], used_temp_reports: bool) -> int:
    print("\n==> Validation suite summary")
    print(f"Report output mode: {'temporary' if used_temp_reports else 'canonical'}")
    for label, path in report_paths.items():
        print(f"{label}: {path}")

    failed = [result for result in results if not result.passed]
    for result in results:
        print(f"- {result.name}: {'PASS' if result.passed else 'FAIL'}")

    if failed:
        print(f"\nValidation suite: FAIL ({len(failed)} failed step{'s' if len(failed) != 1 else ''})")
        return 1

    print("\nValidation suite: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-audit-drift",
        action="store_true",
        help="Do not fail when the mapping audit issue shape differs from the expected current baseline.",
    )
    parser.add_argument(
        "--write-reports",
        action="store_true",
        help="Write validation reports to canonical reports/ paths instead of temporary outputs.",
    )
    parser.add_argument(
        "--tmp-dir",
        default=str(DEFAULT_TMP_DIR),
        help=f"Temporary report directory used unless --write-reports is set. Default: {DEFAULT_TMP_DIR}",
    )
    args = parser.parse_args()

    tmp_dir = Path(args.tmp_dir)
    if args.write_reports:
        audit_md = REPO_ROOT / "reports/mapping-consistency-audit.md"
        audit_csv = REPO_ROOT / "reports/mapping-consistency-audit.csv"
        smoke_report = REPO_ROOT / "reports/instance-data-smoke-test.md"
        elk_report = REPO_ROOT / "reports/elk-instance-mapping-entailments.md"
    else:
        audit_md = tmp_dir / "mapping-consistency-audit.md"
        audit_csv = tmp_dir / "mapping-consistency-audit.csv"
        smoke_report = tmp_dir / "instance-data-smoke-test.md"
        elk_report = tmp_dir / "elk-instance-mapping-entailments.md"

    report_paths = {
        "mapping audit markdown": audit_md,
        "mapping audit CSV": audit_csv,
        "instance smoke report": smoke_report,
        "ELK entailment report": elk_report,
    }

    results: list[StepResult] = []
    results.append(parse_ttl_check())
    if results[-1].passed:
        results.append(run_mapping_audit(audit_md, audit_csv))
    if results[-1].passed:
        results.append(audit_summary(audit_csv, args.allow_audit_drift))
    if results[-1].passed:
        results.append(
            run_command(
                "Instance-data smoke test",
                [sys.executable, "tools/test_instance_data.py", "--output", str(smoke_report)],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "ELK instance mapping entailment test",
                [
                    sys.executable,
                    "tools/test_elk_instance_mapping_entailments.py",
                    "--output",
                    str(elk_report),
                ],
            )
        )
    if results[-1].passed:
        results.append(compile_check())
    if results[-1].passed:
        results.append(run_command("Git whitespace check", ["git", "diff", "--check"]))

    return print_summary(results, report_paths, not args.write_reports)


if __name__ == "__main__":
    raise SystemExit(main())
