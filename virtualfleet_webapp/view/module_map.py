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

                # Only one deployment mode (markers / line / polygon) can be active at a time. 
                if geom_type == "Point":
                    if action == "create" and (line_markers() or shape_markers()):
                        ui.notification_show(
                            "Can't mix single markers with an existing line/polygon — clear it first.",
                            type="error",
                        )
                        dc.clear_markers()
                        dc.clear_circle_markers()
                        continue
                    lon, lat = geom["coordinates"]
                    add_or_remove(point_markers, action, {"lat": lat, "lon": lon})

                elif geom_type == "LineString":
                    if action == "create" and (point_markers() or shape_markers()):
                        ui.notification_show(
                            "Can't mix a deployment line with existing markers/polygon — clear it first.",
                            type="error",
                        )
                        dc.clear_polylines()
                        continue
                    # A deployment line is a straight source-to-destination segment: exactly 2 points, no intermediate point.
                    if action == "create" and len(geom["coordinates"]) != 2:
                        ui.notification_show(
                            "A deployment line must have exactly 2 points (start and end) — no extra clicks in between.",
                            type="error",
                        )
                        dc.clear_polylines()
                        continue
                    add_or_remove(line_markers, action, geom["coordinates"])

                elif geom_type in ("Polygon", "MultiPolygon"):
                    if action == "create" and (point_markers() or line_markers()):
                        ui.notification_show(
                            "Can't mix a polygon with existing markers/line — clear it first.",
                            type="error",
                        )
                        dc.clear_polygons()
                        dc.clear_rectangles()
                        continue
                    # TODO: regular (grid) distribution as an alternative to
                    # the random fill used at validate/export time.
                    add_or_remove(shape_markers, action, geom["coordinates"])

        dc.on_draw(handle_draw)
        m.add(dc)

        return m

    return point_markers, line_markers, shape_markers
