"""Tests for milestone A training progression."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key
from tests.support.stages import reset_progress


class TrainingProgressionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        self.actor.location_key = "dormitory_a"
        self.world.active_location.key = "dormitory_a"
        self.world.active_location.display_name = "宿舍A"
        self.world.current_time_slot = TimeSlot.NIGHT
        self.world.current_hour = 20
        self.world.current_minute = 0
        self.app.training_service.start_session(
            self.world,
            actor_key=self.actor.key,
            position_key="standing",
        )

    def test_train_touch_increases_short_term_training_values(self) -> None:
        result = self.app.command_service.execute(
            self.world,
            self.actor.key,
            "train_touch",
        )

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_m"), 0)
        self.assertGreater(self.actor.stats.palam.get("lust"), 0)

    def test_train_insert_v_applies_submission_after_underwear_removed(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)

        result = self.app.command_service.execute(
            self.world,
            self.actor.key,
            "train_insert_v",
        )

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("submission"), 0)
        self.assertGreater(self.actor.stats.palam.get("pleasure_v"), 0)

    def test_train_insert_v_tracks_long_term_v_develop_progress(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)

        self.app.command_service.execute(
            self.world,
            self.actor.key,
            "train_insert_v",
        )

        self.assertGreater(
            self.app.training_service.development_value(self.actor, "v_develop"),
            0,
        )

    def test_training_scene_can_drive_dialogue_branch(self) -> None:
        scene = self.app.scene_service.build_for_actor(
            self.world,
            self.actor,
            "train_touch",
            ("private",),
        )

        lines = self.app.dialogue_service.lines_for(scene, ())

        self.assertTrue(lines)


if __name__ == "__main__":
    unittest.main()
