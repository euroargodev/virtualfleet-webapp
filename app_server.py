"""
Server logic
"""

import json
import uuid

from shiny import reactive, render, ui
from shiny_validate import InputValidator, check

# import custom modules
from virtualfleet_webapp.logic.utils import build_geojson, resolve_deployment_points, check_nc_file
from virtualfleet_webapp.view.module_map import map_server

def server(input, output, session):

    ###########################
    # General reactive values #
    ###########################
    iv = InputValidator() # Add InputValidator to validate path to speed field

    # Reactive state for the deployment plan, shared across the sidebar (Part 1)
    # and the map/export logic (Part 3).
    deployment_points = reactive.Value([])

    ########################################################
    # Part 1 - Speed field and config file for the sidebar #
    ########################################################
    iv.add_rule("speed_field_path", check_nc_file)
    iv.enable()

    ###############################################
    # Part 2 - Deployment options for the sidebar #
    ###############################################
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
                style="width: 100%; background: var(--bs-light); color: black; border: none; margin-top: 8px;",
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

    ###############################################
    # Part 3 - Mission parameters for the sidebar #
    ###############################################
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
                ui.div(ui.input_numeric(id="cycle_duration", label=ui.span("Cycle length (hours)", style="font-size: 0.90rem;"), value=240, update_on='blur')),
                ui.div(ui.input_numeric(id="parking_depth", label=ui.span("Drifting depth (m)", style="font-size: 0.90rem;"), value=1000, update_on='blur')),
                ui.div(ui.input_numeric(id="profile_depth", label=ui.span("Max. profile depth (m)", style="font-size: 0.90rem;"), value=2000, update_on='blur')),
                ui.div(ui.input_numeric(id="lifespan", label=ui.span("Life expectancy (cycles)", style="font-size: 0.90rem;"), value=500, update_on='blur')),
                ui.div(
                    {"class": "full-row"},
                    ui.input_numeric(id="vertical_speed", label=ui.span("Vertical speed (m/s)", style="font-size: 0.90rem;"), value=0.09, update_on='blur'),
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

    ###############################################
    # Map module part (see modules/module_map.py) #
    ###############################################
    point_markers, line_markers, shape_markers = map_server("map")

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
        ui.notification_show("Plan OK", type="message")

    @render.download_button(filename=lambda: f"deployment_plan_{uuid.uuid4().hex}.geojson")
    def export_plan():
        geojson = build_geojson(deployment_points(), input.start_date())
        yield json.dumps(geojson, indent=2)
    