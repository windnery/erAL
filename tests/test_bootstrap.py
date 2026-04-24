"""Scaffold tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key


class BootstrapTests(unittest.TestCase):
    def test_create_application_uses_default_config(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)

        self.assertEqual(app.config.game_title, "erAL")
        self.assertEqual(app.world.current_time_slot, TimeSlot.MORNING)
        self.assertEqual(app.world.current_day, 1)
        self.assertEqual(app.world.active_location.key, "command_office")
        self.assertEqual(app.port_map.key, "starter_port")
        self.assertGreaterEqual(len(app.world.characters), 2)
        enterprise = actor_by_key(app, "enterprise")
        laffey = actor_by_key(app, "laffey")
        self.assertEqual(enterprise.location_key, "dock")
        self.assertEqual(laffey.location_key, "cafeteria")
        self.assertFalse(app.world.is_busy)
        self.assertFalse(app.world.is_date_traveling)

    def test_application_bootstrap_exposes_skin_definitions_and_service(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)

        self.assertIn("enterprise_oath", app.skin_service.skin_definitions)
        self.assertIn("enterprise_oath", app.appearance_definitions)

    def test_bootstrap_assigns_default_skin_to_loaded_characters(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        enterprise = actor_by_key(app, "enterprise")

        self.assertIn("enterprise_default", enterprise.owned_skins)
        self.assertEqual(enterprise.equipped_skin_key, "enterprise_default")

    def test_bootstrap_keeps_legacy_character_base_as_initial_only(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        enterprise = actor_by_key(app, "enterprise")

        self.assertEqual(enterprise.stats.base.get("0"), 1200)
        self.assertEqual(enterprise.stats.base.get("1"), 900)
        self.assertEqual(enterprise.base_caps, {})
        self.assertEqual(enterprise.base_recover_rates, {})


if __name__ == "__main__":
    unittest.main()
