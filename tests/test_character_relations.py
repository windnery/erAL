"""Tests for character-to-character affinity relations."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.character_relations import load_character_relations


class CharacterRelationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_load_returns_empty_when_missing(self) -> None:
        index = load_character_relations(self.repo_root / "nonexistent_file.toml")
        self.assertEqual(index.relations, ())
        self.assertEqual(index.affinity("a", "b"), 0)
        self.assertEqual(index.tags("a", "b"), ())

    def test_load_parses_declared_relations(self) -> None:
        index = load_character_relations(
            self.repo_root / "data" / "base" / "character_relations.toml"
        )
        self.assertTrue(len(index.relations) > 0)
        self.assertEqual(index.affinity("javelin", "laffey"), 50)
        self.assertIn("驱逐小伙伴", index.tags("javelin", "laffey"))

    def test_undeclared_pair_returns_zero(self) -> None:
        index = load_character_relations(
            self.repo_root / "data" / "base" / "character_relations.toml"
        )
        self.assertEqual(index.affinity("enterprise", "akashi"), 0)
        self.assertEqual(index.tags("enterprise", "akashi"), ())

    def test_asymmetric_relations_supported(self) -> None:
        index = load_character_relations(
            self.repo_root / "data" / "base" / "character_relations.toml"
        )
        # javelin → laffey = 50; laffey → javelin = 40（不同方向不同值）
        self.assertEqual(index.affinity("javelin", "laffey"), 50)
        self.assertEqual(index.affinity("laffey", "javelin"), 40)

    def test_bootstrap_wires_relations(self) -> None:
        app = create_application(self.repo_root)
        self.assertIsNotNone(app.character_relations)
        self.assertEqual(app.character_relations.affinity("javelin", "laffey"), 50)

    def test_relations_from_and_to(self) -> None:
        index = load_character_relations(
            self.repo_root / "data" / "base" / "character_relations.toml"
        )
        enterprise_out = index.relations_from("enterprise")
        self.assertTrue(all(r.from_key == "enterprise" for r in enterprise_out))
        laffey_in = index.relations_to("laffey")
        self.assertTrue(all(r.to_key == "laffey" for r in laffey_in))


if __name__ == "__main__":
    unittest.main()
