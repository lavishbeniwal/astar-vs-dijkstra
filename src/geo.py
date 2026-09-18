"""Geographic distance for real road-network coordinates, where positions are
(longitude, latitude) degrees rather than a flat (x, y) plane."""

import math

EARTH_RADIUS_M = 6_371_000.0


def haversine_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Great-circle distance in meters between two (lon, lat) points."""
    lon1, lat1 = p1
    lon2, lat2 = p2
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_degrees(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Compass bearing in degrees [0, 360) from point p1 to p2."""
    lon1, lat1 = math.radians(p1[0]), math.radians(p1[1])
    lon2, lat2 = math.radians(p2[0]), math.radians(p2[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


MANHATTAN_GRID_BEARING_DEG = 29.0  # Manhattan's avenues run ~29 degrees east of true north


def grid_alignment_angle(
    p1: tuple[float, float], p2: tuple[float, float], grid_bearing_deg: float = MANHATTAN_GRID_BEARING_DEG
) -> float:
    """How diagonal a route is relative to the street grid, in degrees from
    0 (running parallel to an avenue or street -- the easy case for a
    straight-line heuristic) to 45 (running along the diagonal between them --
    the hard case, since many equally-short staircase paths become tied)."""
    line_bearing = bearing_degrees(p1, p2) % 180  # a line has no direction, so ignore its sense
    offset = (line_bearing - grid_bearing_deg) % 90
    return min(offset, 90 - offset)
