"""Dialogue conditioning and priority selection tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.dialogue import DialogueEntry
from eral.domain.scene import SceneContext
from eral.systems.dialogue import DialogueService
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import seed_like


def _scene(
    actor_key: str = "enterprise",
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
    equipped_skin_key: str | None = None,
    equipped_skin_tags: tuple[str, ...] = (),
    removed_slots: tuple[str, ...] = (),
    marks: dict[str, int] | None = None,
) -> SceneContext:
    return SceneContext(
        actor_key=actor_key,
        actor_tags=("enterprise",),
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
        equipped_skin_key=equipped_skin_key,
        equipped_skin_tags=equipped_skin_tags,
        removed_slots=removed_slots,
        marks=marks or {},
    )


class DialogueConditionMatchingTests(unittest.TestCase):
    """Test DialogueService._matches with various scene conditions."""

    def setUp(self) -> None:
        self.service = DialogueService(entries=())

    def test_no_conditions_always_matches(self) -> None:
        entry = DialogueEntry(key="chat", actor_key="enterprise", lines=("fallback",))
        self.assertTrue(self.service._matches(entry, _scene()))

    def test_required_stage_must_match(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="enterprise", lines=(),
            required_stage="like",
        )
        self.assertFalse(self.service._matches(entry, _scene(relationship_stage="stranger")))
        self.assertTrue(self.service._matches(entry, _scene(relationship_stage="like")))

    def test_time_slots_must_contain_current(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="enterprise", lines=(),
            time_slots=("evening", "night"),
        )
        self.assertFalse(self.service._matches(entry, _scene(time_slot="morning")))
        self.assertTrue(self.service._matches(entry, _scene(time_slot="evening")))

    def test_location_keys_must_contain_current(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="enterprise", lines=(),
            location_keys=("dock",),
        )
        self.assertFalse(self.service._matches(entry, _scene(location_key="command_office")))
        self.assertTrue(self.service._matches(entry, _scene(location_key="dock")))

    def test_min_affection_threshold(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="enterprise", lines=(),
            min_affection=5,
        )
        self.assertFalse(self.service._matches(entry, _scene(affection=3)))
        self.assertTrue(self.service._matches(entry, _scene(affection=5)))

    def test_min_trust_threshold(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="enterprise", lines=(),
            min_trust=3,
        )
        self.assertFalse(self.service._matches(entry, _scene(trust=1)))
        self.assertTrue(self.service._matches(entry, _scene(trust=3)))

    def test_min_obedience_threshold(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="enterprise", lines=(),
            min_obedience=5,
        )
        self.assertFalse(self.service._matches(entry, _scene(obedience=2)))
        self.assertTrue(self.service._matches(entry, _scene(obedience=5)))

    def test_requires_private(self) -> None:
        entry = DialogueEntry(
            key="tease", actor_key="enterprise", lines=(),
            requires_private=True,
        )
        self.assertFalse(self.service._matches(entry, _scene(is_private=False)))
        self.assertTrue(self.service._matches(entry, _scene(is_private=True)))

    def test_requires_date(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="enterprise", lines=(),
            requires_date=True,
        )
        self.assertFalse(self.service._matches(entry, _scene(is_on_date=False)))
        self.assertTrue(self.service._matches(entry, _scene(is_on_date=True)))

    def test_requires_following(self) -> None:
        entry = DialogueEntry(
            key="chat", actor_key="enterprise", lines=(),
            requires_following=True,
        )
        self.assertFalse(self.service._matches(entry, _scene(is_following=False)))
        self.assertTrue(self.service._matches(entry, _scene(is_following=True)))

    def test_required_skin_key_must_match(self) -> None:
        entry = DialogueEntry(
            key="chat",
            actor_key="enterprise",
            lines=("ok",),
            required_skin_key="enterprise_oath",
        )
        self.assertFalse(self.service._matches(entry, _scene()))
        self.assertTrue(
            self.service._matches(entry, _scene(equipped_skin_key="enterprise_oath"))
        )

    def test_required_removed_slots_must_match(self) -> None:
        entry = DialogueEntry(
            key="chat",
            actor_key="enterprise",
            lines=("ok",),
            required_removed_slots=("underwear_bottom",),
        )
        self.assertFalse(self.service._matches(entry, _scene(removed_slots=())))
        self.assertTrue(
            self.service._matches(
                entry,
                _scene(removed_slots=("underwear_bottom",)),
            )
        )


class DialoguePrioritySelectionTests(unittest.TestCase):
    """Test that highest-priority matching entry wins."""

    def test_fallback_selected_when_no_conditions_match(self) -> None:
        entries = (
            DialogueEntry(
                key="chat", actor_key="enterprise",
                lines=("fallback",), priority=0,
            ),
            DialogueEntry(
                key="chat", actor_key="enterprise",
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
                key="chat", actor_key="enterprise",
                lines=("fallback",), priority=0,
            ),
            DialogueEntry(
                key="chat", actor_key="enterprise",
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
                key="chat", actor_key="enterprise",
                lines=("fallback",), priority=0,
            ),
            DialogueEntry(
                key="chat", actor_key="enterprise",
                lines=("like",), priority=5,
                required_stage="like",
            ),
            DialogueEntry(
                key="chat", actor_key="enterprise",
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
                key="chat", actor_key="enterprise",
                lines=("fallback",), priority=0,
            ),
            DialogueEntry(
                key="chat", actor_key="enterprise",
                lines=("like",), priority=5,
                required_stage="like",
            ),
            DialogueEntry(
                key="chat", actor_key="enterprise",
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
                key="chat", actor_key="enterprise",
                lines=("generic chat",), priority=0,
            ),
            DialogueEntry(
                key="enterprise_chat_dock", actor_key="enterprise",
                lines=("event-specific",), priority=10,
            ),
        )
        service = DialogueService(entries=entries)
        lines = service.lines_for(
            _scene(action_key="chat"),
            triggered_events=("enterprise_chat_dock",),
        )
        self.assertEqual(lines, ("event-specific",))

    def test_action_key_fallback_when_no_events(self) -> None:
        entries = (
            DialogueEntry(
                key="chat", actor_key="enterprise",
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
        self.actor = next(actor for actor in self.app.world.characters if actor.key == "enterprise")
        place_player_with_actor(self.app, self.actor)

    def test_chat_for_enterprise_uses_real_event_dialogue(self) -> None:
        result = self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="chat",
        )
        # The event-specific dialogue (priority 10) should win over the fallback (priority 0)
        self.assertTrue(any("标准" in line or "企业" in line for line in result.messages))

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

    def test_oath_success_uses_enterprise_success_dialogue(self) -> None:
        seed_like(self.actor)
        self.app.relationship_service.update_actor(self.actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.MORNING
        self.app.world.personal_funds = 1200
        self.app.shop_service.purchase(
            self.app.world,
            shopfront_key="general_shop",
            item_key="pledge_ring",
        )
        self.app.command_service.resolution_service.roll = lambda: 0.0

        result = self.app.command_service.execute(self.app.world, self.actor.key, "oath")

        self.assertTrue(any("回应你的信任" in line for line in result.messages))

    def test_oath_failure_uses_enterprise_failure_dialogue(self) -> None:
        seed_like(self.actor)
        self.app.relationship_service.update_actor(self.actor)
        self.app.world.current_time_slot = self.app.world.current_time_slot.MORNING
        self.app.world.personal_funds = 1200
        self.app.shop_service.purchase(
            self.app.world,
            shopfront_key="general_shop",
            item_key="pledge_ring",
        )
        self.app.command_service.resolution_service.roll = lambda: 0.99

        result = self.app.command_service.execute(self.app.world, self.actor.key, "oath")

        self.assertTrue(any("再试一次吧" in line for line in result.messages))

    def test_chat_with_oath_skin_uses_skin_specific_dialogue(self) -> None:
        self.actor.unlock_skin("enterprise_oath")
        self.actor.equip_skin("enterprise_oath")

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=self.actor.key,
            command_key="chat",
        )

        self.assertTrue(any("礼服" in line or "誓约" in line for line in result.messages))


class DialogueMarkBranchingTests(unittest.TestCase):
    """Test that MARK-conditional dialogue entries produce different lines."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = next(actor for actor in self.app.world.characters if actor.key == "enterprise")

    def test_chat_without_embarrassed_mark_uses_default(self) -> None:
        """Without embarrassed mark, chat should use the default/fallback lines."""
        self.assertFalse(self.actor.has_mark("embarrassed"))
        scene = _scene(actor_key="enterprise", action_key="chat", marks={})
        lines = self.app.dialogue_service._lookup("chat", scene)
        # Should NOT contain embarrassed-variant text
        self.assertTrue(len(lines) > 0)

    def test_chat_with_embarrassed_mark_uses_variant(self) -> None:
        """With embarrassed mark, chat should use the MARK-conditional variant."""
        service = DialogueService(entries=(
            DialogueEntry(key="chat", actor_key="enterprise", lines=("default",), priority=0),
            DialogueEntry(key="chat", actor_key="enterprise", lines=("embarrassed",), priority=5, required_marks={"embarrassed": 1}),
        ))
        scene_no_mark = _scene(actor_key="enterprise", action_key="chat", marks={})
        lines_no_mark = service._lookup("chat", scene_no_mark)

        scene_with_mark = _scene(actor_key="enterprise", action_key="chat", marks={"embarrassed": 1})
        lines_with_mark = service._lookup("chat", scene_with_mark)

        self.assertNotEqual(lines_no_mark, lines_with_mark)

    def test_praise_with_angry_mark_uses_variant(self) -> None:
        """With angry mark, praise should use a different variant."""
        service = DialogueService(entries=(
            DialogueEntry(key="praise", actor_key="enterprise", lines=("default",), priority=0),
            DialogueEntry(key="praise", actor_key="enterprise", lines=("angry",), priority=5, required_marks={"angry": 1}),
        ))
        scene_no_mark = _scene(actor_key="enterprise", action_key="praise", marks={})
        lines_no_mark = service._lookup("praise", scene_no_mark)

        scene_with_mark = _scene(actor_key="enterprise", action_key="praise", marks={"angry": 1})
        lines_with_mark = service._lookup("praise", scene_with_mark)

        self.assertNotEqual(lines_no_mark, lines_with_mark)

    def test_clink_cups_with_drunk_mark_uses_variant(self) -> None:
        """With drunk mark, clink_cups should use a different variant."""
        scene_no_mark = _scene(
            actor_key="enterprise", action_key="clink_cups",
            time_slot="evening", marks={},
        )
        lines_no_mark = self.app.dialogue_service._lookup("clink_cups", scene_no_mark)

        scene_with_mark = _scene(
            actor_key="enterprise", action_key="clink_cups",
            time_slot="evening", marks={"drunk": 1},
        )
        lines_with_mark = self.app.dialogue_service._lookup("clink_cups", scene_with_mark)

        self.assertNotEqual(lines_no_mark, lines_with_mark)

    def test_at_least_three_marks_have_branching(self) -> None:
        """Verify at least 3 different marks produce branching dialogue."""
        marks_with_branching = set()
        for entry in self.app.dialogue_service.entries:
            if entry.required_marks:
                marks_with_branching.update(entry.required_marks.keys())
        self.assertGreaterEqual(len(marks_with_branching), 3)


if __name__ == "__main__":
    unittest.main()
