"""A* search: like Dijkstra, but orders the frontier by f(n) = g(n) + h(n),
so the estimated remaining distance to the goal steers expansion toward it."""

import heapq
import itertools
import time
from typing import Hashable

from src.algorithms.common import SearchResult, reconstruct_path
from src.algorithms.heuristics import Heuristic
from src.graph import Graph


def astar(graph: Graph, start: Hashable, goal: Hashable, heuristic: Heuristic) -> SearchResult:
    start_time = time.perf_counter()
    counter = itertools.count()

    g_score: dict[Hashable, float] = {start: 0.0}
    prev: dict[Hashable, Hashable] = {}
    visited: set[Hashable] = set()
    explored_order: list[Hashable] = []
    heap: list[tuple[float, int, Hashable]] = [(heuristic(start, goal), next(counter), start)]

    while heap:
        _, _, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        explored_order.append(node)
        if node == goal:
            break

        for neighbor, weight in graph.neighbors(node):
            if neighbor in visited:
                continue
            tentative_g = g_score[node] + weight
            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                prev[neighbor] = node
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(heap, (f_score, next(counter), neighbor))

    found = goal in visited
    return SearchResult(
        path=reconstruct_path(prev, start, goal) if found else [],
        cost=g_score.get(goal, float("inf")),
        nodes_explored=len(explored_order),
        explored_order=explored_order,
        execution_time=time.perf_counter() - start_time,
        found=found,
    )
