"""Phase 5: the actual answer to the research question. Samples many random
source-destination pairs across Manhattan, runs Dijkstra and A* on each, and
aggregates the results -- rather than relying on the handful of hand-picked
routes used in earlier phases.

Tests a specific hypothesis raised by Phases 1-3: that A*'s advantage
shrinks on routes running diagonally across the street grid, because a
straight-line heuristic can't distinguish between many equally-short
staircase paths there.

Run from the project root:

    python -m experiments.batch_comparison
"""

import csv
import math
import os
import random
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.geo import grid_alignment_angle, haversine_distance
from src.graph_builder import build_road_graph
from src.metrics import compare

OUTPUT_DIR = "experiments/output"
N_PAIRS = 150
MIN_DISTANCE_M = 300
SEED = 42


def sample_pairs(graph, n: int, min_distance_m: float, seed: int) -> list[tuple]:
    rng = random.Random(seed)
    nodes = graph.nodes
    pairs = []
    attempts, max_attempts = 0, n * 50
    while len(pairs) < n and attempts < max_attempts:
        attempts += 1
        a, b = rng.sample(nodes, 2)
        if haversine_distance(graph.positions[a], graph.positions[b]) >= min_distance_m:
            pairs.append((a, b))
    return pairs


def run_batch(graph, pairs) -> tuple[list[dict], int]:
    rows, unreachable = [], 0
    for start, goal in pairs:
        result = compare(graph, start, goal)
        if not (result.dijkstra.found and result.astar.found):
            unreachable += 1
            continue
        rows.append(
            {
                "start": start,
                "goal": goal,
                "distance_km": result.dijkstra.cost / 1000,
                "dijkstra_nodes": result.dijkstra.nodes_explored,
                "astar_nodes": result.astar.nodes_explored,
                "reduction_pct": result.nodes_explored_reduction_pct,
                "dijkstra_time_ms": result.dijkstra.execution_time * 1000,
                "astar_time_ms": result.astar.execution_time * 1000,
                "grid_angle_deg": grid_alignment_angle(graph.positions[start], graph.positions[goal]),
                "costs_match": result.costs_match,
            }
        )
    return rows, unreachable


def correlation(xs: list[float], ys: list[float]) -> float:
    mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    return 0.0 if var_x == 0 or var_y == 0 else cov / math.sqrt(var_x * var_y)


def save_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_scatter(rows: list[dict], path: str) -> None:
    angles = [r["grid_angle_deg"] for r in rows]
    reductions = [r["reduction_pct"] for r in rows]
    distances = [r["distance_km"] for r in rows]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].scatter(angles, reductions, alpha=0.6, color="#2452C9", s=22)
    trend = np.polyfit(angles, reductions, 1)
    xs = np.linspace(min(angles), max(angles), 50)
    axes[0].plot(xs, trend[0] * xs + trend[1], color="#C0392B", linewidth=2)
    axes[0].set_xlabel("Grid alignment angle (0° = aligned with the grid, 45° = diagonal)")
    axes[0].set_ylabel("A* nodes-explored reduction (%)")
    axes[0].set_title("Reduction vs. route angle relative to the street grid")

    axes[1].scatter(distances, reductions, alpha=0.6, color="#0E8E86", s=22)
    axes[1].set_xlabel("Route distance (km)")
    axes[1].set_ylabel("A* nodes-explored reduction (%)")
    axes[1].set_title("Reduction vs. route distance")

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def summarize(rows: list[dict]) -> None:
    reductions = [r["reduction_pct"] for r in rows]
    distances = [r["distance_km"] for r in rows]
    angles = [r["grid_angle_deg"] for r in rows]
    matches = sum(1 for r in rows if r["costs_match"])

    print(f"Routes evaluated: {len(rows)}")
    print(f"Optimal-cost match (Dijkstra == A*): {matches}/{len(rows)}\n")

    print(
        f"Nodes-explored reduction -- mean: {statistics.mean(reductions):.1f}%  "
        f"median: {statistics.median(reductions):.1f}%  min: {min(reductions):.1f}%  "
        f"max: {max(reductions):.1f}%  stdev: {statistics.stdev(reductions):.1f}%\n"
    )

    print(f"Correlation(grid-alignment angle, reduction%): {correlation(angles, reductions):.2f}")
    print(f"Correlation(distance, reduction%): {correlation(distances, reductions):.2f}\n")

    print("By grid alignment (0° = aligned with the street grid, 45° = diagonal):")
    for lo, hi, label in [(0, 15, "aligned   (0-15 deg)"), (15, 30, "mixed     (15-30 deg)"), (30, 46, "diagonal  (30-45 deg)")]:
        subset = [r["reduction_pct"] for r in rows if lo <= r["grid_angle_deg"] < hi]
        if subset:
            print(f"  {label}   n={len(subset):3}   mean reduction={statistics.mean(subset):5.1f}%")

    print("\nBy trip length:")
    for lo, hi, label in [(0, 1, "short  (<1 km)"), (1, 5, "medium (1-5 km)"), (5, 100, "long   (>5 km)")]:
        subset = [r["reduction_pct"] for r in rows if lo <= r["distance_km"] < hi]
        if subset:
            print(f"  {label}   n={len(subset):3}   mean reduction={statistics.mean(subset):5.1f}%")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    graph = build_road_graph()
    pairs = sample_pairs(graph, N_PAIRS, MIN_DISTANCE_M, SEED)
    rows, unreachable = run_batch(graph, pairs)

    print(f"Manhattan road network: {len(graph)} nodes")
    print(f"Sampled {len(rows)} reachable pairs ({unreachable} discarded as unreachable)\n")

    save_csv(rows, os.path.join(OUTPUT_DIR, "batch_results.csv"))
    plot_scatter(rows, os.path.join(OUTPUT_DIR, "batch_scatter.png"))
    summarize(rows)


if __name__ == "__main__":
    main()
