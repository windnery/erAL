"""Starter command execution with SOURCE production, settlement, and MARK application."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.commands import CommandDefinition
from eral.content.marks import MarkDefinition
from eral.domain.actions import ActionResult
from eral.domain.map import PortMap
from eral.domain.world import CharacterState, WorldState
from eral.engine.runtime_logger import RuntimeLogger
from eral.systems.dialogue import DialogueService
from eral.systems.events import EventService
from eral.systems.companions import CompanionService
from eral.systems.dates import DateService
from eral.systems.relationships import RelationshipService
from eral.systems.scene import SceneService
from eral.systems.settlement import SettlementService


@dataclass(slots=True)
class CommandService:
    """Execute static commands against a visible actor."""

    commands: dict[str, CommandDefinition]
    settlement: SettlementService
    port_map: PortMap
    scene_service: SceneService
    event_service: EventService
    dialogue_service: DialogueService
    relationship_service: RelationshipService
    companion_service: CompanionService | None = None
    date_service: DateService | None = None
    mark_definitions: dict[str, MarkDefinition] | None = None
    runtime_logger: RuntimeLogger | None = None

    def available_commands(self, world: WorldState) -> tuple[CommandDefinition, ...]:
        location = self.port_map.location_by_key(world.active_location.key)
        available: list[CommandDefinition] = []

        for command in self.commands.values():
            if self._is_available_at_location(world, command, location.tags):
                available.append(command)

        return tuple(available)

    def available_commands_for_actor(
        self,
        world: WorldState,
        actor_key: str,
    ) -> tuple[CommandDefinition, ...]:
        actor = self._resolve_actor(world, actor_key)
        location = self.port_map.location_by_key(world.active_location.key)
        available: list[CommandDefinition] = []

        if actor.location_key != world.active_location.key:
            return ()

        for command in self.commands.values():
            if self._availability_failure_reason(world, actor, command, location.tags) is None:
                available.append(command)

        return tuple(available)

    def execute(self, world: WorldState, actor_key: str, command_key: str) -> ActionResult:
        command = self.commands[command_key]
        actor = self._resolve_actor(world, actor_key)
        location = self.port_map.location_by_key(world.active_location.key)

        unavailable_reason = self._availability_failure_reason(world, actor, command, location.tags)
        if unavailable_reason is not None:
            self._log_failure(world, actor_key, command_key, unavailable_reason)
            raise ValueError(unavailable_reason)

        scene = self.scene_service.build_for_actor(world, actor, command.key, location.tags)
        for source_key, delta in command.source.items():
            actor.stats.source.add(source_key, delta)

        changes = self.settlement.settle_actor(world, actor)
        trigger_scene = self.scene_service.build_for_actor(world, actor, command.key, location.tags)
        self._apply_operation(world, actor, command)
        self._apply_marks(actor, command)
        self._remove_marks(actor, command)
        settled_scene = self.scene_service.build_for_actor(world, actor, command.key, location.tags)
        triggered_events = self.event_service.triggered_events(trigger_scene)
        if not triggered_events:
            triggered_events = self.event_service.triggered_events(settled_scene)
        dialogue_lines = self.dialogue_service.lines_for(settled_scene, triggered_events)
        self._log_success(world, actor.key, command.key, triggered_events)
        return ActionResult(
            action_key=command.key,
            actor_key=actor.key,
            scene=scene,
            triggered_events=list(triggered_events),
            source_deltas=dict(command.source),
            changes=changes,
            messages=list(dialogue_lines) or [f"{actor.display_name} handled command {command.display_name}."],
        )

    def _log_success(
        self,
        world: WorldState,
        actor_key: str,
        command_key: str,
        triggered_events: tuple[str, ...],
    ) -> None:
        if self.runtime_logger is None:
            return
        self.runtime_logger.append(
            kind="command",
            action_key=command_key,
            actor_key=actor_key,
            day=world.current_day,
            time_slot=world.current_time_slot.value,
            location_key=world.active_location.key,
            triggered_events=list(triggered_events),
        )

    def _log_failure(
        self,
        world: WorldState,
        actor_key: str,
        command_key: str,
        reason: str,
    ) -> None:
        if self.runtime_logger is None:
            return
        self.runtime_logger.append(
            kind="command_failed",
            action_key=command_key,
            actor_key=actor_key,
            day=world.current_day,
            time_slot=world.current_time_slot.value,
            location_key=world.active_location.key,
            reason=reason,
        )

    @staticmethod
    def _resolve_actor(world: WorldState, actor_key: str) -> CharacterState:
        for actor in world.characters:
            if actor.key == actor_key:
                return actor
        raise KeyError(actor_key)

    @staticmethod
    def _is_available_at_location(
        world: WorldState,
        command: CommandDefinition,
        location_tags: tuple[str, ...],
    ) -> bool:
        if command.location_tags and not any(tag in location_tags for tag in command.location_tags):
            return False
        if command.time_slots and world.current_time_slot.value not in command.time_slots:
            return False
        return True

    def _is_available_for_actor(
        self,
        world: WorldState,
        actor: CharacterState,
        command: CommandDefinition,
        location_tags: tuple[str, ...],
    ) -> bool:
        return self._availability_failure_reason(world, actor, command, location_tags) is None

    def _availability_failure_reason(
        self,
        world: WorldState,
        actor: CharacterState,
        command: CommandDefinition,
        location_tags: tuple[str, ...],
    ) -> str | None:
        if actor.location_key != world.active_location.key:
            return "目标角色不在当前地点。"
        if not self._passes_command_category_gate(command):
            return "该指令分类未启用。"
        global_reason = self._global_mode_failure_reason(world, command)
        if global_reason is not None:
            return global_reason
        return self._specific_failure_reason(world, actor, command, location_tags)

    @staticmethod
    def _passes_command_category_gate(command: CommandDefinition) -> bool:
        return bool(command.category)

    @staticmethod
    def _global_mode_failure_reason(world: WorldState, command: CommandDefinition) -> str | None:
        if world.is_busy and command.category in {"daily", "work", "follow", "date", "intimacy"}:
            return "当前处于忙碌状态，无法执行该指令。"
        if world.is_date_traveling and command.category == "date":
            return "当前处于约会途中，无法执行该约会指令。"
        return None

    def _specific_failure_reason(
        self,
        world: WorldState,
        actor: CharacterState,
        command: CommandDefinition,
        location_tags: tuple[str, ...],
    ) -> str | None:
        if not self._is_available_at_location(world, command, location_tags):
            if command.time_slots and world.current_time_slot.value not in command.time_slots:
                return "当前时段不可执行该指令。"
            return "当前地点不可执行该指令。"
        if command.min_affection is not None and actor.affection < command.min_affection:
            return "当前好感不足，无法执行该指令。"
        if command.min_trust is not None and actor.trust < command.min_trust:
            return "当前信赖不足，无法执行该指令。"
        if command.min_obedience is not None and actor.obedience < command.min_obedience:
            return "当前服从不足，无法执行该指令。"
        if command.required_stage is not None:
            if actor.relationship_stage is None:
                return "当前关系阶段不足，无法执行该指令。"
            required_rank = self.relationship_service.rank_of(command.required_stage)
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

    def _apply_marks(
        self,
        actor: CharacterState,
        command: CommandDefinition,
    ) -> None:
        if not command.apply_marks:
            return
        for mark_key, delta in command.apply_marks.items():
            max_level = 1
            if self.mark_definitions and mark_key in self.mark_definitions:
                max_level = self.mark_definitions[mark_key].max_level
            actor.add_mark(mark_key, delta, max_level)

    @staticmethod
    def _remove_marks(
        actor: CharacterState,
        command: CommandDefinition,
    ) -> None:
        for mark_key in command.remove_marks:
            if mark_key in actor.marks:
                del actor.marks[mark_key]

    def _apply_operation(
        self,
        world: WorldState,
        actor: CharacterState,
        command: CommandDefinition,
    ) -> None:
        if self.companion_service is None or command.operation is None:
            return
        if command.operation == "start_follow":
            self.companion_service.start_follow(world, actor)
        elif command.operation == "stop_follow":
            self.companion_service.stop_follow(world, actor)
        elif command.operation == "start_date" and self.date_service is not None:
            self.date_service.start_date(world, actor)
        elif command.operation == "end_date" and self.date_service is not None:
            self.date_service.end_date(world, actor)
