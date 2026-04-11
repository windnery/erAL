"""Load a small expandable port map from TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path

from eral.domain.map import PortConnection, PortMap, PortMapLocation


def load_port_map(path: Path) -> PortMap:
    """Load the starter port map definition."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    meta = raw_data.get("meta", {})
    locations = tuple(
        PortMapLocation(
            key=item["key"],
            display_name=item["display_name"],
            zone=item["zone"],
            tags=tuple(item.get("tags", [])),
            start=bool(item.get("start", False)),
            visibility=item.get("visibility", "public"),
        )
        for item in raw_data.get("locations", [])
    )
    connections = tuple(
        PortConnection(
            source=item["from"],
            target=item["to"],
            bidirectional=bool(item.get("bidirectional", True)),
        )
        for item in raw_data.get("connections", [])
    )

    return PortMap(
        key=meta.get("key", "port"),
        display_name=meta.get("display_name", "Port"),
        locations=locations,
        connections=connections,
    )

