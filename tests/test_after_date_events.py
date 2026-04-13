"""Tests for after-date follow-up event resolution."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.dialogue import DialogueEntry
from eral.content.events import EventDefinition
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress


class AfterDateEventTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)
        self._install_after_date_fixtures()

    def _install_after_date_fixtures(self) -> None:
        self.app.event_service.events = self.app.event_service.events + (
            EventDefinition(
                key="secretary_after_date_default",
                action_key="after_date_event",
                actor_tags=("enterprise",),
                location_keys=("cafeteria",),
                time_slots=("evening",),
                min_affection=310,
                min_trust=160,
                min_obedience=None,
                required_stage="like",
                requires_date=False,
                requires_private=False,
                required_marks={},
            ),
            EventDefinition(
                key="secretary_after_date_confessed",
                action_key="after_date_event",
                actor_tags=("enterprise",),
                location_keys=("cafeteria",),
                time_slots=("evening",),
                min_affection=850,
                min_trust=450,
                min_obedience=None,
                required_stage="love",
                requires_date=False,
                requires_private=False,
                required_marks={"confessed": 1},
            ),
        )
        self.app.dialogue_service.entries = self.app.dialogue_service.entries + (
            DialogueEntry(
                key="secretary_after_date_default",
                actor_key="enterprise",
                lines=("约会散场后，她还特意回头看了你一眼。",),
                priority=10,
            ),
            DialogueEntry(
                key="secretary_after_date_confessed",
                actor_key="enterprise",
                lines=("离开前，她低声补了一句要你别忘记刚才的告白。",),
                priority=10,
            ),
        )

    def _prepare_date(self, *, love: bool = False, confessed: bool = False) -> None:
        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        self.actor.location_key = "cafeteria"
        if love:
            self.actor.affection = 850
            self.actor.trust = 450
            self.actor.stats.compat.cflag.set(2, 850)
            self.actor.stats.compat.cflag.set(4, 450)
            self.actor.stats.compat.abl.set(12, 5)
        else:
            self.actor.affection = 420
            self.actor.trust = 220
            self.actor.stats.compat.cflag.set(2, 420)
            self.actor.stats.compat.cflag.set(4, 220)
            self.actor.stats.compat.abl.set(12, 3)
        self.app.relationship_service.update_actor(self.actor)
        if confessed:
            self.actor.add_mark("confessed", 1)
        self.app.command_service.execute(self.app.world, self.actor.key, "invite_follow")
        self.app.command_service.execute(self.app.world, self.actor.key, "invite_date")

    def test_end_date_triggers_default_after_date_event(self) -> None:
        self._prepare_date(love=False, confessed=False)

        result = self.app.command_service.execute(self.app.world, self.actor.key, "end_date")

        self.assertIn("secretary_after_date_default", result.triggered_events)
        self.assertTrue(any("约会散场后" in line for line in result.messages))

    def test_end_date_prefers_confessed_after_date_branch(self) -> None:
        self._prepare_date(love=True, confessed=True)

        result = self.app.command_service.execute(self.app.world, self.actor.key, "end_date")

        self.assertIn("secretary_after_date_confessed", result.triggered_events)
        self.assertTrue(any("告白" in line for line in result.messages))


if __name__ == "__main__":
    unittest.main()