"""Tests for the status panel supporting data layers (milestones + panel helpers)."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.food import FoodPreferences, load_food_preferences
from eral.ui import body_info, personal_info
from tests.support.real_actors import actor_by_key
from tests.support.stages import reset_progress


class FoodPreferencesTests(unittest.TestCase):
    def test_load_empty_returns_defaults(self) -> None:
        prefs = load_food_preferences(None)
        self.assertEqual(prefs.liked_tags, ())
        self.assertEqual(prefs.disliked_tags, ())

    def test_load_tags_are_strings(self) -> None:
        prefs = load_food_preferences({"liked_tags": ["sweet"], "disliked_tags": ["bitter"]})
        self.assertEqual(prefs.liked_tags, ("sweet",))
        self.assertEqual(prefs.disliked_tags, ("bitter",))

    def test_multiplier_reflects_liked_disliked(self) -> None:
        prefs = FoodPreferences(liked_tags=("sweet",), disliked_tags=("bitter",))
        self.assertEqual(prefs.preference_multiplier(("sweet",)), 2.0)
        self.assertEqual(prefs.preference_multiplier(("bitter",)), 0.3)
        self.assertEqual(prefs.preference_multiplier(("savory",)), 1.0)

    def test_character_food_prefs_load_from_toml(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        enterprise = next(d for d in app.roster if d.key == "enterprise")
        self.assertIn("savory", enterprise.food_preferences.liked_tags)
        self.assertIn("sweet", enterprise.food_preferences.disliked_tags)


class MilestoneRecordingTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)

    def test_first_date_records_milestone(self) -> None:
        self.world.current_day = 5
        # invite_date is the command key that maps to start_date operation
        cmd = self.app.command_service.commands.get("invite_date")
        if cmd is None:
            self.skipTest("invite_date command not found")
        self.app.command_service._record_milestones(self.world, self.actor, cmd)
        self.assertEqual(
            self.actor.get_condition("milestone:first_date_day"), 5
        )
        self.assertGreater(
            self.actor.memories.get("milestone:first_date", 0), 0
        )

    def test_milestone_records_only_first_occurrence(self) -> None:
        self.actor.set_condition("milestone:first_kiss_day", 3)
        self.actor.record_memory("milestone:first_kiss")
        self.world.current_day = 10
        # Simulate a later command by calling the internal helper directly.
        cmd = self.app.command_service.commands["kiss"]
        self.app.command_service._record_milestones(self.world, self.actor, cmd)
        self.assertEqual(
            self.actor.get_condition("milestone:first_kiss_day"), 3
        )


class PersonalInfoHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def test_personality_from_tags(self) -> None:
        self.assertEqual(
            personal_info.personality_from_tags(("enterprise", "carrier", "eagle_union", "serious")),
            "serious",
        )

    def test_activity_hours_spans_non_home_slots(self) -> None:
        enterprise = next(d for d in self.app.roster if d.key == "enterprise")
        hours = personal_info.activity_hours(enterprise)
        # Enterprise's schedule has morning through night, dormitory at late_night
        self.assertIn("时", hours)

    def test_frequent_areas_lists_area_names(self) -> None:
        enterprise = next(d for d in self.app.roster if d.key == "enterprise")
        areas = personal_info.frequent_areas(enterprise, self.app.port_map)
        self.assertNotEqual(areas, "—")


class BodyInfoHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")
        reset_progress(self.actor)

    def test_outer_parts_returns_four(self) -> None:
        parts = body_info.outer_parts(self.actor)
        labels = tuple(p.label for p in parts)
        self.assertEqual(labels, ("身", "指", "胸", "阴蒂"))

    def test_inner_parts_returns_four_with_history(self) -> None:
        parts = body_info.inner_parts(self.actor)
        labels = tuple(p.label for p in parts)
        self.assertEqual(labels, ("口", "肛", "膣", "子宫"))
        # Mouth/Anal/Vagina should carry history lines even at zero
        for part in parts[:3]:
            self.assertTrue(part.history)

    def test_mouth_history_updates_after_first_kiss(self) -> None:
        self.actor.memories["milestone:first_kiss"] = 1
        self.actor.set_condition("milestone:first_kiss_day", 7)
        parts = body_info.inner_parts(self.actor)
        mouth = next(p for p in parts if p.label == "口")
        self.assertIn("第 7 日", mouth.history)


class StatusPanelRenderSmokeTest(unittest.TestCase):
    """Ensure each tab renders without exception for a real actor."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.actor = actor_by_key(self.app, "enterprise")

    def test_tabs_render_without_exceptions(self) -> None:
        import io
        from contextlib import redirect_stdout
        from eral.ui import cli

        buf = io.StringIO()
        with redirect_stdout(buf):
            cli._render_tab_clothing_ability(self.actor, self.app)
            cli._render_tab_exp_jewel(self.actor, self.app)
            cli._render_tab_personal(self.actor, self.app)
            cli._render_tab_likes(self.actor, self.app)
            cli._render_tab_body(self.actor, self.app)
            cli._render_tab_fallen(self.actor, self.app.relationship_stages, self.app)

        output = buf.getvalue()
        # Sanity: all 6 panels produced output with their section headers
        self.assertIn("服装", output)
        self.assertIn("经验", output)
        self.assertIn("个人情报", output)
        self.assertIn("个人好恶", output)
        self.assertIn("身体情报", output)
        self.assertIn("陷落状态", output)
