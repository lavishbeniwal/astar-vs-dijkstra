"""Runs both algorithms on the same start/goal and packages their results for
side-by-side comparison."""

from dataclasses import dataclass

from src.algorithms.astar import astar
from src.algorithms.common import SearchResult
from src.algorithms.dijkstra import dijkstra
from src.algorithms.heuristics import make_straight_line_heuristic
from src.graph import Graph


@dataclass
class ComparisonResult:
    dijkstra: SearchResult
    astar: SearchResult

    @property
    def nodes_explored_reduction_pct(self) -> float:
        if self.dijkstra.nodes_explored == 0:
            return 0.0
        return (1 - self.astar.nodes_explored / self.dijkstra.nodes_explored) * 100

    @property
    def costs_match(self) -> bool:
        return abs(self.dijkstra.cost - self.astar.cost) < 1e-6


def compare(graph: Graph, start, goal) -> ComparisonResult:
    heuristic = make_straight_line_heuristic(graph)
    return ComparisonResult(
        dijkstra=dijkstra(graph, start, goal),
        astar=astar(graph, start, goal, heuristic),
    )
