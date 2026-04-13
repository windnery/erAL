"""Tests for private location visibility rules."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.map import PortMap, PortConnection, PortMapLocation
from eral.domain.world import CharacterState, WorldState, PortLocation, TimeSlot
from eral.systems.navigation import NavigationService
from eral.systems.companions import CompanionService
from tests.support.real_actors import actor_by_key


def _make_port_map() -> PortMap:
    """Build a minimal port map with public and private locations."""
    return PortMap(
        key="test_port",
        display_name="测试港",
        locations=(
            PortMapLocation(key="corridor", display_name="走廊", zone="hq", tags=("transit",), visibility="public"),
            PortMapLocation(key="office", display_name="办公室", zone="hq", tags=("work",), visibility="public"),
            PortMapLocation(key="dormitory", display_name="宿舍", zone="residential", tags=("residential",), visibility="private"),
            PortMapLocation(key="bathhouse", display_name="浴场", zone="support", tags=("social",), visibility="private"),
            PortMapLocation(key="vault", display_name="密室", zone="hq", tags=("secret",), visibility="hidden"),
        ),
        connections=(
            PortConnection(source="corridor", target="office", bidirectional=True),
            PortConnection(source="corridor", target="dormitory", bidirectional=True),
            PortConnection(source="corridor", target="bathhouse", bidirectional=True),
            PortConnection(source="corridor", target="vault", bidirectional=True),
        ),
    )


class PortMapVisibilityTests(unittest.TestCase):
    def test_public_locations_always_visible(self) -> None:
        port_map = _make_port_map()
        visible = port_map.visible_neighbors("corridor", can_see_private=False)
        self.assertIn("office", visible)

    def test_private_locations_hidden_without_flag(self) -> None:
        port_map = _make_port_map()
        visible = port_map.visible_neighbors("corridor", can_see_private=False)
        self.assertNotIn("dormitory", visible)
        self.assertNotIn("bathhouse", visible)

    def test_private_locations_visible_with_flag(self) -> None:
        port_map = _make_port_map()
        visible = port_map.visible_neighbors("corridor", can_see_private=True)
        self.assertIn("dormitory", visible)
        self.assertIn("bathhouse", visible)

    def test_hidden_locations_never_visible(self) -> None:
        port_map = _make_port_map()
        visible_no_private = port_map.visible_neighbors("corridor", can_see_private=False)
        visible_with_private = port_map.visible_neighbors("corridor", can_see_private=True)
        self.assertNotIn("vault", visible_no_private)
        self.assertNotIn("vault", visible_with_private)

    def test_structural_neighbors_unchanged(self) -> None:
        """neighbors_of still returns all connections regardless of visibility."""
        port_map = _make_port_map()
        all_neighbors = port_map.neighbors_of("corridor")
        self.assertIn("dormitory", all_neighbors)
        self.assertIn("bathhouse", all_neighbors)
        self.assertIn("vault", all_neighbors)
        self.assertIn("office", all_neighbors)


class NavigationVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.port_map = _make_port_map()
        self.companion_service = CompanionService()
        self.nav = NavigationService(
            port_map=self.port_map,
            companion_service=self.companion_service,
        )

    def test_can_see_private_false_by_default(self) -> None:
        app = create_application(Path(__file__).resolve().parents[1])
        self.assertFalse(app.navigation_service.can_see_private(app.world))

    def test_can_see_private_true_when_following(self) -> None:
        app = create_application(Path(__file__).resolve().parents[1])
        actor = actor_by_key(app, "enterprise")
        actor.is_following = True
        self.assertTrue(app.navigation_service.can_see_private(app.world))

    def test_can_see_private_true_when_on_date(self) -> None:
        app = create_application(Path(__file__).resolve().parents[1])
        actor = actor_by_key(app, "enterprise")
        actor.is_on_date = True
        self.assertTrue(app.navigation_service.can_see_private(app.world))

    def test_visible_destinations_excludes_private_by_default(self) -> None:
        app = create_application(Path(__file__).resolve().parents[1])
        destinations = app.navigation_service.visible_destinations(app.world)
        # dormitory_a and bathhouse are private — should not appear
        for key in destinations:
            loc = app.port_map.location_by_key(key)
            self.assertNotEqual(loc.visibility, "private", f"Private location {key} should not be visible")

    def test_visible_destinations_includes_private_when_following(self) -> None:
        app = create_application(Path(__file__).resolve().parents[1])
        # Move to main_corridor first — it's the hub connecting to private locations
        app.navigation_service.move_player(app.world, "main_corridor")
        actor = actor_by_key(app, "enterprise")
        actor.location_key = "main_corridor"
        actor.is_following = True
        destinations = app.navigation_service.visible_destinations(app.world)
        # Now private locations should be visible from main_corridor
        location_keys = list(destinations)
        self.assertTrue(
            any(app.port_map.location_by_key(k).visibility == "private" for k in location_keys),
            "Expected at least one private location to be visible when following",
        )

    def test_move_to_private_blocked_without_follow(self) -> None:
        app = create_application(Path(__file__).resolve().parents[1])
        # Move to main_corridor first so dormitory_a is a structural neighbor
        app.navigation_service.move_player(app.world, "main_corridor")
        with self.assertRaises(ValueError):
            app.navigation_service.move_player(app.world, "dormitory_a")

    def test_move_to_private_allowed_when_following(self) -> None:
        app = create_application(Path(__file__).resolve().parents[1])
        # Move to main_corridor first
        app.navigation_service.move_player(app.world, "main_corridor")
        actor = actor_by_key(app, "enterprise")
        actor.is_following = True
        result = app.navigation_service.move_player(app.world, "dormitory_a")
        self.assertEqual(result.action_key, "move")
        self.assertIn("宿舍A", result.messages[0])

    def test_data_private_locations_have_visibility_field(self) -> None:
        """Verify the real data has visibility='private' on dormitory_a and bathhouse."""
        app = create_application(Path(__file__).resolve().parents[1])
        dorm = app.port_map.location_by_key("dormitory_a")
        bath = app.port_map.location_by_key("bathhouse")
        self.assertEqual(dorm.visibility, "private")
        self.assertEqual(bath.visibility, "private")
        # Public locations default to "public"
        office = app.port_map.location_by_key("command_office")
        self.assertEqual(office.visibility, "public")


if __name__ == "__main__":
    unittest.main()
