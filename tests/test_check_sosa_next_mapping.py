#!/usr/bin/env python3
"""Focused tests for the governed SOSA-next COMS checker."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_sosa_next_mapping as checker  # noqa: E402


GOVERNED_INPUTS = (
    REPO_ROOT / "mappings/SOSA-next-to-BFO-COMS.xlsx",
    REPO_ROOT / "src/sosa-next/catalog-v001.xml",
    checker.SOURCE_VERSION_CONFIG,
    *checker.SOURCE_FILES,
)

CURRENT_PRODUCTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT
    / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT
    / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT
    / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)

DATATYPE_DEFERRAL = (
    "Datatype-property mapping deferred pending repository-wide COMS "
    "support for datatype-property source terms. This capability must be "
    "implemented consistently for both the current SOSA mapping and the "
    "forthcoming SOSA mapping."
)

EXPECTED_DATATYPE_TERMS = {
    "sosa:endTime",
    "sosa:hasSimpleResult",
    "sosa:resultTime",
    "sosa:startTime",
}

EXPECTED_CLASS_DEFERRALS: set[str] = set()

EXPECTED_CLASS_NO_DIRECT_MAPPING = {
    "sosa:ActuatableProperty",
    "sosa:ActuatingProcedure",
    "sosa:Observation",
    "sosa:ObservableProperty",
    "sosa:ObservingProcedure",
    "sosa:Result",
    "sosa:SamplingProcedure",
    "sosa:SpatialSample",
}

EXPECTED_OBJECT_PROPERTY_DEFERRALS = {
    "sosa:actsOn",
    "sosa:actsOnProperty",
    "sosa:featureHasUltimateSample",
    "sosa:forProperty",
    "sosa:hasInput",
    "sosa:hasInputValue",
    "sosa:hasOperatingConditions",
    "sosa:hasOriginalSample",
    "sosa:hasOutput",
    "sosa:hasSystemCapability",
    "sosa:observedProperty",
    "sosa:observes",
    "sosa:hosts",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CheckSosaNextMappingTests(unittest.TestCase):
    def test_governed_workbook_and_reasoning_are_exact(self) -> None:
        protected_paths = (*GOVERNED_INPUTS, *CURRENT_PRODUCTS)
        original_prefix_files = dict(checker.coms.PREFIX_FILES)
        original_source_imports = tuple(checker.coms.SOURCE_IMPORTS)

        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in protected_paths
        }

        with tempfile.TemporaryDirectory(
            prefix="sosa-next-check-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="sosa-next-check-b-"
        ) as second_dir:
            first = checker.run_check(Path(first_dir))
            self.assertEqual(
                checker.coms.PREFIX_FILES,
                original_prefix_files,
            )
            self.assertEqual(
                checker.coms.SOURCE_IMPORTS,
                original_source_imports,
            )

            second = checker.run_check(Path(second_dir))
            self.assertEqual(
                checker.coms.PREFIX_FILES,
                original_prefix_files,
            )
            self.assertEqual(
                checker.coms.SOURCE_IMPORTS,
                original_source_imports,
            )

            for summary in (first, second):
                self.assertTrue(summary["passed"], summary)
                self.assertEqual(
                    summary["source_identity"],
                    checker.SOURCE_IDENTITY,
                )
                self.assertEqual(
                    summary["source_version_authority"],
                    "config/sosa-source-version.toml",
                )
                self.assertEqual(
                    summary["source_version_authority_sha256"],
                    sha256(checker.SOURCE_VERSION_CONFIG),
                )
                self.assertEqual(
                    summary["source_edition_version_iri"],
                    checker.SOURCE_VERSION_AUTHORITY.edition_version_iri,
                )
                self.assertEqual(
                    summary["source_upstream_commit"],
                    checker.SOURCE_VERSION_AUTHORITY.upstream_commit,
                )
                self.assertEqual(summary["source_triple_count"], 1207)
                self.assertEqual(
                    summary["source_sha256"],
                    {
                        path.relative_to(REPO_ROOT).as_posix(): digest
                        for path, digest
                        in checker.PINNED_SOURCE_SHA256.items()
                    },
                )
                self.assertEqual(summary["governed_row_count"], 119)
                self.assertEqual(summary["unique_row_id_count"], 119)
                self.assertEqual(summary["active_mapping_count"], 46)
                self.assertEqual(summary["deferred_mapping_count"], 17)
                self.assertEqual(
                    summary["explicitly_unmapped_row_count"],
                    56,
                )
                self.assertEqual(summary["malformed_row_count"], 0)
                self.assertEqual(
                    summary["canonical_authoritative_axiom_count"],
                    46,
                )
                self.assertEqual(
                    summary["active_ontology_triple_count"],
                    274,
                )

                reasoning = summary["reasoning"]
                self.assertTrue(reasoning["passed"])
                self.assertEqual(reasoning["return_code"], 0)
                self.assertTrue(reasoning["reasoned_output_exists"])
                self.assertEqual(
                    reasoning["reasoned_output_triples"],
                    1749,
                )
                self.assertEqual(
                    reasoning["unsatisfiable_classes"],
                    [],
                )
                self.assertEqual(reasoning["robot_output"], "")

                deferred = {
                    item["subject"]: item
                    for item in summary["deferred_mappings"]
                }
                self.assertEqual(len(deferred), 17)
                self.assertEqual(
                    len(deferred),
                    len(summary["deferred_mappings"]),
                )
                self.assertTrue(
                    all(
                        item["reasoning"]
                        for item in summary["deferred_mappings"]
                    )
                )

                class_terms = {
                    subject
                    for subject, item in deferred.items()
                    if item["subject_kind"] == "class"
                }
                self.assertEqual(
                    class_terms,
                    EXPECTED_CLASS_DEFERRALS,
                )

                object_property_terms = {
                    subject
                    for subject, item in deferred.items()
                    if item["subject_kind"] == "object_property"
                }
                self.assertEqual(
                    object_property_terms,
                    EXPECTED_OBJECT_PROPERTY_DEFERRALS,
                )

                datatype_terms = {
                    subject
                    for subject, item in deferred.items()
                    if item["subject_kind"] == "datatype_property"
                }
                self.assertEqual(
                    datatype_terms,
                    EXPECTED_DATATYPE_TERMS,
                )

                self.assertEqual(
                    set(deferred),
                    (
                        EXPECTED_CLASS_DEFERRALS
                        | EXPECTED_OBJECT_PROPERTY_DEFERRALS
                        | EXPECTED_DATATYPE_TERMS
                    ),
                )

                for subject in EXPECTED_DATATYPE_TERMS:
                    self.assertEqual(
                        deferred[subject]["reasoning"],
                        DATATYPE_DEFERRAL,
                    )

                no_direct_mapping = {
                    item["subject"]: item
                    for item in summary["no_direct_mapping_rows"]
                }
                self.assertEqual(
                    set(no_direct_mapping),
                    EXPECTED_CLASS_NO_DIRECT_MAPPING,
                )
                self.assertEqual(
                    summary["no_direct_mapping_row_count"],
                    8,
                )
                self.assertEqual(
                    summary["unreviewed_row_count"],
                    48,
                )

                explicitly_unmapped = {
                    item["subject"]: item
                    for item in summary["explicitly_unmapped_rows"]
                }
                self.assertEqual(len(explicitly_unmapped), 56)
                self.assertEqual(
                    len(explicitly_unmapped),
                    len(summary["explicitly_unmapped_rows"]),
                )
                self.assertIn(
                    "sosa:hasSample",
                    explicitly_unmapped,
                )
                self.assertIn(
                    "sosa:isSampleOf",
                    explicitly_unmapped,
                )
                self.assertNotIn(
                    "sosa:phenomenonTime",
                    explicitly_unmapped,
                )

            stable_sections = (
                "source_identity",
                "source_version_authority",
                "source_version_authority_sha256",
                "source_edition_version_iri",
                "source_upstream_commit",
                "source_sha256",
                "source_triple_count",
                "governed_row_count",
                "unique_row_id_count",
                "active_mapping_count",
                "deferred_mapping_count",
                "explicitly_unmapped_row_count",
                "malformed_row_count",
                "canonical_authoritative_axiom_count",
                "active_ontology_triple_count",
                "deferred_mappings",
                "explicitly_unmapped_rows",
                "reasoning",
            )

            for section in stable_sections:
                self.assertEqual(
                    first[section],
                    second[section],
                )

            for directory, summary in (
                (Path(first_dir), first),
                (Path(second_dir), second),
            ):
                summary_path = directory / "summary.json"
                self.assertTrue(summary_path.is_file())
                self.assertEqual(
                    json.loads(
                        summary_path.read_text(encoding="utf-8")
                    ),
                    summary,
                )

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in protected_paths
        }
        self.assertEqual(before, after)
        self.assertEqual(
            checker.coms.PREFIX_FILES,
            original_prefix_files,
        )
        self.assertEqual(
            checker.coms.SOURCE_IMPORTS,
            original_source_imports,
        )


if __name__ == "__main__":
    unittest.main()
