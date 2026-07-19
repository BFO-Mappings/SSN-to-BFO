#!/usr/bin/env python3
"""Canonical schema-1 release-manifest models and validation."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import urlsplit

from release_context import FormalReleaseContextError, parse_formal_release_context


SCHEMA_VERSION = 1
PRODUCT_ORDER = (
    "integrated",
    "alignment_core",
    "strict_bfo_mapping",
    "bfo_projection",
    "cco_extension",
)
FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS = (
    ("integrated", 15915),
    ("alignment_core", 1215),
    ("strict_bfo_mapping", 14992),
    ("bfo_projection", 15003),
    ("cco_extension", 15937),
)
if tuple(key for key, _ in FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS) != PRODUCT_ORDER:
    raise RuntimeError("formal fixed-closure counts and product order differ")
PRODUCT_IMPORT_COUNTS = {
    "integrated": 4,
    "alignment_core": 0,
    "strict_bfo_mapping": 1,
    "bfo_projection": 1,
    "cco_extension": 1,
}
INPUT_KEY_ORDER = (
    "coms_workbook",
    "publication_metadata",
    "product_dispositions",
    "release_notes",
    "license",
    "module_coms_row_identity",
    "module_product_dispositions",
    "module_publication_metadata",
    "module_release_context",
    "module_generate_mapping_from_coms",
    "module_modular_products",
    "module_release_manifest",
    "module_build_release",
)
DEPENDENCY_KEY_ORDER = (
    "sosa",
    "sosa_sampling",
    "ssn",
    "ssn_systems",
    "merged_cco_bfo",
)
INCLUDED_FILE_PATH_ORDER = (
    "LICENSE",
    "RELEASE-NOTES.md",
    "SSN2BFO.ttl",
    "catalog-v001.xml",
    "current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    "current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    "current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
    "current-ssn-sosa/ssn-sosa-cco-extension.ttl",
    "evidence/coms-product-dispositions.json",
    "sources/SSN2BFO-COMS.xlsx",
    "sources/publication-metadata.toml",
)
TOP_LEVEL_FIELDS = (
    "schema_version",
    "release_identifier",
    "release_date",
    "git_tag",
    "source_commit",
    "repository_iri",
    "inputs",
    "product_order",
    "products",
    "dependencies",
    "validation_environment",
    "validation",
    "included_files",
)
INPUT_FIELDS = ("key", "source_path", "package_path", "sha256", "byte_size")
PRODUCT_FIELDS = (
    "key",
    "path",
    "stable_ontology_iri",
    "version_iri",
    "imports",
    "sha256",
    "byte_size",
    "ontology_declaration_count",
    "import_count",
    "static_metadata_count",
    "formal_metadata_count",
    "logical_triple_count",
    "total_triple_count",
    "direct_governed_axiom_count",
    "governed_closure_axiom_count",
    "reasoning_mode",
)
DEPENDENCY_FIELDS = (
    "key",
    "role",
    "path",
    "ontology_iri",
    "version_iri",
    "sha256",
    "byte_size",
)
VALIDATION_ENVIRONMENT_FIELDS = (
    "python_implementation",
    "python_version",
    "java_vendor",
    "java_version",
    "java_vm_name",
    "robot_artifact",
    "robot_version",
    "robot_sha256",
    "toolchain_path",
    "toolchain_sha256",
    "requirements_path",
    "requirements_sha256",
)
HERMIT_FIELDS = (
    "product_key",
    "status",
    "fixed_closure_triple_count",
    "return_code",
    "reasoned_output_produced",
    "named_unsatisfiable_class_count",
    "owl_nothing_equivalent_named_class_count",
)
VALIDATION_FIELDS = (
    "strict_turtle_parsing",
    "formal_metadata_validation",
    "serialized_header_validation",
    "governed_axiom_reconciliation",
    "import_graph_validation",
    "catalog_validation",
    "checksum_validation",
    "development_artifact_nonmutation",
    "deterministic_package_rebuild",
    "hermit_results",
)
INCLUDED_FILE_FIELDS = ("path", "role", "sha256", "byte_size")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class ReleaseManifestInput:
    key: str
    source_path: str
    package_path: str | None
    sha256: str
    byte_size: int


@dataclass(frozen=True)
class ReleaseManifestProduct:
    key: str
    path: str
    stable_ontology_iri: str
    version_iri: str
    imports: tuple[str, ...]
    sha256: str
    byte_size: int
    ontology_declaration_count: int
    import_count: int
    static_metadata_count: int
    formal_metadata_count: int
    logical_triple_count: int
    total_triple_count: int
    direct_governed_axiom_count: int
    governed_closure_axiom_count: int
    reasoning_mode: str


@dataclass(frozen=True)
class ReleaseManifestDependency:
    key: str
    role: str
    path: str
    ontology_iri: str
    version_iri: str | None
    sha256: str
    byte_size: int


@dataclass(frozen=True)
class ReleaseManifestValidationEnvironment:
    python_implementation: str
    python_version: str
    java_vendor: str
    java_version: str
    java_vm_name: str
    robot_artifact: str
    robot_version: str
    robot_sha256: str
    toolchain_path: str
    toolchain_sha256: str
    requirements_path: str
    requirements_sha256: str


@dataclass(frozen=True)
class ReleaseManifestHermitResult:
    product_key: str
    status: str
    fixed_closure_triple_count: int
    return_code: int
    reasoned_output_produced: bool
    named_unsatisfiable_class_count: int
    owl_nothing_equivalent_named_class_count: int


@dataclass(frozen=True)
class ReleaseManifestValidation:
    strict_turtle_parsing: bool
    formal_metadata_validation: bool
    serialized_header_validation: bool
    governed_axiom_reconciliation: bool
    import_graph_validation: bool
    catalog_validation: bool
    checksum_validation: bool
    development_artifact_nonmutation: bool
    deterministic_package_rebuild: bool
    hermit_results: tuple[ReleaseManifestHermitResult, ...]


@dataclass(frozen=True)
class ReleaseManifestIncludedFile:
    path: str
    role: str
    sha256: str
    byte_size: int


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    release_identifier: str
    release_date: str
    git_tag: str
    source_commit: str
    repository_iri: str
    inputs: tuple[ReleaseManifestInput, ...]
    product_order: tuple[str, ...]
    products: tuple[ReleaseManifestProduct, ...]
    dependencies: tuple[ReleaseManifestDependency, ...]
    validation_environment: ReleaseManifestValidationEnvironment
    validation: ReleaseManifestValidation
    included_files: tuple[ReleaseManifestIncludedFile, ...]


@dataclass(frozen=True)
class ReleaseManifestIssue:
    code: str
    field: str
    message: str

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return self.field, self.code, self.message


class ReleaseManifestError(ValueError):
    """One or more deterministic manifest failures."""

    def __init__(self, issues: Iterable[ReleaseManifestIssue]):
        self.issues = tuple(sorted(set(issues), key=lambda value: value.sort_key))
        super().__init__("; ".join(format_issue(issue) for issue in self.issues))


def format_issue(issue: ReleaseManifestIssue) -> str:
    return f"ERROR [{issue.code}] {issue.field}: {issue.message}"


def _issue(code: str, field: str, message: str) -> ReleaseManifestIssue:
    return ReleaseManifestIssue(code, field, message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def release_manifest_sha256(value: ReleaseManifest | bytes) -> str:
    serialized = canonical_manifest_bytes(value) if isinstance(value, ReleaseManifest) else value
    return sha256_bytes(serialized)


def is_safe_relative_posix_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    if urlsplit(value).scheme or value.startswith("/") or value.endswith("/"):
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return PurePosixPath(value).as_posix() == value


def _ordered(record: dict[str, object], fields: tuple[str, ...]) -> dict[str, object]:
    return {field: record.get(field) for field in fields}


def manifest_document(manifest: ReleaseManifest) -> dict[str, object]:
    environment = _ordered(asdict(manifest.validation_environment), VALIDATION_ENVIRONMENT_FIELDS)
    validation = asdict(manifest.validation)
    validation["hermit_results"] = [
        _ordered(asdict(value), HERMIT_FIELDS)
        for value in sorted(
            manifest.validation.hermit_results,
            key=lambda item: PRODUCT_ORDER.index(item.product_key),
        )
    ]
    document: dict[str, object] = {
        "schema_version": manifest.schema_version,
        "release_identifier": manifest.release_identifier,
        "release_date": manifest.release_date,
        "git_tag": manifest.git_tag,
        "source_commit": manifest.source_commit,
        "repository_iri": manifest.repository_iri,
        "inputs": [
            _ordered(asdict(value), INPUT_FIELDS)
            for value in sorted(
                manifest.inputs,
                key=lambda item: INPUT_KEY_ORDER.index(item.key),
            )
        ],
        "product_order": list(manifest.product_order),
        "products": [
            _ordered({**asdict(value), "imports": list(value.imports)}, PRODUCT_FIELDS)
            for value in sorted(
                manifest.products,
                key=lambda item: PRODUCT_ORDER.index(item.key),
            )
        ],
        "dependencies": [
            _ordered(asdict(value), DEPENDENCY_FIELDS)
            for value in sorted(
                manifest.dependencies,
                key=lambda item: DEPENDENCY_KEY_ORDER.index(item.key),
            )
        ],
        "validation_environment": environment,
        "validation": _ordered(validation, VALIDATION_FIELDS),
        "included_files": [
            _ordered(asdict(value), INCLUDED_FILE_FIELDS)
            for value in sorted(manifest.included_files, key=lambda item: item.path)
        ],
    }
    return _ordered(document, TOP_LEVEL_FIELDS)


def canonical_manifest_bytes(value: ReleaseManifest | dict[str, object]) -> bytes:
    if isinstance(value, ReleaseManifest):
        document = manifest_document(value)
    else:
        document = _canonicalize_document(value)
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _canonicalize_document(document: dict[str, object]) -> dict[str, object]:
    result = _ordered(document, TOP_LEVEL_FIELDS)
    result["inputs"] = [
        _ordered(value, INPUT_FIELDS)
        for value in sorted(
            document.get("inputs", []),
            key=lambda item: INPUT_KEY_ORDER.index(item.get("key"))
            if isinstance(item, dict) and item.get("key") in INPUT_KEY_ORDER
            else len(INPUT_KEY_ORDER),
        )
        if isinstance(value, dict)
    ] if isinstance(document.get("inputs"), list) else document.get("inputs")
    result["products"] = [
        _ordered(value, PRODUCT_FIELDS)
        for value in sorted(
            document.get("products", []),
            key=lambda item: PRODUCT_ORDER.index(item.get("key"))
            if isinstance(item, dict) and item.get("key") in PRODUCT_ORDER
            else len(PRODUCT_ORDER),
        )
        if isinstance(value, dict)
    ] if isinstance(document.get("products"), list) else document.get("products")
    result["dependencies"] = [
        _ordered(value, DEPENDENCY_FIELDS)
        for value in sorted(
            document.get("dependencies", []),
            key=lambda item: DEPENDENCY_KEY_ORDER.index(item.get("key"))
            if isinstance(item, dict) and item.get("key") in DEPENDENCY_KEY_ORDER
            else len(DEPENDENCY_KEY_ORDER),
        )
        if isinstance(value, dict)
    ] if isinstance(document.get("dependencies"), list) else document.get("dependencies")
    environment = document.get("validation_environment")
    if isinstance(environment, dict):
        result["validation_environment"] = _ordered(environment, VALIDATION_ENVIRONMENT_FIELDS)
    validation = document.get("validation")
    if isinstance(validation, dict):
        ordered_validation = _ordered(validation, VALIDATION_FIELDS)
        hermit = validation.get("hermit_results")
        if isinstance(hermit, list):
            ordered_validation["hermit_results"] = [
                _ordered(value, HERMIT_FIELDS)
                for value in sorted(
                    hermit,
                    key=lambda item: PRODUCT_ORDER.index(item.get("product_key"))
                    if isinstance(item, dict) and item.get("product_key") in PRODUCT_ORDER
                    else len(PRODUCT_ORDER),
                )
                if isinstance(value, dict)
            ]
        result["validation"] = ordered_validation
    result["included_files"] = [
        _ordered(value, INCLUDED_FILE_FIELDS)
        for value in sorted(
            document.get("included_files", []),
            key=lambda item: item.get("path", "") if isinstance(item, dict) else "",
        )
        if isinstance(value, dict)
    ] if isinstance(document.get("included_files"), list) else document.get("included_files")
    return result


def _strict_json_loads(value: bytes) -> dict[str, object]:
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReleaseManifestError((_issue("INVALID_UTF8", "manifest", str(exc)),)) from exc

    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in values:
            if key in result:
                raise ReleaseManifestError(
                    (_issue("DUPLICATE_FIELD", key, "JSON object field occurs more than once"),)
                )
            result[key] = item
        return result

    try:
        document = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_float=lambda _: (_ for _ in ()).throw(ValueError("floating-point values are prohibited")),
        )
    except ReleaseManifestError:
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        raise ReleaseManifestError((_issue("INVALID_JSON", "manifest", str(exc)),)) from exc
    if not isinstance(document, dict):
        raise ReleaseManifestError((_issue("DOCUMENT_TYPE", "manifest", "expected object"),))
    return document


def _check_fields(
    value: object,
    fields: tuple[str, ...],
    path: str,
    issues: list[ReleaseManifestIssue],
) -> dict[str, object] | None:
    if not isinstance(value, dict):
        issues.append(_issue("OBJECT_TYPE", path, "expected object"))
        return None
    missing = [field for field in fields if field not in value]
    extra = sorted(set(value) - set(fields))
    for field in missing:
        issues.append(_issue("MISSING_FIELD", f"{path}.{field}", "required field is absent"))
    for field in extra:
        issues.append(_issue("UNKNOWN_FIELD", f"{path}.{field}", "field is not allowed"))
    return value


def _string(value: object, field: str, issues: list[ReleaseManifestIssue]) -> str | None:
    if not isinstance(value, str) or not value:
        issues.append(_issue("STRING_VALUE", field, "expected non-empty string"))
        return None
    if unicodedata.normalize("NFC", value) != value:
        issues.append(_issue("NON_NFC_STRING", field, "string must be NFC-normalized"))
    return value


def _integer(value: object, field: str, issues: list[ReleaseManifestIssue]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        issues.append(_issue("INTEGER_VALUE", field, "expected non-negative integer"))
        return None
    return value


def _hash(value: object, field: str, issues: list[ReleaseManifestIssue]) -> None:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        issues.append(_issue("SHA256_VALUE", field, "expected 64 lowercase hexadecimal characters"))


def _path(value: object, field: str, issues: list[ReleaseManifestIssue], *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not is_safe_relative_posix_path(value):
        issues.append(_issue("UNSAFE_PATH", field, "expected normalized relative POSIX path"))
    elif isinstance(value, str) and unicodedata.normalize("NFC", value) != value:
        issues.append(_issue("NON_NFC_STRING", field, "path must be NFC-normalized"))


def _iri(value: object, field: str, issues: list[ReleaseManifestIssue], *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    text = _string(value, field, issues)
    if text is None:
        return
    parsed = urlsplit(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.fragment:
        issues.append(_issue("IRI_VALUE", field, "expected absolute HTTP(S) IRI without fragment"))


def validate_release_manifest_document(document: object) -> tuple[ReleaseManifestIssue, ...]:
    issues: list[ReleaseManifestIssue] = []
    top = _check_fields(document, TOP_LEVEL_FIELDS, "manifest", issues)
    if top is None:
        return tuple(sorted(set(issues), key=lambda value: value.sort_key))
    if top.get("schema_version") != SCHEMA_VERSION:
        issues.append(_issue("SCHEMA_VERSION", "schema_version", "expected 1"))
    try:
        parse_formal_release_context(
            top.get("release_identifier"),
            top.get("release_date"),
            top.get("git_tag"),
            top.get("source_commit"),
        )
    except FormalReleaseContextError as exc:
        issues.extend(_issue(value.code, value.field, value.message) for value in exc.issues)
    _iri(top.get("repository_iri"), "repository_iri", issues)

    product_order = top.get("product_order")
    if product_order != list(PRODUCT_ORDER):
        issues.append(_issue("PRODUCT_ORDER", "product_order", f"expected {list(PRODUCT_ORDER)!r}"))

    inputs = top.get("inputs")
    if not isinstance(inputs, list):
        issues.append(_issue("ARRAY_TYPE", "inputs", "expected array"))
    else:
        keys: list[str] = []
        for index, value in enumerate(inputs):
            path = f"inputs[{index}]"
            record = _check_fields(value, INPUT_FIELDS, path, issues)
            if record is None:
                continue
            key = _string(record.get("key"), f"{path}.key", issues)
            if key is not None:
                keys.append(key)
            _path(record.get("source_path"), f"{path}.source_path", issues)
            _path(record.get("package_path"), f"{path}.package_path", issues, nullable=True)
            _hash(record.get("sha256"), f"{path}.sha256", issues)
            _integer(record.get("byte_size"), f"{path}.byte_size", issues)
        if len(keys) != len(set(keys)):
            issues.append(_issue("DUPLICATE_INPUT_KEY", "inputs", "input keys must be unique"))
        if keys != list(INPUT_KEY_ORDER):
            issues.append(_issue("INPUT_ORDER", "inputs", f"expected {list(INPUT_KEY_ORDER)!r}"))

    products = top.get("products")
    if not isinstance(products, list):
        issues.append(_issue("ARRAY_TYPE", "products", "expected array"))
    else:
        observed_keys: list[str] = []
        for index, value in enumerate(products):
            path = f"products[{index}]"
            record = _check_fields(value, PRODUCT_FIELDS, path, issues)
            if record is None:
                continue
            key = _string(record.get("key"), f"{path}.key", issues)
            if key is not None:
                observed_keys.append(key)
            _path(record.get("path"), f"{path}.path", issues)
            _iri(record.get("stable_ontology_iri"), f"{path}.stable_ontology_iri", issues)
            _iri(record.get("version_iri"), f"{path}.version_iri", issues)
            imports = record.get("imports")
            if not isinstance(imports, list) or not all(isinstance(item, str) for item in imports):
                issues.append(_issue("IMPORTS_TYPE", f"{path}.imports", "expected string array"))
            else:
                for import_index, iri in enumerate(imports):
                    _iri(iri, f"{path}.imports[{import_index}]", issues)
                if len(imports) != len(set(imports)):
                    issues.append(_issue("DUPLICATE_IMPORT", f"{path}.imports", "imports must be unique"))
                expected_import_count = PRODUCT_IMPORT_COUNTS.get(key)
                if expected_import_count is not None and len(imports) != expected_import_count:
                    issues.append(
                        _issue(
                            "IMPORT_COUNT",
                            f"{path}.imports",
                            f"expected {expected_import_count}, got {len(imports)}",
                        )
                    )
            _hash(record.get("sha256"), f"{path}.sha256", issues)
            for field in PRODUCT_FIELDS[6:15]:
                if field != "reasoning_mode":
                    _integer(record.get(field), f"{path}.{field}", issues)
            if record.get("reasoning_mode") != "independent":
                issues.append(_issue("REASONING_MODE", f"{path}.reasoning_mode", "expected independent"))
        if observed_keys != list(PRODUCT_ORDER):
            issues.append(_issue("PRODUCT_RECORD_ORDER", "products", f"expected {list(PRODUCT_ORDER)!r}"))

    dependencies = top.get("dependencies")
    if not isinstance(dependencies, list):
        issues.append(_issue("ARRAY_TYPE", "dependencies", "expected array"))
    else:
        keys: list[str] = []
        for index, value in enumerate(dependencies):
            path = f"dependencies[{index}]"
            record = _check_fields(value, DEPENDENCY_FIELDS, path, issues)
            if record is None:
                continue
            key = _string(record.get("key"), f"{path}.key", issues)
            if key is not None:
                keys.append(key)
            _string(record.get("role"), f"{path}.role", issues)
            _path(record.get("path"), f"{path}.path", issues)
            _iri(record.get("ontology_iri"), f"{path}.ontology_iri", issues)
            _iri(record.get("version_iri"), f"{path}.version_iri", issues, nullable=True)
            _hash(record.get("sha256"), f"{path}.sha256", issues)
            _integer(record.get("byte_size"), f"{path}.byte_size", issues)
        if len(keys) != len(set(keys)):
            issues.append(_issue("DUPLICATE_DEPENDENCY_KEY", "dependencies", "dependency keys must be unique"))
        if keys != list(DEPENDENCY_KEY_ORDER):
            issues.append(_issue("DEPENDENCY_ORDER", "dependencies", f"expected {list(DEPENDENCY_KEY_ORDER)!r}"))

    environment = _check_fields(
        top.get("validation_environment"),
        VALIDATION_ENVIRONMENT_FIELDS,
        "validation_environment",
        issues,
    )
    if environment is not None:
        for field in VALIDATION_ENVIRONMENT_FIELDS:
            if field.endswith("_path"):
                _path(environment.get(field), f"validation_environment.{field}", issues)
            elif field.endswith("_sha256"):
                _hash(environment.get(field), f"validation_environment.{field}", issues)
            elif field == "robot_artifact":
                _iri(environment.get(field), f"validation_environment.{field}", issues)
            else:
                _string(environment.get(field), f"validation_environment.{field}", issues)

    validation = _check_fields(top.get("validation"), VALIDATION_FIELDS, "validation", issues)
    if validation is not None:
        for field in VALIDATION_FIELDS[:-1]:
            if validation.get(field) is not True:
                issues.append(_issue("VALIDATION_OUTCOME", f"validation.{field}", "expected true"))
        hermit = validation.get("hermit_results")
        if not isinstance(hermit, list):
            issues.append(_issue("ARRAY_TYPE", "validation.hermit_results", "expected array"))
        else:
            keys: list[str] = []
            for index, value in enumerate(hermit):
                path = f"validation.hermit_results[{index}]"
                record = _check_fields(value, HERMIT_FIELDS, path, issues)
                if record is None:
                    continue
                key = _string(record.get("product_key"), f"{path}.product_key", issues)
                if key is not None:
                    keys.append(key)
                if record.get("status") != "PASS":
                    issues.append(_issue("HERMIT_STATUS", f"{path}.status", "expected PASS"))
                closure_count = _integer(
                    record.get("fixed_closure_triple_count"),
                    f"{path}.fixed_closure_triple_count",
                    issues,
                )
                if index < len(FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS):
                    expected_key, expected_count = FORMAL_FIXED_CLOSURE_TRIPLE_COUNTS[index]
                    if closure_count is not None and closure_count != expected_count:
                        issues.append(
                            _issue(
                                "FIXED_CLOSURE_TRIPLE_COUNT_MISMATCH",
                                f"{path}.fixed_closure_triple_count",
                                f"expected {expected_count} for {expected_key}, got {closure_count}",
                            )
                        )
                if record.get("return_code") != 0:
                    issues.append(_issue("HERMIT_RETURN_CODE", f"{path}.return_code", "expected zero"))
                if record.get("reasoned_output_produced") is not True:
                    issues.append(_issue("HERMIT_OUTPUT", f"{path}.reasoned_output_produced", "expected true"))
                for field in (
                    "named_unsatisfiable_class_count",
                    "owl_nothing_equivalent_named_class_count",
                ):
                    if record.get(field) != 0:
                        issues.append(_issue("HERMIT_UNSAT", f"{path}.{field}", "expected zero"))
            if keys != list(PRODUCT_ORDER):
                issues.append(_issue("HERMIT_PRODUCT_ORDER", "validation.hermit_results", f"expected {list(PRODUCT_ORDER)!r}"))

    included = top.get("included_files")
    if not isinstance(included, list):
        issues.append(_issue("ARRAY_TYPE", "included_files", "expected array"))
    else:
        paths: list[str] = []
        for index, value in enumerate(included):
            path = f"included_files[{index}]"
            record = _check_fields(value, INCLUDED_FILE_FIELDS, path, issues)
            if record is None:
                continue
            file_path = record.get("path")
            _path(file_path, f"{path}.path", issues)
            if isinstance(file_path, str):
                paths.append(file_path)
            _string(record.get("role"), f"{path}.role", issues)
            _hash(record.get("sha256"), f"{path}.sha256", issues)
            _integer(record.get("byte_size"), f"{path}.byte_size", issues)
        if paths != list(INCLUDED_FILE_PATH_ORDER):
            issues.append(
                _issue(
                    "INCLUDED_FILE_ORDER",
                    "included_files",
                    f"expected {list(INCLUDED_FILE_PATH_ORDER)!r}",
                )
            )
        if len(paths) != len(set(paths)):
            issues.append(_issue("DUPLICATE_INCLUDED_FILE", "included_files", "paths must be unique"))
        if len(paths) != len(INCLUDED_FILE_PATH_ORDER):
            issues.append(
                _issue(
                    "INCLUDED_FILE_COUNT",
                    "included_files",
                    f"expected {len(INCLUDED_FILE_PATH_ORDER)}, got {len(paths)}",
                )
            )
        prohibited = {"manifest.json", "SHA256SUMS"} & set(paths)
        if prohibited:
            issues.append(_issue("MANIFEST_SELF_REFERENCE", "included_files", f"prohibited paths: {sorted(prohibited)!r}"))
    return tuple(sorted(set(issues), key=lambda value: value.sort_key))


def _manifest_from_document(document: dict[str, object]) -> ReleaseManifest:
    return ReleaseManifest(
        schema_version=document["schema_version"],
        release_identifier=document["release_identifier"],
        release_date=document["release_date"],
        git_tag=document["git_tag"],
        source_commit=document["source_commit"],
        repository_iri=document["repository_iri"],
        inputs=tuple(ReleaseManifestInput(**value) for value in document["inputs"]),
        product_order=tuple(document["product_order"]),
        products=tuple(
            ReleaseManifestProduct(**{**value, "imports": tuple(value["imports"])})
            for value in document["products"]
        ),
        dependencies=tuple(ReleaseManifestDependency(**value) for value in document["dependencies"]),
        validation_environment=ReleaseManifestValidationEnvironment(**document["validation_environment"]),
        validation=ReleaseManifestValidation(
            **{
                **document["validation"],
                "hermit_results": tuple(
                    ReleaseManifestHermitResult(**value)
                    for value in document["validation"]["hermit_results"]
                ),
            }
        ),
        included_files=tuple(
            ReleaseManifestIncludedFile(**value) for value in document["included_files"]
        ),
    )


def build_release_manifest(**values: object) -> ReleaseManifest:
    manifest = ReleaseManifest(schema_version=SCHEMA_VERSION, **values)
    document = manifest_document(manifest)
    issues = validate_release_manifest_document(document)
    if issues:
        raise ReleaseManifestError(issues)
    return _manifest_from_document(document)


def load_and_validate_release_manifest(source: Path | bytes) -> ReleaseManifest:
    serialized = source.read_bytes() if isinstance(source, Path) else source
    document = _strict_json_loads(serialized)
    issues = list(validate_release_manifest_document(document))
    if canonical_manifest_bytes(document) != serialized:
        issues.append(
            _issue(
                "NONCANONICAL_SERIALIZATION",
                "manifest",
                "bytes differ from canonical schema-ordered JSON",
            )
        )
    if issues:
        raise ReleaseManifestError(issues)
    return _manifest_from_document(document)
