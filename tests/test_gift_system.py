"""Tests for gift system — preferences, SOURCE multipliers, inventory consumption."""

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.gifts import GiftDefinition, GiftPreferences, load_gift_definitions
from eral.domain.relationship import RelationshipStage
from eral.domain.world import TimeSlot
from eral.systems.gifts import GiftService

ROOT = Path(__file__).resolve().parent.parent


class GiftPreferenceTests(unittest.TestCase):
    def setUp(self):
        self.gifts = {
            "chocolate_box": GiftDefinition(key="chocolate_box", display_name="巧克力礼盒", tags=("sweet", "romantic"), price=200),
            "jewelry_box": GiftDefinition(key="jewelry_box", display_name="首饰盒", tags=("luxury", "accessory"), price=1500),
            "snack_bag": GiftDefinition(key="snack_bag", display_name="零食大礼包", tags=("sweet", "casual"), price=100),
            "perfume": GiftDefinition(key="perfume", display_name="香水", tags=("luxury", "romantic"), price=800),
            "book_gift": GiftDefinition(key="book_gift", display_name="精装书", tags=("intellectual", "culture"), price=250),
        }

    def test_liked_tag_doubles_multiplier(self):
        prefs = GiftPreferences(liked_tags=("romantic",))
        self.assertEqual(prefs.preference_multiplier(self.gifts["chocolate_box"]), 2.0)

    def test_disliked_tag_reduces_multiplier(self):
        prefs = GiftPreferences(disliked_tags=("casual",))
        self.assertEqual(prefs.preference_multiplier(self.gifts["snack_bag"]), 0.3)

    def test_neutral_returns_one(self):
        prefs = GiftPreferences(liked_tags=("cute",), disliked_tags=("horror",))
        self.assertEqual(prefs.preference_multiplier(self.gifts["book_gift"]), 1.0)

    def test_liked_overrides_disliked(self):
        prefs = GiftPreferences(liked_tags=("sweet",), disliked_tags=("casual",))
        self.assertEqual(prefs.preference_multiplier(self.gifts["snack_bag"]), 2.0)

    def test_empty_preferences(self):
        prefs = GiftPreferences()
        self.assertEqual(prefs.preference_multiplier(self.gifts["perfume"]), 1.0)


class GiftServiceTests(unittest.TestCase):
    def setUp(self):
        gifts = {
            "snack_bag": GiftDefinition(key="snack_bag", display_name="零食大礼包", tags=("sweet",), price=100),
            "chocolate_box": GiftDefinition(key="chocolate_box", display_name="巧克力礼盒", tags=("sweet", "romantic"), price=200),
            "jewelry_box": GiftDefinition(key="jewelry_box", display_name="首饰盒", tags=("luxury",), price=1500),
        }
        prefs = {
            "enterprise": GiftPreferences(liked_tags=("intellectual",)),
            "laffey": GiftPreferences(liked_tags=("sweet",), disliked_tags=("luxury",)),
        }
        self.service = GiftService(gift_definitions=gifts, character_preferences=prefs)

    def test_best_gift_picks_most_expensive(self):
        inv = {"snack_bag": 1, "chocolate_box": 1, "jewelry_box": 1}
        self.assertEqual(self.service.best_gift_in_inventory(inv), "jewelry_box")

    def test_best_gift_skips_zero_stock(self):
        inv = {"snack_bag": 1, "chocolate_box": 0}
        self.assertEqual(self.service.best_gift_in_inventory(inv), "snack_bag")

    def test_best_gift_empty_inventory(self):
        self.assertIsNone(self.service.best_gift_in_inventory({}))

    def test_preference_multiplier_liked(self):
        self.assertEqual(self.service.preference_multiplier("laffey", "chocolate_box"), 2.0)

    def test_preference_multiplier_disliked(self):
        self.assertEqual(self.service.preference_multiplier("laffey", "jewelry_box"), 0.3)

    def test_preference_multiplier_unknown_actor(self):
        self.assertEqual(self.service.preference_multiplier("unknown", "chocolate_box"), 1.0)

    def test_apply_gift_source_doubles(self):
        result = self.service.apply_gift_source({"affection": 150, "trust": 50}, 2.0)
        self.assertEqual(result["affection"], 300)
        self.assertEqual(result["trust"], 100)


class DataLoaderTests(unittest.TestCase):
    def test_load_gifts(self):
        gifts = load_gift_definitions(ROOT / "data" / "base" / "gifts.toml")
        keys = {g.key for g in gifts}
        self.assertIn("bouquet", keys)
        self.assertIn("chocolate_box", keys)
        self.assertIn("jewelry_box", keys)
        self.assertGreater(len(gifts), 5)

    def test_gift_has_tags(self):
        gifts = load_gift_definitions(ROOT / "data" / "base" / "gifts.toml")
        bouquet = next(g for g in gifts if g.key == "bouquet")
        self.assertIn("flower", bouquet.tags)
        self.assertIn("romantic", bouquet.tags)


class IntegrationGiftTests(unittest.TestCase):
    def setUp(self):
        self.app = create_application(ROOT)

    def _setup_date(self, actor_key="enterprise"):
        world = self.app.world
        actor = next(a for a in world.characters if a.key == actor_key)
        world.active_location = self.app.port_map.location_by_key("garden")
        actor.location_key = "garden"
        actor.is_on_date = True
        world.date_partner_key = actor.key
        world.current_time_slot = TimeSlot.AFTERNOON
        actor.affection = 500
        actor.trust = 300
        actor.stats.compat.cflag.set(2, 500)
        actor.stats.compat.cflag.set(4, 300)
        actor.stats.compat.abl.set(9, 3)
        actor.relationship_stage = RelationshipStage(key="like", display_name="喜欢", rank=2)
        actor.sync_compat_from_runtime()
        return actor

    def test_gift_requires_item_in_inventory(self):
        actor = self._setup_date()
        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.app.world, actor.key, "gift")
        self.assertIn("礼物", str(ctx.exception))

    def test_gift_consumes_item(self):
        actor = self._setup_date()
        self.app.world.add_item("chocolate_box", 1)
        self.assertEqual(self.app.world.item_count("chocolate_box"), 1)
        self.app.command_service.execute(self.app.world, actor.key, "gift")
        self.assertEqual(self.app.world.item_count("chocolate_box"), 0)

    def test_gift_records_memory(self):
        actor = self._setup_date()
        self.app.world.add_item("chocolate_box", 1)
        self.app.command_service.execute(self.app.world, actor.key, "gift")
        self.assertTrue(actor.has_memory("gift:chocolate_box"))

    def test_gift_with_liked_preference_gives_bonus(self):
        actor = self._setup_date()
        # Give enterprise intellectual preference via service override
        from eral.content.gifts import GiftPreferences
        self.app.command_service.gift_service.character_preferences["enterprise"] = GiftPreferences(
            liked_tags=("romantic",),
        )
        self.app.world.add_item("chocolate_box", 1)
        result = self.app.command_service.execute(self.app.world, actor.key, "gift")
        self.assertTrue(result.success)
        self.assertIn("affection", result.source_deltas)

    def test_gift_picks_most_expensive(self):
        actor = self._setup_date()
        self.app.world.add_item("snack_bag", 1)
        self.app.world.add_item("chocolate_box", 1)
        self.app.command_service.execute(self.app.world, actor.key, "gift")
        self.assertEqual(self.app.world.item_count("chocolate_box"), 0)
        self.assertEqual(self.app.world.item_count("snack_bag"), 1)


if __name__ == "__main__":
    unittest.main()
