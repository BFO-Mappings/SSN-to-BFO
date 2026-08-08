#!/usr/bin/env python3
"""Load and validate the approved SOSA formal-package scope decision."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import sosa_source_version


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config/sosa-release-scope.toml"

EXPECTED_PUBLICATION_MODEL = "separate_package"
EXPECTED_PRODUCT_ORDER = (
    "alignment_core",
    "strict_bfo_mapping",
    "cco_extension",
)
EXPECTED_CURRENT_TRACK_POLICY = "unchanged"


@dataclass(frozen=True)
class SosaReleaseScope:
    schema_version: int
    status: str
    source_identity: str
    development_alias: str
    publication_model: str
    formal_track_component: str
    product_order: tuple[str, ...]
    integrated_product: bool
    bfo_projection_product: bool
    current_track_formal_release: str


def _require_exact_keys(
    value: dict[str, object],
    expected: set[str],
    label: str,
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(
            f"{label}: noncanonical keys; missing={missing}; extra={extra}"
        )


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{label}: expected nonempty string")
    return value


def _require_boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise RuntimeError(f"{label}: expected boolean")
    return value


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
            "product_order",
            "integrated_product",
            "bfo_projection_product",
            "current_track_formal_release",
        },
        "document",
    )

    schema_version = document["schema_version"]
    if isinstance(schema_version, bool) or schema_version != 1:
        raise RuntimeError(
            f"schema_version: expected integer 1, got {schema_version!r}"
        )

    status = _require_string(document["status"], "status")
    if status != "approved":
        raise RuntimeError(
            f"status: expected 'approved', got {status!r}"
        )

    source_authority = (
        sosa_source_version.load_source_version_authority()
    )

    source_identity = _require_string(
        document["source_identity"],
        "source_identity",
    )
    if source_identity != source_authority.source_identity:
        raise RuntimeError(
            "source_identity: must equal the approved SOSA source-version "
            f"identity {source_authority.source_identity!r}"
        )

    development_alias = _require_string(
        document["development_alias"],
        "development_alias",
    )
    if development_alias != source_authority.development_alias:
        raise RuntimeError(
            "development_alias: must equal the source-version authority"
        )

    publication_model = _require_string(
        document["publication_model"],
        "publication_model",
    )
    if publication_model != EXPECTED_PUBLICATION_MODEL:
        raise RuntimeError(
            "publication_model: approved model is "
            f"{EXPECTED_PUBLICATION_MODEL!r}"
        )

    formal_track_component = _require_string(
        document["formal_track_component"],
        "formal_track_component",
    )
    if formal_track_component != source_identity:
        raise RuntimeError(
            "formal_track_component: must equal the approved source identity"
        )

    raw_product_order = document["product_order"]
    if not isinstance(raw_product_order, list):
        raise RuntimeError("product_order: expected array")

    if not all(
        isinstance(value, str) and value
        for value in raw_product_order
    ):
        raise RuntimeError(
            "product_order: expected nonempty product strings"
        )

    product_order = tuple(raw_product_order)
    if product_order != EXPECTED_PRODUCT_ORDER:
        raise RuntimeError(
            "product_order: approved order is "
            f"{EXPECTED_PRODUCT_ORDER!r}"
        )

    if len(set(product_order)) != len(product_order):
        raise RuntimeError("product_order: duplicate product key")

    integrated_product = _require_boolean(
        document["integrated_product"],
        "integrated_product",
    )
    if integrated_product:
        raise RuntimeError(
            "integrated_product: not approved for the formal source-version package"
        )

    bfo_projection_product = _require_boolean(
        document["bfo_projection_product"],
        "bfo_projection_product",
    )
    if bfo_projection_product:
        raise RuntimeError(
            "bfo_projection_product: not approved for the formal source-version package"
        )

    current_track_formal_release = _require_string(
        document["current_track_formal_release"],
        "current_track_formal_release",
    )
    if current_track_formal_release != EXPECTED_CURRENT_TRACK_POLICY:
        raise RuntimeError(
            "current_track_formal_release: current formal package contract "
            "must remain unchanged"
        )

    return SosaReleaseScope(
        schema_version=1,
        status=status,
        source_identity=source_identity,
        development_alias=development_alias,
        publication_model=publication_model,
        formal_track_component=formal_track_component,
        product_order=product_order,
        integrated_product=integrated_product,
        bfo_projection_product=bfo_projection_product,
        current_track_formal_release=current_track_formal_release,
    )
