"""Graph representation for the road network: nodes are intersections with 2D
positions, edges are road segments weighted by distance."""

import math
from typing import Callable, Hashable, Optional

DistanceFn = Callable[[tuple[float, float], tuple[float, float]], float]


def _euclidean(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


class Graph:
    def __init__(self, distance_fn: Optional[DistanceFn] = None):
        self.adjacency: dict[Hashable, list[tuple[Hashable, float]]] = {}
        self.positions: dict[Hashable, tuple[float, float]] = {}
        self._distance_fn = distance_fn or _euclidean

    def add_node(self, node: Hashable, x: float, y: float) -> None:
        self.adjacency.setdefault(node, [])
        self.positions[node] = (x, y)

    def add_edge(
        self, a: Hashable, b: Hashable, weight: Optional[float] = None, bidirectional: bool = True
    ) -> None:
        if weight is None:
            weight = self.distance(a, b)
        self.adjacency[a].append((b, weight))
        if bidirectional:
            self.adjacency[b].append((a, weight))

    def neighbors(self, node: Hashable) -> list[tuple[Hashable, float]]:
        return self.adjacency.get(node, [])

    def distance(self, a: Hashable, b: Hashable) -> float:
        """Straight-line distance between two nodes' positions, regardless of
        whether an edge connects them. Used both to default edge weights and
        as A*'s admissible heuristic. Uses Euclidean distance on a flat plane
        by default, or whatever distance_fn was supplied (e.g. haversine for
        real lon/lat coordinates)."""
        return self._distance_fn(self.positions[a], self.positions[b])

    @property
    def nodes(self) -> list[Hashable]:
        return list(self.adjacency.keys())

    def __len__(self) -> int:
        return len(self.adjacency)


def build_grid_graph(rows: int, cols: int, spacing: float = 1.0) -> Graph:
    """A 4-connected grid graph: a simplified city block layout with uniform
    street spacing. Used to validate both algorithms before real map data."""
    graph = Graph()
    for r in range(rows):
        for c in range(cols):
            graph.add_node((r, c), x=c * spacing, y=r * spacing)
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                graph.add_edge((r, c), (r, c + 1))
            if r + 1 < rows:
                graph.add_edge((r, c), (r + 1, c))
    return graph
