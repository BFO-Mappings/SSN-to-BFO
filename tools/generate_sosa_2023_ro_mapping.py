#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = (
    REPO_ROOT
    / "config/sosa-2023-ro-product.toml"
)

TARGET_PATTERN = re.compile(
    r"^(RO|BFO):([0-9]{7})$"
)

SOURCE_PATTERN = re.compile(
    r"^sosa:"
    r"[A-Za-z_]"
    r"[A-Za-z0-9_.-]*$"
)


class RoGenerationError(
    RuntimeError
):
    pass


def sha256_bytes(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def load_product_config() -> dict:
    with CONFIG_PATH.open(
        "rb"
    ) as handle:
        raw = tomllib.load(
            handle
        )

    if raw.get(
        "schema_version"
    ) != 1:
        raise RoGenerationError(
            "schema_version must be 1"
        )

    product = raw.get(
        "product"
    )

    if not isinstance(
        product,
        dict,
    ):
        raise RoGenerationError(
            "missing [product] table"
        )

    return product


def load_governed_rows(
    product: dict,
):
    sys.path.insert(
        0,
        str(REPO_ROOT / "tools"),
    )

    import generate_mapping_from_coms as coms

    workbook = (
        REPO_ROOT
        / product[
            "workbook_path"
        ]
    )

    rows, stats = (
        coms.read_workbook(
            workbook
        )
    )

    coms.validate_workbook_row_ids(
        rows,
        stats,
    )

    return rows


def validate_governance(
    product: dict,
    rows,
):
    governed_expected = product[
        "governed_property_count"
    ]

    if len(rows) != governed_expected:
        raise RoGenerationError(
            "governed-property count "
            f"mismatch: expected "
            f"{governed_expected}; "
            f"observed {len(rows)}"
        )

    counts = Counter(
        row.mapping_status_text
        for row in rows
    )

    expected_counts = Counter(
        {
            "active":
                product[
                    "active_axiom_count"
                ],
            "no_direct_mapping":
                product[
                    "no_direct_mapping_count"
                ],
        }
    )

    if counts != expected_counts:
        raise RoGenerationError(
            "mapping-status counts "
            f"differ: expected "
            f"{expected_counts}; "
            f"observed {counts}"
        )

    active = []

    for row in rows:
        status = (
            row.mapping_status_text
        )

        if status == "active":
            if (
                row.predicate_text
                != "rdfs:subPropertyOf"
            ):
                raise RoGenerationError(
                    f"{row.diagnostic_id}: "
                    "active RO row must use "
                    "rdfs:subPropertyOf"
                )

            if not SOURCE_PATTERN.fullmatch(
                row.subject_text
            ):
                raise RoGenerationError(
                    f"{row.diagnostic_id}: "
                    f"unsupported source "
                    f"{row.subject_text!r}"
                )

            match = TARGET_PATTERN.fullmatch(
                row.target_text
            )

            if match is None:
                raise RoGenerationError(
                    f"{row.diagnostic_id}: "
                    f"unsupported RO-profile "
                    f"target "
                    f"{row.target_text!r}"
                )

            if (
                "skos:"
                in row.predicate_text.lower()
                or
                "skos:"
                in row.target_text.lower()
            ):
                raise RoGenerationError(
                    f"{row.diagnostic_id}: "
                    "SKOS mapping is prohibited"
                )

            active.append(
                row
            )

        elif (
            status
            == "no_direct_mapping"
        ):
            if (
                row.predicate_text
                or row.target_text
            ):
                raise RoGenerationError(
                    f"{row.diagnostic_id}: "
                    "no_direct_mapping row "
                    "contains mapping content"
                )

        else:
            raise RoGenerationError(
                f"{row.diagnostic_id}: "
                f"unsupported mapping status "
                f"{status!r}"
            )

    return tuple(
        sorted(
            active,
            key=lambda row:
                row.subject_text,
        )
    )


def render_target(
    value: str,
) -> str:
    match = TARGET_PATTERN.fullmatch(
        value
    )

    if match is None:
        raise RoGenerationError(
            f"malformed target {value!r}"
        )

    prefix = match.group(1)
    identifier = match.group(2)

    return (
        "obo:"
        + prefix
        + "_"
        + identifier
    )


def render_product(
    product: dict,
    active,
) -> bytes:
    ontology_iri = product[
        "stable_ontology_iri"
    ]

    label = product[
        "label"
    ]

    if (
        '"' in label
        or "\n" in label
        or "\r" in label
    ):
        raise RoGenerationError(
            "product label is not "
            "safe for canonical Turtle"
        )

    lines = [
        "@prefix obo: "
        "<http://purl.obolibrary.org/obo/> .",
        "@prefix owl: "
        "<http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs: "
        "<http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix sosa: "
        "<http://www.w3.org/ns/sosa/> .",
        "",
        f"<{ontology_iri}>",
        "    a owl:Ontology ;",
        f'    rdfs:label "{label}"@en .',
        "",
    ]

    for row in active:
        lines.append(
            row.subject_text
            + " rdfs:subPropertyOf "
            + render_target(
                row.target_text
            )
            + " ."
        )

    lines.append(
        ""
    )

    return (
        "\n".join(lines)
        .encode("utf-8")
    )


def build() -> tuple[
    dict,
    tuple,
    bytes,
]:
    product = load_product_config()

    rows = load_governed_rows(
        product
    )

    active = validate_governance(
        product,
        rows,
    )

    rendered = render_product(
        product,
        active,
    )

    return (
        product,
        active,
        rendered,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the governed "
            "SOSA-2023 Relations "
            "Ontology mapping product."
        )
    )

    parser.add_argument(
        "--output",
        help=(
            "Output path. Defaults to "
            "the governed product path."
        ),
    )

    args = parser.parse_args()

    try:
        product, active, rendered = (
            build()
        )
    except (
        RoGenerationError,
        OSError,
        ValueError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    if args.output:
        output = Path(
            args.output
        )

        if not output.is_absolute():
            output = (
                REPO_ROOT
                / output
            )
    else:
        output = (
            REPO_ROOT
            / product[
                "output_path"
            ]
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_bytes(
        rendered
    )

    print(
        "Governed properties:",
        product[
            "governed_property_count"
        ],
    )

    print(
        "Active axioms:",
        len(active),
    )

    print(
        "No direct:",
        product[
            "no_direct_mapping_count"
        ],
    )

    print(
        "SKOS mappings: 0"
    )

    print(
        "Imports: 0"
    )

    print(
        "Output:",
        output,
    )

    print(
        "SHA-256:",
        sha256_bytes(
            rendered
        ),
    )

    print(
        "RO mapping generation: PASS"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
