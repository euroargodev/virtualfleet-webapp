from shiny import ui
import numpy as np
import datetime
import os
import json

# Sidebar
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

def check_nc_file(value):
    if not value.lower().endswith(".nc"):
        return "File should be a NetCDF file (ends with .nc)"
    if not os.path.exists(value):
        return "File not found at this path"
    return None

def check_config_file(value):
    """Validate an uploaded variable mapping config file.

    Expects a JSON file defining two objects, i.e.:
        {
            "variables": {"U": "uo", "V": "vo"},
            "dimensions": {"time": "time", "depth": "depth", "lat": "latitude", "lon": "longitude"}
        }
    """
    if not value:
        #return "A config file is required"
        return None
        
    try:
        with open(value[0]["datapath"], "r") as f:
            config = json.load(f)
    except Exception:
        return "File could not be read"

    if not isinstance(config, dict):
        return "File must contain dict"

    variables = config.get("variables")
    dimensions = config.get("dimensions")

    if not isinstance(variables, dict):
        return "File must define a 'variables' dict"
    if not isinstance(dimensions, dict):
        return "File must define a 'dimensions' dict"

    missing_variables = {"U", "V"} - variables.keys()
    if missing_variables:
        return f"'variables' is missing required keys: {', '.join(sorted(missing_variables))}"

    missing_dimensions = {"time", "lat", "lon", "depth"} - dimensions.keys()
    if missing_dimensions:
        return f"'dimensions' is missing required keys: {', '.join(sorted(missing_dimensions))}"

    return None

# Map module
def interpolate_along_line(coords, n):
    """Evenly space n points between two [lon, lat] endpoints (inclusive)."""
    (lon1, lat1), (lon2, lat2) = coords
    lons = np.linspace(lon1, lon2, n)
    lats = np.linspace(lat1, lat2, n)
    return [{"lat": lat, "lon": lon} for lon, lat in zip(lons, lats)]

#from pyproj import Geod
#def interpolate_along_line_geodesic(coords, n):
#    (lon1, lat1), (lon2, lat2) = coords
#    geod = Geod(ellps="WGS84")
#    pts = geod.npts(lon1, lat1, lon2, lat2, n - 2)  # excludes endpoints
#    all_pts = [(lon1, lat1)] + pts + [(lon2, lat2)]
#    return [{"lat": lat, "lon": lon} for lon, lat in all_pts]


def resolve_deployment_points(points, lines, shapes, num_floats):
    """Validate the current map state and return the list of float
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
        return 0 # Needs to be implemented
    return points


def build_geojson(points, start_date):
    timestamp = datetime.datetime.combine(start_date, datetime.time.min).isoformat() # Check required format
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