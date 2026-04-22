"""Load predefined character-to-character affinity relationships."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CharacterRelation:
    """A directional affinity record between two characters (from → to)."""

    from_key: str
    to_key: str
    affinity: int
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CharacterRelationIndex:
    """Fast lookup over the loaded relations."""

    relations: tuple[CharacterRelation, ...]
    _by_pair: dict[tuple[str, str], CharacterRelation] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        by_pair = {(r.from_key, r.to_key): r for r in self.relations}
        object.__setattr__(self, "_by_pair", by_pair)

    def affinity(self, from_key: str, to_key: str) -> int:
        """Return the affinity from `from_key` to `to_key`; 0 if not declared."""
        record = self._by_pair.get((from_key, to_key))
        return record.affinity if record is not None else 0

    def tags(self, from_key: str, to_key: str) -> tuple[str, ...]:
        """Return the tags declared for the pair; empty tuple if not declared."""
        record = self._by_pair.get((from_key, to_key))
        return record.tags if record is not None else ()

    def relations_from(self, from_key: str) -> tuple[CharacterRelation, ...]:
        """All outgoing relations from the given character."""
        return tuple(r for r in self.relations if r.from_key == from_key)

    def relations_to(self, to_key: str) -> tuple[CharacterRelation, ...]:
        """All incoming relations towards the given character."""
        return tuple(r for r in self.relations if r.to_key == to_key)


def load_character_relations(path: Path) -> CharacterRelationIndex:
    """Load character relations from a TOML file; return empty index if missing."""

    if not path.exists():
        return CharacterRelationIndex(relations=())

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    relations = tuple(
        CharacterRelation(
            from_key=str(item["from"]),
            to_key=str(item["to"]),
            affinity=int(item.get("affinity", 0)),
            tags=tuple(str(t) for t in item.get("tags", ())),
        )
        for item in raw_data.get("relations", [])
    )
    return CharacterRelationIndex(relations=relations)
