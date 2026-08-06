"""
Application User Interface
"""

from shiny import ui

app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css",
        ),
        ui.tags.link(rel="stylesheet", href="styles.css"),
    ),
    ui.busy_indicators.use(),
    ui.layout_sidebar(
        ui.sidebar(
            # Part 1 - Speed Field
            ui.tooltip(
                ui.span(
                    ui.HTML("<strong>1. Speed Field </strong>"),
                    ui.HTML('<i class="bi bi-question-circle-fill"></i>'),
                ),
                ui.HTML(
                    "TBD"
                ),
                placement="right",
            ),
            ui.input_text(id="speed_field_path", label="", value="", placeholder="Path to the speed field"),
            ui.input_file(id="upload_config_file", label="", placeholder="Import config file"),
            ui.HTML("<br>"),

            # Part 2 - Deployment Plan
            ui.tooltip(
                ui.span(
                    ui.HTML("<strong>2. Deployment Plan </strong>"),
                    ui.HTML('<i class="bi bi-question-circle-fill"></i>'),
                ),
                ui.HTML(
                    "Create your deployment plan: build it on the map, set a start date, then validate it for simulation."
                ),
                placement="right",
            ),
            ui.HTML("Create the plan with the map"),
            ui.div(
                ui.span("Number of floats"),
                ui.input_numeric(
                    id="param_float_number", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Start date"),
                ui.input_date(id="deployment_start_date", label="", width="150px").add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.input_action_button(id="deployment_validate", label="Validate plan", class_="btn-primary"),
            ui.HTML("Or, import your pre-built plan"),
            ui.input_file(id="upload_deployment_plan", label="", placeholder="Deployment plan file"),
            ui.HTML("<br>"),

            # Part 3 - Mission Parameters
            ui.tooltip(
                ui.span(
                    ui.HTML("<strong>3. Mission Parameters </strong>"),
                    ui.HTML('<i class="bi bi-question-circle-fill"></i>'),
                ),
                ui.HTML(
                    "TBD"
                ),
                placement="right",
            ),
            ui.div(
                ui.span("Cycle duration (unit)"),
                ui.input_numeric(
                    id="param_cycle_duration", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Parking depth (m)"),
                ui.input_numeric(
                    id="param_parking_depth", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Profile depth (m)"),
                ui.input_numeric(
                    id="param_profile_depth", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Lifespan (unit)"),
                ui.input_numeric(
                    id="param_lifespan", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Vertical speed (m/s)"),
                ui.input_numeric(
                    id="param_vertical_speed", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.input_file(id="upload_mission_config_file", label="", placeholder="Mission config file"),
            ui.HTML("<br>"),

            # Part 4 - Simulation Parameters
            ui.tooltip(
                ui.span(
                    ui.HTML("<strong>4. Simulation Parameters </strong>"),
                    ui.HTML('<i class="bi bi-question-circle-fill"></i>'),
                ),
                ui.HTML(
                    "TBD"
                ),
                placement="right",
            ),
            ui.div(
                ui.span("Simulation time (unit)"),
                ui.input_numeric(
                    id="param_simulation_time", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Time step (unit)"),
                ui.input_numeric(
                    id="param_time_step", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Writing step (unit)"),
                ui.input_numeric(
                    id="param_writing_step", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.input_task_button(id="run_simulation", label="Run Simulation", class_="btn-primary", label_busy="Running..."),
            ui.input_task_button(id="save_simulation", label="Save Simulation", class_="btn-light", label_busy="Saving..."),
        bg="",
        width=350,
        gap=10 # Vertical spacing in the sidebar
        ),
    ),
    # use brand theme
    theme=ui.Theme.from_brand(__file__),
)
