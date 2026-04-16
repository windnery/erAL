"""Shop service semantics tests."""

from __future__ import annotations

import unittest

from tests.support.stages import make_app


class ShopServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        self.world = self.app.world
        self.shop_service = self.app.shop_service
        self.world.inventory.clear()

    def test_general_shop_lists_pledge_ring(self) -> None:
        item_keys = {item.key for item in self.shop_service.list_items("general_shop")}

        self.assertIn("pledge_ring", item_keys)

    def test_skin_shop_does_not_list_pledge_ring(self) -> None:
        item_keys = {item.key for item in self.shop_service.list_items("skin_shop")}

        self.assertNotIn("pledge_ring", item_keys)

    def test_purchase_fails_when_funds_are_insufficient(self) -> None:
        self.world.personal_funds = 999

        result = self.shop_service.purchase(self.world, "general_shop", "pledge_ring")

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "资金不足。")
        self.assertEqual(self.world.item_count("pledge_ring"), 0)
        self.assertEqual(self.world.personal_funds, 999)

    def test_purchase_succeeds_and_updates_funds_and_inventory(self) -> None:
        self.world.personal_funds = 1200

        result = self.shop_service.purchase(self.world, "general_shop", "pledge_ring")

        self.assertTrue(result.success)
        self.assertEqual(result.total_price, 1000)
        self.assertEqual(self.world.personal_funds, 200)
        self.assertEqual(self.world.item_count("pledge_ring"), 1)


if __name__ == "__main__":
    unittest.main()
