"""Regression tests for multi-character concurrent play flows."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot


class MultiCharacterRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.secretary = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")
        self.destroyer = next(actor for actor in self.app.world.characters if actor.key == "starter_destroyer")
        self.cruiser = next(actor for actor in self.app.world.characters if actor.key == "starter_cruiser")

    def test_three_characters_can_progress_in_parallel_without_state_collision(self) -> None:
        world = self.app.world

        world.current_time_slot = TimeSlot.MORNING
        world.active_location.key = "command_office"
        world.active_location.display_name = "指挥室"
        self.secretary.location_key = "command_office"
        self.destroyer.location_key = "command_office"
        self.cruiser.location_key = "cafeteria"

        self.app.command_service.execute(world, self.secretary.key, "chat")
        self.app.command_service.execute(world, self.destroyer.key, "praise")

        self.app.game_loop.advance_time(world)
        self.app.companion_service.refresh_world(world)
        world.active_location.key = "command_office"
        world.active_location.display_name = "指挥室"
        self.cruiser.location_key = "command_office"
        self.app.command_service.execute(world, self.cruiser.key, "study")

        self.secretary.affection = 3
        self.secretary.trust = 2
        self.secretary.stats.compat.cflag.set(2, 3)
        self.secretary.stats.compat.cflag.set(4, 2)
        self.app.relationship_service.update_actor(self.secretary)

        world.current_time_slot = TimeSlot.EVENING
        world.active_location.key = "cafeteria"
        world.active_location.display_name = "食堂"
        self.secretary.location_key = "cafeteria"
        self.destroyer.location_key = "cafeteria"
        self.cruiser.location_key = "cafeteria"

        self.app.command_service.execute(world, self.secretary.key, "invite_follow")
        self.app.command_service.execute(world, self.secretary.key, "invite_date")
        self.app.command_service.execute(world, self.destroyer.key, "invite_meal")
        self.app.command_service.execute(world, self.cruiser.key, "share_snack")

        self.assertTrue(self.secretary.is_on_date)
        self.assertTrue(self.secretary.is_following)
        self.assertFalse(self.destroyer.is_on_date)
        self.assertFalse(self.destroyer.is_following)
        self.assertFalse(self.cruiser.is_on_date)

        self.assertGreaterEqual(self.secretary.affection, 4)
        self.assertGreaterEqual(self.destroyer.affection, 2)
        self.assertGreaterEqual(self.cruiser.affection, 3)
        self.assertEqual(world.date_partner_key, self.secretary.key)

    def test_multi_character_dialogue_resolution_stays_actor_scoped(self) -> None:
        world = self.app.world
        world.current_time_slot = TimeSlot.EVENING
        world.active_location.key = "dock"
        world.active_location.display_name = "码头"
        self.secretary.location_key = "dock"
        self.destroyer.location_key = "dock"
        self.cruiser.location_key = "dock"

        sec_result = self.app.command_service.execute(world, self.secretary.key, "clink_cups")
        des_result = self.app.command_service.execute(world, self.destroyer.key, "clink_cups")
        cru_result = self.app.command_service.execute(world, self.cruiser.key, "clink_cups")

        self.assertNotEqual(sec_result.messages, des_result.messages)
        self.assertNotEqual(sec_result.messages, cru_result.messages)
        self.assertNotEqual(des_result.messages, cru_result.messages)
        self.assertTrue(any("夜风" in line or "杯" in line for line in sec_result.messages))
        self.assertTrue(any("庆功会" in line or "碰了过来" in line for line in des_result.messages))
        self.assertTrue(any("从容" in line or "记住" in line for line in cru_result.messages))


if __name__ == "__main__":
    unittest.main()
