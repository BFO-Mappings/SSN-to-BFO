#!/usr/bin/env python3
"""Validate the repository-wide product-role inclusion policy."""

from __future__ import annotations

import product_role_policy


def run_check() -> dict[str, object]:
    policy = product_role_policy.load_product_role_policy()

    return {
        "schema_version": policy.schema_version,
        "status": policy.status,
        "role_order": policy.role_order,
        "materialization_rule": policy.materialization_rule,
        "empty_role_boundary_is_sufficient": (
            policy.empty_role_boundary_is_sufficient
        ),
        "tracks": {
            track.track_key: {
                "formal_product_order": track.formal_product_order,
                "omitted_product_roles": track.omitted_product_roles,
            }
            for track in policy.tracks
        },
        "passed": True,
    }


def main() -> int:
    try:
        summary = run_check()
    except Exception as exc:
        print(f"Product-role policy: FAIL\n{exc}")
        return 1

    print(f"Status: {summary['status']}")
    print(
        "Role order: "
        + ", ".join(summary["role_order"])
    )
    print(
        "Materialization rule: "
        f"{summary['materialization_rule']}"
    )
    print(
        "Empty role boundary sufficient: "
        f"{summary['empty_role_boundary_is_sufficient']}"
    )

    for track_key, track in summary["tracks"].items():
        print(f"{track_key}:")
        print(
            "  formal products: "
            + ", ".join(track["formal_product_order"])
        )
        print(
            "  omitted roles: "
            + ", ".join(track["omitted_product_roles"])
        )

    print("Summary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
