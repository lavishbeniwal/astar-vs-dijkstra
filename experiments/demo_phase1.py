"""Phase 1 demo: run Dijkstra and A* on a synthetic grid graph across several
routes and print a side-by-side comparison. Run from the project root:

    python -m experiments.demo_phase1

The last route is a deliberate edge case, not a typical result: see the note
printed after the table.
"""

from src.graph import build_grid_graph
from src.metrics import compare

ROWS, COLS = 15, 15

ROUTES = [
    ((0, 0), (14, 3), "mostly horizontal"),
    ((0, 0), (3, 14), "mostly vertical"),
    ((7, 0), (7, 14), "straight horizontal line"),
    ((0, 7), (14, 7), "straight vertical line"),
    ((2, 3), (11, 9), "off-center asymmetric"),
    ((0, 0), (14, 14), "perfect diagonal (edge case)"),
]


def main() -> None:
    graph = build_grid_graph(ROWS, COLS, spacing=1.0)
    print(f"Grid graph: {ROWS}x{COLS} ({len(graph)} nodes)\n")

    header = f"{'Route':30}{'Cost':>8}{'Dijkstra':>10}{'A*':>8}{'Reduction':>11}{'Match':>8}"
    print(header)
    print("-" * len(header))

    for start, goal, label in ROUTES:
        result = compare(graph, start, goal)
        d, a = result.dijkstra, result.astar
        print(
            f"{label:30}{d.cost:>8.2f}{d.nodes_explored:>10}{a.nodes_explored:>8}"
            f"{result.nodes_explored_reduction_pct:>10.1f}%{str(result.costs_match):>8}"
        )

    print(
        "\nNote on the diagonal edge case: when start and goal are exactly on a "
        "45-degree line, the grid has many tied-optimal staircase paths, and a "
        "straight-line heuristic can't tell them apart. A* falls back to "
        "exploring almost as much as Dijkstra. Every other route above shows "
        "a large reduction. This is real experimental evidence, not a fluke -- "
        "keep it, it directly answers the 'is A* always better?' question."
    )


if __name__ == "__main__":
    main()
