"""Shared result type and path reconstruction used by both search algorithms,
so their outputs are directly comparable."""

from dataclasses import dataclass
from typing import Hashable


@dataclass
class SearchResult:
    path: list[Hashable]
    cost: float
    nodes_explored: int
    explored_order: list[Hashable]
    execution_time: float
    found: bool


def reconstruct_path(
    prev: dict[Hashable, Hashable], start: Hashable, goal: Hashable
) -> list[Hashable]:
    if start == goal:
        return [start]
    path = [goal]
    node = goal
    while node != start:
        node = prev[node]
        path.append(node)
    path.reverse()
    return path
