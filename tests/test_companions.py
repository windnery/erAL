"""Companion and follow tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.compat_semantics import CFLAGKey, actor_cflag
from tests.support.real_actors import actor_by_key, place_player_with_actor, reset_progress


class CompanionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        place_player_with_actor(self.app, actor)
        return actor

    def test_invite_follow_starts_follow_and_moves_with_player(self) -> None:
        actor = self._actor()
        actor.affection = 2
        actor.trust = 0
        self.app.relationship_service.update_actor(actor)

        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )

        self.assertTrue(actor.is_following)
        self.assertTrue(actor.is_same_room)
        self.assertEqual(actor_cflag.get(actor, CFLAGKey.FOLLOWING), 1)

        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.assertEqual(self.app.world.active_location.key, "main_corridor")
        self.assertEqual(actor.location_key, "main_corridor")

        self.app.game_loop.advance_time(self.app.world)
        self.assertEqual(self.app.world.current_time_slot.value, "afternoon")
        self.assertEqual(actor.location_key, "main_corridor")

    def test_dismiss_follow_stops_following(self) -> None:
        actor = self._actor()
        actor.affection = 2
        self.app.relationship_service.update_actor(actor)

        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="dismiss_follow",
        )

        self.assertFalse(actor.is_following)
        self.assertEqual(actor_cflag.get(actor, CFLAGKey.FOLLOWING), 0)

    def test_walk_together_available_when_following_at_public_location(self) -> None:
        actor = self._actor()
        actor.affection = 2
        actor_cflag.set(actor, CFLAGKey.AFFECTION, 2)
        self.app.relationship_service.update_actor(actor)

        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")

        available = self.app.command_service.available_commands_for_actor(
            self.app.world,
            actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertIn("walk_together", keys)

    def test_lap_pillow_available_when_following(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        actor.affection = 2
        actor_cflag.set(actor, CFLAGKey.AFFECTION, 2)
        self.app.relationship_service.update_actor(actor)

        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )

        available = self.app.command_service.available_commands_for_actor(
            self.app.world,
            actor.key,
        )
        keys = [cmd.key for cmd in available]
        self.assertIn("lap_pillow", keys)
