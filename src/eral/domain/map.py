"""Map definitions used by the port runtime."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortMapLocation:
    """Static location on the port map."""

    key: str
    display_name: str
    zone: str
    tags: tuple[str, ...] = ()
    start: bool = False
    visibility: str = "public"  # "public", "private", "hidden"


@dataclass(frozen=True, slots=True)
class PortConnection:
    """Directed or bidirectional edge between two locations."""

    source: str
    target: str
    bidirectional: bool = True


@dataclass(frozen=True, slots=True)
class PortMap:
    """Small but expandable map definition."""

    key: str
    display_name: str
    locations: tuple[PortMapLocation, ...]
    connections: tuple[PortConnection, ...]

    def location_by_key(self, key: str) -> PortMapLocation:
        for location in self.locations:
            if location.key == key:
                return location
        raise KeyError(key)

    def starting_location(self) -> PortMapLocation:
        for location in self.locations:
            if location.start:
                return location
        return self.locations[0]

    def neighbors_of(self, key: str) -> tuple[str, ...]:
        neighbors: list[str] = []
        for connection in self.connections:
            if connection.source == key:
                neighbors.append(connection.target)
            if connection.bidirectional and connection.target == key:
                neighbors.append(connection.source)
        return tuple(neighbors)

    def visible_neighbors(self, key: str, can_see_private: bool = False) -> tuple[str, ...]:
        """Return neighbor keys the player can see, filtering by visibility rules.

        - "public" locations are always visible.
        - "private" locations are visible only when can_see_private is True.
        - "hidden" locations are never visible (reserved for future use).
        """
        result: list[str] = []
        for neighbor_key in self.neighbors_of(key):
            loc = self.location_by_key(neighbor_key)
            if loc.visibility == "hidden":
                continue
            if loc.visibility == "private" and not can_see_private:
                continue
            result.append(neighbor_key)
        return tuple(result)

