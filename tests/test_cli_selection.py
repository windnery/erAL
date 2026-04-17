"""Tests for paginated location roster and auto-selection helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.stat_axes import load_stat_axis_catalog
from eral.content.tw_axis_registry import load_tw_axis_registry
from eral.domain.stats import ActorNumericState
from eral.domain.world import CharacterState
from eral.ui.cli import (
    _auto_select_actor_key,
    _build_menu,
    _page_index_for_actor,
    _paginate_present_characters,
)


class CliSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.repo_root = repo_root

    def test_auto_select_returns_none_when_location_empty(self) -> None:
        selected = _auto_select_actor_key(self.app, "command_office")
        self.assertIsNone(selected)

    def test_auto_select_returns_highest_priority_actor(self) -> None:
        selected = _auto_select_actor_key(self.app, "dock")
        self.assertEqual(selected, "enterprise")

    def test_paginate_present_characters_limits_to_ten_per_page(self) -> None:
        stat_axes = load_stat_axis_catalog(self.repo_root / "data" / "base" / "stat_axes.toml")
        tw_axes = load_tw_axis_registry(self.repo_root / "data" / "generated" / "tw_axis_registry.json")
        for idx in range(15):
            stats = ActorNumericState.zeroed(stat_axes, tw_axes)
            actor = CharacterState(
                key=f"extra_{idx}",
                display_name=f"额外{idx}",
                location_key="dock",
                stats=stats,
            )
            self.app.world.characters.append(actor)
        page = _paginate_present_characters(self.app, "dock", page_index=0)
        self.assertLessEqual(len(page), 10)

    def test_page_index_for_actor_returns_page_containing_selected_actor(self) -> None:
        stat_axes = load_stat_axis_catalog(self.repo_root / "data" / "base" / "stat_axes.toml")
        tw_axes = load_tw_axis_registry(self.repo_root / "data" / "generated" / "tw_axis_registry.json")
        for idx in range(15):
            stats = ActorNumericState.zeroed(stat_axes, tw_axes)
            actor = CharacterState(
                key=f"extra_{idx:02d}",
                display_name=f"额外{idx}",
                location_key="dock",
                stats=stats,
            )
            self.app.world.characters.append(actor)

        second_page = _paginate_present_characters(self.app, "dock", page_index=1)

        self.assertTrue(second_page)
        self.assertEqual(
            _page_index_for_actor(self.app, "dock", second_page[0].key),
            1,
        )

    def test_build_menu_only_exposes_commands_for_selected_actor(self) -> None:
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "主码头"
        for actor in self.app.world.characters:
            actor.location_key = "dock"

        menu = _build_menu(
            self.app,
            self.app.world,
            selected_actor_key="laffey",
            roster_page_index=0,
        )

        command_labels = [
            label
            for label, action_type, _ in menu["daily"] + menu["follow"] + menu["date"] + menu["intimacy"] + menu["recovery"] + menu["work"]
            if action_type == "command"
        ]

        self.assertTrue(command_labels)
        self.assertTrue(all(label.endswith("→拉菲") for label in command_labels))

    def test_build_menu_adds_select_actions_for_other_present_characters(self) -> None:
        self.app.world.active_location.key = "dock"
        self.app.world.active_location.display_name = "主码头"
        for actor in self.app.world.characters:
            actor.location_key = "dock"

        menu = _build_menu(
            self.app,
            self.app.world,
            selected_actor_key="enterprise",
            roster_page_index=0,
        )

        select_actions = [
            (label, param)
            for label, action_type, param in menu["system"]
            if action_type == "select_actor"
        ]

        self.assertTrue(any(param == "laffey" for _, param in select_actions))
        self.assertTrue(any(param == "javelin" for _, param in select_actions))


if __name__ == "__main__":
    unittest.main()
