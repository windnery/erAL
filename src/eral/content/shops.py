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

    if not path.exists():
        return ()

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        ShopfrontDefinition(
            key=item["key"],
            display_name=item["display_name"],
            item_categories=tuple(item.get("item_categories", [])),
        )
        for item in raw_data.get("shopfronts", [])
    )
