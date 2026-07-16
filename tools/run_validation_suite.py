#!/usr/bin/env python3
"""Run the standard local validation suite for SSN-to-BFO mapping work."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TMP_DIR = Path("/tmp/ssn-to-bfo-validation-suite")


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


def compile_check() -> StepResult:
    return run_command(
        "Python compile check",
        [
            sys.executable,
            "-m",
            "py_compile",
            "tools/run_validation_suite.py",
            "tools/test_elk_instance_mapping_entailments.py",
            "tools/test_full_sosa_closure_hermit.py",
            "tools/test_object_property_typing_probes.py",
            "tools/test_instance_data.py",
            "tools/compare_mappings.py",
            "tools/coms_row_identity.py",
            "tools/product_dispositions.py",
            "tools/modular_products.py",
            "tools/generate_mapping_from_coms.py",
            "tools/check_coms_mapping.py",
            "tools/watch_coms_mapping.py",
            "tools/publication_metadata.py",
            "tools/check_publication_metadata.py",
            "tests/test_generate_mapping_from_coms.py",
            "tests/test_coms_row_identity.py",
            "tests/test_product_dispositions.py",
            "tests/test_modular_products.py",
            "tests/test_strict_bfo_mapping.py",
            "tests/test_cco_extension.py",
            "tests/test_publication_metadata.py",
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
        smoke_report = REPO_ROOT / "reports/instance-data-smoke-test.md"
        elk_report = REPO_ROOT / "reports/elk-instance-mapping-entailments.md"
        full_sosa_hermit_report = REPO_ROOT / "reports/full-sosa-closure-hermit-check.md"
    else:
        smoke_report = tmp_dir / "instance-data-smoke-test.md"
        elk_report = tmp_dir / "elk-instance-mapping-entailments.md"
        full_sosa_hermit_report = tmp_dir / "full-sosa-closure-hermit-check.md"

    report_paths = {
        "instance smoke report": smoke_report,
        "ELK entailment report": elk_report,
        "full SOSA closure HermiT report": full_sosa_hermit_report,
    }

    results: list[StepResult] = []
    results.append(parse_ttl_check())
    if results[-1].passed:
        results.append(
            run_command(
                "COMS row-identity focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_coms_row_identity.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "COMS product-disposition focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_product_dispositions.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Alignment-core modular-product focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_modular_products.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Strict-BFO modular-product focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_strict_bfo_mapping.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "CCO-extension modular-product focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_cco_extension.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Publication metadata focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_publication_metadata.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "Publication metadata development check",
                [sys.executable, "tools/check_publication_metadata.py"],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "COMS generator focused tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_generate_mapping_from_coms.py",
                ],
            )
        )
    if results[-1].passed:
        results.append(
            run_command(
                "COMS workbook freshness and candidate quality check",
                [sys.executable, "tools/check_coms_mapping.py", "--check-only"],
            )
        )
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
        results.append(
            run_command(
                "Full local SOSA closure HermiT check",
                [
                    sys.executable,
                    "tools/test_full_sosa_closure_hermit.py",
                    "--output",
                    str(full_sosa_hermit_report),
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
