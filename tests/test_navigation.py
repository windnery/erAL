"""Navigation tests for the starter map."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot


class NavigationTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        return next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")

    def test_move_player_to_neighboring_location(self) -> None:
        result = self.app.navigation_service.move_player(self.app.world, "main_corridor")

        self.assertEqual(result.action_key, "move")
        self.assertEqual(self.app.world.active_location.key, "main_corridor")

    def test_move_player_to_non_neighbor_fails(self) -> None:
        with self.assertRaises(ValueError):
            self.app.navigation_service.move_player(self.app.world, "dock")

    def test_encounter_on_arrival(self) -> None:
        """Moving to a location with a character produces an encounter message."""
        world = self.app.world
        actor = self._actor()
        # Secretary is at command_office in the morning; move to corridor then cafeteria
        # First put the actor at cafeteria for the test
        actor.location_key = "cafeteria"
        actor.encounter_location_key = None

        # Move player to corridor, then cafeteria
        self.app.navigation_service.move_player(world, "main_corridor")
        result = self.app.navigation_service.move_player(world, "cafeteria")

        self.assertTrue(any("遇到" in m for m in result.messages))
        self.assertEqual(actor.encounter_location_key, "cafeteria")

    def test_no_encounter_when_already_seen(self) -> None:
        """If actor was already encountered at this location, no repeated encounter."""
        world = self.app.world
        actor = self._actor()
        actor.location_key = "cafeteria"
        actor.encounter_location_key = "cafeteria"  # Already encountered
        for other in world.characters:
            if other.key != actor.key:
                other.location_key = "dock"

        self.app.navigation_service.move_player(world, "main_corridor")
        result = self.app.navigation_service.move_player(world, "cafeteria")

        self.assertFalse(any("遇到" in m for m in result.messages))

    def test_schedule_refresh_clears_encounter(self) -> None:
        """When schedule moves a character, encounter state resets."""
        world = self.app.world
        actor = self._actor()
        actor.encounter_location_key = "command_office"

        # Advance to afternoon — secretary moves to training_ground
        world.current_time_slot = TimeSlot.MORNING
        self.app.game_loop.advance_time(world)  # -> afternoon

        self.assertEqual(actor.location_key, "training_ground")
        self.assertIsNone(actor.encounter_location_key)


if __name__ == "__main__":
    unittest.main()
