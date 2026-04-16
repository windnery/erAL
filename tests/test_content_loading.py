"""Tests for static content loading."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.content import load_item_definitions, load_shopfront_definitions


class ContentLoadingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_load_item_definitions_includes_complete_pledge_ring_metadata(self) -> None:
        items = {
            item.key: item for item in load_item_definitions(self.repo_root / "data" / "base" / "items.toml")
        }

        pledge_ring = items["pledge_ring"]
        self.assertEqual(pledge_ring.display_name, "誓约之戒")
        self.assertEqual(pledge_ring.category, "general_shop")
        self.assertEqual(pledge_ring.price, 1000)
        self.assertEqual(
            pledge_ring.description,
            "用于正式誓约的戒指。成功誓约时消耗，失败不会消耗。",
        )

    def test_load_shopfront_definitions_includes_general_and_skin_shops(self) -> None:
        shopfronts = {
            shopfront.key: shopfront
            for shopfront in load_shopfront_definitions(self.repo_root / "data" / "base" / "shopfronts.toml")
        }

        general_shop = shopfronts["general_shop"]
        self.assertEqual(general_shop.display_name, "日常用品店")
        self.assertEqual(general_shop.item_categories, ("general_shop",))

        skin_shop = shopfronts["skin_shop"]
        self.assertEqual(skin_shop.display_name, "皮肤商店")
        self.assertEqual(skin_shop.item_categories, ("skin_shop",))


if __name__ == "__main__":
    unittest.main()
