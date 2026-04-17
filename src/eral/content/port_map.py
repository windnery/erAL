"""Load a small expandable port map from TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path

from eral.domain.map import (
    PortConnection,
    PortMap,
    PortMapArea,
    PortMapLocation,
    PortMapSlot,
    PortMapSubArea,
)


def load_port_map(path: Path) -> PortMap:
    """Load the starter port map definition."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    meta = raw_data.get("meta", {})
    areas = tuple(
        PortMapArea(
            key=item["key"],
            display_name=item["display_name"],
            kind=item["kind"],
            faction_key=item.get("faction_key"),
        )
        for item in raw_data.get("areas", [])
    )
    sub_areas = tuple(
        PortMapSubArea(
            key=item["key"],
            area_key=item["area_key"],
            display_name=item["display_name"],
            tags=tuple(item.get("tags", [])),
        )
        for item in raw_data.get("sub_areas", [])
    )
    locations = tuple(
        PortMapLocation(
            key=item["key"],
            display_name=item["display_name"],
            zone=item["zone"],
            area_key=item.get("area_key", ""),
            sub_area_key=item.get("sub_area_key", ""),
            tags=tuple(item.get("tags", [])),
            start=bool(item.get("start", False)),
            visibility=item.get("visibility", "public"),
            capacity_soft=int(item.get("capacity_soft", 0)),
            capacity_hard=int(item.get("capacity_hard", 0)),
            overflow_targets=tuple(item.get("overflow_targets", [])),
        )
        for item in raw_data.get("locations", [])
    )
    connections = tuple(
        PortConnection(
            source=item["from"],
            target=item["to"],
            bidirectional=bool(item.get("bidirectional", True)),
            cost_minutes=int(item.get("cost_minutes", 15)),
        )
        for item in raw_data.get("connections", [])
    )
    slots = tuple(
        PortMapSlot(
            key=item["key"],
            location_key=item["location_key"],
            display_name=item["display_name"],
            capacity_soft=int(item.get("capacity_soft", 0)),
        )
        for item in raw_data.get("slots", [])
    )

    return PortMap(
        key=meta.get("key", "port"),
        display_name=meta.get("display_name", "Port"),
        areas=areas,
        sub_areas=sub_areas,
        locations=locations,
        connections=connections,
        slots=slots,
    )

