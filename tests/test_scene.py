"""SceneService unit tests."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.systems.scene import SceneService
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress


@dataclass(frozen=True, slots=True)
class _FakeSkin:
    tags: tuple[str, ...]


class _FakeSkinService:
    def __init__(self) -> None:
        self.skin_definitions = {
            "test_skin": _FakeSkin(tags=("cute", "white")),
        }


class SceneServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)
        self.world.current_month = 7
        self.world.season_month_map = {7: "summer"}
        self.world.weather_key = "rain"

    def test_build_scene_reflects_core_actor_and_world_state(self) -> None:
        self.actor.affection = 12
        self.actor.trust = 34
        self.actor.obedience = 56
        self.actor.removed_slots = ("underwear_bottom",)
        self.actor.marks["soft"] = 1

        scene = self.app.scene_service.build_for_actor(
            self.world,
            self.actor,
            action_key="chat",
            location_tags=("public",),
        )

        self.assertEqual(scene.actor_key, self.actor.key)
        self.assertEqual(scene.actor_tags, self.actor.tags)
        self.assertEqual(scene.current_day, self.world.current_day)
        self.assertEqual(scene.time_slot, self.world.current_time_slot.value)
        self.assertEqual(scene.location_key, self.world.active_location.key)
        self.assertEqual(scene.location_tags, ("public",))
        self.assertEqual(scene.affection, 12)
        self.assertEqual(scene.trust, 34)
        self.assertEqual(scene.obedience, 56)
        self.assertEqual(scene.relationship_stage, "stranger")
        self.assertEqual(scene.relationship_rank, 0)
        self.assertEqual(scene.season, "summer")
        self.assertEqual(scene.weather_key, "rain")
        self.assertEqual(scene.removed_slots, ("underwear_bottom",))
        self.assertEqual(scene.marks, {"soft": 1})
        self.assertEqual(scene.memories, {})

    def test_build_scene_marks_private_space_from_visible_characters(self) -> None:
        second_actor = actor_by_key(self.app, "laffey")
        reset_progress(second_actor)
        second_actor.location_key = self.actor.location_key

        scene = self.app.scene_service.build_for_actor(
            self.world,
            self.actor,
            action_key="chat",
            location_tags=("public",),
        )

        self.assertEqual(scene.visible_count, 2)
        self.assertFalse(scene.is_private)

    def test_build_scene_includes_training_state(self) -> None:
        self.world.training_active = True
        self.world.training_actor_key = self.actor.key
        self.world.training_position_key = "bridge"
        self.world.training_step_index = 4
        self.world.training_flags["last_results"] = "orgasm_b,rejected"

        scene = self.app.scene_service.build_for_actor(
            self.world,
            self.actor,
            action_key="train_breast_touch",
            location_tags=("private",),
        )

        self.assertTrue(scene.is_training)
        self.assertEqual(scene.training_position_key, "bridge")
        self.assertEqual(scene.training_results, ("orgasm_b", "rejected"))
        self.assertEqual(scene.training_step_index, 4)

    def test_build_scene_uses_skin_tags_and_copies_mutable_state(self) -> None:
        self.actor.equipped_skin_key = "test_skin"
        self.actor.marks["intro"] = 1
        self.actor.memories["meeting"] = 2
        service = SceneService(skin_service=_FakeSkinService())

        scene = service.build_for_actor(
            self.world,
            self.actor,
            action_key="chat",
            location_tags=("public",),
        )

        self.actor.marks["intro"] = 3
        self.actor.memories["meeting"] = 4

        self.assertEqual(scene.equipped_skin_key, "test_skin")
        self.assertEqual(scene.equipped_skin_tags, ("cute", "white"))
        self.assertEqual(scene.marks, {"intro": 1})
        self.assertEqual(scene.memories, {"meeting": 2})


if __name__ == "__main__":
    unittest.main()
