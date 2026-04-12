"""Tests for split character stat files."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eral.content.character_packs import load_character_packs
from eral.content.marks import load_mark_definitions
from eral.content.stat_axes import load_stat_axis_catalog
from eral.content.tw_axis_registry import load_tw_axis_registry


class CharacterPackStatFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.temp_root = self.repo_root / ".tmp-test-data"
        self.temp_root.mkdir(exist_ok=True)
        self.stat_axes = load_stat_axis_catalog(self.repo_root / "data" / "base" / "stat_axes.toml")
        self.tw_axes = load_tw_axis_registry(self.repo_root / "data" / "generated" / "tw_axis_registry.json")
        self.mark_keys = {
            mark.key for mark in load_mark_definitions(self.repo_root / "data" / "base" / "marks.toml")
        }

    def test_loads_split_stat_files_into_initial_stats(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.temp_root) as tmp:
            pack_dir = Path(tmp) / "enterprise"
            pack_dir.mkdir(parents=True, exist_ok=True)
            (pack_dir / "character.toml").write_text(
                "\n".join(
                    [
                        'key = "enterprise"',
                        'display_name = "企业"',
                        'tags = ["enterprise", "carrier"]',
                        'initial_location = "dock"',
                        "",
                        "[schedule]",
                        'morning = "dock"',
                    ]
                ),
                encoding="utf-8",
            )
            (pack_dir / "base.toml").write_text('stamina = 1200\nspirit = 900\n', encoding="utf-8")
            (pack_dir / "palam.toml").write_text('favor = 3\n', encoding="utf-8")
            (pack_dir / "abl.toml").write_text('"41" = 2\n', encoding="utf-8")
            (pack_dir / "talent.toml").write_text('"92" = 1\n', encoding="utf-8")
            (pack_dir / "cflag.toml").write_text('"2" = 4\n"4" = 3\n', encoding="utf-8")
            (pack_dir / "marks.toml").write_text('confessed = 1\n', encoding="utf-8")

            packs = load_character_packs(
                Path(tmp),
                stat_axes=self.stat_axes,
                tw_axes=self.tw_axes,
                mark_keys=self.mark_keys,
            )

        character = packs[0].character
        self.assertEqual(character.initial_stats.base["stamina"], 1200)
        self.assertEqual(character.initial_stats.base["spirit"], 900)
        self.assertEqual(character.initial_stats.palam["favor"], 3)
        self.assertEqual(character.initial_stats.abl[41], 2)
        self.assertEqual(character.initial_stats.talent[92], 1)
        self.assertEqual(character.initial_stats.cflag[2], 4)
        self.assertEqual(character.initial_stats.cflag[4], 3)
        self.assertEqual(character.initial_stats.marks["confessed"], 1)

    def test_rejects_unknown_split_stat_key(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.temp_root) as tmp:
            pack_dir = Path(tmp) / "bad_pack"
            pack_dir.mkdir(parents=True, exist_ok=True)
            (pack_dir / "character.toml").write_text(
                "\n".join(
                    [
                        'key = "bad_pack"',
                        'display_name = "坏角色"',
                        'initial_location = "command_office"',
                        "",
                        "[schedule]",
                        'morning = "command_office"',
                    ]
                ),
                encoding="utf-8",
            )
            (pack_dir / "base.toml").write_text('not_a_real_base = 1\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "not_a_real_base"):
                load_character_packs(
                    Path(tmp),
                    stat_axes=self.stat_axes,
                    tw_axes=self.tw_axes,
                    mark_keys=self.mark_keys,
                )


if __name__ == "__main__":
    unittest.main()
