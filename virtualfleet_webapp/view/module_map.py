from ipyleaflet import Map, ScaleControl, GeomanDrawControl, basemaps
from shiny import module, reactive, ui
from shinywidgets import output_widget, render_widget

@module.ui
def map_ui():
    return ui.card(
        output_widget("map"),
    )

@module.server
def map_server(input, output, session):

    point_markers = reactive.Value([])
    line_markers = reactive.Value([])
    shape_markers = reactive.Value([])

    @output
    @render_widget
    def map():
        m = Map(
                center=(0, 0),
                zoom=2,
                basemap=basemaps.Esri.WorldImagery,
                scroll_wheel_zoom=True,
        )

        # Add options
        m.add(ScaleControl(position='bottomleft'))

        dc = GeomanDrawControl(
            position='topleft',
            draw_circle=False,
            draw_marker=True,
            draw_polygon=True,
            draw_polyline=False,
            draw_rectangle=True,
            edit_mode=False,
            drag_mode=True,
        )

        def add_or_remove(store, action, value):
            current = store()
            if action == "create":
                store.set(current + [value])
            elif action == "remove" and value in current:
                current = current.copy() # needed to avoid modifying the list in place, which would not trigger a reactive update
                current.remove(value)
                store.set(current)

        def handle_draw(_control, action, geo_json):

            for feature in geo_json:
                geom = feature["geometry"]
                geom_type = geom["type"]

                if geom_type == "Point":
                    # Single markers and a deployment line are mutually
                    # exclusive. If a line already exists, the line store
                    # is non-empty and the point store is guaranteed empty
                    # (this same rule prevents the reverse), so clearing
                    # all markers only removes the one just rejected.
                    if action == "create" and line_markers():
                        ui.notification_show(
                            "Can't mix single markers with a deployment line — clear the line first.",
                            type="error",
                        )
                        dc.clear_markers()
                        dc.clear_circle_markers()
                        continue
                    lon, lat = geom["coordinates"]
                    add_or_remove(point_markers, action, {"lat": lat, "lon": lon})

                elif geom_type == "LineString":
                    if action == "create" and point_markers():
                        ui.notification_show(
                            "Can't mix a deployment line with single markers — clear the markers first.",
                            type="error",
                        )
                        dc.clear_polylines()
                        continue
                    # A deployment line is a straight source-to-destination
                    # segment: exactly 2 points, no intermediate vertices.
                    if action == "create" and len(geom["coordinates"]) != 2:
                        ui.notification_show(
                            "A deployment line must have exactly 2 points (start and end) — no extra clicks in between.",
                            type="error",
                        )
                        dc.clear_polylines()
                        continue
                    add_or_remove(line_markers, action, geom["coordinates"])

                elif geom_type in ("Polygon", "MultiPolygon"):
                    # TODO: fill with random or regular points, respect
                    # square/circle/rectangle presets.
                    add_or_remove(shape_markers, action, geom["coordinates"])

        dc.on_draw(handle_draw)
        m.add(dc)

        return m

    return point_markers, line_markers, shape_markers
