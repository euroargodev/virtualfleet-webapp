"""
Server logic
"""

import json
import uuid

from shiny import reactive, render, req, ui
# import custom modules
from virtualfleet_webapp.logic.utils import build_geojson, resolve_deployment_points
from virtualfleet_webapp.view.module_map import map_server

def server(input, output, session):

    # Reactive state for the deployment plan, shared across the sidebar (Part 1)
    # and the map/export logic (Part 3).
    valid_plan = reactive.Value(False)
    deployment_points = reactive.Value([])

    # Part 1 - Deployment options for the sidebar
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
            {"class": "option-header", "onclick": "Shiny.setInputValue('pick_a', Math.random())"},
            ui.tags.i(class_="fa-solid fa-map"),
            "Option A — create with map",
        )

        if not selected:
            return ui.div({"class": card_class}, header)

        # Grey out (and disable clicks on) the export button until the plan is validated.
        export_style = "width: 100%; color: black; border: none; margin-top: 8px; "
        export_style += (
            "background: var(--bs-light);"
            if valid_plan()
            else "background: #ced4da; opacity: 0.65; pointer-events: none; cursor: not-allowed;"
        )

        return ui.div(
            {"class": card_class},
            header,
            ui.input_numeric(id="num_floats", label=ui.span("Number of floats", style="font-size: 0.90rem;"), value=0),
            ui.input_date(id="start_date", label=ui.span("Start date", style="font-size: 0.90rem;")),
            ui.input_action_button(
                id="validate_plan", label=ui.HTML('<i class="fa-solid fa-check"></i> Validate plan'),
                style="width: 100%; background: var(--bs-primary); color: white; border: none; margin-top: 8px;",
            ),
            ui.download_button(
                id="export_plan", label=ui.HTML('<i class="fa-solid fa-download"></i> Export deployment plan'),
                style=export_style,
            ),
        )

    @render.ui
    def card_b():
        selected = input.deploy_option() == "B"
        card_class = "option-card selected" if selected else "option-card collapsed"

        header = ui.div(
            {"class": "option-header", "onclick": "Shiny.setInputValue('pick_b', Math.random())"},
            ui.tags.i(class_="fa-solid fa-file-upload"),
            "Option B — import a pre-built plan",
        )

        if not selected:
            return ui.div({"class": card_class}, header)

        return ui.div(
            {"class": card_class},
            header,
            ui.input_file(id="plan_file", label="", accept=[".geojson"]),
        )
    
    # Part 2 - Mission parameters for the sidebar
    @reactive.effect
    @reactive.event(input.pick_same)
    def _():
        ui.update_radio_buttons("mission_mode", selected="same")
 
    @reactive.effect
    @reactive.event(input.pick_different)
    def _():
        ui.update_radio_buttons("mission_mode", selected="different")

    @render.ui
    def card_same():
        selected = input.mission_mode() == "same"
        card_class = "option-card selected" if selected else "option-card collapsed"
 
        header = ui.div(
            {"class": "option-header", "onclick": "Shiny.setInputValue('pick_same', Math.random())"},
            ui.tags.i(class_="fa-solid fa-sliders"),
            "Same mission for all floats",
        )
 
        if not selected:
            return ui.div({"class": card_class}, header)
 
        return ui.div(
            {"class": card_class},
            header,
            ui.div(
                {"class": "mission-grid"},
                ui.div(ui.input_numeric(id="cycle_duration", label=ui.span("Cycle length (hours)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
                ui.div(ui.input_numeric(id="parking_depth", label=ui.span("Drifting depth (m)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
                ui.div(ui.input_numeric(id="profile_depth", label=ui.span("Max. profile depth (m)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
                ui.div(ui.input_numeric(id="lifespan", label=ui.span("Life expectancy (cycles)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
                ui.div(
                    {"class": "full-row"},
                    ui.input_numeric(id="vertical_speed", label=ui.span("Vertical speed (m/s)", style="font-size: 0.90rem;"), value=0, update_on='blur'),
                ),
            ),
        )
    
    @render.ui
    def card_different():
        selected = input.mission_mode() == "different"
        card_class = "option-card selected" if selected else "option-card collapsed"
 
        header = ui.div(
            {"class": "option-header", "onclick": "Shiny.setInputValue('pick_different', Math.random())"},
            ui.tags.i(class_="fa-solid fa-file-upload"),
            "Different mission per float",
        )
 
        if not selected:
            return ui.div({"class": card_class}, header)
 
        return ui.div(
            {"class": card_class},
            header,
            ui.input_file(id="mission_config_file", label="", accept=[".csv", ".txt"]), # should be a python dict()
        )

    # Part 3 - Map for the main panel (see modules/module_map.py)
    point_markers, line_markers, shape_markers = map_server("map")

    # Any change to the drawn geometry or float count invalidates a previously
    # validated plan, so a stale plan can't be exported.
    @reactive.effect
    def _invalidate_plan_on_change(): # could also just write def _()
        point_markers()
        line_markers()
        shape_markers()
        input.num_floats()
        valid_plan.set(False)

    @reactive.effect
    @reactive.event(input.validate_plan)
    def _():
        try:
            points = resolve_deployment_points(
                point_markers(), line_markers(), shape_markers(), input.num_floats()
            )
        except ValueError as error:
            ui.notification_show(str(error), type="error")
            return
        deployment_points.set(points)
        valid_plan.set(True)
        ui.notification_show("Plan OK", type="message")

    @render.download_button(filename=lambda: f"deployment_plan_{uuid.uuid4().hex}.geojson")
    def export_plan():
        req(valid_plan())  # does not harm to keep this here even though the button is disabled when the plan is invalid
        geojson = build_geojson(deployment_points(), input.start_date())
        yield json.dumps(geojson, indent=2)
    