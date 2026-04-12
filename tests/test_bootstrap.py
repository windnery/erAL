"""Scaffold tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot


class BootstrapTests(unittest.TestCase):
    def test_create_application_uses_default_config(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)

        self.assertEqual(app.config.game_title, "erAL")
        self.assertEqual(app.world.current_time_slot, TimeSlot.MORNING)
        self.assertEqual(app.world.current_day, 1)
        self.assertEqual(app.world.active_location.key, "command_office")
        self.assertEqual(app.port_map.key, "starter_port")
        self.assertEqual(len(app.world.characters), 5)
        secretary = next(actor for actor in app.world.characters if actor.key == "starter_secretary")
        cruiser = next(actor for actor in app.world.characters if actor.key == "starter_cruiser")
        self.assertEqual(secretary.location_key, "command_office")
        self.assertEqual(cruiser.location_key, "cafeteria")
        self.assertFalse(app.world.is_busy)
        self.assertFalse(app.world.is_date_traveling)


if __name__ == "__main__":
    unittest.main()
