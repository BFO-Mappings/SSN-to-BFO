#!/usr/bin/env python3
"""Watch the COMS workbook and run its atomic quality check after saves."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = REPO_ROOT / "mappings/SSN2BFO-COMS.xlsx"
CHECKER = REPO_ROOT / "tools/check_coms_mapping.py"
LAST_SUCCESS = REPO_ROOT / ".cache/coms/last-success.json"
MAINTAINED_OUTPUTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "reports/coms-generation-validation.md",
    REPO_ROOT / "reports/coms-source-term-coverage.md",
    REPO_ROOT / "reports/coms-vs-pre-coms-legacy-diff.md",
    REPO_ROOT / "reports/coms-product-dispositions.json",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)
POLL_SECONDS = 1.0
DEBOUNCE_SECONDS = 1.5


def now_text() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except FileNotFoundError:
        return None


def last_good_status(workbook_hash: str | None, check_passed: bool) -> str:
    if check_passed and workbook_hash is not None:
        return "current"
    if not all(path.is_file() and path.stat().st_size > 0 for path in MAINTAINED_OUTPUTS):
        return "unavailable"
    if not LAST_SUCCESS.is_file():
        return "preserved (no local last-success metadata)"
    try:
        payload = json.loads(LAST_SUCCESS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "preserved (last-success metadata unreadable)"
    return f"preserved (workbook SHA-256 {payload.get('workbook_sha256', 'unknown')})"


def last_success_coverage_status() -> str | None:
    try:
        payload = json.loads(LAST_SUCCESS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    counts = payload.get("source_term_counts")
    if not isinstance(counts, dict):
        return None
    mapped = counts.get("mapped_object_properties")
    typing_only = counts.get("listed_only_in_domain_range_rows")
    unmapped = counts.get("unmapped_object_properties")
    if any(value is None for value in (mapped, typing_only, unmapped)):
        return None
    return (
        f"Coverage counts: mapped object properties {mapped}; "
        f"listed only in domain/range property-typing rows {typing_only}; "
        f"unmapped object properties {unmapped}"
    )


def last_success_metadata_status() -> str | None:
    try:
        payload = json.loads(LAST_SUCCESS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    counts = [payload.get("generated_candidate_metadata_annotation_count")]
    for product_key in (
        "alignment_core",
        "strict_bfo_mapping",
        "bfo_projection",
        "cco_extension",
    ):
        product = payload.get(product_key)
        counts.append(
            product.get("metadata_annotation_count")
            if isinstance(product, dict)
            else None
        )
    if any(value is None for value in counts):
        return None
    return "Development metadata annotations: " + ", ".join(
        f"{key} {count}"
        for key, count in zip(
            ("integrated", "alignment core", "strict BFO", "BFO projection", "CCO extension"),
            counts,
        )
    )


def run_check(trigger: str, workbook_hash: str | None) -> bool:
    started = time.perf_counter()
    print(f"Detection time: {now_text()}", flush=True)
    print(f"Workbook hash: {workbook_hash or 'unavailable'}", flush=True)
    print(f"Check start: {trigger}", flush=True)
    proc = subprocess.run([sys.executable, str(CHECKER)], cwd=REPO_ROOT)
    elapsed = time.perf_counter() - started
    passed = proc.returncode == 0
    print(f"Check result: {'PASS' if passed else f'FAIL ({proc.returncode})'}", flush=True)
    print(f"Duration: {elapsed:.2f} seconds", flush=True)
    print(f"Last-good output status: {last_good_status(workbook_hash, passed)}", flush=True)
    if passed:
        coverage_status = last_success_coverage_status()
        if coverage_status is not None:
            print(coverage_status, flush=True)
        metadata_status = last_success_metadata_status()
        if metadata_status is not None:
            print(metadata_status, flush=True)
    return passed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    parse_args(argv or sys.argv[1:])
    print(f"Watching: {WORKBOOK.relative_to(REPO_ROOT)}", flush=True)
    print(
        f"Polling every {POLL_SECONDS:.1f}s; saves are debounced for {DEBOUNCE_SECONDS:.1f}s. "
        "Press Ctrl+C to stop.",
        flush=True,
    )
    print("Office lock files are ignored; only the configured workbook content hash is monitored.", flush=True)

    observed_hash = sha256_file(WORKBOOK)
    run_check("startup", observed_hash)
    last_processed_hash = observed_hash
    stable_since = time.monotonic()
    missing_reported = observed_hash is None

    try:
        while True:
            time.sleep(POLL_SECONDS)
            current_hash = sha256_file(WORKBOOK)
            now = time.monotonic()

            if current_hash is None:
                if not missing_reported:
                    print(
                        f"Detection time: {now_text()} - workbook temporarily unavailable; waiting for rename/save completion",
                        flush=True,
                    )
                    missing_reported = True
                observed_hash = None
                stable_since = now
                continue

            missing_reported = False
            if current_hash != observed_hash:
                observed_hash = current_hash
                stable_since = now
                print(f"Detection time: {now_text()}", flush=True)
                print(f"Workbook hash: {current_hash}", flush=True)
                print("Content change detected; waiting for the workbook to remain stable", flush=True)
                continue

            if current_hash == last_processed_hash:
                continue
            if now - stable_since < DEBOUNCE_SECONDS:
                continue

            run_check("debounced workbook save", current_hash)
            last_processed_hash = current_hash
            post_check_hash = sha256_file(WORKBOOK)
            if post_check_hash != current_hash:
                observed_hash = post_check_hash
                stable_since = time.monotonic()
    except KeyboardInterrupt:
        print("\nWatcher stopped cleanly.", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
