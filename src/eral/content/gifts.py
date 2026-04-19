"""Load gift definitions and manage gift preferences."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GiftDefinition:
    key: str
    display_name: str
    tags: tuple[str, ...]
    price: int


@dataclass(frozen=True, slots=True)
class GiftPreferences:
    liked_tags: tuple[str, ...] = ()
    disliked_tags: tuple[str, ...] = ()

    def preference_multiplier(self, gift: GiftDefinition) -> float:
        if any(tag in self.liked_tags for tag in gift.tags):
            return 2.0
        if any(tag in self.disliked_tags for tag in gift.tags):
            return 0.3
        return 1.0


def load_gift_definitions(path: Path) -> tuple[GiftDefinition, ...]:
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return tuple(
        GiftDefinition(
            key=item["key"],
            display_name=item["display_name"],
            tags=tuple(str(v) for v in item.get("tags", [])),
            price=int(item.get("price", 0)),
        )
        for item in raw.get("gifts", [])
    )


def load_gift_preferences(raw: dict | None) -> GiftPreferences:
    if raw is None:
        return GiftPreferences()
    return GiftPreferences(
        liked_tags=tuple(str(v) for v in raw.get("liked_tags", [])),
        disliked_tags=tuple(str(v) for v in raw.get("disliked_tags", [])),
    )
