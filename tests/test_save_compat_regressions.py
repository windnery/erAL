"""Fixture-based regression tests for loading legacy saves."""

from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from eral.app.bootstrap import create_application


class SaveCompatibilityRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(self.repo_root)
        temp_saves = self.app.paths.runtime / f"compat_saves_{uuid.uuid4().hex}"
        temp_saves.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, temp_saves, True)
        self.app.paths.saves = temp_saves

    def _load_fixture(self, fixture_name: str):
        fixture_path = self.repo_root / "tests" / "fixtures" / "saves" / fixture_name
        save_path = self.app.save_service.quicksave_path()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")
        return self.app.save_service.load_world()

    def test_loads_legacy_save_without_real_time_and_skin_fields(self) -> None:
        restored = self._load_fixture("legacy_pre_time_and_skin.json")

        self.assertEqual(restored.current_day, 3)
        self.assertEqual(restored.current_time_slot.value, "morning")
        self.assertEqual(restored.current_hour, 8)
        self.assertEqual(restored.current_minute, 0)
        self.assertEqual(restored.active_location.key, "dock")
        self.assertEqual(restored.active_location.display_name, "dock")
        self.assertEqual(restored.inventory, {})
        self.assertEqual(restored.facility_levels, {})

        actor = restored.characters[0]
        self.assertEqual(actor.key, "enterprise")
        self.assertIn("enterprise_default", actor.owned_skins)
        self.assertEqual(actor.equipped_skin_key, "enterprise_default")
        self.assertEqual(actor.removed_slots, ())
        self.assertEqual(actor.affection, 310)
        self.assertEqual(actor.trust, 160)

    def test_loads_legacy_save_without_runtime_actor_fields_and_sparse_stats(self) -> None:
        restored = self._load_fixture("legacy_pre_runtime_fields.json")

        self.assertEqual(restored.current_day, 5)
        self.assertEqual(restored.current_time_slot.value, "evening")
        self.assertEqual(restored.active_location.key, "garden")
        self.assertEqual(restored.active_location.display_name, "garden")

        actor = restored.characters[0]
        self.assertEqual(actor.key, "laffey")
        self.assertEqual(actor.location_key, "garden")
        self.assertEqual(actor.affection, 210)
        self.assertEqual(actor.trust, 110)
        self.assertEqual(actor.obedience, 40)
        self.assertFalse(actor.is_same_room)
        self.assertFalse(actor.is_following)
        self.assertFalse(actor.follow_ready)
        self.assertFalse(actor.is_on_date)
        self.assertTrue(all(value == 0 for value in actor.stats.source.values.values()))
        self.assertTrue(all(value == 0 for value in actor.stats.compat.abl.values.values()))
        self.assertTrue(all(value == 0 for value in actor.stats.compat.talent.values.values()))


if __name__ == "__main__":
    unittest.main()
