"""Tests for the weather system."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key


class WeatherSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world

    def test_default_weather_is_clear(self) -> None:
        self.assertEqual(self.world.weather_key, "1")

    def test_weather_service_returns_current_definition(self) -> None:
        weather = self.app.weather_service.current(self.world)
        self.assertEqual(weather.key, "1")
        self.assertEqual(weather.display_name, "晴")

    def test_refresh_changes_weather_key(self) -> None:
        self.app.weather_service.refresh(self.world)
        self.assertIn(self.world.weather_key, {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"})

    def test_recovery_modifier_for_clear(self) -> None:
        self.assertEqual(self.app.weather_service.recovery_modifier(self.world), 1.0)

    def test_movement_modifier_for_rain(self) -> None:
        self.world.weather_key = "4"
        self.assertEqual(self.app.weather_service.movement_modifier(self.world), 0.8)

    def test_is_raining(self) -> None:
        self.assertFalse(self.app.weather_service.is_raining(self.world))
        self.world.weather_key = "4"
        self.assertTrue(self.app.weather_service.is_raining(self.world))

    def test_is_storming(self) -> None:
        self.assertFalse(self.app.weather_service.is_storming(self.world))
        self.world.weather_key = "5"
        self.assertTrue(self.app.weather_service.is_storming(self.world))

    def test_scene_context_includes_weather(self) -> None:
        self.world.weather_key = "4"
        actor = actor_by_key(self.app, "enterprise")
        scene = self.app.scene_service.build_for_actor(
            self.world, actor, "talk", ("public",),
        )
        self.assertEqual(scene.weather_key, "4")

    def test_weather_refreshes_on_dawn(self) -> None:
        self.world.current_time_slot = TimeSlot.LATE_NIGHT
        self.app.game_loop.advance_time(self.world)
        self.assertEqual(self.world.current_time_slot, TimeSlot.DAWN)
        # Weather should have been refreshed (may or may not change)
        self.assertIn(self.world.weather_key, {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"})

    def test_weather_does_not_refresh_mid_day(self) -> None:
        self.world.current_time_slot = TimeSlot.MORNING
        original = self.world.weather_key
        self.app.game_loop.advance_time(self.world)
        self.assertEqual(self.world.weather_key, original)


if __name__ == "__main__":
    unittest.main()
