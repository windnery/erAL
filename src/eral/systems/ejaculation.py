"""Player-side ejaculation and character fluid response."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import CharacterState, WorldState

AROUSAL_KEY = "player_arousal"
EJACULATE_INSIDE_KEY = "ejaculate_inside"
AROUSAL_THRESHOLD = 100
DEFAULT_AROUSAL_GAIN = 20
INSERTED_STATES = frozenset({"inserted_v", "inserted_a"})

TAG_EJACULATION_INSIDE = "player_ejaculation_inside"
TAG_EJACULATION_OUTSIDE = "player_ejaculation_outside"


@dataclass(slots=True)
class EjaculationService:
    """Track player arousal during insertion and fire ejaculation events."""

    threshold: int = AROUSAL_THRESHOLD
    default_gain: int = DEFAULT_AROUSAL_GAIN

    def is_inserted(self, actor: CharacterState) -> bool:
        return bool(actor.active_persistent_states & INSERTED_STATES)

    def get_arousal(self, world: WorldState) -> int:
        return world.conditions.get(AROUSAL_KEY, 0)

    def get_inside(self, world: WorldState) -> bool:
        return world.conditions.get(EJACULATE_INSIDE_KEY, 1) != 0

    def set_inside(self, world: WorldState, inside: bool) -> None:
        world.conditions[EJACULATE_INSIDE_KEY] = 1 if inside else 0

    def toggle_inside(self, world: WorldState) -> bool:
        new_val = not self.get_inside(world)
        self.set_inside(world, new_val)
        return new_val

    def reset_arousal(self, world: WorldState) -> None:
        world.conditions[AROUSAL_KEY] = 0

    def accumulate(
        self,
        world: WorldState,
        actor: CharacterState,
        gain: int | None = None,
    ) -> int:
        if not self.is_inserted(actor):
            return self.get_arousal(world)
        delta = self.default_gain if gain is None else gain
        ceiling = self.threshold * 2
        value = min(ceiling, self.get_arousal(world) + delta)
        world.conditions[AROUSAL_KEY] = value
        return value

    def check_and_fire(
        self, world: WorldState, actor: CharacterState
    ) -> str | None:
        """Return ejaculation tag if arousal crossed threshold; reset counter."""

        if self.get_arousal(world) < self.threshold:
            return None
        inside = self.get_inside(world)
        self.reset_arousal(world)
        if inside:
            actor.stats.source.add("fluid", 30)
            actor.stats.source.add("pleasure_v", 10)
            return TAG_EJACULATION_INSIDE
        return TAG_EJACULATION_OUTSIDE
