"""Relationship stage state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RelationshipStage:
    """Resolved relationship stage on a character."""

    key: str
    display_name: str
    rank: int
