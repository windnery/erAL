"""Work command end-to-end tests: availability, vitality cost, personal income."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import make_app, reset_progress

_REPO_ROOT = Path(__file__).resolve().parents[1]


class WorkCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        # Place at work location
        self.actor.location_key = "command_office"
        self.app.world.active_location.key = "command_office"
        self.app.world.active_location.display_name = "指挥室"

    def test_office_shift_available_at_work_location(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="office_shift",
        )
        self.assertEqual(result.action_key, "office_shift")
        self.assertFalse(result.fainted)

    def test_office_shift_grants_personal_income(self) -> None:
        initial = self.app.world.personal_funds
        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="office_shift",
        )
        self.assertEqual(self.app.world.personal_funds, initial + 30)

    def test_office_shift_result_contains_funds_delta(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="office_shift",
        )
        self.assertEqual(result.funds_delta.get("personal"), 30)

    def test_office_shift_consumes_stamina_and_spirit(self) -> None:
        initial_stamina = self.actor.stats.base.get("stamina")
        initial_spirit = self.actor.stats.base.get("spirit")
        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="office_shift",
        )
        self.assertLess(self.actor.stats.base.get("stamina"), initial_stamina)
        self.assertLess(self.actor.stats.base.get("spirit"), initial_spirit)

    def test_extra_shift_grants_more_income(self) -> None:
        from eral.domain.world import TimeSlot
        self.app.world.current_time_slot = TimeSlot.AFTERNOON
        initial = self.app.world.personal_funds
        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="extra_shift",
        )
        self.assertEqual(self.app.world.personal_funds, initial + 50)

    def test_extra_shift_consumes_more_stamina(self) -> None:
        from eral.domain.world import TimeSlot
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="office_shift",
        )
        office_stamina = self.actor.stats.base.get("stamina")
        reset_progress(self.actor)
        self.actor.location_key = "command_office"
        self.app.world.active_location.key = "command_office"
        self.app.world.current_time_slot = TimeSlot.AFTERNOON

        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="extra_shift",
        )
        extra_stamina = self.actor.stats.base.get("stamina")
        self.assertLess(extra_stamina, office_stamina)

    def test_work_commands_produce_abl_exp(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="office_shift",
        )
        self.assertIn("abl_13", result.source_deltas)

    def test_multiple_shifts_accumulate_funds(self) -> None:
        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="office_shift",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="office_shift",
        )
        self.assertEqual(self.app.world.personal_funds, 60)

    def test_normal_command_does_not_grant_income(self) -> None:
        initial = self.app.world.personal_funds
        self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="chat",
        )
        self.assertEqual(self.app.world.personal_funds, initial)


if __name__ == "__main__":
    unittest.main()
