"""Tests for real date and clock state."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application


class TimeSystemStateTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world

    def test_world_bootstrap_uses_real_date_and_clock_defaults(self) -> None:
        self.assertEqual(self.world.current_year, 1)
        self.assertEqual(self.world.current_month, 1)
        self.assertEqual(self.world.current_day, 1)
        self.assertEqual(self.world.current_weekday, "mon")
        self.assertEqual(self.world.current_hour, 8)
        self.assertEqual(self.world.current_minute, 0)
        self.assertEqual(self.world.current_time_slot.value, "morning")

    def test_advance_minutes_rolls_hour(self) -> None:
        self.world.current_hour = 8
        self.world.current_minute = 50

        self.app.time_service.advance_minutes(self.world, 15)

        self.assertEqual((self.world.current_hour, self.world.current_minute), (9, 5))

    def test_advance_minutes_rolls_day_and_weekday(self) -> None:
        self.world.current_month = 1
        self.world.current_day = 31
        self.world.current_weekday = "mon"
        self.world.current_hour = 23
        self.world.current_minute = 50

        self.app.time_service.advance_minutes(self.world, 15)

        self.assertEqual(self.world.current_month, 2)
        self.assertEqual(self.world.current_day, 1)
        self.assertEqual(self.world.current_weekday, "tue")
        self.assertEqual((self.world.current_hour, self.world.current_minute), (0, 5))


if __name__ == "__main__":
    unittest.main()
