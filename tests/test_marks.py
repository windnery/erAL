"""MARK system tests — definitions, character state, command integration."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.marks import MarkDefinition, load_mark_definitions
from eral.domain.world import CharacterState
from eral.domain.stats import ActorNumericState
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress


class MarkDefinitionTests(unittest.TestCase):
    def test_load_mark_definitions_from_toml(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        marks = load_mark_definitions(repo_root / "data" / "base" / "axes" / "marks.toml")
        keys = [m.key for m in marks]
        self.assertIn("0", keys)
        self.assertIn("1", keys)
        self.assertIn("3", keys)

    def test_pain_mark_has_max_level_3(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        marks = load_mark_definitions(repo_root / "data" / "base" / "axes" / "marks.toml")
        pain = next(m for m in marks if m.key == "0")
        self.assertEqual(pain.max_level, 3)

    def test_pleasure_mark_has_max_level_3(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        marks = load_mark_definitions(repo_root / "data" / "base" / "axes" / "marks.toml")
        pleasure = next(m for m in marks if m.key == "1")
        self.assertEqual(pleasure.max_level, 3)


class CharacterMarkStateTests(unittest.TestCase):
    """Test mark methods on CharacterState in isolation."""

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        cls.app = create_application(repo_root)

    def _make_actor(self) -> CharacterState:
        stats = ActorNumericState.zeroed(self.app.stat_axes)
        return CharacterState(
            key="test_actor",
            display_name="测试角色",
            location_key="command_office",
            stats=stats,
        )

    def test_has_mark_returns_false_when_absent(self) -> None:
        actor = self._make_actor()
        self.assertFalse(actor.has_mark("0"))

    def test_set_mark_and_has_mark(self) -> None:
        actor = self._make_actor()
        actor.set_mark("0", 1, max_level=3)
        self.assertTrue(actor.has_mark("0"))
        self.assertEqual(actor.marks["0"], 1)

    def test_set_mark_clamps_to_max_level(self) -> None:
        actor = self._make_actor()
        actor.set_mark("1", 5, max_level=3)
        self.assertEqual(actor.marks["1"], 3)

    def test_add_mark_increments(self) -> None:
        actor = self._make_actor()
        actor.add_mark("0", 1, max_level=3)
        self.assertEqual(actor.marks["0"], 1)
        actor.add_mark("0", 1, max_level=3)
        self.assertEqual(actor.marks["0"], 2)
        actor.add_mark("0", 1, max_level=3)
        self.assertEqual(actor.marks["0"], 3)

    def test_add_mark_clamps_at_max(self) -> None:
        actor = self._make_actor()
        actor.add_mark("0", 1, max_level=3)
        actor.add_mark("0", 1, max_level=3)
        actor.add_mark("0", 1, max_level=3)
        result = actor.add_mark("0", 1, max_level=3)
        self.assertEqual(result, 3)

    def test_add_mark_does_not_go_below_zero(self) -> None:
        actor = self._make_actor()
        result = actor.add_mark("0", -1, max_level=3)
        self.assertEqual(result, 0)

    def test_has_mark_with_min_level(self) -> None:
        actor = self._make_actor()
        actor.add_mark("0", 2, max_level=3)
        self.assertTrue(actor.has_mark("0", min_level=1))
        self.assertTrue(actor.has_mark("0", min_level=2))
        self.assertFalse(actor.has_mark("0", min_level=3))


class MarkCommandIntegrationTests(unittest.TestCase):
    """Test that commands apply marks and check required_marks."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)
        place_player_with_actor(self.app, self.actor)

    def test_command_with_required_marks_unavailable_without_mark(self) -> None:
        """If a future command requires a mark the actor lacks, it should not be available."""
        available = self.app.command_service.available_commands_for_actor(
            self.app.world, self.actor.key,
        )
        from eral.content.commands import CommandDefinition
        cmd = CommandDefinition(
            index=9990,
            display_name="测试",
            category="train",
            location_tags=("private",),
            time_slots=("night",),
            min_affection=None,
            min_trust=None,
            min_obedience=None,
            required_stage=None,
            operation=None,
            requires_following=None,
            requires_date=None,
            required_marks={"1": 1},
            apply_marks={},
            remove_marks=(),
            success_tiers=(0.1, 1.0, 2.0),
        )
        location = self.app.port_map.location_by_key(self.app.world.active_location.key)
        self.assertFalse(
            self.app.command_service._is_available_for_actor(
                self.app.world, self.actor, cmd, location.tags,
            ),
        )

    def test_command_with_required_marks_available_with_mark(self) -> None:
        from eral.content.commands import CommandDefinition
        cmd = CommandDefinition(
            index=9991,
            display_name="测试",
            category="daily",
            location_tags=(),
            time_slots=(),
            min_affection=None,
            min_trust=None,
            min_obedience=None,
            required_stage=None,
            operation=None,
            requires_following=None,
            requires_date=None,
            required_marks={"1": 1},
            apply_marks={},
            remove_marks=(),
            success_tiers=(0.1, 1.0, 2.0),
        )
        self.actor.set_mark("1", 1, max_level=3)
        location = self.app.port_map.location_by_key(self.app.world.active_location.key)
        self.assertTrue(
            self.app.command_service._is_available_for_actor(
                self.app.world, self.actor, cmd, location.tags,
            ),
        )


if __name__ == "__main__":
    unittest.main()
