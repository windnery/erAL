"""Smoke tests for multi-day playable flow."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot


def _actor(world, key: str):
    return next(a for a in world.characters if a.key == key)


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
        secretary = next(actor for actor in world.characters if actor.key == "starter_secretary")
        destroyer = next(actor for actor in world.characters if actor.key == "starter_destroyer")
        cruiser = next(actor for actor in world.characters if actor.key == "starter_cruiser")

        self.app.command_service.execute(world, secretary.key, "chat")
        self.app.command_service.execute(world, secretary.key, "invite_follow")
        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "dock")
        self.app.command_service.execute(world, secretary.key, "walk_together")

        self.app.game_loop.advance_time(world)
        self.app.companion_service.refresh_world(world)
        self.app.command_service.execute(world, secretary.key, "invite_date")
        self.app.command_service.execute(world, secretary.key, "date_stroll")

        self.app.game_loop.advance_time(world)
        self.app.companion_service.refresh_world(world)
        self.app.command_service.execute(world, secretary.key, "date_watch_sea")

        self.app.game_loop.advance_time(world)
        self.app.companion_service.refresh_world(world)
        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "bathhouse")
        self.app.command_service.execute(world, secretary.key, "date_tease")
        self.app.command_service.execute(world, secretary.key, "end_date")

        while not (world.current_day == 2 and world.current_time_slot == TimeSlot.MORNING):
            self.app.game_loop.advance_time(world)
            self.app.companion_service.refresh_world(world)

        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "command_office")
        self.app.command_service.execute(world, destroyer.key, "chat")
        self.app.command_service.execute(world, destroyer.key, "serve_tea")
        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "cafeteria")
        self.app.command_service.execute(world, cruiser.key, "chat")
        self.app.command_service.execute(world, cruiser.key, "share_snack")

        while not (world.current_day == 3 and world.current_time_slot == TimeSlot.EVENING):
            self.app.game_loop.advance_time(world)
            self.app.companion_service.refresh_world(world)

        self.app.navigation_service.move_player(world, "main_corridor")
        self.app.navigation_service.move_player(world, "dock")
        self.app.command_service.execute(world, destroyer.key, "clink_cups")
        self.app.command_service.execute(world, cruiser.key, "clink_cups")

        while not (world.current_day == 4 and world.current_time_slot == TimeSlot.MORNING):
            self.app.game_loop.advance_time(world)
            self.app.companion_service.refresh_world(world)

        self.assertEqual(world.current_day, 4)
        self.assertEqual(world.current_time_slot, TimeSlot.MORNING)
        self.assertGreaterEqual(secretary.affection, 8)
        self.assertTrue(secretary.has_mark("teased"))
        self.assertFalse(secretary.is_on_date)
        self.assertTrue(secretary.is_following)
        self.assertGreaterEqual(destroyer.affection, 1)
        self.assertGreaterEqual(cruiser.trust, 1)


class SevenDayPlayableSmokeTests(unittest.TestCase):
    """Exercise all 5 characters across 7 in-game days without errors."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world

    # ── helpers ──

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

    # ── Day 1: Secretary intro (morning: office, afternoon: training, evening: cafeteria) ──

    def _play_day1(self) -> None:
        self._advance_to(1, TimeSlot.MORNING)
        self._go("command_office")
        self._cmd("starter_secretary", "chat")
        self._cmd("starter_secretary", "serve_tea")
        self._cmd("starter_secretary", "paperwork")

        self._advance_to(1, TimeSlot.AFTERNOON)
        self._go("main_corridor", "training_ground")
        self._cmd("starter_secretary", "train_together")

        self._advance_to(1, TimeSlot.EVENING)
        self._go("main_corridor", "cafeteria")
        self._cmd("starter_secretary", "invite_meal")
        self._cmd("starter_secretary", "eat_meal")

    # ── Day 2: Secretary date ──

    def _play_day2(self) -> None:
        self._advance_to(2, TimeSlot.MORNING)
        self._go("command_office")
        self._cmd("starter_secretary", "invite_follow")

        self._advance_to(2, TimeSlot.AFTERNOON)
        self._cmd("starter_secretary", "invite_date")
        self._go("main_corridor", "dock")
        self._cmd("starter_secretary", "date_stroll")
        self._cmd("starter_secretary", "hold_hands")

        self._advance_to(2, TimeSlot.EVENING)
        self._go("main_corridor", "cafeteria")
        self._cmd("starter_secretary", "date_meal")
        self._cmd("starter_secretary", "dessert_date")
        self._cmd("starter_secretary", "end_date")

    # ── Day 3: Destroyer (morning: office, afternoon: training, evening: dock) ──

    def _play_day3(self) -> None:
        self._advance_to(3, TimeSlot.MORNING)
        self._go("command_office")
        self._cmd("starter_destroyer", "chat")
        self._cmd("starter_destroyer", "praise")

        self._advance_to(3, TimeSlot.AFTERNOON)
        self._go("main_corridor", "training_ground")
        self._cmd("starter_destroyer", "train_together")

        self._advance_to(3, TimeSlot.EVENING)
        self._go("main_corridor", "dock")
        self._cmd("starter_destroyer", "clink_cups")

    # ── Day 4: Cruiser (morning: cafeteria, afternoon: office, evening: dock) ──

    def _play_day4(self) -> None:
        self._advance_to(4, TimeSlot.MORNING)
        self._go("cafeteria")
        self._cmd("starter_cruiser", "chat")
        self._cmd("starter_cruiser", "share_snack")

        self._advance_to(4, TimeSlot.AFTERNOON)
        self._go("command_office")
        self._cmd("starter_cruiser", "study")

        self._advance_to(4, TimeSlot.EVENING)
        self._go("dock")
        self._cmd("starter_cruiser", "listen")

    # ── Day 5: Enterprise (morning: dock, afternoon: training, evening: office) ──

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

    # ── Day 6: Laffey (morning: cafeteria, afternoon: garden, evening: dock) ──

    def _play_day6(self) -> None:
        self._advance_to(6, TimeSlot.MORNING)
        self._go("cafeteria")
        self._cmd("laffey", "chat")
        self._cmd("laffey", "share_snack")

        self._advance_to(6, TimeSlot.AFTERNOON)
        self._go("garden")
        self._cmd("laffey", "rest")
        self._cmd("laffey", "touch_head")

        self._advance_to(6, TimeSlot.EVENING)
        self._go("dock")
        self._cmd("laffey", "listen")
        self._cmd("laffey", "clink_cups")

    # ── Day 7: Multi-character finale ──

    def _play_day7(self) -> None:
        self._advance_to(7, TimeSlot.MORNING)
        self._go("main_corridor", "command_office")
        self._cmd("starter_secretary", "chat")
        self._cmd("starter_destroyer", "share_snack")

        self._advance_to(7, TimeSlot.AFTERNOON)
        self._go("main_corridor", "command_office")
        self._cmd("starter_cruiser", "study")

        self._advance_to(7, TimeSlot.EVENING)
        self._go("main_corridor", "dock")
        self._cmd("starter_destroyer", "clink_cups")
        self._cmd("starter_cruiser", "clink_cups")
        self._cmd("laffey", "listen")

    def test_seven_day_loop_remains_playable(self) -> None:
        self._play_day1()
        self._play_day2()
        self._play_day3()
        self._play_day4()
        self._play_day5()
        self._play_day6()
        self._play_day7()

        # Basic sanity: 7 full days completed
        self.assertGreaterEqual(self.world.current_day, 7)

        # Secretary should have progressed significantly
        sec = _actor(self.world, "starter_secretary")
        self.assertGreaterEqual(sec.affection, 5)

        # All other characters should have at least some affection/trust growth
        for key in ("starter_destroyer", "starter_cruiser", "enterprise", "laffey"):
            actor = _actor(self.world, key)
            self.assertGreaterEqual(
                actor.affection + actor.trust, 1,
                f"{key} should have gained at least 1 affection or trust over 7 days",
            )

        # No stale follow/date state
        for actor in self.world.characters:
            self.assertFalse(actor.is_on_date, f"{actor.key} should not be on date at end")


if __name__ == "__main__":
    unittest.main()
