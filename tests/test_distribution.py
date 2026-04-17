"""Tests for lightweight map distribution helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application


class DistributionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def test_commissioned_actor_is_excluded_from_present_characters(self) -> None:
        actor = next(actor for actor in self.app.world.characters if actor.key == "enterprise")
        actor.is_on_commission = True

        present = self.app.distribution_service.present_characters(self.app.world, "dock")

        self.assertNotIn(actor.key, [item.key for item in present])

    def test_present_characters_returns_sorted_visible_characters_for_location(self) -> None:
        present = self.app.distribution_service.present_characters(self.app.world, "dock")

        self.assertTrue(all(actor.location_key == "dock" for actor in present))
        self.assertGreaterEqual(len(present), 1)


if __name__ == "__main__":
    unittest.main()
