"""Action and settlement result models."""

from __future__ import annotations

from dataclasses import dataclass, field

from eral.domain.scene import SceneContext


@dataclass(frozen=True, slots=True)
class AppliedChange:
    """A single applied stat or compat change."""

    family: str
    target: str
    before: int
    after: int
    delta: int


@dataclass(slots=True)
class ActionResult:
    """Result of executing a command or movement."""

    action_key: str
    success: bool = True
    chance: float = 1.0
    actor_key: str | None = None
    scene: SceneContext | None = None
    triggered_events: list[str] = field(default_factory=list)
    source_deltas: dict[str, int] = field(default_factory=dict)
    changes: list[AppliedChange] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    funds_delta: dict[str, int] = field(default_factory=dict)
    fainted: bool = False
    shopfront_key: str | None = None


@dataclass(slots=True)
class CupBoard:
    """Per-turn accumulation buffer for CUP (positive) and CDOWN (negative).

    Mirrors eraTW's CUP/CDOWN mechanism. After all SOURCE rules are applied,
    PALAM gets += CUP - CDOWN, then both are cleared.
    CFLAG and BASE are written directly without going through this buffer.
    """

    cup: dict[str, int] = field(default_factory=dict)
    cdown: dict[str, int] = field(default_factory=dict)

    def add_cup(self, key: str, value: int) -> None:
        self.cup[key] = self.cup.get(key, 0) + value

    def add_cdown(self, key: str, value: int) -> None:
        self.cdown[key] = self.cdown.get(key, 0) + value

    def clear(self) -> None:
        self.cup.clear()
        self.cdown.clear()
