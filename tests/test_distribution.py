"""Tests for lightweight map distribution helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from tests.support.real_actors import actor_by_key


class DistributionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world

    def test_commissioned_actor_is_excluded_from_present_characters(self) -> None:
        actor = actor_by_key(self.app, "enterprise")
        actor.is_on_commission = True

        present = self.app.distribution_service.present_characters(self.world, "dock")

        self.assertNotIn(actor.key, [item.key for item in present])

    def test_present_characters_returns_sorted_visible_characters_for_location(self) -> None:
        present = self.app.distribution_service.present_characters(self.world, "dock")

        self.assertTrue(all(actor.location_key == "dock" for actor in present))
        self.assertGreaterEqual(len(present), 1)

    def test_refresh_world_places_actor_at_real_time_work_schedule_location(self) -> None:
        enterprise = actor_by_key(self.app, "enterprise")
        self.world.current_weekday = "mon"
        self.world.current_month = 1
        self.world.current_day = 6
        self.world.current_hour = 10
        self.world.current_minute = 0
        self.world.sync_time_slot_from_clock()

        self.app.distribution_service.refresh_world(self.world)

        self.assertEqual(enterprise.location_key, "command_office")

    def test_refresh_world_staggers_dinner_window_by_actor(self) -> None:
        enterprise = actor_by_key(self.app, "enterprise")
        laffey = actor_by_key(self.app, "laffey")
        javelin = actor_by_key(self.app, "javelin")
        self.world.current_weekday = "mon"
        self.world.current_month = 1
        self.world.current_day = 6
        self.world.current_hour = 17
        self.world.current_minute = 50
        self.world.sync_time_slot_from_clock()

        self.app.distribution_service.refresh_world(self.world)

        self.assertEqual(javelin.location_key, "cafeteria")
        self.assertNotEqual(enterprise.location_key, "cafeteria")
        self.assertNotEqual(laffey.location_key, "cafeteria")

    def test_refresh_world_returns_to_home_location_during_late_night(self) -> None:
        enterprise = actor_by_key(self.app, "enterprise")
        laffey = actor_by_key(self.app, "laffey")
        javelin = actor_by_key(self.app, "javelin")
        self.world.current_weekday = "mon"
        self.world.current_month = 1
        self.world.current_day = 6
        self.world.current_hour = 0
        self.world.current_minute = 30
        self.world.sync_time_slot_from_clock()

        self.app.distribution_service.refresh_world(self.world)

        self.assertEqual(enterprise.location_key, "dormitory_a")
        self.assertEqual(laffey.location_key, "dormitory_a")
        self.assertEqual(javelin.location_key, "garden")

    def test_refresh_world_can_bias_off_duty_actor_toward_player_location(self) -> None:
        enterprise = actor_by_key(self.app, "enterprise")
        self.world.active_location.key = "garden"
        self.world.active_location.display_name = "庭院"
        self.world.current_weekday = "sat"
        self.world.current_month = 1
        self.world.current_day = 10
        self.world.current_hour = 15
        self.world.current_minute = 30
        self.world.sync_time_slot_from_clock()
        enterprise.affection = 400
        enterprise.trust = 400

        self.app.distribution_service.refresh_world(self.world)

        self.assertEqual(enterprise.location_key, "garden")


if __name__ == "__main__":
    unittest.main()
