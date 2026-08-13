from shiny import ui
from datetime import datetime, timezone
import numpy as np
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
    timestamp = start_date.strftime("%Y-%m-%d")
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

# Deployment plan
def read_deployment_plan(filepath):
    """Read a deployment-plan GeoJSON file return it in the columnar format expected by the simulation:
    {'lat': array, 'lon': array, 'time': array}.
    """
    with open(filepath, "r") as f:
        geojson = json.load(f)

    lats, lons, times = [], [], []
    for feature in geojson["features"]:
        lon, lat = feature["geometry"]["coordinates"]
        lats.append(lat)
        lons.append(lon)
        times.append(np.datetime64(feature["properties"]["timestamp"]))

    return {
        "lat": np.array(lats),
        "lon": np.array(lons),
        "time": np.array(times),
    }

# Mission parameters
def build_mission_config(cycle_duration, life_expectancy, parking_depth, profile_depth, vertical_speed, name="default"):
    """Build a VirtualFleet float configuration JSON from the "same mission
    for all floats" inputs (cycle_duration, lifespan, parking_depth,
    profile_depth, vertical_speed).
    """
    return {
        "created": datetime.now(timezone.utc).isoformat(),
        "version": "2.0",
        "name": name,
        "parameters": [
            {
                "name": "cycle_duration",
                "value": float(cycle_duration),
                "description": "Maximum length of float complete cycle",
                "meta": {"unit": "hours", "dtype": "float", "techkey": "CONFIG_CycleTime_hours"},
            },
            {
                "name": "life_expectancy",
                "value": int(life_expectancy),
                "description": "Maximum number of completed cycle",
                "meta": {"unit": "cycle", "dtype": "int", "techkey": "CONFIG_MaxCycles_NUMBER"},
            },
            {
                "name": "parking_depth",
                "value": float(parking_depth),
                "description": "Drifting depth",
                "meta": {"unit": "m", "dtype": "float", "techkey": "CONFIG_ParkPressure_dbar"},
            },
            {
                "name": "profile_depth",
                "value": float(profile_depth),
                "description": "Maximum profile depth",
                "meta": {"unit": "m", "dtype": "float", "techkey": "CONFIG_ProfilePressure_dbar"},
            },
            {
                "name": "vertical_speed",
                "value": float(vertical_speed),
                "description": "Vertical profiling speed",
                "meta": {"unit": "m/s", "dtype": "float", "techkey": ""},
            },
        ],
        "$schema": "https://raw.githubusercontent.com/euroargodev/VirtualFleet/json-schemas-FloatConfiguration/schemas/VF-ArgoFloat-Configuration.json",
    }


def read_mission_config(filepath):
    """Read a "different mission per float" file: a JSON array of VirtualFleet
    float configuration documents (as produced by build_mission_config), one
    per float, in the same order as the deployment plan.
    """
    with open(filepath, "r") as f:
        configs = json.load(f)

    if not isinstance(configs, list):
        raise ValueError("Mission config file must contain a JSON array of configurations.")

    return configs