"""Load MARK definitions from TOML.

MARKs are stage-like status tags applied to characters by commands or
events.  They gate downstream actions, events, and dialogue variants
similar to how eraTW uses its MARK array.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MarkDefinition:
    """Static metadata for one MARK type."""

    key: str
    display_name: str
    group: str
    max_level: int = 1


def load_mark_definitions(path: Path) -> tuple[MarkDefinition, ...]:
    """Load mark definitions from TOML."""

    if not path.exists():
        return ()

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        MarkDefinition(
            key=str(item.get("key", item["index"])),
            display_name=item["display_name"],
            group=item.get("group", "general"),
            max_level=int(item.get("max_level", 1)),
        )
        for item in raw_data.get("marks", [])
    )
