"""Golden tests for SOURCE_EXTRA modifiers (phase-based, eval-free)."""

from __future__ import annotations

import unittest

from eral.content.source_extra import SourceExtraCondition, SourceExtraModifier
from eral.systems.source_extra import apply_source_extra
from tests.support.stages import make_app


class SourceExtraGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()

    def _actor(self, key: str = "laffey"):
        return next(a for a in self.app.world.characters if a.key == key)

    # ------------------------------------------------------------------
    # talent_level 互斥素质测试（用内联数据，不依赖 TOML 具体数值）
    # ------------------------------------------------------------------

    def test_talent_level_two_state_boost_at_v1(self) -> None:
        """互斥 talent：v=1 时提升目标 SOURCE。"""
        actor = self._actor()
        actor.stats.source.set("pain", 100)
        actor.stats.compat.talent.set(10, 1)

        modifier = SourceExtraModifier(
            target_sources=("pain",),
            conditions=(
                SourceExtraCondition(
                    kind="talent_level",
                    talent_index=10,
                    levels=((0, 0.8), (1, 1.2)),
                ),
            ),
        )
        apply_source_extra(actor.stats, (modifier,))

        # v=1 对应 1.2 → 100 * 1.2 = 120
        self.assertEqual(actor.stats.source.get("pain"), 120)

    def test_talent_level_two_state_reduce_at_v0(self) -> None:
        """互斥 talent：v=0 时降低目标 SOURCE。"""
        actor = self._actor()
        actor.stats.source.set("pain", 100)
        actor.stats.compat.talent.set(10, 0)

        modifier = SourceExtraModifier(
            target_sources=("pain",),
            conditions=(
                SourceExtraCondition(
                    kind="talent_level",
                    talent_index=10,
                    levels=((0, 0.8), (1, 1.2)),
                ),
            ),
        )
        apply_source_extra(actor.stats, (modifier,))

        # v=0 对应 0.8 → 100 * 0.8 = 80
        self.assertEqual(actor.stats.source.get("pain"), 80)

    def test_talent_level_three_state_unmatched_returns_one(self) -> None:
        """talent_level 查找不到匹配值时返回 1.0（无效果）。"""
        actor = self._actor()
        actor.stats.source.set("pain", 100)
        actor.stats.compat.talent.set(10, 5)  # 5 不在 levels 中

        modifier = SourceExtraModifier(
            target_sources=("pain",),
            conditions=(
                SourceExtraCondition(
                    kind="talent_level",
                    talent_index=10,
                    levels=((0, 0.8), (1, 1.2)),
                ),
            ),
        )
        apply_source_extra(actor.stats, (modifier,))

        self.assertEqual(actor.stats.source.get("pain"), 100)

    def test_talent_level_stacks_multiplicatively(self) -> None:
        """同一 modifier 的多个 condition 乘叠。"""
        actor = self._actor()
        actor.stats.source.set("shame", 100)
        actor.stats.compat.talent.set(13, 1)
        actor.stats.compat.talent.set(33, 1)

        modifier = SourceExtraModifier(
            target_sources=("shame",),
            conditions=(
                SourceExtraCondition(
                    kind="talent_level",
                    talent_index=13,
                    levels=((0, 0.8), (1, 1.2)),
                ),
                SourceExtraCondition(
                    kind="talent_level",
                    talent_index=33,
                    levels=((0, 0.7), (1, 1.3)),
                ),
            ),
        )
        apply_source_extra(actor.stats, (modifier,))

        # 1.2 * 1.3 = 1.56 → 100 * 1.56 = 156
        self.assertEqual(actor.stats.source.get("shame"), 156)

    def test_talent_level_different_keys_no_interference(self) -> None:
        """不同 modifier 目标不同 SOURCE key，互不干扰。"""
        actor = self._actor()
        actor.stats.source.set("pain", 100)
        actor.stats.source.set("shame", 100)
        actor.stats.compat.talent.set(10, 1)
        actor.stats.compat.talent.set(33, 1)

        pain_mod = SourceExtraModifier(
            target_sources=("pain",),
            conditions=(
                SourceExtraCondition(
                    kind="talent_level",
                    talent_index=10,
                    levels=((0, 0.8), (1, 1.2)),
                ),
            ),
        )
        shame_mod = SourceExtraModifier(
            target_sources=("shame",),
            conditions=(
                SourceExtraCondition(
                    kind="talent_level",
                    talent_index=33,
                    levels=((0, 0.7), (1, 1.3)),
                ),
            ),
        )
        apply_source_extra(actor.stats, (pain_mod, shame_mod))

        self.assertEqual(actor.stats.source.get("pain"), 120)
        self.assertEqual(actor.stats.source.get("shame"), 130)

    # ------------------------------------------------------------------
    # talent_value 单向素质测试（保留，验证旧公式仍可用）
    # ------------------------------------------------------------------

    def test_talent_value_linear_formula(self) -> None:
        """talent_value 公式 (base + coeff*v) / base 仍正常工作。"""
        actor = self._actor()
        actor.stats.source.set("service", 100)
        actor.stats.compat.talent.set(62, 2)

        modifier = SourceExtraModifier(
            target_sources=("service",),
            conditions=(
                SourceExtraCondition(
                    kind="talent_value",
                    talent_index=62,
                    base=100,
                    coeff=15,
                ),
            ),
        )
        apply_source_extra(actor.stats, (modifier,))

        # (100 + 15*2) / 100 = 1.3 → 130
        self.assertEqual(actor.stats.source.get("service"), 130)

    def test_talent_value_zero_returns_one(self) -> None:
        """talent_value v=0 时返回 1.0（无效果）。"""
        actor = self._actor()
        actor.stats.source.set("service", 100)
        actor.stats.compat.talent.set(62, 0)

        modifier = SourceExtraModifier(
            target_sources=("service",),
            conditions=(
                SourceExtraCondition(
                    kind="talent_value",
                    talent_index=62,
                    base=100,
                    coeff=15,
                ),
            ),
        )
        apply_source_extra(actor.stats, (modifier,))

        self.assertEqual(actor.stats.source.get("service"), 100)

    # ------------------------------------------------------------------
    # 从 TOML 加载的数据回归测试（验证 loader 和系统联调）
    # ------------------------------------------------------------------

    def test_loaded_modifiers_apply_without_crash(self) -> None:
        """从 TOML 加载的 modifiers 能正常应用到 actor 上（不崩溃）。"""
        actor = self._actor()
        actor.stats.source.set("13", 100)   # 苦痛
        actor.stats.source.set("17", 100)   # 露出（流向 PALAM 羞耻）
        actor.stats.source.set("15", 100)   # 欲情

        apply_source_extra(actor.stats, self.app.settlement_service.source_extra_modifiers)

        # 只要没抛异常就算通过；具体数值由 TOML 数据决定，不在此硬断言
        self.assertTrue(True)
