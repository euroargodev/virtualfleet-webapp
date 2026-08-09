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


def resolve_deployment_points(points, lines, num_floats):
    """Validate the current map state and return the flat list of float
    positions to deploy. Raises ValueError if the plan is incomplete.
    Only the first drawn line is used if there are several.
    """
    if not points and not lines:
        raise ValueError("Place markers or draw a deployment line first.")
    if lines:
        if not num_floats or num_floats < 2:
            raise ValueError("Set 'Number of floats' to at least 2 for a line deployment.")
        return interpolate_along_line(lines[0], num_floats)
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