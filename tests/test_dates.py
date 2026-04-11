"""Date flow tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application


class DateTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        return next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")

    def test_invite_date_requires_follow_and_like_stage(self) -> None:
        actor = self._actor()

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="invite_date",
            )

        actor.affection = 3
        actor.trust = 2
        actor.stats.compat.cflag.set(2, 3)
        actor.stats.compat.cflag.set(4, 2)
        self.app.relationship_service.update_actor(actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING

        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )

        self.assertTrue(actor.is_on_date)
        self.assertTrue(actor.is_following)
        self.assertEqual(self.app.world.date_partner_key, actor.key)
        self.assertEqual(actor.stats.compat.cflag.get(12), 1)
        self.assertIn("secretary_invite_date_evening", result.triggered_events)

    def test_end_date_clears_date_state(self) -> None:
        actor = self._actor()
        actor.affection = 3
        actor.trust = 2
        actor.stats.compat.cflag.set(2, 3)
        actor.stats.compat.cflag.set(4, 2)
        self.app.relationship_service.update_actor(actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING

        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="end_date",
        )

        self.assertFalse(actor.is_on_date)
        self.assertIsNone(self.app.world.date_partner_key)
        self.assertEqual(actor.stats.compat.cflag.get(12), 0)
        self.assertIn("secretary_end_date", result.triggered_events)
