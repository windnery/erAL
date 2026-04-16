"""Load shipgirl work schedules from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class WorkScheduleDefinition:
    key: str
    actor_key: str
    location_key: str
    work_key: str
    work_label: str
    start_time: str
    end_time: str
    date_rules: dict[str, tuple[str | int, ...]]


def load_work_schedule_definitions(path: Path) -> tuple[WorkScheduleDefinition, ...]:
    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    schedules = []
    for entry in raw_data.get("work_schedules", []):
        date_rules = {}
        for key, values in entry.get("date_rules", {}).items():
            date_rules[str(key)] = tuple(values)
        schedules.append(
            WorkScheduleDefinition(
                key=str(entry["key"]),
                actor_key=str(entry["actor_key"]),
                location_key=str(entry["location_key"]),
                work_key=str(entry["work_key"]),
                work_label=str(entry["work_label"]),
                start_time=str(entry["start_time"]),
                end_time=str(entry["end_time"]),
                date_rules=date_rules,
            )
        )
    return tuple(schedules)
