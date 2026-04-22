"""Derive personal-info panel data from character definition + world state.

Exposes small helper functions used by the CLI status panel. No UI coupling.
"""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.characters import CharacterDefinition
from eral.content.work_schedules import WorkScheduleDefinition
from eral.domain.map import PortMap
from eral.domain.world import CharacterState


_SLOT_HOUR_RANGE: dict[str, tuple[int, int]] = {
    "dawn": (5, 8),
    "morning": (8, 12),
    "afternoon": (12, 17),
    "evening": (17, 20),
    "night": (20, 24),
    "late_night": (0, 5),
}

_WEEKDAY_LABELS = {
    "mon": "周一", "tue": "周二", "wed": "周三",
    "thu": "周四", "fri": "周五", "sat": "周六", "sun": "周日",
}


@dataclass(frozen=True, slots=True)
class WorkEntry:
    work_label: str
    days: str              # "平日" / "周末" / "周一/周三"
    time_range: str        # "18:00-21:00"
    location_display: str


@dataclass(frozen=True, slots=True)
class Milestone:
    label: str
    day: int


def personality_from_tags(tags: tuple[str, ...]) -> str:
    """Pick the descriptive tag (last non-category tag) as personality.

    Personality is derived from TALENT axes + tags; erAL does not carry a
    separate personality field on the character definition.
    """
    category_tags = {
        "destroyer", "carrier", "cruiser", "battleship",
        "eagle_union", "royal_navy", "sakura", "iron_blood", "iris",
    }
    descriptive = [t for t in tags if t not in category_tags and t != tags[0]]
    return descriptive[0] if descriptive else "普通"


def activity_hours(definition: CharacterDefinition) -> str:
    """Derive earliest–latest active hour range from schedule, excluding home slots."""
    home = definition.home_location_key
    active_slots = [
        slot for slot, loc in definition.schedule.items()
        if loc != home and slot in _SLOT_HOUR_RANGE
    ]
    if not active_slots:
        return "—"
    starts = [_SLOT_HOUR_RANGE[s][0] for s in active_slots]
    ends = [_SLOT_HOUR_RANGE[s][1] for s in active_slots]
    start = min(starts)
    end = max(ends)
    if end == 0:
        end = 24
    return f"{start}时～{end}时"


def frequent_areas(
    definition: CharacterDefinition, port_map: PortMap
) -> str:
    """Collect areas the character tends to be in."""
    areas: list[str] = []
    seen: set[str] = set()
    for loc_key in definition.schedule.values():
        try:
            loc = port_map.location_by_key(loc_key)
        except KeyError:
            continue
        if loc.area_key and loc.area_key not in seen:
            seen.add(loc.area_key)
            area = port_map.area_by_key(loc.area_key)
            areas.append(area.display_name if area else loc.area_key)
    return " / ".join(areas) if areas else "—"


def home_location_display(
    definition: CharacterDefinition, port_map: PortMap
) -> str:
    try:
        loc = port_map.location_by_key(definition.home_location_key)
    except KeyError:
        return definition.home_location_key or "—"
    area = port_map.area_by_key(loc.area_key) if loc.area_key else None
    if area:
        return f"{area.display_name} / {loc.display_name}"
    return loc.display_name


def work_entries(
    actor_key: str,
    schedules: tuple[WorkScheduleDefinition, ...],
    port_map: PortMap,
) -> tuple[WorkEntry, ...]:
    """Pretty-print work schedules owned by this actor."""
    entries: list[WorkEntry] = []
    for schedule in schedules:
        if schedule.actor_key != actor_key:
            continue
        weekdays = schedule.date_rules.get("weekdays", ())
        days_label = _days_label(weekdays)
        try:
            loc = port_map.location_by_key(schedule.location_key)
            location_display = loc.display_name
        except KeyError:
            location_display = schedule.location_key
        entries.append(
            WorkEntry(
                work_label=schedule.work_label,
                days=days_label,
                time_range=f"{schedule.start_time}-{schedule.end_time}",
                location_display=location_display,
            )
        )
    return tuple(entries)


def _days_label(weekdays: tuple) -> str:
    if not weekdays:
        return "每日"
    weekday_set = {str(d) for d in weekdays}
    weekday_all = {"mon", "tue", "wed", "thu", "fri"}
    weekend_all = {"sat", "sun"}
    if weekday_set == weekday_all:
        return "平日"
    if weekday_set == weekend_all:
        return "周末"
    labels = [_WEEKDAY_LABELS.get(d, d) for d in weekday_set]
    return "/".join(labels)


_MILESTONE_LABELS: dict[str, str] = {
    "milestone:first_kiss": "初吻日",
    "milestone:first_date": "初次约会",
    "milestone:first_sex": "初次交合",
    "milestone:first_hug": "初次拥抱",
    "milestone:oath_day": "誓约日",
}


def milestones(actor: CharacterState) -> tuple[Milestone, ...]:
    out: list[Milestone] = []
    for memory_key, label in _MILESTONE_LABELS.items():
        if actor.memories.get(memory_key, 0) <= 0:
            continue
        day = actor.get_condition(f"{memory_key}_day")
        if day <= 0:
            continue
        out.append(Milestone(label=label, day=day))
    return tuple(out)
