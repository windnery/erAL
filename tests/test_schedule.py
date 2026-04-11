"""Schedule refresh tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application


class ScheduleTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def test_time_advance_refreshes_character_location(self) -> None:
        actor = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")
        self.assertEqual(actor.location_key, "command_office")

        self.app.game_loop.advance_time(self.app.world)
        self.assertEqual(self.app.world.current_time_slot.value, "afternoon")
        self.assertEqual(actor.location_key, "training_ground")

        self.app.game_loop.advance_time(self.app.world)
        self.assertEqual(self.app.world.current_time_slot.value, "evening")
        self.assertEqual(actor.location_key, "cafeteria")


if __name__ == "__main__":
    unittest.main()
