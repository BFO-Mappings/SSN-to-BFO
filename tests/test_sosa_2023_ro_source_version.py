#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

CONFIG = (
    REPO_ROOT
    / "config/sosa-2023-ro-source-version.toml"
)

CHECKER = (
    REPO_ROOT
    / "tools/check_sosa_2023_ro_source_version.py"
)


class Sosa2023RoSourceVersionTest(
    unittest.TestCase
):
    def test_authority_lock(
        self,
    ) -> None:
        with CONFIG.open("rb") as handle:
            data = tomllib.load(
                handle
            )

        source = data["source"]

        self.assertEqual(
            source["status"],
            "approved",
        )

        self.assertEqual(
            source["track"],
            "sosa-2023",
        )

        self.assertEqual(
            source["dependency"],
            "relations-ontology",
        )

        self.assertEqual(
            source["release_tag"],
            "v2025-12-17",
        )

        self.assertEqual(
            source[
                "upstream_repository"
            ],
            "https://github.com/"
            "oborel/obo-relations",
        )

        self.assertEqual(
            source[
                "upstream_commit"
            ],
            "13620e1d75465c6504c755d2fdfa706922e9b7e7",
        )

        self.assertEqual(
            source["local_path"],
            "src/sosa-next/imports/"
            "ro-full.owl",
        )

    def test_checker_passes(
        self,
    ) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(CHECKER),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=(
                result.stdout
                + result.stderr
            ),
        )

        self.assertIn(
            "Summary: PASS",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
