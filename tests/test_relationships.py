"""Relationship stage tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.compat_semantics import CFLAGKey, actor_cflag
from tests.support.real_actors import actor_by_key, place_player_with_actor
from tests.support.stages import reset_progress
from eral.content.relationships import RelationshipStageDefinition, load_relationship_stages


class RelationshipTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        return actor_by_key(self.app, "enterprise")

    def test_default_stage_is_stranger(self) -> None:
        actor = self._actor()
        reset_progress(actor)
        self.app.relationship_service.update_actor(actor)
        self.assertIsNotNone(actor.relationship_stage)
        self.assertEqual(actor.relationship_stage.key, "stranger")

    def test_chat_increments_affection(self) -> None:
        actor = self._actor()
        reset_progress(actor)
        place_player_with_actor(self.app, actor)
        self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="chat",
        )
        self.assertEqual(actor.affection, 3)
        # enterprise has talent 92 (魅力) which boosts affection SOURCE by 1.1x
        self.assertEqual(actor.stats.palam.get("favor"), 55)

    def test_sync_derived_fields_matches_cflag(self) -> None:
        actor = self._actor()
        actor_cflag.set(actor, CFLAGKey.AFFECTION, 42)
        actor_cflag.set(actor, CFLAGKey.TRUST, 17)
        actor.sync_derived_fields()

        self.assertEqual(actor.affection, 42)
        self.assertEqual(actor.trust, 17)

    def test_relationship_stages_ordering_validated(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "base" / "relationship_stages.toml"
        stages = load_relationship_stages(path)

        for i in range(1, len(stages)):
            prev, curr = stages[i - 1], stages[i]
            self.assertLessEqual(
                (prev.min_affection, prev.min_trust),
                (curr.min_affection, curr.min_trust),
                f"Stage '{curr.key}' is not in ascending order after '{prev.key}'",
            )


if __name__ == "__main__":
    unittest.main()
