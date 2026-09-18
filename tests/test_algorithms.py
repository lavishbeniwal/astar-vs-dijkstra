"""Correctness checks for Dijkstra and A* before trusting either on real map
data. Run from the project root:

    python -m unittest discover -s tests
"""

import unittest

from src.algorithms.astar import astar
from src.algorithms.dijkstra import dijkstra
from src.algorithms.heuristics import make_straight_line_heuristic
from src.graph import Graph, build_grid_graph


class TestAlgorithmsOnGrid(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = build_grid_graph(6, 6)
        self.heuristic = make_straight_line_heuristic(self.graph)

    def test_same_optimal_cost_on_several_routes(self) -> None:
        pairs = [((0, 0), (5, 5)), ((0, 5), (5, 0)), ((2, 2), (2, 2)), ((0, 0), (0, 5))]
        for start, goal in pairs:
            d = dijkstra(self.graph, start, goal)
            a = astar(self.graph, start, goal, self.heuristic)
            self.assertTrue(d.found)
            self.assertTrue(a.found)
            self.assertAlmostEqual(d.cost, a.cost, places=6)

    def test_path_is_connected_and_cost_matches_its_edges(self) -> None:
        start, goal = (0, 0), (5, 5)
        result = dijkstra(self.graph, start, goal)
        self.assertEqual(result.path[0], start)
        self.assertEqual(result.path[-1], goal)

        total = 0.0
        for a, b in zip(result.path, result.path[1:]):
            edge_weights = dict(self.graph.neighbors(a))
            self.assertIn(b, edge_weights)
            total += edge_weights[b]
        self.assertAlmostEqual(total, result.cost, places=6)

    def test_astar_never_explores_more_nodes_than_dijkstra(self) -> None:
        start, goal = (0, 0), (5, 5)
        d = dijkstra(self.graph, start, goal)
        a = astar(self.graph, start, goal, self.heuristic)
        self.assertLessEqual(a.nodes_explored, d.nodes_explored)

    def test_unreachable_goal_is_reported_as_not_found(self) -> None:
        graph = Graph()
        graph.add_node("A", 0, 0)
        graph.add_node("B", 10, 10)
        result = dijkstra(graph, "A", "B")
        self.assertFalse(result.found)
        self.assertEqual(result.cost, float("inf"))
        self.assertEqual(result.path, [])

    def test_start_equals_goal(self) -> None:
        start = (3, 3)
        result = dijkstra(self.graph, start, start)
        self.assertEqual(result.path, [start])
        self.assertEqual(result.cost, 0.0)


if __name__ == "__main__":
    unittest.main()
