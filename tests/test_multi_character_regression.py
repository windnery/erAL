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
        self.enterprise = next(actor for actor in self.app.world.characters if actor.key == "enterprise")
        self.laffey = next(actor for actor in self.app.world.characters if actor.key == "laffey")
        self.javelin = next(actor for actor in self.app.world.characters if actor.key == "javelin")

    def test_three_characters_can_progress_in_parallel_without_state_collision(self) -> None:
        world = self.app.world

        world.current_time_slot = TimeSlot.MORNING
        world.active_location.key = "command_office"
        world.active_location.display_name = "指挥室"
        self.enterprise.location_key = "command_office"
        self.laffey.location_key = "command_office"
        self.javelin.location_key = "cafeteria"

        self.app.command_service.execute(world, self.enterprise.key, "chat")
        self.app.command_service.execute(world, self.laffey.key, "praise")

        self.app.game_loop.advance_time(world)
        self.app.companion_service.refresh_world(world)
        world.active_location.key = "command_office"
        world.active_location.display_name = "指挥室"
        self.javelin.location_key = "command_office"
        self.app.command_service.execute(world, self.javelin.key, "chat")

        self.enterprise.affection = 3
        self.enterprise.trust = 2
        self.enterprise.stats.compat.cflag.set(2, 3)
        self.enterprise.stats.compat.cflag.set(4, 2)
        self.app.relationship_service.update_actor(self.enterprise)

        world.current_time_slot = TimeSlot.EVENING
        world.active_location.key = "cafeteria"
        world.active_location.display_name = "食堂"
        self.enterprise.location_key = "cafeteria"
        self.laffey.location_key = "cafeteria"
        self.javelin.location_key = "cafeteria"

        self.app.command_service.execute(world, self.enterprise.key, "invite_follow")
        self.app.command_service.execute(world, self.enterprise.key, "invite_date")
        self.app.command_service.execute(world, self.laffey.key, "invite_meal")
        self.app.command_service.execute(world, self.javelin.key, "share_snack")

        self.assertTrue(self.enterprise.is_on_date)
        self.assertTrue(self.enterprise.is_following)
        self.assertFalse(self.laffey.is_on_date)
        self.assertFalse(self.laffey.is_following)
        self.assertFalse(self.javelin.is_on_date)

        self.assertGreaterEqual(self.enterprise.affection, 4)
        self.assertGreaterEqual(self.laffey.affection, 2)
        self.assertGreaterEqual(self.javelin.affection, 1)
        self.assertEqual(world.date_partner_key, self.enterprise.key)

    def test_multi_character_dialogue_resolution_stays_actor_scoped(self) -> None:
        world = self.app.world
        world.current_time_slot = TimeSlot.EVENING
        world.active_location.key = "dock"
        world.active_location.display_name = "码头"
        self.enterprise.location_key = "dock"
        self.laffey.location_key = "dock"
        self.javelin.location_key = "dock"

        ent_result = self.app.command_service.execute(world, self.enterprise.key, "clink_cups")
        laf_result = self.app.command_service.execute(world, self.laffey.key, "clink_cups")
        jav_result = self.app.command_service.execute(world, self.javelin.key, "clink_cups")

        self.assertNotEqual(ent_result.messages, laf_result.messages)
        self.assertNotEqual(ent_result.messages, jav_result.messages)
        self.assertNotEqual(laf_result.messages, jav_result.messages)
        self.assertTrue(any("企业" in line or "报告" in line for line in ent_result.messages))
        self.assertTrue(any("拉菲" in line or "海" in line for line in laf_result.messages))


if __name__ == "__main__":
    unittest.main()