"""Real date and clock advancement helpers."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import WorldState

_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_MONTH_LENGTHS = {i: 30 for i in range(1, 13)}
_REPRESENTATIVE_TIMES = {
    "dawn": (6, 0),
    "morning": (8, 0),
    "afternoon": (12, 0),
    "evening": (17, 0),
    "night": (20, 0),
    "late_night": (0, 0),
}


@dataclass(slots=True)
class TimeService:
    """Advance the world's real date and clock state."""

    def advance_days(self, world: WorldState, days: int = 1) -> None:
        """Advance the world's calendar by whole days."""

        for _ in range(max(0, days)):
            self._advance_one_day(world)

    def advance_minutes(self, world: WorldState, minutes: int) -> None:
        """Advance world time by a positive number of minutes."""

        if minutes <= 0:
            return
        if (
            world.current_time_slot != world.derive_time_slot()
            and (world.current_hour, world.current_minute)
            == _REPRESENTATIVE_TIMES[world.current_time_slot.value]
        ):
            world._sync_clock_from_time_slot()
        total_minutes = world.current_hour * 60 + world.current_minute + minutes
        extra_days, minute_of_day = divmod(total_minutes, 24 * 60)
        world.current_hour, world.current_minute = divmod(minute_of_day, 60)
        self.advance_days(world, extra_days)

    def _advance_one_day(self, world: WorldState) -> None:
        """Advance date and weekday by one day."""

        world.current_day += 1
        month_length = _MONTH_LENGTHS[world.current_month]
        if world.current_day > month_length:
            world.current_day = 1
            world.current_month += 1
            if world.current_month > 12:
                world.current_month = 1
                world.current_year += 1
        weekday_index = _WEEKDAYS.index(world.current_weekday)
        world.current_weekday = _WEEKDAYS[(weekday_index + 1) % len(_WEEKDAYS)]
