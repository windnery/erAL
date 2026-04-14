"""ABL upgrade system tests: demand computation, level-up logic, end-to-end pipeline."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.content.abl_upgrade import load_abl_upgrade_config
from eral.domain.stats import ActorNumericState
from eral.content.stat_axes import load_stat_axis_catalog
from eral.content.tw_axis_registry import load_tw_axis_registry
from eral.systems.abl_upgrade import compute_demand, check_and_apply_abl_upgrades
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import make_app, reset_progress

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFIG = load_abl_upgrade_config(_REPO_ROOT / "data" / "base" / "abl_upgrade.toml")


class ComputeDemandTests(unittest.TestCase):
    """Test demand computation for ABL upgrades."""

    def test_level_0_to_1_demand_is_explv_1(self) -> None:
        demand = compute_demand(9, 0, 0, _CONFIG)
        self.assertEqual(demand, _CONFIG.explv[1])

    def test_level_1_to_2_demand_is_explv_2(self) -> None:
        demand = compute_demand(9, 1, 0, _CONFIG)
        self.assertEqual(demand, _CONFIG.explv[2])

    def test_demand_minimum_is_1(self) -> None:
        demand = compute_demand(9, 0, 100, _CONFIG)
        self.assertGreaterEqual(demand, 1)

    def test_positive_aptitude_offset_reduces_demand(self) -> None:
        demand_normal = compute_demand(9, 0, 0, _CONFIG)
        demand_apt = compute_demand(9, 0, 1, _CONFIG)
        self.assertLessEqual(demand_apt, demand_normal)

    def test_high_rate_reduces_demand(self) -> None:
        demand_9 = compute_demand(9, 0, 0, _CONFIG)   # rate=1.0
        demand_10 = compute_demand(10, 0, 0, _CONFIG)  # rate=1.5
        self.assertLess(demand_10, demand_9)

    def test_max_level_no_overflow(self) -> None:
        max_lvl = len(_CONFIG.explv) - 2
        demand = compute_demand(9, max_lvl, 0, _CONFIG)
        self.assertGreater(demand, 0)


class CheckAndApplyUpgradesTests(unittest.TestCase):
    """Test level-up application logic."""

    def setUp(self) -> None:
        catalog = load_stat_axis_catalog(_REPO_ROOT / "data" / "base" / "stat_axes.toml")
        registry = load_tw_axis_registry(_REPO_ROOT / "data" / "generated" / "tw_axis_registry.json")
        self.stats = ActorNumericState.zeroed(catalog, registry)

    def test_no_experience_no_upgrade(self) -> None:
        results = check_and_apply_abl_upgrades(self.stats, _CONFIG)
        self.assertEqual(results, [])

    def test_sufficient_experience_triggers_upgrade(self) -> None:
        demand = compute_demand(9, 0, 0, _CONFIG)
        self.stats.source.add("abl_9", demand)
        results = check_and_apply_abl_upgrades(self.stats, _CONFIG)
        self.assertTrue(any(abl_idx == 9 for abl_idx, _, _ in results))
        self.assertEqual(self.stats.compat.abl.get(9), 1)

    def test_insufficient_experience_accumulates(self) -> None:
        demand = compute_demand(9, 0, 0, _CONFIG)
        # First action: not enough
        self.stats.source.add("abl_9", demand - 1)
        results = check_and_apply_abl_upgrades(self.stats, _CONFIG)
        self.assertFalse(any(abl_idx == 9 for abl_idx, _, _ in results))
        self.assertEqual(self.stats.compat.abl.get(9), 0)
        # Experience should be accumulated
        self.assertEqual(self.stats.abl_exp.get(9, 0), demand - 1)

    def test_accumulated_experience_triggers_across_actions(self) -> None:
        demand = compute_demand(9, 0, 0, _CONFIG)
        # First action
        self.stats.source.add("abl_9", demand - 1)
        check_and_apply_abl_upgrades(self.stats, _CONFIG)
        self.stats.source.clear()
        # Second action adds the remainder
        self.stats.source.add("abl_9", 1)
        results = check_and_apply_abl_upgrades(self.stats, _CONFIG)
        self.assertTrue(any(abl_idx == 9 for abl_idx, _, _ in results))
        self.assertEqual(self.stats.compat.abl.get(9), 1)

    def test_result_includes_old_and_new_level(self) -> None:
        self.stats.compat.abl.set(9, 2)
        demand = compute_demand(9, 2, 0, _CONFIG)
        self.stats.source.add("abl_9", demand)
        results = check_and_apply_abl_upgrades(self.stats, _CONFIG)
        match = [(idx, old, new) for idx, old, new in results if idx == 9]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0], (9, 2, 3))

    def test_multiple_abls_can_upgrade_simultaneously(self) -> None:
        self.stats.source.add("abl_9", compute_demand(9, 0, 0, _CONFIG))
        self.stats.source.add("abl_10", compute_demand(10, 0, 0, _CONFIG))
        results = check_and_apply_abl_upgrades(self.stats, _CONFIG)
        upgraded_indices = {idx for idx, _, _ in results}
        self.assertIn(9, upgraded_indices)
        self.assertIn(10, upgraded_indices)

    def test_only_one_level_per_check(self) -> None:
        demand = compute_demand(9, 0, 0, _CONFIG)
        self.stats.source.add("abl_9", demand * 10)
        results = check_and_apply_abl_upgrades(self.stats, _CONFIG)
        match = [(idx, old, new) for idx, old, new in results if idx == 9]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0][2], 1)  # only level 0→1, not skipped

    def test_leftover_experience_preserved(self) -> None:
        demand = compute_demand(9, 0, 0, _CONFIG)
        self.stats.source.add("abl_9", demand + 5)
        check_and_apply_abl_upgrades(self.stats, _CONFIG)
        # 5 leftover after level-up
        self.assertEqual(self.stats.abl_exp.get(9, 0), 5)


class AblUpgradeEndToEndTests(unittest.TestCase):
    """End-to-end: command -> SOURCE -> settlement includes ABL upgrade."""

    def setUp(self) -> None:
        self.app = make_app()
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)

    def test_chat_produces_abl_experience_in_source(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="chat",
        )
        # chat has abl_9=3, abl_41=1 in source
        self.assertIn("abl_9", result.source_deltas)
        self.assertEqual(result.source_deltas["abl_9"], 3)

    def test_settlement_clears_abl_source_after_processing(self) -> None:
        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="chat",
        )
        # SOURCE should be cleared after settlement
        self.assertEqual(self.actor.stats.source.get("abl_9"), 0)

    def test_repeated_chat_can_level_up_intimacy(self) -> None:
        initial_abl = self.actor.stats.compat.abl.get(9)
        demand = compute_demand(9, initial_abl, 0, _CONFIG)
        # Each chat gives abl_9=3. Accumulate enough across actions.
        chats_needed = (demand // 3) + 2
        for _ in range(chats_needed):
            self.app.command_service.execute(
                self.app.world,
                actor_key="enterprise",
                command_key="chat",
            )
        # Should have leveled up at least once
        final_abl = self.actor.stats.compat.abl.get(9)
        self.assertGreater(final_abl, initial_abl)

    def test_praise_produces_obedience_abl_exp(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="praise",
        )
        # praise has abl_10=2
        self.assertIn("abl_10", result.source_deltas)
        self.assertEqual(result.source_deltas["abl_10"], 2)

    def test_train_produces_combat_abl_exp(self) -> None:
        self.actor.location_key = "training_ground"
        self.app.world.active_location.key = "training_ground"
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="train_together",
        )
        # train_together has abl_42=3
        self.assertIn("abl_42", result.source_deltas)
        self.assertEqual(result.source_deltas["abl_42"], 3)

    def test_cook_produces_cooking_abl_exp(self) -> None:
        self.actor.location_key = "cafeteria"
        self.app.world.active_location.key = "cafeteria"
        # cook is available afternoon/evening
        from eral.domain.world import TimeSlot
        self.app.world.current_time_slot = TimeSlot.AFTERNOON
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="cook",
        )
        # cook has abl_44=3
        self.assertIn("abl_44", result.source_deltas)
        self.assertEqual(result.source_deltas["abl_44"], 3)

    def test_no_abl_exp_commands_dont_upgrade(self) -> None:
        initial_abl = self.actor.stats.compat.abl.get(9)
        # nap has no source at all
        self.actor.location_key = "dormitory_a"
        self.app.world.active_location.key = "dormitory_a"
        from eral.domain.world import TimeSlot
        self.app.world.current_time_slot = TimeSlot.AFTERNOON
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="nap",
        )
        self.assertEqual(self.actor.stats.compat.abl.get(9), initial_abl)


if __name__ == "__main__":
    unittest.main()
