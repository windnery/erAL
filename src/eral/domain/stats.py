"""Numeric state blocks using era-style axis catalogs."""

from __future__ import annotations

from dataclasses import dataclass, field

from eral.content.stat_axes import AxisFamily, StatAxisCatalog


@dataclass(slots=True)
class StatBlock:
    """Named values for one numeric axis family."""

    family: AxisFamily
    values: dict[str, int] = field(default_factory=dict)

    @classmethod
    def zeroed(cls, family: AxisFamily, catalog: StatAxisCatalog) -> "StatBlock":
        return cls(
            family=family,
            values={axis.key: 0 for axis in catalog.family_axes(family)},
        )

    def get(self, key: str) -> int:
        return self.values.get(key, 0)

    def set(self, key: str, value: int) -> None:
        self.values[key] = value

    def add(self, key: str, delta: int) -> int:
        self.values[key] = self.get(key) + delta
        return self.values[key]

    def clear(self) -> None:
        for key in tuple(self.values.keys()):
            self.values[key] = 0


@dataclass(slots=True)
class IndexedStatBlock:
    """Integer-keyed block that preserves original era indices."""

    family: AxisFamily
    values: dict[int, int] = field(default_factory=dict)

    @classmethod
    def zeroed(cls, family: AxisFamily, catalog: StatAxisCatalog) -> "IndexedStatBlock":
        return cls(
            family=family,
            values={axis.era_index: 0 for axis in catalog.family_axes(family)},
        )

    def get(self, era_index: int) -> int:
        return self.values.get(era_index, 0)

    def set(self, era_index: int, value: int) -> None:
        self.values[era_index] = value

    def add(self, era_index: int, delta: int) -> int:
        self.values[era_index] = self.get(era_index) + delta
        return self.values[era_index]

    def clear(self) -> None:
        for era_index in tuple(self.values.keys()):
            self.values[era_index] = 0


@dataclass(slots=True)
class CharacterEraCompatState:
    """Per-character raw compatibility blocks imported from eraTW."""

    abl: IndexedStatBlock
    talent: IndexedStatBlock
    cflag: IndexedStatBlock

    @classmethod
    def zeroed(cls, catalog: StatAxisCatalog) -> "CharacterEraCompatState":
        return cls(
            abl=IndexedStatBlock.zeroed(AxisFamily.ABL, catalog),
            talent=IndexedStatBlock.zeroed(AxisFamily.TALENT, catalog),
            cflag=IndexedStatBlock.zeroed(AxisFamily.CFLAG, catalog),
        )


@dataclass(slots=True)
class ActorNumericState:
    """Typed numeric state attached to an actor."""

    base: StatBlock
    palam: StatBlock
    source: StatBlock
    juel: StatBlock
    exp: StatBlock
    cup: IndexedStatBlock
    compat: CharacterEraCompatState

    @classmethod
    def zeroed(
        cls,
        catalog: StatAxisCatalog,
    ) -> "ActorNumericState":
        source_axes = catalog.family_axes(AxisFamily.SOURCE)
        return cls(
            base=StatBlock.zeroed(AxisFamily.BASE, catalog),
            palam=StatBlock.zeroed(AxisFamily.PALAM, catalog),
            source=StatBlock.zeroed(AxisFamily.SOURCE, catalog),
            juel=StatBlock.zeroed(AxisFamily.JUEL, catalog),
            exp=StatBlock.zeroed(AxisFamily.EXP, catalog),
            cup=IndexedStatBlock(
                family=AxisFamily.SOURCE,
                values={axis.era_index: 0 for axis in source_axes},
            ),
            compat=CharacterEraCompatState.zeroed(catalog),
        )

    def clear_source(self) -> None:
        self.source.clear()

    def clear_cup(self) -> None:
        self.cup.clear()
