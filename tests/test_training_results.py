"""Tests for milestone B: result states, extended commands, and development axes."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.training import TrainingResult, TrainingSettlementResult
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key
from tests.support.stages import reset_progress


def _start_training_session(app, actor, world) -> None:
    app.training_service.start_session(
        world,
        actor_key=actor.key,
        position_key="standing",
    )
    private_location = next(
        location for location in app.port_map.locations if "private" in location.tags
    )
    actor.location_key = private_location.key
    world.active_location.key = private_location.key
    world.active_location.display_name = private_location.display_name
    world.current_time_slot = TimeSlot.NIGHT
    world.current_hour = 22
    world.current_minute = 0


class TrainingResultDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_session(self.app, self.actor, self.world)

    def test_detect_results_returns_empty_when_no_threshold_met(self) -> None:
        result = self.app.training_service.detect_results(self.actor)

        self.assertEqual(result.orgasm_count, 0)
        self.assertFalse(result.was_rejected)
        self.assertFalse(result.was_interrupted)
        self.assertEqual(result.results, ())

    def test_detect_orgasm_c_when_palam_c_exceeds_threshold(self) -> None:
        self.actor.stats.palam.set("pleasure_c", 3000)

        result = self.app.training_service.detect_results(self.actor)

        self.assertGreater(result.orgasm_count, 0)
        self.assertIn(TrainingResult.ORGASM_C, result.results)
        self.assertEqual(self.actor.stats.palam.get("pleasure_c"), 0)
        self.assertGreater(self.actor.stats.base.get("pleasure_c_afterglow"), 0)

    def test_detect_multiple_orgasms(self) -> None:
        self.actor.stats.palam.set("pleasure_c", 3000)
        self.actor.stats.palam.set("pleasure_v", 3000)

        result = self.app.training_service.detect_results(self.actor)

        self.assertEqual(result.orgasm_count, 2)
        self.assertIn(TrainingResult.ORGASM_C, result.results)
        self.assertIn(TrainingResult.ORGASM_V, result.results)

    def test_detect_interrupt_when_spirit_depleted(self) -> None:
        self.actor.stats.base.set("spirit", 0)

        result = self.app.training_service.detect_results(self.actor)

        self.assertTrue(result.was_interrupted)
        self.assertIn(TrainingResult.INTERRUPTED, result.results)

    def test_detect_rejection_when_submission_low_vs_lust(self) -> None:
        self.actor.stats.base.set("spirit", 5)
        self.actor.stats.palam.set("lust", 500)
        self.actor.stats.palam.set("submission", 100)
        self.actor.stats.palam.set("obedience", 100)

        result = self.app.training_service.detect_results(self.actor)

        self.assertTrue(result.was_rejected)
        self.assertIn(TrainingResult.REJECTED, result.results)

    def test_no_rejection_when_submission_overcomes_lust(self) -> None:
        self.actor.stats.base.set("spirit", 5)
        self.actor.stats.palam.set("lust", 100)
        self.actor.stats.palam.set("submission", 500)
        self.actor.stats.palam.set("obedience", 500)

        result = self.app.training_service.detect_results(self.actor)

        self.assertFalse(result.was_rejected)

    def test_orgasm_increments_total_orgasm_count_condition(self) -> None:
        self.actor.stats.palam.set("pleasure_b", 5000)

        self.app.training_service.detect_results(self.actor)

        self.assertGreater(self.actor.get_condition("total_orgasm_count"), 0)

    def test_orgasm_increments_afterglow_base(self) -> None:
        self.actor.stats.palam.set("pleasure_m", 2500)

        self.app.training_service.detect_results(self.actor)

        self.assertGreater(self.actor.stats.base.get("orgasm_afterglow"), 0)


class ExtendedTrainingCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_session(self.app, self.actor, self.world)

    def test_train_breast_touch_increases_pleasure_b(self) -> None:
        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_breast_touch",
        )

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_b"), 0)

    def test_train_c_touch_increases_pleasure_c(self) -> None:
        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_c_touch",
        )

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_c"), 0)

    def test_train_hand_increases_give_pleasure_c(self) -> None:
        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_hand",
        )

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_c"), 0)

    def test_train_oral_increases_submission(self) -> None:
        self.actor.set_condition("train_hand_develop", 5)

        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_oral",
        )

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("submission"), 0)

    def test_end_training_exits_training_mode(self) -> None:
        result = self.app.command_service.execute(
            self.world, self.actor.key, "end_training",
        )

        self.assertTrue(result.success)
        self.assertFalse(self.world.training_active)

    def test_training_step_index_increments_per_command(self) -> None:
        self.assertEqual(self.world.training_step_index, 0)

        self.app.command_service.execute(self.world, self.actor.key, "train_touch")
        self.assertEqual(self.world.training_step_index, 1)

        self.app.command_service.execute(self.world, self.actor.key, "train_touch")
        self.assertEqual(self.world.training_step_index, 2)


class TrainingDevelopmentAxesTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_session(self.app, self.actor, self.world)

    def test_train_breast_touch_tracks_b_develop(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "train_breast_touch")

        self.assertGreater(
            self.app.training_service.development_value(self.actor, "b_develop"), 0,
        )

    def test_train_c_touch_tracks_c_develop(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "train_c_touch")

        self.assertGreater(
            self.app.training_service.development_value(self.actor, "c_develop"), 0,
        )

    def test_train_hand_tracks_hand_develop(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "train_hand")

        self.assertGreater(
            self.app.training_service.development_value(self.actor, "hand_develop"), 0,
        )

    def test_train_oral_tracks_oral_and_service_develop(self) -> None:
        self.actor.set_condition("train_hand_develop", 5)

        self.app.command_service.execute(self.world, self.actor.key, "train_oral")

        self.assertGreater(
            self.app.training_service.development_value(self.actor, "oral_develop"), 0,
        )
        self.assertGreater(
            self.app.training_service.development_value(self.actor, "service_develop"), 0,
        )

    def test_total_steps_condition_increments(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "train_touch")
        self.app.command_service.execute(self.world, self.actor.key, "train_breast_touch")

        self.assertEqual(self.actor.get_condition("train_total_steps"), 2)

    def test_add_development_method(self) -> None:
        self.app.training_service.add_development(self.actor, "v_develop", 5)

        self.assertEqual(
            self.app.training_service.development_value(self.actor, "v_develop"), 5,
        )


class TrainingResultDialogueTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_session(self.app, self.actor, self.world)

    def test_orgasm_result_tag_appears_in_triggered_events(self) -> None:
        self.actor.stats.palam.set("pleasure_c", 5000)

        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_c_touch",
        )

        self.assertIn("orgasm_c", result.triggered_events)

    def test_scene_context_carries_training_results(self) -> None:
        self.actor.stats.palam.set("pleasure_b", 5000)
        self.app.command_service.execute(self.world, self.actor.key, "train_breast_touch")

        scene = self.app.scene_service.build_for_actor(
            self.world, self.actor, "train_breast_touch", ("private",),
        )

        self.assertIn("orgasm_b", scene.training_results)

    def test_training_result_fallback_dialogue_exists(self) -> None:
        from eral.content.dialogue import load_dialogue_entries

        entries = load_dialogue_entries(
            self.app.root / "data" / "base" / "dialogue.toml",
        )
        result_keys = {"orgasm_c", "orgasm_v", "orgasm_b", "orgasm_m", "rejected", "interrupted"}
        entry_keys = {e.key for e in entries}
        for key in result_keys:
            self.assertIn(key, entry_keys, f"Missing dialogue entry for {key}")


class DevelopmentGateTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_session(self.app, self.actor, self.world)

    def test_train_oral_blocked_without_hand_develop(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.world, self.actor.key, "train_oral")
        self.assertIn("手技开发度不足", str(ctx.exception))

    def test_train_oral_unlocked_with_hand_develop_5(self) -> None:
        self.actor.set_condition("train_hand_develop", 5)

        result = self.app.command_service.execute(self.world, self.actor.key, "train_oral")

        self.assertTrue(result.success)

    def test_train_insert_a_blocked_without_c_develop(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        self.actor.set_condition("train_v_develop", 5)

        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.world, self.actor.key, "train_insert_a")
        self.assertIn("C开发度不足", str(ctx.exception))

    def test_train_insert_a_blocked_without_v_develop(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        self.actor.set_condition("train_c_develop", 10)

        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.world, self.actor.key, "train_insert_a")
        self.assertIn("V开发度不足", str(ctx.exception))

    def test_train_insert_a_unlocked_with_both_develop(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        self.actor.set_condition("train_c_develop", 10)
        self.actor.set_condition("train_v_develop", 5)

        result = self.app.command_service.execute(self.world, self.actor.key, "train_insert_a")

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_a"), 0)

    def test_train_insert_a_tracks_a_develop(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        self.actor.set_condition("train_c_develop", 10)
        self.actor.set_condition("train_v_develop", 5)

        self.app.command_service.execute(self.world, self.actor.key, "train_insert_a")

        self.assertGreater(
            self.app.training_service.development_value(self.actor, "a_develop"), 0,
        )

    def test_train_deep_oral_blocked_without_oral_develop(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.world, self.actor.key, "train_deep_oral")
        self.assertIn("口技开发度不足", str(ctx.exception))

    def test_train_deep_oral_unlocked_with_oral_develop_10(self) -> None:
        self.actor.set_condition("train_oral_develop", 10)

        result = self.app.command_service.execute(self.world, self.actor.key, "train_deep_oral")

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_c"), 0)


class PositionSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_session(self.app, self.actor, self.world)

    def test_default_position_is_standing(self) -> None:
        self.assertEqual(self.world.training_position_key, "standing")

    def test_change_to_missionary(self) -> None:
        result = self.app.command_service.execute(
            self.world, self.actor.key, "change_position_missionary",
        )
        self.assertTrue(result.success)
        self.assertEqual(self.world.training_position_key, "missionary")

    def test_change_to_behind(self) -> None:
        result = self.app.command_service.execute(
            self.world, self.actor.key, "change_position_behind",
        )
        self.assertTrue(result.success)
        self.assertEqual(self.world.training_position_key, "from_behind")

    def test_change_back_to_standing(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "change_position_behind")
        self.app.command_service.execute(self.world, self.actor.key, "change_position_standing")
        self.assertEqual(self.world.training_position_key, "standing")

    def test_missionary_insert_blocked_in_standing(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        self.assertEqual(self.world.training_position_key, "standing")

        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(
                self.world, self.actor.key, "train_insert_v_missionary",
            )
        self.assertIn("体位", str(ctx.exception))

    def test_missionary_insert_works_in_missionary(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        self.app.command_service.execute(self.world, self.actor.key, "change_position_missionary")

        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_insert_v_missionary",
        )

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_b"), 0)

    def test_behind_insert_works_in_from_behind(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        self.app.command_service.execute(self.world, self.actor.key, "change_position_behind")

        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_insert_v_behind",
        )

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_b"), 0)

    def test_position_variant_tracks_v_develop(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        self.app.command_service.execute(self.world, self.actor.key, "change_position_missionary")
        self.app.command_service.execute(self.world, self.actor.key, "train_insert_v_missionary")

        self.assertGreater(
            self.app.training_service.development_value(self.actor, "v_develop"), 0,
        )


class ServiceRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_session(self.app, self.actor, self.world)

    def test_service_hand_blocked_without_obedience(self) -> None:
        self.actor.stats.compat.cflag.set(6, 50)
        self.actor.sync_derived_fields()

        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.world, self.actor.key, "train_service_hand")
        self.assertIn("服从不足", str(ctx.exception))

    def test_service_hand_unlocked_with_obedience(self) -> None:
        self.actor.stats.compat.cflag.set(6, 250)
        self.actor.sync_derived_fields()

        result = self.app.command_service.execute(self.world, self.actor.key, "train_service_hand")

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_c"), 0)

    def test_service_hand_tracks_service_develop(self) -> None:
        self.actor.stats.compat.cflag.set(6, 250)
        self.actor.sync_derived_fields()

        self.app.command_service.execute(self.world, self.actor.key, "train_service_hand")

        self.assertGreater(
            self.app.training_service.development_value(self.actor, "service_develop"), 0,
        )

    def test_service_oral_blocked_without_service_develop(self) -> None:
        self.actor.stats.compat.cflag.set(6, 450)
        self.actor.sync_derived_fields()

        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.world, self.actor.key, "train_service_oral")
        self.assertIn("奉仕开发度不足", str(ctx.exception))

    def test_service_oral_unlocked_with_both(self) -> None:
        self.actor.stats.compat.cflag.set(6, 450)
        self.actor.sync_derived_fields()
        self.actor.set_condition("train_service_develop", 5)

        result = self.app.command_service.execute(self.world, self.actor.key, "train_service_oral")

        self.assertTrue(result.success)

    def test_paizu_blocked_without_top_removed(self) -> None:
        self.actor.stats.compat.cflag.set(6, 450)
        self.actor.sync_derived_fields()
        self.actor.set_condition("train_b_develop", 10)

        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.world, self.actor.key, "train_paizu")
        self.assertIn("服装条件不足", str(ctx.exception))

    def test_paizu_unlocked_with_all_conditions(self) -> None:
        self.actor.stats.compat.cflag.set(6, 450)
        self.actor.sync_derived_fields()
        self.actor.set_condition("train_b_develop", 10)
        self.app.command_service.execute(self.world, self.actor.key, "remove_top")

        result = self.app.command_service.execute(self.world, self.actor.key, "train_paizu")

        self.assertTrue(result.success)
        self.assertGreater(self.actor.stats.palam.get("pleasure_c"), 0)

    def test_remove_top_adds_top_slot(self) -> None:
        self.app.command_service.execute(self.world, self.actor.key, "remove_top")

        self.assertIn("top", self.actor.removed_slots)


if __name__ == "__main__":
    unittest.main()
