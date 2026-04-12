"""Save/load tests for the runtime quicksave flow."""

from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.ui.cli import _build_menu


class SaveLoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(self.repo_root)
        temp_saves = self.app.paths.runtime / f"test_saves_{uuid.uuid4().hex}"
        temp_saves.mkdir(parents=True, exist_ok=True)
        self.app.paths.saves = temp_saves

    def test_quicksave_writes_json_file(self) -> None:
        actor = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="chat",
        )

        save_path = self.app.save_service.save_world(self.app.world)

        self.assertTrue(save_path.exists())
        payload = json.loads(save_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["current_day"], 1)
        self.assertEqual(payload["active_location"]["key"], "command_office")

    def test_load_restores_world_state(self) -> None:
        actor = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="chat",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.save_service.save_world(self.app.world)

        actor.affection = 99
        actor.trust = 99
        actor.location_key = "dock"
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"

        restored = self.app.save_service.load_world()
        self.app.relationship_service.refresh_world(restored)
        self.app.companion_service.refresh_world(restored)
        self.app.date_service.refresh_world(restored)

        restored_actor = next(actor for actor in restored.characters if actor.key == "starter_secretary")
        self.assertEqual(restored.active_location.key, "main_corridor")
        self.assertEqual(restored_actor.location_key, "main_corridor")
        self.assertEqual(restored_actor.affection, 3)
        self.assertEqual(restored_actor.trust, 2)
        self.assertTrue(restored_actor.is_following)

    def test_cli_menu_includes_save_and_load_when_save_exists(self) -> None:
        menu = _build_menu(self.app, self.app.world)
        action_types = [item[1] for item in menu]
        self.assertIn("save", action_types)
        self.assertNotIn("load", action_types)

        self.app.save_service.save_world(self.app.world)
        menu = _build_menu(self.app, self.app.world)
        action_types = [item[1] for item in menu]
        self.assertIn("save", action_types)
        self.assertIn("load", action_types)


    def test_load_restores_enterprise_and_laffey_seeded_stats(self) -> None:
        enterprise = next(actor for actor in self.app.world.characters if actor.key == "enterprise")
        laffey = next(actor for actor in self.app.world.characters if actor.key == "laffey")

        self.app.save_service.save_world(self.app.world)

        enterprise.stats.base.set("stamina", 1)
        enterprise.stats.compat.cflag.set(2, 0)
        enterprise.marks["confessed"] = 0
        laffey.stats.palam.set("favor", 0)
        laffey.stats.compat.cflag.set(2, 0)
        laffey.marks["kissed"] = 0

        restored = self.app.save_service.load_world()
        restored_enterprise = next(actor for actor in restored.characters if actor.key == "enterprise")
        restored_laffey = next(actor for actor in restored.characters if actor.key == "laffey")

        self.assertEqual(restored_enterprise.stats.base.get("stamina"), 1200)
        self.assertEqual(restored_enterprise.stats.compat.cflag.get(2), 4)
        self.assertEqual(restored_enterprise.marks["confessed"], 1)
        self.assertEqual(restored_laffey.stats.palam.get("favor"), 2)
        self.assertEqual(restored_laffey.stats.compat.cflag.get(2), 3)
        self.assertEqual(restored_laffey.marks["kissed"], 1)


if __name__ == "__main__":
    unittest.main()
