"""Map definitions used by the port runtime."""

from __future__ import annotations

import heapq
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortMapLocation:
    """Static location on the port map."""

    key: str
    display_name: str
    zone: str
    area_key: str = ""
    sub_area_key: str = ""
    tags: tuple[str, ...] = ()
    start: bool = False
    visibility: str = "public"  # "public", "private", "hidden"
    capacity_soft: int = 0
    capacity_hard: int = 0
    overflow_targets: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PortMapArea:
    """Top-level area in the layered port map."""

    key: str
    display_name: str
    kind: str
    faction_key: str | None = None


@dataclass(frozen=True, slots=True)
class PortMapSubArea:
    """Intermediate cluster inside one top-level area."""

    key: str
    area_key: str
    display_name: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PortMapSlot:
    """Optional internal slot grouping for one location."""

    key: str
    location_key: str
    display_name: str
    capacity_soft: int = 0


@dataclass(frozen=True, slots=True)
class PortConnection:
    """Directed or bidirectional edge between two locations."""

    source: str
    target: str
    bidirectional: bool = True
    cost_minutes: int = 15


@dataclass(frozen=True, slots=True)
class PathResult:
    """UI-agnostic shortest path result."""

    destination: str
    path: tuple[str, ...]
    total_cost: int

    @property
    def hop_count(self) -> int:
        return max(0, len(self.path) - 1)


@dataclass(frozen=True, slots=True)
class PortMap:
    """Small but expandable map definition."""

    key: str
    display_name: str
    locations: tuple[PortMapLocation, ...]
    connections: tuple[PortConnection, ...]
    areas: tuple[PortMapArea, ...] = ()
    sub_areas: tuple[PortMapSubArea, ...] = ()
    slots: tuple[PortMapSlot, ...] = ()

    def area_keys(self) -> tuple[str, ...]:
        return tuple(area.key for area in self.areas)

    def area_by_key(self, key: str) -> PortMapArea | None:
        for area in self.areas:
            if area.key == key:
                return area
        return None

    def sub_area_by_key(self, key: str) -> PortMapSubArea:
        for sub_area in self.sub_areas:
            if sub_area.key == key:
                return sub_area
        raise KeyError(key)

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

    # ── Adjacency helper ────────────────────────────────────────────

    def _adjacency_with_costs(self) -> dict[str, list[tuple[str, int]]]:
        """Build adjacency list: location_key -> [(neighbor_key, cost)]."""
        adj: dict[str, list[tuple[str, int]]] = {
            loc.key: [] for loc in self.locations
        }
        for conn in self.connections:
            adj[conn.source].append((conn.target, conn.cost_minutes))
            if conn.bidirectional:
                adj[conn.target].append((conn.source, conn.cost_minutes))
        return adj

    # ── Pathfinding (Dijkstra) ──────────────────────────────────────

    def shortest_path(self, from_key: str, to_key: str) -> PathResult | None:
        """Return the shortest path between two locations, or None if unreachable."""
        if from_key == to_key:
            return PathResult(to_key, (from_key,), 0)
        adj = self._adjacency_with_costs()
        if from_key not in adj or to_key not in adj:
            return None
        dist: dict[str, int] = {from_key: 0}
        prev: dict[str, str] = {}
        heap: list[tuple[int, str]] = [(0, from_key)]
        visited: set[str] = set()
        while heap:
            cost, node = heapq.heappop(heap)
            if node in visited:
                continue
            visited.add(node)
            if node == to_key:
                break
            for neighbor, edge_cost in adj.get(node, ()):
                new_cost = cost + edge_cost
                if neighbor not in dist or new_cost < dist[neighbor]:
                    dist[neighbor] = new_cost
                    prev[neighbor] = node
                    heapq.heappush(heap, (new_cost, neighbor))
        if to_key not in visited:
            return None
        path: list[str] = []
        cur: str = to_key
        while cur != from_key:
            path.append(cur)
            cur = prev[cur]
        path.append(from_key)
        path.reverse()
        return PathResult(to_key, tuple(path), dist[to_key])

    def reachable_destinations(
        self, from_key: str, can_see_private: bool = False,
    ) -> dict[str, PathResult]:
        """All reachable locations from *from_key*, filtered by visibility.

        Returns a dict mapping destination_key -> PathResult.
        """
        adj = self._adjacency_with_costs()
        if from_key not in adj:
            return {}
        dist: dict[str, int] = {from_key: 0}
        prev: dict[str, str] = {}
        heap: list[tuple[int, str]] = [(0, from_key)]
        visited: set[str] = set()
        while heap:
            cost, node = heapq.heappop(heap)
            if node in visited:
                continue
            visited.add(node)
            for neighbor, edge_cost in adj.get(node, ()):
                new_cost = cost + edge_cost
                if neighbor not in dist or new_cost < dist[neighbor]:
                    dist[neighbor] = new_cost
                    prev[neighbor] = node
                    heapq.heappush(heap, (new_cost, neighbor))
        results: dict[str, PathResult] = {}
        for dest_key in visited:
            if dest_key == from_key:
                continue
            loc = self.location_by_key(dest_key)
            if loc.visibility == "hidden":
                continue
            if loc.visibility == "private" and not can_see_private:
                continue
            path: list[str] = []
            cur: str = dest_key
            while cur != from_key:
                path.append(cur)
                cur = prev[cur]
            path.append(from_key)
            path.reverse()
            results[dest_key] = PathResult(dest_key, tuple(path), dist[dest_key])
        return results

