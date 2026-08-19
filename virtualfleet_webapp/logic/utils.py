import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from shiny import ui


# Generic functions
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
    if not value.endswith(".nc"):
        return "File should be a NetCDF file"
    if not Path(value).exists():
        return "File not found at this path"
    return None


# Speed field
def check_config_file(value):
    """Validate an uploaded variable mapping config file.

    Expects a JSON file defining two objects, for e.g.:
        {
            "variables": {"U": "uo", "V": "vo"},
            "dimensions": {"time": "time", "depth": "depth", "lat": "latitude", "lon": "longitude"}
        }
    """
    if not value:
        #return "A config file is required"
        return None

    try:
        with Path(value[0]["datapath"]).open() as f:
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

    # gives all elements from the first set of variables that are not in the dict.
    missing_variables = {"U", "V"} - variables.keys() 
    if missing_variables:
        return f"'variables' is missing required keys: {', '.join(sorted(missing_variables))}"

    missing_dimensions = {"time", "lat", "lon", "depth"} - dimensions.keys()
    if missing_dimensions:
        return f"'dimensions' is missing required keys: {', '.join(sorted(missing_dimensions))}"

    return None


def read_config_file(config_file):
    """Read a variable mapping configuration file. 
    All checks are done in check_config_file() hence there is not need for more checks.
    """
    with Path(config_file).open() as f:
        return json.load(f)


# Deployment plan module
def interpolate_along_line(coords, n):
    """Evenly space n points between two [lon, lat] endpoints (including them)."""
    (lon1, lat1), (lon2, lat2) = coords
    lons = np.linspace(lon1, lon2, n)
    lats = np.linspace(lat1, lat2, n)
    return [{"lat": lat, "lon": lon} for lon, lat in zip(lons, lats, strict=True)]


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
        return 0  # Needs to be implemented
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


def read_deployment_plan(filepath):
    """Read a deployment plan GeoJSON file and return it in the format expected by VirtualFleet, 
    i.e.: {'lat': array, 'lon': array, 'time': array}.
    """
    with Path(filepath).open() as f:
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


def build_deployment_plan_geojson(plan):
    """Serialize a validated deployment plan (columnar {'lat', 'lon', 'time'}
    arrays, as returned by the deployment plan module) into a GeoJSON
    FeatureCollection, one Point feature per float.
    """
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                "properties": {"timestamp": np.datetime_as_string(t, unit="D")},
            }
            for lat, lon, t in zip(plan["lat"], plan["lon"], plan["time"], strict=True)
        ],
    }


# Mission config module
def build_mission_config(cycle_duration, life_expectancy, parking_depth, profile_depth, vertical_speed):
    """Build a VirtualFleet float configuration JSON from the "same mission
    for all floats" inputs (cycle_duration, lifespan, parking_depth,
    profile_depth, vertical_speed).
    """
    return {
        "created": datetime.now(UTC).isoformat(),
        "version": "2.0",
        "name": "default",
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


def check_positive_number(value):
    """Validate a numeric input that must be strictly greater than zero."""
    if value is None:
        return "A value is required"
    if value <= 0:
        return "Must be greater than 0"
    return None


def read_mission_config(filepath):
    """Read a "different mission per float" file: a JSON array of VirtualFleet
    float configuration documents (as produced by build_mission_config), one
    per float, in the same order as the deployment plan.
    """
    with Path(filepath).open() as f:
        configs = json.load(f)

    if not isinstance(configs, list):
        raise ValueError("Mission config file must contain a JSON array of configurations.")

    return configs


def flatten_mission_config(config):
    """Flatten one or more VF-ArgoFloat-Configuration documents (as produced by
    build_mission_config / read_mission_config) into the flat parameter dicts
    expected by VirtualFleet's `mission` argument.
    """
    if isinstance(config, list):
        return [flatten_mission_config(c) for c in config]
    return {p["name"]: p["value"] for p in config["parameters"]}
