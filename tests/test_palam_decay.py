"""Tests for PALAM natural decay system."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from eral.systems.palam_decay import PalamDecayRule, apply_palam_decay
from tests.support.real_actors import actor_by_key
from tests.support.stages import reset_progress


class PalamDecayRuleTests(unittest.TestCase):
    def test_decay_reduces_palam_value(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.palam.set("lust", 200)

        rules = (PalamDecayRule(palam_key="lust", base_decay=50),)
        applied = apply_palam_decay(actor, rules)

        self.assertEqual(actor.stats.palam.get("lust"), 150)
        self.assertEqual(applied["lust"], 50)

    def test_decay_clamps_to_zero(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.palam.set("pain", 30)

        rules = (PalamDecayRule(palam_key="pain", base_decay=80),)
        apply_palam_decay(actor, rules)

        self.assertEqual(actor.stats.palam.get("pain"), 0)

    def test_decay_skips_zero_palam(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)

        rules = (PalamDecayRule(palam_key="lust", base_decay=50),)
        applied = apply_palam_decay(actor, rules)

        self.assertNotIn("lust", applied)

    def test_decay_applied_on_time_advance(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        world = app.world
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        actor.stats.palam.set("pleasure_c", 300)

        world.current_time_slot = TimeSlot.MORNING
        app.game_loop.advance_time(world)

        self.assertLess(actor.stats.palam.get("pleasure_c"), 300)


if __name__ == "__main__":
    unittest.main()
