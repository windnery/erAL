"""Smoke tests for multi-day playable flow."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from eral.domain.compat_semantics import CFLAGKey, actor_cflag


def _actor(world, key: str):
    return next(a for a in world.characters if a.key == key)


def _seed_friendly(actor, app=None) -> None:
    actor_cflag.set(actor, CFLAGKey.AFFECTION, 210)
    actor_cflag.set(actor, CFLAGKey.TRUST, 110)
    actor.sync_derived_fields()
    if app is not None:
        app.relationship_service.update_actor(actor)


def _advance_to(app, world, day: int, slot: TimeSlot) -> None:
    """Fast-forward until target day/time_slot is reached."""
    while True:
        if world.current_day == day and world.current_time_slot == slot:
            return
        if world.current_day > day:
            return
        app.game_loop.advance_time(world)


class ThreeDayPlayableSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def test_three_day_loop_remains_playable(self) -> None:
        world = self.app.world
        enterprise = next(actor for actor in world.characters if actor.key == "enterprise")
        laffey = next(actor for actor in world.characters if actor.key == "laffey")

        # Day 1 morning: enterprise is at dock
        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "dock")
        self.app.command_service.execute(world, enterprise.key, "chat")
        self.app.command_service.execute(world, enterprise.key, "touch_head")
        _seed_friendly(enterprise, self.app)
        self.app.command_service.execute(world, enterprise.key, "invite_follow")

        self.app.game_loop.advance_time(world)
        self.app.companion_service.refresh_world(world)
        # afternoon: enterprise follows, go to training_ground
        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "training_ground")
        self.app.command_service.execute(world, enterprise.key, "walk_together")
        self.app.command_service.execute(world, enterprise.key, "follow_training")

        self.app.game_loop.advance_time(world)
        self.app.companion_service.refresh_world(world)
        # evening: go to garden for rest
        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "garden")
        self.app.command_service.execute(world, enterprise.key, "follow_rest")
        self.app.command_service.execute(world, enterprise.key, "dismiss_follow")

        # Day 2
        while not (world.current_day == 2 and world.current_time_slot == TimeSlot.AFTERNOON):
            self.app.game_loop.advance_time(world)
            self.app.companion_service.refresh_world(world)

        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "garden")
        self.app.command_service.execute(world, laffey.key, "chat")
        self.app.command_service.execute(world, laffey.key, "share_snack")

        # Day 3
        while not (world.current_day == 3 and world.current_time_slot == TimeSlot.EVENING):
            self.app.game_loop.advance_time(world)
            self.app.companion_service.refresh_world(world)

        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "dock")
        self.app.command_service.execute(world, laffey.key, "clink_cups")

        self.assertGreaterEqual(enterprise.affection, 210)
        self.assertTrue(enterprise.is_following is False or enterprise.affection >= 210)
        self.assertGreaterEqual(laffey.affection, 1)


class SevenDayPlayableSmokeTests(unittest.TestCase):
    """Exercise real characters across 7 in-game days without errors."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world

    def _go(self, *locations: str) -> None:
        """Navigate through a sequence, auto-inserting main_corridor when needed."""
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

    def _advance_to(self, day: int, slot: TimeSlot) -> None:
        _advance_to(self.app, self.world, day, slot)

    # ── Day 1: Enterprise (morning: dock, afternoon: training_ground, evening: command_office) ──

    def _play_day1(self) -> None:
        self._advance_to(1, TimeSlot.MORNING)
        self._go("dock")
        self._cmd("enterprise", "chat")
        self._cmd("enterprise", "touch_head")
        self._cmd("enterprise", "praise")
        _seed_friendly(_actor(self.world, "enterprise"))

        self._advance_to(1, TimeSlot.AFTERNOON)
        self._go("training_ground")
        self._cmd("enterprise", "train_together")

        self._advance_to(1, TimeSlot.EVENING)
        self._go("command_office")
        self._cmd("enterprise", "serve_tea")
        self._cmd("enterprise", "chat")

    # ── Day 2: Enterprise follow + build affection ──

    def _play_day2(self) -> None:
        self._advance_to(2, TimeSlot.MORNING)
        self._go("dock")
        _seed_friendly(_actor(self.world, "enterprise"))
        self._cmd("enterprise", "invite_follow")

        self._advance_to(2, TimeSlot.AFTERNOON)
        self._go("training_ground")
        self._cmd("enterprise", "follow_training")

        self._advance_to(2, TimeSlot.EVENING)
        self._go("garden")
        self._cmd("enterprise", "follow_rest")
        self._cmd("enterprise", "dismiss_follow")

    # ── Day 3: Laffey (morning: cafeteria, afternoon: garden, evening: dock) ──

    def _play_day3(self) -> None:
        self._advance_to(3, TimeSlot.MORNING)
        self._go("cafeteria")
        self._cmd("laffey", "chat")
        self._cmd("laffey", "share_snack")

        self._advance_to(3, TimeSlot.AFTERNOON)
        self._go("garden")
        self._cmd("laffey", "rest")
        self._cmd("laffey", "touch_head")

        self._advance_to(3, TimeSlot.EVENING)
        self._go("dock")
        self._cmd("laffey", "listen")

    # ── Day 4: Javelin (morning: training_ground, afternoon: cafeteria, evening: garden) ──

    def _play_day4(self) -> None:
        self._advance_to(4, TimeSlot.MORNING)
        self._go("training_ground")
        self._cmd("javelin", "chat")
        self._cmd("javelin", "praise")

        self._advance_to(4, TimeSlot.AFTERNOON)
        self._go("cafeteria")
        self._cmd("javelin", "share_snack")

        self._advance_to(4, TimeSlot.EVENING)
        self._go("garden")
        self._cmd("javelin", "listen")

    # ── Day 5: Enterprise again ──

    def _play_day5(self) -> None:
        self._advance_to(5, TimeSlot.MORNING)
        self._go("dock")
        self._cmd("enterprise", "chat")
        self._cmd("enterprise", "touch_head")

        self._advance_to(5, TimeSlot.AFTERNOON)
        self._go("training_ground")
        self._cmd("enterprise", "train_together")

        self._advance_to(5, TimeSlot.EVENING)
        self._go("command_office")
        self._cmd("enterprise", "serve_tea")
        self._cmd("enterprise", "praise")

    # ── Day 6: Laffey again ──

    def _play_day6(self) -> None:
        self._advance_to(6, TimeSlot.MORNING)
        self._go("cafeteria")
        self._cmd("laffey", "chat")
        self._cmd("laffey", "touch_head")

        self._advance_to(6, TimeSlot.AFTERNOON)
        self._go("garden")
        self._cmd("laffey", "rest")
        self._cmd("laffey", "praise")

        self._advance_to(6, TimeSlot.EVENING)
        self._go("dock")
        self._cmd("laffey", "clink_cups")

    # ── Day 7: Multi-character finale ──

    def _play_day7(self) -> None:
        self._advance_to(7, TimeSlot.AFTERNOON)
        # afternoon: javelin at cafeteria, laffey at garden
        self._go("cafeteria")
        self._cmd("javelin", "chat")
        self._cmd("javelin", "share_snack")

        self._advance_to(7, TimeSlot.EVENING)
        # evening: enterprise at command_office, laffey at dock, javelin at garden
        self._go("command_office")
        self._cmd("enterprise", "chat")
        self._cmd("enterprise", "serve_tea")

        self._go("dock")
        self._cmd("laffey", "clink_cups")
        self._cmd("laffey", "listen")

    def test_seven_day_loop_remains_playable(self) -> None:
        self._play_day1()
        self._play_day2()
        self._play_day3()
        self._play_day4()
        self._play_day5()
        self._play_day6()
        self._play_day7()

        self.assertGreaterEqual(self.world.current_day, 7)

        ent = _actor(self.world, "enterprise")
        self.assertGreaterEqual(ent.affection, 210)

        for key in ("laffey", "javelin"):
            actor = _actor(self.world, key)
            self.assertGreaterEqual(
                actor.affection + actor.trust, 1,
                f"{key} should have gained at least 1 affection or trust over 7 days",
            )

        for actor in self.world.characters:
            self.assertFalse(actor.is_on_date, f"{actor.key} should not be on date at end")


if __name__ == "__main__":
    unittest.main()