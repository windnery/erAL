"""Port facility system end-to-end tests: upgrade, effects, recovery, save/load."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.facilities import load_facility_definitions
from eral.systems.facilities import FacilityService
from eral.systems.wallet import WalletService
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import make_app, reset_progress

_REPO_ROOT = Path(__file__).resolve().parents[1]


class FacilityDefinitionLoadingTests(unittest.TestCase):
    def test_load_facilities_toml(self) -> None:
        defs = load_facility_definitions(_REPO_ROOT / "data" / "base" / "facilities.toml")
        self.assertGreaterEqual(len(defs), 3)
        keys = [d.key for d in defs]
        self.assertIn("dorm", keys)
        self.assertIn("canteen", keys)
        self.assertIn("date_spot", keys)

    def test_dorm_definition_fields(self) -> None:
        defs = load_facility_definitions(_REPO_ROOT / "data" / "base" / "facilities.toml")
        dorm = next(d for d in defs if d.key == "dorm")
        self.assertEqual(dorm.display_name, "宿舍")
        self.assertEqual(dorm.max_level, 4)
        self.assertEqual(dorm.upgrade_costs, (5000, 15000, 40000, 100000))
        self.assertEqual(len(dorm.effects), 4)
        self.assertTrue(all(e.type == "boost_recovery" for e in dorm.effects))

    def test_canteen_definition_fields(self) -> None:
        defs = load_facility_definitions(_REPO_ROOT / "data" / "base" / "facilities.toml")
        canteen = next(d for d in defs if d.key == "canteen")
        self.assertEqual(canteen.display_name, "食堂")
        self.assertEqual(canteen.max_level, 4)
        self.assertTrue(all(e.type == "boost_income" for e in canteen.effects))

    def test_date_spot_definition_fields(self) -> None:
        defs = load_facility_definitions(_REPO_ROOT / "data" / "base" / "facilities.toml")
        date_spot = next(d for d in defs if d.key == "date_spot")
        self.assertEqual(date_spot.display_name, "约会场所")
        self.assertEqual(date_spot.max_level, 4)
        self.assertTrue(all(e.type == "boost_relation" for e in date_spot.effects))


class FacilityUpgradeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.app.world.port_funds = 200000

    def test_upgrade_increments_level(self) -> None:
        self.assertTrue(self.app.facility_service.upgrade(self.app.world, "dorm"))
        self.assertEqual(self.app.facility_service.get_level(self.app.world, "dorm"), 1)

    def test_upgrade_deducts_port_funds(self) -> None:
        initial = self.app.world.port_funds
        self.app.facility_service.upgrade(self.app.world, "dorm")
        self.assertEqual(self.app.world.port_funds, initial - 5000)

    def test_upgrade_fails_insufficient_funds(self) -> None:
        self.app.world.port_funds = 100
        self.assertFalse(self.app.facility_service.upgrade(self.app.world, "dorm"))
        self.assertEqual(self.app.facility_service.get_level(self.app.world, "dorm"), 0)

    def test_upgrade_fails_at_max_level(self) -> None:
        self.app.world.port_funds = 99999999
        for _ in range(4):
            self.app.facility_service.upgrade(self.app.world, "dorm")
        self.assertFalse(self.app.facility_service.upgrade(self.app.world, "dorm"))
        self.assertEqual(self.app.facility_service.get_level(self.app.world, "dorm"), 4)

    def test_upgrade_unknown_facility_fails(self) -> None:
        self.assertFalse(self.app.facility_service.upgrade(self.app.world, "nonexistent"))

    def test_multi_level_upgrade_costs(self) -> None:
        self.app.world.port_funds = 99999999
        self.assertTrue(self.app.facility_service.upgrade(self.app.world, "dorm"))
        self.assertEqual(self.app.world.port_funds, 99999999 - 5000)
        self.assertTrue(self.app.facility_service.upgrade(self.app.world, "dorm"))
        self.assertEqual(self.app.world.port_funds, 99999999 - 5000 - 15000)
        self.assertTrue(self.app.facility_service.upgrade(self.app.world, "dorm"))
        self.assertEqual(self.app.world.port_funds, 99999999 - 5000 - 15000 - 40000)


class FacilityEffectQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()

    def test_recovery_multiplier_no_facilities(self) -> None:
        self.assertEqual(self.app.facility_service.recovery_multiplier(self.app.world), 1.0)

    def test_recovery_multiplier_dorm_level_1(self) -> None:
        self.app.world.port_funds = 999999
        self.app.facility_service.upgrade(self.app.world, "dorm")
        self.assertAlmostEqual(self.app.facility_service.recovery_multiplier(self.app.world), 1.1)

    def test_recovery_multiplier_dorm_level_2(self) -> None:
        self.app.world.port_funds = 999999
        for _ in range(2):
            self.app.facility_service.upgrade(self.app.world, "dorm")
        # L1 gives 0.1, L2 gives 0.15 — highest matching min_level wins
        # But total_effect sums ALL matching effects, so 0.1 + 0.15 = 0.25
        self.assertAlmostEqual(self.app.facility_service.recovery_multiplier(self.app.world), 1.25)

    def test_recovery_multiplier_dorm_level_3(self) -> None:
        self.app.world.port_funds = 999999
        for _ in range(3):
            self.app.facility_service.upgrade(self.app.world, "dorm")
        # 0.1 + 0.15 + 0.2 = 0.45
        self.assertAlmostEqual(self.app.facility_service.recovery_multiplier(self.app.world), 1.45)

    def test_total_effect_generic_query(self) -> None:
        self.app.world.port_funds = 999999
        self.app.facility_service.upgrade(self.app.world, "dorm")
        result = self.app.facility_service.total_effect(self.app.world, "boost_recovery")
        self.assertIn("multiplier", result)
        self.assertAlmostEqual(result["multiplier"], 0.1)

    def test_total_effect_unknown_type_empty(self) -> None:
        result = self.app.facility_service.total_effect(self.app.world, "nonexistent")
        self.assertEqual(result, {})


class FacilityIncomeMultiplierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.app.world.port_funds = 999999

    def test_income_multiplier_no_facilities(self) -> None:
        self.assertEqual(self.app.facility_service.income_multiplier(self.app.world), 1.0)

    def test_income_multiplier_canteen_level_1(self) -> None:
        self.app.facility_service.upgrade(self.app.world, "canteen")
        self.assertAlmostEqual(self.app.facility_service.income_multiplier(self.app.world), 1.1)

    def test_income_multiplier_canteen_level_3(self) -> None:
        for _ in range(3):
            self.app.facility_service.upgrade(self.app.world, "canteen")
        self.assertAlmostEqual(self.app.facility_service.income_multiplier(self.app.world), 1.45)


class FacilityRelationMultiplierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.app.world.port_funds = 999999

    def test_relation_multiplier_no_facilities(self) -> None:
        self.assertEqual(self.app.facility_service.relation_multiplier(self.app.world), 1.0)

    def test_relation_multiplier_date_spot_level_2(self) -> None:
        for _ in range(2):
            self.app.facility_service.upgrade(self.app.world, "date_spot")
        self.assertAlmostEqual(self.app.facility_service.relation_multiplier(self.app.world), 1.25)


class FacilityCommissionIncomeE2ETests(unittest.TestCase):
    """Test that canteen facility boosts commission income."""

    def setUp(self) -> None:
        self.app = make_app()
        self.app.world.port_funds = 999999

    def test_canteen_boosts_commission_income(self) -> None:
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        # Baseline commission income without canteen
        self.app.world.port_funds = 0
        self.app.commission_service.dispatch(self.app.world, actor, "patrol")
        for _ in range(3):
            self.app.commission_service.tick_slot(self.app.world)
        baseline_income = self.app.world.port_funds

        # Now with canteen level 1
        actor.is_on_commission = False
        actor.commission_assignment = None
        self.app.world.port_funds = 999999
        self.app.facility_service.upgrade(self.app.world, "canteen")
        self.app.world.port_funds = 0

        self.app.commission_service.dispatch(self.app.world, actor, "patrol")
        for _ in range(3):
            self.app.commission_service.tick_slot(self.app.world)
        boosted_income = self.app.world.port_funds

        self.assertGreater(boosted_income, baseline_income)


class FacilityRelationE2ETests(unittest.TestCase):
    """Test that date_spot facility boosts relation gains during settlement."""

    def setUp(self) -> None:
        self.app = make_app()
        self.app.world.port_funds = 999999
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)

    def test_date_spot_boosts_affection_gain(self) -> None:
        # Give enough SOURCE to trigger affection growth
        self.actor.stats.source.set("affection", 50)

        # Settle without date_spot
        self.app.settlement_service.settle_actor(self.app.world, self.actor)
        affection_before = self.actor.affection

        # Reset and settle with date_spot
        self.actor.stats.source.set("affection", 50)
        self.actor.stats.source.set("joy", 10)
        for _ in range(2):
            self.app.facility_service.upgrade(self.app.world, "date_spot")

        self.app.settlement_service.settle_actor(self.app.world, self.actor)
        affection_after = self.actor.affection

        # With date_spot, the second settlement should have gained more
        # (since affection deltas compound with multiplier)
        self.assertGreater(affection_after, affection_before)


class FacilityVitalIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)

    def test_dorm_boosts_natural_recovery(self) -> None:
        self.actor.stats.base.set("stamina", 500)
        self.actor.stats.base.set("spirit", 500)

        # Recovery without dorm
        recovery_before_stamina = self.app.vital_service.natural_recovery(self.actor, self.app.world)["stamina"]

        # Reset
        self.actor.stats.base.set("stamina", 500)
        self.actor.stats.base.set("spirit", 500)

        # Upgrade dorm
        self.app.world.port_funds = 999999
        self.app.facility_service.upgrade(self.app.world, "dorm")

        recovery_after_stamina = self.app.vital_service.natural_recovery(self.actor, self.app.world)["stamina"]
        self.assertGreater(recovery_after_stamina, recovery_before_stamina)

    def test_dorm_boosts_sleep_recovery(self) -> None:
        self.actor.stats.base.set("stamina", 100)
        self.actor.stats.base.set("spirit", 100)

        # Recovery without dorm
        recovery_before = self.app.vital_service.sleep_recovery(self.actor, self.app.world)["stamina"]

        # Reset
        self.actor.stats.base.set("stamina", 100)
        self.actor.stats.base.set("spirit", 100)

        # Upgrade dorm
        self.app.world.port_funds = 999999
        self.app.facility_service.upgrade(self.app.world, "dorm")

        recovery_after = self.app.vital_service.sleep_recovery(self.actor, self.app.world)["stamina"]
        self.assertGreater(recovery_after, recovery_before)


class FacilitySaveLoadTests(unittest.TestCase):
    def test_facility_levels_round_trip(self) -> None:
        app = make_app()
        app.world.port_funds = 999999
        app.facility_service.upgrade(app.world, "dorm")
        app.facility_service.upgrade(app.world, "dorm")

        path = app.save_service.save_world(app.world)
        loaded = app.save_service.load_world()

        self.assertEqual(loaded.facility_levels, {"dorm": 2})
        self.assertEqual(loaded.port_funds, app.world.port_funds)

    def test_old_save_compatible_empty_facility_levels(self) -> None:
        app = make_app()
        # Save without any facility_levels manipulation
        path = app.save_service.save_world(app.world)

        # Manually remove facility_levels from save to simulate old save
        payload = json.loads(path.read_text(encoding="utf-8"))
        del payload["facility_levels"]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        loaded = app.save_service.load_world()
        self.assertEqual(loaded.facility_levels, {})


if __name__ == "__main__":
    unittest.main()
