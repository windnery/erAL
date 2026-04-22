"""Tests for initial_stats support in character packs."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application


class InitialStatsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_default_character_has_initial_overrides_applied(self) -> None:
        """Character starting state reflects applied initial overrides from split files."""
        app = create_application(self.repo_root)
        actor = next(actor for actor in app.world.characters if actor.key == "laffey")
        self.assertEqual(actor.affection, 0)
        self.assertEqual(actor.trust, 0)
        self.assertEqual(actor.obedience, 0)
        self.assertEqual(actor.relationship_stage.key, "stranger")

    def test_initial_cflag_values_in_actor(self) -> None:
        """Character pack with cflag overrides reflects them after bootstrap."""
        app = create_application(self.repo_root)
        laffey = next(actor for actor in app.world.characters if actor.key == "laffey")
        self.assertEqual(laffey.affection, 0)
        self.assertEqual(laffey.trust, 0)

    def test_initial_stat_overrides_applied_to_actor(self) -> None:
        """When initial_stats has cflag overrides, the actor reflects them after bootstrap."""
        from eral.content.characters import CharacterDefinition, InitialStatOverrides
        from eral.domain.stats import ActorNumericState
        from eral.content.stat_axes import load_stat_axis_catalog

        stat_axes = load_stat_axis_catalog(self.repo_root / "data" / "base" / "axes")

        overrides = InitialStatOverrides(
            base={"stamina": 500},
            palam={"favor": 2},
            abl={41: 1},
            talent={92: 1},
            cflag={2: 3, 4: 2},
        )
        stats = ActorNumericState.zeroed(stat_axes)

        self.assertEqual(stats.base.get("stamina"), 0)
        self.assertEqual(stats.compat.cflag.get(2), 0)

        from eral.app.bootstrap import _apply_initial_stats
        _apply_initial_stats(stats, overrides)

        self.assertEqual(stats.base.get("stamina"), 500)
        self.assertEqual(stats.palam.get("favor"), 2)
        self.assertEqual(stats.compat.abl.get(41), 1)
        self.assertEqual(stats.compat.talent.get(92), 1)
        self.assertEqual(stats.compat.cflag.get(2), 3)
        self.assertEqual(stats.compat.cflag.get(4), 2)

    def test_initial_stats_with_cflag_syncs_derived_fields(self) -> None:
        """After applying cflag overrides and calling sync_derived_fields, the
        CharacterState convenience fields match."""
        from eral.content.characters import InitialStatOverrides
        from eral.domain.stats import ActorNumericState
        from eral.domain.world import CharacterState
        from eral.content.stat_axes import load_stat_axis_catalog
        from eral.app.bootstrap import _apply_initial_stats

        stat_axes = load_stat_axis_catalog(self.repo_root / "data" / "base" / "axes")

        stats = ActorNumericState.zeroed(stat_axes)
        overrides = InitialStatOverrides(cflag={2: 5, 4: 3, 6: 2})
        _apply_initial_stats(stats, overrides)

        actor = CharacterState(
            key="test",
            display_name="测试",
            location_key="dormitory_a",
            tags=(),
            stats=stats,
        )
        actor.sync_derived_fields()

        self.assertEqual(actor.affection, 5)
        self.assertEqual(actor.trust, 3)
        self.assertEqual(actor.obedience, 2)

    def test_parse_initial_stats_from_toml(self) -> None:
        """_parse_initial_stats correctly parses TOML initial_stats section."""
        from eral.content.characters import _parse_initial_stats

        result = _parse_initial_stats(None)
        self.assertEqual(result.base, {})
        self.assertEqual(result.palam, {})
        self.assertEqual(result.abl, {})
        self.assertEqual(result.talent, {})
        self.assertEqual(result.cflag, {})
        self.assertEqual(result.marks, {})

        result = _parse_initial_stats({})
        self.assertEqual(result.base, {})
        self.assertEqual(result.palam, {})
        self.assertEqual(result.abl, {})
        self.assertEqual(result.talent, {})
        self.assertEqual(result.cflag, {})
        self.assertEqual(result.marks, {})

        raw = {
            "base": {"stamina": 800, "energy": 200},
            "palam": {"favor": 3, "obedience": 1},
            "abl": {"41": 2},
            "talent": {"92": 1},
            "cflag": {"2": 3, "4": 2},
            "marks": {"kissed": 1},
        }
        result = _parse_initial_stats(raw)
        self.assertEqual(result.base, {"stamina": 800, "energy": 200})
        self.assertEqual(result.palam, {"favor": 3, "obedience": 1})
        self.assertEqual(result.abl, {41: 2})
        self.assertEqual(result.talent, {92: 1})
        self.assertEqual(result.cflag, {2: 3, 4: 2})
        self.assertEqual(result.marks, {"kissed": 1})

    def test_character_pack_initial_stats_can_seed_multiple_families(self) -> None:
        app = create_application(self.repo_root)
        actor = next(actor for actor in app.world.characters if actor.key == "javelin")

        self.assertEqual(actor.stats.base.get("stamina"), 450)
        self.assertEqual(actor.stats.palam.get("favor"), 1)
        self.assertEqual(actor.stats.compat.abl.get(41), 1)
        self.assertEqual(actor.stats.compat.talent.get(92), 1)
        self.assertEqual(actor.trust, 0)
        self.assertTrue(actor.has_mark("kissed"))

    def test_enterprise_and_laffey_initial_stats_apply_after_bootstrap(self) -> None:
        app = create_application(self.repo_root)
        enterprise = next(actor for actor in app.world.characters if actor.key == "enterprise")
        laffey = next(actor for actor in app.world.characters if actor.key == "laffey")

        self.assertEqual(enterprise.stats.base.get("stamina"), 1200)
        self.assertEqual(enterprise.stats.base.get("spirit"), 900)
        self.assertEqual(enterprise.stats.palam.get("favor"), 3)
        self.assertEqual(enterprise.stats.compat.abl.get(41), 2)
        self.assertEqual(enterprise.affection, 0)
        self.assertTrue(enterprise.has_mark("confessed"))

        self.assertEqual(laffey.stats.base.get("stamina"), 900)
        self.assertEqual(laffey.stats.palam.get("favor"), 2)
        self.assertEqual(laffey.stats.compat.talent.get(92), 1)
        self.assertEqual(laffey.affection, 0)
        self.assertTrue(laffey.has_mark("kissed"))


if __name__ == "__main__":
    unittest.main()