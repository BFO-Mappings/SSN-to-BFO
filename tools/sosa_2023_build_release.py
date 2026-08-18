#!/usr/bin/env python3
"""Build one deterministic SOSA-2023 formal-release candidate package."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
from xml.etree import ElementTree
from xml.sax.saxutils import quoteattr

from rdflib import Graph, OWL, RDF, URIRef
from rdflib.compare import isomorphic

import check_sosa_next_mapping as mapping_checker
import generate_mapping_from_coms as coms
import generate_sosa_next_products as products
import publication_metadata as publication
from release_context import (
    FormalReleaseContext,
    parse_formal_release_context,
    validate_formal_release_context,
)
import sosa_2023_release_manifest as manifest
import sosa_2023_release_runtime as runtime


REPO_ROOT = Path(__file__).resolve().parents[1]

PRODUCT_ORDER = manifest.PRODUCT_ORDER
PRODUCT_PACKAGE_PATHS = manifest.PRODUCT_PACKAGE_PATHS
INCLUDED_FILE_PATHS = manifest.INCLUDED_FILE_PATH_ORDER

PACKAGE_FILE_PATHS = tuple(
    sorted(
        (
            *INCLUDED_FILE_PATHS,
            "manifest.json",
            "SHA256SUMS",
        )
    )
)

CHECKSUM_PATHS = tuple(
    value
    for value in PACKAGE_FILE_PATHS
    if value != "SHA256SUMS"
)

if len(PACKAGE_FILE_PATHS) != 13:
    raise RuntimeError(
        "SOSA-2023 complete package must contain 13 files"
    )

if len(CHECKSUM_PATHS) != 12:
    raise RuntimeError(
        "SOSA-2023 checksum inventory must contain 12 files"
    )

if tuple(
    value
    for value in PACKAGE_FILE_PATHS
    if value not in {"manifest.json", "SHA256SUMS"}
) != tuple(sorted(INCLUDED_FILE_PATHS)):
    raise RuntimeError(
        "complete-package and included-file inventories differ"
    )

DEVELOPMENT_OUTPUT_PATHS = (
    "releases/sosa-next/sosa-integrated.ttl",
    "releases/sosa-next/sosa-bfo-mapping.ttl",
    "releases/sosa-next/sosa-cco-extension.ttl",
)

CATALOG_NAMESPACE = (
    "urn:oasis:names:tc:entity:xmlns:xml:catalog"
)

TEMP_PREFIX = ".sosa-2023-release-package-build-"


ReleasePackageIssue = runtime.ReleasePackageIssue
ReleasePackageError = runtime.ReleasePackageError
DevelopmentSnapshot = runtime.DevelopmentSnapshot
ResolvedValidationToolchain = runtime.ResolvedValidationToolchain

package_issue = runtime.package_issue
sha256_bytes = runtime.sha256_bytes
validate_release_notes_bytes = (
    runtime.validate_release_notes_bytes
)
resolve_validation_toolchain = (
    runtime.resolve_validation_toolchain
)
verified_robot_launcher = (
    runtime.verified_robot_launcher
)


@dataclass(frozen=True)
class AssembledReleasePackage:
    manifest: manifest.ReleaseManifest
    manifest_bytes: bytes
    catalog_bytes: bytes
    sha256sums_bytes: bytes


def _sha256(path: Path) -> str:
    return sha256_bytes(
        path.read_bytes()
    )


def snapshot_development_outputs(
    repository_root: Path,
) -> tuple[DevelopmentSnapshot, ...]:
    values: list[DevelopmentSnapshot] = []

    for relative in DEVELOPMENT_OUTPUT_PATHS:
        path = repository_root / relative
        content = path.read_bytes()

        values.append(
            DevelopmentSnapshot(
                relative,
                content,
                sha256_bytes(content),
                path.stat().st_mtime_ns,
            )
        )

    return tuple(values)


def development_snapshot_issues(
    repository_root: Path,
    snapshots: Iterable[DevelopmentSnapshot],
) -> tuple[ReleasePackageIssue, ...]:
    issues: list[ReleasePackageIssue] = []

    for snapshot in snapshots:
        path = repository_root / snapshot.path

        if not path.is_file():
            issues.append(
                package_issue(
                    "DEVELOPMENT_OUTPUT_MISSING",
                    snapshot.path,
                    "file is absent",
                )
            )
            continue

        content = path.read_bytes()

        if (
            content != snapshot.content
            or sha256_bytes(content)
            != snapshot.sha256
        ):
            issues.append(
                package_issue(
                    "DEVELOPMENT_OUTPUT_MUTATED",
                    snapshot.path,
                    "bytes changed",
                )
            )

        if path.stat().st_mtime_ns != snapshot.mtime_ns:
            issues.append(
                package_issue(
                    "DEVELOPMENT_OUTPUT_MTIME",
                    snapshot.path,
                    "mtime changed",
                )
            )

    return tuple(
        sorted(
            set(issues),
            key=lambda value: value.sort_key,
        )
    )


def collect_validation_environment(
    repository_root: Path,
    toolchain: ResolvedValidationToolchain,
) -> manifest.ReleaseManifestValidationEnvironment:
    toolchain_path = (
        "config/validation-toolchain.env"
    )
    requirements_path = (
        "requirements/validation.txt"
    )

    return manifest.ReleaseManifestValidationEnvironment(
        python_implementation=platform.python_implementation(),
        python_version=platform.python_version(),
        java_vendor=toolchain.java_vendor,
        java_version=toolchain.java_version,
        java_vm_name=toolchain.java_vm_name,
        robot_artifact=toolchain.robot_artifact,
        robot_version=toolchain.robot_version,
        robot_sha256=toolchain.robot_jar_sha256,
        toolchain_path=toolchain_path,
        toolchain_sha256=_sha256(
            repository_root / toolchain_path
        ),
        requirements_path=requirements_path,
        requirements_sha256=_sha256(
            repository_root / requirements_path
        ),
    )


def collect_dependencies(
    repository_root: Path,
) -> tuple[
    manifest.ReleaseManifestDependency,
    ...
]:
    values: list[
        manifest.ReleaseManifestDependency
    ] = []

    for (
        key,
        role,
        relative,
        expected_ontology_iri,
    ) in manifest.DEPENDENCY_POLICIES:
        path = repository_root / relative

        graph = Graph().parse(
            path,
            format="turtle",
        )

        ontology_iris = sorted(
            str(value)
            for value in graph.subjects(
                RDF.type,
                OWL.Ontology,
            )
            if isinstance(value, URIRef)
        )

        if ontology_iris != [
            expected_ontology_iri
        ]:
            raise ReleasePackageError(
                (
                    package_issue(
                        "DEPENDENCY_ONTOLOGY_IDENTITY",
                        relative,
                        "expected "
                        f"{[expected_ontology_iri]!r}, "
                        f"got {ontology_iris!r}",
                    ),
                )
            )

        version_iris = sorted(
            str(value)
            for value in graph.objects(
                URIRef(expected_ontology_iri),
                OWL.versionIRI,
            )
            if isinstance(value, URIRef)
        )

        if len(version_iris) > 1:
            raise ReleasePackageError(
                (
                    package_issue(
                        "DEPENDENCY_VERSION_IDENTITY",
                        relative,
                        "expected at most one "
                        "version IRI, got "
                        f"{version_iris!r}",
                    ),
                )
            )

        values.append(
            manifest.ReleaseManifestDependency(
                key=key,
                role=role,
                path=relative,
                ontology_iri=(
                    expected_ontology_iri
                ),
                version_iri=(
                    version_iris[0]
                    if version_iris
                    else None
                ),
                sha256=_sha256(path),
                byte_size=path.stat().st_size,
            )
        )

    return tuple(values)


def process_workbook(
    workbook_path: Path,
    temporary_root: Path,
) -> tuple[
    list[coms.ProcessedRow],
    dict[str, int],
]:
    temporary_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    mapping_checker.validate_source_pins()

    merged_source = (
        temporary_root
        / "sosa-2023-source-merged.ttl"
    )

    mapping_checker.build_merged_source(
        merged_source
    )

    rows, workbook_stats = (
        coms.read_workbook(
            workbook_path
        )
    )

    coms.validate_workbook_row_ids(
        rows,
        workbook_stats,
    )

    (
        active,
        deferred,
        explicitly_unmapped,
    ) = products.classify_workbook_rows(
        rows
    )

    counts = {
        "governed_row_count": len(rows),
        "unique_row_id_count": (
            workbook_stats.unique_row_id_count
        ),
        "active_mapping_count": len(active),
        "deferred_mapping_count": len(
            deferred
        ),
        "explicitly_unmapped_row_count": len(
            explicitly_unmapped
        ),
    }

    for (
        key,
        expected,
    ) in products.EXPECTED_WORKBOOK_COUNTS.items():
        if (
            key
            == "canonical_authoritative_axiom_count"
        ):
            continue

        actual = counts[key]

        if actual != expected:
            raise ReleasePackageError(
                (
                    package_issue(
                        "WORKBOOK_COUNT",
                        key,
                        f"expected {expected}, "
                        f"got {actual}",
                    ),
                )
            )

    previous_prefix_files = dict(
        coms.PREFIX_FILES
    )

    previous_source_imports = tuple(
        coms.SOURCE_IMPORTS
    )

    stats = coms.WorkbookStats(
        worksheets_read=list(
            workbook_stats.worksheets_read
        )
    )

    mapping_checker.configure_coms_resolver(
        merged_source
    )

    try:
        processed = (
            coms.validate_and_process_rows(
                active,
                coms.Resolver(),
                stats,
            )
        )
    finally:
        coms.PREFIX_FILES = (
            previous_prefix_files
        )
        coms.SOURCE_IMPORTS = (
            previous_source_imports
        )

    if dict(coms.PREFIX_FILES) != (
        previous_prefix_files
    ):
        raise ReleasePackageError(
            (
                package_issue(
                    "RESOLVER_STATE",
                    "PREFIX_FILES",
                    "resolver prefix state "
                    "was not restored",
                ),
            )
        )

    if tuple(coms.SOURCE_IMPORTS) != (
        previous_source_imports
    ):
        raise ReleasePackageError(
            (
                package_issue(
                    "RESOLVER_STATE",
                    "SOURCE_IMPORTS",
                    "resolver source-import "
                    "state was not restored",
                ),
            )
        )

    expected_active = (
        products.EXPECTED_WORKBOOK_COUNTS[
            "canonical_authoritative_axiom_count"
        ]
    )

    if len(processed) != expected_active:
        raise ReleasePackageError(
            (
                package_issue(
                    "PROCESSED_MAPPING_COUNT",
                    "workbook",
                    f"expected {expected_active}, "
                    f"got {len(processed)}",
                ),
            )
        )

    return processed, counts


def render_formal_products(
    context: FormalReleaseContext,
    workbook_path: Path,
    metadata_path: Path,
    temporary_root: Path,
    *,
    reverse_input: bool = False,
) -> tuple[
    publication.PublicationMetadata,
    dict[str, dict[str, object]],
]:
    validated_context = (
        validate_formal_release_context(
            context
        )
    )

    metadata = publication.load_metadata(
        metadata_path,
        product_order=PRODUCT_ORDER,
    )

    processed, _ = process_workbook(
        workbook_path,
        temporary_root,
    )

    records, _ = (
        products.build_product_records(
            processed
        )
    )

    rendered: dict[
        str,
        dict[str, object],
    ] = {}

    logical_graphs: dict[
        str,
        Graph,
    ] = {}

    for key in PRODUCT_ORDER:
        if key == "integrated":
            supplied = [
                *records[
                    "strict_bfo_mapping"
                ],
                *records[
                    "cco_extension"
                ],
            ]
        else:
            supplied = list(
                records[key]
            )

        if reverse_input:
            supplied = list(
                reversed(supplied)
            )

        (
            serialized,
            logical,
            result,
        ) = products.serialize_formal_product(
            metadata,
            validated_context,
            key,
            supplied,
        )

        rendered[key] = {
            **result,
            "serialized_bytes": serialized,
            "logical_graph": logical,
        }

        logical_graphs[key] = logical

    modular_union = Graph()

    for key in (
        "strict_bfo_mapping",
        "cco_extension",
    ):
        for triple in logical_graphs[key]:
            modular_union.add(triple)

    if len(modular_union) != 277:
        raise ReleasePackageError(
            (
                package_issue(
                    "FORMAL_LOGICAL_UNION",
                    "products",
                    "expected 277 triples, "
                    f"got {len(modular_union)}",
                ),
            )
        )

    if not isomorphic(
        modular_union,
        logical_graphs["integrated"],
    ):
        raise ReleasePackageError(
            (
                package_issue(
                    "FORMAL_LOGICAL_UNION",
                    "products",
                    "modular logical union "
                    "differs from Integrated",
                ),
            )
        )

    return metadata, rendered


def formal_product_bytes(
    rendered: Mapping[
        str,
        Mapping[str, object],
    ],
) -> dict[str, bytes]:
    return {
        key: rendered[key][
            "serialized_bytes"
        ]
        for key in PRODUCT_ORDER
    }


def collect_product_records(
    rendered: Mapping[
        str,
        Mapping[str, object],
    ],
    metadata: publication.PublicationMetadata,
    context: FormalReleaseContext,
) -> tuple[
    manifest.ReleaseManifestProduct,
    ...
]:
    metadata_by_key = {
        value.key: value
        for value in metadata.products
    }

    values: list[
        manifest.ReleaseManifestProduct
    ] = []

    for key in PRODUCT_ORDER:
        result = rendered[key]
        static = (
            manifest.PRODUCT_STATIC_EVIDENCE[
                key
            ]
        )

        if int(result["byte_size"]) != (
            static["byte_size"]
        ):
            raise ReleasePackageError(
                (
                    package_issue(
                        "PRODUCT_BYTE_SIZE",
                        key,
                        "expected "
                        f"{static['byte_size']}, "
                        f"got "
                        f"{result['byte_size']}",
                    ),
                )
            )

        if int(
            result["logical_triple_count"]
        ) != static[
            "logical_triple_count"
        ]:
            raise ReleasePackageError(
                (
                    package_issue(
                        "PRODUCT_LOGICAL_COUNT",
                        key,
                        "formal logical triple "
                        "count differs from "
                        "manifest authority",
                    ),
                )
            )

        if int(
            result["total_triple_count"]
        ) != static[
            "total_triple_count"
        ]:
            raise ReleasePackageError(
                (
                    package_issue(
                        "PRODUCT_TOTAL_COUNT",
                        key,
                        "formal total triple "
                        "count differs from "
                        "manifest authority",
                    ),
                )
            )

        imports = tuple(
            str(value)
            for value in result["imports"]
        )

        expected_imports = (
            manifest.expected_product_imports(
                key,
                context.release_date,
            )
        )

        if imports != expected_imports:
            raise ReleasePackageError(
                (
                    package_issue(
                        "PRODUCT_IMPORTS",
                        key,
                        "expected "
                        f"{expected_imports!r}, "
                        f"got {imports!r}",
                    ),
                )
            )

        values.append(
            manifest.ReleaseManifestProduct(
                key=key,
                path=(
                    PRODUCT_PACKAGE_PATHS[
                        key
                    ]
                ),
                stable_ontology_iri=(
                    metadata_by_key[
                        key
                    ].stable_ontology_iri
                ),
                version_iri=(
                    publication
                    .release_version_iri(
                        metadata,
                        key,
                        context,
                    )
                ),
                imports=imports,
                sha256=str(
                    result["sha256"]
                ),
                byte_size=int(
                    result["byte_size"]
                ),
                ontology_declaration_count=(
                    static[
                        "ontology_declaration_count"
                    ]
                ),
                import_count=static[
                    "import_count"
                ],
                static_metadata_count=(
                    static[
                        "static_metadata_count"
                    ]
                ),
                formal_metadata_count=(
                    static[
                        "formal_metadata_count"
                    ]
                ),
                logical_triple_count=(
                    static[
                        "logical_triple_count"
                    ]
                ),
                total_triple_count=(
                    static[
                        "total_triple_count"
                    ]
                ),
                direct_governed_axiom_count=(
                    static[
                        "direct_governed_axiom_count"
                    ]
                ),
                governed_closure_axiom_count=(
                    static[
                        "governed_closure_axiom_count"
                    ]
                ),
                reasoning_mode=static[
                    "reasoning_mode"
                ],
            )
        )

    return tuple(values)


def collect_inputs(
    repository_root: Path,
    notes_relative: str,
    *,
    notes_bytes: bytes | None = None,
) -> tuple[
    manifest.ReleaseManifestInput,
    ...
]:
    values: list[
        manifest.ReleaseManifestInput
    ] = []

    for (
        key,
        source,
        package_path,
    ) in manifest.INPUT_POLICIES:
        if key == "release_notes":
            source = notes_relative

            if notes_bytes is None:
                content = (
                    repository_root
                    / source
                ).read_bytes()
            else:
                content = notes_bytes
        else:
            if source is None:
                raise ReleasePackageError(
                    (
                        package_issue(
                            "INPUT_POLICY",
                            key,
                            "non-note input has "
                            "no source path",
                        ),
                    )
                )

            content = (
                repository_root
                / source
            ).read_bytes()

        values.append(
            manifest.ReleaseManifestInput(
                key=key,
                source_path=source,
                package_path=package_path,
                sha256=sha256_bytes(
                    content
                ),
                byte_size=len(content),
            )
        )

    return tuple(values)


def collect_included_files(
    package_dir: Path,
) -> tuple[
    manifest.ReleaseManifestIncludedFile,
    ...
]:
    roles = {
        "LICENSE": "project license",
        "RELEASE-NOTES.md": (
            "release notes"
        ),
        "catalog-v001.xml": (
            "formal version-IRI catalog"
        ),
        PRODUCT_PACKAGE_PATHS[
            "integrated"
        ]: (
            "formal Integrated ontology "
            "product"
        ),
        PRODUCT_PACKAGE_PATHS[
            "strict_bfo_mapping"
        ]: (
            "formal Strict BFO Mapping "
            "ontology product"
        ),
        PRODUCT_PACKAGE_PATHS[
            "cco_extension"
        ]: (
            "formal CCO Extension "
            "ontology product"
        ),
        "sources/SOSA-2023-to-BFO-COMS.xlsx": (
            "governed SOSA-2023 COMS "
            "workbook"
        ),
        "sources/product-role-policy.toml": (
            "governed product-role policy"
        ),
        "sources/sosa-2023-publication-metadata.toml": (
            "governed SOSA-2023 "
            "publication metadata"
        ),
        "sources/sosa-release-scope.toml": (
            "governed SOSA release-scope "
            "policy"
        ),
        "sources/sosa-source-version.toml": (
            "governed immutable SOSA "
            "source-version evidence"
        ),
    }

    if set(roles) != set(
        INCLUDED_FILE_PATHS
    ):
        raise RuntimeError(
            "included-file role map differs "
            "from manifest inventory"
        )

    return tuple(
        manifest.ReleaseManifestIncludedFile(
            path=relative,
            role=roles[relative],
            sha256=_sha256(
                package_dir / relative
            ),
            byte_size=(
                package_dir
                / relative
            ).stat().st_size,
        )
        for relative in INCLUDED_FILE_PATHS
    )


def _copy_package_inputs(
    repository_root: Path,
    notes_bytes: bytes,
    package_dir: Path,
) -> None:
    for (
        key,
        source,
        package_path,
    ) in manifest.INPUT_POLICIES:
        if package_path is None:
            continue

        if key == "release_notes":
            content = notes_bytes
        else:
            if source is None:
                raise RuntimeError(
                    f"{key}: copied input "
                    "has no source"
                )

            content = (
                repository_root
                / source
            ).read_bytes()

        destination = (
            package_dir
            / package_path
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_bytes(
            content
        )


def canonical_catalog_bytes(
    metadata: publication.PublicationMetadata,
    context: FormalReleaseContext,
) -> bytes:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<catalog xmlns="'
            f'{CATALOG_NAMESPACE}">'
        ),
    ]

    for key in PRODUCT_ORDER:
        version_iri = (
            publication.release_version_iri(
                metadata,
                key,
                context,
            )
        )

        lines.append(
            "  <uri "
            f"name={quoteattr(version_iri)} "
            "uri="
            f"{quoteattr(PRODUCT_PACKAGE_PATHS[key])}"
            "/>"
        )

    lines.append("</catalog>")

    return (
        "\n".join(lines)
        + "\n"
    ).encode("utf-8")


def validate_catalog_bytes(
    value: bytes,
    metadata: publication.PublicationMetadata,
    context: FormalReleaseContext,
) -> tuple[
    ReleasePackageIssue,
    ...
]:
    if any(
        token in value
        for token in (
            b"<!DOCTYPE",
            b"<!ENTITY",
            b"<!--",
        )
    ):
        return (
            package_issue(
                "CATALOG_PROHIBITED_XML",
                "catalog-v001.xml",
                "DTD, entity, and comments "
                "are prohibited",
            ),
        )

    issues: list[
        ReleasePackageIssue
    ] = []

    try:
        root = ElementTree.fromstring(
            value
        )
    except (
        ElementTree.ParseError,
        UnicodeDecodeError,
    ) as exc:
        return (
            package_issue(
                "CATALOG_XML",
                "catalog-v001.xml",
                str(exc),
            ),
        )

    if root.tag != (
        f"{{{CATALOG_NAMESPACE}}}"
        "catalog"
    ):
        issues.append(
            package_issue(
                "CATALOG_ROOT",
                "catalog-v001.xml",
                "wrong catalog namespace "
                "or root",
            )
        )

    entries = [
        (
            child.attrib.get("name"),
            child.attrib.get("uri"),
        )
        for child in root
    ]

    expected = [
        (
            publication.release_version_iri(
                metadata,
                key,
                context,
            ),
            PRODUCT_PACKAGE_PATHS[key],
        )
        for key in PRODUCT_ORDER
    ]

    if entries != expected:
        issues.append(
            package_issue(
                "CATALOG_ENTRIES",
                "catalog-v001.xml",
                "version-IRI mappings differ",
            )
        )

    if value != canonical_catalog_bytes(
        metadata,
        context,
    ):
        issues.append(
            package_issue(
                "NONCANONICAL_CATALOG",
                "catalog-v001.xml",
                "bytes differ from "
                "canonical XML",
            )
        )

    return tuple(
        sorted(
            set(issues),
            key=lambda item: item.sort_key,
        )
    )


def canonical_sha256sums_bytes(
    package_dir: Path,
) -> bytes:
    lines = [
        f"{_sha256(package_dir / path)}  "
        f"{path}"
        for path in CHECKSUM_PATHS
    ]

    return (
        "\n".join(lines)
        + "\n"
    ).encode("ascii")


def validate_sha256sums_bytes(
    package_dir: Path,
    value: bytes,
) -> tuple[
    ReleasePackageIssue,
    ...
]:
    expected = (
        canonical_sha256sums_bytes(
            package_dir
        )
    )

    if value == expected:
        return ()

    return (
        package_issue(
            "NONCANONICAL_CHECKSUMS",
            "SHA256SUMS",
            "bytes differ from exact "
            "canonical checksums",
        ),
    )


def run_independent_reasoning(
    package_dir: Path,
    temporary_root: Path,
    toolchain: ResolvedValidationToolchain,
) -> tuple[
    manifest.ReleaseManifestHermitResult,
    ...
]:
    serialized = {
        key: (
            package_dir
            / PRODUCT_PACKAGE_PATHS[key]
        ).read_bytes()
        for key in PRODUCT_ORDER
    }

    profiles = {
        "integrated": (
            products.build_reasoning_closure(
                (
                    serialized[
                        "integrated"
                    ],
                ),
                include_target_dependency=True,
            )
        ),
        "strict_bfo_mapping": (
            products.build_reasoning_closure(
                (
                    serialized[
                        "strict_bfo_mapping"
                    ],
                ),
                include_target_dependency=True,
            )
        ),
        "cco_extension": (
            products.build_reasoning_closure(
                (
                    serialized[
                        "cco_extension"
                    ],
                    serialized[
                        "strict_bfo_mapping"
                    ],
                ),
                include_target_dependency=True,
            )
        ),
    }

    expected_closures = dict(
        manifest
        .FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS
    )

    evidence: list[
        manifest.ReleaseManifestHermitResult
    ] = []

    issues: list[
        ReleasePackageIssue
    ] = []

    with verified_robot_launcher(
        toolchain,
        temporary_root,
    ) as launcher:
        for key in PRODUCT_ORDER:
            closure = profiles[key]

            if list(
                closure.triples(
                    (
                        None,
                        OWL.imports,
                        None,
                    )
                )
            ):
                issues.append(
                    package_issue(
                        "HERMIT_CLOSURE_IMPORTS",
                        key,
                        "fixed validation closure "
                        "retains owl:imports",
                    )
                )
                continue

            expected_count = (
                expected_closures[key]
            )

            if len(closure) != (
                expected_count
            ):
                issues.append(
                    package_issue(
                        "HERMIT_CLOSURE_COUNT",
                        key,
                        f"expected "
                        f"{expected_count}, "
                        f"got {len(closure)}",
                    )
                )

            root = (
                temporary_root
                / key
            )

            root.mkdir(
                parents=True,
                exist_ok=True,
            )

            closure_path = (
                root / "closure.ttl"
            )

            reasoned_path = (
                root / "reasoned.ttl"
            )

            unsat_path = (
                root
                / "unsatisfiable.ttl"
            )

            closure.serialize(
                closure_path,
                format="turtle",
            )

            result = (
                mapping_checker
                .run_reasoner(
                    str(launcher),
                    closure_path,
                    reasoned_path,
                    unsat_path,
                )
            )

            inferred_unsats = {
                URIRef(value)
                for value in result[
                    "unsatisfiable_classes"
                ]
            }

            reasoned_output_produced = bool(
                result[
                    "reasoned_output_exists"
                ]
                and reasoned_path.is_file()
                and reasoned_path.stat().st_size
                > 0
            )

            if reasoned_output_produced:
                reasoned_graph = (
                    Graph().parse(
                        reasoned_path,
                        format="turtle",
                    )
                )

                inferred_unsats |= set(
                    coms.unsat_classes(
                        reasoned_graph
                    )
                )

            return_code = (
                -1
                if result[
                    "return_code"
                ]
                is None
                else int(
                    result[
                        "return_code"
                    ]
                )
            )

            passed = (
                return_code == 0
                and reasoned_output_produced
                and not inferred_unsats
                and len(closure)
                == expected_count
            )

            if not passed:
                issues.append(
                    package_issue(
                        "HERMIT_FAILED",
                        key,
                        str(
                            result.get(
                                "robot_output"
                            )
                            or result
                        ),
                    )
                )

            evidence.append(
                manifest
                .ReleaseManifestHermitResult(
                    product_key=key,
                    status=(
                        "PASS"
                        if passed
                        else "FAIL"
                    ),
                    fixed_closure_triple_count=(
                        len(closure)
                    ),
                    return_code=return_code,
                    reasoned_output_produced=(
                        reasoned_output_produced
                    ),
                    named_unsatisfiable_class_count=(
                        len(
                            inferred_unsats
                        )
                    ),
                    owl_nothing_equivalent_named_class_count=(
                        len(
                            inferred_unsats
                        )
                    ),
                )
            )

    if issues:
        raise ReleasePackageError(
            issues
        )

    return tuple(evidence)


def _validate_paths(
    context: FormalReleaseContext,
    notes_source: Path,
    output_dir: Path,
    repository_root: Path,
) -> str:
    if output_dir.name != (
        context.release_identifier
    ):
        raise ReleasePackageError(
            (
                package_issue(
                    "OUTPUT_BASENAME",
                    "output_dir",
                    "expected basename "
                    f"{context.release_identifier!r}",
                ),
            )
        )

    if os.path.lexists(
        output_dir
    ):
        raise ReleasePackageError(
            (
                package_issue(
                    "OUTPUT_EXISTS",
                    "output_dir",
                    "output directory "
                    "already exists",
                ),
            )
        )

    if not output_dir.parent.is_dir():
        raise ReleasePackageError(
            (
                package_issue(
                    "OUTPUT_PARENT",
                    "output_dir",
                    "parent directory "
                    "does not exist",
                ),
            )
        )

    resolved_repo = (
        repository_root.resolve()
    )

    resolved_notes = (
        notes_source.resolve()
    )

    try:
        relative = (
            resolved_notes
            .relative_to(
                resolved_repo
            )
            .as_posix()
        )
    except ValueError as exc:
        raise ReleasePackageError(
            (
                package_issue(
                    "NOTES_OUTSIDE_REPOSITORY",
                    "notes_source",
                    "notes must be inside "
                    "repository",
                ),
            )
        ) from exc

    if relative == (
        "release-notes/TEMPLATE.md"
    ):
        raise ReleasePackageError(
            (
                package_issue(
                    "RELEASE_NOTES_TEMPLATE",
                    "notes_source",
                    "template cannot "
                    "be packaged",
                ),
            )
        )

    if notes_source.is_symlink():
        raise ReleasePackageError(
            (
                package_issue(
                    "RELEASE_NOTES_SYMLINK",
                    "notes_source",
                    "notes must be a regular "
                    "repository file",
                ),
            )
        )

    if not resolved_notes.is_file():
        raise ReleasePackageError(
            (
                package_issue(
                    "RELEASE_NOTES_MISSING",
                    "notes_source",
                    "notes file is absent",
                ),
            )
        )

    return relative


def assemble_release_package(
    context: FormalReleaseContext,
    notes_bytes: bytes,
    notes_relative: str,
    package_dir: Path,
    repository_root: Path,
    toolchain: ResolvedValidationToolchain,
    snapshots: tuple[
        DevelopmentSnapshot,
        ...
    ],
    *,
    reverse_input: bool = False,
) -> AssembledReleasePackage:
    package_dir = Path(
        package_dir
    )

    repository_root = (
        repository_root.resolve()
    )

    if os.path.lexists(
        package_dir
    ):
        raise ReleasePackageError(
            (
                package_issue(
                    "ASSEMBLY_OUTPUT_EXISTS",
                    "package_dir",
                    "assembly directory exists",
                ),
            )
        )

    if not package_dir.parent.is_dir():
        raise ReleasePackageError(
            (
                package_issue(
                    "ASSEMBLY_PARENT",
                    "package_dir",
                    "assembly parent "
                    "does not exist",
                ),
            )
        )

    note_issues = (
        validate_release_notes_bytes(
            notes_bytes,
            template_bytes=(
                repository_root
                / "release-notes/TEMPLATE.md"
            ).read_bytes(),
        )
    )

    if note_issues:
        raise ReleasePackageError(
            note_issues
        )

    package_dir.mkdir()

    work_root = (
        package_dir.parent
        / (
            f".{package_dir.name}"
            "-sosa-2023-build-work"
        )
    )

    shutil.rmtree(
        work_root,
        ignore_errors=True,
    )

    work_root.mkdir()

    try:
        _copy_package_inputs(
            repository_root,
            notes_bytes,
            package_dir,
        )

        metadata, rendered = (
            render_formal_products(
                context,
                package_dir
                / (
                    "sources/"
                    "SOSA-2023-to-BFO-COMS.xlsx"
                ),
                package_dir
                / (
                    "sources/"
                    "sosa-2023-publication-"
                    "metadata.toml"
                ),
                work_root / "render",
                reverse_input=reverse_input,
            )
        )

        for (
            key,
            value,
        ) in formal_product_bytes(
            rendered
        ).items():
            destination = (
                package_dir
                / PRODUCT_PACKAGE_PATHS[
                    key
                ]
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination.write_bytes(
                value
            )

        catalog = (
            canonical_catalog_bytes(
                metadata,
                context,
            )
        )

        catalog_issues = (
            validate_catalog_bytes(
                catalog,
                metadata,
                context,
            )
        )

        if catalog_issues:
            raise ReleasePackageError(
                catalog_issues
            )

        (
            package_dir
            / "catalog-v001.xml"
        ).write_bytes(
            catalog
        )

        hermit = (
            run_independent_reasoning(
                package_dir,
                work_root / "reasoning",
                toolchain,
            )
        )

        snapshot_issues = (
            development_snapshot_issues(
                repository_root,
                snapshots,
            )
        )

        if snapshot_issues:
            raise ReleasePackageError(
                snapshot_issues
            )

        validation = (
            manifest.ReleaseManifestValidation(
                strict_turtle_parsing=True,
                formal_metadata_validation=True,
                serialized_header_validation=True,
                governed_axiom_reconciliation=True,
                import_graph_validation=True,
                catalog_validation=True,
                checksum_validation=True,
                development_artifact_nonmutation=True,
                deterministic_package_rebuild=True,
                hermit_results=hermit,
            )
        )

        release_manifest = (
            manifest.build_release_manifest(
                release_identifier=(
                    context.release_identifier
                ),
                release_date=(
                    context.release_date
                ),
                git_tag=context.git_tag,
                source_commit=(
                    context.source_commit
                ),
                repository_iri=(
                    metadata.publication
                    .repository_iri
                ),
                inputs=collect_inputs(
                    repository_root,
                    notes_relative,
                    notes_bytes=notes_bytes,
                ),
                product_order=(
                    PRODUCT_ORDER
                ),
                products=(
                    collect_product_records(
                        rendered,
                        metadata,
                        context,
                    )
                ),
                dependencies=(
                    collect_dependencies(
                        repository_root
                    )
                ),
                validation_environment=(
                    collect_validation_environment(
                        repository_root,
                        toolchain,
                    )
                ),
                validation=validation,
                included_files=(
                    collect_included_files(
                        package_dir
                    )
                ),
            )
        )

        manifest_bytes = (
            manifest
            .canonical_manifest_bytes(
                release_manifest
            )
        )

        (
            package_dir
            / "manifest.json"
        ).write_bytes(
            manifest_bytes
        )

        (
            manifest
            .load_and_validate_release_manifest(
                package_dir
                / "manifest.json"
            )
        )

        sums = (
            canonical_sha256sums_bytes(
                package_dir
            )
        )

        (
            package_dir
            / "SHA256SUMS"
        ).write_bytes(
            sums
        )

        checksum_issues = (
            validate_sha256sums_bytes(
                package_dir,
                sums,
            )
        )

        if checksum_issues:
            raise ReleasePackageError(
                checksum_issues
            )

        return AssembledReleasePackage(
            manifest=release_manifest,
            manifest_bytes=manifest_bytes,
            catalog_bytes=catalog,
            sha256sums_bytes=sums,
        )
    except Exception:
        shutil.rmtree(
            package_dir,
            ignore_errors=True,
        )
        raise
    finally:
        shutil.rmtree(
            work_root,
            ignore_errors=True,
        )


def compare_complete_packages(
    first: Path,
    second: Path,
) -> tuple[
    ReleasePackageIssue,
    ...
]:
    issues: list[
        ReleasePackageIssue
    ] = []

    for package_dir in (
        first,
        second,
    ):
        observed = tuple(
            path.relative_to(
                package_dir
            ).as_posix()
            for path in sorted(
                package_dir.rglob("*"),
                key=lambda value: (
                    value.relative_to(
                        package_dir
                    ).as_posix()
                ),
            )
            if path.is_file()
        )

        if observed != (
            PACKAGE_FILE_PATHS
        ):
            issues.append(
                package_issue(
                    "PACKAGE_INVENTORY",
                    str(package_dir),
                    "expected "
                    f"{PACKAGE_FILE_PATHS!r}, "
                    f"got {observed!r}",
                )
            )

    if issues:
        return tuple(
            sorted(
                set(issues),
                key=lambda value: (
                    value.sort_key
                ),
            )
        )

    for relative in (
        PACKAGE_FILE_PATHS
    ):
        if (
            first / relative
        ).read_bytes() != (
            second / relative
        ).read_bytes():
            issues.append(
                package_issue(
                    "NONDETERMINISTIC_PACKAGE_REBUILD",
                    relative,
                    "independent complete "
                    "package builds differ",
                )
            )

    return tuple(
        sorted(
            set(issues),
            key=lambda value: value.sort_key,
        )
    )


def build_release_package(
    context: FormalReleaseContext,
    notes_source: Path,
    output_dir: Path,
    repository_root: Path = REPO_ROOT,
) -> AssembledReleasePackage:
    context = (
        validate_formal_release_context(
            context
        )
    )

    repository_root = (
        Path(repository_root).resolve()
    )

    notes_source = Path(
        notes_source
    )

    output_dir = Path(
        output_dir
    )

    notes_relative = _validate_paths(
        context,
        notes_source,
        output_dir,
        repository_root,
    )

    notes_bytes = (
        notes_source.read_bytes()
    )

    note_issues = (
        validate_release_notes_bytes(
            notes_bytes,
            template_bytes=(
                repository_root
                / "release-notes/TEMPLATE.md"
            ).read_bytes(),
        )
    )

    if note_issues:
        raise ReleasePackageError(
            note_issues
        )

    snapshots = (
        snapshot_development_outputs(
            repository_root
        )
    )

    toolchain = (
        resolve_validation_toolchain(
            repository_root
        )
    )

    first_root = Path(
        tempfile.mkdtemp(
            prefix=TEMP_PREFIX,
            dir=output_dir.parent,
        )
    )

    second_root = Path(
        tempfile.mkdtemp(
            prefix=TEMP_PREFIX,
            dir=output_dir.parent,
        )
    )

    first = (
        first_root
        / context.release_identifier
    )

    second = (
        second_root
        / context.release_identifier
    )

    try:
        assemble_release_package(
            context,
            notes_bytes,
            notes_relative,
            first,
            repository_root,
            toolchain,
            snapshots,
        )

        assemble_release_package(
            context,
            notes_bytes,
            notes_relative,
            second,
            repository_root,
            toolchain,
            snapshots,
            reverse_input=True,
        )

        comparison = (
            compare_complete_packages(
                first,
                second,
            )
        )

        if comparison:
            raise ReleasePackageError(
                comparison
            )

        snapshot_issues = (
            development_snapshot_issues(
                repository_root,
                snapshots,
            )
        )

        if snapshot_issues:
            raise ReleasePackageError(
                snapshot_issues
            )

        import sosa_2023_check_release as checker

        validation_issues = (
            checker.validate_release_package(
                first,
                repository_root=(
                    repository_root
                ),
                toolchain=toolchain,
                reconstruct=False,
            )
        )

        if validation_issues:
            raise ReleasePackageError(
                validation_issues
            )

        os.replace(
            first,
            output_dir,
        )

        return AssembledReleasePackage(
            manifest=(
                manifest
                .load_and_validate_release_manifest(
                    output_dir
                    / "manifest.json"
                )
            ),
            manifest_bytes=(
                output_dir
                / "manifest.json"
            ).read_bytes(),
            catalog_bytes=(
                output_dir
                / "catalog-v001.xml"
            ).read_bytes(),
            sha256sums_bytes=(
                output_dir
                / "SHA256SUMS"
            ).read_bytes(),
        )
    finally:
        shutil.rmtree(
            first_root,
            ignore_errors=True,
        )

        shutil.rmtree(
            second_root,
            ignore_errors=True,
        )


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--release-id",
        required=True,
    )

    parser.add_argument(
        "--release-date",
        required=True,
    )

    parser.add_argument(
        "--git-tag",
        required=True,
    )

    parser.add_argument(
        "--source-commit",
        required=True,
    )

    parser.add_argument(
        "--notes",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
    )

    return parser.parse_args(
        argv
    )


def main(
    argv: list[str] | None = None,
) -> int:
    args = parse_args(
        argv
    )

    try:
        context = (
            parse_formal_release_context(
                args.release_id,
                args.release_date,
                args.git_tag,
                args.source_commit,
            )
        )

        result = (
            build_release_package(
                context,
                args.notes,
                args.output_dir,
                REPO_ROOT,
            )
        )
    except Exception as exc:
        print(str(exc))
        return 1

    print(
        "SOSA-2023 release package "
        "build: PASS"
    )

    print(
        "Release identifier: "
        f"{result.manifest.release_identifier}"
    )

    print(
        "Package files: "
        f"{len(PACKAGE_FILE_PATHS)}"
    )

    print(
        "Checksummed files: "
        f"{len(CHECKSUM_PATHS)}"
    )

    print(
        "Manifest SHA-256: "
        + manifest.release_manifest_sha256(
            result.manifest_bytes
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
