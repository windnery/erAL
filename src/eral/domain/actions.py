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
    actor_key: str | None = None
    scene: SceneContext | None = None
    triggered_events: list[str] = field(default_factory=list)
    source_deltas: dict[str, int] = field(default_factory=dict)
    changes: list[AppliedChange] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
