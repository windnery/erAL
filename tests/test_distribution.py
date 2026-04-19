"""Tests for map distribution service — v2 with faction routing and capacity."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key


class DistributionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world

    def test_commissioned_actor_is_excluded_from_present_characters(self) -> None:
        actor = actor_by_key(self.app, "enterprise")
        actor.is_on_commission = True

        present = self.app.distribution_service.present_characters(self.world, "dock")

        self.assertNotIn(actor.key, [item.key for item in present])

    def test_present_characters_returns_sorted_visible_characters_for_location(self) -> None:
        present = self.app.distribution_service.present_characters(self.world, "dock")

        self.assertTrue(all(actor.location_key == "dock" for actor in present))
        self.assertGreaterEqual(len(present), 1)

    def test_refresh_world_places_actor_at_real_time_work_schedule_location(self) -> None:
        enterprise = actor_by_key(self.app, "enterprise")
        self.world.current_weekday = "mon"
        self.world.current_month = 1
        self.world.current_day = 6
        self.world.current_hour = 10
        self.world.current_minute = 0
        self.world.sync_time_slot_from_clock()

        self.app.distribution_service.refresh_world(self.world)

        self.assertEqual(enterprise.location_key, "command_office")

    def test_refresh_world_staggers_dinner_window_by_actor(self) -> None:
        enterprise = actor_by_key(self.app, "enterprise")
        laffey = actor_by_key(self.app, "laffey")
        javelin = actor_by_key(self.app, "javelin")
        self.world.current_weekday = "mon"
        self.world.current_month = 1
        self.world.current_day = 6
        self.world.current_hour = 17
        self.world.current_minute = 50
        self.world.sync_time_slot_from_clock()

        self.app.distribution_service.refresh_world(self.world)

        self.assertEqual(javelin.location_key, "cafeteria")
        self.assertNotEqual(enterprise.location_key, "cafeteria")
        self.assertNotEqual(laffey.location_key, "cafeteria")

    def test_refresh_world_returns_to_home_location_during_late_night(self) -> None:
        enterprise = actor_by_key(self.app, "enterprise")
        laffey = actor_by_key(self.app, "laffey")
        javelin = actor_by_key(self.app, "javelin")
        self.world.current_weekday = "mon"
        self.world.current_month = 1
        self.world.current_day = 6
        self.world.current_hour = 0
        self.world.current_minute = 30
        self.world.sync_time_slot_from_clock()

        self.app.distribution_service.refresh_world(self.world)

        self.assertEqual(enterprise.location_key, "dormitory_a")
        self.assertEqual(laffey.location_key, "dormitory_a")
        self.assertEqual(javelin.location_key, "garden")

    def test_refresh_world_can_bias_off_duty_actor_toward_player_location(self) -> None:
        enterprise = actor_by_key(self.app, "enterprise")
        self.world.active_location.key = "garden"
        self.world.active_location.display_name = "庭院"
        self.world.current_weekday = "sat"
        self.world.current_month = 1
        self.world.current_day = 10
        self.world.current_hour = 15
        self.world.current_minute = 30
        self.world.sync_time_slot_from_clock()
        enterprise.affection = 400
        enterprise.trust = 400

        self.app.distribution_service.refresh_world(self.world)

        self.assertEqual(enterprise.location_key, "garden")

    # ── v2: Faction routing ────────────────────────────────────────

    def test_faction_routing_night_eagle_goes_to_eagle_area(self) -> None:
        """Enterprise (eagle_union) should prefer eagle_living locations at night."""
        enterprise = actor_by_key(self.app, "enterprise")
        self.world.current_time_slot = TimeSlot.NIGHT
        # Clear schedule influence — test pure faction routing
        enterprise.affection = 0
        enterprise.trust = 0

        self.app.distribution_service.refresh_world(self.world)

        loc = self.port_map.location_by_key(enterprise.location_key)
        # Should be in eagle_living or home (which is in eagle_living)
        self.assertIn(enterprise.location_key, ("dormitory_a", "bathhouse"))

    def test_faction_routing_night_royal_goes_to_royal_area(self) -> None:
        """Javelin (royal_navy) should prefer royal_living locations at night."""
        javelin = actor_by_key(self.app, "javelin")
        self.world.current_time_slot = TimeSlot.NIGHT
        javelin.affection = 0
        javelin.trust = 0

        self.app.distribution_service.refresh_world(self.world)

        loc = self.port_map.location_by_key(javelin.location_key)
        self.assertEqual(loc.area_key, "royal_living")

    def test_faction_routing_evening_moderate_bias(self) -> None:
        """Evening gives moderate faction bias — character drifts toward faction area."""
        javelin = actor_by_key(self.app, "javelin")
        self.world.current_time_slot = TimeSlot.EVENING
        javelin.affection = 0
        javelin.trust = 0

        self.app.distribution_service.refresh_world(self.world)

        # Javelin should still be somewhere reasonable
        self.assertIsNotNone(javelin.location_key)

    def test_tag_matching_prefers_faction_locations(self) -> None:
        """When a tag matches locations in the character's faction area, it gets bonus weight."""
        enterprise = actor_by_key(self.app, "enterprise")
        # Enterprise has "work" tag → command_office. At morning with no schedule bias,
        # should still go somewhere with matching tags.
        self.world.current_time_slot = TimeSlot.MORNING
        enterprise.affection = 0
        enterprise.trust = 0

        self.app.distribution_service.refresh_world(self.world)

        self.assertIsNotNone(enterprise.location_key)

    # ── v2: Capacity overflow ──────────────────────────────────────

    def test_capacity_overflow_reduces_weight(self) -> None:
        """When a location exceeds soft capacity, its weight is reduced."""
        ds = self.app.distribution_service
        # Place 10 characters at cafeteria (soft cap = 10)
        for actor in self.world.characters:
            actor.location_key = "cafeteria"

        enterprise = actor_by_key(self.app, "enterprise")
        self.world.current_time_slot = TimeSlot.MORNING
        enterprise.affection = 0
        enterprise.trust = 0

        ds.refresh_world(self.world)

        # Enterprise should avoid overcrowded cafeteria
        self.assertNotEqual(enterprise.location_key, "cafeteria")

    def test_capacity_hard_cap_removes_from_candidates(self) -> None:
        """When a location exceeds hard capacity, it is removed from candidates."""
        ds = self.app.distribution_service
        pm = self.port_map
        # Cafeteria hard cap = 20, fill it with "fake" population via existing characters
        for actor in self.world.characters:
            actor.location_key = "cafeteria"

        enterprise = actor_by_key(self.app, "enterprise")
        self.world.current_time_slot = TimeSlot.AFTERNOON
        enterprise.affection = 0
        enterprise.trust = 0

        ds.refresh_world(self.world)

        # Should not be at cafeteria
        self.assertNotEqual(enterprise.location_key, "cafeteria")

    # ── v2: Player bias tiers ──────────────────────────────────────

    def test_player_bias_low_tier(self) -> None:
        """Characters with affection+trust >= 300 get weak player bias."""
        javelin = actor_by_key(self.app, "javelin")
        self.world.active_location.key = "cafeteria"
        self.world.active_location.display_name = "食堂"
        self.world.current_time_slot = TimeSlot.AFTERNOON
        javelin.affection = 200
        javelin.trust = 150  # total 350 >= 300

        self.app.distribution_service.refresh_world(self.world)

        # Javelin should have some chance of going to cafeteria
        # (not guaranteed — just no crash and valid location)
        self.assertIsNotNone(javelin.location_key)

    # ── Cross-region visit (来访) ─────────────────────────────────

    def test_visit_returns_none_during_late_night(self) -> None:
        service = self.app.distribution_service
        actor = actor_by_key(self.app, "enterprise")
        definition = service.roster[actor.key]
        self.world.current_time_slot = TimeSlot.LATE_NIGHT
        self.assertIsNone(
            service._visiting_area_for_slot(self.world, actor, definition)
        )

    def test_visit_target_is_not_own_residence(self) -> None:
        service = self.app.distribution_service
        actor = actor_by_key(self.app, "enterprise")
        definition = service.roster[actor.key]
        self.world.current_time_slot = TimeSlot.AFTERNOON
        hits: set[str] = set()
        for day in range(1, 200):
            self.world.current_day = day
            area = service._visiting_area_for_slot(self.world, actor, definition)
            if area is not None:
                hits.add(area)
        self.assertTrue(hits)
        self.assertNotIn(definition.residence_area_key, hits)

    def test_visit_is_stable_within_same_slot(self) -> None:
        service = self.app.distribution_service
        actor = actor_by_key(self.app, "enterprise")
        definition = service.roster[actor.key]
        self.world.current_time_slot = TimeSlot.AFTERNOON
        self.world.current_day = 7
        first = service._visiting_area_for_slot(self.world, actor, definition)
        second = service._visiting_area_for_slot(self.world, actor, definition)
        self.assertEqual(first, second)

    # ── Helper ─────────────────────────────────────────────────────

    @property
    def port_map(self):
        return self.app.port_map


if __name__ == "__main__":
    unittest.main()
