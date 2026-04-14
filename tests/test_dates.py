"""Date flow tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.compat_semantics import CFLAGKey, actor_cflag
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress


class DateTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        place_player_with_actor(self.app, actor)
        return actor

    def _seed_like(self, actor) -> None:
        actor.affection = 420
        actor.trust = 220
        actor_cflag.set(actor, CFLAGKey.AFFECTION, 420)
        actor_cflag.set(actor, CFLAGKey.TRUST, 220)
        actor.stats.compat.abl.set(9, 3)
        self.app.relationship_service.update_actor(actor)

    def test_invite_date_requires_follow_and_like_stage(self) -> None:
        actor = self._actor()

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="invite_date",
            )

        self._seed_like(actor)
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
        self.assertEqual(actor_cflag.get(actor, CFLAGKey.ON_DATE), 1)
        self.assertEqual(result.action_key, "invite_date")

    def test_end_date_clears_date_state(self) -> None:
        actor = self._actor()
        self._seed_like(actor)
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
        self.assertEqual(actor_cflag.get(actor, CFLAGKey.ON_DATE), 0)
        self.assertEqual(result.action_key, "end_date")