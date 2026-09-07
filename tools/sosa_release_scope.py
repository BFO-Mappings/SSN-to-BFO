#!/usr/bin/env python3
"""Load and validate the governed SOSA formal package-scope decision."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import product_role_policy
import sosa_source_version


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config/sosa-release-scope.toml"

EXPECTED_PUBLICATION_MODEL = "separate_package"
EXPECTED_ROLE_POLICY_PATH = "config/product-role-policy.toml"
EXPECTED_CURRENT_TRACK_STATE = "product_role_policy_migration_complete"


@dataclass(frozen=True)
class SosaReleaseScope:
    schema_version: int
    status: str
    source_identity: str
    development_alias: str
    publication_model: str
    formal_track_component: str
    product_role_policy: str
    formal_product_order: tuple[str, ...]
    omitted_product_roles: tuple[str, ...]
    current_track_formal_release: str


def _require_exact_keys(
    value: dict[str, object],
    expected: set[str],
    label: str,
) -> None:
    actual = set(value)
    if actual != expected:
        raise RuntimeError(
            f"{label}: noncanonical keys; "
            f"missing={sorted(expected - actual)}; "
            f"extra={sorted(actual - expected)}"
        )


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{label}: expected nonempty string")
    return value


def _require_string_list(
    value: object,
    label: str,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise RuntimeError(f"{label}: expected array")
    if not all(isinstance(item, str) and item for item in value):
        raise RuntimeError(f"{label}: expected nonempty strings")
    return tuple(value)


def load_release_scope(
    config_path: Path = CONFIG_PATH,
) -> SosaReleaseScope:
    with config_path.open("rb") as handle:
        document = tomllib.load(handle)

    _require_exact_keys(
        document,
        {
            "schema_version",
            "status",
            "source_identity",
            "development_alias",
            "publication_model",
            "formal_track_component",
            "product_role_policy",
            "formal_product_order",
            "omitted_product_roles",
            "current_track_formal_release",
        },
        "document",
    )

    schema_version = document["schema_version"]
    if isinstance(schema_version, bool) or schema_version != 2:
        raise RuntimeError("schema_version: expected integer 2")

    status = _require_string(document["status"], "status")
    if status != "approved":
        raise RuntimeError("status: expected 'approved'")

    source = sosa_source_version.load_source_version_authority()
    role_policy = product_role_policy.load_product_role_policy()

    source_identity = _require_string(
        document["source_identity"],
        "source_identity",
    )
    if source_identity != source.source_identity:
        raise RuntimeError(
            "source_identity: must equal approved source-version identity"
        )

    development_alias = _require_string(
        document["development_alias"],
        "development_alias",
    )
    if development_alias != source.development_alias:
        raise RuntimeError(
            "development_alias: must equal source-version authority"
        )

    publication_model = _require_string(
        document["publication_model"],
        "publication_model",
    )
    if publication_model != EXPECTED_PUBLICATION_MODEL:
        raise RuntimeError(
            "publication_model: separate package decision remains approved"
        )

    formal_track_component = _require_string(
        document["formal_track_component"],
        "formal_track_component",
    )
    if formal_track_component != source_identity:
        raise RuntimeError(
            "formal_track_component: must equal source identity"
        )

    role_policy_path = _require_string(
        document["product_role_policy"],
        "product_role_policy",
    )
    if role_policy_path != EXPECTED_ROLE_POLICY_PATH:
        raise RuntimeError(
            f"product_role_policy: expected {EXPECTED_ROLE_POLICY_PATH!r}"
        )

    governed_track = role_policy.track(source_identity)

    formal_product_order = _require_string_list(
        document["formal_product_order"],
        "formal_product_order",
    )
    if formal_product_order != governed_track.formal_product_order:
        raise RuntimeError(
            "formal_product_order: must equal product-role policy"
        )

    omitted_product_roles = _require_string_list(
        document["omitted_product_roles"],
        "omitted_product_roles",
    )
    if omitted_product_roles != governed_track.omitted_product_roles:
        raise RuntimeError(
            "omitted_product_roles: must equal product-role policy"
        )

    current_track_state = _require_string(
        document["current_track_formal_release"],
        "current_track_formal_release",
    )
    if current_track_state != EXPECTED_CURRENT_TRACK_STATE:
        raise RuntimeError(
            "current_track_formal_release: expected completed role-policy migration"
        )

    return SosaReleaseScope(
        schema_version=2,
        status=status,
        source_identity=source_identity,
        development_alias=development_alias,
        publication_model=publication_model,
        formal_track_component=formal_track_component,
        product_role_policy=role_policy_path,
        formal_product_order=formal_product_order,
        omitted_product_roles=omitted_product_roles,
        current_track_formal_release=current_track_state,
    )
