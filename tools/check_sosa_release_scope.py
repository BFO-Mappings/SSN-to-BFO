#!/usr/bin/env python3
"""Validate the governed SOSA formal package-scope authority."""

from __future__ import annotations

import sosa_release_scope


def run_check() -> dict[str, object]:
    scope = sosa_release_scope.load_release_scope()

    return {
        "schema_version": scope.schema_version,
        "status": scope.status,
        "source_identity": scope.source_identity,
        "development_alias": scope.development_alias,
        "publication_model": scope.publication_model,
        "formal_track_component": scope.formal_track_component,
        "product_role_policy": scope.product_role_policy,
        "formal_product_order": scope.formal_product_order,
        "omitted_product_roles": scope.omitted_product_roles,
        "current_track_formal_release": (
            scope.current_track_formal_release
        ),
        "passed": True,
    }


def main() -> int:
    try:
        summary = run_check()
    except Exception as exc:
        print(f"SOSA release-package scope: FAIL\n{exc}")
        return 1

    print(f"Status: {summary['status']}")
    print(f"Source identity: {summary['source_identity']}")
    print(f"Development alias: {summary['development_alias']}")
    print(f"Publication model: {summary['publication_model']}")
    print(
        "Formal track component: "
        f"{summary['formal_track_component']}"
    )
    print(
        "Product-role policy: "
        f"{summary['product_role_policy']}"
    )
    print(
        "Formal product order: "
        + ", ".join(summary["formal_product_order"])
    )
    print(
        "Omitted product roles: "
        + ", ".join(summary["omitted_product_roles"])
    )
    print(
        "Current-track formal release: "
        f"{summary['current_track_formal_release']}"
    )
    print("Summary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
