"""Gift preference resolution and SOURCE calculation."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.gifts import GiftDefinition, GiftPreferences


@dataclass(slots=True)
class GiftService:
    gift_definitions: dict[str, GiftDefinition]
    character_preferences: dict[str, GiftPreferences]

    def best_gift_in_inventory(
        self,
        inventory: dict[str, int],
    ) -> str | None:
        for gift_key in sorted(
            self.gift_definitions.keys(),
            key=lambda k: self.gift_definitions[k].price,
            reverse=True,
        ):
            if inventory.get(gift_key, 0) > 0:
                return gift_key
        return None

    def preference_multiplier(self, actor_key: str, gift_key: str) -> float:
        prefs = self.character_preferences.get(actor_key)
        if prefs is None:
            return 1.0
        gift_def = self.gift_definitions.get(gift_key)
        if gift_def is None:
            return 1.0
        return prefs.preference_multiplier(gift_def)

    def apply_gift_source(
        self,
        base_source: dict[str, int],
        multiplier: float,
    ) -> dict[str, int]:
        return {k: int(v * multiplier) for k, v in base_source.items()}
