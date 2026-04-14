"""Economic loop smoke test: 14-day work+commission+upgrade cycle.

Validates the economic balance targets:
- Day 3-5: can afford a mid-range gift (personal funds)
- Day 7-10: can upgrade first facility tier (port funds from commissions)
- Day 14: complete one work+commission+upgrade loop without going broke
"""

from __future__ import annotations

import unittest

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key
from tests.support.stages import make_app, reset_progress, seed_friendly

_REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def _place_at_work(app, actor) -> None:
    """Place player and actor at a work-tagged location."""
    actor.location_key = "command_office"
    app.world.active_location.key = "command_office"
    app.world.active_location.display_name = "指挥室"


def _advance_one_day(app) -> None:
    """Advance through all 6 time slots (= 1 day)."""
    for _ in range(6):
        app.game_loop.advance_time(app.world)


class EconomicBalanceTests(unittest.TestCase):
    """Test economic targets over a 14-day simulated play session."""

    def test_14_day_personal_funds_from_work(self) -> None:
        """Work income: 300 per office_shift, once per day → personal funds grow."""
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        _place_at_work(app, actor)

        for _ in range(14):
            _place_at_work(app, actor)
            app.world.current_time_slot = TimeSlot.MORNING
            app.command_service.execute(app.world, "enterprise", "office_shift")
            _advance_one_day(app)

        # 14 days × 300 = 4200 (some stamina may run out, so lower bound)
        self.assertGreaterEqual(app.world.personal_funds, 3000)

    def test_14_day_port_funds_from_commissions(self) -> None:
        """Commission income: patrol = 1200 every 2 slots, over 14 days."""
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        _place_at_work(app, actor)
        seed_friendly(actor)

        for day in range(14):
            if not actor.is_on_commission:
                app.commission_service.dispatch(app.world, actor, "patrol")
            _advance_one_day(app)

        # patrol = 1200 per completion, ~1 per day (2 slots) = ~14000-16800
        self.assertGreaterEqual(app.world.port_funds, 10000)

    def test_first_facility_upgrade_by_day_10(self) -> None:
        """Target: first facility upgrade (5000) affordable by day 7-10."""
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        _place_at_work(app, actor)
        seed_friendly(actor)

        can_upgrade = False
        for day in range(10):
            if not actor.is_on_commission:
                app.commission_service.dispatch(app.world, actor, "patrol")
            _advance_one_day(app)
            if app.world.port_funds >= 5000:
                can_upgrade = True
                break

        self.assertTrue(can_upgrade, "Should be able to afford first upgrade by day 10")
        self.assertTrue(app.facility_service.upgrade(app.world, "dorm"))
        self.assertEqual(app.facility_service.get_level(app.world, "dorm"), 1)

    def test_14_day_full_economic_loop(self) -> None:
        """Complete loop: work + commission + facility upgrade, not broke by day 14."""
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        _place_at_work(app, actor)
        seed_friendly(actor)

        upgraded = False
        for day in range(14):
            _place_at_work(app, actor)
            app.world.current_time_slot = TimeSlot.MORNING
            app.command_service.execute(app.world, "enterprise", "office_shift")

            if not actor.is_on_commission:
                app.commission_service.dispatch(app.world, actor, "patrol")

            if not upgraded and app.world.port_funds >= 5000:
                upgraded = app.facility_service.upgrade(app.world, "dorm")

            _advance_one_day(app)

        self.assertTrue(upgraded, "Should have upgraded dorm at least once")
        self.assertGreater(app.world.personal_funds, 0, "Should have personal funds from work")
        self.assertGreater(app.world.port_funds, 0, "Should have port funds remaining after upgrade")
        self.assertEqual(app.facility_service.get_level(app.world, "dorm"), 1)

    def test_mid_range_gift_affordable_by_day_5(self) -> None:
        """Target: can afford a mid-range gift (~2000) by day 3-5."""
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        _place_at_work(app, actor)

        for day in range(5):
            _place_at_work(app, actor)
            app.world.current_time_slot = TimeSlot.MORNING
            app.command_service.execute(app.world, "enterprise", "office_shift")
            app.world.current_time_slot = TimeSlot.AFTERNOON
            app.command_service.execute(app.world, "enterprise", "office_shift")
            _advance_one_day(app)

        # 5 days × 2 shifts × 300 = 3000 (minus stamina costs), enough for ~2000 gift
        self.assertGreaterEqual(app.world.personal_funds, 2000)

    def test_work_income_range(self) -> None:
        """Verify work command income values are in the 300-800 range."""
        app = make_app()
        actor = actor_by_key(app, "enterprise")
        reset_progress(actor)
        _place_at_work(app, actor)

        # office_shift
        app.world.current_time_slot = TimeSlot.MORNING
        result = app.command_service.execute(app.world, "enterprise", "office_shift")
        self.assertGreaterEqual(result.funds_delta.get("personal", 0), 300)
        self.assertLessEqual(result.funds_delta.get("personal", 0), 800)

        # extra_shift
        app.world.current_time_slot = TimeSlot.AFTERNOON
        result = app.command_service.execute(app.world, "enterprise", "extra_shift")
        self.assertGreaterEqual(result.funds_delta.get("personal", 0), 300)
        self.assertLessEqual(result.funds_delta.get("personal", 0), 800)

    def test_commission_income_range(self) -> None:
        """Verify commission income values are in the 1200-4000 range."""
        import pathlib
        from eral.content.commissions import load_commission_definitions

        defs = load_commission_definitions(
            pathlib.Path(__file__).resolve().parents[1] / "data" / "base" / "commissions.toml"
        )
        for d in defs:
            self.assertGreaterEqual(d.port_income, 1200, f"{d.key} income too low: {d.port_income}")
            self.assertLessEqual(d.port_income, 4000, f"{d.key} income too high: {d.port_income}")


if __name__ == "__main__":
    unittest.main()
