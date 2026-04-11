"""Smoke test for multi-day playable flow."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot


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


if __name__ == "__main__":
    unittest.main()
