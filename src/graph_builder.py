"""Builds our Graph representation from a real road network pulled via osmnx,
so the same search algorithms from Phase 1 run against actual city streets."""

import os

import osmnx as ox

from src.geo import haversine_distance
from src.graph import Graph

DEFAULT_PLACE = "Manhattan, New York, USA"
DEFAULT_CACHE_PATH = "data/manhattan_drive.graphml"


def load_osm_graph(
    place: str = DEFAULT_PLACE, cache_path: str = DEFAULT_CACHE_PATH, network_type: str = "drive"
):
    """Loads the road network from a local cache when available, otherwise
    downloads it from OpenStreetMap (via the Overpass API) and caches it --
    downloading a whole borough takes about a minute and shouldn't be repeated
    on every run."""
    if os.path.exists(cache_path):
        return ox.load_graphml(cache_path)

    nx_graph = ox.graph_from_place(place, network_type=network_type)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    ox.save_graphml(nx_graph, cache_path)
    return nx_graph


def build_road_graph(place: str = DEFAULT_PLACE, cache_path: str = DEFAULT_CACHE_PATH) -> Graph:
    """Converts an osmnx/networkx road network into our Graph representation.
    Distances use real edge lengths (meters) from OSM, positions use real
    (lon, lat) coordinates with a haversine distance metric, and one-way
    streets are preserved by adding edges in only the direction osmnx gives
    them (never forced bidirectional)."""
    nx_graph = load_osm_graph(place, cache_path)

    graph = Graph(distance_fn=haversine_distance)
    for node_id, data in nx_graph.nodes(data=True):
        graph.add_node(node_id, x=float(data["x"]), y=float(data["y"]))

    for u, v, data in nx_graph.edges(data=True):
        length = float(data["length"]) if "length" in data else graph.distance(u, v)
        graph.add_edge(u, v, weight=length, bidirectional=False)

    return graph


def nearest_node(graph: Graph, lat: float, lon: float):
    """Finds the graph node closest to a (lat, lon) coordinate -- used to turn
    a human-picked location into a start/goal node for the search algorithms."""
    target = (lon, lat)
    return min(graph.nodes, key=lambda n: haversine_distance(target, graph.positions[n]))
