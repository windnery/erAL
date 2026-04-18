"""Minimal training content placeholders for future expansion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrainingProgressionDefinition:
    """Minimal long-term training progression definition."""

    key: str
    display_name: str

