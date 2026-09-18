"""Dijkstra's algorithm / uniform cost search: expands nodes purely by cost
accumulated from the start, with no notion of where the goal is."""

import heapq
import itertools
import time
from typing import Hashable

from src.algorithms.common import SearchResult, reconstruct_path
from src.graph import Graph


def dijkstra(graph: Graph, start: Hashable, goal: Hashable) -> SearchResult:
    start_time = time.perf_counter()
    counter = itertools.count()  # tie-breaker so heap never compares nodes directly

    dist: dict[Hashable, float] = {start: 0.0}
    prev: dict[Hashable, Hashable] = {}
    visited: set[Hashable] = set()
    explored_order: list[Hashable] = []
    heap: list[tuple[float, int, Hashable]] = [(0.0, next(counter), start)]

    while heap:
        d, _, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        explored_order.append(node)
        if node == goal:
            break

        for neighbor, weight in graph.neighbors(node):
            if neighbor in visited:
                continue
            new_dist = d + weight
            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(heap, (new_dist, next(counter), neighbor))

    found = goal in visited
    return SearchResult(
        path=reconstruct_path(prev, start, goal) if found else [],
        cost=dist.get(goal, float("inf")),
        nodes_explored=len(explored_order),
        explored_order=explored_order,
        execution_time=time.perf_counter() - start_time,
        found=found,
    )
