"""Tests for vital statistics system: DOWNBASE, recovery, fatigue, and gate checks."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.systems.vital import VitalService
from eral.systems.command_gates import (
    CommandAvailabilityContext,
    CommandCategoryGate,
    VitalGate,
)
from eral.content.commands import CommandDefinition
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import make_app, reset_progress


_REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_vital_service() -> VitalService:
    return VitalService(
        max_values={"stamina": 2000, "spirit": 1500},
        recover_rates={"stamina": 10, "spirit": 10},
    )


def _make_app_with_vitals():
    app = make_app()
    place_player_with_actor(app, actor_by_key(app, "enterprise"))
    return app


class VitalServiceDownbaseTests(unittest.TestCase):
    def test_apply_downbase_subtracts_from_base(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 2000)
        actor.stats.base.set("1", 1500)

        vital.apply_downbase(actor, {"0": 100, "1": 50})

        self.assertEqual(actor.stats.base.get("0"), 1900)
        self.assertEqual(actor.stats.base.get("1"), 1450)

    def test_apply_downbase_clamps_to_zero(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 30)
        actor.stats.base.set("1", 10)

        vital.apply_downbase(actor, {"0": 100, "1": 50})

        self.assertEqual(actor.stats.base.get("0"), 0)
        self.assertEqual(actor.stats.base.get("1"), 0)

    def test_apply_downbase_accumulates_fatigue(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 2000)
        actor.stats.base.set("1", 1500)
        actor.fatigue = 10

        vital.apply_downbase(actor, {"0": 100, "1": 50})

        self.assertGreater(actor.fatigue, 10)

    def test_apply_downbase_fatigue_formula(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 2000)
        actor.stats.base.set("1", 1500)
        actor.fatigue = 0

        vital.apply_downbase(actor, {"0": 100, "1": 50})

        from eral.systems.fatigue import calc_tired
        expected = calc_tired(100, 50)
        self.assertEqual(actor.fatigue, expected)


class VitalServiceRecoveryTests(unittest.TestCase):
    def test_natural_recovery_increases_stats(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1900)
        actor.stats.base.set("1", 1400)

        result = vital.natural_recovery(actor)

        self.assertGreater(actor.stats.base.get("0"), 1900)
        self.assertGreater(actor.stats.base.get("1"), 1400)
        self.assertIn("stamina", result)
        self.assertIn("spirit", result)

    def test_natural_recovery_clamps_to_max(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1995)
        actor.stats.base.set("1", 1497)

        vital.natural_recovery(actor)

        self.assertLessEqual(actor.stats.base.get("0"), 2000)
        self.assertLessEqual(actor.stats.base.get("1"), 1500)

    def test_natural_recovery_reduces_fatigue(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1900)
        actor.stats.base.set("1", 1400)
        actor.fatigue = 50

        vital.natural_recovery(actor)

        self.assertLess(actor.fatigue, 50)

    def test_natural_recovery_fatigue_floor_is_zero(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1900)
        actor.stats.base.set("1", 1400)
        actor.fatigue = 2

        vital.natural_recovery(actor)

        self.assertGreaterEqual(actor.fatigue, 0)

    def test_sleep_recovery_major_recovery(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 500)
        actor.stats.base.set("1", 300)
        actor.fatigue = 100

        result = vital.sleep_recovery(actor)

        self.assertGreater(actor.stats.base.get("0"), 500)
        self.assertGreater(actor.stats.base.get("1"), 300)
        self.assertLess(actor.fatigue, 100)
        self.assertIn("stamina", result)
        self.assertIn("spirit", result)

    def test_sleep_recovery_stamina_better_than_spirit(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 0)
        actor.stats.base.set("1", 0)
        actor.fatigue = 50

        vital.sleep_recovery(actor)

        stamina_recovered = actor.stats.base.get("0")
        spirit_recovered = actor.stats.base.get("1")
        self.assertGreater(stamina_recovered, spirit_recovered)

    def test_rest_recovery_moderate(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1000)
        actor.stats.base.set("1", 800)
        actor.fatigue = 40

        vital.rest_recovery(actor)

        self.assertGreater(actor.stats.base.get("0"), 1000)
        self.assertGreater(actor.stats.base.get("1"), 800)
        self.assertLess(actor.fatigue, 40)

    def test_bathe_recovery_spirit_focused(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1000)
        actor.stats.base.set("1", 800)
        actor.fatigue = 40

        vital.bathe_recovery(actor)

        self.assertGreater(actor.stats.base.get("0"), 1000)
        self.assertGreater(actor.stats.base.get("1"), 800)
        spirit_delta = actor.stats.base.get("1") - 800
        stamina_delta = actor.stats.base.get("0") - 1000
        self.assertGreater(spirit_delta, stamina_delta)

    def test_restore_generic_interface(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1000)
        actor.stats.base.set("1", 800)
        actor.fatigue = 50

        result = vital.restore(actor, stamina=200, spirit=100, reduce_fatigue=30)

        self.assertEqual(actor.stats.base.get("0"), 1200)
        self.assertEqual(actor.stats.base.get("1"), 900)
        self.assertEqual(actor.fatigue, 20)

    def test_restore_clamps_to_maxbase(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1900)

        vital.restore(actor, stamina=200)

        self.assertLessEqual(actor.stats.base.get("0"), 2000)

    def test_restore_prefers_actor_specific_caps(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.base_caps["0"] = 1200
        actor.stats.base.set("0", 1100)

        vital.restore(actor, stamina=200)

        self.assertEqual(actor.stats.base.get("0"), 1200)

    def test_restore_fatigue_floor(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.fatigue = 5

        vital.restore(actor, reduce_fatigue=100)

        self.assertEqual(actor.fatigue, 0)


class VitalServiceThresholdTests(unittest.TestCase):
    def test_is_fainted_when_stamina_zero(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 0)

        self.assertTrue(vital.is_fainted(actor))

    def test_not_fainted_with_stamina(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1)

        self.assertFalse(vital.is_fainted(actor))

    def test_is_spirit_depleted_when_zero(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("1", 0)

        self.assertTrue(vital.is_spirit_depleted(actor))

    def test_not_spirit_depleted_with_spirit(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("1", 1)

        self.assertFalse(vital.is_spirit_depleted(actor))

    def test_is_decay_both_low(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 300)
        actor.stats.base.set("1", 200)

        self.assertTrue(vital.is_decay(actor))

    def test_not_decay_stamina_ok(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 500)
        actor.stats.base.set("1", 200)

        self.assertFalse(vital.is_decay(actor))

    def test_not_decay_spirit_ok(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 300)
        actor.stats.base.set("1", 500)

        self.assertFalse(vital.is_decay(actor))


class GameLoopRecoveryTests(unittest.TestCase):
    def test_advance_time_applies_natural_recovery(self):
        app = _make_app_with_vitals()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("0", 1900)
        actor.stats.base.set("1", 1400)
        actor.fatigue = 30

        app.game_loop.advance_time(app.world)

        self.assertGreater(actor.stats.base.get("0"), 1900)
        self.assertGreater(actor.stats.base.get("1"), 1400)
        self.assertLess(actor.fatigue, 30)


if __name__ == "__main__":
    unittest.main()
