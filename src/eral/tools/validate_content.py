"""Validate character packs against current command/map content."""

from __future__ import annotations

import argparse
from pathlib import Path

from eral.content.character_packs import load_character_packs
from eral.content.commands import load_command_definitions
from eral.content.port_map import load_port_map

MIN_EVENTS_PER_PACK = 4
MIN_DIALOGUE_PER_PACK = 8


def validate_content(root: Path) -> list[str]:
    """Return validation error messages for current content packs."""

    errors: list[str] = []
    commands = {
        command.key for command in load_command_definitions(root / "data" / "base" / "commands.toml")
    }
    port_map = load_port_map(root / "data" / "base" / "port_map.toml")
    location_keys = {location.key for location in port_map.locations}

    for pack in load_character_packs(root / "data" / "base" / "characters"):
        character = pack.character

        if character.initial_location not in location_keys:
            errors.append(
                f"{character.key}: initial_location '{character.initial_location}' does not exist"
            )

        if len(pack.events) < MIN_EVENTS_PER_PACK:
            errors.append(
                f"{character.key}: 事件数量不足（当前 {len(pack.events)}，至少需要 {MIN_EVENTS_PER_PACK}）"
            )

        if len(pack.dialogue) < MIN_DIALOGUE_PER_PACK:
            errors.append(
                f"{character.key}: 对话数量不足（当前 {len(pack.dialogue)}，至少需要 {MIN_DIALOGUE_PER_PACK}）"
            )

        for slot, location_key in character.schedule.items():
            if location_key not in location_keys:
                errors.append(
                    f"{character.key}: schedule[{slot}] points to unknown location '{location_key}'"
                )

        for event in pack.events:
            if event.action_key not in commands:
                errors.append(
                    f"{character.key}: event '{event.key}' references unknown action '{event.action_key}'"
                )
            for location_key in event.location_keys:
                if location_key not in location_keys:
                    errors.append(
                        f"{character.key}: event '{event.key}' references unknown location '{location_key}'"
                    )

        for entry in pack.dialogue:
            if entry.actor_key != character.key:
                errors.append(
                    f"{character.key}: dialogue '{entry.key}' actor_key must equal '{character.key}'"
                )
            if not entry.lines:
                errors.append(f"{character.key}: dialogue '{entry.key}' has no lines")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate erAL content packs.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing data/base.",
    )
    args = parser.parse_args()

    errors = validate_content(args.root.resolve())
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)

    print("content validation ok")


if __name__ == "__main__":
    main()
