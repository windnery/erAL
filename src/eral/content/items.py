"""Load static item catalog definitions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ItemDefinition:
    """Static item metadata."""

    key: str
    display_name: str


def load_item_definitions(path: Path) -> tuple[ItemDefinition, ...]:
    """Load item definitions from TOML."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        ItemDefinition(
            key=item["key"],
            display_name=item["display_name"],
        )
        for item in raw_data.get("items", [])
    )
