"""Phase 2 demo: run Dijkstra and A* on the real Manhattan drivable road
network (via osmnx/OpenStreetMap) across several real routes. Run from the
project root:

    python -m experiments.demo_phase2

The first run downloads and caches the road network (~1 minute); later runs
load it from data/manhattan_drive.graphml instantly.
"""

from src.graph_builder import build_road_graph, nearest_node
from src.metrics import compare

# (lat, lon) pairs for named Manhattan locations.
ROUTES = [
    ((40.7033, -74.0170), (40.8677, -73.9212), "Battery Park -> Inwood (long, north-south)"),
    ((40.7402, -74.0027), (40.7527, -73.9772), "West Village -> Grand Central"),
    ((40.7825, -73.9601), (40.7850, -73.9713), "Upper East Side -> Upper West Side (crosstown)"),
    ((40.7074, -74.0113), (40.8075, -73.9465), "Financial District -> Harlem (long diagonal)"),
    ((40.7359, -74.0036), (40.7369, -74.0015), "Two blocks in the West Village (short local trip)"),
]


def main() -> None:
    graph = build_road_graph()
    print(f"Manhattan drivable road network: {len(graph)} nodes\n")

    header = f"{'Route':48}{'Dist (km)':>10}{'Dijkstra':>10}{'A*':>8}{'Reduction':>11}{'Match':>8}"
    print(header)
    print("-" * len(header))

    for (start_lat, start_lon), (goal_lat, goal_lon), label in ROUTES:
        start = nearest_node(graph, start_lat, start_lon)
        goal = nearest_node(graph, goal_lat, goal_lon)
        result = compare(graph, start, goal)
        d, a = result.dijkstra, result.astar
        print(
            f"{label:48}{d.cost / 1000:>10.2f}{d.nodes_explored:>10}{a.nodes_explored:>8}"
            f"{result.nodes_explored_reduction_pct:>10.1f}%{str(result.costs_match):>8}"
        )


if __name__ == "__main__":
    main()
