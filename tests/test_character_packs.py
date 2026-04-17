"""Character pack discovery tests."""

from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from eral.content.character_packs import load_character_packs
from eral.content.marks import load_mark_definitions
from eral.content.stat_axes import load_stat_axis_catalog
from eral.content.tw_axis_registry import load_tw_axis_registry
from eral.tools.validate_content import validate_content


class CharacterPackTests(unittest.TestCase):
    def test_loads_all_real_character_packs(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        stat_axes = load_stat_axis_catalog(repo_root / "data" / "base" / "stat_axes.toml")
        tw_axes = load_tw_axis_registry(repo_root / "data" / "generated" / "tw_axis_registry.json")
        mark_keys = {m.key for m in load_mark_definitions(repo_root / "data" / "base" / "marks.toml")}
        packs = load_character_packs(
            repo_root / "data" / "base" / "characters",
            stat_axes=stat_axes,
            tw_axes=tw_axes,
            mark_keys=mark_keys,
        )

        pack_map = {pack.character.key: pack for pack in packs}
        self.assertGreaterEqual(len(packs), 3)
        self.assertIn("enterprise", pack_map)
        self.assertIn("laffey", pack_map)
        self.assertIn("javelin", pack_map)
        self.assertEqual(pack_map["enterprise"].character.schedule["night"], "garden")
        self.assertEqual(pack_map["laffey"].character.schedule["afternoon"], "garden")
        self.assertEqual(pack_map["javelin"].character.schedule["afternoon"], "cafeteria")
        self.assertEqual(pack_map["javelin"].character.initial_stats.base["stamina"], 450)
        self.assertEqual(pack_map["javelin"].character.initial_stats.palam["favor"], 1)
        self.assertEqual(pack_map["javelin"].character.initial_stats.abl[41], 1)
        self.assertEqual(pack_map["javelin"].character.initial_stats.talent[92], 1)
        self.assertEqual(pack_map["javelin"].character.initial_stats.marks["kissed"], 1)
        self.assertEqual(pack_map["enterprise"].character.faction_key, "eagle_union")
        self.assertEqual(pack_map["enterprise"].character.residence_area_key, "eagle_living")
        self.assertEqual(pack_map["enterprise"].character.dorm_group_key, "eagle_dorm")
        self.assertEqual(pack_map["javelin"].character.faction_key, "royal_navy")
        self.assertEqual(len(pack_map["enterprise"].events), 31)
        self.assertEqual(len(pack_map["enterprise"].dialogue), 62)
        self.assertEqual(len(pack_map["laffey"].events), 30)
        self.assertEqual(len(pack_map["laffey"].dialogue), 60)
        self.assertGreaterEqual(len(pack_map["javelin"].events), 20)
        self.assertGreaterEqual(len(pack_map["javelin"].dialogue), 30)
        self.assertEqual(pack_map["enterprise"].character.initial_stats.base["stamina"], 1200)
        self.assertEqual(pack_map["enterprise"].character.initial_stats.palam["favor"], 3)
        self.assertEqual(pack_map["laffey"].character.initial_stats.base["stamina"], 900)
        self.assertEqual(pack_map["laffey"].character.initial_stats.palam["favor"], 2)
        self.assertEqual(pack_map["laffey"].character.initial_stats.marks["kissed"], 1)

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
