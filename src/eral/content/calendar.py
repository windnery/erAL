"""Load calendar and festival definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FestivalDefinition:
    key: str
    display_name: str
    month: int
    day: int
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SeasonDefinition:
    key: str
    months: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CalendarDefinition:
    weekday_names: tuple[str, ...]
    month_lengths: dict[int, int]
    seasons: tuple[SeasonDefinition, ...]
    festivals: tuple[FestivalDefinition, ...]

    def season_for_month(self, month: int) -> str:
        for season in self.seasons:
            if month in season.months:
                return season.key
        return "unknown"


def load_calendar_definition(path: Path) -> CalendarDefinition:
    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    calendar = raw_data.get("calendar", {})
    return CalendarDefinition(
        weekday_names=tuple(str(name) for name in calendar.get("weekday_names", [])),
        month_lengths={int(key): int(value) for key, value in calendar.get("month_lengths", {}).items()},
        seasons=tuple(
            SeasonDefinition(
                key=str(entry["key"]),
                months=tuple(int(month) for month in entry.get("months", [])),
            )
            for entry in raw_data.get("seasons", [])
        ),
        festivals=tuple(
            FestivalDefinition(
                key=str(entry["key"]),
                display_name=str(entry["display_name"]),
                month=int(entry["month"]),
                day=int(entry["day"]),
                tags=tuple(str(tag) for tag in entry.get("tags", [])),
            )
            for entry in raw_data.get("festivals", [])
        ),
    )
