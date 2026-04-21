"""Layered command availability gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from eral.content.commands import CommandDefinition
from eral.content.items import ItemDefinition
from eral.domain.persistent import PersistentStateDefinition, SlotDefinition, can_activate
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
    item_definitions: dict[str, ItemDefinition] | None = None
    vital_service: VitalService | None = None
    persistent_state_definitions: dict[str, PersistentStateDefinition] | None = None
    slot_definitions: dict[str, SlotDefinition] | None = None


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
        if command.requires_training:
            if not world.training_active:
                return "当前未处于调教状态。"
            if world.training_actor_key != actor.key:
                return "当前调教对象不一致。"
            if command.required_removed_slots and not all(
                slot in actor.removed_slots for slot in command.required_removed_slots
            ):
                return "当前服装条件不足，无法执行该调教指令。"
            if command.training_position_keys and world.training_position_key not in command.training_position_keys:
                return "当前体位无法执行该调教指令。"
        _ABL_DISPLAY = {
            "abl_0": "C感觉",
            "abl_1": "V感觉",
            "abl_2": "A感觉",
            "abl_3": "B感觉",
            "abl_9": "亲密",
            "abl_10": "顺从",
            "abl_11": "欲望",
            "abl_12": "技巧",
            "abl_13": "奉仕精神",
            "abl_50": "指技",
            "abl_51": "舌技",
            "abl_52": "胸技",
        }
        _CONDITION_DISPLAY = {
            "train_v_develop": "V开发度",
            "train_a_develop": "A开发度",
            "train_c_develop": "C开发度",
            "train_b_develop": "B开发度",
            "train_hand_develop": "手技开发度",
            "train_oral_develop": "口技开发度",
            "train_service_develop": "奉仕开发度",
        }
        for condition_key, min_value in command.required_conditions.items():
            if condition_key.startswith("abl_"):
                abl_index = int(condition_key[4:])
                current = actor.stats.compat.abl.get(abl_index)
            else:
                current = actor.get_condition(condition_key)
            if current < min_value:
                name = _ABL_DISPLAY.get(condition_key, _CONDITION_DISPLAY.get(condition_key, condition_key))
                return f"{name}不足，无法执行该指令。"
        for condition_key in command.forbidden_conditions:
            if actor.get_condition(condition_key) > 0:
                return f"当前条件禁止执行：{condition_key}。"
        if command.required_actor_tags and not any(tag in actor.tags for tag in command.required_actor_tags):
            return "该指令只能对特定角色使用。"

        missing_items: list[str] = []
        for item_key, required_count in command.required_items.items():
            if world.item_count(item_key) >= required_count:
                continue
            item_def = context.item_definitions.get(item_key) if context.item_definitions else None
            item_name = item_def.display_name if item_def is not None else item_key
            missing_items.append(f"{item_name} x{required_count}")
        if missing_items:
            return f"缺少所需道具：{'、'.join(missing_items)}。"
        for mark_key, min_level in command.required_marks.items():
            if not actor.has_mark(mark_key, min_level):
                return f"缺少所需标记：{mark_key}。"
        return None


@dataclass(frozen=True, slots=True)
class PersistentStateGate:
    def failure_reason(self, context: CommandAvailabilityContext) -> str | None:
        actor = context.actor
        command = context.command
        ps_defs = context.persistent_state_definitions
        slot_defs = context.slot_definitions

        if ps_defs is None or slot_defs is None:
            return None

        for blocked_ps in command.blocked_by_persistent_states:
            if blocked_ps in actor.active_persistent_states:
                ps_def = ps_defs.get(blocked_ps)
                name = ps_def.display_name if ps_def else blocked_ps
                return f"当前处于「{name}」状态，无法执行该指令。"

        ps_key = command.activates_persistent_state
        if ps_key and ps_key not in actor.active_persistent_states:
            if not can_activate(ps_key, actor.active_persistent_states, ps_defs, slot_defs):
                ps_def = ps_defs.get(ps_key)
                name = ps_def.display_name if ps_def else ps_key
                return f"身体槽位不足，无法进入「{name}」状态。"

        return None


__all__ = [
    "CommandAvailabilityContext",
    "CommandAvailabilityGate",
    "CommandCategoryGate",
    "GlobalModeGate",
    "VitalGate",
    "CommandSpecificGate",
    "PersistentStateGate",
]
