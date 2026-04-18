"""Training session runtime state tests."""

from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from eral.app.bootstrap import create_application


class TrainingSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(self.repo_root)
        temp_saves = self.app.paths.runtime / f"training_saves_{uuid.uuid4().hex}"
        temp_saves.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, temp_saves, True)
        self.app.paths.saves = temp_saves

    def test_worldstate_can_start_and_end_training_session_by_setting_fields(self) -> None:
        world = self.app.world

        self.assertFalse(world.training_active)
        self.assertIsNone(world.training_actor_key)
        self.assertIsNone(world.training_position_key)
        self.assertEqual(world.training_step_index, 0)
        self.assertEqual(world.training_flags, {})

        world.training_active = True
        world.training_actor_key = "enterprise"
        world.training_position_key = "bridge"
        world.training_step_index = 2
        world.training_flags = {"intro_seen": 1, "reward_claimed": 0}

        self.assertTrue(world.training_active)
        self.assertEqual(world.training_actor_key, "enterprise")
        self.assertEqual(world.training_position_key, "bridge")
        self.assertEqual(world.training_step_index, 2)
        self.assertEqual(
            world.training_flags,
            {"intro_seen": 1, "reward_claimed": 0},
        )

        world.training_active = False
        world.training_actor_key = None
        world.training_position_key = None
        world.training_step_index = 0
        world.training_flags = {}

        self.assertFalse(world.training_active)
        self.assertIsNone(world.training_actor_key)
        self.assertIsNone(world.training_position_key)
        self.assertEqual(world.training_step_index, 0)
        self.assertEqual(world.training_flags, {})

    def test_save_and_load_roundtrips_training_session_state(self) -> None:
        world = self.app.world
        world.training_active = True
        world.training_actor_key = "enterprise"
        world.training_position_key = "bridge"
        world.training_step_index = 3
        world.training_flags = {"intro_seen": 1, "branch_index": 2}

        self.app.save_service.save_world(world)

        restored = self.app.save_service.load_world()

        self.assertTrue(restored.training_active)
        self.assertEqual(restored.training_actor_key, "enterprise")
        self.assertEqual(restored.training_position_key, "bridge")
        self.assertEqual(restored.training_step_index, 3)
        self.assertEqual(
            restored.training_flags,
            {"intro_seen": 1, "branch_index": 2},
        )

    def test_load_older_save_defaults_training_session_state(self) -> None:
        self.app.save_service.save_world(self.app.world)
        save_path = self.app.save_service.quicksave_path()
        payload = json.loads(save_path.read_text(encoding="utf-8"))
        payload.pop("training_active", None)
        payload.pop("training_actor_key", None)
        payload.pop("training_position_key", None)
        payload.pop("training_step_index", None)
        payload.pop("training_flags", None)
        save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        restored = self.app.save_service.load_world()

        self.assertFalse(restored.training_active)
        self.assertIsNone(restored.training_actor_key)
        self.assertIsNone(restored.training_position_key)
        self.assertEqual(restored.training_step_index, 0)
        self.assertEqual(restored.training_flags, {})

    def test_training_service_start_and_end_session_updates_world_state(self) -> None:
        world = self.app.world

        self.app.training_service.start_session(
            world,
            actor_key="enterprise",
            position_key="bridge",
        )

        self.assertTrue(world.training_active)
        self.assertEqual(world.training_actor_key, "enterprise")
        self.assertEqual(world.training_position_key, "bridge")
        self.assertEqual(world.training_step_index, 0)
        self.assertEqual(world.training_flags, {})

        self.app.training_service.end_session(world)

        self.assertFalse(world.training_active)
        self.assertIsNone(world.training_actor_key)
        self.assertIsNone(world.training_position_key)
        self.assertEqual(world.training_step_index, 0)
        self.assertEqual(world.training_flags, {})

    def test_scene_context_exposes_training_state(self) -> None:
        actor = self.app.world.characters[0]

        self.app.training_service.start_session(
            self.app.world,
            actor_key=actor.key,
            position_key="bridge",
        )

        scene = self.app.scene_service.build_for_actor(
            self.app.world,
            actor,
            action_key="train_together",
            location_tags=(),
        )

        self.assertTrue(scene.is_training)
        self.assertEqual(scene.training_position_key, "bridge")


if __name__ == "__main__":
    unittest.main()
