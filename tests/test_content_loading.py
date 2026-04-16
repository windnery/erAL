"""Tests for static content loading."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.content import (
    load_calendar_definition,
    load_appearance_definitions,
    load_item_definitions,
    load_shopfront_definitions,
    load_skin_definitions,
    load_work_schedule_definitions,
)


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

    def test_load_skin_definitions_exposes_enterprise_shop_and_oath_skins(self) -> None:
        skins = {
            skin.key: skin
            for skin in load_skin_definitions(self.repo_root / "data" / "base" / "skins.toml")
        }

        self.assertEqual(skins["enterprise_oath"].grant_mode, "oath_reward")
        self.assertEqual(skins["enterprise_summer"].shop_visibility, "manual")
        self.assertEqual(skins["enterprise_summer"].tags, ("summer", "swimsuit"))

    def test_load_appearance_definitions_exposes_full_slot_mapping(self) -> None:
        appearances = {
            appearance.key: appearance
            for appearance in load_appearance_definitions(
                self.repo_root / "data" / "base" / "appearances.toml"
            )
        }

        oath = appearances["enterprise_oath"]
        self.assertEqual(oath.portrait_key, "enterprise_oath_main")
        self.assertEqual(oath.slots["headwear"], "oath_crown")
        self.assertEqual(oath.slots["underwear_bottom"], "oath_inner_bottom")
        self.assertEqual(oath.slots["attachment"], "oath_veil")

    def test_load_calendar_definition_exposes_festival_and_season_rules(self) -> None:
        definition = load_calendar_definition(self.repo_root / "data" / "base" / "calendar.toml")

        self.assertEqual(definition.month_lengths[6], 30)
        self.assertEqual(definition.season_for_month(6), "summer")
        self.assertEqual(definition.festivals[0].key, "summer_festival")

    def test_load_work_schedules_exposes_enterprise_office_shift(self) -> None:
        schedules = {
            schedule.key: schedule
            for schedule in load_work_schedule_definitions(
                self.repo_root / "data" / "base" / "work_schedules.toml"
            )
        }

        entry = schedules["enterprise_office_weekday_morning"]
        self.assertEqual(entry.actor_key, "enterprise")
        self.assertEqual(entry.start_time, "09:00")
        self.assertEqual(entry.date_rules["weekdays"], ("mon", "tue", "wed", "thu", "fri"))


if __name__ == "__main__":
    unittest.main()
