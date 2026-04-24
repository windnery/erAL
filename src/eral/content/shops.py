"""Load shopfront definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ShopfrontDefinition:
    """Static shopfront metadata."""

    key: str
    display_name: str
    item_categories: tuple[str, ...]


def load_shopfront_definitions(path: Path) -> tuple[ShopfrontDefinition, ...]:
    """Load shopfront definitions from TOML."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        ShopfrontDefinition(
            key=str(shopfront.get("key", shopfront["index"])),
            display_name=shopfront["display_name"],
            item_categories=tuple(shopfront.get("item_categories", [])),
        )
        for shopfront in raw_data.get("shopfronts", [])
    )
