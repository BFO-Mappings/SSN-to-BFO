#!/usr/bin/env python3
"""Focused tests for governed ROBOT STAR extraction equivalence."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import robot_extract_pilot as pilot  # noqa: E402


MAINTAINED_PRODUCTS = (
    REPO_ROOT / "SSN2BFO.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-alignment-core.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-bfo-mapping.ttl",
    REPO_ROOT / "releases/current-ssn-sosa/ssn-sosa-cco-extension.ttl",
)

MODULE_SHA256 = (
    "52e51f34d95b9b44b6c3d17008166b26"
    "e3eb49052c3e1ee72a99ae428f97efa4"
)

EXPECTED_ERROR_IRIS = [
    f"http://org.semanticweb.owlapi/error#Error{number}"
    for number in range(1, 5)
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def without_robot_output(
    value: dict[str, object],
) -> dict[str, object]:
    return {
        key: item
        for key, item in value.items()
        if key != "robot_output"
    }


def stable_inconsistency(
    value: dict[str, object],
) -> dict[str, object]:
    return {
        **value,
        "baseline": without_robot_output(
            value["baseline"],
        ),
        "module": without_robot_output(
            value["module"],
        ),
    }


class RobotExtractPilotTests(unittest.TestCase):
    def test_governed_star_module_preserves_current_reasoning_evidence(
        self,
    ) -> None:
        before = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }

        with tempfile.TemporaryDirectory(
            prefix="robot-extract-pilot-a-"
        ) as first_dir, tempfile.TemporaryDirectory(
            prefix="robot-extract-pilot-b-"
        ) as second_dir:
            first = pilot.run_pilot(Path(first_dir))
            second = pilot.run_pilot(Path(second_dir))

            self.assertTrue(first["passed"], first)
            self.assertTrue(second["passed"], second)

            for summary in (first, second):
                self.assertEqual(summary["governed_row_count"], 105)
                self.assertEqual(
                    summary["governed_signature_term_count"],
                    150,
                )

                seeds = summary["seed_inventory"]
                self.assertEqual(seeds["seed_count"], 59)
                self.assertEqual(seeds["bfo_seed_count"], 20)
                self.assertEqual(seeds["cco_seed_count"], 39)
                self.assertEqual(seeds["seed_file_bytes"], 2771)
                self.assertEqual(
                    seeds["first_seed"],
                    "http://purl.obolibrary.org/obo/BFO_0000002",
                )
                self.assertEqual(
                    seeds["last_seed"],
                    (
                        "https://www.commoncoreontologies.org/"
                        "ont00001986"
                    ),
                )

                strict = summary["strict_extraction"]
                self.assertTrue(strict["rejection_proven"])
                self.assertEqual(strict["return_code"], 1)
                self.assertFalse(strict["output_exists"])
                self.assertEqual(strict["output_bytes"], 0)
                self.assertEqual(
                    strict["entity_recognition_error_count"],
                    4,
                )
                self.assertEqual(
                    strict["synthetic_error_iris"],
                    EXPECTED_ERROR_IRIS,
                )
                self.assertIn(
                    "INVALID ONTOLOGY FILE ERROR",
                    strict["robot_output"],
                )

                module = summary["module"]
                self.assertTrue(module["passed"])
                self.assertEqual(
                    module["source_triple_count"],
                    13649,
                )
                self.assertEqual(
                    module["module_triple_count"],
                    3090,
                )
                self.assertEqual(
                    module["source_supported_axiom_count"],
                    2065,
                )
                self.assertEqual(
                    module["module_supported_axiom_count"],
                    194,
                )
                self.assertEqual(
                    module["module_only_axiom_ids"],
                    [],
                )
                self.assertEqual(
                    module["shared_mismatched_axiom_ids"],
                    [],
                )
                self.assertEqual(
                    module["missing_seed_declarations"],
                    [],
                )
                self.assertEqual(module["owl_imports"], [])
                self.assertEqual(
                    module["synthetic_error_iris"],
                    [],
                )
                self.assertEqual(
                    module["sha256"],
                    MODULE_SHA256,
                )
                self.assertEqual(
                    module["output_bytes"],
                    416359,
                )

                reproducibility = summary["reproducibility"]
                self.assertTrue(reproducibility["passed"])
                self.assertEqual(
                    reproducibility["first_return_code"],
                    0,
                )
                self.assertEqual(
                    reproducibility["second_return_code"],
                    0,
                )
                self.assertEqual(
                    reproducibility["first_robot_output"],
                    "",
                )
                self.assertEqual(
                    reproducibility["second_robot_output"],
                    "",
                )
                self.assertTrue(
                    reproducibility["graphs_isomorphic"]
                )
                self.assertTrue(
                    reproducibility["canonical_axioms_equal"]
                )
                self.assertTrue(
                    reproducibility["bytes_equal"]
                )
                self.assertEqual(
                    reproducibility["first_sha256"],
                    MODULE_SHA256,
                )
                self.assertEqual(
                    reproducibility["second_sha256"],
                    MODULE_SHA256,
                )

                expected_reasoning = {
                    "strict_bfo": (14986, 4433, 163),
                    "cco_extension": (15918, 5365, 232),
                }

                for name, (
                    baseline_triples,
                    module_triples,
                    axiom_count,
                ) in expected_reasoning.items():
                    result = summary["reasoning"][name]
                    self.assertTrue(result["passed"])
                    self.assertEqual(
                        result["baseline_closure_triples"],
                        baseline_triples,
                    )
                    self.assertEqual(
                        result["module_closure_triples"],
                        module_triples,
                    )
                    self.assertEqual(
                        result["closure_triple_reduction"],
                        10553,
                    )

                    for reasoning_result in (
                        result["baseline"],
                        result["module"],
                    ):
                        self.assertTrue(
                            reasoning_result["passed"]
                        )
                        self.assertEqual(
                            reasoning_result["return_code"],
                            0,
                        )
                        self.assertTrue(
                            reasoning_result[
                                "reasoned_output_produced"
                            ]
                        )
                        self.assertEqual(
                            reasoning_result["unsat_count"],
                            0,
                        )
                        self.assertEqual(
                            reasoning_result["unsat_classes"],
                            [],
                        )
                        self.assertEqual(
                            reasoning_result["robot_output"],
                            "",
                        )

                    comparison = result[
                        "governed_axiom_comparison"
                    ]
                    self.assertTrue(comparison["passed"])
                    self.assertEqual(
                        comparison["expected_count"],
                        axiom_count,
                    )
                    self.assertEqual(
                        comparison["actual_count"],
                        axiom_count,
                    )
                    self.assertEqual(
                        comparison["missing_axiom_ids"],
                        [],
                    )
                    self.assertEqual(
                        comparison["extra_axiom_ids"],
                        [],
                    )
                    self.assertEqual(
                        comparison["mismatched_axiom_ids"],
                        [],
                    )

                inconsistency = summary[
                    "controlled_inconsistency"
                ]
                self.assertTrue(inconsistency["passed"])
                self.assertEqual(
                    inconsistency["controlled_term"],
                    (
                        "http://purl.obolibrary.org/obo/"
                        "BFO_0000002"
                    ),
                )
                self.assertTrue(
                    inconsistency[
                        "same_inconsistency_diagnostic"
                    ]
                )

                for reasoning_result in (
                    inconsistency["baseline"],
                    inconsistency["module"],
                ):
                    self.assertFalse(
                        reasoning_result["passed"]
                    )
                    self.assertEqual(
                        reasoning_result["return_code"],
                        1,
                    )
                    self.assertFalse(
                        reasoning_result[
                            "reasoned_output_produced"
                        ]
                    )
                    self.assertEqual(
                        reasoning_result["unsat_count"],
                        0,
                    )
                    self.assertEqual(
                        reasoning_result["unsat_classes"],
                        [],
                    )
                    self.assertIn(
                        "The ontology is inconsistent",
                        reasoning_result["robot_output"],
                    )

            self.assertEqual(
                first["seed_inventory"],
                second["seed_inventory"],
            )
            self.assertEqual(
                first["module"],
                second["module"],
            )
            self.assertEqual(
                first["reproducibility"],
                second["reproducibility"],
            )
            self.assertEqual(
                first["reasoning"],
                second["reasoning"],
            )
            self.assertEqual(
                without_robot_output(
                    first["strict_extraction"]
                ),
                without_robot_output(
                    second["strict_extraction"]
                ),
            )
            self.assertEqual(
                stable_inconsistency(
                    first["controlled_inconsistency"]
                ),
                stable_inconsistency(
                    second["controlled_inconsistency"]
                ),
            )

        after = {
            path.relative_to(REPO_ROOT).as_posix(): sha256(path)
            for path in MAINTAINED_PRODUCTS
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
