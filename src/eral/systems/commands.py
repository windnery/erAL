"""Starter command execution with SOURCE production, settlement, and MARK application."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.commands import CommandDefinition
from eral.content.marks import MarkDefinition
from eral.content.items import ItemDefinition
from eral.domain.actions import ActionResult
from eral.domain.map import PortMap
from eral.domain.world import CharacterState, WorldState
from eral.engine.runtime_logger import RuntimeLogger
from eral.systems.command_gates import (
    CommandAvailabilityContext,
    CommandCategoryGate,
    CommandSpecificGate,
    GlobalModeGate,
    PersistentStateGate,
    VitalGate,
)
from eral.systems.gifts import GiftService
from eral.domain.persistent import PersistentStateDefinition, SlotDefinition, clear_states_by_event, persistent_source
from eral.systems.dialogue import DialogueService
from eral.systems.ejaculation import EjaculationService
from eral.systems.events import EventService
from eral.systems.companions import CompanionService
from eral.systems.dates import DateService
from eral.systems.distribution import DistributionService
from eral.systems.facilities import FacilityService
from eral.systems.game_loop import GameLoop
from eral.systems.relationships import RelationshipService
from eral.systems.scene import SceneService
from eral.systems.resolution import ResolutionService
from eral.systems.settlement import SettlementService
from eral.systems.skins import SkinService
from eral.systems.time_service import TimeService
from eral.domain.training import TrainingResult
from eral.systems.training import TrainingService
from eral.systems.source_extra import apply_source_extra, apply_training_mark_effects
from eral.systems.vital import VitalService
from eral.systems.wallet import WalletService
from eral.content.talent_effects import TalentEffect


@dataclass(slots=True)
class CommandService:
    """Execute static commands against a visible actor."""

    commands: dict[str, CommandDefinition]
    item_definitions: dict[str, ItemDefinition] | None
    settlement: SettlementService
    port_map: PortMap
    scene_service: SceneService
    event_service: EventService
    dialogue_service: DialogueService
    relationship_service: RelationshipService
    vital_service: VitalService | None = None
    companion_service: CompanionService | None = None
    date_service: DateService | None = None
    game_loop: GameLoop | None = None
    mark_definitions: dict[str, MarkDefinition] | None = None
    runtime_logger: RuntimeLogger | None = None
    talent_effects: tuple[TalentEffect, ...] = ()
    wallet_service: WalletService | None = None
    facility_service: FacilityService | None = None
    resolution_service: ResolutionService | None = None
    skin_service: SkinService | None = None
    time_service: TimeService | None = None
    distribution_service: DistributionService | None = None
    training_service: TrainingService | None = None
    persistent_state_definitions: dict[str, PersistentStateDefinition] | None = None
    slot_definitions: dict[str, SlotDefinition] | None = None
    gift_service: GiftService | None = None
    ejaculation_service: EjaculationService | None = None

    def _apply_downbase(self, actor: CharacterState, downbase: dict[str, int]) -> None:
        if self.vital_service is not None:
            self.vital_service.apply_downbase(actor, downbase)
        else:
            for base_key, delta in downbase.items():
                current = actor.stats.base.get(base_key)
                new_val = max(0, current - delta)
                actor.stats.base.set(base_key, new_val)

    def execute(self, world: WorldState, actor_key: str, command_key: str) -> ActionResult:
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
        resolution_result = self._resolve_command(world, actor, command)
        resolution_tags = self._resolution_result_tags(command, resolution_result)
        if resolution_result is not None and not resolution_result.success:
            dialogue_lines = list(self.dialogue_service.lines_for(scene, resolution_tags))
            return ActionResult(
                action_key=command.key,
                success=False,
                chance=resolution_result.chance,
                actor_key=actor.key,
                scene=scene,
                triggered_events=list(resolution_tags),
                messages=dialogue_lines or [f"{actor.display_name}未能完成{command.display_name}。"],
            )

        for source_key, delta in command.source.items():
            actor.stats.source.add(source_key, delta)

        gift_consumed = self._apply_gift(world, actor, command)

        self._apply_persistent_source(actor)

        if command.activates_persistent_state:
            self._toggle_persistent_state(actor, command.activates_persistent_state)

        if command.requires_training and self.training_service is not None:
            self._apply_training_development(actor, command.key)
            actor.add_condition("train_total_steps", 1)

        apply_source_extra(actor.stats, self.talent_effects)

        if command.requires_training:
            apply_training_mark_effects(actor)

        self._apply_downbase(actor, command.downbase)

        actor.record_memory(f"cmd:{command.key}")

        fainted = False
        if self.vital_service is not None and self.vital_service.is_fainted(actor):
            fainted = True
            self.vital_service.sleep_recovery(actor, world)
            if self.game_loop is not None:
                self.game_loop.advance_to_dawn(world)

        if self.time_service is not None and not fainted:
            self.time_service.advance_minutes(world, command.elapsed_minutes)

        changes = self.settlement.settle_actor(world, actor)

        training_settlement = None
        ejaculation_tag: str | None = None
        if command.requires_training and self.training_service is not None:
            training_settlement = self.training_service.detect_results(actor)
            result_tags = tuple(r.value for r in training_settlement.results)
            if result_tags:
                world.training_flags["last_results"] = ",".join(result_tags)
            else:
                world.training_flags.pop("last_results", None)
            if training_settlement.counter is not None:
                self._apply_counter_source(actor, training_settlement.counter)
            world.training_step_index += 1
            if self.ejaculation_service is not None:
                self.ejaculation_service.accumulate(world, actor)
                ejaculation_tag = self.ejaculation_service.check_and_fire(world, actor)

        # Process personal income from work commands
        funds_delta: dict[str, int] = {}
        if command.personal_income > 0 and self.wallet_service is not None:
            income = command.personal_income
            if self.facility_service is not None:
                income = int(income * self.facility_service.income_multiplier(world))
            earned = self.wallet_service.add_personal(
                world, income, reason="work", source_key=command.key,
            )
            if earned > 0:
                funds_delta["personal"] = earned

        trigger_scene = self.scene_service.build_for_actor(world, actor, command.key, location.tags)
        self._apply_operation(world, actor, command)
        self._apply_marks(actor, command)
        self._remove_marks(actor, command)
        settled_scene = self.scene_service.build_for_actor(world, actor, command.key, location.tags)
        triggered_events = self.event_service.triggered_events(trigger_scene)
        if not triggered_events:
            triggered_events = self.event_service.triggered_events(settled_scene)
        training_tags = tuple(r.value for r in training_settlement.results) if training_settlement else ()
        if training_settlement and training_settlement.counter is not None:
            training_tags = training_tags + (training_settlement.counter.value,)
        if ejaculation_tag is not None:
            training_tags = training_tags + (ejaculation_tag,)
        dialogue_keys = resolution_tags + training_tags + triggered_events
        dialogue_lines = list(self.dialogue_service.lines_for(settled_scene, dialogue_keys))
        after_date_events, after_date_lines = self._resolve_after_date_followup(
            world,
            actor,
            command,
            location.tags,
        )
        if after_date_lines:
            dialogue_lines.extend(after_date_lines)
        all_triggered_events = resolution_tags + training_tags + triggered_events + after_date_events
        for event_key in all_triggered_events:
            actor.record_memory(f"evt:{event_key}")
        self._log_success(world, actor.key, command.key, all_triggered_events)
        return ActionResult(
            action_key=command.key,
            success=True,
            chance=resolution_result.chance if resolution_result is not None else 1.0,
            actor_key=actor.key,
            scene=scene,
            triggered_events=list(all_triggered_events),
            source_deltas=dict(command.source),
            changes=changes,
            messages=dialogue_lines or [f"{actor.display_name} handled command {command.display_name}."],
            funds_delta=funds_delta,
            fainted=fainted,
        )

    def _resolve_command(
        self,
        world: WorldState,
        actor: CharacterState,
        command: CommandDefinition,
    ):
        if command.resolution_key is None:
            return None
        if self.resolution_service is None:
            raise ValueError(f"Missing resolution service for {command.resolution_key}")
        result = self.resolution_service.resolve(command.resolution_key, world, actor)
        if not result.success:
            return result
        if command.resolution_key == "oath":
            if not world.consume_item("pledge_ring", 1):
                raise ValueError("缺少所需道具：誓约之戒 x1。")
            self._ensure_oath_mark(actor)
            if self.skin_service is not None:
                for skin in self.skin_service.skin_definitions.values():
                    if skin.actor_key == actor.key and skin.grant_mode == "oath_reward":
                        actor.unlock_skin(skin.key)
            self.relationship_service.update_actor(actor)
        return result

    @staticmethod
    def _resolution_result_tags(command: CommandDefinition, resolution_result) -> tuple[str, ...]:
        if command.resolution_key != "oath" or resolution_result is None:
            return ()
        return ("oath_success",) if resolution_result.success else ("oath_failure",)

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
            vital_service=self.vital_service,
            item_definitions=self.item_definitions,
            persistent_state_definitions=self.persistent_state_definitions,
            slot_definitions=self.slot_definitions,
        )

    @staticmethod
    def _availability_gates() -> tuple[object, ...]:
        return (
            CommandCategoryGate(),
            GlobalModeGate(),
            VitalGate(),
            CommandSpecificGate(),
            PersistentStateGate(),
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

    _TRAINING_DEV_MAP = {
        "train_touch": {"train_touch_count": 1},
        "train_breast_touch": {"train_b_develop": 1},
        "train_c_touch": {"train_c_develop": 1},
        "train_hand": {"train_hand_develop": 1},
        "train_oral": {"train_oral_develop": 1, "train_service_develop": 1},
        "train_deep_oral": {"train_oral_develop": 2, "train_service_develop": 2},
        "train_insert_v": {"train_v_develop": 1, "submission": 30},
        "train_insert_v_missionary": {"train_v_develop": 1, "submission": 10},
        "train_insert_v_behind": {"train_v_develop": 1, "submission": 15},
        "train_insert_v_face": {"train_v_develop": 1, "submission": 10},
        "train_insert_v_backseat": {"train_v_develop": 1, "submission": 15},
        "train_insert_v_riding": {"train_v_develop": 1, "submission": 5},
        "train_insert_a": {"train_a_develop": 1, "submission": 20},
        "train_insert_a_missionary": {"train_a_develop": 1, "submission": 15},
        "train_insert_a_behind": {"train_a_develop": 1, "submission": 20},
        "train_insert_a_face": {"train_a_develop": 1, "submission": 10},
        "train_insert_a_backseat": {"train_a_develop": 1, "submission": 15},
        "train_insert_a_riding": {"train_a_develop": 1, "submission": 5},
        "train_double_insert": {"train_v_develop": 1, "train_a_develop": 1, "submission": 30},
        "train_rape": {"train_v_develop": 1},
        "train_service_hand": {"train_service_develop": 1, "train_hand_develop": 1},
        "train_service_oral": {"train_service_develop": 2, "train_oral_develop": 1},
        "train_paizu": {"train_b_develop": 1, "train_service_develop": 1},
        "train_69": {"train_oral_develop": 1, "train_c_develop": 1},
        "train_bubble_dance": {"train_b_develop": 1},
        "train_foot_job": {"train_service_develop": 1},
        "train_vacuum_blowjob": {"train_oral_develop": 2, "train_service_develop": 1},
        "train_condom_swallow": {"train_oral_develop": 1, "submission": 10},
        "train_paizuri_fuck": {"train_b_develop": 1, "train_service_develop": 1, "submission": 10},
        "train_thigh_job": {"train_c_develop": 1},
        "train_kiss": {"train_kiss_count": 1},
        "train_kiss_deep": {"train_kiss_count": 2},
        "train_continue_kiss": {"train_kiss_count": 1},
        "train_whisper": {"train_whisper_count": 1},
        "train_finger_insert": {"train_c_develop": 2, "train_v_develop": 1},
        "train_nipple_tease": {"train_b_develop": 2},
        "train_masturbate_order": {"train_c_develop": 1, "submission": 20},
        "train_talk_pillow": {},
        "train_double_stim": {"train_c_develop": 1, "train_v_develop": 1},
        "train_moaning": {},
        "use_roter": {"train_c_develop": 1},
        "use_eros": {"train_c_develop": 1},
        "use_clit_cap": {"train_c_develop": 1},
        "use_onahole": {"train_c_develop": 1},
        "use_vibrator": {"train_c_develop": 1, "train_v_develop": 1},
        "use_av": {"train_a_develop": 1},
        "use_anal_beads": {"train_a_develop": 1},
        "use_nipple_cap": {"train_b_develop": 1},
        "use_nipple_vibrator": {"train_b_develop": 1},
        "use_milker": {"train_b_develop": 1},
        "use_lotion": {},
        "spanking": {"train_pain_develop": 1},
        "use_whip": {"train_pain_develop": 2},
        "use_candle": {"train_pain_develop": 1},
        "use_needle": {"train_pain_develop": 2},
        "use_blindfold": {},
        "use_rope": {},
        "use_ball_gag": {},
        "use_restraint": {},
        "use_nipple_spanking": {"train_b_develop": 1, "train_pain_develop": 1},
        "use_aphrodisiac": {},
        "use_diuretic": {},
        "use_videocam": {},
        "use_outdoor": {"train_exhibition_develop": 1},
        "use_bathhouse": {},
        "use_shower": {},
        "use_new_wife": {},
        "use_apron": {"train_exhibition_develop": 1},
        "use_sleep_drug": {},
        "use_ovulation": {},
        "force_cunnilingus": {"train_c_develop": 1, "submission": 20},
        "force_69": {"train_c_develop": 1, "train_oral_develop": 1, "submission": 20},
        "foot_worship": {"train_service_develop": 1, "submission": 10},
        "use_anal_plug": {"train_a_develop": 1},
        "use_enema": {"train_a_develop": 1},
        "use_balloon": {"train_a_develop": 2},
        "use_anal_electrode": {"train_a_develop": 2},
        "use_piss": {},
        "be_penetrated_missionary": {"train_v_develop": 1},
        "be_penetrated_behind": {"train_v_develop": 1},
        "be_penetrated_face": {"train_v_develop": 1},
        "be_penetrated_backseat": {"train_v_develop": 1},
        "be_penetrated_riding": {"train_v_develop": 1},
        "be_fucked_a_missionary": {"train_a_develop": 1},
        "be_fucked_a_behind": {"train_a_develop": 1},
        "be_fucked_a_riding": {"train_a_develop": 1},
    }

    @staticmethod
    def _apply_training_development(actor: CharacterState, command_key: str) -> None:
        dev_map = CommandService._TRAINING_DEV_MAP.get(command_key, {})
        for key, delta in dev_map.items():
            if key == "submission":
                actor.stats.source.add(key, delta)
            else:
                actor.add_condition(key, delta)

    _COUNTER_SOURCE = {
        TrainingResult.COUNTER_KISS: {"affection": 30, "joy": 20, "lust": 15},
        TrainingResult.COUNTER_EMBRACE: {"lust": 25, "submission": 10, "pleasure_m": 15},
        TrainingResult.COUNTER_SERVICE: {"give_pleasure_c": 30, "submission": 20, "abl_13": 1},
        TrainingResult.COUNTER_REQUEST: {"sexual_act": 25, "submission": 15, "lust": 20},
    }

    @staticmethod
    def _apply_counter_source(actor: CharacterState, counter: TrainingResult) -> None:
        source_map = CommandService._COUNTER_SOURCE.get(counter, {})
        for key, delta in source_map.items():
            actor.stats.source.add(key, delta)

    def _apply_operation(
        self,
        world: WorldState,
        actor: CharacterState,
        command: CommandDefinition,
    ) -> None:
        operation = command.operation
        if operation is None and command.key in {
            "start_training",
            "end_training",
            "remove_underwear_bottom",
            "remove_top",
            "change_position_missionary",
            "change_position_behind",
            "change_position_standing",
            "toggle_ejaculate_inside",
        }:
            operation = command.key

        if operation is None:
            return
        if operation == "sleep" and self.vital_service is not None:
            self.vital_service.sleep_recovery(actor, world)
        elif operation == "nap" and self.vital_service is not None:
            self.vital_service.rest_recovery(actor, world)
        elif operation == "bathe" and self.vital_service is not None:
            self.vital_service.bathe_recovery(actor, world)
        elif operation == "start_training" and self.training_service is not None:
            self.training_service.start_session(world, actor.key, position_key="standing")
        elif operation == "end_training" and self.training_service is not None:
            self.training_service.end_session(world)
            self._clear_persistent_states(actor, "end_training")
            actor.clear_removed_slots()
        elif operation == "remove_underwear_bottom":
            if "underwear_bottom" not in actor.removed_slots:
                actor.removed_slots = (*actor.removed_slots, "underwear_bottom")
        elif operation == "remove_top":
            if "top" not in actor.removed_slots:
                actor.removed_slots = (*actor.removed_slots, "top")
        elif operation == "change_position_missionary":
            world.training_position_key = "missionary"
        elif operation == "change_position_behind":
            world.training_position_key = "from_behind"
        elif operation == "change_position_standing":
            world.training_position_key = "standing"
        elif operation == "toggle_ejaculate_inside":
            if self.ejaculation_service is not None:
                self.ejaculation_service.toggle_inside(world)
        elif self.companion_service is None:
            return
        elif operation == "start_follow":
            self.companion_service.start_follow(world, actor)
        elif operation == "stop_follow":
            self.companion_service.stop_follow(world, actor)
        elif operation == "start_date" and self.date_service is not None:
            self.date_service.start_date(world, actor)
        elif operation == "end_date" and self.date_service is not None:
            self.date_service.end_date(world, actor)
            self._clear_persistent_states(actor, "end_date")

    def _apply_gift(self, world: WorldState, actor: CharacterState, command: CommandDefinition) -> str | None:
        if command.key != "gift" or self.gift_service is None:
            return None
        gift_key = self.gift_service.best_gift_in_inventory(world.inventory)
        if gift_key is None:
            raise ValueError("背包中没有可送的礼物。")
        world.consume_item(gift_key, 1)
        multiplier = self.gift_service.preference_multiplier(actor.key, gift_key)
        if multiplier != 1.0:
            bonus_source = self.gift_service.apply_gift_source(command.source, multiplier - 1.0)
            for key, delta in bonus_source.items():
                actor.stats.source.add(key, delta)
        actor.record_memory(f"gift:{gift_key}")
        return gift_key

    def _apply_persistent_source(self, actor: CharacterState) -> None:
        if not self.persistent_state_definitions or not actor.active_persistent_states:
            return
        for key, delta in persistent_source(actor.active_persistent_states, self.persistent_state_definitions).items():
            actor.stats.source.add(key, delta)

    def _toggle_persistent_state(self, actor: CharacterState, ps_key: str) -> None:
        if ps_key in actor.active_persistent_states:
            actor.active_persistent_states.discard(ps_key)
        else:
            actor.active_persistent_states.add(ps_key)

    def _clear_persistent_states(self, actor: CharacterState, event: str) -> None:
        if not self.persistent_state_definitions:
            return
        actor.active_persistent_states = clear_states_by_event(
            actor.active_persistent_states, event, self.persistent_state_definitions,
        )

    def _ensure_oath_mark(self, actor: CharacterState) -> None:
        if actor.has_mark("oath"):
            return
        max_level = 1
        if self.mark_definitions and "oath" in self.mark_definitions:
            max_level = self.mark_definitions["oath"].max_level
        actor.add_mark("oath", 1, max_level)
