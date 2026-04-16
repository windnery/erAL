"""Save/load tests for the runtime quicksave flow."""

from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.ui.cli import _build_menu
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress


class SaveLoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(self.repo_root)
        temp_saves = self.app.paths.runtime / f"test_saves_{uuid.uuid4().hex}"
        temp_saves.mkdir(parents=True, exist_ok=True)
        self.app.paths.saves = temp_saves

    def test_quicksave_writes_json_file(self) -> None:
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        place_player_with_actor(self.app, actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="chat",
        )
        self.app.world.inventory["medkit"] = 3

        save_path = self.app.save_service.save_world(self.app.world)

        self.assertTrue(save_path.exists())
        payload = json.loads(save_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["current_day"], 1)
        self.assertEqual(payload["active_location"]["key"], "dock")
        self.assertEqual(payload["inventory"], {"medkit": 3})

    def test_load_restores_world_state(self) -> None:
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        place_player_with_actor(self.app, actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="chat",
        )
        actor.stats.compat.cflag.set(2, 210)
        actor.stats.compat.cflag.set(4, 110)
        actor.sync_derived_fields()
        self.app.relationship_service.update_actor(actor)
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

        restored_actor = next(actor for actor in restored.characters if actor.key == "enterprise")
        self.assertEqual(restored.active_location.key, "main_corridor")
        self.assertEqual(restored_actor.location_key, "main_corridor")
        self.assertGreaterEqual(restored_actor.affection, 210)
        self.assertGreaterEqual(restored_actor.trust, 110)
        self.assertTrue(restored_actor.is_following)

    def test_load_restores_inventory_counts(self) -> None:
        self.app.world.inventory["medkit"] = 3
        self.app.world.inventory["coin"] = 12

        self.app.save_service.save_world(self.app.world)

        self.app.world.inventory.clear()

        restored = self.app.save_service.load_world()

        self.assertEqual(restored.inventory, {"medkit": 3, "coin": 12})

    def test_load_refresh_preserves_oath_mark_stage_override(self) -> None:
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        place_player_with_actor(self.app, actor)
        actor.marks["oath"] = 1
        self.app.relationship_service.update_actor(actor)
        self.assertEqual(actor.relationship_stage.key, "oath")

        self.app.save_service.save_world(self.app.world)

        actor.marks.pop("oath", None)
        self.app.relationship_service.update_actor(actor)

        restored = self.app.save_service.load_world()
        self.app.relationship_service.refresh_world(restored)

        restored_actor = next(actor for actor in restored.characters if actor.key == "enterprise")
        self.assertTrue(restored_actor.has_mark("oath"))
        self.assertEqual(restored_actor.relationship_stage.key, "oath")

    def test_load_older_save_defaults_inventory_to_empty_dict(self) -> None:
        self.app.save_service.save_world(self.app.world)
        save_path = self.app.save_service.quicksave_path()
        payload = json.loads(save_path.read_text(encoding="utf-8"))
        payload.pop("inventory", None)
        save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        restored = self.app.save_service.load_world()

        self.assertEqual(restored.inventory, {})

    def test_load_ignores_non_dict_inventory_payload(self) -> None:
        self.app.save_service.save_world(self.app.world)
        save_path = self.app.save_service.quicksave_path()
        payload = json.loads(save_path.read_text(encoding="utf-8"))
        payload["inventory"] = ["medkit", 3]
        save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        restored = self.app.save_service.load_world()

        self.assertEqual(restored.inventory, {})

    def test_load_ignores_invalid_inventory_counts(self) -> None:
        self.app.save_service.save_world(self.app.world)
        save_path = self.app.save_service.quicksave_path()
        payload = json.loads(save_path.read_text(encoding="utf-8"))
        payload["inventory"] = {
            "medkit": 3,
            "broken": "not-a-number",
            "empty": 0,
            "negative": -2,
        }
        save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        restored = self.app.save_service.load_world()

        self.assertEqual(restored.inventory, {"medkit": 3})

    def test_worldstate_inventory_helpers(self) -> None:
        world = self.app.world

        self.assertEqual(world.item_count("medkit"), 0)
        self.assertEqual(world.add_item("medkit"), 1)
        self.assertEqual(world.add_item("medkit", 2), 3)
        self.assertEqual(world.item_count("medkit"), 3)
        self.assertTrue(world.consume_item("medkit"))
        self.assertEqual(world.item_count("medkit"), 2)
        self.assertFalse(world.consume_item("medkit", 3))
        self.assertEqual(world.item_count("medkit"), 2)
        self.assertTrue(world.consume_item("medkit", 2))
        self.assertEqual(world.item_count("medkit"), 0)
        self.assertFalse(world.consume_item("medkit"))
        self.assertEqual(world.add_item("medkit", 0), 0)
        self.assertEqual(world.add_item("medkit", -1), 0)
        self.assertTrue(world.consume_item("medkit", 0))

    def test_cli_menu_includes_save_and_load_when_save_exists(self) -> None:
        menu = _build_menu(self.app, self.app.world)
        action_types = [item[1] for items in menu.values() for item in items]
        self.assertIn("save", action_types)
        self.assertNotIn("load", action_types)

        self.app.save_service.save_world(self.app.world)
        menu = _build_menu(self.app, self.app.world)
        action_types = [item[1] for items in menu.values() for item in items]
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
        self.assertEqual(restored_enterprise.stats.compat.cflag.get(2), 310)
        self.assertEqual(restored_enterprise.marks["confessed"], 1)
        self.assertEqual(restored_laffey.stats.palam.get("favor"), 2)
        self.assertEqual(restored_laffey.stats.compat.cflag.get(2), 310)
        self.assertEqual(restored_laffey.marks["kissed"], 1)


if __name__ == "__main__":
    unittest.main()
