#!/usr/bin/env python3
"""Check the maintained SOSA-next modular ontology products."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_sosa_next_products as products


def run_check(
    output_dir: Path,
    robot_path: str | None = None,
) -> dict[str, object]:
    return products.check_maintained_products(
        output_dir,
        robot_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--output-dir",
        default="/tmp/sosa-next-product-check",
        help="Directory for temporary validation evidence.",
    )

    parser.add_argument(
        "--robot",
        help="Optional explicit ROBOT executable path.",
    )

    args = parser.parse_args(argv)

    try:
        summary = run_check(
            Path(args.output_dir),
            args.robot,
        )
    except Exception as exc:
        print("SOSA-next product check: FAIL")
        print(exc)
        return 1

    products.print_summary(summary)

    print(
        "Maintained products fresh: "
        f"{summary['maintained_products_fresh']}"
    )
    print(
        f"Summary: "
        f"{'PASS' if summary['passed'] else 'FAIL'}"
    )

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
