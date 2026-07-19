#!/usr/bin/env python3
"""Validate governed publication metadata in development or release mode."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from publication_metadata import (
    PublicationMetadataError,
    ValidationIssue,
    format_issue,
    load_metadata,
    release_version_iri,
    sha256_file,
)
from release_context import (
    FormalReleaseContext,
    FormalReleaseContextError,
    format_issue as format_release_issue,
    parse_formal_release_context,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA = REPO_ROOT / "config/publication-metadata.toml"


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Exit codes: 0 success; 1 metadata, I/O, or semantic failure; 2 usage error.",
    )
    parser.add_argument(
        "--mode",
        choices=("development", "release"),
        default="development",
        help="Validation context. Default: development.",
    )
    parser.add_argument(
        "--metadata",
        default=str(DEFAULT_METADATA),
        help="Publication metadata TOML path.",
    )
    parser.add_argument("--release-id", help="Formal release identifier (release mode only).")
    parser.add_argument("--release-date", help="Formal release date (release mode only).")
    parser.add_argument("--git-tag", help="Intended Git tag (release mode only).")
    parser.add_argument("--source-commit", help="Exact source commit (release mode only).")
    return parser.parse_args(argv)


def validate_cli_context(args: argparse.Namespace) -> FormalReleaseContext | None:
    values = (args.release_id, args.release_date, args.git_tag, args.source_commit)
    if args.mode == "development":
        if any(value is not None for value in values):
            raise PublicationMetadataError(
                [
                    ValidationIssue(
                        code="DEVELOPMENT_RELEASE_ARGUMENT",
                        field="release_context",
                        message=(
                            "development mode does not accept --release-id, --release-date, "
                            "--git-tag, or --source-commit"
                        ),
                    )
                ]
            )
        return None

    option_names = ("--release-id", "--release-date", "--git-tag", "--source-commit")
    missing = [name for name, value in zip(option_names, values) if value is None]
    if missing:
        raise PublicationMetadataError(
            [
                ValidationIssue(
                    code="RELEASE_ARGUMENT_REQUIRED",
                    field="release_context",
                    message="release mode requires " + " and ".join(missing),
                )
            ]
        )
    return parse_formal_release_context(*values)


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    output = stdout or sys.stdout
    error_output = stderr or sys.stderr
    args = parse_args(argv)
    metadata_path = Path(args.metadata)

    try:
        release_context = validate_cli_context(args)
        metadata = load_metadata(metadata_path)
        metadata_sha256 = sha256_file(metadata_path)
    except PublicationMetadataError as exc:
        for issue in exc.issues:
            print(format_issue(issue), file=error_output)
        return 1
    except FormalReleaseContextError as exc:
        for issue in exc.issues:
            print(format_release_issue(issue), file=error_output)
        return 1
    except OSError as exc:
        issue = ValidationIssue(
            code="METADATA_IO",
            field=str(metadata_path),
            message=f"cannot hash metadata: {exc}",
        )
        print(format_issue(issue), file=error_output)
        return 1

    print("Publication metadata validation: PASS", file=output)
    print(f"Mode: {args.mode}", file=output)
    print(f"Metadata file: {display_path(metadata_path)}", file=output)
    print(f"Metadata SHA-256: {metadata_sha256}", file=output)
    print(f"Schema version: {metadata.schema_version}", file=output)
    print(f"Project title: {metadata.publication.project_title}", file=output)
    print(f"Default language: {metadata.publication.default_language}", file=output)
    print(f"Release IRI base: {metadata.publication.release_iri_base}", file=output)
    print(f"License IRI: {metadata.publication.license_iri}", file=output)
    print(f"Repository IRI: {metadata.publication.repository_iri}", file=output)
    print(f"Generated warning: {metadata.publication.generated_warning}", file=output)
    print(
        "Development status property IRI: "
        f"{metadata.publication.development_status_property_iri}",
        file=output,
    )
    print(
        f"Development status IRI: {metadata.publication.development_status_iri}",
        file=output,
    )
    print(
        f"Formal release status IRI: {metadata.publication.formal_release_status_iri}",
        file=output,
    )
    print(f"Canonical product count: {len(metadata.products)}", file=output)
    print(
        "Canonical product order: "
        + ", ".join(product.key for product in metadata.products),
        file=output,
    )

    for product in metadata.products:
        print(f"Product: {product.key}", file=output)
        print(f"  path: {product.path}", file=output)
        print(f"  stable ontology IRI: {product.stable_ontology_iri}", file=output)
        print(f"  release suffix: {product.release_iri_suffix}", file=output)
        print(f"  label: {product.label}", file=output)
        print(f"  description: {product.description}", file=output)
        print(f"  product-type IRI: {product.product_type_iri}", file=output)

    if release_context is None:
        print("Immutable release version IRI: not claimed in development mode.", file=output)
        return 0

    print(f"Release identifier: {release_context.release_identifier}", file=output)
    print(f"Release date: {release_context.release_date}", file=output)
    print(f"Intended Git tag: {release_context.git_tag}", file=output)
    print(f"Source commit: {release_context.source_commit}", file=output)
    print(
        "Release context classification: illustrative validation input only; "
        "no formal artifact was built.",
        file=output,
    )
    for product in metadata.products:
        print(
            f"Version IRI [{product.key}]: "
            f"{release_version_iri(metadata, product.key, release_context)}",
            file=output,
        )
    print(
        "Foundation limitation: Git tag existence/binding and version-IRI byte "
        "immutability are not checked.",
        file=output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
