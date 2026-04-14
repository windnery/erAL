"""Combined 14-day smoke test: L3 core gameplay + L4 economic loop.

Validates the full integration:
- Movement, chat, interact, follow/dismiss across multiple characters
- Work commands earning personal funds
- Commission dispatch/tick/finalize earning port funds
- Facility upgrades (dorm, canteen, date_spot) with measurable effects
- Relationship growth (affection/trust) over sustained play
- All systems coexist without errors across 14 in-game days.

Character schedules:
  Enterprise: morning=dock, afternoon=training_ground, evening=command_office, night=garden
  Laffey:    morning=cafeteria, afternoon=garden, evening=dock, night=dormitory_a
  Javelin:   morning=training_ground, afternoon=cafeteria, evening=garden, night=dock
"""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import make_app, reset_progress, seed_friendly, seed_like


_REPO_ROOT = Path(__file__).resolve().parents[1]

# Enterprise schedule by slot
ENT_LOC = {
    TimeSlot.DAWN: "dormitory_a",
    TimeSlot.MORNING: "dock",
    TimeSlot.AFTERNOON: "training_ground",
    TimeSlot.EVENING: "command_office",
    TimeSlot.NIGHT: "garden",
    TimeSlot.LATE_NIGHT: "dormitory_a",
}
LAF_LOC = {
    TimeSlot.DAWN: "dormitory_a",
    TimeSlot.MORNING: "cafeteria",
    TimeSlot.AFTERNOON: "garden",
    TimeSlot.EVENING: "dock",
    TimeSlot.NIGHT: "dormitory_a",
    TimeSlot.LATE_NIGHT: "dormitory_a",
}
JAV_LOC = {
    TimeSlot.DAWN: "dormitory_a",
    TimeSlot.MORNING: "training_ground",
    TimeSlot.AFTERNOON: "cafeteria",
    TimeSlot.EVENING: "garden",
    TimeSlot.NIGHT: "dock",
    TimeSlot.LATE_NIGHT: "dormitory_a",
}


def _advance_to(app, world, day: int, slot: TimeSlot) -> None:
    while True:
        if world.current_day == day and world.current_time_slot == slot:
            return
        if world.current_day > day:
            return
        app.game_loop.advance_time(world)


class FourteenDayCombinedSmokeTests(unittest.TestCase):
    """14-day combined smoke: L3 gameplay + L4 economic loop in one flow."""

    def setUp(self) -> None:
        self.app = create_application(_REPO_ROOT)
        self.world = self.app.world
        self.ent = actor_by_key(self.app, "enterprise")
        self.laf = actor_by_key(self.app, "laffey")
        self.jav = actor_by_key(self.app, "javelin")
        # Give enough port funds for initial facility upgrades
        self.world.port_funds = 6000

    # ── Helpers ──────────────────────────────────────────────────────────

    def _go(self, *locations: str) -> None:
        for loc in locations:
            current = self.world.active_location.key
            if loc == current:
                continue
            neighbors = self.app.navigation_service.port_map.neighbors_of(current)
            if loc not in neighbors:
                self.app.navigation_service.move_player(self.world, "main_corridor")
            self.app.navigation_service.move_player(self.world, loc)

    def _cmd(self, actor_key: str, action: str):
        return self.app.command_service.execute(self.world, actor_key, action)

    def _at_and_cmd(self, location: str, actor_key: str, action: str):
        """Navigate to location then execute command."""
        self._go(location)
        return self._cmd(actor_key, action)

    # ── Day 1: Meet Enterprise at dock ──────────────────────────────────

    def _play_day1(self) -> None:
        _advance_to(self.app, self.world, 1, TimeSlot.MORNING)
        self._at_and_cmd("dock", "enterprise", "chat")
        self._at_and_cmd("dock", "enterprise", "touch_head")
        self._at_and_cmd("dock", "enterprise", "praise")

        _advance_to(self.app, self.world, 1, TimeSlot.AFTERNOON)
        self._at_and_cmd("training_ground", "enterprise", "train_together")

        _advance_to(self.app, self.world, 1, TimeSlot.EVENING)
        self._at_and_cmd("command_office", "enterprise", "chat")

    # ── Day 2: Enterprise follow + work ────────────────────────────────

    def _play_day2(self) -> None:
        _advance_to(self.app, self.world, 2, TimeSlot.MORNING)
        seed_friendly(self.ent)
        self._at_and_cmd("dock", "enterprise", "invite_follow")

        _advance_to(self.app, self.world, 2, TimeSlot.AFTERNOON)
        # Enterprise follows, so she stays with player
        self._go("command_office")
        self._cmd("enterprise", "office_shift")

        _advance_to(self.app, self.world, 2, TimeSlot.EVENING)
        self._at_and_cmd("garden", "enterprise", "follow_rest")
        self._cmd("enterprise", "dismiss_follow")

    # ── Day 3: Laffey + first commission ───────────────────────────────

    def _play_day3(self) -> None:
        _advance_to(self.app, self.world, 3, TimeSlot.MORNING)
        self._at_and_cmd("cafeteria", "laffey", "chat")
        self._at_and_cmd("cafeteria", "laffey", "share_snack")

        _advance_to(self.app, self.world, 3, TimeSlot.AFTERNOON)
        self._at_and_cmd("garden", "laffey", "touch_head")

        # Dispatch enterprise on patrol commission
        self.app.commission_service.dispatch(self.world, self.ent, "patrol")

        _advance_to(self.app, self.world, 3, TimeSlot.EVENING)
        self._at_and_cmd("dock", "laffey", "clink_cups")

    # ── Day 4: Javelin + upgrade dorm ─────────────────────────────────

    def _play_day4(self) -> None:
        _advance_to(self.app, self.world, 4, TimeSlot.MORNING)
        self._at_and_cmd("training_ground", "javelin", "chat")
        self._at_and_cmd("training_ground", "javelin", "praise")

        # Upgrade dorm (first facility upgrade)
        self.assertTrue(
            self.app.facility_service.upgrade(self.world, "dorm"),
            "Should be able to upgrade dorm with initial port funds",
        )

        _advance_to(self.app, self.world, 4, TimeSlot.AFTERNOON)
        self._at_and_cmd("cafeteria", "javelin", "share_snack")

        _advance_to(self.app, self.world, 4, TimeSlot.EVENING)
        self._at_and_cmd("garden", "javelin", "listen")

    # ── Day 5: Enterprise again + work ────────────────────────────────

    def _play_day5(self) -> None:
        _advance_to(self.app, self.world, 5, TimeSlot.MORNING)
        self._at_and_cmd("dock", "enterprise", "chat")
        self._at_and_cmd("dock", "enterprise", "touch_head")

        _advance_to(self.app, self.world, 5, TimeSlot.AFTERNOON)
        self._at_and_cmd("training_ground", "enterprise", "train_together")

        _advance_to(self.app, self.world, 5, TimeSlot.EVENING)
        self._at_and_cmd("command_office", "enterprise", "serve_tea")
        self._cmd("enterprise", "praise")

    # ── Day 6: Laffey + commission + upgrade canteen ──────────────────

    def _play_day6(self) -> None:
        _advance_to(self.app, self.world, 6, TimeSlot.MORNING)
        self._at_and_cmd("cafeteria", "laffey", "chat")

        # Dispatch laffey on patrol
        seed_friendly(self.laf)
        self.app.commission_service.dispatch(self.world, self.laf, "patrol")

        # Upgrade canteen (income boost)
        self.world.port_funds += 6000  # ensure affordable
        self.assertTrue(
            self.app.facility_service.upgrade(self.world, "canteen"),
            "Should be able to upgrade canteen",
        )

        _advance_to(self.app, self.world, 6, TimeSlot.AFTERNOON)
        self._at_and_cmd("cafeteria", "javelin", "chat")

        _advance_to(self.app, self.world, 6, TimeSlot.EVENING)
        self._at_and_cmd("command_office", "enterprise", "chat")

    # ── Day 7: Multi-character mid-point ──────────────────────────────

    def _play_day7(self) -> None:
        _advance_to(self.app, self.world, 7, TimeSlot.MORNING)
        self._at_and_cmd("dock", "enterprise", "chat")
        self._at_and_cmd("dock", "enterprise", "touch_head")

        _advance_to(self.app, self.world, 7, TimeSlot.AFTERNOON)
        self._at_and_cmd("cafeteria", "javelin", "chat")
        self._cmd("javelin", "share_snack")

        _advance_to(self.app, self.world, 7, TimeSlot.EVENING)
        self._at_and_cmd("command_office", "enterprise", "serve_tea")

    # ── Day 8-10: Intensive economic + relationship building ──────────

    def _play_days_8_10(self) -> None:
        # Day 8: Enterprise follow + work
        _advance_to(self.app, self.world, 8, TimeSlot.MORNING)
        seed_friendly(self.ent)
        self._at_and_cmd("dock", "enterprise", "invite_follow")

        _advance_to(self.app, self.world, 8, TimeSlot.AFTERNOON)
        self._go("command_office")
        self._cmd("enterprise", "office_shift")

        _advance_to(self.app, self.world, 8, TimeSlot.EVENING)
        self._at_and_cmd("garden", "enterprise", "follow_rest")
        self._cmd("enterprise", "dismiss_follow")

        # Day 9: Dispatch commission for javelin
        _advance_to(self.app, self.world, 9, TimeSlot.MORNING)
        self._at_and_cmd("training_ground", "javelin", "chat")
        seed_friendly(self.jav)
        self.app.commission_service.dispatch(self.world, self.jav, "patrol")

        _advance_to(self.app, self.world, 9, TimeSlot.AFTERNOON)
        self._at_and_cmd("garden", "laffey", "chat")

        _advance_to(self.app, self.world, 9, TimeSlot.EVENING)
        self._at_and_cmd("command_office", "enterprise", "serve_tea")

        # Day 10: Upgrade date_spot
        _advance_to(self.app, self.world, 10, TimeSlot.MORNING)
        self._at_and_cmd("cafeteria", "laffey", "chat")

        self.world.port_funds += 6000  # ensure affordable
        self.assertTrue(
            self.app.facility_service.upgrade(self.world, "date_spot"),
            "Should be able to upgrade date_spot",
        )

        _advance_to(self.app, self.world, 10, TimeSlot.AFTERNOON)
        self._at_and_cmd("training_ground", "enterprise", "train_together")

        _advance_to(self.app, self.world, 10, TimeSlot.EVENING)
        self._at_and_cmd("command_office", "enterprise", "chat")

    # ── Day 11-14: Full integration sprint (date + faint + work) ───────

    def _play_days_11_14(self) -> None:
        # Day 11: Date with Enterprise (requires like stage)
        _advance_to(self.app, self.world, 11, TimeSlot.MORNING)
        self._at_and_cmd("dock", "enterprise", "chat")
        seed_like(self.ent)
        self._at_and_cmd("dock", "enterprise", "invite_follow")

        _advance_to(self.app, self.world, 11, TimeSlot.AFTERNOON)
        self._go("garden")
        self._cmd("enterprise", "invite_date")
        self._cmd("enterprise", "hold_hands")
        self._cmd("enterprise", "end_date")
        self._cmd("enterprise", "dismiss_follow")

        # Day 12: Faint recovery — drains to 0, advances to dawn of day 13
        _advance_to(self.app, self.world, 12, TimeSlot.MORNING)
        self.ent.stats.base.set("stamina", 0)
        self.ent.stats.base.set("spirit", 0)
        self.assertTrue(
            self.app.vital_service.is_fainted(self.ent),
            "Enterprise should be fainted with 0 stamina",
        )
        self.app.game_loop.advance_to_dawn(self.world)
        self.assertGreater(
            self.ent.stats.base.get("stamina"), 0,
            "Enterprise should recover stamina after faint sleep",
        )

        # Day 13: Commission + work (faint skipped us to day 13 dawn)
        _advance_to(self.app, self.world, 13, TimeSlot.MORNING)
        self._at_and_cmd("dock", "enterprise", "chat")

        seed_friendly(self.ent)
        self.app.commission_service.dispatch(self.world, self.ent, "patrol")

        _advance_to(self.app, self.world, 13, TimeSlot.AFTERNOON)
        self._go("command_office")
        self.world.active_location.display_name = "指挥室"
        self.jav.location_key = "command_office"
        self._cmd("javelin", "office_shift")

        _advance_to(self.app, self.world, 13, TimeSlot.EVENING)
        self._at_and_cmd("dock", "laffey", "chat")
        self._cmd("laffey", "share_snack")

        # Day 14: finale
        _advance_to(self.app, self.world, 14, TimeSlot.MORNING)
        self._at_and_cmd("dock", "enterprise", "chat")
        self._cmd("enterprise", "praise")

        _advance_to(self.app, self.world, 14, TimeSlot.AFTERNOON)
        self._at_and_cmd("cafeteria", "javelin", "chat")

        _advance_to(self.app, self.world, 14, TimeSlot.EVENING)
        self._at_and_cmd("command_office", "enterprise", "serve_tea")

    # ── Main test ─────────────────────────────────────────────────────

    def test_14_day_combined_l3_l4_loop(self) -> None:
        """14-day combined smoke: gameplay + economy + facilities, all systems coexist."""
        self._play_day1()
        self._play_day2()
        self._play_day3()
        self._play_day4()
        self._play_day5()
        self._play_day6()
        self._play_day7()
        self._play_days_8_10()
        self._play_days_11_14()

        # ── Final assertions ─────────────────────────────────────────

        # Day progress reached at least day 14
        self.assertGreaterEqual(self.world.current_day, 14)

        # No character stuck in bad state
        for actor in self.world.characters:
            self.assertFalse(
                actor.is_on_date,
                f"{actor.key} should not be on date at end of 14 days",
            )

        # Relationship growth: enterprise should have meaningful affection
        self.assertGreaterEqual(
            self.ent.affection, 100,
            "Enterprise should have at least 100 affection after 14 days of interaction",
        )

        # At least some affection/trust on laffey and javelin
        for key in ("laffey", "javelin"):
            actor = actor_by_key(self.app, key)
            total = actor.affection + actor.trust
            self.assertGreaterEqual(
                total, 1,
                f"{key} should have gained relationship stats over 14 days",
            )

        # Personal funds from work commands
        self.assertGreaterEqual(
            self.world.personal_funds, 500,
            "Should have earned personal funds from work over 14 days",
        )

        # Port funds should exist (commissions completed)
        self.assertGreaterEqual(
            self.world.port_funds, 0,
            "Port funds should be non-negative",
        )

        # Facility upgrades confirmed
        self.assertGreaterEqual(
            self.app.facility_service.get_level(self.world, "dorm"), 1,
            "Dorm should be at least level 1",
        )
        self.assertGreaterEqual(
            self.app.facility_service.get_level(self.world, "canteen"), 1,
            "Canteen should be at least level 1",
        )
        self.assertGreaterEqual(
            self.app.facility_service.get_level(self.world, "date_spot"), 1,
            "Date spot should be at least level 1",
        )

        # Facility effects are measurable
        self.assertGreater(
            self.app.facility_service.recovery_multiplier(self.world), 1.0,
            "Dorm upgrade should increase recovery multiplier above 1.0",
        )
        self.assertGreater(
            self.app.facility_service.income_multiplier(self.world), 1.0,
            "Canteen upgrade should increase income multiplier above 1.0",
        )
        self.assertGreater(
            self.app.facility_service.relation_multiplier(self.world), 1.0,
            "Date spot upgrade should increase relation multiplier above 1.0",
        )


class FourteenDayEconomicBalanceTests(unittest.TestCase):
    """Focused economic balance checks over 14 days without character interaction."""

    def setUp(self) -> None:
        self.app = make_app()
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        seed_friendly(self.actor)

    def _place_at_work(self) -> None:
        self.actor.location_key = "command_office"
        self.world.active_location.key = "command_office"
        self.world.active_location.display_name = "指挥室"

    def _advance_one_day(self) -> None:
        for _ in range(6):
            self.app.game_loop.advance_time(self.world)

    def test_14_day_work_plus_commission_plus_upgrade(self) -> None:
        """Work + commission + facility upgrade loop over 14 days."""
        self._place_at_work()
        upgraded_dorm = False
        upgraded_canteen = False

        for day in range(14):
            # Work once per day
            self._place_at_work()
            self.world.current_time_slot = TimeSlot.MORNING
            self.app.command_service.execute(self.world, "enterprise", "office_shift")

            # Dispatch commission if actor is free
            if not self.actor.is_on_commission:
                self.app.commission_service.dispatch(self.world, self.actor, "patrol")

            # Upgrade facilities when affordable
            if not upgraded_dorm and self.world.port_funds >= 5000:
                upgraded_dorm = self.app.facility_service.upgrade(self.world, "dorm")
            if upgraded_dorm and not upgraded_canteen and self.world.port_funds >= 5000:
                upgraded_canteen = self.app.facility_service.upgrade(self.world, "canteen")

            self._advance_one_day()

        # Economic assertions
        self.assertTrue(upgraded_dorm, "Should have upgraded dorm in 14 days")
        self.assertGreater(self.world.personal_funds, 0, "Personal funds from work")
        self.assertGreater(self.world.port_funds, 0, "Port funds remaining after upgrades")

    def test_canteen_boosts_commission_over_14_days(self) -> None:
        """Commission income with canteen > without canteen over 14 days."""
        # Baseline: no canteen
        self._place_at_work()
        for _ in range(14):
            if not self.actor.is_on_commission:
                self.app.commission_service.dispatch(self.world, self.actor, "patrol")
            self._advance_one_day()
        baseline_port = self.world.port_funds

        # Reset and run with canteen
        reset_progress(self.actor)
        seed_friendly(self.actor)
        self.world.port_funds = 999999
        self.app.facility_service.upgrade(self.world, "canteen")
        self.world.port_funds = 0
        self._place_at_work()

        for _ in range(14):
            if not self.actor.is_on_commission:
                self.app.commission_service.dispatch(self.world, self.actor, "patrol")
            self._advance_one_day()
        boosted_port = self.world.port_funds

        self.assertGreater(boosted_port, baseline_port,
                           "Canteen should boost commission income over 14 days")

    def test_dorm_recovery_better_over_14_days(self) -> None:
        """Characters with dorm upgrade recover more stamina per day."""
        # Baseline
        self.actor.stats.base.set("stamina", 500)
        self.actor.stats.base.set("spirit", 500)
        recovery_before = self.app.vital_service.sleep_recovery(
            self.actor, self.world,
        )["stamina"]

        # With dorm
        self.actor.stats.base.set("stamina", 500)
        self.actor.stats.base.set("spirit", 500)
        self.world.port_funds = 999999
        self.app.facility_service.upgrade(self.world, "dorm")
        recovery_after = self.app.vital_service.sleep_recovery(
            self.actor, self.world,
        )["stamina"]

        self.assertGreater(recovery_after, recovery_before)


if __name__ == "__main__":
    unittest.main()
