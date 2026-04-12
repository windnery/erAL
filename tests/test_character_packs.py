"""Character pack discovery tests."""

from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from eral.content.character_packs import load_character_packs
from eral.tools.validate_content import validate_content


class CharacterPackTests(unittest.TestCase):
    def test_loads_starter_secretary_pack(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        packs = load_character_packs(repo_root / "data" / "base" / "characters")

        pack_map = {pack.character.key: pack for pack in packs}
        self.assertEqual(len(packs), 3)
        self.assertIn("starter_secretary", pack_map)
        self.assertIn("starter_destroyer", pack_map)
        self.assertIn("starter_cruiser", pack_map)
        self.assertEqual(pack_map["starter_secretary"].character.schedule["night"], "bathhouse")
        self.assertEqual(pack_map["starter_destroyer"].character.schedule["morning"], "command_office")
        self.assertEqual(pack_map["starter_cruiser"].character.schedule["morning"], "cafeteria")
        self.assertEqual(pack_map["starter_cruiser"].character.initial_stats.palam["favor"], 1)
        self.assertEqual(pack_map["starter_cruiser"].character.initial_stats.abl[41], 1)
        self.assertEqual(pack_map["starter_cruiser"].character.initial_stats.talent[92], 1)
        self.assertEqual(pack_map["starter_cruiser"].character.initial_stats.marks["kissed"], 1)
        self.assertEqual(len(pack_map["starter_secretary"].events), 48)
        self.assertEqual(len(pack_map["starter_secretary"].dialogue), 111)
        self.assertEqual(len(pack_map["starter_destroyer"].events), 36)
        self.assertEqual(len(pack_map["starter_destroyer"].dialogue), 73)
        self.assertEqual(len(pack_map["starter_cruiser"].events), 36)
        self.assertEqual(len(pack_map["starter_cruiser"].dialogue), 73)

    def test_content_validator_accepts_current_pack_layout(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        errors = validate_content(repo_root)

        self.assertEqual(errors, [])

    def test_content_validator_reports_quantity_gaps_for_sparse_pack(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        temp_root = repo_root / "runtime" / f"validate_test_{uuid.uuid4().hex}"
        shutil.copytree(repo_root / "data", temp_root / "data")

        sparse_dir = temp_root / "data" / "base" / "characters" / "sparse_test"
        sparse_dir.mkdir(parents=True, exist_ok=True)
        (sparse_dir / "character.toml").write_text(
            "\n".join(
                [
                    'key = "sparse_test"',
                    'display_name = "稀疏测试"',
                    'initial_location = "command_office"',
                    "",
                    "[schedule]",
                    'morning = "command_office"',
                ]
            ),
            encoding="utf-8",
        )
        (sparse_dir / "events.toml").write_text(
            "\n".join(
                [
                    "[[events]]",
                    'key = "sparse_event"',
                    'action_key = "chat"',
                ]
            ),
            encoding="utf-8",
        )
        (sparse_dir / "dialogue.toml").write_text(
            "\n".join(
                [
                    "[[entries]]",
                    'key = "chat"',
                    'actor_key = "sparse_test"',
                    'lines = ["只有一条"]',
                ]
            ),
            encoding="utf-8",
        )

        errors = validate_content(temp_root)
        self.assertTrue(any("事件数量不足" in error for error in errors))
        self.assertTrue(any("对话数量不足" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
