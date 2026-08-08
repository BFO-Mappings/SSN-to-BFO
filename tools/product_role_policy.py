#!/usr/bin/env python3
"""Load and validate the repository-wide ontology product-role policy."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import sosa_source_version


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config/product-role-policy.toml"

ROLE_ORDER = (
    "integrated",
    "alignment_core",
    "strict_bfo_mapping",
    "bfo_projection",
    "cco_extension",
)

MATERIALIZE_STATUSES = frozenset(
    {
        "materialize_consumer_function",
        "materialize_direct_content",
    }
)

OMIT_STATUS = "omit_no_substantive_content_or_distinct_function"

EXPECTED_RULE = "direct_logical_content_or_distinct_consumer_function"

ROLE_INCLUSION_BASES = {
    "integrated": "distinct_consumer_function",
    "alignment_core": "direct_product_specific_logical_content",
    "strict_bfo_mapping": "direct_product_specific_logical_content",
    "bfo_projection": "direct_product_specific_logical_content",
    "cco_extension": "direct_product_specific_logical_content",
}


@dataclass(frozen=True)
class ProductRole:
    key: str
    human_label: str
    inclusion_basis: str


@dataclass(frozen=True)
class TrackPolicy:
    track_key: str
    formal_product_order: tuple[str, ...]
    omitted_product_roles: tuple[str, ...]
    role_status: tuple[tuple[str, str], ...]

    def status_map(self) -> dict[str, str]:
        return dict(self.role_status)


@dataclass(frozen=True)
class ProductRolePolicy:
    schema_version: int
    status: str
    role_order: tuple[str, ...]
    materialization_rule: str
    empty_role_boundary_is_sufficient: bool
    roles: tuple[ProductRole, ...]
    tracks: tuple[TrackPolicy, ...]

    def track(self, track_key: str) -> TrackPolicy:
        matches = [
            value
            for value in self.tracks
            if value.track_key == track_key
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"track {track_key!r}: expected exactly one policy record"
            )
        return matches[0]


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


def load_product_role_policy(
    config_path: Path = CONFIG_PATH,
) -> ProductRolePolicy:
    with config_path.open("rb") as handle:
        document = tomllib.load(handle)

    _require_exact_keys(
        document,
        {
            "schema_version",
            "status",
            "role_order",
            "materialization_rule",
            "empty_role_boundary_is_sufficient",
            "roles",
            "tracks",
        },
        "document",
    )

    schema_version = document["schema_version"]
    if isinstance(schema_version, bool) or schema_version != 1:
        raise RuntimeError("schema_version: expected integer 1")

    status = _require_string(document["status"], "status")
    if status != "approved":
        raise RuntimeError("status: expected 'approved'")

    role_order = _require_string_list(
        document["role_order"],
        "role_order",
    )
    if role_order != ROLE_ORDER:
        raise RuntimeError(
            f"role_order: expected canonical order {ROLE_ORDER!r}"
        )

    materialization_rule = _require_string(
        document["materialization_rule"],
        "materialization_rule",
    )
    if materialization_rule != EXPECTED_RULE:
        raise RuntimeError(
            f"materialization_rule: expected {EXPECTED_RULE!r}"
        )

    empty_boundary = document["empty_role_boundary_is_sufficient"]
    if not isinstance(empty_boundary, bool):
        raise RuntimeError(
            "empty_role_boundary_is_sufficient: expected boolean"
        )
    if empty_boundary:
        raise RuntimeError(
            "empty_role_boundary_is_sufficient: empty role boundaries "
            "are not sufficient for materialization"
        )

    raw_roles = document["roles"]
    if not isinstance(raw_roles, dict):
        raise RuntimeError("roles: expected table")

    if set(raw_roles) != set(ROLE_ORDER):
        raise RuntimeError(
            "roles: expected exactly the canonical five product roles"
        )

    roles: list[ProductRole] = []
    for key in ROLE_ORDER:
        raw_role = raw_roles[key]
        if not isinstance(raw_role, dict):
            raise RuntimeError(f"roles.{key}: expected table")

        _require_exact_keys(
            raw_role,
            {"human_label", "inclusion_basis"},
            f"roles.{key}",
        )

        human_label = _require_string(
            raw_role["human_label"],
            f"roles.{key}.human_label",
        )
        inclusion_basis = _require_string(
            raw_role["inclusion_basis"],
            f"roles.{key}.inclusion_basis",
        )

        if inclusion_basis != ROLE_INCLUSION_BASES[key]:
            raise RuntimeError(
                f"roles.{key}.inclusion_basis: expected "
                f"{ROLE_INCLUSION_BASES[key]!r}"
            )

        roles.append(
            ProductRole(
                key=key,
                human_label=human_label,
                inclusion_basis=inclusion_basis,
            )
        )

    raw_tracks = document["tracks"]
    if not isinstance(raw_tracks, list) or len(raw_tracks) != 2:
        raise RuntimeError("tracks: expected exactly two track records")

    source = sosa_source_version.load_source_version_authority()
    expected_track_keys = (
        "current-ssn-sosa",
        source.source_identity,
    )

    tracks: list[TrackPolicy] = []

    for index, raw_track in enumerate(raw_tracks):
        label = f"tracks[{index}]"
        if not isinstance(raw_track, dict):
            raise RuntimeError(f"{label}: expected table")

        _require_exact_keys(
            raw_track,
            {
                "track_key",
                "formal_product_order",
                "omitted_product_roles",
                "role_status",
            },
            label,
        )

        track_key = _require_string(
            raw_track["track_key"],
            f"{label}.track_key",
        )

        if track_key != expected_track_keys[index]:
            raise RuntimeError(
                f"{label}.track_key: expected "
                f"{expected_track_keys[index]!r}"
            )

        formal_product_order = _require_string_list(
            raw_track["formal_product_order"],
            f"{label}.formal_product_order",
        )
        omitted_product_roles = _require_string_list(
            raw_track["omitted_product_roles"],
            f"{label}.omitted_product_roles",
        )

        raw_status = raw_track["role_status"]
        if not isinstance(raw_status, dict):
            raise RuntimeError(f"{label}.role_status: expected table")

        if set(raw_status) != set(ROLE_ORDER):
            raise RuntimeError(
                f"{label}.role_status: expected all five roles"
            )

        status_map: dict[str, str] = {}
        for role_key in ROLE_ORDER:
            role_status = _require_string(
                raw_status[role_key],
                f"{label}.role_status.{role_key}",
            )
            if (
                role_status not in MATERIALIZE_STATUSES
                and role_status != OMIT_STATUS
            ):
                raise RuntimeError(
                    f"{label}.role_status.{role_key}: "
                    "unapproved materialization status"
                )
            status_map[role_key] = role_status

        derived_materialized = tuple(
            role_key
            for role_key in ROLE_ORDER
            if status_map[role_key] in MATERIALIZE_STATUSES
        )
        derived_omitted = tuple(
            role_key
            for role_key in ROLE_ORDER
            if status_map[role_key] == OMIT_STATUS
        )

        if formal_product_order != derived_materialized:
            raise RuntimeError(
                f"{label}.formal_product_order: does not match "
                "materialization statuses"
            )

        if omitted_product_roles != derived_omitted:
            raise RuntimeError(
                f"{label}.omitted_product_roles: does not match "
                "materialization statuses"
            )

        tracks.append(
            TrackPolicy(
                track_key=track_key,
                formal_product_order=formal_product_order,
                omitted_product_roles=omitted_product_roles,
                role_status=tuple(
                    (key, status_map[key])
                    for key in ROLE_ORDER
                ),
            )
        )

    return ProductRolePolicy(
        schema_version=1,
        status=status,
        role_order=role_order,
        materialization_rule=materialization_rule,
        empty_role_boundary_is_sufficient=empty_boundary,
        roles=tuple(roles),
        tracks=tuple(tracks),
    )
