"""Tests for shop NPC presence and shop command availability."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key


class ShopNpcPresenceTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world

    def test_akashi_present_at_general_store_during_day(self) -> None:
        self.world.active_location.key = "general_store"
        self.world.current_time_slot = TimeSlot.MORNING
        self.app.distribution_service.refresh_world(self.world)
        visible = self.world.visible_characters()
        keys = {a.key for a in visible}
        self.assertIn("akashi", keys)

    def test_akashi_at_home_at_night(self) -> None:
        self.world.active_location.key = "sakura_dorm_hall"
        self.world.current_time_slot = TimeSlot.NIGHT
        self.app.distribution_service.refresh_world(self.world)
        visible = self.world.visible_characters()
        keys = {a.key for a in visible}
        self.assertIn("akashi", keys)

    def test_shiranui_present_at_skin_boutique_during_day(self) -> None:
        self.world.active_location.key = "skin_boutique"
        self.world.current_time_slot = TimeSlot.AFTERNOON
        self.app.distribution_service.refresh_world(self.world)
        visible = self.world.visible_characters()
        keys = {a.key for a in visible}
        self.assertIn("shiranui", keys)

    def test_shiranui_at_home_at_night(self) -> None:
        self.world.active_location.key = "sakura_dorm_hall"
        self.world.current_time_slot = TimeSlot.NIGHT
        self.app.distribution_service.refresh_world(self.world)
        visible = self.world.visible_characters()
        keys = {a.key for a in visible}
        self.assertIn("shiranui", keys)


class ShopCommandAvailabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world

    def test_browse_general_shop_available_for_akashi_at_shop(self) -> None:
        self.world.active_location.key = "general_store"
        self.world.current_time_slot = TimeSlot.MORNING
        self.app.distribution_service.refresh_world(self.world)
        cmds = self.app.command_service.available_commands_for_actor(
            self.world, "akashi"
        )
        keys = {c.key for c in cmds}
        self.assertIn("browse_general_shop", keys)

    def test_browse_general_shop_not_available_for_enterprise(self) -> None:
        self.world.active_location.key = "general_store"
        self.world.current_time_slot = TimeSlot.MORNING
        self.app.distribution_service.refresh_world(self.world)
        # Move enterprise to general_store so location gate passes
        enterprise = actor_by_key(self.app, "enterprise")
        enterprise.location_key = "general_store"
        cmds = self.app.command_service.available_commands_for_actor(
            self.world, "enterprise"
        )
        keys = {c.key for c in cmds}
        self.assertNotIn("browse_general_shop", keys)

    def test_browse_skin_shop_available_for_shiranui_at_shop(self) -> None:
        self.world.active_location.key = "skin_boutique"
        self.world.current_time_slot = TimeSlot.MORNING
        self.app.distribution_service.refresh_world(self.world)
        cmds = self.app.command_service.available_commands_for_actor(
            self.world, "shiranui"
        )
        keys = {c.key for c in cmds}
        self.assertIn("browse_skin_shop", keys)

    def test_shop_command_returns_shopfront_key(self) -> None:
        self.world.active_location.key = "general_store"
        self.world.current_time_slot = TimeSlot.MORNING
        self.app.distribution_service.refresh_world(self.world)
        result = self.app.command_service.execute(
            self.world, "akashi", "browse_general_shop"
        )
        self.assertEqual(result.shopfront_key, "general_shop")
        self.assertTrue(result.success)

    def test_shop_command_not_available_when_npc_absent(self) -> None:
        self.world.active_location.key = "command_office"
        self.world.current_time_slot = TimeSlot.MORNING
        self.app.distribution_service.refresh_world(self.world)
        cmds = self.app.command_service.available_commands_for_actor(
            self.world, "akashi"
        )
        keys = {c.key for c in cmds}
        self.assertNotIn("browse_general_shop", keys)


if __name__ == "__main__":
    unittest.main()
