"""CLI shop entry and purchase flow tests."""

from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.ui.cli import (
    _appearance_summary,
    _build_menu,
    _open_shopfront,
    _open_skin_shop_by_type,
    _open_skin_wardrobe,
)


class CliShopTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.world.inventory.clear()

    def test_build_menu_includes_general_shop_entry_when_akashi_present(self) -> None:
        self.world.active_location.key = "general_store"
        menu = _build_menu(self.app, self.world)
        shop_items = [item for item in menu["system"] if item[1] == "shop"]

        self.assertIn(("进入明石的杂货店", "shop", "general_shop"), shop_items)

    def test_build_menu_includes_skin_shop_entry_when_shiranui_present(self) -> None:
        self.world.active_location.key = "skin_boutique"
        menu = _build_menu(self.app, self.world)
        shop_items = [item for item in menu["system"] if item[1] == "shop" and item[2] == "skin_shop"]

        self.assertIn(("进入不知火的时装屋", "shop", "skin_shop"), shop_items)

    def test_build_menu_includes_skin_wardrobe_entry(self) -> None:
        menu = _build_menu(self.app, self.world)
        wardrobe_items = [item for item in menu["system"] if item[1] == "skin_wardrobe"]

        self.assertIn(("切换企业皮肤", "skin_wardrobe", "enterprise"), wardrobe_items)

    def test_open_shopfront_purchases_pledge_ring(self) -> None:
        responses = iter(["1"])
        self.world.personal_funds = 1200

        messages = _open_shopfront(
            self.app,
            self.world,
            "general_shop",
            input_fn=lambda _prompt: next(responses),
        )

        self.assertEqual(self.world.personal_funds, 200)
        self.assertEqual(self.world.item_count("pledge_ring"), 1)
        self.assertTrue(any("购买了 誓约之戒" in line for line in messages))

    def test_open_shopfront_reports_insufficient_funds(self) -> None:
        responses = iter(["1"])
        self.world.personal_funds = 999

        messages = _open_shopfront(
            self.app,
            self.world,
            "general_shop",
            input_fn=lambda _prompt: next(responses),
        )

        self.assertEqual(self.world.personal_funds, 999)
        self.assertEqual(self.world.item_count("pledge_ring"), 0)
        self.assertTrue(any("资金不足" in line for line in messages))

    def test_skin_shop_lists_manual_visible_skin_when_enabled(self) -> None:
        self.app.skin_service.skin_definitions["enterprise_summer"] = dataclasses.replace(
            self.app.skin_service.skin_definitions["enterprise_summer"],
            shop_visibility="always",
        )

        messages = _open_skin_shop_by_type(self.app, self.world, input_fn=lambda _prompt: "0")

        self.assertTrue(any("夏日泳装" in line for line in messages))

    def test_skin_shop_purchase_unlocks_skin_for_actor(self) -> None:
        self.app.skin_service.skin_definitions["enterprise_summer"] = dataclasses.replace(
            self.app.skin_service.skin_definitions["enterprise_summer"],
            shop_visibility="always",
        )
        self.world.personal_funds = 2000

        messages = _open_skin_shop_by_type(self.app, self.world, input_fn=lambda _prompt: "1")
        actor = next(actor for actor in self.world.characters if actor.key == "enterprise")

        self.assertIn("enterprise_summer", actor.owned_skins)
        self.assertEqual(self.world.personal_funds, 320)
        self.assertTrue(any("夏日泳装" in line for line in messages))

    def test_actor_skin_summary_uses_equipped_skin_and_slots(self) -> None:
        actor = next(actor for actor in self.world.characters if actor.key == "enterprise")
        actor.owned_skins = {"enterprise_default", "enterprise_oath"}
        actor.equipped_skin_key = "enterprise_oath"

        summary = _appearance_summary(self.app, actor)

        self.assertIn("誓约礼服", summary)
        self.assertIn("头饰:oath_crown", summary)
        self.assertIn("附属:oath_veil", summary)

    def test_skin_wardrobe_equips_owned_skin(self) -> None:
        actor = next(actor for actor in self.world.characters if actor.key == "enterprise")
        actor.owned_skins = {"enterprise_default", "enterprise_oath"}
        actor.equipped_skin_key = "enterprise_default"

        messages = _open_skin_wardrobe(
            self.app,
            self.world,
            "enterprise",
            input_fn=lambda _prompt: "2",
        )

        self.assertEqual(actor.equipped_skin_key, "enterprise_oath")
        self.assertTrue(any("誓约礼服" in line for line in messages))


if __name__ == "__main__":
    unittest.main()
