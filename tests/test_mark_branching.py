"""MARK branching tests: state marks affect command output and dialogue selection."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.dialogue import DialogueEntry
from eral.domain.scene import SceneContext
from eral.systems.dialogue import DialogueService


def _scene(
    actor_key: str = "starter_secretary",
    action_key: str = "tease",
    time_slot: str = "evening",
    location_key: str = "cafeteria",
    location_tags: tuple[str, ...] = ("social",),
    relationship_stage: str = "friendly",
    relationship_rank: int = 1,
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


class DialogueMarkConditionTests(unittest.TestCase):
    """Test DialogueService._matches with required_marks."""

    def setUp(self) -> None:
        self.service = DialogueService(entries=())

    def test_required_marks_missing_does_not_match(self) -> None:
        entry = DialogueEntry(
            key="tease", actor_key="starter_secretary", lines=(),
            required_marks={"embarrassed": 1},
        )
        self.assertFalse(self.service._matches(entry, _scene(marks={})))

    def test_required_marks_present_matches(self) -> None:
        entry = DialogueEntry(
            key="tease", actor_key="starter_secretary", lines=(),
            required_marks={"embarrassed": 1},
        )
        self.assertTrue(self.service._matches(entry, _scene(marks={"embarrassed": 1})))

    def test_required_marks_insufficient_level_does_not_match(self) -> None:
        entry = DialogueEntry(
            key="tease", actor_key="starter_secretary", lines=(),
            required_marks={"drunk": 2},
        )
        self.assertFalse(self.service._matches(entry, _scene(marks={"drunk": 1})))
        self.assertTrue(self.service._matches(entry, _scene(marks={"drunk": 2})))

    def test_multiple_required_marks_all_must_pass(self) -> None:
        entry = DialogueEntry(
            key="tease", actor_key="starter_secretary", lines=(),
            required_marks={"embarrassed": 1, "drunk": 1},
        )
        self.assertFalse(self.service._matches(entry, _scene(marks={"embarrassed": 1})))
        self.assertFalse(self.service._matches(entry, _scene(marks={"drunk": 1})))
        self.assertTrue(self.service._matches(entry, _scene(marks={"embarrassed": 1, "drunk": 1})))


class DialogueMarkFallbackTests(unittest.TestCase):
    """Test that _any entries serve as fallback when no actor-specific match."""

    def test_any_actor_entry_used_as_fallback(self) -> None:
        entries = (
            DialogueEntry(
                key="scold", actor_key="_any",
                lines=("她看起来很生气。",), priority=1,
                required_marks={"angry": 1},
            ),
        )
        service = DialogueService(entries=entries)
        lines = service._lookup("scold", _scene(marks={"angry": 1}))
        self.assertEqual(lines, ("她看起来很生气。",))

    def test_actor_specific_entry_beats_any_actor(self) -> None:
        entries = (
            DialogueEntry(
                key="scold", actor_key="_any",
                lines=("generic angry",), priority=1,
                required_marks={"angry": 1},
            ),
            DialogueEntry(
                key="scold", actor_key="starter_secretary",
                lines=("secretary angry",), priority=1,
                required_marks={"angry": 1},
            ),
        )
        service = DialogueService(entries=entries)
        lines = service._lookup("scold", _scene(marks={"angry": 1}))
        self.assertEqual(lines, ("secretary angry",))

    def test_any_actor_only_used_when_no_actor_match(self) -> None:
        entries = (
            DialogueEntry(
                key="scold", actor_key="_any",
                lines=("generic angry",), priority=1,
                required_marks={"angry": 1},
            ),
            DialogueEntry(
                key="scold", actor_key="starter_secretary",
                lines=("secretary default",), priority=0,
            ),
        )
        service = DialogueService(entries=entries)
        lines = service._lookup("scold", _scene(marks={"angry": 1}))
        # actor-specific entry without marks matches, beats _any fallback
        self.assertEqual(lines, ("secretary default",))


class CommandMarkApplicationTests(unittest.TestCase):
    """Integration tests: commands apply state marks correctly."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = next(
            actor for actor in self.app.world.characters
            if actor.key == "starter_secretary"
        )

    def _advance_to_friendly(self) -> None:
        """Push affection high enough for friendly stage + min_affection=1."""
        self.actor.stats.compat.cflag.set(2, 3)  # affection
        self.actor.sync_derived_fields()
        from eral.systems.relationships import RelationshipService
        from eral.content.relationships import load_relationship_stages
        stages = load_relationship_stages(
            Path(__file__).resolve().parents[1] / "data" / "base" / "relationship_stages.toml"
        )
        rs = RelationshipService(stages=stages)
        rs.update_actor(self.actor)

    def _advance_to_love(self) -> None:
        """Push affection + trust high enough for love stage."""
        self.actor.stats.compat.cflag.set(2, 10)  # affection
        self.actor.stats.compat.cflag.set(4, 6)   # trust
        self.actor.sync_derived_fields()
        from eral.systems.relationships import RelationshipService
        from eral.content.relationships import load_relationship_stages
        stages = load_relationship_stages(
            Path(__file__).resolve().parents[1] / "data" / "base" / "relationship_stages.toml"
        )
        rs = RelationshipService(stages=stages)
        rs.update_actor(self.actor)

    def test_tease_applies_embarrassed_mark(self) -> None:
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        self.app.world.active_location.key = "cafeteria"
        self.actor.location_key = "cafeteria"
        self._advance_to_friendly()
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="tease",
        )
        self.assertTrue(self.actor.has_mark("embarrassed", 1))
        self.assertTrue(self.actor.has_mark("teased", 1))

    def test_scold_applies_angry_mark(self) -> None:
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="scold",
        )
        self.assertTrue(self.actor.has_mark("angry", 1))

    def test_serve_tea_applies_drunk_mark(self) -> None:
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="serve_tea",
        )
        self.assertTrue(self.actor.has_mark("drunk", 1))

    def test_date_tease_applies_embarrassed_mark(self) -> None:
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        self._advance_to_love()
        self.app.companion_service.start_follow(self.app.world, self.actor)
        self.app.date_service.start_date(self.app.world, self.actor)
        self.app.world.active_location.key = "cafeteria"
        self.actor.location_key = "cafeteria"
        self.app.command_service.execute(
            self.app.world, actor_key=self.actor.key, command_key="date_tease",
        )
        self.assertTrue(self.actor.has_mark("embarrassed", 1))
        self.assertTrue(self.actor.has_mark("teased", 1))

    def test_marks_respect_max_level(self) -> None:
        # teased max_level=3, embarrassed max_level=2
        self.app.world.current_time_slot = self.app.world.current_time_slot.EVENING
        self.app.world.active_location.key = "cafeteria"
        self.actor.location_key = "cafeteria"
        self._advance_to_friendly()
        # Apply tease 3 times
        for _ in range(3):
            self.app.command_service.execute(
                self.app.world, actor_key=self.actor.key, command_key="tease",
            )
        self.assertEqual(self.actor.marks.get("teased"), 3)
        self.assertEqual(self.actor.marks.get("embarrassed"), 2)  # clamped at max_level=2


if __name__ == "__main__":
    unittest.main()
