"""
Server logic
"""

import json
import uuid
import numpy as np

from shiny import reactive, render, ui
from shiny_validate import InputValidator

# import custom modules
from virtualfleet_webapp.logic.utils import build_geojson, resolve_deployment_points, read_deployment_plan, build_mission_config, read_mission_config, check_nc_file, check_config_file
from virtualfleet_webapp.view.module_map import map_server

def server(input, output, session):

    ###########################
    # General reactive values #
    ###########################
    iv = InputValidator() # Add InputValidator to validate path to speed field

    # Reactive state for the deployment plan, shared across the sidebar (Part 1)
    # and the map/export logic (Part 3).
    deployment_points = reactive.Value([])  # Option A: drawn/placed on the map
    uploaded_plan = reactive.Value(None)    # Option B: parsed from an uploaded file
    last_validated_option = reactive.Value(None)  # "A" or "B", whichever was last validated

    mission_config = reactive.Value(None)          # "same": built from the mission inputs
    uploaded_mission_config = reactive.Value(None) # "different": parsed from an uploaded file
    last_validated_mission_option = reactive.Value(None)  # "same" or "different"

    ########################################################
    # Part 1 - Speed field and config file for the sidebar #
    ########################################################
    iv.add_rule("speed_field_path", check_nc_file)
    iv.add_rule("upload_config_file", check_config_file)
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
                id="validate_plan_a", label=ui.HTML('<i class="fa-solid fa-check"></i> Validate plan'),
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
            ui.input_action_button(
                id="validate_plan_b", label=ui.HTML('<i class="fa-solid fa-check"></i> Validate plan'),
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
            ui.input_action_button(
                id="validate_mission_same", label=ui.HTML('<i class="fa-solid fa-check"></i> Validate mission'),
                style="width: 100%; background: var(--bs-primary); color: white; border: none; margin-top: 8px;",
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
            ui.input_file(id="mission_config_file", label="", accept=[".json"]),
            ui.input_action_button(
                id="validate_mission_different", label=ui.HTML('<i class="fa-solid fa-check"></i> Validate mission'),
                style="width: 100%; background: var(--bs-primary); color: white; border: none; margin-top: 8px;",
            ),
        )

    # Reflects whichever mission source was last validated, regardless of
    # which card is currently displayed in the sidebar.
    @reactive.calc
    def last_validated_mission_config():
        option = last_validated_mission_option()

        if option == "same":
            return mission_config()
        if option == "different":
            return uploaded_mission_config()

        return None

    @reactive.effect
    @reactive.event(input.validate_mission_same)
    def _():
        config = build_mission_config(
            cycle_duration=input.cycle_duration(),
            life_expectancy=input.lifespan(),
            parking_depth=input.parking_depth(),
            profile_depth=input.profile_depth(),
            vertical_speed=input.vertical_speed(),
        )
        mission_config.set(config)
        last_validated_mission_option.set("same")
        ui.notification_show("Mission OK", type="message")

    @reactive.effect
    @reactive.event(input.validate_mission_different)
    def _():
        file = input.mission_config_file()
        if not file:
            ui.notification_show("Upload a mission config file first.", type="error")
            return
        try:
            configs = read_mission_config(file[0]["datapath"])
        except Exception:
            ui.notification_show("Could not read the mission config file.", type="error")
            return
        uploaded_mission_config.set(configs)
        last_validated_mission_option.set("different")
        ui.notification_show("Mission OK", type="message")

    ###############################################
    # Map module part (see modules/module_map.py) #
    ###############################################
    point_markers, line_markers, shape_markers = map_server("map", plan=last_validated_plan, show=input.show_plan)

    @reactive.effect
    @reactive.event(input.validate_plan_a)
    def _():
        try:
            points = resolve_deployment_points(
                point_markers(), line_markers(), shape_markers(), input.num_floats()
            )
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
    