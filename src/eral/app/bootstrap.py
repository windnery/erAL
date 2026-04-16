"""Dependency assembly for the erAL runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eral.app.config import AppConfig
from eral.content.abl_upgrade import AblUpgradeConfig, load_abl_upgrade_config
from eral.content.commissions import CommissionDefinition, load_commission_definitions
from eral.content.character_packs import CharacterPack, load_character_packs
from eral.content.characters import CharacterDefinition, InitialStatOverrides, load_character_definitions
from eral.content.commands import CommandDefinition, load_command_definitions
from eral.content.dialogue import DialogueEntry, load_dialogue_entries
from eral.content.events import EventDefinition, load_event_definitions
from eral.content.items import ItemDefinition, load_item_definitions
from eral.content.facilities import FacilityDefinition, load_facility_definitions
from eral.content.marks import MarkDefinition, load_mark_definitions
from eral.content.port_map import load_port_map
from eral.content.relationships import RelationshipStageDefinition, load_relationship_stages
from eral.content.settlement import SettlementRule, load_settlement_rules
from eral.content.stat_axes import StatAxisCatalog, load_stat_axis_catalog
from eral.content.tw_axis_registry import TwAxisRegistry, load_tw_axis_registry
from eral.content.maxbase import load_maxbase
from eral.systems.vital import VitalService
from eral.content.imprint import load_imprint_thresholds
from eral.content.talent_effects import load_talent_effects
from eral.systems.imprint import ImprintService
from eral.systems.favor_calc import load_growth_formula, load_trust_formula
from eral.domain.map import PortMap
from eral.domain.stats import ActorNumericState
from eral.domain.world import CharacterState, PortLocation, TimeSlot, WorldState
from eral.engine.events import EventBus
from eral.engine.paths import RuntimePaths
from eral.engine.runtime_logger import RuntimeLogger
from eral.systems.commands import CommandService
from eral.systems.companions import CompanionService
from eral.systems.commissions import CommissionService
from eral.systems.dates import DateService
from eral.systems.dialogue import DialogueService
from eral.systems.events import EventService
from eral.systems.facilities import FacilityService
from eral.systems.game_loop import GameLoop
from eral.systems.navigation import NavigationService
from eral.systems.relationships import RelationshipService
from eral.systems.resolution import ResolutionService
from eral.systems.schedule import ScheduleService
from eral.systems.scene import SceneService
from eral.systems.save import SaveService
from eral.systems.wallet import WalletService
from eral.systems.settlement import SettlementService


@dataclass(slots=True)
class Application:
    """The assembled application container."""

    root: Path
    config: AppConfig
    paths: RuntimePaths
    stat_axes: StatAxisCatalog
    tw_axes: TwAxisRegistry
    port_map: PortMap
    character_packs: tuple[CharacterPack, ...]
    roster: tuple[CharacterDefinition, ...]
    relationship_stages: tuple[RelationshipStageDefinition, ...]
    events: tuple[EventDefinition, ...]
    dialogue: tuple[DialogueEntry, ...]
    settlement_rules: tuple[SettlementRule, ...]
    commands: tuple[CommandDefinition, ...]
    items: tuple[ItemDefinition, ...]
    event_bus: EventBus
    world: WorldState
    game_loop: GameLoop
    settlement_service: SettlementService
    relationship_service: RelationshipService
    companion_service: CompanionService
    date_service: DateService
    scene_service: SceneService
    event_service: EventService
    dialogue_service: DialogueService
    command_service: CommandService
    navigation_service: NavigationService
    schedule_service: ScheduleService
    save_service: SaveService
    vital_service: VitalService
    wallet_service: WalletService
    commission_service: CommissionService
    abl_upgrade_config: AblUpgradeConfig
    facility_service: FacilityService
    runtime_logger: RuntimeLogger


def _apply_initial_stats(stats: ActorNumericState, overrides: "InitialStatOverrides") -> None:
    """Apply per-character initial stat overrides after zeroing."""
    for key, value in overrides.base.items():
        stats.base.set(key, value)
    for key, value in overrides.palam.items():
        stats.palam.set(key, value)
    for era_index, value in overrides.abl.items():
        stats.compat.abl.set(era_index, value)
    for era_index, value in overrides.talent.items():
        stats.compat.talent.set(era_index, value)
    for era_index, value in overrides.cflag.items():
        stats.compat.cflag.set(era_index, value)


def create_application(root: Path | None = None) -> Application:
    root_path = (root or Path.cwd()).resolve()
    config_path = root_path / "config.ini"
    stat_axes_path = root_path / "data" / "base" / "stat_axes.toml"
    tw_axes_path = root_path / "data" / "generated" / "tw_axis_registry.json"
    port_map_path = root_path / "data" / "base" / "port_map.toml"
    characters_path = root_path / "data" / "base" / "characters.toml"
    character_packs_path = root_path / "data" / "base" / "characters"
    relationship_stages_path = root_path / "data" / "base" / "relationship_stages.toml"
    settlement_rules_path = root_path / "data" / "base" / "settlement_rules.toml"
    commands_path = root_path / "data" / "base" / "commands.toml"
    items_path = root_path / "data" / "base" / "items.toml"
    marks_path = root_path / "data" / "base" / "marks.toml"
    maxbase_path = root_path / "data" / "base" / "maxbase.toml"
    imprint_thresholds_path = root_path / "data" / "base" / "imprint_thresholds.toml"
    abl_upgrade_path = root_path / "data" / "base" / "abl_upgrade.toml"
    commissions_path = root_path / "data" / "base" / "commissions.toml"
    facilities_path = root_path / "data" / "base" / "facilities.toml"

    events_path = root_path / "data" / "base" / "events.toml"
    dialogue_path = root_path / "data" / "base" / "dialogue.toml"

    paths = RuntimePaths.from_root(root_path)
    paths.ensure_runtime_dirs()

    config = AppConfig.load(config_path)
    stat_axes = load_stat_axis_catalog(stat_axes_path)
    tw_axes = load_tw_axis_registry(tw_axes_path)
    port_map = load_port_map(port_map_path)
    mark_defs = load_mark_definitions(marks_path)
    character_packs = load_character_packs(
        character_packs_path,
        stat_axes=stat_axes,
        tw_axes=tw_axes,
        mark_keys={mark.key for mark in mark_defs},
    )
    roster = tuple(pack.character for pack in character_packs) or load_character_definitions(characters_path)
    relationship_stages = load_relationship_stages(relationship_stages_path)
    global_events = load_event_definitions(events_path)
    global_dialogue = load_dialogue_entries(dialogue_path)
    pack_events = tuple(event for pack in character_packs for event in pack.events)
    pack_dialogue = tuple(entry for pack in character_packs for entry in pack.dialogue)
    events = global_events + pack_events
    dialogue = global_dialogue + pack_dialogue
    settlement_rules = load_settlement_rules(settlement_rules_path)
    commands = load_command_definitions(commands_path)
    items = load_item_definitions(items_path)
    maxbase = load_maxbase(maxbase_path)
    imprint_thresholds = load_imprint_thresholds(imprint_thresholds_path)
    abl_upgrade_config = load_abl_upgrade_config(abl_upgrade_path)
    commission_defs = load_commission_definitions(commissions_path)
    facility_defs = load_facility_definitions(facilities_path)
    mark_definitions = {m.key: m for m in mark_defs}
    mark_max_levels = {m.key: m.max_level for m in mark_defs}
    talent_effects = load_talent_effects(root_path / "data" / "base" / "talent_effects.toml")
    favor_formula = load_growth_formula(root_path / "data" / "base" / "relationship_growth.toml")
    trust_formula = load_trust_formula(root_path / "data" / "base" / "relationship_growth.toml")
    start_location = port_map.starting_location()
    event_bus = EventBus()
    runtime_logger = RuntimeLogger(paths=paths)

    world = WorldState(
        current_day=1,
        current_time_slot=TimeSlot.from_name(config.start_time_slot),
        player_name=config.player_name,
        active_location=PortLocation(
            key=start_location.key,
            display_name=start_location.display_name,
        ),
        characters=[],
    )
    schedule_service = ScheduleService(roster={character.key: character for character in roster})
    for definition in roster:
        stats = ActorNumericState.zeroed(stat_axes, tw_axes)
        _apply_initial_stats(stats, definition.initial_stats)
        world.characters.append(
            CharacterState(
                key=definition.key,
                display_name=definition.display_name,
                location_key=definition.initial_location,
                tags=definition.tags,
                stats=stats,
                marks=dict(definition.initial_stats.marks),
            )
        )
    schedule_service.refresh_world(world)

    # Load runtime fields from initial CFLAG overrides, then mirror compat from runtime.
    for actor in world.characters:
        actor.hydrate_runtime_fields_from_compat()
        actor.sync_compat_from_runtime()

    game_loop = GameLoop(
        event_bus=event_bus,
        schedule_service=schedule_service,
        vital_service=None,
        runtime_logger=runtime_logger,
    )
    wallet_service = WalletService()
    facility_service = FacilityService(
        definitions=facility_defs,
        wallet=wallet_service,
    )
    commission_service = CommissionService(
        definitions=commission_defs,
        wallet=wallet_service,
        facility_service=facility_service,
    )
    relationship_service = RelationshipService(stages=relationship_stages)
    companion_service = CompanionService()
    date_service = DateService(companion_service=companion_service)
    settlement_service = SettlementService(
        rules=settlement_rules,
        relationship_service=relationship_service,
        imprint_check=ImprintService(imprint_thresholds),
        mark_max_levels=mark_max_levels,
        favor_formula=favor_formula,
        trust_formula=trust_formula,
        abl_upgrade_config=abl_upgrade_config,
        talent_effects=talent_effects,
        facility_service=facility_service,
    )
    scene_service = SceneService()
    event_service = EventService(events=events, relationship_service=relationship_service)
    dialogue_service = DialogueService(entries=dialogue)
    resolution_service = ResolutionService()
    vital_service = VitalService(
        max_values=maxbase.max_values,
        recover_rates=maxbase.recover_rates,
        talent_effects=talent_effects,
        facility_service=facility_service,
    )
    command_service = CommandService(
        commands={command.key: command for command in commands},
        item_definitions={item.key: item for item in items},
        settlement=settlement_service,
        port_map=port_map,
        scene_service=scene_service,
        event_service=event_service,
        dialogue_service=dialogue_service,
        relationship_service=relationship_service,
        vital_service=vital_service,
        companion_service=companion_service,
        date_service=date_service,
        runtime_logger=runtime_logger,
        mark_definitions=mark_definitions,
        talent_effects=talent_effects,
        game_loop=game_loop,
        wallet_service=wallet_service,
        facility_service=facility_service,
        resolution_service=resolution_service,
    )
    navigation_service = NavigationService(
        port_map=port_map,
        companion_service=companion_service,
        event_bus=event_bus,
        runtime_logger=runtime_logger,
    )
    relationship_service.refresh_world(world)
    companion_service.refresh_world(world)
    date_service.refresh_world(world)
    save_service = SaveService(
        paths=paths,
        stat_axes=stat_axes,
        tw_axes=tw_axes,
        runtime_logger=runtime_logger,
    )
    game_loop.vital_service = vital_service
    game_loop.commission_service = commission_service
    game_loop.facility_service = facility_service
    return Application(
        root=root_path,
        config=config,
        paths=paths,
        stat_axes=stat_axes,
        tw_axes=tw_axes,
        port_map=port_map,
        character_packs=character_packs,
        roster=roster,
        relationship_stages=relationship_stages,
        events=events,
        dialogue=dialogue,
        settlement_rules=settlement_rules,
        commands=commands,
        items=items,
        event_bus=event_bus,
        world=world,
        game_loop=game_loop,
        settlement_service=settlement_service,
        relationship_service=relationship_service,
        companion_service=companion_service,
        date_service=date_service,
        scene_service=scene_service,
        event_service=event_service,
        dialogue_service=dialogue_service,
        command_service=command_service,
        navigation_service=navigation_service,
        schedule_service=schedule_service,
        save_service=save_service,
        vital_service=vital_service,
        wallet_service=wallet_service,
        commission_service=commission_service,
        abl_upgrade_config=abl_upgrade_config,
        facility_service=facility_service,
        runtime_logger=runtime_logger,
    )
