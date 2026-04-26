"""Dependency assembly for the erAL runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eral.app.config import AppConfig
from eral.content.abl_upgrade import AblUpgradeConfig, load_abl_upgrade_config
from eral.content.calendar import CalendarDefinition, load_calendar_definition
from eral.content.commissions import CommissionDefinition, load_commission_definitions
from eral.content.character_packs import CharacterPack, load_character_packs
from eral.content.character_relations import CharacterRelationIndex, load_character_relations
from eral.content.characters import CharacterDefinition, InitialStatOverrides, load_character_definitions
from eral.content.command_effects import load_command_effects
from eral.content.commands import CommandDefinition, load_command_definitions
from eral.content.dialogue import DialogueEntry, load_dialogue_entries
from eral.content.events import EventDefinition, load_event_definitions
from eral.content.items import ItemDefinition, load_item_definitions
from eral.content.facilities import FacilityDefinition, load_facility_definitions
from eral.content.marks import MarkDefinition, load_mark_definitions
from eral.content.port_map import load_port_map
from eral.content.relationships import RelationshipStageDefinition, load_relationship_stages
from eral.content.settlement import SettlementRule, load_settlement_rules
from eral.content.source_extra import load_source_extra_modifiers
from eral.content.source_modifiers import load_source_cbva_rules
from eral.content.skins import (
    AppearanceDefinition,
    SkinDefinition,
    load_appearance_definitions,
    load_skin_definitions,
)
from eral.content.stat_axes import StatAxisCatalog, load_stat_axis_catalog
from eral.content.work_schedules import WorkScheduleDefinition, load_work_schedule_definitions
from eral.content.palamlv import load_curves, load_palam_to_juel_rules
from eral.content.persistent import load_persistent_state_definitions, load_slot_definitions
from eral.content.gifts import load_gift_definitions
from eral.content.ambient_events import load_ambient_events
from eral.domain.persistent import PersistentStateDefinition, SlotDefinition
from eral.systems.gifts import GiftService
from eral.systems.vital import VitalService
from eral.content.imprint import load_imprint_thresholds
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
from eral.systems.ejaculation import EjaculationService
from eral.systems.ambient_events import AmbientEventService
from eral.content.weather import load_weather_definitions


@dataclass(slots=True)
class Application:
    """The assembled application container."""

    root: Path
    config: AppConfig
    paths: RuntimePaths
    stat_axes: StatAxisCatalog
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
    character_relations: CharacterRelationIndex
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
    ejaculation_service: EjaculationService
    ambient_event_service: AmbientEventService


def _apply_initial_stats(stats: ActorNumericState, overrides: "InitialStatOverrides") -> None:
    """Apply per-character initial stat overrides after zeroing."""
    for key, value in overrides.base.items():
        stats.base.set(key, value)
    for key, value in overrides.palam.items():
        stats.palam.set(key, value)
    for key, value in overrides.juel.items():
        stats.juel.set(key, value)
    for key, value in overrides.exp.items():
        stats.exp.set(key, value)
    for era_index, value in overrides.abl.items():
        stats.compat.abl.set(era_index, value)
    for era_index, value in overrides.talent.items():
        stats.compat.talent.set(era_index, value)
    for era_index, value in overrides.cflag.items():
        stats.compat.cflag.set(era_index, value)


def _default_vital_caps() -> dict[str, int]:
    return {
        "stamina": 2000,
        "spirit": 1500,
        "reason": 1000,
        "semen": 1000,
    }


def _default_vital_recover_rates() -> dict[str, int]:
    return {
        "stamina": 10,
        "spirit": 10,
        "reason": 0,
        "semen": 0,
    }


def create_application(root: Path | None = None) -> Application:
    root_path = (root or Path.cwd()).resolve()
    config_path = root_path / "config.ini"
    stat_axes_path = root_path / "data" / "base" / "axes"
    port_map_path = root_path / "data" / "base" / "system" / "port_map.toml"
    characters_path = root_path / "data" / "base" / "characters.toml"
    character_packs_path = root_path / "data" / "base" / "characters"
    relationship_stages_path = root_path / "data" / "base" / "rules" / "relationship_stages.toml"
    cup_routing_path = root_path / "data" / "base" / "rules" / "cup_routing.toml"
    commands_path = root_path / "data" / "base" / "commands" / "train.toml"
    items_path = root_path / "data" / "base" / "shops" / "items.toml"
    calendar_path = root_path / "data" / "base" / "system" / "calendar.toml"
    marks_path = root_path / "data" / "base" / "axes" / "marks.toml"
    abl_upgrade_path = root_path / "data" / "base" / "rules" / "abl_upgrade.toml"
    commissions_path = root_path / "data" / "base" / "system" / "commissions.toml"
    facilities_path = root_path / "data" / "base" / "system" / "facilities.toml"

    events_path = root_path / "data" / "base" / "kojo" / "events.toml"
    dialogue_path = root_path / "data" / "base" / "kojo" / "dialogue.toml"

    paths = RuntimePaths.from_root(root_path)
    paths.ensure_runtime_dirs()

    config = AppConfig.load(config_path)
    stat_axes = load_stat_axis_catalog(stat_axes_path)
    port_map = load_port_map(port_map_path)
    mark_defs = load_mark_definitions(marks_path)
    character_packs = load_character_packs(
        character_packs_path,
        stat_axes=stat_axes,
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
    settlement_rules = load_settlement_rules(cup_routing_path)
    source_cbva_rules = load_source_cbva_rules(
        root_path / "data" / "base" / "rules" / "source_cbva.toml"
    )
    source_extra_modifiers = load_source_extra_modifiers(
        root_path / "data" / "base" / "rules" / "source_extra.toml"
    )
    commands = load_command_definitions(commands_path)
    command_effects = load_command_effects(
        root_path / "data" / "base" / "effects" / "command_effects.toml"
    )
    items = load_item_definitions(items_path)
    # Global skins/appearances removed; per-character cloths/skins live in
    # character pack directories and will be loaded by the content author.
    skin_definitions: tuple = ()
    appearance_definitions: dict = {}
    calendar_definition = load_calendar_definition(calendar_path)
    # Global work_schedules removed; per-character schedules live in character packs.
    work_schedules: tuple = ()
    # character_relations removed; will be per-character if reintroduced.
    character_relations = None
    abl_upgrade_config = load_abl_upgrade_config(abl_upgrade_path)
    commission_defs = load_commission_definitions(commissions_path)
    facility_defs = load_facility_definitions(facilities_path)
    mark_definitions = {m.key: m for m in mark_defs}
    mark_max_levels = {m.key: m.max_level for m in mark_defs}
    imprint_thresholds = load_imprint_thresholds(marks_path)
    imprint_service = ImprintService(imprint_thresholds)
    favor_formula = load_growth_formula(root_path / "data" / "base" / "rules" / "relationship_growth.toml")
    trust_formula = load_trust_formula(root_path / "data" / "base" / "rules" / "relationship_growth.toml")
    start_location = port_map.starting_location()
    event_bus = EventBus()
    runtime_logger = RuntimeLogger(paths=paths)
    time_service = TimeService()
    palam_curve = load_curves(root_path / "data" / "base" / "rules" / "palamlv_curves.toml")
    palam_to_juel_rules = load_palam_to_juel_rules(root_path / "data" / "base" / "rules" / "palam_to_juel.toml")
    training_service = TrainingService(palam_curve=palam_curve)
    weather_definitions = load_weather_definitions(root_path / "data" / "base" / "axes" / "weather.toml")
    weather_service = WeatherService(definitions=weather_definitions)
    calendar_service = CalendarService(calendar_definition=calendar_definition)
    skin_service = SkinService(
        skin_definitions={skin.key: skin for skin in skin_definitions},
        appearance_definitions=appearance_definitions,
    )
    # TODO: wire per-character cloths/skins from character packs once format
    # stabilises (content author is iterating on laffey/cloths.toml).

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
        player_gender=config.player_gender,
        active_location=PortLocation(
            key=start_location.key,
            display_name=start_location.display_name,
        ),
        characters=[],
        season_month_map=season_month_map,
    )
    # 玩家自身的数值状态（体力/气力/精液/兴奋等），供 Web UI 与指令系统读取。
    world.player_stats = ActorNumericState.zeroed(stat_axes)
    # 玩家默认体力/气力满：玩家当前仍使用内置默认上限。
    world.player_stats.base.set("0", 2000)
    world.player_stats.base.set("1", 1500)
    world.player_stats.base.set("11", 1000)
    if config.player_gender == "male":
        world.player_stats.base.set("6", 1000)
    schedule_service = ScheduleService(roster={character.key: character for character in roster})
    for definition in roster:
        stats = ActorNumericState.zeroed(stat_axes)
        _apply_initial_stats(stats, definition.initial_stats)
        world.characters.append(
            CharacterState(
                key=definition.key,
                display_name=definition.display_name,
                location_key=definition.initial_location,
                base_caps=dict(definition.initial_stats.base_caps),
                base_recover_rates=dict(definition.initial_stats.base_recover_rates),
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

    palam_decay_rules = load_palam_decay_rules(root_path / "data" / "base" / "rules" / "palam_decay.toml")

    gift_definitions = load_gift_definitions(root_path / "data" / "base" / "shops" / "gifts.toml")
    gift_service = GiftService(
        gift_definitions={g.key: g for g in gift_definitions},
        character_preferences={c.key: c.gift_preferences for c in roster},
    )
    ejaculation_service = EjaculationService()
    ambient_events = load_ambient_events(root_path / "data" / "base" / "ambient_events.toml")
    ambient_event_service = AmbientEventService(definitions=ambient_events, port_map=port_map)

    game_loop = GameLoop(
        event_bus=event_bus,
        schedule_service=schedule_service,
        vital_service=None,
        runtime_logger=runtime_logger,
        time_service=time_service,
        weather_service=weather_service,
        palam_decay_rules=palam_decay_rules,
        ambient_event_service=ambient_event_service,
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
        palam_to_juel_rules=palam_to_juel_rules,
        source_modifiers=source_cbva_rules,
        source_extra_modifiers=source_extra_modifiers,
        relationship_service=relationship_service,
        imprint_check=imprint_service,
        mark_max_levels=mark_max_levels,
        favor_formula=favor_formula,
        trust_formula=trust_formula,
        abl_upgrade_config=abl_upgrade_config,
        facility_service=facility_service,
    )
    scene_service = SceneService(skin_service=skin_service)
    event_service = EventService(events=events, relationship_service=relationship_service)
    dialogue_service = DialogueService(entries=dialogue)
    resolution_service = ResolutionService()
    vital_service = VitalService(
        max_values=_default_vital_caps(),
        recover_rates=_default_vital_recover_rates(),
        facility_service=facility_service,
    )
    shop_service = ShopService(
        item_definitions={item.key: item for item in items},
    )
    navigation_service = NavigationService(
        port_map=port_map,
        companion_service=companion_service,
        distribution_service=None,
        event_bus=event_bus,
        runtime_logger=runtime_logger,
        time_service=time_service,
    )
    command_service = CommandService(
        commands={command.index: command for command in commands},
        item_definitions={item.key: item for item in items},
        command_effects=command_effects,
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
        game_loop=game_loop,
        wallet_service=wallet_service,
        facility_service=facility_service,
        resolution_service=resolution_service,
        skin_service=skin_service,
        time_service=time_service,
        distribution_service=None,
        training_service=training_service,
        gift_service=gift_service,
        ejaculation_service=ejaculation_service,
        shop_service=shop_service,
        navigation_service=navigation_service,
        stat_axes=stat_axes,
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
        character_relations=character_relations,
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
        ejaculation_service=ejaculation_service,
        ambient_event_service=ambient_event_service,
    )
