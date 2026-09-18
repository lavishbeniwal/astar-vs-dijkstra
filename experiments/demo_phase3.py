"""Phase 3 demo: render side-by-side maps of Dijkstra's and A*'s explored
nodes on the real Manhattan road network. Run from the project root:

    python -m experiments.demo_phase3

Saves PNGs to experiments/output/.
"""

import os

from src.graph_builder import build_road_graph, nearest_node
from src.metrics import compare
from src.visualize import plot_comparison

OUTPUT_DIR = "experiments/output"

ROUTES = [
    (
        (40.7402, -74.0027),
        (40.7527, -73.9772),
        "West Village -> Grand Central",
        "west_village_to_grand_central.png",
    ),
    (
        (40.7074, -74.0113),
        (40.8075, -73.9465),
        "Financial District -> Harlem (the weak-heuristic diagonal case)",
        "financial_district_to_harlem.png",
    ),
]


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    graph = build_road_graph()
    print(f"Manhattan drivable road network: {len(graph)} nodes\n")

    for (start_lat, start_lon), (goal_lat, goal_lon), label, filename in ROUTES:
        start = nearest_node(graph, start_lat, start_lon)
        goal = nearest_node(graph, goal_lat, goal_lon)
        result = compare(graph, start, goal)

        save_path = os.path.join(OUTPUT_DIR, filename)
        plot_comparison(graph, start, goal, result.dijkstra, result.astar, suptitle=label, save_path=save_path)
        print(f"{label}")
        print(
            f"  Dijkstra explored {result.dijkstra.nodes_explored} nodes, "
            f"A* explored {result.astar.nodes_explored} "
            f"({result.nodes_explored_reduction_pct:.1f}% fewer) -> saved {save_path}\n"
        )


if __name__ == "__main__":
    main()
