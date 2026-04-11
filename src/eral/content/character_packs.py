"""Character pack discovery for stage-two content loading."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from eral.content.characters import CharacterDefinition, InitialStatOverrides, _parse_initial_stats
from eral.content.dialogue import DialogueEntry, load_dialogue_entries
from eral.content.events import EventDefinition, load_event_definitions


@dataclass(frozen=True, slots=True)
class CharacterPack:
    """Fully loaded character pack content."""

    character: CharacterDefinition
    events: tuple[EventDefinition, ...]
    dialogue: tuple[DialogueEntry, ...]


def load_character_packs(path: Path) -> tuple[CharacterPack, ...]:
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
        character = _load_character_file(character_file)
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


def _load_character_file(path: Path) -> CharacterDefinition:
    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return CharacterDefinition(
        key=raw_data["key"],
        display_name=raw_data["display_name"],
        tags=tuple(raw_data.get("tags", [])),
        initial_location=raw_data["initial_location"],
        schedule={str(key): str(value) for key, value in raw_data.get("schedule", {}).items()},
        initial_stats=_parse_initial_stats(raw_data.get("initial_stats")),
    )
