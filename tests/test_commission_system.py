"""Commission system end-to-end tests: dispatch, tick, finalize, visibility."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import make_app, reset_progress, seed_friendly

_REPO_ROOT = Path(__file__).resolve().parents[1]


class CommissionDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)

    def test_dispatch_sets_commission_state(self) -> None:
        result = self.app.commission_service.dispatch(
            self.app.world, self.actor, "patrol",
        )
        self.assertTrue(result)
        self.assertTrue(self.actor.is_on_commission)
        self.assertIsNotNone(self.actor.commission_assignment)

    def test_dispatch_unknown_commission_fails(self) -> None:
        self.assertFalse(
            self.app.commission_service.dispatch(self.app.world, self.actor, "nonexistent")
        )

    def test_dispatch_fails_if_following(self) -> None:
        self.actor.is_following = True
        self.assertFalse(
            self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        )

    def test_dispatch_fails_if_on_date(self) -> None:
        self.actor.is_on_date = True
        self.assertFalse(
            self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        )

    def test_dispatch_fails_if_already_on_commission(self) -> None:
        self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        self.assertFalse(
            self.app.commission_service.dispatch(self.app.world, self.actor, "supply_run")
        )


class CommissionTickTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)

    def test_tick_reduces_remaining_slots(self) -> None:
        self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        remaining_before = self.actor.commission_assignment.remaining_slots
        self.app.commission_service.tick_slot(self.app.world)
        self.assertEqual(self.actor.commission_assignment.remaining_slots, remaining_before - 1)

    def test_finalize_clears_commission_state(self) -> None:
        self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        # patrol has duration_slots=2, tick twice
        self.app.commission_service.tick_slot(self.app.world)
        self.assertTrue(self.actor.is_on_commission)
        finalized = self.app.commission_service.tick_slot(self.app.world)
        self.assertFalse(self.actor.is_on_commission)
        self.assertIsNone(self.actor.commission_assignment)
        self.assertIn("patrol", finalized)

    def test_finalize_pays_port_income(self) -> None:
        initial_port = self.app.world.port_funds
        self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        # patrol: duration_slots=2, port_income=1200
        self.app.commission_service.tick_slot(self.app.world)
        self.app.commission_service.tick_slot(self.app.world)
        self.assertEqual(self.app.world.port_funds, initial_port + 1200)

    def test_finalize_high_income_commission(self) -> None:
        seed_friendly(self.actor)
        initial_port = self.app.world.port_funds
        self.app.commission_service.dispatch(self.app.world, self.actor, "joint_exercise")
        # joint_exercise: duration_slots=6, port_income=4000
        for _ in range(6):
            self.app.commission_service.tick_slot(self.app.world)
        self.assertEqual(self.app.world.port_funds, initial_port + 4000)


class CommissionVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)

    def test_commissioned_actor_hidden_from_visible(self) -> None:
        self.assertIn(self.actor, self.app.world.visible_characters())
        self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        self.assertNotIn(self.actor, self.app.world.visible_characters())

    def test_finalized_actor_visible_again(self) -> None:
        self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        self.assertNotIn(self.actor, self.app.world.visible_characters())
        for _ in range(2):
            self.app.commission_service.tick_slot(self.app.world)
        self.assertIn(self.actor, self.app.world.visible_characters())


class CommissionGameLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)

    def test_advance_time_ticks_commission(self) -> None:
        self.app.commission_service.dispatch(self.app.world, self.actor, "patrol")
        remaining_before = self.actor.commission_assignment.remaining_slots
        self.app.game_loop.advance_time(self.app.world)
        self.assertEqual(self.actor.commission_assignment.remaining_slots, remaining_before - 1)


if __name__ == "__main__":
    unittest.main()
