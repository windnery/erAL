"""Tests for character-to-character affinity relations."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.content.character_relations import load_character_relations


class CharacterRelationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_load_returns_empty_when_missing(self) -> None:
        index = load_character_relations(self.repo_root / "nonexistent_file.toml")
        self.assertEqual(index.relations, ())
        self.assertEqual(index.affinity("a", "b"), 0)
        self.assertEqual(index.tags("a", "b"), ())


if __name__ == "__main__":
    unittest.main()
