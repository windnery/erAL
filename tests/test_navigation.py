"""Navigation tests for the starter map."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key


class NavigationTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        return actor_by_key(self.app, "enterprise")

    def test_move_player_to_neighboring_location(self) -> None:
        result = self.app.navigation_service.move_player(self.app.world, "main_corridor")

        self.assertEqual(result.action_key, "move")
        self.assertEqual(self.app.world.active_location.key, "main_corridor")

    def test_move_player_consumes_edge_cost(self) -> None:
        self.app.world.current_hour = 8
        self.app.world.current_minute = 0

        self.app.navigation_service.move_player(self.app.world, "main_corridor")

        # command_office -> main_corridor costs 3 minutes
        self.assertEqual((self.app.world.current_hour, self.app.world.current_minute), (8, 3))

    def test_move_player_to_unreachable_location_fails(self) -> None:
        with self.assertRaises(ValueError):
            self.app.navigation_service.move_player(self.app.world, "nonexistent_location")

    def test_encounter_on_arrival(self) -> None:
        """Moving to a location with a character produces an encounter message."""
        world = self.app.world
        actor = self._actor()
        # Secretary is at command_office in the morning; move to corridor then cafeteria
        # First put the actor at cafeteria for the test
        actor.location_key = "cafeteria"
        actor.encounter_location_key = None

        # Move player to corridor, then cafeteria
        self.app.navigation_service.move_player(world, "main_corridor")
        result = self.app.navigation_service.move_player(world, "cafeteria")

        self.assertTrue(any("遇到" in m for m in result.messages))
        self.assertEqual(actor.encounter_location_key, "cafeteria")

    def test_no_encounter_when_already_seen(self) -> None:
        """If actor was already encountered at this location, no repeated encounter."""
        world = self.app.world
        actor = self._actor()
        actor.location_key = "cafeteria"
        actor.encounter_location_key = "cafeteria"  # Already encountered
        for other in world.characters:
            if other.key != actor.key:
                other.location_key = "dock"

        self.app.navigation_service.move_player(world, "main_corridor")
        result = self.app.navigation_service.move_player(world, "cafeteria")

        self.assertFalse(any("遇到" in m for m in result.messages))

    def test_schedule_refresh_clears_encounter(self) -> None:
        """When schedule moves a character, encounter state resets."""
        world = self.app.world
        actor = self._actor()
        actor.encounter_location_key = "command_office"

        # Advance to afternoon — secretary moves to training_ground
        world.current_time_slot = TimeSlot.MORNING
        self.app.game_loop.advance_time(world)  # -> afternoon

        self.assertEqual(actor.location_key, "training_ground")
        self.assertIsNone(actor.encounter_location_key)

    # ── Shortest-path & MovePlan tests ──────────────────────────────

    def test_shortest_path_adjacent(self) -> None:
        """Adjacent locations return single-hop path with correct cost."""
        result = self.app.port_map.shortest_path("command_office", "main_corridor")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.path, ("command_office", "main_corridor"))
        self.assertEqual(result.total_cost, 3)

    def test_shortest_path_two_hops(self) -> None:
        """command_office -> cafeteria goes via main_corridor."""
        result = self.app.port_map.shortest_path("command_office", "cafeteria")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.path, ("command_office", "main_corridor", "cafeteria"))
        self.assertEqual(result.total_cost, 3 + 5)  # 8 minutes

    def test_shortest_path_same_location(self) -> None:
        """Same location returns zero-cost single-node path."""
        result = self.app.port_map.shortest_path("dock", "dock")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.path, ("dock",))
        self.assertEqual(result.total_cost, 0)

    def test_shortest_path_unreachable(self) -> None:
        """Nonexistent location returns None."""
        result = self.app.port_map.shortest_path("command_office", "nowhere")
        self.assertIsNone(result)

    def test_reachable_destinations_excludes_current(self) -> None:
        """reachable_destinations does not include the current location."""
        results = self.app.port_map.reachable_destinations("command_office")
        self.assertNotIn("command_office", results)
        self.assertIn("main_corridor", results)
        self.assertIn("dock", results)

    def test_reachable_destinations_respects_visibility(self) -> None:
        """Private locations are excluded without can_see_private."""
        results = self.app.port_map.reachable_destinations("main_corridor", can_see_private=False)
        public_keys = {r for r in results}
        # dormitory_a is private — should be excluded
        self.assertNotIn("dormitory_a", public_keys)

        results_with_private = self.app.port_map.reachable_destinations(
            "main_corridor", can_see_private=True,
        )
        self.assertIn("dormitory_a", results_with_private)

    def test_plan_move_returns_move_plan(self) -> None:
        """plan_move returns structured MovePlan with area info."""
        nav = self.app.navigation_service
        plan = nav.plan_move(self.app.world, "dock")
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan.destination_key, "dock")
        self.assertFalse(plan.is_adjacent)  # 2 hops from command_office
        self.assertTrue(plan.total_cost_minutes > 0)

    def test_available_destinations_sorted(self) -> None:
        """available_destinations returns plans sorted by adjacency then area."""
        nav = self.app.navigation_service
        plans = nav.available_destinations(self.app.world)
        self.assertTrue(len(plans) > 0)
        # All plans should have positive cost
        for plan in plans:
            self.assertTrue(plan.total_cost_minutes > 0)

    def test_execute_multi_hop_move_consumes_total_cost(self) -> None:
        """Moving to a non-adjacent location consumes total path cost."""
        world = self.app.world
        world.current_hour = 8
        world.current_minute = 0
        # command_office -> main_corridor -> dock = 3 + 20 = 23 min
        self.app.navigation_service.execute_move(world, "dock")
        self.assertEqual(world.active_location.key, "dock")
        self.assertEqual((world.current_hour, world.current_minute), (8, 23))

    def test_execute_multi_hop_move_shows_via(self) -> None:
        """Multi-hop move message includes intermediate locations."""
        world = self.app.world
        result = self.app.navigation_service.execute_move(world, "dock")
        self.assertTrue(any("途经" in m for m in result.messages))


if __name__ == "__main__":
    unittest.main()
