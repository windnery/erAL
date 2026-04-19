"""Load persistent state and body slot definitions from TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path

from eral.domain.persistent import PersistentStateDefinition, SlotDefinition


def load_slot_definitions(path: Path) -> tuple[SlotDefinition, ...]:
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return tuple(
        SlotDefinition(
            key=item["key"],
            display_name=item["display_name"],
            capacity=int(item.get("capacity", 1)),
            blocked_by=tuple(str(v) for v in item.get("blocked_by", [])),
        )
        for item in raw.get("slots", [])
    )


def load_persistent_state_definitions(path: Path) -> tuple[PersistentStateDefinition, ...]:
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return tuple(
        PersistentStateDefinition(
            key=item["key"],
            display_name=item["display_name"],
            occupies_slots=tuple(str(v) for v in item.get("occupies_slots", [])),
            source_per_turn={str(k): int(v) for k, v in item.get("source_per_turn", {}).items()},
            clear_on=tuple(str(v) for v in item.get("clear_on", [])),
        )
        for item in raw.get("persistent_states", [])
    )
