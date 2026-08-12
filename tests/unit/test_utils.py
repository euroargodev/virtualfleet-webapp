import datetime
import json

import pytest

from virtualfleet_webapp.logic.utils import (
    build_geojson,
    check_config_file,
    interpolate_along_line,
    resolve_deployment_points,
)


def _write_config(tmp_path, content):
    config_path = tmp_path / "config.json"
    config_path.write_text(content)
    return [{"datapath": str(config_path)}]


FULL_VARIABLES = {"U": "uo", "V": "vo"}
FULL_DIMENSIONS = {"time": "time", "depth": "depth", "lat": "latitude", "lon": "longitude"}


class TestCheckConfigFile:
    def test_no_upload_is_valid(self):
        assert check_config_file(None) is None
        assert check_config_file([]) is None

    def test_valid_config_passes(self, tmp_path):
        content = json.dumps({"variables": FULL_VARIABLES, "dimensions": FULL_DIMENSIONS})
        assert check_config_file(_write_config(tmp_path, content)) is None

    def test_top_level_must_be_an_object(self, tmp_path):
        content = json.dumps([1, 2, 3])
        error = check_config_file(_write_config(tmp_path, content))
        assert error is not None

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

    def test_invalid_json_returns_error(self, tmp_path):
        error = check_config_file(_write_config(tmp_path, "this is not valid json {"))
        assert error is not None


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
        with pytest.raises(ValueError):
            resolve_deployment_points([], [], [], num_floats=5)

    def test_points_only_returns_points_unchanged(self):
        points = [{"lat": 1.0, "lon": 2.0}, {"lat": 3.0, "lon": 4.0}]
        result = resolve_deployment_points(points, [], [], num_floats=0)
        assert result == points

    def test_line_requires_at_least_two_floats(self):
        line = [(0.0, 0.0), (1.0, 0.0)]
        with pytest.raises(ValueError):
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
        with pytest.raises(ValueError):
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
        assert feature["properties"]["timestamp"] == "2026-01-15T00:00:00"
        assert feature["properties"]["depth"] == 0

    def test_empty_points_produces_empty_feature_list(self):
        geojson = build_geojson([], datetime.date(2026, 1, 15))
        assert geojson["features"] == []
