"""Load skin and appearance definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SkinDefinition:
    """Static skin metadata for a specific actor."""

    key: str
    actor_key: str
    display_name: str
    price: int
    grant_mode: str
    shop_visibility: str
    tags: tuple[str, ...]
    appearance_key: str


@dataclass(frozen=True, slots=True)
class AppearanceDefinition:
    """Static appearance mapping for one equipped skin."""

    key: str
    portrait_key: str
    slots: dict[str, str]


def load_skin_definitions(path: Path) -> tuple[SkinDefinition, ...]:
    """Load skin definitions from TOML."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        SkinDefinition(
            key=entry["key"],
            actor_key=entry["actor_key"],
            display_name=entry["display_name"],
            price=int(entry.get("price", 0)),
            grant_mode=str(entry["grant_mode"]),
            shop_visibility=str(entry["shop_visibility"]),
            tags=tuple(str(tag) for tag in entry.get("tags", [])),
            appearance_key=str(entry["appearance_key"]),
        )
        for entry in raw_data.get("skins", [])
    )


def load_appearance_definitions(path: Path) -> tuple[AppearanceDefinition, ...]:
    """Load appearance definitions from TOML."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        AppearanceDefinition(
            key=entry["key"],
            portrait_key=str(entry.get("portrait_key", "")),
            slots={str(slot): str(value) for slot, value in entry.get("slots", {}).items()},
        )
        for entry in raw_data.get("appearances", [])
    )
