"""PALAM natural decay over time."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomllib

from eral.domain.world import CharacterState


@dataclass(frozen=True, slots=True)
class PalamDecayRule:
    palam_index: int
    base_decay: int


def load_palam_decay_rules(path: Path) -> tuple[PalamDecayRule, ...]:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return tuple(
        PalamDecayRule(
            palam_index=int(item["palam_index"]),
            base_decay=int(item["base_decay"]),
        )
        for item in raw.get("rule", [])
    )


def apply_palam_decay(actor: CharacterState, rules: tuple[PalamDecayRule, ...]) -> dict[str, int]:
    applied: dict[str, int] = {}
    for rule in rules:
        key = str(rule.palam_index)
        current = actor.stats.palam.get(key)
        if current <= 0:
            continue
        new_val = max(0, current - rule.base_decay)
        actor.stats.palam.set(key, new_val)
        applied[key] = current - new_val
    return applied
