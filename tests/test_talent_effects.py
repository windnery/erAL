"""Golden tests for TALENT → SOURCE multiplier effects (slice-active axes).

Verifies that talent_10/13/33/62 produce predictable SOURCE deltas
when apply_source_extra runs before settlement.
"""

from __future__ import annotations

import unittest

from eral.systems.source_extra import apply_source_extra
from tests.support.stages import make_app


class TalentEffectGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.effects = self.app.settlement_service.talent_effects or ()

    def _actor(self, key: str = "laffey"):
        return next(a for a in self.app.world.characters if a.key == key)

    def test_talent_10_courage_doubles_pain_at_value_5(self) -> None:
        """talent_10 胆量: pain SOURCE multiplier = (10 + 2*v)/10."""
        actor = self._actor()
        actor.stats.source.set("pain", 100)
        actor.stats.compat.talent.set(10, 5)

        apply_source_extra(actor.stats, self.effects)

        # (10 + 2*5) / 10 = 2.0  → 100 * 2 = 200
        self.assertEqual(actor.stats.source.get("pain"), 200)

    def test_talent_10_courage_unchanged_at_zero(self) -> None:
        actor = self._actor()
        actor.stats.source.set("pain", 100)
        actor.stats.compat.talent.set(10, 0)

        apply_source_extra(actor.stats, self.effects)

        self.assertEqual(actor.stats.source.get("pain"), 100)

    def test_talent_13_pride_boosts_shame_at_value_3(self) -> None:
        """talent_13 自尊心: shame SOURCE multiplier = (10 + v)/10."""
        actor = self._actor()
        actor.stats.source.set("shame", 100)
        actor.stats.compat.talent.set(13, 3)

        apply_source_extra(actor.stats, self.effects)

        # (10 + 3) / 10 = 1.3  → 100 * 1.3 = 130
        self.assertEqual(actor.stats.source.get("shame"), 130)

    def test_talent_13_pride_unchanged_at_zero(self) -> None:
        actor = self._actor()
        actor.stats.source.set("shame", 100)
        actor.stats.compat.talent.set(13, 0)

        apply_source_extra(actor.stats, self.effects)

        self.assertEqual(actor.stats.source.get("shame"), 100)

    def test_talent_33_shyness_boosts_shame_at_value_2(self) -> None:
        """talent_33 羞耻心: shame SOURCE multiplier = (10 + 2*v)/10."""
        actor = self._actor()
        actor.stats.source.set("shame", 100)
        actor.stats.compat.talent.set(33, 2)

        apply_source_extra(actor.stats, self.effects)

        # (10 + 2*2) / 10 = 1.4  → 100 * 1.4 = 140
        self.assertEqual(actor.stats.source.get("shame"), 140)

    def test_talent_33_shyness_unchanged_at_zero(self) -> None:
        actor = self._actor()
        actor.stats.source.set("shame", 100)
        actor.stats.compat.talent.set(33, 0)

        apply_source_extra(actor.stats, self.effects)

        self.assertEqual(actor.stats.source.get("shame"), 100)

    def test_talent_62_devoted_boosts_service_at_value_2(self) -> None:
        """talent_62 献身的: service SOURCE multiplier = 1.0 + 0.15*v."""
        actor = self._actor()
        actor.stats.source.set("service", 100)
        actor.stats.compat.talent.set(62, 2)

        apply_source_extra(actor.stats, self.effects)

        # 1.0 + 0.15*2 = 1.3  → 100 * 1.3 = 130
        self.assertEqual(actor.stats.source.get("service"), 130)

    def test_talent_62_devoted_unchanged_at_zero(self) -> None:
        actor = self._actor()
        actor.stats.source.set("service", 100)
        actor.stats.compat.talent.set(62, 0)

        apply_source_extra(actor.stats, self.effects)

        self.assertEqual(actor.stats.source.get("service"), 100)

    def test_talent_10_courage_stacks_with_talent_33_shyness_on_separate_keys(self) -> None:
        """Different TALENT axes target different SOURCE keys and do not interfere."""
        actor = self._actor()
        actor.stats.source.set("pain", 100)
        actor.stats.source.set("shame", 100)
        actor.stats.compat.talent.set(10, 5)
        actor.stats.compat.talent.set(33, 2)

        apply_source_extra(actor.stats, self.effects)

        self.assertEqual(actor.stats.source.get("pain"), 200)
        self.assertEqual(actor.stats.source.get("shame"), 140)
