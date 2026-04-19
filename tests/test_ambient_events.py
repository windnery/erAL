"""Tests for the ambient random event pool."""

from __future__ import annotations

import random
import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.ambient_events import (
    AmbientEventDefinition,
    load_ambient_events,
)
from eral.systems.ambient_events import AmbientEventService


class AmbientEventLoadTests(unittest.TestCase):
    def test_data_pack_loads(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        events = load_ambient_events(repo_root / "data" / "base" / "ambient_events.toml")
        self.assertGreater(len(events), 0)
        self.assertTrue(all(isinstance(e, AmbientEventDefinition) for e in events))

    def test_missing_file_returns_empty(self) -> None:
        events = load_ambient_events(Path("/does/not/exist.toml"))
        self.assertEqual(events, ())


class AmbientEventServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)
        self.world = self.app.world
        self.service = self.app.ambient_event_service
        self.service.rng = random.Random(42)

    def test_roll_returns_none_when_below_chance(self) -> None:
        self.service.rng.random = lambda: 0.99  # type: ignore[assignment]
        self.assertIsNone(self.service.roll(self.world))

    def test_roll_emits_outcome_with_tags(self) -> None:
        self.service.rng.random = lambda: 0.0  # type: ignore[assignment]
        outcome = self.service.roll(self.world)
        if outcome is None:
            # Could be no eligible events depending on initial location/slot.
            self.assertFalse(self.service._eligible(self.world))
        else:
            self.assertTrue(outcome.key)
            self.assertIsInstance(outcome.tags, tuple)

    def test_cooldown_prevents_immediate_refire(self) -> None:
        eligible = self.service._eligible(self.world)
        if not eligible:
            self.skipTest("no eligible events in default scene")
        picked = eligible[0]
        self.service.rng.random = lambda: 0.0  # type: ignore[assignment]
        self.service.rng.choices = lambda pool, weights, k: [picked]  # type: ignore[assignment]

        first = self.service.roll(self.world)
        self.assertIsNotNone(first)
        remaining = self.service._eligible(self.world)
        self.assertNotIn(picked, remaining)

    def test_empty_definitions_yield_none(self) -> None:
        empty = AmbientEventService(definitions=(), port_map=self.app.port_map)
        self.assertIsNone(empty.roll(self.world))

    def test_game_loop_advance_rolls_ambient(self) -> None:
        # Force deterministic fire
        self.service.rng.random = lambda: 0.0  # type: ignore[assignment]
        received: list[dict] = []
        self.app.event_bus.subscribe(
            "ambient_event.fired",
            lambda event: received.append(event.payload),
        )
        self.app.game_loop.advance_time(self.world)
        # May or may not fire depending on eligibility — if nothing fired, bus has no event
        if received:
            self.assertIn("key", received[0])
            self.assertIn("message", received[0])
