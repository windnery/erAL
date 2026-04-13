"""Tests for compat semantic registry and access helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.stat_axes import AxisFamily
from eral.content.tw_axis_registry import load_tw_axis_registry
from eral.domain.compat_semantics import (
    ABLKey,
    CFLAGKey,
    TALENTKey,
    actor_abl,
    actor_cflag,
    actor_talent,
    build_default_compat_semantics,
)
from tests.support.real_actors import actor_by_key, reset_progress


class CompatSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.tw_registry = load_tw_axis_registry(repo_root / "data" / "generated" / "tw_axis_registry.json")
        self.semantics = build_default_compat_semantics(self.tw_registry)
        self.app = create_application(repo_root)

    def _actor(self):
        actor = actor_by_key(self.app, "enterprise")
        reset_progress(actor)
        return actor

    def test_resolves_registered_cflag_entry(self) -> None:
        entry = self.semantics.entry(AxisFamily.CFLAG, CFLAGKey.AFFECTION)

        self.assertEqual(entry.era_index, 2)
        self.assertEqual(entry.label, self.tw_registry.get_by_index(AxisFamily.CFLAG, 2).label)

    def test_resolves_registered_abl_and_talent_entries(self) -> None:
        abl_entry = self.semantics.entry(AxisFamily.ABL, ABLKey.TALK_SKILL)
        talent_entry = self.semantics.entry(AxisFamily.TALENT, TALENTKey.CHARM)

        self.assertEqual(abl_entry.era_index, 41)
        self.assertEqual(talent_entry.era_index, 92)
        self.assertEqual(abl_entry.label, self.tw_registry.get_by_index(AxisFamily.ABL, 41).label)
        self.assertEqual(talent_entry.label, self.tw_registry.get_by_index(AxisFamily.TALENT, 92).label)

    def test_actor_accessors_read_write_by_semantic_key(self) -> None:
        actor = self._actor()

        actor_cflag.set(actor, CFLAGKey.AFFECTION, 5)
        actor_cflag.add(actor, CFLAGKey.TRUST, 2)
        actor_abl.set(actor, ABLKey.TALK_SKILL, 3)
        actor_talent.set(actor, TALENTKey.CHARM, 1)

        self.assertEqual(actor_cflag.get(actor, CFLAGKey.AFFECTION), 5)
        self.assertEqual(actor_cflag.get(actor, CFLAGKey.TRUST), 2)
        self.assertEqual(actor_abl.get(actor, ABLKey.TALK_SKILL), 3)
        self.assertEqual(actor_talent.get(actor, TALENTKey.CHARM), 1)

    def test_rejects_unknown_key(self) -> None:
        with self.assertRaises(KeyError):
            self.semantics.entry(AxisFamily.CFLAG, "not_registered")


if __name__ == "__main__":
    unittest.main()
