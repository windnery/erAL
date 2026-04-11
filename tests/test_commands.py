"""Command and settlement pipeline tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.commands import load_command_definitions


class CommandPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        return next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")

    def test_chat_command_applies_source_and_settles_to_stats(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="starter_secretary",
            command_key="chat",
        )
        actor = self._actor()

        self.assertEqual(result.action_key, "chat")
        self.assertEqual(actor.affection, 2)
        self.assertEqual(actor.trust, 1)
        self.assertEqual(actor.stats.palam.get("favor"), 2)
        self.assertEqual(actor.stats.base.get("mood"), 1)
        self.assertEqual(actor.stats.source.get("affection"), 0)

    def test_work_command_updates_obedience_and_trust(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="starter_secretary",
            command_key="paperwork",
        )
        actor = self._actor()

        self.assertEqual(result.action_key, "paperwork")
        self.assertEqual(actor.stats.palam.get("obedience"), 1)
        self.assertEqual(actor.stats.compat.cflag.get(6), 1)
        self.assertEqual(actor.trust, 2)

    def test_tease_requires_minimum_affection_and_time_slot(self) -> None:
        actor = self._actor()

        with self.assertRaises(ValueError):
            self.app.command_service.execute(
                self.app.world,
                actor_key="starter_secretary",
                command_key="tease",
            )

        actor.affection = 1
        actor.stats.compat.cflag.set(2, 1)
        self.app.relationship_service.update_actor(actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.NIGHT
        self.app.world.active_location.key = "bathhouse"
        self.app.world.active_location.display_name = "Bathhouse"
        actor.location_key = "bathhouse"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key="starter_secretary",
            command_key="tease",
        )

        self.assertEqual(result.action_key, "tease")

    def test_tease_failure_reports_time_slot_reason(self) -> None:
        actor = self._actor()
        actor.affection = 1
        actor.stats.compat.cflag.set(2, 1)
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
            actor_key="starter_secretary",
            command_key="praise",
        )
        actor = self._actor()

        self.assertEqual(result.action_key, "praise")
        self.assertEqual(actor.affection, 2)
        self.assertEqual(actor.trust, 1)
        self.assertEqual(actor.stats.palam.get("obedience"), 1)
        self.assertEqual(actor.stats.compat.cflag.get(6), 1)

    def test_scold_command_settles_negative_palam(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="starter_secretary",
            command_key="scold",
        )
        actor = self._actor()

        self.assertEqual(result.action_key, "scold")
        self.assertEqual(actor.stats.palam.get("fear"), 1)
        self.assertEqual(actor.stats.palam.get("shame"), 1)
        self.assertEqual(actor.stats.palam.get("obedience"), 1)

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
        self.assertEqual(actor.affection, 1)
        self.assertEqual(actor.trust, 1)

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

        actor.affection = 2
        actor.stats.compat.cflag.set(2, 2)
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

        actor.affection = 2
        actor.stats.compat.cflag.set(2, 2)
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
        actor.affection = 6
        actor.trust = 4
        actor.stats.compat.cflag.set(2, 6)
        actor.stats.compat.cflag.set(4, 4)
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
        actor.affection = 6
        actor.trust = 4
        actor.stats.compat.cflag.set(2, 6)
        actor.stats.compat.cflag.set(4, 4)
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

    def test_serve_tea_command_increases_trust(self) -> None:
        actor = self._actor()
        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="serve_tea",
        )

        self.assertEqual(result.action_key, "serve_tea")
        self.assertEqual(actor.trust, 2)
        self.assertEqual(actor.affection, 1)

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

        actor.affection = 2
        actor.stats.compat.cflag.set(2, 2)
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
        self.assertEqual(actor.trust, 2)

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

        actor.affection = 2
        actor.stats.compat.cflag.set(2, 2)
        self.app.relationship_service.update_actor(actor)
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

    def test_busy_world_blocks_daily_command_execution(self) -> None:
        actor = self._actor()
        self.app.world.is_busy = True

        with self.assertRaisesRegex(ValueError, "忙碌"):
            self.app.command_service.execute(
                self.app.world,
                actor_key=actor.key,
                command_key="chat",
            )



if __name__ == "__main__":
    unittest.main()
