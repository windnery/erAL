"""Tests for layered command availability gates."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.commands import CommandDefinition
from eral.systems.command_gates import (
    CommandAvailabilityContext,
    CommandCategoryGate,
    CommandSpecificGate,
    GlobalModeGate,
)
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress, seed_like


class CommandGateTests(unittest.TestCase):
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

    def test_category_gate_rejects_command_without_category(self) -> None:
        command = CommandDefinition(
            key="bad",
            display_name="Bad",
            location_tags=(),
            time_slots=(),
            min_affection=None,
            min_trust=None,
            min_obedience=None,
            required_stage=None,
            operation=None,
            requires_following=None,
            requires_date=None,
            required_marks={},
            apply_marks={},
            remove_marks=(),
            source={},
            downbase={},
            success_tiers=(0.1, 1.0, 2.0),
            category="",
        )

        reason = CommandCategoryGate().failure_reason(self._context(command))
        self.assertIsNotNone(reason)

    def test_global_mode_gate_blocks_busy_daily_command(self) -> None:
        self.app.world.is_busy = True
        command = self.app.command_service.commands["chat"]

        reason = GlobalModeGate().failure_reason(self._context(command))
        self.assertEqual(reason, "当前处于忙碌状态，无法执行该指令。")

    def test_specific_gate_reports_follow_requirement(self) -> None:
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        command = self.app.command_service.commands["lap_pillow"]

        reason = CommandSpecificGate().failure_reason(self._context(command))
        self.assertEqual(reason, "需要同行状态才能执行该指令。")

    def test_specific_gate_reports_missing_required_item(self) -> None:
        seed_like(self.actor)
        self.app.relationship_service.update_actor(self.actor)
        location = self.app.port_map.location_by_key("dock")
        self.app.world.active_location.key = location.key
        self.app.world.active_location.display_name = location.display_name
        self.app.world.current_time_slot = self.app.world.current_time_slot.MORNING
        self.actor.location_key = location.key
        self.location = location
        self.app.world.inventory.pop("pledge_ring", None)
        command = self.app.command_service.commands["oath"]

        reason = CommandSpecificGate().failure_reason(self._context(command))

        self.assertEqual(reason, "缺少所需道具：誓约之戒 x1。")

    def test_specific_gate_reports_time_slot_reason_with_consistent_copy(self) -> None:
        seed_like(self.actor)
        self.app.relationship_service.update_actor(self.actor)
        self.location = self.app.port_map.location_by_key("bathhouse")
        self.app.world.active_location.key = self.location.key
        self.app.world.active_location.display_name = self.location.display_name
        self.actor.location_key = self.location.key
        command = self.app.command_service.commands["tease"]

        reason = CommandSpecificGate().failure_reason(self._context(command))

        self.assertEqual(reason, "当前时段不可执行该指令。")

    def test_specific_gate_reports_relationship_reason_with_consistent_copy(self) -> None:
        command = self.app.command_service.commands["hug"]
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING

        reason = CommandSpecificGate().failure_reason(self._context(command))

        self.assertEqual(reason, "当前关系阶段不足，无法执行该指令。")


if __name__ == "__main__":
    unittest.main()
