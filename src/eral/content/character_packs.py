"""Character pack discovery for stage-two content loading."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from eral.content.character_stats import load_split_initial_stats
from eral.content.characters import CharacterDefinition, InitialStatOverrides, _parse_initial_stats
from eral.content.dialogue import DialogueEntry, load_dialogue_entries
from eral.content.events import EventDefinition, load_event_definitions
from eral.content.gifts import load_gift_preferences
from eral.content.stat_axes import StatAxisCatalog
from eral.content.tw_axis_registry import TwAxisRegistry


@dataclass(frozen=True, slots=True)
class CharacterPack:
    """Fully loaded character pack content."""

    character: CharacterDefinition
    events: tuple[EventDefinition, ...]
    dialogue: tuple[DialogueEntry, ...]


def load_character_packs(
    path: Path,
    *,
    stat_axes: StatAxisCatalog | None = None,
    tw_axes: TwAxisRegistry | None = None,
    mark_keys: set[str] | None = None,
) -> tuple[CharacterPack, ...]:
    """Load character packs from directory entries."""

    if not path.exists():
        return ()

    packs: list[CharacterPack] = []
    for entry in sorted(path.iterdir()):
        if not entry.is_dir():
            continue
        character_file = entry / "character.toml"
        if not character_file.exists():
            continue
        initial_stats = None
        if stat_axes is not None and tw_axes is not None and mark_keys is not None:
            initial_stats = load_split_initial_stats(
                entry,
                stat_axes=stat_axes,
                tw_axes=tw_axes,
                mark_keys=mark_keys,
            )
        character = _load_character_file(character_file, initial_stats=initial_stats)
        events = (
            load_event_definitions(entry / "events.toml")
            if (entry / "events.toml").exists()
            else ()
        )
        dialogue = (
            load_dialogue_entries(entry / "dialogue.toml")
            if (entry / "dialogue.toml").exists()
            else ()
        )
        packs.append(CharacterPack(character=character, events=events, dialogue=dialogue))

    return tuple(packs)


def _load_character_file(
    path: Path,
    *,
    initial_stats: InitialStatOverrides | None = None,
) -> CharacterDefinition:
    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return CharacterDefinition(
        key=raw_data["key"],
        display_name=raw_data["display_name"],
        tags=tuple(raw_data.get("tags", [])),
        initial_location=raw_data["initial_location"],
        faction_key=str(raw_data.get("faction_key", "")),
        residence_area_key=str(raw_data.get("residence_area_key", "")),
        dorm_group_key=str(raw_data.get("dorm_group_key", "")),
        home_location_key=str(raw_data.get("home_location_key", "")),
        default_activity_tags=tuple(raw_data.get("default_activity_tags", [])),
        schedule={str(key): str(value) for key, value in raw_data.get("schedule", {}).items()},
        initial_stats=initial_stats or _parse_initial_stats(raw_data.get("initial_stats")),
        gift_preferences=load_gift_preferences(raw_data.get("gift_preferences")),
    )
