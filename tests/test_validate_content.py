"""Tests for content density reporting."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from eral.tools.validate_content import collect_content_stats, main, render_content_report


class ValidateContentReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_collect_content_stats_reports_counts_and_gaps(self) -> None:
        stats = collect_content_stats(self.repo_root)
        by_key = {item.character_key: item for item in stats}

        self.assertEqual(by_key["enterprise"].event_count, 30)
        self.assertEqual(by_key["enterprise"].dialogue_count, 58)
        self.assertEqual(by_key["enterprise"].event_gap, 0)
        self.assertEqual(by_key["enterprise"].dialogue_gap, 0)

    def test_render_content_report_includes_summary_lines(self) -> None:
        stats = collect_content_stats(self.repo_root)
        report = render_content_report(stats)

        self.assertIn("content density report:", report)
        self.assertIn("enterprise", report)
        self.assertIn("events=30", report)
        self.assertIn("dialogue=58", report)

    def test_main_prints_content_density_report(self) -> None:
        buf = io.StringIO()
        with patch("sys.argv", ["validate_content"]), redirect_stdout(buf):
            main()

        output = buf.getvalue()
        self.assertIn("content validation ok", output)
        self.assertIn("content density report:", output)
        self.assertIn("enterprise", output)
        self.assertIn("laffey", output)


if __name__ == "__main__":
    unittest.main()
