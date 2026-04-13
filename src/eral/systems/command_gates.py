"""Layered command availability gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from eral.content.commands import CommandDefinition
from eral.domain.world import CharacterState, WorldState
from eral.systems.relationships import RelationshipService
from eral.systems.vital import VitalService


@dataclass(frozen=True, slots=True)
class CommandAvailabilityContext:
    world: WorldState
    actor: CharacterState
    command: CommandDefinition
    location_tags: tuple[str, ...]
    relationship_service: RelationshipService
    vital_service: VitalService | None = None


class CommandAvailabilityGate(Protocol):
    def failure_reason(self, context: CommandAvailabilityContext) -> str | None: ...


@dataclass(frozen=True, slots=True)
class CommandCategoryGate:
    def failure_reason(self, context: CommandAvailabilityContext) -> str | None:
        if not context.command.category:
            return "该指令分类未启用。"
        return None


@dataclass(frozen=True, slots=True)
class GlobalModeGate:
    def failure_reason(self, context: CommandAvailabilityContext) -> str | None:
        world = context.world
        command = context.command
        if world.is_busy and command.category in {"daily", "work", "follow", "date", "intimacy"}:
            return "当前处于忙碌状态，无法执行该指令。"
        if world.is_date_traveling and command.category == "date":
            return "当前处于约会途中，无法执行该约会指令。"
        return None


@dataclass(frozen=True, slots=True)
class VitalGate:
    """Block commands when actor's vitals are depleted."""

    def failure_reason(self, context: CommandAvailabilityContext) -> str | None:
        actor = context.actor
        command = context.command
        vital = context.vital_service
        if vital is None:
            return None

        if vital.is_fainted(actor):
            return "体力耗尽，已晕倒。"

        if vital.is_spirit_depleted(actor) and command.downbase.get("spirit", 0) > 0:
            return "气力耗尽，无法执行该指令。"

        return None


@dataclass(frozen=True, slots=True)
class CommandSpecificGate:
    def failure_reason(self, context: CommandAvailabilityContext) -> str | None:
        world = context.world
        actor = context.actor
        command = context.command
        location_tags = context.location_tags

        if command.location_tags and not any(tag in location_tags for tag in command.location_tags):
            if command.time_slots and world.current_time_slot.value not in command.time_slots:
                return "当前时段不可执行该指令。"
            return "当前地点不可执行该指令。"
        if command.time_slots and world.current_time_slot.value not in command.time_slots:
            return "当前时段不可执行该指令。"
        if command.min_affection is not None and actor.affection < command.min_affection:
            return "当前好感不足，无法执行该指令。"
        if command.min_trust is not None and actor.trust < command.min_trust:
            return "当前信赖不足，无法执行该指令。"
        if command.min_obedience is not None and actor.obedience < command.min_obedience:
            return "当前服从不足，无法执行该指令。"
        if command.required_stage is not None:
            if actor.relationship_stage is None:
                return "当前关系阶段不足，无法执行该指令。"
            required_rank = context.relationship_service.rank_of(command.required_stage)
            if actor.relationship_stage.rank < required_rank:
                return "当前关系阶段不足，无法执行该指令。"
        if command.requires_following is not None and actor.is_following != command.requires_following:
            return "需要同行状态才能执行该指令。"
        if command.requires_date is not None and actor.is_on_date != command.requires_date:
            return "需要约会状态才能执行该指令。"
        for mark_key, min_level in command.required_marks.items():
            if not actor.has_mark(mark_key, min_level):
                return f"缺少所需标记：{mark_key}。"
        return None


__all__ = [
    "CommandAvailabilityContext",
    "CommandAvailabilityGate",
    "CommandCategoryGate",
    "GlobalModeGate",
    "VitalGate",
    "CommandSpecificGate",
]
