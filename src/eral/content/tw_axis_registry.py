"""Load full axis registries imported from eraTW CSV files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from eral.content.stat_axes import AxisFamily


@dataclass(frozen=True, slots=True)
class TwAxisEntry:
    """A raw axis entry imported from eraTW."""

    family: AxisFamily
    key: str
    era_index: int
    label: str
    section: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class TwAxisRegistry:
    """Imported eraTW axis metadata grouped by family."""

    by_family: dict[AxisFamily, tuple[TwAxisEntry, ...]]
    by_index: dict[tuple[AxisFamily, int], TwAxisEntry]

    def family_entries(self, family: AxisFamily) -> tuple[TwAxisEntry, ...]:
        return self.by_family.get(family, ())

    def get_by_index(self, family: AxisFamily, era_index: int) -> TwAxisEntry:
        return self.by_index[(family, era_index)]


def load_tw_axis_registry(path: Path) -> TwAxisRegistry:
    """Load the generated eraTW axis registry JSON."""

    raw_data = json.loads(path.read_text(encoding="utf-8"))
    by_family: dict[AxisFamily, tuple[TwAxisEntry, ...]] = {}
    by_index: dict[tuple[AxisFamily, int], TwAxisEntry] = {}

    for family_name, raw_entries in raw_data.items():
        family = AxisFamily(family_name)
        entries = tuple(
            TwAxisEntry(
                family=family,
                key=item["key"],
                era_index=int(item["era_index"]),
                label=item["label"],
                section=item.get("section"),
                notes=item.get("notes"),
            )
            for item in raw_entries
        )
        by_family[family] = entries
        for entry in entries:
            by_index[(family, entry.era_index)] = entry

    return TwAxisRegistry(by_family=by_family, by_index=by_index)

