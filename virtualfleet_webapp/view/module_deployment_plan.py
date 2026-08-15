import json
import uuid

import numpy as np
from ipyleaflet import GeomanDrawControl, Map, Marker, ScaleControl, basemaps
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from virtualfleet_webapp.logic.utils import (
    build_geojson,
    read_deployment_plan,
    resolve_deployment_points,
    section_title,
)


@module.ui
def deployment_plan_ui():
    return ui.TagList(
        section_title(2, "Deployment Plan", tooltip="TBD"),
        # Hidden radio group driving which card is "selected"
        ui.div(
            {"class": "option-radio"},
            ui.input_radio_buttons(
                id="deploy_option",
                label=None,
                choices={"A": "Option A", "B": "Option B"},
                selected="A",
            ),
        ),
        # Option A card
        ui.output_ui("card_a"),
        # Option B card
        ui.output_ui("card_b"),
        ui.input_switch(id="show_plan", label="Show current plan", value=False),
        ui.hr({"class": "section-divider"}),
    )


@module.ui
def deployment_plan_map_ui():
    return ui.card(
        output_widget("map"),
    )


@module.server
def deployment_plan_server(input, output, session):

    # Reactive state for the deployment plan
    deployment_points = reactive.Value([])  # Option A: drawn/placed on the map
    uploaded_plan = reactive.Value(None)  # Option B: parsed from an uploaded file
    last_validated_option = reactive.Value(None)  # "A" or "B", whichever was last validated

    # Reactive state for the map's drawing layer
    point_markers = reactive.Value([])
    line_markers = reactive.Value([])
    shape_markers = reactive.Value([])
    preview_markers = []

    #######
    # MAP #
    #######
    m = Map(
        center=(0, 0),
        zoom=2,
        basemap=basemaps.Esri.WorldImagery,
        scroll_wheel_zoom=True,
    )

    # Add options
    m.add(ScaleControl(position="bottomleft"))

    # Drawing control for markers, lines and polygons, check also https://geoman.io/docs/leaflet/toolbar
    dc = GeomanDrawControl(
        position="topright",
        marker={"pathOptions": {}},
        circlemarker={},
        polyline={"pathOptions": {}},
        rectangle={"pathOptions": {}},
        polygon={},
        edit=False,
        drag=True,
        cut=False,
        rotate=False,
    )

    # Add or remove drawn objects
    def add_or_remove(store, action, value):
        current = store()
        if action == "create":
            store.set([*current, value])
        elif action == "remove" and value in current:
            current = (
                current.copy()
            )  # needed to avoid modifying the list in place, which would not trigger a reactive update
            current.remove(value)
            store.set(current)

    def handle_draw(
        _control, action, geo_json
    ):  # see https://ipyleaflet.readthedocs.io/en/latest/_modules/ipyleaflet/leaflet.html#GeomanDrawControl

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
                # A deployment line is exactly 2 points, no intermediate point.
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
                # TODO
                add_or_remove(shape_markers, action, geom["coordinates"])

    dc.on_draw(handle_draw)
    m.add(dc)

    def clear_all_layers():
        dc.clear_markers()
        dc.clear_circle_markers()
        dc.clear_polylines()
        dc.clear_polygons()
        dc.clear_rectangles()

    @output
    @render_widget
    def map():
        return m

    ######################
    # Deployment options #
    ######################
    @reactive.effect
    @reactive.event(input.pick_a)
    def _():
        ui.update_radio_buttons(id="deploy_option", selected="A")

    @reactive.effect
    @reactive.event(input.pick_b)
    def _():
        ui.update_radio_buttons(id="deploy_option", selected="B")

    @render.ui
    def card_a():
        selected = input.deploy_option() == "A"
        card_class = "option-card selected" if selected else "option-card collapsed"

        header = ui.div(
            {"class": "option-header", "onclick": f"Shiny.setInputValue('{session.ns('pick_a')}', Math.random())"},
            ui.tags.i(class_="fa-solid fa-map"),
            "Option A — create with map",
        )

        if not selected:
            return ui.div({"class": card_class}, header)

        return ui.div(
            {"class": card_class},
            header,
            ui.input_numeric(id="num_floats", label=ui.span("Number of floats", style="font-size: 0.90rem;"), value=0),
            ui.input_date(id="start_date", label=ui.span("Start date", style="font-size: 0.90rem;")),
            ui.input_action_button(
                id="validate_plan_a",
                label=ui.HTML('<i class="fa-solid fa-check"></i> Validate plan'),
                style="width: 100%; background: var(--bs-primary); color: white; border: none; margin-top: 8px;",
            ),
            ui.download_button(
                id="export_plan",
                label=ui.HTML('<i class="fa-solid fa-download"></i> Export deployment plan'),
                style="width: 100%; background: var(--bs-light); color: black; border: none; margin-top: 8px;",
            ),
        )

    @render.ui
    def card_b():
        selected = input.deploy_option() == "B"
        card_class = "option-card selected" if selected else "option-card collapsed"

        header = ui.div(
            {"class": "option-header", "onclick": f"Shiny.setInputValue('{session.ns('pick_b')}', Math.random())"},
            ui.tags.i(class_="fa-solid fa-file-upload"),
            "Option B — import a pre-built plan",
        )

        if not selected:
            return ui.div({"class": card_class}, header)

        return ui.div(
            {"class": card_class},
            header,
            ui.input_file(id="plan_file", label="", accept=[".geojson"]),
            ui.input_action_button(
                id="validate_plan_b",
                label=ui.HTML('<i class="fa-solid fa-check"></i> Validate plan'),
                style="width: 100%; background: var(--bs-primary); color: white; border: none; margin-top: 8px;",
            ),
        )

    # Reflects whichever option was last validated, regardless of which
    # card is currently displayed in the sidebar.
    @reactive.calc
    def last_validated_plan():
        option = last_validated_option()

        if option == "B":
            return uploaded_plan()

        if option == "A":
            points = deployment_points()
            start = input.start_date()
            if not points or not start:
                return None
            t = np.datetime64(start)
            return {
                "lat": np.array([p["lat"] for p in points]),
                "lon": np.array([p["lon"] for p in points]),
                "time": np.array([t] * len(points)),
            }
        return None

    @reactive.effect
    @reactive.event(input.validate_plan_a)
    def _():
        try:
            points = resolve_deployment_points(point_markers(), line_markers(), shape_markers(), input.num_floats())
        except ValueError as error:
            ui.notification_show(str(error), type="error")
            return
        deployment_points.set(points)
        last_validated_option.set("A")
        ui.notification_show("Plan OK", type="message")

    @reactive.effect
    @reactive.event(input.validate_plan_b)
    def _():
        file = input.plan_file()
        if not file:
            ui.notification_show("Upload a .geojson file first.", type="error")
            return
        try:
            plan = read_deployment_plan(file[0]["datapath"])
        except Exception:
            ui.notification_show("Could not read the uploaded plan.", type="error")
            return
        uploaded_plan.set(plan)
        last_validated_option.set("B")
        ui.notification_show("Plan OK", type="message")

    @render.download_button(filename=lambda: f"deployment_plan_{uuid.uuid4().hex}.geojson")
    def export_plan():
        geojson = build_geojson(deployment_points(), input.start_date())
        yield json.dumps(geojson, indent=2)

    # "Show current plan" replaces whatever is being drafted on the map with
    # read-only markers for the validated plan. Switching it off just hides
    # those markers again — it does not restore the draft that was cleared.
    @reactive.effect
    def _():
        for marker in preview_markers:
            m.remove(marker)
        preview_markers.clear()

        current_plan = last_validated_plan()
        if not input.show_plan() or not current_plan:
            return

        clear_all_layers()
        point_markers.set([])
        line_markers.set([])
        shape_markers.set([])

        for lat, lon in zip(current_plan["lat"], current_plan["lon"], strict=True):
            marker = Marker(location=(float(lat), float(lon)), draggable=False)
            m.add(marker)
            preview_markers.append(marker)

    return last_validated_plan
