#!/usr/bin/env python3
"""Human-gated workflow checks for SSN-to-BFO branch work."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
COMPILE_COMMAND = [
    PYTHON,
    "-m",
    "py_compile",
    "tools/run_validation_suite.py",
    "tools/test_elk_instance_mapping_entailments.py",
    "tools/test_full_sosa_closure_hermit.py",
    "tools/test_object_property_typing_probes.py",
    "tools/test_instance_data.py",
    "tools/compare_mappings.py",
    "tools/workflow_check.py",
]
VALIDATE_COMMAND = [PYTHON, "tools/run_validation_suite.py"]
VALIDATE_WRITE_COMMAND = [PYTHON, "tools/run_validation_suite.py", "--write-reports"]


@dataclass
class CommandResult:
    name: str
    returncode: int


@dataclass
class WorkflowState:
    branch: str = ""
    changed_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    results: list[CommandResult] = field(default_factory=list)


def command_text(command: list[str]) -> str:
    return shlex.join(command)


def run_command(name: str, command: list[str], *, required: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"\n==> {name}")
    print(f"$ {command_text(command)}")
    proc = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    status = "PASS" if proc.returncode == 0 else f"FAIL ({proc.returncode})"
    print(f"{name}: {status}")
    if required and proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc


def run_step(state: WorkflowState, name: str, command: list[str], *, required: bool = True) -> None:
    proc = run_command(name, command, required=required)
    state.results.append(CommandResult(name, proc.returncode))


def capture_lines(name: str, command: list[str], *, required: bool = True) -> list[str]:
    proc = run_command(name, command, required=required)
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def current_branch(state: WorkflowState) -> str:
    lines = capture_lines("Current branch", ["git", "branch", "--show-current"])
    branch = lines[0] if lines else ""
    state.branch = branch
    return branch


def print_git_overview(state: WorkflowState) -> None:
    current_branch(state)
    run_command("Git status", ["git", "status", "--short"])
    run_command("Unstaged diff stat", ["git", "diff", "--stat"])
    run_command("Staged diff stat", ["git", "diff", "--cached", "--stat"])


def git_name_list(name: str, command: list[str]) -> list[str]:
    return capture_lines(name, command)


def changed_files() -> tuple[list[str], list[str], list[str], list[str]]:
    unstaged = git_name_list("Unstaged changed files", ["git", "diff", "--name-only"])
    staged = git_name_list("Staged changed files", ["git", "diff", "--cached", "--name-only"])
    untracked = git_name_list(
        "Untracked files",
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    combined = sorted(set(unstaged) | set(staged) | set(untracked))
    return unstaged, staged, untracked, combined


def print_changed_files(state: WorkflowState) -> None:
    unstaged, staged, untracked, combined = changed_files()
    state.changed_files = combined
    print("\n==> Changed files summary")
    print_list("unstaged", unstaged)
    print_list("staged", staged)
    print_list("untracked", untracked)
    print_list("combined", combined)


def print_list(label: str, values: list[str]) -> None:
    print(f"{label}:")
    if not values:
        print("  (none)")
        return
    for value in values:
        print(f"  {value}")


def check_catalog(state: WorkflowState) -> None:
    present = (REPO_ROOT / "catalog-v001.xml").exists()
    print("\n==> Catalog check")
    print(f"catalog-v001.xml present: {'yes' if present else 'no'}")
    if present:
        state.warnings.append("catalog-v001.xml is present; confirm it is intentional before review.")


def run_validation_set(state: WorkflowState) -> None:
    run_step(state, "Validation suite", VALIDATE_COMMAND)
    run_step(state, "Python compile check", COMPILE_COMMAND)
    run_step(state, "Git whitespace check", ["git", "diff", "--check"])


def compare_expected_files(state: WorkflowState, expected_files: list[str]) -> None:
    if not expected_files:
        return
    expected = set(expected_files)
    changed = set(state.changed_files)
    present = sorted(expected & changed)
    unexpected = sorted(changed - expected)
    missing = sorted(expected - changed)
    print("\n==> Expected-file comparison")
    print_list("expected files present", present)
    print_list("changed files not expected", unexpected)
    print_list("expected files not changed", missing)
    if unexpected:
        state.warnings.append("Some changed files were not in --expected-file.")
    if missing:
        state.warnings.append("Some --expected-file paths were not changed.")


def report_only_scope(state: WorkflowState, expected_files: list[str]) -> None:
    if expected_files:
        compare_expected_files(state, expected_files)
        return
    outside = [path for path in state.changed_files if not path.startswith("reports/")]
    if outside:
        state.warnings.append("Report-only mode found files outside reports/.")
        print("\nWARNING: report-only mode found files outside reports/:")
        for path in outside:
            print(f"  {path}")


def mapping_change_scope(state: WorkflowState) -> None:
    expected = {
        "SSN2BFO.ttl",
        "Current_SOSA-SSN to BFO-CCO.xlsx",
        "reports/mapping-consistency-audit.md",
        "reports/mapping-consistency-audit.csv",
        "reports/elk-instance-mapping-entailments.md",
    }
    unexpected = [
        path
        for path in state.changed_files
        if path not in expected and not (path.startswith("reports/") and "hermit" in path.lower())
    ]
    print("\n==> Mapping-change scope reminder")
    print("Expected mapping-change files are usually limited to:")
    for path in sorted(expected):
        print(f"  {path}")
    print("  reports/<new HermiT or evaluation report>.md")
    if unexpected:
        state.warnings.append("Mapping-change mode found files unexpected for review.")
        print("\nUnexpected for review:")
        for path in unexpected:
            print(f"  {path}")


def post_merge_mode(state: WorkflowState) -> None:
    current_branch(state)
    run_command("Git status before validation", ["git", "status", "--short"])
    run_step(state, "Validation suite", VALIDATE_COMMAND)
    final_status = capture_lines("Git status after validation", ["git", "status", "--short"])
    state.changed_files = sorted(set(final_status))
    if final_status:
        state.warnings.append("Working tree is dirty after post-merge validation.")
        print("\nERROR: working tree is dirty after post-merge validation.")
        raise SystemExit(1)


def pre_commit_mode(state: WorkflowState, expected_files: list[str]) -> None:
    print_git_overview(state)
    print_changed_files(state)
    check_catalog(state)
    compare_expected_files(state, expected_files)
    run_validation_set(state)


def write_reports_mode(state: WorkflowState, expected_files: list[str]) -> None:
    current_branch(state)
    run_step(state, "Validation suite with canonical reports", VALIDATE_WRITE_COMMAND)
    run_step(state, "Validation suite with temporary reports", VALIDATE_COMMAND)
    run_step(state, "Python compile check", COMPILE_COMMAND)
    run_step(state, "Git whitespace check", ["git", "diff", "--check"])
    run_command("Git status", ["git", "status", "--short"])
    run_command("Diff stat", ["git", "diff", "--stat"])
    run_command("Staged diff stat", ["git", "diff", "--cached", "--stat"])
    print_changed_files(state)
    check_catalog(state)
    compare_expected_files(state, expected_files)


def suggested_gate(mode: str, state: WorkflowState) -> str:
    if any(result.returncode != 0 for result in state.results):
        return "stop and investigate"
    if state.warnings:
        return "inspect diff"
    if mode == "post-merge":
        return "done / start next branch"
    if state.changed_files:
        return "commit"
    return "create PR"


def print_human_summary(mode: str, state: WorkflowState) -> None:
    print("\nHuman Review Summary")
    print(f"mode: {mode}")
    print(f"branch: {state.branch or '(unknown)'}")
    print_list("changed files", state.changed_files)
    print_list("warnings", state.warnings)
    print("validation status:")
    if not state.results:
        print("  (no validation commands recorded)")
    for result in state.results:
        status = "PASS" if result.returncode == 0 else f"FAIL ({result.returncode})"
        print(f"  {result.name}: {status}")
    print(f"suggested next human gate: {suggested_gate(mode, state)}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=["pre-commit", "post-merge", "report-only", "mapping-change", "write-reports"],
    )
    parser.add_argument(
        "--expected-file",
        action="append",
        default=[],
        help="Expected changed file path. May be supplied more than once.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    state = WorkflowState()
    try:
        if args.mode == "pre-commit":
            pre_commit_mode(state, args.expected_file)
        elif args.mode == "post-merge":
            post_merge_mode(state)
        elif args.mode == "report-only":
            pre_commit_mode(state, args.expected_file)
            report_only_scope(state, args.expected_file)
        elif args.mode == "mapping-change":
            pre_commit_mode(state, args.expected_file)
            mapping_change_scope(state)
            if (REPO_ROOT / "catalog-v001.xml").exists():
                print("\nWARNING: catalog-v001.xml is present.")
        elif args.mode == "write-reports":
            write_reports_mode(state, args.expected_file)
    finally:
        if not state.changed_files:
            _, _, _, combined = changed_files()
            state.changed_files = combined
        if not state.branch:
            proc = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            state.branch = proc.stdout.strip()
        print_human_summary(args.mode, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
