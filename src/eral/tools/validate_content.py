"""Validate character packs against current command/map content."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import tomllib

from eral.content.character_packs import CharacterPack, load_character_packs
from eral.content.commands import (
    SUPPORTED_OPERATIONS,
    SUPPORTED_TARGET_MODES,
    load_command_definitions,
)
from eral.content.dialogue import load_dialogue_entries
from eral.content.events import load_event_definitions
from eral.content.marks import load_mark_definitions
from eral.content.port_map import load_port_map
from eral.content.stat_axes import load_stat_axis_catalog

MIN_EVENTS_PER_PACK = 4
MIN_DIALOGUE_PER_PACK = 8


@dataclass(frozen=True, slots=True)
class ContentPackStat:
    character_key: str
    display_name: str
    event_count: int
    dialogue_count: int
    event_gap: int
    dialogue_gap: int


def _load_packs(root: Path) -> tuple[CharacterPack, ...]:
    stat_axes = load_stat_axis_catalog(root / "data" / "base" / "axes")
    mark_keys = {
        mark.key for mark in load_mark_definitions(root / "data" / "base" / "axes" / "marks.toml")
    }
    return load_character_packs(
        root / "data" / "base" / "characters",
        stat_axes=stat_axes,
        mark_keys=mark_keys,
    )


def collect_content_stats(root: Path) -> tuple[ContentPackStat, ...]:
    stats: list[ContentPackStat] = []
    for pack in _load_packs(root):
        stats.append(
            ContentPackStat(
                character_key=pack.character.key,
                display_name=pack.character.display_name,
                event_count=len(pack.events),
                dialogue_count=len(pack.dialogue),
                event_gap=max(0, MIN_EVENTS_PER_PACK - len(pack.events)),
                dialogue_gap=max(0, MIN_DIALOGUE_PER_PACK - len(pack.dialogue)),
            )
        )
    return tuple(stats)


def render_content_report(stats: tuple[ContentPackStat, ...]) -> str:
    lines = ["content density report:"]
    for item in stats:
        status_parts: list[str] = []
        if item.event_gap:
            status_parts.append(f"event_gap={item.event_gap}")
        if item.dialogue_gap:
            status_parts.append(f"dialogue_gap={item.dialogue_gap}")
        status = ", ".join(status_parts) if status_parts else "ok"
        lines.append(
            f"- {item.character_key} ({item.display_name}): events={item.event_count}, dialogue={item.dialogue_count}, status={status}"
        )
    return "\n".join(lines)


def validate_commands(root: Path) -> list[str]:
    """Return validation error messages for train.toml command definitions."""

    errors: list[str] = []
    commands_path = root / "data" / "base" / "commands" / "train.toml"
    if not commands_path.exists():
        return [f"train.toml not found at {commands_path}"]
    with commands_path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    known_fields = {
        "index", "label", "category", "location_tags", "time_slots",
        "min_affection", "min_trust", "min_obedience", "required_stage",
        "operation", "requires_following", "requires_date",
        "required_removed_slots", "training_position_keys",
        "required_conditions", "forbidden_conditions",
        "required_marks", "apply_marks", "remove_marks",
        "success_tiers", "required_items",
        "resolution_key", "shopfront_key", "required_actor_tags",
        "personal_income", "elapsed_minutes", "target_mode",
        "activates_persistent_state", "blocked_by_persistent_states",
    }
    seen_indices: set[int] = set()

    if "train" not in raw_data:
        return [f"train.toml missing [[train]] entries at {commands_path}"]

    for item in raw_data.get("train", []):
        if "index" not in item:
            errors.append("train.toml: entry missing 'index' field")
            continue
        index = int(item["index"])
        if index in seen_indices:
            errors.append(f"train.toml: duplicate index '{index}'")
        seen_indices.add(index)

        if "label" not in item:
            errors.append(f"train.toml: '{index}' missing 'label'")

        unknown = set(item.keys()) - known_fields
        if unknown:
            errors.append(f"train.toml: '{index}' has unknown fields: {', '.join(sorted(unknown))}")

        target_mode = str(item.get("target_mode", "actor"))
        if target_mode not in SUPPORTED_TARGET_MODES:
            errors.append(
                f"train.toml: '{index}' has invalid target_mode '{target_mode}'"
            )
        operation = item.get("operation")
        if operation is not None and str(operation) not in SUPPORTED_OPERATIONS:
            errors.append(
                f"train.toml: '{index}' has unsupported operation '{operation}'"
            )

    return errors


def validate_command_effects(root: Path) -> list[str]:
    """Return validation error messages for command_effects.toml."""

    errors: list[str] = []
    path = root / "data" / "base" / "effects" / "command_effects.toml"
    if not path.exists():
        return []

    commands_path = root / "data" / "base" / "commands" / "train.toml"
    with commands_path.open("rb") as handle:
        commands_raw = tomllib.load(handle)
    known_command_indices = {
        int(item["index"]) for item in commands_raw.get("train", []) if "index" in item
    }

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    known_effect_fields = {
        "command_index", "source", "vitals", "experience", "conditions",
    }
    known_pair_fields = {"target", "player"}
    seen_indices: set[int] = set()

    for item in raw_data.get("effect", []):
        if "command_index" not in item:
            errors.append("command_effects.toml: effect missing 'command_index'")
            continue
        index = int(item["command_index"])
        if index in seen_indices:
            errors.append(f"command_effects.toml: duplicate command_index '{index}'")
        seen_indices.add(index)
        if index not in known_command_indices:
            errors.append(
                f"command_effects.toml: unknown command_index '{index}' (not found in train.toml)"
            )

        unknown = set(item.keys()) - known_effect_fields
        if unknown:
            errors.append(
                f"command_effects.toml: '{index}' has unknown fields: {', '.join(sorted(unknown))}"
            )

        raw_source = item.get("source", {})
        if not isinstance(raw_source, dict):
            errors.append(f"command_effects.toml: '{index}' source must be a table")
        else:
            bad_source_keys = set(raw_source.keys()) - known_pair_fields
            if bad_source_keys:
                errors.append(
                    f"command_effects.toml: '{index}' source has unknown fields: {', '.join(sorted(bad_source_keys))}"
                )

        raw_vitals = item.get("vitals", {})
        if raw_vitals and not isinstance(raw_vitals, dict):
            errors.append(f"command_effects.toml: '{index}' vitals must be a table")
        elif isinstance(raw_vitals, dict):
            bad_vitals_keys = set(raw_vitals.keys()) - known_pair_fields
            if bad_vitals_keys:
                errors.append(
                    f"command_effects.toml: '{index}' vitals has unknown fields: {', '.join(sorted(bad_vitals_keys))}"
                )

        raw_exp = item.get("experience", {})
        if raw_exp and not isinstance(raw_exp, dict):
            errors.append(f"command_effects.toml: '{index}' experience must be a table")
        elif isinstance(raw_exp, dict):
            bad_exp_keys = set(raw_exp.keys()) - known_pair_fields
            if bad_exp_keys:
                errors.append(
                    f"command_effects.toml: '{index}' experience has unknown fields: {', '.join(sorted(bad_exp_keys))}"
                )

        raw_conditions = item.get("conditions", {})
        if raw_conditions and not isinstance(raw_conditions, dict):
            errors.append(f"command_effects.toml: '{index}' conditions must be a table")
        elif isinstance(raw_conditions, dict):
            bad_condition_keys = set(raw_conditions.keys()) - {"target", "player", "world"}
            if bad_condition_keys:
                errors.append(
                    f"command_effects.toml: '{index}' conditions has unknown fields: {', '.join(sorted(bad_condition_keys))}"
                )

    return errors


def validate_content(root: Path) -> list[str]:
    """Return validation error messages for current content packs."""

    errors: list[str] = []
    errors.extend(validate_commands(root))
    errors.extend(validate_command_effects(root))
    commands = {
        command.key
        for command in load_command_definitions(
            root / "data" / "base" / "commands" / "train.toml"
        )
    }
    port_map = load_port_map(root / "data" / "base" / "port_map.toml")
    location_keys = {location.key for location in port_map.locations}
    area_keys = {area.key for area in port_map.areas}
    sub_area_keys = {sub_area.key for sub_area in port_map.sub_areas}
    packs = _load_packs(root)
    character_keys = {pack.character.key for pack in packs}

    for pack in packs:
        character = pack.character

        if character.initial_location not in location_keys:
            errors.append(
                f"{character.key}: initial_location '{character.initial_location}' does not exist"
            )
        if not character.faction_key:
            errors.append(f"{character.key}: missing faction_key")
        if not character.residence_area_key:
            errors.append(f"{character.key}: missing residence_area_key")
        elif character.residence_area_key not in area_keys:
            errors.append(
                f"{character.key}: residence_area_key '{character.residence_area_key}' does not exist"
            )
        if not character.dorm_group_key:
            errors.append(f"{character.key}: missing dorm_group_key")
        elif character.dorm_group_key not in sub_area_keys:
            errors.append(
                f"{character.key}: dorm_group_key '{character.dorm_group_key}' does not exist"
            )
        if not character.home_location_key:
            errors.append(f"{character.key}: missing home_location_key")
        elif character.home_location_key not in location_keys:
            errors.append(
                f"{character.key}: home_location_key '{character.home_location_key}' does not exist"
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
            for location_key in entry.location_keys:
                if location_key not in location_keys:
                    errors.append(
                        f"{character.key}: dialogue '{entry.key}' references unknown location '{location_key}'"
                    )

    for event in load_event_definitions(root / "data" / "base" / "kojo" / "events.toml"):
        if event.action_key not in commands:
            errors.append(
                f"global: event '{event.key}' references unknown action '{event.action_key}'"
            )
        for location_key in event.location_keys:
            if location_key not in location_keys:
                errors.append(
                    f"global: event '{event.key}' references unknown location '{location_key}'"
                )

    for entry in load_dialogue_entries(root / "data" / "base" / "kojo" / "dialogue.toml"):
        if entry.actor_key != "_any" and entry.actor_key not in character_keys:
            errors.append(
                f"global: dialogue '{entry.key}' references unknown actor '{entry.actor_key}'"
            )
        for location_key in entry.location_keys:
            if location_key not in location_keys:
                errors.append(
                    f"global: dialogue '{entry.key}' references unknown location '{location_key}'"
                )

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
    print(render_content_report(collect_content_stats(args.root.resolve())))


if __name__ == "__main__":
    main()
