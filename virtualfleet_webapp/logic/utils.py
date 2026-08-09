from shiny import ui
import numpy as np
import datetime

# UI
def section_title(number, text, tooltip=None):
    """Numbered circle badge + header used at the top of each sidebar section."""
    children = [
        ui.span({"class": "section-badge"}, str(number)),
        ui.h5(text, style="margin: 0;"),
    ]
    if tooltip:
        children.append(ui.HTML('<i class="fa-regular fa-circle-question"></i>'))

    heading = ui.div({"class": "section-title"}, *children)

    if tooltip:
        return ui.tooltip(heading, tooltip, placement="right")
    return heading

# Map module
def interpolate_along_line(coords, n):
    """Split a drawn line (list of [lon, lat] vertices) into n points spaced
    evenly by path length, endpoints included. Linear interpolation in
    lon/lat space.
    """
    pts = np.array(coords, dtype=float)
    cumulative = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    targets = np.linspace(0, cumulative[-1], n)
    lons = np.interp(targets, cumulative, pts[:, 0])
    lats = np.interp(targets, cumulative, pts[:, 1])
    return [{"lat": lat, "lon": lon} for lon, lat in zip(lons, lats)]


def _inside_ring(candidates, ring):
    """Ray-casting point-in-polygon test, vectorized over `candidates`
    (N, 2) array of [lon, lat], against a single linear ring (list of
    [lon, lat], first point == last point).
    See also https://en.wikipedia.org/wiki/Point_in_polygon
    """
    ring = np.array(ring, dtype=float)
    x, y = candidates[:, 0], candidates[:, 1]
    x1, y1 = ring[:-1, 0], ring[:-1, 1]
    x2, y2 = ring[1:, 0], ring[1:, 1]

    inside = np.zeros(len(candidates), dtype=bool)
    for i in range(len(x1)):
        with np.errstate(divide="ignore", invalid="ignore"):
            crosses = ((y1[i] > y) != (y2[i] > y)) & (
                x < (x2[i] - x1[i]) * (y - y1[i]) / (y2[i] - y1[i]) + x1[i]
            )
        inside ^= crosses
    return inside


def random_points_in_polygon(coords, n, max_attempts=200):
    """Uniformly sample n random points strictly inside a GeoJSON polygon
    (coords = list of linear rings; holes are ignored, only the exterior
    ring is used, which is fine for a hand-drawn polygon/rectangle).
    """
    ring = np.array(coords[0], dtype=float)
    lower, upper = ring.min(axis=0), ring.max(axis=0) # Bounding box of the polygon

    rng = np.random.default_rng()
    found = []
    for _ in range(max_attempts):
        remaining = n - len(found)
        if remaining <= 0:
            break
        candidates = rng.uniform(lower, upper, size=(remaining * 4, 2))
        found.extend(candidates[_inside_ring(candidates, ring)][:remaining].tolist())

    if len(found) < n:
        raise ValueError(
            "Could not fit that many floats inside the drawn polygon — try a larger shape or fewer floats."
        )
    return [{"lat": lat, "lon": lon} for lon, lat in found]


def resolve_deployment_points(points, lines, shapes, num_floats):
    """Validate the current map state and return the flat list of float
    positions to deploy. Raises ValueError if the plan is incomplete.
    Only the first drawn line/shape is used if there are several.
    """
    if not points and not lines and not shapes:
        raise ValueError("Place markers, draw a deployment line, or draw a polygon first.")
    if lines:
        if not num_floats or num_floats < 2:
            raise ValueError("Set 'Number of floats' to at least 2 for a line deployment.")
        return interpolate_along_line(lines[0], num_floats)
    if shapes:
        if not num_floats or num_floats < 1:
            raise ValueError("Set 'Number of floats' to at least 1 for a polygon deployment.")
        return random_points_in_polygon(shapes[0], num_floats)
    return points


def build_geojson(points, start_date):
    # Single shared timestamp for now (per-marker override is future work).
    timestamp = datetime.datetime.combine(start_date, datetime.time.min).isoformat()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
                "properties": {"timestamp": timestamp, "depth": 0},
            }
            for p in points
        ],
    }