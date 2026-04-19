"""Date-specific command branch tests — date commands availability and execution."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.dialogue import DialogueEntry
from eral.content.events import EventDefinition
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress


class DateCommandAvailabilityTests(unittest.TestCase):
    """Test that date-only commands appear only during dates."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)
        # Set up like stage for date invitation
        self.actor.affection = 420
        self.actor.trust = 220
        self.actor.stats.compat.cflag.set(2, 420)
        self.actor.stats.compat.cflag.set(4, 220)
        self.actor.stats.compat.abl.set(9, 3)
        self.app.relationship_service.update_actor(self.actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING

    def _start_date(self) -> None:
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="invite_date",
        )

    def test_hold_hands_not_available_without_date(self) -> None:
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertNotIn("hold_hands", keys)

    def test_date_stroll_not_available_without_date(self) -> None:
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertNotIn("date_stroll", keys)

    def test_date_meal_not_available_without_date(self) -> None:
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertNotIn("date_meal", keys)

    def test_gift_not_available_without_date(self) -> None:
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertNotIn("gift", keys)

    def test_hold_hands_available_during_date(self) -> None:
        self._start_date()
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertIn("hold_hands", keys)

    def test_date_stroll_available_during_date_at_public_location(self) -> None:
        self._start_date()
        # cafeteria has "food" and "social" tags; stroll needs "public" or "harbor"
        # Move to a public location
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.world.active_location.key = "main_corridor"
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertIn("date_stroll", keys)

    def test_room_visit_available_during_date_at_dormitory(self) -> None:
        self._start_date()
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dormitory_a")
        self.actor.location_key = "dormitory_a"

        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertIn("room_visit", keys)

    def test_end_date_removes_date_commands(self) -> None:
        self._start_date()
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="end_date",
        )
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertNotIn("hold_hands", keys)
        self.assertNotIn("date_stroll", keys)
        self.assertNotIn("date_meal", keys)
        self.assertNotIn("gift", keys)

    def test_date_travel_hides_date_commands(self) -> None:
        self._start_date()
        self.app.world.is_date_traveling = True

        available = self.app.command_service.available_commands_for_actor(
            self.app.world,
            self.actor.key,
        )
        keys = [cmd.key for cmd in available]

        self.assertNotIn("hold_hands", keys)
        self.assertNotIn("date_stroll", keys)
        self.assertNotIn("date_meal", keys)

    def test_date_travel_reports_specific_failure_reason(self) -> None:
        self._start_date()
        self.app.world.is_date_traveling = True

        with self.assertRaisesRegex(ValueError, "约会途中"):
            self.app.command_service.execute(
                self.app.world,
                actor_key=self.actor.key,
                command_key="date_meal",
            )


class DateCommandExecutionTests(unittest.TestCase):
    """Test executing date commands produces correct results."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)
        self.actor.affection = 420
        self.actor.trust = 220
        self.actor.stats.compat.cflag.set(2, 420)
        self.actor.stats.compat.cflag.set(4, 220)
        self.actor.stats.compat.abl.set(9, 3)
        self.app.relationship_service.update_actor(self.actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        # Start date
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="invite_date",
        )

    def test_hold_hands_produces_source(self) -> None:
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="hold_hands",
        )
        self.assertEqual(result.action_key, "hold_hands")
        # hold_hands source: affection=100, joy=80
        self.assertIn("affection", result.source_deltas)
        self.assertEqual(result.source_deltas["affection"], 100)

    def test_date_meal_at_cafeteria(self) -> None:
        # cafeteria has "food" tag → date_meal is available
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="date_meal",
        )
        self.assertEqual(result.action_key, "date_meal")

    def test_gift_on_date_at_cafeteria(self) -> None:
        self.app.world.add_item("chocolate_box", 1)
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="gift",
        )
        self.assertEqual(result.action_key, "gift")
        self.assertIn("affection", result.source_deltas)

    def test_dessert_date_at_cafeteria(self) -> None:
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="dessert_date",
        )
        self.assertEqual(result.action_key, "dessert_date")

    def test_enter_room_requires_love_stage_at_dormitory(self) -> None:
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dormitory_a")
        self.actor.location_key = "dormitory_a"

        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertNotIn("enter_room", keys)

        self.actor.affection = 850
        self.actor.trust = 450
        self.actor.stats.compat.cflag.set(2, 850)
        self.actor.stats.compat.cflag.set(4, 450)
        self.actor.stats.compat.abl.set(9, 5)
        self.app.relationship_service.update_actor(self.actor)
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertIn("enter_room", keys)

    def test_date_watch_sea_requires_love_stage(self) -> None:
        # At like stage, date_watch_sea should not be available
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertNotIn("date_watch_sea", keys)

    def test_date_watch_sea_available_at_love_stage_on_dock(self) -> None:
        # Advance to love stage
        self.actor.affection = 850
        self.actor.trust = 450
        self.actor.stats.compat.cflag.set(2, 850)
        self.actor.stats.compat.cflag.set(4, 450)
        self.actor.stats.compat.abl.set(9, 5)
        self.app.relationship_service.update_actor(self.actor)
        # Move to dock (harbor tag)
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.world.active_location.key = "dock"
        self.actor.location_key = "dock"

        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertIn("date_watch_sea", keys)


class DateEventTriggerTests(unittest.TestCase):
    """Test that date-specific events fire correctly."""

    def _install_date_event_fixtures(self) -> None:
        self.app.event_service.events = self.app.event_service.events + (
            EventDefinition(
                key="enterprise_date_watch_sea_fixture",
                action_key="date_watch_sea",
                actor_tags=("enterprise",),
                location_keys=("dock",),
                time_slots=("night",),
                min_affection=800,
                min_trust=400,
                min_obedience=None,
                required_stage="love",
                requires_date=True,
                requires_private=False,
                required_marks={},
            ),
            EventDefinition(
                key="enterprise_enter_room_fixture",
                action_key="enter_room",
                actor_tags=("enterprise",),
                location_keys=("dormitory_a",),
                time_slots=("night",),
                min_affection=800,
                min_trust=400,
                min_obedience=None,
                required_stage="love",
                requires_date=True,
                requires_private=True,
                required_marks={},
            ),
        )
        self.app.dialogue_service.entries = self.app.dialogue_service.entries + (
            DialogueEntry(
                key="enterprise_date_watch_sea_fixture",
                actor_key="enterprise",
                lines=("她望向夜海，声音比海风还轻。",),
                priority=10,
            ),
            DialogueEntry(
                key="enterprise_enter_room_fixture",
                actor_key="enterprise",
                lines=("她在宿舍门口停了一瞬，还是让你跟了进去。",),
                priority=10,
            ),
        )

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)
        self._install_date_event_fixtures()
        self.actor.affection = 850
        self.actor.trust = 450
        self.actor.stats.compat.cflag.set(2, 850)
        self.actor.stats.compat.cflag.set(4, 450)
        self.actor.stats.compat.abl.set(9, 5)
        self.app.relationship_service.update_actor(self.actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.NIGHT
        # Start date
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dock")
        self.actor.location_key = "dock"
        self.app.world.active_location.key = "dock"
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="invite_date",
        )

    def test_date_watch_sea_triggers_event(self) -> None:
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="date_watch_sea",
        )
        self.assertIn("enterprise_date_watch_sea_fixture", result.triggered_events)

    def test_enter_room_triggers_dormitory_event(self) -> None:
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dormitory_a")
        self.actor.location_key = "dormitory_a"
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="enter_room",
        )
        self.assertIn("enterprise_enter_room_fixture", result.triggered_events)


if __name__ == "__main__":
    unittest.main()