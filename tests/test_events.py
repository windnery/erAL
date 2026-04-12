"""Event and dialogue pipeline tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot


class EventPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        return next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")

    def test_chat_triggers_command_office_event_dialogue(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="starter_secretary",
            command_key="chat",
        )

        self.assertIn("secretary_chat_command_office", result.triggered_events)
        self.assertTrue(result.messages)
        self.assertIn("报告文件夹", result.messages[0])

    def test_tease_triggers_private_event_dialogue(self) -> None:
        actor = self._actor()
        actor.affection = 1
        actor.stats.compat.cflag.set(2, 1)
        self.app.relationship_service.update_actor(actor)
        self.app.world.current_time_slot = TimeSlot.NIGHT
        self.app.world.active_location.key = "bathhouse"
        self.app.world.active_location.display_name = "浴场"
        actor.location_key = "bathhouse"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key="starter_secretary",
            command_key="tease",
        )

        self.assertIn("secretary_tease_private", result.triggered_events)
        self.assertIn("胆子就大了", result.messages[1])

    def test_praise_triggers_office_event_dialogue(self) -> None:
        result = self.app.command_service.execute(
            self.app.world,
            actor_key="starter_secretary",
            command_key="praise",
        )

        self.assertIn("secretary_praise_office", result.triggered_events)
        self.assertTrue(any("夸奖" in line or "干劲" in line for line in result.messages))

    def test_confess_triggers_confession_event_dialogue(self) -> None:
        actor = self._actor()
        self.app.world.current_time_slot = TimeSlot.EVENING
        actor.affection = 6
        actor.trust = 4
        actor.stats.compat.cflag.set(2, 6)
        actor.stats.compat.cflag.set(4, 4)
        self.app.relationship_service.update_actor(actor)

        result = self.app.command_service.execute(
            self.app.world,
            actor_key="starter_secretary",
            command_key="confess",
        )

        self.assertIn("secretary_confess_love", result.triggered_events)
        self.assertTrue(any("告白" in line or "回答" in line for line in result.messages))

    def test_same_chat_command_yields_different_dialogue_for_different_characters(self) -> None:
        secretary = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")
        destroyer = next(actor for actor in self.app.world.characters if actor.key == "starter_destroyer")

        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "command_office"
        self.app.world.active_location.display_name = "指挥室"
        secretary.location_key = "command_office"
        destroyer.location_key = "command_office"

        secretary_result = self.app.command_service.execute(
            self.app.world,
            actor_key=secretary.key,
            command_key="chat",
        )
        destroyer_result = self.app.command_service.execute(
            self.app.world,
            actor_key=destroyer.key,
            command_key="chat",
        )

        self.assertNotEqual(secretary_result.messages, destroyer_result.messages)
        self.assertIn("报告文件夹", secretary_result.messages[0])
        self.assertTrue(any("前辈" in line or "精神" in line for line in destroyer_result.messages))

    def test_chat_command_for_cruiser_has_its_own_dialogue(self) -> None:
        cruiser = next(actor for actor in self.app.world.characters if actor.key == "starter_cruiser")

        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        cruiser.location_key = "cafeteria"

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=cruiser.key,
            command_key="chat",
        )

        self.assertIn("cruiser_chat_cafeteria", result.triggered_events)
        self.assertTrue(any("餐后" in line or "从容" in line for line in result.messages))

    def test_clink_cups_has_different_dialogue_by_character(self) -> None:
        secretary = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")
        cruiser = next(actor for actor in self.app.world.characters if actor.key == "starter_cruiser")

        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"
        secretary.location_key = "dock"
        cruiser.location_key = "dock"

        secretary_result = self.app.command_service.execute(
            self.app.world,
            actor_key=secretary.key,
            command_key="clink_cups",
        )
        cruiser_result = self.app.command_service.execute(
            self.app.world,
            actor_key=cruiser.key,
            command_key="clink_cups",
        )

        self.assertNotEqual(secretary_result.messages, cruiser_result.messages)
        self.assertTrue(any("杯" in line or "夜风" in line for line in secretary_result.messages))
        self.assertTrue(any("从容" in line or "碰杯" in line for line in cruiser_result.messages))

    def test_gift_has_different_dialogue_by_character(self) -> None:
        secretary = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")
        destroyer = next(actor for actor in self.app.world.characters if actor.key == "starter_destroyer")

        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        secretary.location_key = "cafeteria"
        destroyer.location_key = "cafeteria"
        secretary.affection = 3
        secretary.trust = 2
        secretary.stats.compat.cflag.set(2, 3)
        secretary.stats.compat.cflag.set(4, 2)
        destroyer.affection = 3
        destroyer.trust = 2
        destroyer.stats.compat.cflag.set(2, 3)
        destroyer.stats.compat.cflag.set(4, 2)
        self.app.relationship_service.refresh_world(self.app.world)
        self.app.command_service.execute(self.app.world, secretary.key, "invite_follow")
        self.app.command_service.execute(self.app.world, secretary.key, "invite_date")
        self.app.command_service.execute(self.app.world, destroyer.key, "invite_follow")
        self.app.command_service.execute(self.app.world, destroyer.key, "invite_date")

        secretary_result = self.app.command_service.execute(
            self.app.world, actor_key=secretary.key, command_key="gift",
        )
        destroyer_result = self.app.command_service.execute(
            self.app.world, actor_key=destroyer.key, command_key="gift",
        )

        self.assertNotEqual(secretary_result.messages, destroyer_result.messages)

    def test_cook_has_different_dialogue_by_character(self) -> None:
        secretary = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")
        destroyer = next(actor for actor in self.app.world.characters if actor.key == "starter_destroyer")

        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "cafeteria")
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        secretary.location_key = "cafeteria"
        destroyer.location_key = "cafeteria"

        secretary_result = self.app.command_service.execute(
            self.app.world, actor_key=secretary.key, command_key="cook",
        )
        destroyer_result = self.app.command_service.execute(
            self.app.world, actor_key=destroyer.key, command_key="cook",
        )

        self.assertNotEqual(secretary_result.messages, destroyer_result.messages)
        self.assertTrue(any("料理" in line or "火候" in line for line in secretary_result.messages))
        self.assertTrue(any("好香" in line or "厨房" in line for line in destroyer_result.messages))

    def test_study_at_library_triggers_secretary_library_event(self) -> None:
        secretary = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")

        self.app.world.current_time_slot = TimeSlot.AFTERNOON
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "library")
        self.app.world.active_location.key = "library"
        self.app.world.active_location.display_name = "图书室"
        secretary.location_key = "library"

        result = self.app.command_service.execute(
            self.app.world, actor_key=secretary.key, command_key="study",
        )

        self.assertIn("secretary_study_library", result.triggered_events)
        self.assertTrue(any("图书室" in line or "书页" in line for line in result.messages))

    def test_rest_at_garden_triggers_destroyer_garden_event(self) -> None:
        destroyer = next(actor for actor in self.app.world.characters if actor.key == "starter_destroyer")

        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "garden")
        self.app.world.active_location.key = "garden"
        self.app.world.active_location.display_name = "庭院"
        destroyer.location_key = "garden"

        result = self.app.command_service.execute(
            self.app.world, actor_key=destroyer.key, command_key="rest",
        )

        self.assertIn("destroyer_rest_garden", result.triggered_events)
        self.assertTrue(any("庭院" in line or "风" in line for line in result.messages))

    def test_care_at_infirmary_triggers_cruiser_infirmary_event(self) -> None:
        cruiser = next(actor for actor in self.app.world.characters if actor.key == "starter_cruiser")

        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        cruiser.location_key = "cafeteria"
        cruiser.affection = 2
        cruiser.stats.compat.cflag.set(2, 2)
        self.app.relationship_service.update_actor(cruiser)
        self.app.command_service.execute(self.app.world, actor_key=cruiser.key, command_key="invite_follow")
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "infirmary")
        self.app.world.active_location.key = "infirmary"
        self.app.world.active_location.display_name = "医务室"
        cruiser.location_key = "infirmary"

        result = self.app.command_service.execute(
            self.app.world, actor_key=cruiser.key, command_key="care",
        )

        self.assertIn("cruiser_care_infirmary", result.triggered_events)
        self.assertTrue(any("医务室" in line or "安静" in line for line in result.messages))

    # ── MARK 条件事件触发 ──

    def test_chat_with_embarrassed_mark_triggers_secretary_mark_event(self) -> None:
        secretary = self._actor()
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "command_office"
        secretary.location_key = "command_office"
        secretary.add_mark("embarrassed", 1)

        result = self.app.command_service.execute(
            self.app.world, actor_key="starter_secretary", command_key="chat",
        )

        self.assertIn("secretary_chat_embarrassed", result.triggered_events)
        self.assertTrue(any("不太适合" in line or "没办法" in line for line in result.messages))

    def test_chat_without_mark_does_not_trigger_mark_event(self) -> None:
        secretary = self._actor()
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "command_office"
        secretary.location_key = "command_office"

        result = self.app.command_service.execute(
            self.app.world, actor_key="starter_secretary", command_key="chat",
        )

        self.assertNotIn("secretary_chat_embarrassed", result.triggered_events)
        self.assertNotIn("secretary_chat_drunk", result.triggered_events)
        self.assertNotIn("secretary_chat_angry", result.triggered_events)

    def test_apologize_with_angry_mark_triggers_destroyer_mark_event(self) -> None:
        destroyer = next(a for a in self.app.world.characters if a.key == "starter_destroyer")
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "command_office"
        destroyer.location_key = "command_office"
        destroyer.add_mark("angry", 1)

        result = self.app.command_service.execute(
            self.app.world, actor_key="starter_destroyer", command_key="apologize",
        )

        self.assertIn("destroyer_apologize_angry", result.triggered_events)
        self.assertTrue(any("没办法继续生气" in line for line in result.messages))

    def test_enterprise_chat_embarrassed_mark_event(self) -> None:
        enterprise = next(a for a in self.app.world.characters if a.key == "enterprise")
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "dock"
        enterprise.location_key = "dock"
        enterprise.add_mark("embarrassed", 1)

        result = self.app.command_service.execute(
            self.app.world, actor_key="enterprise", command_key="chat",
        )

        self.assertIn("enterprise_chat_embarrassed", result.triggered_events)
        self.assertTrue(any("没办法正常" in line for line in result.messages))

    def test_laffey_chat_drunk_mark_event(self) -> None:
        laffey = next(a for a in self.app.world.characters if a.key == "laffey")
        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.world.active_location.key = "dock"
        laffey.location_key = "dock"
        laffey.add_mark("drunk", 1)

        result = self.app.command_service.execute(
            self.app.world, actor_key="laffey", command_key="chat",
        )

        self.assertIn("laffey_chat_drunk", result.triggered_events)
        self.assertTrue(any("最喜欢" in line for line in result.messages))


if __name__ == "__main__":
    unittest.main()
