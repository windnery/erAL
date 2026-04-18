"""Scene context for command and event resolution."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SceneContext:
    """Resolved local scene state used by events and dialogue."""

    actor_key: str
    actor_tags: tuple[str, ...]
    action_key: str
    current_day: int
    time_slot: str
    location_key: str
    location_tags: tuple[str, ...]
    affection: int
    trust: int
    obedience: int
    relationship_stage: str
    relationship_rank: int
    is_following: bool
    is_on_date: bool
    is_same_room: bool
    visible_count: int
    is_private: bool
    season: str = "unknown"
    equipped_skin_key: str | None = None
    equipped_skin_tags: tuple[str, ...] = ()
    removed_slots: tuple[str, ...] = ()
    marks: dict[str, int] = field(default_factory=dict)
    is_training: bool = False
    training_position_key: str | None = None
    training_results: tuple[str, ...] = ()
    training_step_index: int = 0
