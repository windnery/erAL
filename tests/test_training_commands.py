"""Tests for training-specific command gates."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.commands import CommandDefinition
from eral.domain.world import TimeSlot
from eral.systems.command_gates import CommandAvailabilityContext, CommandSpecificGate
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress


class TrainingCommandGateTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)
        self.location = self.app.port_map.location_by_key(self.app.world.active_location.key)

    def _context(self, command: CommandDefinition) -> CommandAvailabilityContext:
        return CommandAvailabilityContext(
            world=self.app.world,
            actor=self.actor,
            command=command,
            location_tags=self.location.tags,
            relationship_service=self.app.relationship_service,
            item_definitions={item.key: item for item in self.app.items},
        )

    def test_training_command_requires_active_training_session(self) -> None:
        command = CommandDefinition(
            key="train_touch",
            display_name="爱抚",
            category="training",
            location_tags=(),
            time_slots=(),
            min_affection=None,
            min_trust=None,
            min_obedience=None,
            required_stage=None,
            operation=None,
            requires_following=None,
            requires_date=None,
            requires_training=True,
            required_removed_slots=(),
            training_position_keys=(),
            required_marks={},
            apply_marks={},
            remove_marks=(),
            source={},
            downbase={},
            success_tiers=(0.1, 1.0, 2.0),
        )

        reason = CommandSpecificGate().failure_reason(self._context(command))

        self.assertEqual(reason, "当前未处于调教状态。")

    def test_insertion_command_requires_removed_underwear_bottom(self) -> None:
        self.app.world.training_active = True
        self.app.world.training_actor_key = self.actor.key
        self.app.world.training_position_key = "standing"
        command = CommandDefinition(
            key="train_insert_v",
            display_name="插入",
            category="training",
            location_tags=(),
            time_slots=(),
            min_affection=None,
            min_trust=None,
            min_obedience=None,
            required_stage=None,
            operation=None,
            requires_following=None,
            requires_date=None,
            requires_training=True,
            required_removed_slots=("underwear_bottom",),
            training_position_keys=(),
            required_marks={},
            apply_marks={},
            remove_marks=(),
            source={},
            downbase={},
            success_tiers=(0.1, 1.0, 2.0),
        )

        reason = CommandSpecificGate().failure_reason(self._context(command))

        self.assertEqual(reason, "当前服装条件不足，无法执行该调教指令。")


class TrainingCommandExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)
        private_location = next(
            location for location in self.app.port_map.locations if "private" in location.tags
        )
        self.actor.location_key = private_location.key
        self.app.world.active_location.key = private_location.key
        self.app.world.active_location.display_name = private_location.display_name
        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.world.current_hour = 17
        self.app.world.current_minute = 0

    def test_start_training_command_enters_training_mode(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            self.actor.key,
            "start_training",
        )

        self.assertTrue(result.success)
        self.assertTrue(self.app.world.training_active)
        self.assertEqual(self.app.world.training_actor_key, self.actor.key)
        self.assertEqual(self.app.world.training_position_key, "standing")

    def test_remove_underwear_bottom_updates_removed_slots(self) -> None:
        self.app.training_service.start_session(
            self.app.world,
            actor_key=self.actor.key,
            position_key="standing",
        )

        result = self.app.command_service.execute(
            self.app.world,
            self.actor.key,
            "remove_underwear_bottom",
        )

        self.assertTrue(result.success)
        self.assertEqual(self.actor.removed_slots, ("underwear_bottom",))


if __name__ == "__main__":
    unittest.main()
