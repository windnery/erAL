"""Dependency assembly for the erAL runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eral.app.config import AppConfig
from eral.content.abl_upgrade import AblUpgradeConfig, load_abl_upgrade_config
from eral.content.calendar import CalendarDefinition, load_calendar_definition
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
from eral.content.shops import load_shopfront_definitions
from eral.content.skins import (
    AppearanceDefinition,
    SkinDefinition,
    load_appearance_definitions,
    load_skin_definitions,
)
from eral.content.stat_axes import StatAxisCatalog, load_stat_axis_catalog
from eral.content.tw_axis_registry import TwAxisRegistry, load_tw_axis_registry
from eral.content.work_schedules import WorkScheduleDefinition, load_work_schedule_definitions
from eral.content.maxbase import load_maxbase
from eral.content.palamlv import load_curves
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
from eral.systems.calendar import CalendarService, CalendarViewService
from eral.systems.companions import CompanionService
from eral.systems.commissions import CommissionService
from eral.systems.dates import DateService
from eral.systems.dialogue import DialogueService
from eral.systems.distribution import DistributionService
from eral.systems.events import EventService
from eral.systems.facilities import FacilityService
from eral.systems.game_loop import GameLoop
from eral.systems.navigation import NavigationService
from eral.systems.relationships import RelationshipService
from eral.systems.shop import ShopService
from eral.systems.skins import SkinService
from eral.systems.resolution import ResolutionService
from eral.systems.schedule import ScheduleService
from eral.systems.scene import SceneService
from eral.systems.save import SaveService
from eral.systems.wallet import WalletService
from eral.systems.settlement import SettlementService
from eral.systems.time_service import TimeService
from eral.systems.training import TrainingService
from eral.systems.weather import WeatherService
from eral.systems.palam_decay import load_palam_decay_rules
from eral.content.weather import load_weather_definitions


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
    skin_definitions: tuple[SkinDefinition, ...]
    appearance_definitions: dict[str, AppearanceDefinition]
    calendar_definition: CalendarDefinition
    work_schedules: tuple[WorkScheduleDefinition, ...]
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
    distribution_service: DistributionService
    schedule_service: ScheduleService
    save_service: SaveService
    vital_service: VitalService
    wallet_service: WalletService
    shop_service: ShopService
    skin_service: SkinService
    commission_service: CommissionService
    abl_upgrade_config: AblUpgradeConfig
    facility_service: FacilityService
    runtime_logger: RuntimeLogger
    time_service: TimeService
    calendar_service: CalendarService
    calendar_view_service: CalendarViewService
    training_service: TrainingService
    weather_service: WeatherService


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
    shopfronts_path = root_path / "data" / "base" / "shopfronts.toml"
    skins_path = root_path / "data" / "base" / "skins.toml"
    appearances_path = root_path / "data" / "base" / "appearances.toml"
    calendar_path = root_path / "data" / "base" / "calendar.toml"
    work_schedules_path = root_path / "data" / "base" / "work_schedules.toml"
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
    shopfronts = load_shopfront_definitions(shopfronts_path)
    skin_definitions = load_skin_definitions(skins_path)
    appearance_definitions = {
        appearance.key: appearance
        for appearance in load_appearance_definitions(appearances_path)
    }
    calendar_definition = load_calendar_definition(calendar_path)
    work_schedules = load_work_schedule_definitions(work_schedules_path)
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
    time_service = TimeService()
    curve_set = load_curves(root_path / "data" / "base" / "palamlv_curves.toml")
    training_service = TrainingService(palam_curve=curve_set.palam_curve)
    weather_definitions = load_weather_definitions(root_path / "data" / "base" / "weather.toml")
    weather_service = WeatherService(definitions=weather_definitions)
    calendar_service = CalendarService(calendar_definition=calendar_definition)
    skin_service = SkinService(
        skin_definitions={skin.key: skin for skin in skin_definitions},
        appearance_definitions=appearance_definitions,
    )

    season_month_map: dict[int, str] = {}
    for season in calendar_definition.seasons:
        for month in season.months:
            season_month_map[month] = season.key

    world = WorldState(
        current_day=1,
        current_time_slot=TimeSlot.from_name(config.start_time_slot),
        current_year=1,
        current_month=1,
        current_weekday="mon",
        current_hour=8,
        current_minute=0,
        player_name=config.player_name,
        active_location=PortLocation(
            key=start_location.key,
            display_name=start_location.display_name,
        ),
        characters=[],
        season_month_map=season_month_map,
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
        skin_service.ensure_default_skin_state(actor)
        actor.hydrate_runtime_fields_from_compat()
        actor.sync_compat_from_runtime()

    palam_decay_rules = load_palam_decay_rules(root_path / "data" / "base" / "palam_decay.toml")

    game_loop = GameLoop(
        event_bus=event_bus,
        schedule_service=schedule_service,
        vital_service=None,
        runtime_logger=runtime_logger,
        time_service=time_service,
        weather_service=weather_service,
        palam_decay_rules=palam_decay_rules,
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
    scene_service = SceneService(skin_service=skin_service)
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
        skin_service=skin_service,
        time_service=time_service,
        distribution_service=None,
        training_service=training_service,
    )
    shop_service = ShopService(
        item_definitions={item.key: item for item in items},
        shopfront_definitions={shop.key: shop for shop in shopfronts},
    )
    navigation_service = NavigationService(
        port_map=port_map,
        companion_service=companion_service,
        distribution_service=None,
        event_bus=event_bus,
        runtime_logger=runtime_logger,
        time_service=time_service,
    )
    distribution_service = DistributionService(
        roster={character.key: character for character in roster},
        port_map=port_map,
        work_schedules=work_schedules,
        calendar_service=calendar_service,
        companion_service=companion_service,
    )
    command_service.distribution_service = distribution_service
    navigation_service.distribution_service = distribution_service
    game_loop.distribution_service = distribution_service
    distribution_service.refresh_world(world)
    relationship_service.refresh_world(world)
    companion_service.refresh_world(world)
    date_service.refresh_world(world)
    calendar_view_service = CalendarViewService(
        calendar_service=calendar_service,
        work_schedules=work_schedules,
        actor_names={character.key: character.display_name for character in roster},
        location_names={location.key: location.display_name for location in port_map.locations},
    )
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
        skin_definitions=skin_definitions,
        appearance_definitions=appearance_definitions,
        calendar_definition=calendar_definition,
        work_schedules=work_schedules,
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
        distribution_service=distribution_service,
        schedule_service=schedule_service,
        save_service=save_service,
        vital_service=vital_service,
        wallet_service=wallet_service,
        shop_service=shop_service,
        skin_service=skin_service,
        commission_service=commission_service,
        abl_upgrade_config=abl_upgrade_config,
        facility_service=facility_service,
        runtime_logger=runtime_logger,
        time_service=time_service,
        calendar_service=calendar_service,
        calendar_view_service=calendar_view_service,
        training_service=training_service,
        weather_service=weather_service,
    )
