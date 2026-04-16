"""Regression coverage for local src import resolution."""

from __future__ import annotations

import unittest
from pathlib import Path

import eral


class ImportResolutionTests(unittest.TestCase):
    def test_eral_package_resolves_from_current_repo_src(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected = repo_root / "src" / "eral"
        resolved = Path(eral.__file__).resolve().parent

        self.assertEqual(resolved, expected)


if __name__ == "__main__":
    unittest.main()
