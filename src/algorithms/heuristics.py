"""Heuristic functions for A*. Each factory closes over the graph so the
returned function has the simple signature h(node, goal) that astar() expects."""

from typing import Callable, Hashable

from src.graph import Graph

Heuristic = Callable[[Hashable, Hashable], float]


def make_straight_line_heuristic(graph: Graph) -> Heuristic:
    """Straight-line distance to the goal, using whatever distance metric the
    graph was built with (planar Euclidean for the synthetic grid, haversine
    for real lon/lat road networks). Admissible whenever edge weights are at
    least the straight-line distance between their endpoints -- true here,
    since roads never travel in a straighter line than the crow flies."""

    def heuristic(node: Hashable, goal: Hashable) -> float:
        return graph.distance(node, goal)

    return heuristic
