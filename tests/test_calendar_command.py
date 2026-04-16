"""Tests for the read-only calendar command."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.ui.cli import _render_calendar_preview


class CalendarCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def test_calendar_preview_includes_today_and_adjacent_days(self) -> None:
        lines = _render_calendar_preview(self.app, self.app.world)
        joined = "\n".join(lines)

        self.assertIn("前后2天", joined)
        self.assertIn("1月1日", joined)
        self.assertIn("1月2日", joined)

    def test_calendar_preview_includes_festival_and_work_schedule(self) -> None:
        self.app.world.current_month = 6
        self.app.world.current_day = 21
        self.app.world.current_weekday = "sat"
        self.app.world.current_hour = 10
        self.app.world.current_minute = 0
        lines = _render_calendar_preview(self.app, self.app.world)
        joined = "\n".join(lines)

        self.assertIn("夏日祭", joined)
        self.assertIn("夏季巡逻", joined)


if __name__ == "__main__":
    unittest.main()
