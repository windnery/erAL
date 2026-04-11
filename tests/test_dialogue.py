"""Dialogue conditioning and priority selection tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.dialogue import DialogueEntry
from eral.domain.scene import SceneContext
from eral.systems.dialogue import DialogueService


def _scene(
    actor_key: str = "starter_secretary",
    action_key: str = "chat",
    time_slot: str = "morning",
    location_key: str = "command_office",
    location_tags: tuple[str, ...] = ("work",),
    relationship_stage: str = "stranger",
    relationship_rank: int = 0,
    affection: int = 0,
    trust: int = 0,
    obedience: int = 0,
    is_following: bool = False,
    is_on_date: bool = False,
    is_private: bool = False,
    is_same_room: bool = False,
    visible_count: int = 1,
    marks: dict[str, int] | None = None,
) -> SceneContext:
    return SceneContext(
        actor_key=actor_key,
        actor_tags=("secretary",),
        action_key=action_key,
        current_day=1,
        time_slot=time_slot,
        location_key=location_key,
        location_tags=location_tags,
        affection=affection,
        trust=trust,
        obedience=obedience,
        relationship_stage=relationship_stage,
        relationship_rank=relationship_rank,
        is_following=is_following,
        is_on_date=is_on_date,
        is_same_room=is_same_room,
        visible_count=visible_count,
        is_private=is_private,
        marks=marks or {},
    )


class DialogueConditionMatchingTests(unittest.TestCase):
    """Test DialogueService._matches with various scene conditions."""

    def setUp(self) -> None:
        self.service = DialogueService(entries=())

    def test_no_conditions_always_matches(self) -> None:
        entry = DialogueEntry(key="chat", actor_key="starter_secretary", lines=("fallback",))
        self.assertTrue(self.service._matches(entry, _scene()))

    def test_required_stage_must_match(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="starter_secretary", lines=(),
            required_stage="like",
        )
        self.assertFalse(self.service._matches(entry, _scene(relationship_stage="stranger")))
        self.assertTrue(self.service._matches(entry, _scene(relationship_stage="like")))

    def test_time_slots_must_contain_current(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="starter_secretary", lines=(),
            time_slots=("evening", "night"),
        )
        self.assertFalse(self.service._matches(entry, _scene(time_slot="morning")))
        self.assertTrue(self.service._matches(entry, _scene(time_slot="evening")))

    def test_location_keys_must_contain_current(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="starter_secretary", lines=(),
            location_keys=("dock",),
        )
        self.assertFalse(self.service._matches(entry, _scene(location_key="command_office")))
        self.assertTrue(self.service._matches(entry, _scene(location_key="dock")))

    def test_min_affection_threshold(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="starter_secretary", lines=(),
            min_affection=5,
        )
        self.assertFalse(self.service._matches(entry, _scene(affection=3)))
        self.assertTrue(self.service._matches(entry, _scene(affection=5)))

    def test_min_trust_threshold(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="starter_secretary", lines=(),
            min_trust=3,
        )
        self.assertFalse(self.service._matches(entry, _scene(trust=1)))
        self.assertTrue(self.service._matches(entry, _scene(trust=3)))

    def test_min_obedience_threshold(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="starter_secretary", lines=(),
            min_obedience=5,
        )
        self.assertFalse(self.service._matches(entry, _scene(obedience=2)))
        self.assertTrue(self.service._matches(entry, _scene(obedience=5)))

    def test_requires_private(self) -> None:
        entry = DialogueEntry(
            key="tease", actor_key="starter_secretary", lines=(),
            requires_private=True,
        )
        self.assertFalse(self.service._matches(entry, _scene(is_private=False)))
        self.assertTrue(self.service._matches(entry, _scene(is_private=True)))

    def test_requires_date(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="starter_secretary", lines=(),
            requires_date=True,
        )
        self.assertFalse(self.service._matches(entry, _scene(is_on_date=False)))
        self.assertTrue(self.service._matches(entry, _scene(is_on_date=True)))

    def test_requires_following(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="starter_secretary", lines=(),
            requires_following=True,
        )
        self.assertFalse(self.service._matches(entry, _scene(is_following=False)))
        self.assertTrue(self.service._matches(entry, _scene(is_following=True)))


class DialoguePrioritySelectionTests(unittest.TestCase):
    """Test that highest-priority matching entry wins."""

    def test_fallback_selected_when_no_conditions_match(self) -> None:
        entries = (
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("fallback",), priority=0,
            ),
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("friendly variant",), priority=5,
                required_stage="like",
            ),
        )
        service = DialogueService(entries=entries)
        lines = service._lookup("chat", _scene(relationship_stage="stranger"))
        self.assertEqual(lines, ("fallback",))

    def test_higher_priority_variant_selected_when_conditions_match(self) -> None:
        entries = (
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("fallback",), priority=0,
            ),
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("friendly variant",), priority=5,
                required_stage="like",
            ),
        )
        service = DialogueService(entries=entries)
        lines = service._lookup("chat", _scene(relationship_stage="like"))
        self.assertEqual(lines, ("friendly variant",))

    def test_love_variant_beats_like_variant(self) -> None:
        entries = (
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("fallback",), priority=0,
            ),
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("like",), priority=5,
                required_stage="like",
            ),
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("love",), priority=5,
                required_stage="love",
            ),
        )
        service = DialogueService(entries=entries)
        lines = service._lookup("chat", _scene(relationship_stage="love"))
        self.assertEqual(lines, ("love",))

    def test_date_variant_has_highest_priority(self) -> None:
        entries = (
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("fallback",), priority=0,
            ),
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("like",), priority=5,
                required_stage="like",
            ),
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("on date",), priority=6,
                requires_date=True,
            ),
        )
        service = DialogueService(entries=entries)
        lines = service._lookup("chat", _scene(
            relationship_stage="like", is_on_date=True,
        ))
        self.assertEqual(lines, ("on date",))


class DialogueEventKeyLookupTests(unittest.TestCase):
    """Test that event-key entries take precedence over action-key fallback."""

    def test_triggered_event_lines_returned_first(self) -> None:
        entries = (
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("generic chat",), priority=0,
            ),
            DialogueEntry(
                key="secretary_chat_command_office", actor_key="starter_secretary",
                lines=("event-specific",), priority=10,
            ),
        )
        service = DialogueService(entries=entries)
        lines = service.lines_for(
            _scene(action_key="chat"),
            triggered_events=("secretary_chat_command_office",),
        )
        self.assertEqual(lines, ("event-specific",))

    def test_action_key_fallback_when_no_events(self) -> None:
        entries = (
            DialogueEntry(
                key="chat", actor_key="starter_secretary",
                lines=("generic chat",), priority=0,
            ),
        )
        service = DialogueService(entries=entries)
        lines = service.lines_for(_scene(action_key="chat"), triggered_events=())
        self.assertEqual(lines, ("generic chat",))


class DialogueRealDataTests(unittest.TestCase):
    """Integration tests using the real loaded dialogue entries."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = next(actor for actor in self.app.world.characters if actor.key == "starter_secretary")

    def test_chat_at_command_office_triggers_event_dialogue(self) -> None:
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="chat",
        )
        # The event-specific dialogue (priority 10) should win over the fallback (priority 0)
        self.assertTrue(any("报告文件夹" in line for line in result.messages))

    def test_share_snack_fallback_when_no_event_matches(self) -> None:
        # Move to dock where share_snack has no event trigger and time still works
        self.app.world.active_location.key = "dock"
        self.actor.location_key = "dock"
        self.app.world.current_time_slot = self.app.world.current_time_slot.MORNING
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="share_snack",
        )
        # Should get the generic fallback (priority 0)
        self.assertTrue(any("分享" in line or "气氛" in line for line in result.messages))


if __name__ == "__main__":
    unittest.main()
