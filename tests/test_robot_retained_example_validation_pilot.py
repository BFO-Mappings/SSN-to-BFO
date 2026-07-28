#!/usr/bin/env python3
"""Focused tests for retained-example ROBOT validation."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import robot_retained_example_validation_pilot as pilot  # noqa: E402


MAINTAINED_FILES = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-projection.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
    *sorted(
        (
            REPO_ROOT
            / "src/current-ssn-sosa/examples"
        ).rglob("*.ttl")
    ),
)

EXPECTED_CANONICAL_HASHES = {
    "sosa-instance-data/Beer-Full-IBS-TH2.ttl":
        "803132051350169369b4ecf3d2bedeae7345c19b3daebb80c727a89dd2486330",
    "sosa-instance-data/IDEAS.ttl":
        "cf15af21f0e629cc9769238fb81fef0a07548e49704a6be16c642aee3121a79d",
    "sosa-instance-data/apartment-134.ttl":
        "138dba0c12c8efa3ddc1f8c23418f60e708a7bc6f60f728817d8bf73131864c9",
    "sosa-instance-data/dht22-deployment.ttl":
        "638a2cef427982c9225545db282fc9c45d1e45b63218197bf5bbecca0716fcbf",
    "sosa-instance-data/dht22.ttl":
        "7846bdf67662674f2e90e1c67c2e8a5b52e3c5e303468a18bb6c1dd3204d9d08",
    "sosa-instance-data/ip68.ttl":
        "882ed807fc62e7c2e230cc949ef96a53275f7778a935ad7eebefce18c682e98d",
    "sosa-instance-data/iphone_barometer-sosa.ttl":
        "d1c372c4e6ba4ad6c0e11b68df9cc04cae63d73e1ac3ca192d90b05e25b544c2",
    "sosa-instance-data/seismograph.ttl":
        "02ebc0eb2baeab200c1e98458bffd80c217028183f107ad5819fede81aa6904d",
    "sosa-instance-data/spinning-cups.ttl":
        "2ae64004862b43907c6d08efb1642197d4c8db83cf078178afe1c906cf309993",
    "sosa-instance-data/sunspots.ttl":
        "13c0d1fae9ff7a64ebc04990fe814436e6fea661c358cf4fae413a6c987a3a59",
    "sosa-instance-data/tree-height.ttl":
        "d3e42c6afc34f9c32399968c2613c10db9a172677c32cc5c03d76390bfcffeaa",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RobotRetainedExampleValidationPilotTests(unittest.TestCase):
    def test_retained_examples_and_malformed_control_are_exact(
        self,
    ) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_FILES
        }

        with tempfile.TemporaryDirectory(
            prefix="robot-retained-examples-"
        ) as temporary_dir:
            output_dir = Path(temporary_dir)
            summary = pilot.run_pilot(output_dir)

            self.assertTrue(summary["passed"], summary)
            self.assertEqual(summary["expected_example_count"], 11)
            self.assertEqual(summary["actual_example_count"], 11)
            self.assertTrue(summary["inventory_matches"])
            self.assertEqual(
                summary["expected_inventory"],
                list(pilot.EXPECTED_EXAMPLES),
            )
            self.assertEqual(
                summary["actual_inventory"],
                list(pilot.EXPECTED_EXAMPLES),
            )
            self.assertEqual(
                summary["successful_example_count"],
                11,
            )
            self.assertEqual(
                summary["raw_byte_reproducible_count"],
                10,
            )
            self.assertEqual(
                summary["canonical_reproducible_count"],
                11,
            )
            self.assertEqual(
                summary[
                    "total_output_structural_declarations_removed"
                ],
                422,
            )
            self.assertEqual(
                summary[
                    "total_source_integral_decimals_rewritten"
                ],
                1,
            )

            examples = {
                result["source"]: result
                for result in summary["examples"]
            }
            self.assertEqual(
                set(examples),
                set(pilot.EXPECTED_EXAMPLES),
            )

            for source, result in examples.items():
                self.assertTrue(result["passed"], result)
                self.assertTrue(
                    result["source_output_isomorphic"]
                )
                self.assertTrue(
                    result["repeated_outputs_isomorphic"]
                )
                self.assertTrue(
                    result["canonical_hashes_equal"]
                )
                self.assertEqual(
                    result["normalized_canonical_sha256"],
                    EXPECTED_CANONICAL_HASHES[source],
                )

                for conversion_name in (
                    "first_conversion",
                    "second_conversion",
                ):
                    conversion = result[conversion_name]
                    self.assertEqual(
                        conversion["return_code"],
                        0,
                    )
                    self.assertTrue(
                        conversion["output_exists"]
                    )
                    self.assertGreater(
                        conversion["output_bytes"],
                        0,
                    )
                    self.assertEqual(
                        conversion["robot_output"],
                        "",
                    )

                self.assertEqual(
                    result[
                        "normalized_source_triple_count"
                    ],
                    result[
                        "normalized_first_output_triple_count"
                    ],
                )
                self.assertEqual(
                    result[
                        "normalized_source_triple_count"
                    ],
                    result[
                        "normalized_second_output_triple_count"
                    ],
                )

            self.assertFalse(
                examples[
                    "sosa-instance-data/ip68.ttl"
                ]["raw_bytes_equal"]
            )
            self.assertTrue(
                examples[
                    "sosa-instance-data/iphone_barometer-sosa.ttl"
                ]["raw_bytes_equal"]
            )
            self.assertEqual(
                examples[
                    "sosa-instance-data/iphone_barometer-sosa.ttl"
                ]["source_integral_decimals_rewritten"],
                1,
            )

            for source, result in examples.items():
                if source != "sosa-instance-data/ip68.ttl":
                    self.assertTrue(
                        result["raw_bytes_equal"],
                        source,
                    )

            malformed = summary["malformed_control"]
            self.assertTrue(malformed["passed"])
            self.assertEqual(malformed["return_code"], 1)
            self.assertFalse(malformed["output_exists"])
            self.assertEqual(malformed["output_bytes"], 0)
            self.assertEqual(malformed["output_sha256"], "")
            self.assertTrue(
                malformed["invalid_ontology_diagnostic"]
            )
            self.assertIn(
                "INVALID ONTOLOGY FILE ERROR",
                malformed["robot_output"],
            )

            summary_path = output_dir / "summary.json"
            self.assertTrue(summary_path.is_file())
            self.assertEqual(
                json.loads(
                    summary_path.read_text(encoding="utf-8")
                ),
                summary,
            )

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_FILES
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
