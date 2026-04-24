"""Tests for split character stat file loaders."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eral.content.character_stats import load_split_initial_stats
from eral.content.marks import load_mark_definitions
from eral.content.stat_axes import load_stat_axis_catalog


class CharacterStatsLoaderTests(unittest.TestCase):
    def test_load_split_initial_stats_supports_explicit_base_schema(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        stat_axes = load_stat_axis_catalog(repo_root / "data" / "base" / "axes")
        mark_defs = load_mark_definitions(repo_root / "data" / "base" / "axes" / "marks.toml")

        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp)
            (pack_dir / "base.toml").write_text(
                "\n".join(
                    (
                        "[current]",
                        "0 = 800",
                        "1 = 600",
                        "",
                        "[cap]",
                        "0 = 1600",
                        "1 = 1200",
                        "",
                        "[recover]",
                        "0 = 12",
                        "1 = 8",
                        "",
                    )
                ),
                encoding="utf-8",
            )

            loaded = load_split_initial_stats(
                pack_dir,
                stat_axes=stat_axes,
                mark_keys={mark.key for mark in mark_defs},
            )

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.base, {"0": 800, "1": 600})
        self.assertEqual(loaded.base_caps, {"0": 1600, "1": 1200})
        self.assertEqual(loaded.base_recover_rates, {"0": 12, "1": 8})


if __name__ == "__main__":
    unittest.main()
