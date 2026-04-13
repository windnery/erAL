"""Core world state models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from eral.domain.compat_semantics import CFLAGKey, actor_cflag
from eral.domain.relationship import RelationshipStage
from eral.domain.stats import ActorNumericState, WorldEraCompatState


class TimeSlot(StrEnum):
    """Coarse-grained day segments for the early project stage."""

    DAWN = "dawn"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    LATE_NIGHT = "late_night"

    @classmethod
    def from_name(cls, value: str) -> "TimeSlot":
        try:
            return cls(value.lower())
        except ValueError:
            return cls.MORNING

    def next(self) -> "TimeSlot":
        order = [
            TimeSlot.DAWN,
            TimeSlot.MORNING,
            TimeSlot.AFTERNOON,
            TimeSlot.EVENING,
            TimeSlot.NIGHT,
            TimeSlot.LATE_NIGHT,
        ]
        current_index = order.index(self)
        return order[(current_index + 1) % len(order)]


@dataclass(slots=True)
class PortLocation:
    """Named location in the port map."""

    key: str
    display_name: str


@dataclass(slots=True)
class CharacterState:
    """Minimal runtime character state."""

    key: str
    display_name: str
    location_key: str
    stats: ActorNumericState
    tags: tuple[str, ...] = ()
    affection: int = 0
    trust: int = 0
    obedience: int = 0
    relationship_stage: RelationshipStage | None = None
    previous_location_key: str | None = None
    encounter_location_key: str | None = None
    is_same_room: bool = False
    is_following: bool = False
    follow_ready: bool = False
    is_on_date: bool = False
    fatigue: int = 0
    marks: dict[str, int] = field(default_factory=dict)

    def sync_derived_fields(self) -> None:
        """Synchronise derived fields from the authoritative CFLAG block."""

        self.affection = actor_cflag.get(self, CFLAGKey.AFFECTION)
        self.trust = actor_cflag.get(self, CFLAGKey.TRUST)
        self.obedience = actor_cflag.get(self, CFLAGKey.OBEDIENCE)

    def has_mark(self, key: str, min_level: int = 1) -> bool:
        """Check whether a mark is present at or above the given level."""

        return self.marks.get(key, 0) >= min_level

    def set_mark(self, key: str, level: int, max_level: int = 1) -> None:
        """Set a mark, clamping to [0, max_level]."""

        self.marks[key] = max(0, min(level, max_level))

    def add_mark(self, key: str, delta: int = 1, max_level: int = 1) -> int:
        """Increment a mark by delta, clamping to [0, max_level]."""

        current = self.marks.get(key, 0)
        new_level = max(0, min(current + delta, max_level))
        self.marks[key] = new_level
        return new_level


@dataclass(slots=True)
class WorldState:
    """Top-level world state for the playable runtime."""

    current_day: int
    current_time_slot: TimeSlot
    player_name: str
    active_location: PortLocation
    compat: WorldEraCompatState
    date_partner_key: str | None = None
    is_busy: bool = False
    is_date_traveling: bool = False
    characters: list[CharacterState] = field(default_factory=list)

    def visible_characters(self) -> tuple[CharacterState, ...]:
        """Return characters currently at the player's location."""

        return tuple(
            character
            for character in self.characters
            if character.location_key == self.active_location.key
        )

    def encounter_characters(self) -> tuple[CharacterState, ...]:
        """Return characters newly encountered at the current location.

        A character counts as newly encountered when their
        ``encounter_location_key`` differs from the player's current
        location — meaning the player just arrived or the character
        just arrived via schedule refresh.
        """

        return tuple(
            character
            for character in self.characters
            if (
                character.location_key == self.active_location.key
                and character.encounter_location_key != self.active_location.key
            )
        )
