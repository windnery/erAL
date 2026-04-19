"""Food preferences — tagged liked/disliked structures for culinary interactions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FoodPreferences:
    """Tagged culinary preferences mirroring the gift preference model."""

    liked_tags: tuple[str, ...] = ()
    disliked_tags: tuple[str, ...] = ()

    def preference_multiplier(self, tags: tuple[str, ...]) -> float:
        if any(tag in self.liked_tags for tag in tags):
            return 2.0
        if any(tag in self.disliked_tags for tag in tags):
            return 0.3
        return 1.0


def load_food_preferences(raw: dict | None) -> FoodPreferences:
    if raw is None:
        return FoodPreferences()
    return FoodPreferences(
        liked_tags=tuple(str(v) for v in raw.get("liked_tags", [])),
        disliked_tags=tuple(str(v) for v in raw.get("disliked_tags", [])),
    )
