"""Static content registration layer."""

from .abl_upgrade import AblDefinition, AblUpgradeConfig, load_abl_upgrade_config
from .characters import CharacterDefinition, InitialStatOverrides, load_character_definitions
from .character_packs import CharacterPack, load_character_packs
from .commands import CommandDefinition, load_command_definitions
from .dialogue import DialogueEntry, load_dialogue_entries
from .events import EventDefinition, load_event_definitions
from .marks import MarkDefinition, load_mark_definitions
from .port_map import load_port_map
from .relationships import RelationshipStageDefinition, load_relationship_stages
from .settlement import SettlementRule, load_settlement_rules
from .stat_axes import AxisFamily, StatAxis, StatAxisCatalog, load_stat_axis_catalog
from .tw_axis_registry import TwAxisEntry, TwAxisRegistry, load_tw_axis_registry

__all__ = [
    "AblDefinition",
    "AblUpgradeConfig",
    "AxisFamily",
    "CharacterPack",
    "CharacterDefinition",
    "CommandDefinition",
    "DialogueEntry",
    "EventDefinition",
    "MarkDefinition",
    "RelationshipStageDefinition",
    "SettlementRule",
    "StatAxis",
    "StatAxisCatalog",
    "TwAxisEntry",
    "TwAxisRegistry",
    "load_abl_upgrade_config",
    "load_character_definitions",
    "load_character_packs",
    "load_command_definitions",
    "load_dialogue_entries",
    "load_event_definitions",
    "load_mark_definitions",
    "load_port_map",
    "load_relationship_stages",
    "load_settlement_rules",
    "load_stat_axis_catalog",
    "load_tw_axis_registry",
]
