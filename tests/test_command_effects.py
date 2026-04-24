"""Tests for declarative command effect application."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.command_effects import CommandEffect, SourcePayload
from eral.systems.command_effects import apply_command_effect
from tests.support.real_actors import actor_by_key


class CommandEffectsTests(unittest.TestCase):
    def test_apply_command_effect_writes_player_source_to_player_stats(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        app = create_application(repo_root)
        actor = actor_by_key(app, "enterprise")
        assert app.world.player_stats is not None

        effect = CommandEffect(
            command_index=999,
            source=SourcePayload(target={0: 40}, player={41: 25}),
        )

        apply_command_effect(actor, effect, app.world.player_stats)

        self.assertEqual(actor.stats.source.get("0"), 40)
        self.assertEqual(app.world.player_stats.source.get("41"), 25)


if __name__ == "__main__":
    unittest.main()
