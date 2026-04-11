"""Load relationship stage thresholds."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RelationshipStageDefinition:
    """Static threshold for one relationship stage."""

    key: str
    display_name: str
    min_affection: int
    min_trust: int


def load_relationship_stages(path: Path) -> tuple[RelationshipStageDefinition, ...]:
    """Load relationship stage thresholds from TOML.

    Stages must be ordered by ascending min_affection, then min_trust.
    """

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    stages = tuple(
        RelationshipStageDefinition(
            key=item["key"],
            display_name=item["display_name"],
            min_affection=int(item["min_affection"]),
            min_trust=int(item["min_trust"]),
        )
        for item in raw_data.get("stages", [])
    )

    for i in range(1, len(stages)):
        prev, curr = stages[i - 1], stages[i]
        if (curr.min_affection, curr.min_trust) < (prev.min_affection, prev.min_trust):
            raise ValueError(
                f"relationship_stages must be in ascending order: "
                f"'{curr.key}' ({curr.min_affection},{curr.min_trust}) "
                f"comes after '{prev.key}' ({prev.min_affection},{prev.min_trust})"
            )

    return stages

