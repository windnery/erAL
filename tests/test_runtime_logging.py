"""Runtime logging tests for key gameplay chains."""

from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from eral.app.bootstrap import create_application
from tests.support.real_actors import actor_by_key, place_player_with_actor, reset_progress


class RuntimeLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        temp_logs = self.app.paths.runtime / f"test_logs_{uuid.uuid4().hex}"
        temp_logs.mkdir(parents=True, exist_ok=True)
        self.app.paths.logs = temp_logs
        self.app.runtime_logger.paths = self.app.paths

    def _read_entries(self) -> list[dict]:
        log_path = self.app.runtime_logger.log_path()
        if not log_path.exists():
            return []
        return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_command_success_writes_log_entry(self) -> None:
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        place_player_with_actor(self.app, actor)

        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="chat",
        )

        entries = self._read_entries()
        self.assertTrue(entries)
        entry = entries[-1]
        self.assertEqual(entry["kind"], "command")
        self.assertEqual(entry["action_key"], "chat")
        self.assertEqual(entry["actor_key"], "enterprise")
        self.assertEqual(entry["day"], 1)
        self.assertEqual(entry["time_slot"], "morning")
        self.assertIn("triggered_events", entry)

    def test_command_failure_writes_reason(self) -> None:
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.NIGHT
        self.app.world.active_location.key = "bathhouse"
        self.app.world.active_location.display_name = "浴场"
        actor.location_key = "bathhouse"

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="tease",
            )

        entries = self._read_entries()
        self.assertTrue(entries)
        entry = entries[-1]
        self.assertEqual(entry["kind"], "command_failed")
        self.assertEqual(entry["action_key"], "tease")
        self.assertEqual(entry["actor_key"], "enterprise")
        self.assertIn("reason", entry)
        self.assertIn("好感", entry["reason"])

    def test_move_and_time_advance_write_log_entries(self) -> None:
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.game_loop.advance_time(self.app.world)

        entries = self._read_entries()
        kinds = [entry["kind"] for entry in entries]
        self.assertIn("move", kinds)
        self.assertIn("time_advanced", kinds)

    def test_save_writes_log_entry(self) -> None:
        self.app.save_service.save_world(self.app.world)

        entries = self._read_entries()
        self.assertTrue(entries)
        entry = entries[-1]
        self.assertEqual(entry["kind"], "save")
        self.assertEqual(entry["day"], 1)
        self.assertEqual(entry["time_slot"], "morning")


if __name__ == "__main__":
    unittest.main()
