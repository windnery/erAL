"""Tests for player state and new-game bootstrap flow."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application


class PlayerStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(self.repo_root)

    def test_player_stats_are_initialized(self) -> None:
        world = self.app.world
        self.assertIsNotNone(world.player_stats)
        # 玩家默认有合理的初始体力/气力
        self.assertGreater(world.player_stats.base.get("stamina"), 0)
        self.assertGreater(world.player_stats.base.get("spirit"), 0)

    def test_default_gender_is_male(self) -> None:
        self.assertEqual(self.app.world.player_gender, "male")

    def test_male_player_has_semen_axis(self) -> None:
        world = self.app.world
        # 男性玩家初始有精液值
        self.assertGreater(world.player_stats.base.get("semen"), 0)

    def test_new_game_started_flag_defaults_false(self) -> None:
        self.assertEqual(self.app.world.get_condition("game_started"), 0)


class NewGameFlowTests(unittest.TestCase):
    """Verify the new-game payload integration path used by /api/new_game."""

    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(self.repo_root)

    def _apply_new_game(self, *, name: str, gender: str, stat_bonuses: dict, talent_picks: list, bonus_funds: int) -> None:
        # 这里内联 web_server /api/new_game 的核心逻辑（保持与处理器同步的职责由 API 层测试覆盖）
        world = self.app.world
        world.player_name = name
        world.player_gender = gender
        for key, delta in stat_bonuses.items():
            world.player_stats.base.add(key, int(delta))
        for era_idx in talent_picks:
            world.player_stats.compat.talent.set(int(era_idx), 1)
        world.personal_funds += bonus_funds
        world.set_condition("game_started", 1)

    def test_new_game_updates_player_identity(self) -> None:
        self._apply_new_game(
            name="白鹭",
            gender="female",
            stat_bonuses={"stamina": 300, "spirit": 200},
            talent_picks=[137],
            bonus_funds=500,
        )
        self.assertEqual(self.app.world.player_name, "白鹭")
        self.assertEqual(self.app.world.player_gender, "female")
        self.assertEqual(self.app.world.get_condition("game_started"), 1)

    def test_new_game_applies_stat_bonuses(self) -> None:
        before = self.app.world.player_stats.base.get("stamina")
        self._apply_new_game(
            name="指挥官",
            gender="male",
            stat_bonuses={"stamina": 300, "spirit": 200},
            talent_picks=[],
            bonus_funds=0,
        )
        self.assertEqual(self.app.world.player_stats.base.get("stamina"), before + 300)

    def test_new_game_applies_talent_picks(self) -> None:
        self._apply_new_game(
            name="指挥官",
            gender="male",
            stat_bonuses={},
            talent_picks=[92, 137],
            bonus_funds=0,
        )
        # TALENT:92 = 魅力; TALENT:137 = 大胃王
        self.assertEqual(self.app.world.player_stats.compat.talent.get(92), 1)
        self.assertEqual(self.app.world.player_stats.compat.talent.get(137), 1)

    def test_new_game_bonus_funds_accumulate(self) -> None:
        before = self.app.world.personal_funds
        self._apply_new_game(
            name="指挥官",
            gender="male",
            stat_bonuses={},
            talent_picks=[],
            bonus_funds=1500,
        )
        self.assertEqual(self.app.world.personal_funds, before + 1500)


if __name__ == "__main__":
    unittest.main()
