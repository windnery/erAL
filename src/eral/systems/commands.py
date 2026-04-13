"""Starter command execution with SOURCE production, settlement, and MARK application."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.commands import CommandDefinition
from eral.content.marks import MarkDefinition
from eral.domain.actions import ActionResult
from eral.domain.map import PortMap
from eral.domain.world import CharacterState, WorldState
from eral.engine.runtime_logger import RuntimeLogger
from eral.systems.command_gates import (
    CommandAvailabilityContext,
    CommandCategoryGate,
    CommandSpecificGate,
    GlobalModeGate,
)
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
    maxbase: dict[str, int] | None = None

    def _maxbase_for(self, key: str) -> int:
        if self.maxbase and key in self.maxbase:
            return self.maxbase[key]
        return 9999

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

        for base_key, delta in command.downbase.items():
            current = actor.stats.base.get(base_key)
            maxbase = self._maxbase_for(base_key)
            new_val = max(0, current - delta)
            actor.stats.base.set(base_key, new_val)

        changes = self.settlement.settle_actor(world, actor)
        trigger_scene = self.scene_service.build_for_actor(world, actor, command.key, location.tags)
        self._apply_operation(world, actor, command)
        self._apply_marks(actor, command)
        self._remove_marks(actor, command)
        settled_scene = self.scene_service.build_for_actor(world, actor, command.key, location.tags)
        triggered_events = self.event_service.triggered_events(trigger_scene)
        if not triggered_events:
            triggered_events = self.event_service.triggered_events(settled_scene)
        dialogue_lines = list(self.dialogue_service.lines_for(settled_scene, triggered_events))
        after_date_events, after_date_lines = self._resolve_after_date_followup(
            world,
            actor,
            command,
            location.tags,
        )
        if after_date_lines:
            dialogue_lines.extend(after_date_lines)
        all_triggered_events = triggered_events + after_date_events
        self._log_success(world, actor.key, command.key, all_triggered_events)
        return ActionResult(
            action_key=command.key,
            actor_key=actor.key,
            scene=scene,
            triggered_events=list(all_triggered_events),
            source_deltas=dict(command.source),
            changes=changes,
            messages=dialogue_lines or [f"{actor.display_name} handled command {command.display_name}."],
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

    def _availability_context(
        self,
        world: WorldState,
        actor: CharacterState,
        command: CommandDefinition,
        location_tags: tuple[str, ...],
    ) -> CommandAvailabilityContext:
        return CommandAvailabilityContext(
            world=world,
            actor=actor,
            command=command,
            location_tags=location_tags,
            relationship_service=self.relationship_service,
        )

    @staticmethod
    def _availability_gates() -> tuple[object, ...]:
        return (
            CommandCategoryGate(),
            GlobalModeGate(),
            CommandSpecificGate(),
        )

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

        context = self._availability_context(world, actor, command, location_tags)
        for gate in self._availability_gates():
            reason = gate.failure_reason(context)
            if reason is not None:
                return reason
        return None

    def _resolve_after_date_followup(
        self,
        world: WorldState,
        actor: CharacterState,
        command: CommandDefinition,
        location_tags: tuple[str, ...],
    ) -> tuple[tuple[str, ...], list[str]]:
        if command.operation != "end_date":
            return (), []
        after_date_scene = self.scene_service.build_for_actor(
            world,
            actor,
            "after_date_event",
            location_tags,
        )
        after_date_events = self.event_service.triggered_events(after_date_scene)
        if not after_date_events:
            return (), []
        after_date_lines = list(self.dialogue_service.lines_for(after_date_scene, after_date_events))
        return after_date_events, after_date_lines

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
