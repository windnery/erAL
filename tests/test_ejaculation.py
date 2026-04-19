"""Tests for player ejaculation and character fluid response."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from eral.systems.ejaculation import (
    AROUSAL_KEY,
    EJACULATE_INSIDE_KEY,
    TAG_EJACULATION_INSIDE,
    TAG_EJACULATION_OUTSIDE,
)
from tests.support.real_actors import actor_by_key
from tests.support.stages import reset_progress


def _start_training_in_private(app, actor, world) -> None:
    app.training_service.start_session(
        world, actor_key=actor.key, position_key="standing"
    )
    private_location = next(
        loc for loc in app.port_map.locations if "private" in loc.tags
    )
    actor.location_key = private_location.key
    world.active_location.key = private_location.key
    world.active_location.display_name = private_location.display_name
    world.current_time_slot = TimeSlot.NIGHT
    world.current_hour = 22
    world.current_minute = 0


class EjaculationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_in_private(self.app, self.actor, self.world)
        self.ejaculation = self.app.ejaculation_service

    def test_accumulate_only_when_inserted(self) -> None:
        self.ejaculation.accumulate(self.world, self.actor, gain=50)
        self.assertEqual(self.ejaculation.get_arousal(self.world), 0)

        self.actor.active_persistent_states.add("inserted_v")
        self.ejaculation.accumulate(self.world, self.actor, gain=50)
        self.assertEqual(self.ejaculation.get_arousal(self.world), 50)

    def test_check_and_fire_inside_emits_tag_and_adds_fluid(self) -> None:
        self.actor.active_persistent_states.add("inserted_v")
        self.world.conditions[AROUSAL_KEY] = 120  # >= threshold 100
        before_fluid = self.actor.stats.source.get("fluid")

        tag = self.ejaculation.check_and_fire(self.world, self.actor)
        self.assertEqual(tag, TAG_EJACULATION_INSIDE)
        self.assertEqual(self.ejaculation.get_arousal(self.world), 0)
        self.assertGreater(self.actor.stats.source.get("fluid"), before_fluid)

    def test_check_and_fire_outside_when_toggled(self) -> None:
        self.actor.active_persistent_states.add("inserted_v")
        self.ejaculation.set_inside(self.world, False)
        self.world.conditions[AROUSAL_KEY] = 150
        before_fluid = self.actor.stats.source.get("fluid")

        tag = self.ejaculation.check_and_fire(self.world, self.actor)
        self.assertEqual(tag, TAG_EJACULATION_OUTSIDE)
        # Outside: no fluid deposit
        self.assertEqual(self.actor.stats.source.get("fluid"), before_fluid)

    def test_check_and_fire_below_threshold_returns_none(self) -> None:
        self.actor.active_persistent_states.add("inserted_v")
        self.world.conditions[AROUSAL_KEY] = 50
        self.assertIsNone(self.ejaculation.check_and_fire(self.world, self.actor))

    def test_toggle_inside_flips_state(self) -> None:
        self.assertTrue(self.ejaculation.get_inside(self.world))
        self.assertFalse(self.ejaculation.toggle_inside(self.world))
        self.assertTrue(self.ejaculation.toggle_inside(self.world))

    def test_toggle_command_flips_state(self) -> None:
        self.assertTrue(self.ejaculation.get_inside(self.world))
        result = self.app.command_service.execute(
            self.world, self.actor.key, "toggle_ejaculate_inside"
        )
        self.assertTrue(result.success)
        self.assertFalse(self.ejaculation.get_inside(self.world))


class EjaculationCommandIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        _start_training_in_private(self.app, self.actor, self.world)

    def test_training_command_with_insertion_accumulates_arousal(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_insert_v"
        )
        self.assertTrue(result.success, msg=result.messages)
        self.assertIn("inserted_v", self.actor.active_persistent_states)
        self.assertGreater(
            self.world.conditions.get(AROUSAL_KEY, 0), 0
        )

    def test_ejaculation_tag_enters_triggered_events(self) -> None:
        self.actor.removed_slots = ("underwear_bottom",)
        # Prime arousal just below threshold so next command's gain crosses it.
        self.world.conditions[AROUSAL_KEY] = 90
        result = self.app.command_service.execute(
            self.world, self.actor.key, "train_insert_v"
        )
        self.assertTrue(result.success, msg=result.messages)
        self.assertIn(TAG_EJACULATION_INSIDE, result.triggered_events)

    def test_ejaculation_state_persists_in_world_conditions(self) -> None:
        self.app.ejaculation_service.set_inside(self.world, False)
        self.assertEqual(
            self.world.conditions.get(EJACULATE_INSIDE_KEY), 0
        )
