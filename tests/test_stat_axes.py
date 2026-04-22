"""Tests for eraTW-derived numeric axes."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.content.stat_axes import AxisFamily, load_stat_axis_catalog
from eral.domain.stats import ActorNumericState


class StatAxisTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.catalog = load_stat_axis_catalog(repo_root / "data" / "base" / "axes")

    def test_catalog_preserves_known_tw_indices(self) -> None:
        self.assertEqual(self.catalog.get_by_index(AxisFamily.BASE, 0).label, "体力")
        self.assertEqual(self.catalog.get_by_index(AxisFamily.PALAM, 11).label, "欲情")
        self.assertEqual(self.catalog.get_by_index(AxisFamily.SOURCE, 50).label, "诱惑")

    def test_actor_numeric_state_is_zeroed_from_catalog(self) -> None:
        state = ActorNumericState.zeroed(self.catalog)

        self.assertEqual(state.base.get("stamina"), 0)
        self.assertEqual(state.palam.get("lust"), 0)
        self.assertEqual(state.source.get("temptation"), 0)

        state.source.add("temptation", 7)
        self.assertEqual(state.source.get("temptation"), 7)

        state.clear_source()
        self.assertEqual(state.source.get("temptation"), 0)

    def test_catalog_preserves_compat_indices(self) -> None:
        self.assertEqual(self.catalog.get_by_index(AxisFamily.ABL, 42).label, "战斗能力")
        self.assertEqual(self.catalog.get_by_index(AxisFamily.TALENT, 3).label, "恋慕")
        self.assertEqual(self.catalog.get_by_index(AxisFamily.CFLAG, 2).label, "好感度")


if __name__ == "__main__":
    unittest.main()
