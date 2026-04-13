"""Event and dialogue pipeline tests using injected fixtures over real actors."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.dialogue import DialogueEntry
from eral.content.events import EventDefinition
from eral.domain.compat_semantics import CFLAGKey, actor_cflag
from eral.domain.world import TimeSlot
from tests.support.real_actors import actor_by_key, place_player_with_actor, reset_progress


class EventPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.enterprise = actor_by_key(self.app, "enterprise")
        self.laffey = actor_by_key(self.app, "laffey")
        for actor in (self.enterprise, self.laffey):
            reset_progress(actor)
        place_player_with_actor(self.app, self.enterprise)
        self._install_fixtures()

    def _install_fixtures(self) -> None:
        fixture_events = (
            EventDefinition(
                key="enterprise_chat_fixture",
                action_key="chat",
                actor_tags=("enterprise",),
                location_keys=("dock",),
                time_slots=("morning",),
                min_affection=None,
                min_trust=None,
                min_obedience=None,
                required_stage=None,
                requires_date=False,
                requires_private=False,
                required_marks={},
            ),
            EventDefinition(
                key="enterprise_tease_fixture",
                action_key="tease",
                actor_tags=("enterprise",),
                location_keys=("bathhouse",),
                time_slots=("night",),
                min_affection=1,
                min_trust=None,
                min_obedience=None,
                required_stage=None,
                requires_date=False,
                requires_private=True,
                required_marks={},
            ),
            EventDefinition(
                key="enterprise_praise_fixture",
                action_key="praise",
                actor_tags=("enterprise",),
                location_keys=("dock",),
                time_slots=("morning",),
                min_affection=None,
                min_trust=None,
                min_obedience=None,
                required_stage=None,
                requires_date=False,
                requires_private=False,
                required_marks={},
            ),
            EventDefinition(
                key="enterprise_confess_fixture",
                action_key="confess",
                actor_tags=("enterprise",),
                location_keys=("dock",),
                time_slots=("evening",),
                min_affection=6,
                min_trust=4,
                min_obedience=None,
                required_stage="love",
                requires_date=False,
                requires_private=False,
                required_marks={},
            ),
            EventDefinition(
                key="laffey_chat_fixture",
                action_key="chat",
                actor_tags=("laffey",),
                location_keys=("cafeteria",),
                time_slots=("morning",),
                min_affection=None,
                min_trust=None,
                min_obedience=None,
                required_stage=None,
                requires_date=False,
                requires_private=False,
                required_marks={},
            ),
            EventDefinition(
                key="enterprise_gift_fixture",
                action_key="gift",
                actor_tags=("enterprise",),
                location_keys=("cafeteria",),
                time_slots=("evening",),
                min_affection=3,
                min_trust=2,
                min_obedience=None,
                required_stage="like",
                requires_date=True,
                requires_private=False,
                required_marks={},
            ),
            EventDefinition(
                key="laffey_gift_fixture",
                action_key="gift",
                actor_tags=("laffey",),
                location_keys=("cafeteria",),
                time_slots=("evening",),
                min_affection=3,
                min_trust=2,
                min_obedience=None,
                required_stage="like",
                requires_date=True,
                requires_private=False,
                required_marks={},
            ),
            EventDefinition(
                key="enterprise_chat_embarrassed_fixture",
                action_key="chat",
                actor_tags=("enterprise",),
                location_keys=("dock",),
                time_slots=("morning",),
                min_affection=None,
                min_trust=None,
                min_obedience=None,
                required_stage=None,
                requires_date=False,
                requires_private=False,
                required_marks={"embarrassed": 1},
            ),
            EventDefinition(
                key="laffey_chat_drunk_fixture",
                action_key="chat",
                actor_tags=("laffey",),
                location_keys=("dock",),
                time_slots=("evening",),
                min_affection=None,
                min_trust=None,
                min_obedience=None,
                required_stage=None,
                requires_date=False,
                requires_private=False,
                required_marks={"drunk": 1},
            ),
            EventDefinition(
                key="laffey_apologize_angry_fixture",
                action_key="apologize",
                actor_tags=("laffey",),
                location_keys=("cafeteria",),
                time_slots=("morning",),
                min_affection=None,
                min_trust=None,
                min_obedience=None,
                required_stage=None,
                requires_date=False,
                requires_private=False,
                required_marks={"angry": 1},
            ),
        )
        fixture_dialogue = (
            DialogueEntry(key="enterprise_chat_fixture", actor_key="enterprise", lines=("企业把今日汇总推到你面前。",), priority=10),
            DialogueEntry(key="enterprise_tease_fixture", actor_key="enterprise", lines=("她抬眼看你，耳尖一下就红了。", "胆子就大起来了？"), priority=10),
            DialogueEntry(key="enterprise_praise_fixture", actor_key="enterprise", lines=("她把这句夸奖记在心里。",), priority=10),
            DialogueEntry(key="enterprise_confess_fixture", actor_key="enterprise", lines=("她把那句告白说得极轻，却没有移开视线。",), priority=10),
            DialogueEntry(key="laffey_chat_fixture", actor_key="laffey", lines=("拉菲揉着眼睛，还是慢吞吞地回应了你。",), priority=10),
            DialogueEntry(key="enterprise_gift_fixture", actor_key="enterprise", lines=("企业收下礼物时神情郑重。",), priority=10),
            DialogueEntry(key="laffey_gift_fixture", actor_key="laffey", lines=("拉菲抱着礼物，困意都少了一点。",), priority=10),
            DialogueEntry(key="enterprise_chat_embarrassed_fixture", actor_key="enterprise", lines=("她努力维持镇定，但还是有些不太适合直视你。",), priority=20),
            DialogueEntry(key="laffey_chat_drunk_fixture", actor_key="laffey", lines=("她晃着杯子说今晚最喜欢和你说话。",), priority=20),
            DialogueEntry(key="laffey_apologize_angry_fixture", actor_key="laffey", lines=("她嘴上还带着气，但总算肯听你解释。",), priority=20),
        )
        self.app.event_service.events = self.app.event_service.events + fixture_events
        self.app.dialogue_service.entries = self.app.dialogue_service.entries + fixture_dialogue

    def _set_like(self, actor) -> None:
        actor.affection = 3
        actor.trust = 2
        actor_cflag.set(actor, CFLAGKey.AFFECTION, 3)
        actor_cflag.set(actor, CFLAGKey.TRUST, 2)
        self.app.relationship_service.update_actor(actor)

    def _set_love(self, actor) -> None:
        actor.affection = 6
        actor.trust = 4
        actor_cflag.set(actor, CFLAGKey.AFFECTION, 6)
        actor_cflag.set(actor, CFLAGKey.TRUST, 4)
        self.app.relationship_service.update_actor(actor)

    def test_chat_triggers_fixture_dialogue(self) -> None:
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"
        self.enterprise.location_key = "dock"

        result = self.app.command_service.execute(self.app.world, self.enterprise.key, "chat")

        self.assertIn("enterprise_chat_fixture", result.triggered_events)
        self.assertTrue(any("状态" in line or "汇报" in line for line in result.messages))

    def test_tease_triggers_private_fixture_dialogue(self) -> None:
        self.enterprise.affection = 1
        actor_cflag.set(self.enterprise, CFLAGKey.AFFECTION, 1)
        self.app.relationship_service.update_actor(self.enterprise)
        self.app.world.current_time_slot = TimeSlot.NIGHT
        self.app.world.active_location.key = "bathhouse"
        self.app.world.active_location.display_name = "浴场"
        self.enterprise.location_key = "bathhouse"

        result = self.app.command_service.execute(self.app.world, self.enterprise.key, "tease")

        self.assertIn("enterprise_tease_fixture", result.triggered_events)
        self.assertTrue(any("胆子就大起来了" in line for line in result.messages))

    def test_praise_triggers_fixture_dialogue(self) -> None:
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"
        self.enterprise.location_key = "dock"

        result = self.app.command_service.execute(self.app.world, self.enterprise.key, "praise")

        self.assertIn("enterprise_praise_fixture", result.triggered_events)
        self.assertTrue(any("夸奖" in line for line in result.messages))

    def test_confess_triggers_fixture_dialogue(self) -> None:
        self._set_love(self.enterprise)
        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"
        self.enterprise.location_key = "dock"

        result = self.app.command_service.execute(self.app.world, self.enterprise.key, "confess")

        self.assertIn("enterprise_confess_fixture", result.triggered_events)
        self.assertTrue(any("告白" in line for line in result.messages))

    def test_same_command_yields_different_dialogue_for_different_real_characters(self) -> None:
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"
        self.enterprise.location_key = "dock"
        self.laffey.location_key = "cafeteria"

        enterprise_result = self.app.command_service.execute(self.app.world, self.enterprise.key, "chat")
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        self.laffey.location_key = "cafeteria"
        laffey_result = self.app.command_service.execute(self.app.world, self.laffey.key, "chat")

        self.assertNotEqual(enterprise_result.messages, laffey_result.messages)

    def test_gift_has_different_dialogue_by_character(self) -> None:
        self._set_like(self.enterprise)
        self._set_like(self.laffey)
        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        self.enterprise.location_key = "cafeteria"
        self.app.command_service.execute(self.app.world, self.enterprise.key, "invite_follow")
        self.app.command_service.execute(self.app.world, self.enterprise.key, "invite_date")
        enterprise_result = self.app.command_service.execute(self.app.world, self.enterprise.key, "gift")
        self.app.command_service.execute(self.app.world, self.enterprise.key, "end_date")

        self.laffey.location_key = "cafeteria"
        self.app.command_service.execute(self.app.world, self.laffey.key, "invite_follow")
        self.app.command_service.execute(self.app.world, self.laffey.key, "invite_date")
        laffey_result = self.app.command_service.execute(self.app.world, self.laffey.key, "gift")

        self.assertNotEqual(enterprise_result.messages, laffey_result.messages)

    def test_chat_with_embarrassed_mark_triggers_enterprise_mark_event(self) -> None:
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"
        self.enterprise.location_key = "dock"
        self.enterprise.add_mark("embarrassed", 1)

        result = self.app.command_service.execute(self.app.world, self.enterprise.key, "chat")

        self.assertIn("enterprise_chat_embarrassed_fixture", result.triggered_events)
        self.assertTrue(any("正常跟你说话" in line or "靠近" in line for line in result.messages))

    def test_chat_without_mark_does_not_trigger_mark_event(self) -> None:
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"
        self.enterprise.location_key = "dock"

        result = self.app.command_service.execute(self.app.world, self.enterprise.key, "chat")

        self.assertNotIn("enterprise_chat_embarrassed_fixture", result.triggered_events)

    def test_apologize_with_angry_mark_triggers_laffey_mark_event(self) -> None:
        self.app.world.current_time_slot = TimeSlot.MORNING
        self.app.world.active_location.key = "cafeteria"
        self.app.world.active_location.display_name = "食堂"
        self.laffey.location_key = "cafeteria"
        self.laffey.add_mark("angry", 1)

        result = self.app.command_service.execute(self.app.world, self.laffey.key, "apologize")

        self.assertIn("laffey_apologize_angry_fixture", result.triggered_events)
        self.assertTrue(any("原谅" in line or "补偿" in line for line in result.messages))

    def test_laffey_chat_drunk_mark_event(self) -> None:
        self.app.world.current_time_slot = TimeSlot.EVENING
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "码头"
        self.laffey.location_key = "dock"
        self.laffey.add_mark("drunk", 1)

        result = self.app.command_service.execute(self.app.world, self.laffey.key, "chat")

        self.assertIn("laffey_chat_drunk_fixture", result.triggered_events)
        self.assertTrue(any("最喜欢" in line for line in result.messages))


if __name__ == "__main__":
    unittest.main()
