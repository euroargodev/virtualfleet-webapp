import datetime
import json

import numpy as np
import pytest

from virtualfleet_webapp.logic.utils import (
    build_deployment_plan_geojson,
    build_geojson,
    build_mission_config,
    check_config_file,
    check_positive_number,
    flatten_mission_config,
    interpolate_along_line,
    read_config_file,
    read_deployment_plan,
    read_mission_config,
    resolve_deployment_points,
)


def _write_config(tmp_path, content):
    config_path = tmp_path / "config.json"
    config_path.write_text(content)
    return [{"datapath": str(config_path)}]


FULL_VARIABLES = {"U": "uo", "V": "vo"}
FULL_DIMENSIONS = {"time": "time", "depth": "depth", "lat": "latitude", "lon": "longitude"}


class TestCheckConfigFile:
    def test_valid_config_passes(self, tmp_path):
        content = json.dumps({"variables": FULL_VARIABLES, "dimensions": FULL_DIMENSIONS})
        assert check_config_file(_write_config(tmp_path, content)) is None

    def test_missing_variables_dict(self, tmp_path):
        content = json.dumps({"dimensions": FULL_DIMENSIONS})
        error = check_config_file(_write_config(tmp_path, content))
        assert "variables" in error

    def test_missing_dimensions_dict(self, tmp_path):
        content = json.dumps({"variables": FULL_VARIABLES})
        error = check_config_file(_write_config(tmp_path, content))
        assert "dimensions" in error

    def test_missing_required_variable_key(self, tmp_path):
        content = json.dumps({"variables": {"U": "uo"}, "dimensions": FULL_DIMENSIONS})
        error = check_config_file(_write_config(tmp_path, content))
        assert error is not None
        assert "V" in error

    def test_missing_required_dimension_key(self, tmp_path):
        content = json.dumps(
            {"variables": FULL_VARIABLES, "dimensions": {"time": "time", "lat": "latitude", "lon": "longitude"}}
        )
        error = check_config_file(_write_config(tmp_path, content))
        assert error is not None
        assert "depth" in error

    def test_no_file_uploaded_is_valid(self):
        assert check_config_file(None) is None


class TestCheckPositiveNumber:
    def test_positive_value_passes(self):
        assert check_positive_number(5) is None

    def test_zero_fails(self):
        assert check_positive_number(0) is not None

    def test_negative_fails(self):
        assert check_positive_number(-1) is not None

    def test_none_fails(self):
        assert check_positive_number(None) is not None


class TestReadConfigFile:
    def test_reads_the_config_file_contents(self, tmp_path):
        config = {"variables": FULL_VARIABLES, "dimensions": FULL_DIMENSIONS}
        path = tmp_path / "config.json"
        path.write_text(json.dumps(config))

        assert read_config_file(str(path)) == config


class TestInterpolateAlongLine:
    def test_endpoints_are_included(self):
        points = interpolate_along_line([(0.0, 0.0), (10.0, 0.0)], 3)
        assert points[0] == {"lat": 0.0, "lon": 0.0}
        assert points[-1] == {"lat": 0.0, "lon": 10.0}

    def test_returns_n_evenly_spaced_points(self):
        points = interpolate_along_line([(0.0, 0.0), (4.0, 0.0)], 5)
        assert [p["lon"] for p in points] == [0.0, 1.0, 2.0, 3.0, 4.0]
        assert all(p["lat"] == 0.0 for p in points)


class TestResolveDeploymentPoints:
    def test_raises_when_nothing_drawn(self):
        with pytest.raises(ValueError, match="Place markers"):
            resolve_deployment_points([], [], [], num_floats=5)

    def test_points_only_returns_points_unchanged(self):
        points = [{"lat": 1.0, "lon": 2.0}, {"lat": 3.0, "lon": 4.0}]
        result = resolve_deployment_points(points, [], [], num_floats=0)
        assert result == points

    def test_line_requires_at_least_two_floats(self):
        line = [(0.0, 0.0), (1.0, 0.0)]
        with pytest.raises(ValueError, match="at least 2 for a line deployment"):
            resolve_deployment_points([], [line], [], num_floats=1)

    def test_line_interpolates_requested_number_of_floats(self):
        line = [(0.0, 0.0), (1.0, 0.0)]
        result = resolve_deployment_points([], [line], [], num_floats=4)
        assert len(result) == 4

    def test_line_ignores_extra_lines_and_uses_the_first(self):
        first = [(0.0, 0.0), (1.0, 0.0)]
        second = [(9.0, 9.0), (10.0, 10.0)]
        result = resolve_deployment_points([], [first, second], [], num_floats=2)
        assert result == interpolate_along_line(first, 2)

    def test_shape_requires_at_least_one_float(self):
        with pytest.raises(ValueError, match="at least 1 for a polygon deployment"):
            resolve_deployment_points([], [], [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]], num_floats=0)

    def test_shape_deployment_is_not_implemented_yet(self):
        # resolve_deployment_points() returns a placeholder `0` for shapes today
        # (see the "# Needs to be implemented" note in logic/utils.py). Update this
        # test once real polygon-based point generation lands.
        shape = [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]]
        assert resolve_deployment_points([], [], shape, num_floats=3) == 0


class TestBuildGeojson:
    def test_produces_a_feature_collection_with_one_point_feature_per_input_point(self):
        points = [{"lat": 1.5, "lon": 2.5}, {"lat": -3.0, "lon": 4.0}]
        geojson = build_geojson(points, datetime.date(2026, 1, 15))

        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 2

        feature = geojson["features"][0]
        assert feature["type"] == "Feature"
        assert feature["geometry"] == {"type": "Point", "coordinates": [2.5, 1.5]}
        assert feature["properties"]["timestamp"] == "2026-01-15"
        assert feature["properties"]["depth"] == 0

    def test_empty_points_produces_empty_feature_list(self):
        geojson = build_geojson([], datetime.date(2026, 1, 15))
        assert geojson["features"] == []


class TestReadDeploymentPlan:
    def test_reads_a_geojson_plan_into_columnar_arrays(self, tmp_path):
        points = [{"lat": 1.5, "lon": 2.5}, {"lat": -3.0, "lon": 4.0}]
        geojson = build_geojson(points, datetime.date(2026, 1, 15))
        path = tmp_path / "plan.geojson"
        path.write_text(json.dumps(geojson))

        plan = read_deployment_plan(str(path))

        assert list(plan["lat"]) == [1.5, -3.0]
        assert list(plan["lon"]) == [2.5, 4.0]
        assert list(plan["time"]) == [np.datetime64("2026-01-15")] * 2

    def test_empty_features_produce_empty_arrays(self, tmp_path):
        geojson = build_geojson([], datetime.date(2026, 1, 15))
        path = tmp_path / "plan.geojson"
        path.write_text(json.dumps(geojson))

        plan = read_deployment_plan(str(path))

        assert len(plan["lat"]) == 0
        assert len(plan["lon"]) == 0
        assert len(plan["time"]) == 0


class TestBuildDeploymentPlanGeojson:
    def test_produces_a_feature_per_point_with_day_precision_timestamp(self):
        plan = {
            "lat": np.array([1.5, -3.0]),
            "lon": np.array([2.5, 4.0]),
            "time": np.array([np.datetime64("2026-01-15")] * 2),
        }

        geojson = build_deployment_plan_geojson(plan)

        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 2
        feature = geojson["features"][0]
        assert feature["geometry"] == {"type": "Point", "coordinates": [2.5, 1.5]}
        assert feature["properties"]["timestamp"] == "2026-01-15"

    def test_timestamp_keeps_day_precision_even_with_nanosecond_input(self):
        plan = {
            "lat": np.array([1.5]),
            "lon": np.array([2.5]),
            "time": np.array([np.datetime64("2026-01-15T00:00:00.000000000")]),
        }

        geojson = build_deployment_plan_geojson(plan)

        assert geojson["features"][0]["properties"]["timestamp"] == "2026-01-15"

    def test_round_trips_through_read_deployment_plan_with_day_precision(self, tmp_path):
        points = [{"lat": 1.5, "lon": 2.5}]
        original = build_geojson(points, datetime.date(2026, 1, 15))
        path = tmp_path / "plan.geojson"
        path.write_text(json.dumps(original))

        plan = read_deployment_plan(str(path))
        rebuilt = build_deployment_plan_geojson(plan)

        assert rebuilt["features"][0]["properties"]["timestamp"] == "2026-01-15"

    def test_empty_plan_produces_empty_feature_list(self):
        plan = {"lat": np.array([]), "lon": np.array([]), "time": np.array([], dtype="datetime64[D]")}
        assert build_deployment_plan_geojson(plan)["features"] == []


class TestBuildMissionConfig:
    def test_produces_the_expected_document_shape(self):
        config = build_mission_config(
            cycle_duration=240,
            life_expectancy=200,
            parking_depth=1000,
            profile_depth=2000,
            vertical_speed=0.09,
        )

        assert config["version"] == "2.0"
        assert config["name"] == "default"
        assert "created" in config
        assert config["$schema"].startswith("https://")
        assert len(config["parameters"]) == 5


    def test_parameter_values_and_types(self):
        config = build_mission_config(
            cycle_duration=240,
            life_expectancy=200,
            parking_depth=1000,
            profile_depth=2000,
            vertical_speed=0.09,
        )
        values = {p["name"]: p["value"] for p in config["parameters"]}

        assert values["cycle_duration"] == 240.0
        assert values["life_expectancy"] == 200
        assert isinstance(values["life_expectancy"], int)
        assert values["parking_depth"] == 1000.0
        assert values["profile_depth"] == 2000.0
        assert values["vertical_speed"] == 0.09


class TestReadMissionConfig:
    def test_reads_a_list_of_configs(self, tmp_path):
        configs = [
            build_mission_config(
                cycle_duration=240,
                life_expectancy=200,
                parking_depth=depth,
                profile_depth=2000,
                vertical_speed=0.09
            )
            for depth in enumerate([100, 200, 500])
        ]
        path = tmp_path / "mission.json"
        path.write_text(json.dumps(configs))


    def test_raises_when_file_is_not_a_json_array(self, tmp_path):
        path = tmp_path / "mission.json"
        path.write_text(json.dumps({"not": "a list"}))

        with pytest.raises(ValueError, match="must contain a JSON array"):
            read_mission_config(str(path))


class TestFlattenMissionConfig:
    def test_flattens_a_single_config_document(self):
        config = build_mission_config(
            cycle_duration=240,
            life_expectancy=200,
            parking_depth=1000,
            profile_depth=2000,
            vertical_speed=0.09,
        )

        flat = flatten_mission_config(config)

        assert flat == {
            "cycle_duration": 240.0,
            "life_expectancy": 200,
            "parking_depth": 1000.0,
            "profile_depth": 2000.0,
            "vertical_speed": 0.09,
        }

    def test_flattens_a_list_of_config_documents(self):
        configs = [
            build_mission_config(
                cycle_duration=240,
                life_expectancy=200,
                parking_depth=depth,
                profile_depth=2000,
                vertical_speed=0.09
            )
            for i, depth in enumerate([100, 200, 500])
        ]

        flat = flatten_mission_config(configs)

        assert [f["parking_depth"] for f in flat] == [100.0, 200.0, 500.0]
        assert all(f["cycle_duration"] == 240.0 for f in flat)
