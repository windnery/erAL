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
        actor.stats.base.set("stamina", 2000)
        actor.stats.base.set("spirit", 1500)

        vital.apply_downbase(actor, {"stamina": 100, "spirit": 50})

        self.assertEqual(actor.stats.base.get("stamina"), 1900)
        self.assertEqual(actor.stats.base.get("spirit"), 1450)

    def test_apply_downbase_clamps_to_zero(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 30)
        actor.stats.base.set("spirit", 10)

        vital.apply_downbase(actor, {"stamina": 100, "spirit": 50})

        self.assertEqual(actor.stats.base.get("stamina"), 0)
        self.assertEqual(actor.stats.base.get("spirit"), 0)

    def test_apply_downbase_accumulates_fatigue(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 2000)
        actor.stats.base.set("spirit", 1500)
        actor.fatigue = 10

        vital.apply_downbase(actor, {"stamina": 100, "spirit": 50})

        self.assertGreater(actor.fatigue, 10)

    def test_apply_downbase_fatigue_formula(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 2000)
        actor.stats.base.set("spirit", 1500)
        actor.fatigue = 0

        vital.apply_downbase(actor, {"stamina": 100, "spirit": 50})

        from eral.systems.fatigue import calc_tired
        expected = calc_tired(100, 50)
        self.assertEqual(actor.fatigue, expected)


class VitalServiceRecoveryTests(unittest.TestCase):
    def test_natural_recovery_increases_stats(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1900)
        actor.stats.base.set("spirit", 1400)

        result = vital.natural_recovery(actor)

        self.assertGreater(actor.stats.base.get("stamina"), 1900)
        self.assertGreater(actor.stats.base.get("spirit"), 1400)
        self.assertIn("stamina", result)
        self.assertIn("spirit", result)

    def test_natural_recovery_clamps_to_max(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1995)
        actor.stats.base.set("spirit", 1497)

        vital.natural_recovery(actor)

        self.assertLessEqual(actor.stats.base.get("stamina"), 2000)
        self.assertLessEqual(actor.stats.base.get("spirit"), 1500)

    def test_natural_recovery_reduces_fatigue(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1900)
        actor.stats.base.set("spirit", 1400)
        actor.fatigue = 50

        vital.natural_recovery(actor)

        self.assertLess(actor.fatigue, 50)

    def test_natural_recovery_fatigue_floor_is_zero(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1900)
        actor.stats.base.set("spirit", 1400)
        actor.fatigue = 2

        vital.natural_recovery(actor)

        self.assertGreaterEqual(actor.fatigue, 0)

    def test_sleep_recovery_major_recovery(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 500)
        actor.stats.base.set("spirit", 300)
        actor.fatigue = 100

        result = vital.sleep_recovery(actor)

        self.assertGreater(actor.stats.base.get("stamina"), 500)
        self.assertGreater(actor.stats.base.get("spirit"), 300)
        self.assertLess(actor.fatigue, 100)
        self.assertIn("stamina", result)
        self.assertIn("spirit", result)

    def test_sleep_recovery_stamina_better_than_spirit(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 0)
        actor.stats.base.set("spirit", 0)
        actor.fatigue = 50

        vital.sleep_recovery(actor)

        stamina_recovered = actor.stats.base.get("stamina")
        spirit_recovered = actor.stats.base.get("spirit")
        self.assertGreater(stamina_recovered, spirit_recovered)

    def test_rest_recovery_moderate(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1000)
        actor.stats.base.set("spirit", 800)
        actor.fatigue = 40

        vital.rest_recovery(actor)

        self.assertGreater(actor.stats.base.get("stamina"), 1000)
        self.assertGreater(actor.stats.base.get("spirit"), 800)
        self.assertLess(actor.fatigue, 40)

    def test_bathe_recovery_spirit_focused(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1000)
        actor.stats.base.set("spirit", 800)
        actor.fatigue = 40

        vital.bathe_recovery(actor)

        self.assertGreater(actor.stats.base.get("stamina"), 1000)
        self.assertGreater(actor.stats.base.get("spirit"), 800)
        spirit_delta = actor.stats.base.get("spirit") - 800
        stamina_delta = actor.stats.base.get("stamina") - 1000
        self.assertGreater(spirit_delta, stamina_delta)

    def test_restore_generic_interface(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1000)
        actor.stats.base.set("spirit", 800)
        actor.fatigue = 50

        result = vital.restore(actor, stamina=200, spirit=100, reduce_fatigue=30)

        self.assertEqual(actor.stats.base.get("stamina"), 1200)
        self.assertEqual(actor.stats.base.get("spirit"), 900)
        self.assertEqual(actor.fatigue, 20)

    def test_restore_clamps_to_maxbase(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1900)

        vital.restore(actor, stamina=200)

        self.assertLessEqual(actor.stats.base.get("stamina"), 2000)

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
        actor.stats.base.set("stamina", 0)

        self.assertTrue(vital.is_fainted(actor))

    def test_not_fainted_with_stamina(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1)

        self.assertFalse(vital.is_fainted(actor))

    def test_is_spirit_depleted_when_zero(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("spirit", 0)

        self.assertTrue(vital.is_spirit_depleted(actor))

    def test_not_spirit_depleted_with_spirit(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("spirit", 1)

        self.assertFalse(vital.is_spirit_depleted(actor))

    def test_is_decay_both_low(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 300)
        actor.stats.base.set("spirit", 200)

        self.assertTrue(vital.is_decay(actor))

    def test_not_decay_stamina_ok(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 500)
        actor.stats.base.set("spirit", 200)

        self.assertFalse(vital.is_decay(actor))

    def test_not_decay_spirit_ok(self):
        vital = _make_vital_service()
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 300)
        actor.stats.base.set("spirit", 500)

        self.assertFalse(vital.is_decay(actor))


class VitalGateTests(unittest.TestCase):
    def test_fainted_blocks_all_commands(self):
        app = _make_app_with_vitals()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 0)
        vital = app.vital_service
        command = app.command_service.commands["chat"]
        location = app.port_map.location_by_key(app.world.active_location.key)

        context = CommandAvailabilityContext(
            world=app.world,
            actor=actor,
            command=command,
            location_tags=location.tags,
            relationship_service=app.relationship_service,
            vital_service=vital,
        )
        gate = VitalGate()
        reason = gate.failure_reason(context)

        self.assertIsNotNone(reason)
        self.assertIn("晕倒", reason)

    def test_spirit_depleted_blocks_spirit_commands(self):
        app = _make_app_with_vitals()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1000)
        actor.stats.base.set("spirit", 0)
        vital = app.vital_service
        command = app.command_service.commands["chat"]
        location = app.port_map.location_by_key(app.world.active_location.key)

        context = CommandAvailabilityContext(
            world=app.world,
            actor=actor,
            command=command,
            location_tags=location.tags,
            relationship_service=app.relationship_service,
            vital_service=vital,
        )
        gate = VitalGate()
        reason = gate.failure_reason(context)

        self.assertIsNotNone(reason)
        self.assertIn("气力", reason)

    def test_spirit_depleted_allows_free_commands(self):
        app = _make_app_with_vitals()
        reset_progress(actor_by_key(app, "enterprise"))
        actor = actor_by_key(app, "enterprise")
        actor.stats.base.set("stamina", 1000)
        actor.stats.base.set("spirit", 0)
        vital = app.vital_service
        command = CommandDefinition(
            key="free_action",
            display_name="Free Action",
            location_tags=(),
            time_slots=(),
            min_affection=None,
            min_trust=None,
            min_obedience=None,
            required_stage=None,
            operation=None,
            requires_following=None,
            requires_date=None,
            required_marks={},
            apply_marks={},
            remove_marks=(),
            source={},
            downbase={},
            success_tiers=(0.1, 1.0, 2.0),
            category="daily",
        )
        location = app.port_map.location_by_key(app.world.active_location.key)

        context = CommandAvailabilityContext(
            world=app.world,
            actor=actor,
            command=command,
            location_tags=location.tags,
            relationship_service=app.relationship_service,
            vital_service=vital,
        )
        gate = VitalGate()
        reason = gate.failure_reason(context)

        self.assertIsNone(reason)

    def test_healthy_actor_passes_gate(self):
        app = _make_app_with_vitals()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1000)
        actor.stats.base.set("spirit", 500)
        vital = app.vital_service
        command = app.command_service.commands["chat"]
        location = app.port_map.location_by_key(app.world.active_location.key)

        context = CommandAvailabilityContext(
            world=app.world,
            actor=actor,
            command=command,
            location_tags=location.tags,
            relationship_service=app.relationship_service,
            vital_service=vital,
        )
        gate = VitalGate()
        reason = gate.failure_reason(context)

        self.assertIsNone(reason)

    def test_gate_none_when_vital_service_missing(self):
        app = _make_app_with_vitals()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 0)
        command = app.command_service.commands["chat"]
        location = app.port_map.location_by_key(app.world.active_location.key)

        context = CommandAvailabilityContext(
            world=app.world,
            actor=actor,
            command=command,
            location_tags=location.tags,
            relationship_service=app.relationship_service,
            vital_service=None,
        )
        gate = VitalGate()
        reason = gate.failure_reason(context)

        self.assertIsNone(reason)


class GameLoopRecoveryTests(unittest.TestCase):
    def test_advance_time_applies_natural_recovery(self):
        app = _make_app_with_vitals()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 1900)
        actor.stats.base.set("spirit", 1400)
        actor.fatigue = 30

        app.game_loop.advance_time(app.world)

        self.assertGreater(actor.stats.base.get("stamina"), 1900)
        self.assertGreater(actor.stats.base.get("spirit"), 1400)
        self.assertLess(actor.fatigue, 30)


class CommandIntegrationTests(unittest.TestCase):
    def test_command_applies_downbase_and_fatigue(self):
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 2000)
        actor.stats.base.set("spirit", 1500)
        place_player_with_actor(app, actor)
        initial_stamina = actor.stats.base.get("stamina")
        initial_spirit = actor.stats.base.get("spirit")
        initial_fatigue = actor.fatigue

        app.command_service.execute(app.world, actor_key="enterprise", command_key="chat")

        self.assertLess(actor.stats.base.get("stamina"), initial_stamina)
        self.assertLess(actor.stats.base.get("spirit"), initial_spirit)
        self.assertGreater(actor.fatigue, initial_fatigue)

    def test_recovery_command_rest(self):
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 500)
        actor.stats.base.set("spirit", 300)
        actor.fatigue = 50
        app.world.current_time_slot = app.world.current_time_slot.AFTERNOON
        actor.location_key = "dormitory_a"
        app.world.active_location.key = "dormitory_a"
        app.world.active_location.display_name = "宿舍A"
        place_player_with_actor(app, actor)

        app.command_service.execute(app.world, actor_key="enterprise", command_key="nap")

        self.assertLess(actor.fatigue, 50)

    def test_fainted_actor_cannot_execute_commands(self):
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 0)
        place_player_with_actor(app, actor)

        with self.assertRaises(ValueError):
            app.command_service.execute(app.world, actor_key="enterprise", command_key="chat")


class MaxbaseLoadingTests(unittest.TestCase):
    def test_load_maxbase_includes_recover_rates(self):
        from eral.content.maxbase import load_maxbase

        maxbase = load_maxbase(_REPO_ROOT / "data" / "base" / "maxbase.toml")

        self.assertIn("stamina", maxbase.max_values)
        self.assertIn("spirit", maxbase.max_values)
        self.assertEqual(maxbase.max_values["stamina"], 2000)
        self.assertEqual(maxbase.max_values["spirit"], 1500)
        self.assertIn("stamina", maxbase.recover_rates)
        self.assertIn("spirit", maxbase.recover_rates)
        self.assertEqual(maxbase.recover_rates["stamina"], 10)
        self.assertEqual(maxbase.recover_rates["spirit"], 10)


class FaintHandlingTests(unittest.TestCase):
    """Test that fainting triggers sleep recovery and advances time to dawn."""

    def test_faint_sets_flag_and_sleep_recovers(self):
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 5)
        actor.stats.base.set("spirit", 500)
        actor.fatigue = 30
        place_player_with_actor(app, actor)

        result = app.command_service.execute(
            app.world, actor_key="enterprise", command_key="chat",
        )

        self.assertTrue(result.fainted)
        self.assertGreater(actor.stats.base.get("stamina"), 0)
        self.assertLess(actor.fatigue, 30)

    def test_no_faint_when_stamina_remains(self):
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 2000)
        actor.stats.base.set("spirit", 1500)
        place_player_with_actor(app, actor)

        result = app.command_service.execute(
            app.world, actor_key="enterprise", command_key="chat",
        )

        self.assertFalse(result.fainted)

    def test_faint_advances_time_to_dawn(self):
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.base.set("stamina", 5)
        actor.stats.base.set("spirit", 500)
        place_player_with_actor(app, actor)
        app.world.current_time_slot = app.world.current_time_slot.AFTERNOON
        app.world.current_day = 3

        app.command_service.execute(
            app.world, actor_key="enterprise", command_key="chat",
        )

        self.assertEqual(app.world.current_time_slot, app.world.current_time_slot.DAWN)
        self.assertGreater(app.world.current_day, 3)


if __name__ == "__main__":
    unittest.main()