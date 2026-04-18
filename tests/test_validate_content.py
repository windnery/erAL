"""Tests for content density reporting."""

from __future__ import annotations

import io
import shutil
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from eral.tools.validate_content import collect_content_stats, main, render_content_report, validate_content


class ValidateContentReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_collect_content_stats_reports_counts_and_gaps(self) -> None:
        stats = collect_content_stats(self.repo_root)
        by_key = {item.character_key: item for item in stats}

        self.assertEqual(by_key["enterprise"].event_count, 31)
        self.assertEqual(by_key["enterprise"].dialogue_count, 62)
        self.assertEqual(by_key["enterprise"].event_gap, 0)
        self.assertEqual(by_key["enterprise"].dialogue_gap, 0)

    def test_render_content_report_includes_summary_lines(self) -> None:
        stats = collect_content_stats(self.repo_root)
        report = render_content_report(stats)

        self.assertIn("content density report:", report)
        self.assertIn("enterprise", report)
        self.assertIn("events=31", report)
        self.assertIn("dialogue=62", report)

    def test_main_prints_content_density_report(self) -> None:
        buf = io.StringIO()
        with patch("sys.argv", ["validate_content"]), redirect_stdout(buf):
            main()

        output = buf.getvalue()
        self.assertIn("content validation ok", output)
        self.assertIn("content density report:", output)
        self.assertIn("enterprise", output)
        self.assertIn("laffey", output)

    def test_validate_content_reports_invalid_global_dialogue_and_event_references(self) -> None:
        temp_root = self.repo_root / "runtime" / f"validate_content_{uuid.uuid4().hex}"
        shutil.copytree(self.repo_root / "data", temp_root / "data")

        (temp_root / "data" / "base" / "dialogue.toml").write_text(
            "\n".join(
                [
                    "[[entries]]",
                    'key = "chat"',
                    'actor_key = "ghost_actor"',
                    'lines = ["不存在角色"]',
                ]
            ),
            encoding="utf-8",
        )
        (temp_root / "data" / "base" / "events.toml").write_text(
            "\n".join(
                [
                    "[[events]]",
                    'key = "ghost_event"',
                    'action_key = "missing_action"',
                    'location_keys = ["missing_location"]',
                ]
            ),
            encoding="utf-8",
        )

        errors = validate_content(temp_root)

        self.assertTrue(any("dialogue 'chat' references unknown actor 'ghost_actor'" in error for error in errors))
        self.assertTrue(any("event 'ghost_event' references unknown action 'missing_action'" in error for error in errors))
        self.assertTrue(any("event 'ghost_event' references unknown location 'missing_location'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
