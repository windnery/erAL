"""Tests for the memory and unlock tracking system."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key
from tests.support.stages import reset_progress


def _setup_training(app, actor, world) -> None:
    app.training_service.start_session(world, actor.key, "standing")
    private_location = next(l for l in app.port_map.locations if "private" in l.tags)
    actor.location_key = private_location.key
    world.active_location.key = private_location.key
    world.active_location.display_name = private_location.display_name
    world.current_time_slot = TimeSlot.NIGHT


class MemoryDomainTests(unittest.TestCase):
    def test_record_memory_increments(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)

        self.assertEqual(actor.record_memory("kiss"), 1)
        self.assertEqual(actor.record_memory("kiss"), 2)
        self.assertEqual(actor.memories["kiss"], 2)

    def test_has_memory_checks_count(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)

        self.assertFalse(actor.has_memory("kiss"))
        self.assertFalse(actor.has_memory("kiss", 1))
        actor.record_memory("kiss")
        self.assertTrue(actor.has_memory("kiss", 1))
        self.assertFalse(actor.has_memory("kiss", 2))

    def test_memories_default_empty(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        self.assertEqual(actor.memories, {})


class MemoryCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _setup_training(self.app, self.actor, self.world)

    def test_command_records_memory(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "train_touch")
        self.assertEqual(self.actor.memories.get("cmd:train_touch"), 1)

    def test_repeated_command_increments_memory(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "train_touch")
        self.app.command_service.execute(self.world, self.actor.key, "train_touch")
        self.assertEqual(self.actor.memories.get("cmd:train_touch"), 2)

    def test_different_commands_track_separately(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "train_touch")
        self.app.command_service.execute(self.world, self.actor.key, "train_breast_touch")
        self.assertEqual(self.actor.memories.get("cmd:train_touch"), 1)
        self.assertEqual(self.actor.memories.get("cmd:train_breast_touch"), 1)


class MemorySceneContextTests(unittest.TestCase):
    def test_scene_context_carries_memories(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        world = app.world
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.record_memory("test_memory")

        scene = app.scene_service.build_for_actor(world, actor, "talk", ("public",))
        self.assertEqual(scene.memories.get("test_memory"), 1)


if __name__ == "__main__":
    unittest.main()
