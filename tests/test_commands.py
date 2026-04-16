"""Command and settlement pipeline tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.content.commands import load_command_definitions
from tests.support.expected import cflag_obedience_delta, favor_delta, trust_delta
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import ABL_INTIMACY_INDEX, make_app, reset_progress, seed_friendly, seed_like, seed_love, seed_stranger, stage_threshold


class CommandPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        place_player_with_actor(self.app, actor)

    def _actor(self):
        return actor_by_key(self.app, "enterprise")

    def test_chat_command_applies_source_and_settles_to_stats(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="chat",
        )
        actor = self._actor()

        self.assertEqual(result.action_key, "chat")
        self.assertEqual(actor.affection, favor_delta({"affection": 50, "joy": 30}, "stranger"))
        self.assertEqual(actor.trust, trust_delta({"affection": 50, "joy": 30}, "stranger"))
        self.assertEqual(actor.stats.palam.get("favor"), 50)
        self.assertEqual(actor.stats.base.get("mood"), 30)
        self.assertEqual(actor.stats.source.get("affection"), 0)

    def test_work_command_updates_obedience_and_trust(self) -> None:
        actor = self._actor()
        self.app.world.active_location.key = "command_office"
        self.app.world.active_location.display_name = "指挥室"
        actor.location_key = "command_office"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="paperwork",
        )

        self.assertEqual(result.action_key, "paperwork")
        self.assertEqual(actor.stats.palam.get("obedience"), 30)
        self.assertEqual(actor.stats.compat.cflag.get(6), cflag_obedience_delta(30))
        self.assertEqual(actor.trust, trust_delta({"affection": 30, "service": 100, "obedience": 30}, "stranger"))

    def test_tease_requires_minimum_affection_and_time_slot(self) -> None:
        actor = self._actor()

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key="enterprise",
                command_key="tease",
            )

        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.NIGHT
        self.app.world.active_location.key = "bathhouse"
        self.app.world.active_location.display_name = "Bathhouse"
        actor.location_key = "bathhouse"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="tease",
        )

        self.assertEqual(result.action_key, "tease")

    def test_tease_failure_reports_time_slot_reason(self) -> None:
        actor = self._actor()
        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.world.active_location.key = "bathhouse"
        self.app.world.active_location.display_name = "浴场"
        actor.location_key = "bathhouse"

        with self.assertRaisesRegex(ValueError, "时段"):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="tease",
            )

    def test_praise_command_increases_affection_and_obedience(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="praise",
        )
        actor = self._actor()

        self.assertEqual(result.action_key, "praise")
        self.assertEqual(actor.affection, favor_delta({"affection": 50, "joy": 30, "obedience": 30}, "stranger"))
        self.assertEqual(actor.trust, trust_delta({"affection": 50, "joy": 30, "obedience": 30}, "stranger"))
        self.assertEqual(actor.stats.palam.get("obedience"), 30)
        self.assertEqual(actor.stats.compat.cflag.get(6), cflag_obedience_delta(30))

    def test_scold_command_settles_negative_palam(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="enterprise",
            command_key="scold",
        )
        actor = self._actor()

        self.assertEqual(result.action_key, "scold")
        self.assertEqual(actor.stats.palam.get("fear"), 100)
        self.assertEqual(actor.stats.palam.get("shame"), 50)
        self.assertEqual(actor.stats.palam.get("obedience"), 60)

    def test_train_together_requires_training_ground(self) -> None:
        actor = self._actor()

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="train_together",
            )

        self.app.game_loop.advance_time(self.app.world)
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "training_ground")
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="train_together",
        )

        self.assertEqual(result.action_key, "train_together")
        self.assertEqual(actor.affection, favor_delta({"affection": 30, "service": 80, "obedience": 40}, "stranger"))
        self.assertEqual(actor.trust, trust_delta({"affection": 30, "service": 80, "obedience": 40}, "stranger"))

    def test_walk_together_requires_following(self) -> None:
        actor = self._actor()

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="walk_together",
            )

    def test_touch_head_is_available_as_basic_daily_command(self) -> None:
        actor = self._actor()

        available = self.app.command_service.available_commands_for_actor(
            self.app.world,
            actor.key,
        )
        keys = [cmd.key for cmd in available]

        self.assertIn("touch_head", keys)

    def test_hug_requires_friendly_stage(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="hug",
            )

        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="hug",
        )

        self.assertEqual(result.action_key, "hug")

    def test_lap_pillow_requires_following(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="lap_pillow",
            )

        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="lap_pillow",
        )

        self.assertEqual(result.action_key, "lap_pillow")

    def test_lap_pillow_failure_reports_follow_reason(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING

        with self.assertRaisesRegex(ValueError, "同行"):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="lap_pillow",
            )

    def test_kiss_applies_kissed_mark(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        seed_love(actor)
        self.app.relationship_service.update_actor(actor)

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="kiss",
        )

        self.assertEqual(result.action_key, "kiss")
        self.assertTrue(actor.has_mark("kissed"))

    def test_confess_applies_confessed_mark(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        seed_love(actor)
        self.app.relationship_service.update_actor(actor)

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="confess",
        )

        self.assertEqual(result.action_key, "confess")
        self.assertTrue(actor.has_mark("confessed"))

    def test_command_categories_load_from_toml(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        commands = {
            command.key: command
            for command in load_command_definitions(repo_root / "data" / "base" / "commands.toml")
        }

        self.assertEqual(commands["chat"].category, "daily")
        self.assertEqual(commands["invite_follow"].category, "follow")
        self.assertEqual(commands["tease"].category, "intimacy")
        self.assertEqual(commands["date_meal"].category, "date")
        self.assertEqual(commands["serve_tea"].category, "daily")

    def test_oath_command_loads_required_items_and_resolution_key(self) -> None:
        command = self.app.command_service.commands["oath"]

        self.assertEqual(command.required_items, {"pledge_ring": 1})
        self.assertEqual(command.resolution_key, "oath")

    def test_oath_failure_keeps_ring_and_does_not_apply_mark(self) -> None:
        actor = self._actor()
        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.MORNING
        self.app.world.inventory["pledge_ring"] = 1
        self.app.command_service.resolution_service.roll = lambda: 0.99

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="oath",
        )

        self.assertEqual(result.action_key, "oath")
        self.assertFalse(result.success)
        self.assertGreater(result.chance, 0.0)
        self.assertLess(result.chance, 0.99)
        self.assertEqual(self.app.world.item_count("pledge_ring"), 1)
        self.assertFalse(actor.has_mark("oath"))
        self.assertEqual(actor.relationship_stage.key, "like")

    def test_oath_success_consumes_ring_and_resolves_stage_to_oath(self) -> None:
        actor = self._actor()
        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.MORNING
        self.app.world.inventory["pledge_ring"] = 1
        self.app.command_service.resolution_service.roll = lambda: 0.0

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="oath",
        )

        self.assertEqual(result.action_key, "oath")
        self.assertTrue(result.success)
        self.assertGreater(result.chance, 0.0)
        self.assertEqual(self.app.world.item_count("pledge_ring"), 0)
        self.assertTrue(actor.has_mark("oath"))
        self.assertEqual(actor.relationship_stage.key, "oath")

    def test_serve_tea_command_increases_trust(self) -> None:
        actor = self._actor()
        self.app.world.active_location.key = "command_office"
        self.app.world.active_location.display_name = "指挥室"
        actor.location_key = "command_office"
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="serve_tea",
        )

        self.assertEqual(result.action_key, "serve_tea")
        self.assertEqual(actor.trust, trust_delta({"affection": 30, "trust": 30, "joy": 20}, "stranger"))
        self.assertEqual(actor.affection, favor_delta({"affection": 30, "trust": 30, "joy": 20}, "stranger"))

    def test_clink_cups_requires_evening_social_location(self) -> None:
        actor = self._actor()

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="clink_cups",
            )

        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        actor.location_key = "cafeteria"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="clink_cups",
        )

        self.assertEqual(result.action_key, "clink_cups")

    def test_care_requires_friendly_stage(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        actor.location_key = "cafeteria"

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="care",
            )

        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="care",
        )

        self.assertEqual(result.action_key, "care")

    def test_rest_command_raises_mood(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.AFTERNOON

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="rest",
        )

        self.assertEqual(result.action_key, "rest")
        self.assertEqual(actor.trust, trust_delta({"trust": 30, "joy": 30}, "stranger"))

    def test_study_requires_work_location(self) -> None:
        actor = self._actor()
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        actor.location_key = "cafeteria"

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="study",
            )

        self.app.world.current_time_slot = self.app.world.current_time_slot.AFTERNOON
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "command_office")
        actor.location_key = "command_office"
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="study",
        )

        self.assertEqual(result.action_key, "study")

    def test_cook_requires_food_location(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="cook",
            )

        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        actor.location_key = "cafeteria"
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="cook",
        )

        self.assertEqual(result.action_key, "cook")

    def test_invite_meal_requires_friendly_stage(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        actor.location_key = "cafeteria"

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="invite_meal",
            )

        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        actor.location_key = "cafeteria"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_meal",
        )

        self.assertEqual(result.action_key, "invite_meal")

    def test_busy_world_hides_daily_commands(self) -> None:
        actor = self._actor()
        self.app.world.is_busy = True

        available = self.app.command_service.available_commands_for_actor(
            self.app.world,
            actor.key,
        )
        keys = [cmd.key for cmd in available]

        self.assertNotIn("chat", keys)
        self.assertNotIn("share_snack", keys)

    def test_follow_rest_requires_following(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.AFTERNOON

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="follow_rest",
            )

        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="follow_rest",
        )

        self.assertEqual(result.action_key, "follow_rest")

    def test_escort_room_requires_like_stage(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="escort_room",
            )

    def test_buy_things_requires_date(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.AFTERNOON

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="buy_things",
            )

        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="buy_things",
        )

        self.assertEqual(result.action_key, "buy_things")

    def test_drink_together_applies_drunk_mark(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        actor.location_key = "cafeteria"
        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="drink_together",
        )

        self.assertEqual(result.action_key, "drink_together")
        self.assertTrue(actor.has_mark("drunk"))

    def test_invite_dark_place_requires_date_and_love(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        seed_love(actor)
        self.app.relationship_service.update_actor(actor)

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="invite_dark_place",
            )

        seed_love(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        self.app.world.active_location.key = "bathhouse"
        self.app.world.active_location.display_name = "浴场"
        actor.location_key = "bathhouse"
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_dark_place",
        )

        self.assertEqual(result.action_key, "invite_dark_place")

    def test_room_kiss_applies_kissed_mark(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        self.app.world.active_location.key = "bathhouse"
        self.app.world.active_location.display_name = "浴场"
        actor.location_key = "bathhouse"
        seed_love(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="room_kiss",
        )

        self.assertEqual(result.action_key, "room_kiss")
        self.assertTrue(actor.has_mark("kissed"))

    def test_apologize_increases_trust_and_removes_angry_mark(self) -> None:
        actor = self._actor()
        actor.add_mark("angry", 1, 1)
        self.assertTrue(actor.has_mark("angry"))

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="apologize",
        )

        self.assertEqual(result.action_key, "apologize")
        self.assertFalse(actor.has_mark("angry"))
        self.assertGreaterEqual(actor.trust, trust_delta({"affection": 30, "trust": 60}, "stranger"))

    def test_help_work_increases_service(self) -> None:
        actor = self._actor()
        self.app.world.active_location.key = "command_office"
        self.app.world.active_location.display_name = "指挥室"
        actor.location_key = "command_office"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="help_work",
        )

        self.assertEqual(result.action_key, "help_work")
        self.assertGreaterEqual(actor.affection, favor_delta({"affection": 60, "trust": 30, "service": 100}, "stranger"))

    def test_pat_cheek_requires_friendly_stage(self) -> None:
        actor = self._actor()

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="pat_cheek",
            )

        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="pat_cheek",
        )

        self.assertEqual(result.action_key, "pat_cheek")
        self.assertTrue(actor.has_mark("embarrassed"))

    def test_poke_cheek_requires_like_stage(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.AFTERNOON

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="poke_cheek",
            )

        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="poke_cheek",
        )

        self.assertEqual(result.action_key, "poke_cheek")
        self.assertTrue(actor.has_mark("embarrassed"))

    def test_read_aloud_at_library(self) -> None:
        actor = self._actor()
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "library")
        actor.location_key = "library"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="read_aloud",
        )

        self.assertEqual(result.action_key, "read_aloud")

    def test_follow_training_requires_following(self) -> None:
        actor = self._actor()
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "training_ground")
        actor.location_key = "training_ground"

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="follow_training",
            )

        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "command_office")
        actor.location_key = "command_office"
        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "training_ground")
        actor.location_key = "training_ground"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="follow_training",
        )

        self.assertEqual(result.action_key, "follow_training")

    def test_follow_meal_requires_following(self) -> None:
        actor = self._actor()
        seed_friendly(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        actor.location_key = "cafeteria"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="follow_meal",
        )

        self.assertEqual(result.action_key, "follow_meal")

    def test_flower_shop_requires_date(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.AFTERNOON

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="flower_shop",
            )

        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="flower_shop",
        )

        self.assertEqual(result.action_key, "flower_shop")

    def test_fishing_date_requires_date_and_harbor(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.AFTERNOON
        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dock")
        actor.location_key = "dock"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="fishing_date",
        )

        self.assertEqual(result.action_key, "fishing_date")

    def test_takeout_bento_requires_date(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.AFTERNOON
        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        actor.location_key = "cafeteria"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="takeout_bento",
        )

        self.assertEqual(result.action_key, "takeout_bento")

    def test_sleep_together_requires_love_and_date_and_private(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.NIGHT

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="sleep_together",
            )

        seed_love(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dormitory_a")
        actor.location_key = "dormitory_a"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="sleep_together",
        )

        self.assertEqual(result.action_key, "sleep_together")

    def test_night_visit_applies_mark(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = self.app.world.current_time_slot.NIGHT
        seed_love(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_follow",
        )
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="invite_date",
        )
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dormitory_a")
        actor.location_key = "dormitory_a"
        self.app.world.current_time_slot = self.app.world.current_time_slot.LATE_NIGHT

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="night_visit",
        )

        self.assertEqual(result.action_key, "night_visit")
        self.assertTrue(actor.has_mark("night_visit"))

    def test_busy_world_blocks_daily_command_execution(self) -> None:
        actor = self._actor()
        self.app.world.is_busy = True

        with self.assertRaisesRegex(ValueError, "忙碌"):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="chat",
            )

    def test_actor_not_present_reason_still_beats_gate_failures(self) -> None:
        actor = self._actor()
        self.app.world.is_busy = True
        actor.location_key = "harbor"

        with self.assertRaisesRegex(ValueError, "目标角色不在当前地点"):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="chat",
            )


if __name__ == "__main__":
    unittest.main()
