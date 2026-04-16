"""Calendar and work schedule query helpers."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.calendar import CalendarDefinition
from eral.content.work_schedules import WorkScheduleDefinition
from eral.domain.world import WorldState

_WEEKDAY_LABELS = {
    "mon": "周一",
    "tue": "周二",
    "wed": "周三",
    "thu": "周四",
    "fri": "周五",
    "sat": "周六",
    "sun": "周日",
}


@dataclass(frozen=True, slots=True)
class WorkScheduleView:
    actor_name: str
    time_range: str
    location_name: str
    work_label: str


@dataclass(frozen=True, slots=True)
class CalendarDayView:
    year: int
    month: int
    day: int
    weekday: str
    season: str
    festival_labels: tuple[str, ...]
    schedule_entries: tuple[WorkScheduleView, ...]


@dataclass(slots=True)
class CalendarService:
    calendar_definition: CalendarDefinition

    def festival_labels_for_date(self, month: int, day: int) -> tuple[str, ...]:
        return tuple(
            festival.display_name
            for festival in self.calendar_definition.festivals
            if festival.month == month and festival.day == day
        )

    def festival_tags_for_date(self, month: int, day: int) -> tuple[str, ...]:
        tags: list[str] = []
        for festival in self.calendar_definition.festivals:
            if festival.month == month and festival.day == day:
                tags.append(festival.key)
                tags.extend(festival.tags)
        return tuple(tags)

    def shift_date(self, year: int, month: int, day: int, weekday: str, delta_days: int) -> tuple[int, int, int, str]:
        current_year = year
        current_month = month
        current_day = day
        weekday_names = self.calendar_definition.weekday_names
        weekday_index = weekday_names.index(weekday)
        step = 1 if delta_days >= 0 else -1
        for _ in range(abs(delta_days)):
            if step > 0:
                current_day += 1
                month_length = self.calendar_definition.month_lengths[current_month]
                if current_day > month_length:
                    current_day = 1
                    current_month += 1
                    if current_month > 12:
                        current_month = 1
                        current_year += 1
                weekday_index = (weekday_index + 1) % len(weekday_names)
            else:
                current_day -= 1
                if current_day <= 0:
                    current_month -= 1
                    if current_month <= 0:
                        current_month = 12
                        current_year -= 1
                    current_day = self.calendar_definition.month_lengths[current_month]
                weekday_index = (weekday_index - 1) % len(weekday_names)
        return current_year, current_month, current_day, weekday_names[weekday_index]


@dataclass(slots=True)
class CalendarViewService:
    calendar_service: CalendarService
    work_schedules: tuple[WorkScheduleDefinition, ...]
    actor_names: dict[str, str]
    location_names: dict[str, str]

    def day_views(self, world: WorldState, span_before: int = 2, span_after: int = 2) -> tuple[CalendarDayView, ...]:
        views: list[CalendarDayView] = []
        for offset in range(-span_before, span_after + 1):
            year, month, day, weekday = self.calendar_service.shift_date(
                world.current_year,
                world.current_month,
                world.current_day,
                world.current_weekday,
                offset,
            )
            festival_labels = self.calendar_service.festival_labels_for_date(month, day)
            festival_tags = self.calendar_service.festival_tags_for_date(month, day)
            season = self.calendar_service.calendar_definition.season_for_month(month)
            schedule_entries = self.schedule_entries_for_day(month, day, weekday, festival_tags)
            views.append(
                CalendarDayView(
                    year=year,
                    month=month,
                    day=day,
                    weekday=weekday,
                    season=season,
                    festival_labels=festival_labels,
                    schedule_entries=schedule_entries,
                )
            )
        return tuple(views)

    def schedule_entries_for_day(
        self,
        month: int,
        day: int,
        weekday: str,
        festival_tags: tuple[str, ...],
    ) -> tuple[WorkScheduleView, ...]:
        entries: list[WorkScheduleView] = []
        for schedule in self.work_schedules:
            if not self._matches_rules(schedule, month, day, weekday, festival_tags):
                continue
            entries.append(
                WorkScheduleView(
                    actor_name=self.actor_names.get(schedule.actor_key, schedule.actor_key),
                    time_range=f"{schedule.start_time}-{schedule.end_time}",
                    location_name=self.location_names.get(schedule.location_key, schedule.location_key),
                    work_label=schedule.work_label,
                )
            )
        return tuple(entries)

    def _matches_rules(
        self,
        schedule: WorkScheduleDefinition,
        month: int,
        day: int,
        weekday: str,
        festival_tags: tuple[str, ...],
    ) -> bool:
        rules = schedule.date_rules
        weekdays = rules.get("weekdays", ())
        if weekdays and weekday not in weekdays:
            return False
        months = rules.get("months", ())
        if months and month not in months:
            return False
        days = rules.get("days", ())
        if days and day not in days:
            return False
        required_festival_tags = rules.get("festival_tags", ())
        if required_festival_tags and not all(tag in festival_tags for tag in required_festival_tags):
            return False
        return True


def weekday_label(weekday: str) -> str:
    return _WEEKDAY_LABELS.get(weekday, weekday)
