"""Plots the road network with each algorithm's explored nodes and final
route overlaid, so the difference between blind and heuristic-guided search
is visible rather than just numeric."""

import math

import matplotlib

matplotlib.use("Agg")  # headless-safe: no display server required to save figures
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from src.algorithms.common import SearchResult
from src.graph import Graph

DIJKSTRA_CMAP = "YlOrBr"
ASTAR_CMAP = "GnBu"
EDGE_COLOR = "#cfd6d3"
PATH_COLOR = "#2452C9"
START_COLOR = "#1B7A3D"
GOAL_COLOR = "#C0392B"


def _edge_segments(graph: Graph) -> list[list[tuple[float, float]]]:
    segments = []
    for node, edges in graph.adjacency.items():
        p1 = graph.positions[node]
        for neighbor, _ in edges:
            segments.append([p1, graph.positions[neighbor]])
    return segments


def _geographic_aspect(graph: Graph) -> float:
    """Longitude degrees are physically shorter than latitude degrees away
    from the equator; correcting for that keeps the map's proportions true
    to real distances instead of visually stretching it east-west."""
    lats = [y for _, y in graph.positions.values()]
    mean_lat = (min(lats) + max(lats)) / 2
    return 1 / math.cos(math.radians(mean_lat))


def _plot_panel(ax, graph, edge_segments, result: SearchResult, start, goal, cmap_name, label, aspect):
    ax.add_collection(LineCollection(edge_segments, colors=EDGE_COLOR, linewidths=0.4, zorder=1))

    if result.explored_order:
        xs = [graph.positions[n][0] for n in result.explored_order]
        ys = [graph.positions[n][1] for n in result.explored_order]
        visit_order = range(len(result.explored_order))
        ax.scatter(xs, ys, c=list(visit_order), cmap=cmap_name, s=6, linewidths=0, zorder=2)

    if result.found and result.path:
        path_xs = [graph.positions[n][0] for n in result.path]
        path_ys = [graph.positions[n][1] for n in result.path]
        ax.plot(path_xs, path_ys, color=PATH_COLOR, linewidth=2.2, zorder=3, solid_capstyle="round")

    sx, sy = graph.positions[start]
    gx, gy = graph.positions[goal]
    ax.scatter([sx], [sy], c=START_COLOR, s=70, edgecolors="white", linewidths=1, zorder=4)
    ax.scatter([gx], [gy], c=GOAL_COLOR, s=90, marker="*", edgecolors="white", linewidths=1, zorder=4)

    ax.set_aspect(aspect)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(
        f"{label}\n{result.nodes_explored} nodes explored  ·  "
        f"{result.cost / 1000:.2f} km  ·  {result.execution_time * 1000:.1f} ms",
        fontsize=11,
    )


def plot_comparison(graph, start, goal, dijkstra_result, astar_result, suptitle=None, save_path=None):
    edge_segments = _edge_segments(graph)
    aspect = _geographic_aspect(graph)

    lons = [x for x, _ in graph.positions.values()]
    lats = [y for _, y in graph.positions.values()]
    lon_span = (max(lons) - min(lons)) * aspect
    lat_span = max(lats) - min(lats)
    panel_height = 9.0
    panel_width = max(3.0, panel_height * (lon_span / lat_span))

    fig, axes = plt.subplots(1, 2, figsize=(panel_width * 2, panel_height))
    _plot_panel(axes[0], graph, edge_segments, dijkstra_result, start, goal, DIJKSTRA_CMAP, "Dijkstra (Uniform Cost Search)", aspect)
    _plot_panel(axes[1], graph, edge_segments, astar_result, start, goal, ASTAR_CMAP, "A* Search", aspect)

    if suptitle:
        fig.suptitle(suptitle, fontsize=14, fontweight="bold")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.02, wspace=0.03)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
