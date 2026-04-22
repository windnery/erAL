"""Core world state models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from eral.domain.relationship import RelationshipStage
from eral.domain.stats import ActorNumericState


CFLAG_AFFECTION = 2
CFLAG_TRUST = 4
CFLAG_OBEDIENCE = 6
CFLAG_ON_DATE = 12
CFLAG_SAME_ROOM = 319
CFLAG_FOLLOWING = 320
CFLAG_FOLLOW_READY = 329

CONDITION_ON_DATE = "on_date"
CONDITION_SAME_ROOM = "same_room"
CONDITION_FOLLOWING = "following"
CONDITION_FOLLOW_READY = "follow_ready"


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
    is_on_commission: bool = False
    fatigue: int = 0
    marks: dict[str, int] = field(default_factory=dict)
    conditions: dict[str, int] = field(default_factory=dict)
    memories: dict[str, int] = field(default_factory=dict)
    active_persistent_states: set[str] = field(default_factory=set)
    owned_skins: set[str] = field(default_factory=set)
    equipped_skin_key: str | None = None
    removed_slots: tuple[str, ...] = ()
    commission_assignment: object | None = None

    def sync_derived_fields(self) -> None:
        """Synchronise derived runtime fields from legacy compat CFLAG values."""

        self.affection = self.stats.compat.cflag.get(CFLAG_AFFECTION)
        self.trust = self.stats.compat.cflag.get(CFLAG_TRUST)
        self.obedience = self.stats.compat.cflag.get(CFLAG_OBEDIENCE)

    def sync_compat_from_runtime(self) -> None:
        """Mirror explicit runtime state to compat CFLAG for save compatibility."""

        self.stats.compat.cflag.set(CFLAG_AFFECTION, self.affection)
        self.stats.compat.cflag.set(CFLAG_TRUST, self.trust)
        self.stats.compat.cflag.set(CFLAG_OBEDIENCE, self.obedience)
        self.stats.compat.cflag.set(CFLAG_ON_DATE, 1 if self.is_on_date else 0)
        self.stats.compat.cflag.set(CFLAG_SAME_ROOM, 1 if self.is_same_room else 0)
        self.stats.compat.cflag.set(CFLAG_FOLLOWING, 1 if self.is_following else 0)
        self.stats.compat.cflag.set(CFLAG_FOLLOW_READY, 1 if self.follow_ready else 0)
        self.conditions[CONDITION_ON_DATE] = 1 if self.is_on_date else 0
        self.conditions[CONDITION_SAME_ROOM] = 1 if self.is_same_room else 0
        self.conditions[CONDITION_FOLLOWING] = 1 if self.is_following else 0
        self.conditions[CONDITION_FOLLOW_READY] = 1 if self.follow_ready else 0

    def hydrate_runtime_fields_from_compat(self) -> None:
        """Load runtime state from compat CFLAG for legacy data compatibility."""

        self.sync_derived_fields()
        self.is_on_date = self.stats.compat.cflag.get(CFLAG_ON_DATE) > 0
        self.is_same_room = self.stats.compat.cflag.get(CFLAG_SAME_ROOM) > 0
        self.is_following = self.stats.compat.cflag.get(CFLAG_FOLLOWING) > 0
        self.follow_ready = self.stats.compat.cflag.get(CFLAG_FOLLOW_READY) > 0
        self.sync_compat_from_runtime()

    def get_cflag(self, era_index: int) -> int:
        """Read cflag via explicit runtime state for active semantics."""

        if era_index == CFLAG_AFFECTION:
            return self.affection
        if era_index == CFLAG_TRUST:
            return self.trust
        if era_index == CFLAG_OBEDIENCE:
            return self.obedience
        if era_index == CFLAG_ON_DATE:
            return 1 if self.is_on_date else 0
        if era_index == CFLAG_SAME_ROOM:
            return 1 if self.is_same_room else 0
        if era_index == CFLAG_FOLLOWING:
            return 1 if self.is_following else 0
        if era_index == CFLAG_FOLLOW_READY:
            return 1 if self.follow_ready else 0
        return self.stats.compat.cflag.get(era_index)

    def set_cflag(self, era_index: int, value: int) -> None:
        """Write cflag via explicit runtime state and mirror to compat."""

        if era_index == CFLAG_AFFECTION:
            self.affection = value
        elif era_index == CFLAG_TRUST:
            self.trust = value
        elif era_index == CFLAG_OBEDIENCE:
            self.obedience = value
        elif era_index == CFLAG_ON_DATE:
            self.is_on_date = value > 0
        elif era_index == CFLAG_SAME_ROOM:
            self.is_same_room = value > 0
        elif era_index == CFLAG_FOLLOWING:
            self.is_following = value > 0
        elif era_index == CFLAG_FOLLOW_READY:
            self.follow_ready = value > 0
        self.stats.compat.cflag.set(era_index, value)

    def add_cflag(self, era_index: int, delta: int) -> int:
        """Increment cflag via explicit runtime state for active semantics."""

        after = self.get_cflag(era_index) + delta
        self.set_cflag(era_index, after)
        return after

    def get_condition(self, key: str) -> int:
        """Read extensible runtime condition value by key."""

        return int(self.conditions.get(key, 0))

    def set_condition(self, key: str, value: int) -> None:
        """Write extensible runtime condition value by key."""

        self.conditions[key] = int(value)

    def add_condition(self, key: str, delta: int) -> int:
        """Increment a runtime condition value by key."""

        value = self.get_condition(key) + int(delta)
        self.set_condition(key, value)
        return value

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

    def record_memory(self, key: str) -> int:
        self.memories[key] = self.memories.get(key, 0) + 1
        return self.memories[key]

    def has_memory(self, key: str, min_count: int = 1) -> bool:
        return self.memories.get(key, 0) >= min_count

    def has_skin(self, skin_key: str) -> bool:
        """Check whether the actor has unlocked the given skin."""

        return skin_key in self.owned_skins

    def unlock_skin(self, skin_key: str) -> None:
        """Unlock a skin for the actor."""

        self.owned_skins.add(skin_key)

    def equip_skin(self, skin_key: str) -> None:
        """Mark one unlocked skin as currently equipped."""

        self.equipped_skin_key = skin_key

    def clear_removed_slots(self) -> None:
        """Reset temporary clothing removal state."""

        self.removed_slots = ()


@dataclass(slots=True)
class WorldState:
    """Top-level world state for the playable runtime."""

    current_day: int
    current_time_slot: TimeSlot
    player_name: str
    active_location: PortLocation
    current_year: int = 1
    current_month: int = 1
    current_weekday: str = "mon"
    current_hour: int = 8
    current_minute: int = 0
    player_gender: str = "male"
    player_stats: ActorNumericState | None = None
    date_partner_key: str | None = None
    is_busy: bool = False
    is_date_traveling: bool = False
    personal_funds: int = 0
    port_funds: int = 0
    training_active: bool = False
    training_actor_key: str | None = None
    training_position_key: str | None = None
    training_step_index: int = 0
    training_flags: dict[str, int] = field(default_factory=dict)
    weather_key: str = "clear"
    conditions: dict[str, int] = field(default_factory=dict)
    inventory: dict[str, int] = field(default_factory=dict)
    facility_levels: dict[str, int] = field(default_factory=dict)
    characters: list[CharacterState] = field(default_factory=list)
    season_month_map: dict[int, str] = field(default_factory=dict)  # month -> season_key

    def __post_init__(self) -> None:
        """Keep coarse time slot and real clock aligned on bootstrap/load."""

        if (self.current_hour, self.current_minute) == (8, 0):
            self._sync_clock_from_time_slot()
        self.sync_time_slot_from_clock()

    def derive_time_slot(self) -> TimeSlot:
        """Derive legacy coarse slot from the real clock."""

        total_minutes = (self.current_hour * 60) + self.current_minute
        if 5 * 60 <= total_minutes < 8 * 60:
            return TimeSlot.DAWN
        if 8 * 60 <= total_minutes < 12 * 60:
            return TimeSlot.MORNING
        if 12 * 60 <= total_minutes < 17 * 60:
            return TimeSlot.AFTERNOON
        if 17 * 60 <= total_minutes < 20 * 60:
            return TimeSlot.EVENING
        if 20 * 60 <= total_minutes <= (23 * 60 + 59):
            return TimeSlot.NIGHT
        return TimeSlot.LATE_NIGHT

    def sync_time_slot_from_clock(self) -> None:
        """Mirror real clock values to the legacy coarse slot."""

        self.current_time_slot = self.derive_time_slot()

    @property
    def current_season(self) -> str:
        """Current season derived from current_month via injected season_month_map."""
        return self.season_month_map.get(self.current_month, "unknown")

    def _sync_clock_from_time_slot(self) -> None:
        """Assign a representative clock value from the coarse slot."""

        representative = {
            TimeSlot.DAWN: (6, 0),
            TimeSlot.MORNING: (8, 0),
            TimeSlot.AFTERNOON: (12, 0),
            TimeSlot.EVENING: (17, 0),
            TimeSlot.NIGHT: (20, 0),
            TimeSlot.LATE_NIGHT: (0, 0),
        }
        self.current_hour, self.current_minute = representative[self.current_time_slot]

    def get_condition(self, key: str) -> int:
        """Read global extensible runtime condition value by key."""

        return int(self.conditions.get(key, 0))

    def set_condition(self, key: str, value: int) -> None:
        """Write global extensible runtime condition value by key."""

        self.conditions[key] = int(value)

    def add_condition(self, key: str, delta: int) -> int:
        """Increment a global runtime condition value by key."""

        value = self.get_condition(key) + int(delta)
        self.set_condition(key, value)
        return value

    def item_count(self, item_key: str) -> int:
        """Return the current count for an inventory item."""

        return self.inventory.get(item_key, 0)

    def add_item(self, item_key: str, amount: int = 1) -> int:
        """Increase an inventory item count and return the new value."""

        if amount <= 0:
            return self.item_count(item_key)
        new_count = self.item_count(item_key) + amount
        self.inventory[item_key] = new_count
        return new_count

    def consume_item(self, item_key: str, amount: int = 1) -> bool:
        """Decrease an inventory item count when enough stock exists."""

        if amount <= 0:
            return True
        current = self.item_count(item_key)
        if current < amount:
            return False
        remaining = current - amount
        if remaining > 0:
            self.inventory[item_key] = remaining
        else:
            self.inventory.pop(item_key, None)
        return True

    def visible_characters(self) -> tuple[CharacterState, ...]:
        """Return characters currently at the player's location."""

        return tuple(
            character
            for character in self.characters
            if character.location_key == self.active_location.key
            and not character.is_on_commission
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
