"""Command resolution checks for gated success/failure outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import random
from typing import Callable

from eral.domain.world import CharacterState, WorldState
from eral.systems.relationships import ABL_INTIMACY_INDEX


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    """Outcome of resolving a command with an explicit success chance."""

    success: bool
    chance: float


@dataclass(slots=True)
class ResolutionService:
    """Resolve command outcomes that depend on a probabilistic check."""

    roll: Callable[[], float] = field(default=random)

    def resolve(
        self,
        resolution_key: str,
        world: WorldState,
        actor: CharacterState,
    ) -> ResolutionResult:
        if resolution_key != "oath":
            raise ValueError(f"Unsupported resolution key: {resolution_key}")
        chance = self._oath_chance(world, actor)
        return ResolutionResult(success=self.roll() <= chance, chance=chance)

    @staticmethod
    def _oath_chance(world: WorldState, actor: CharacterState) -> float:
        del world
        intimacy = actor.stats.compat.abl.get(ABL_INTIMACY_INDEX)
        chance = 0.35
        chance += min(actor.affection, 1200) / 8000
        chance += min(actor.trust, 800) / 5000
        chance += min(intimacy, 10) * 0.03
        return max(0.05, min(0.95, chance))
