"""
Application User Interface
"""

from shiny import ui

app_ui = ui.page_fluid(
    # Style
    ui.head_content(
        ui.tags.link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css",
        ),
        ui.tags.link(
            rel="stylesheet",
            href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css",
        ),
        ui.tags.link(rel="stylesheet", href="styles.css"),
        #ui.tags.style(custom_css),
    ),
    # Busy indicator
    ui.busy_indicators.use(),
    # Navbar layout
    ui.navset_bar(
        title=ui.row(
            ui.column(
                2,
                ui.a(
                    ui.img(
                        src="images/logo-EuroArgo.png",
                        style="height:50px; display:block; pointer-events:none;",
                    ),
                    href="https://www.euro-argo.eu/",
                    target="_blank",
                    style="display:inline-block; cursor:pointer; position:relative;",
                ),
            ),
        ),
    ),
    # Sidebar layout
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

            # Hidden radio group driving which card is "selected"
            ui.div(
                {"class": "mission-radio"},
                ui.input_radio_buttons(
                    "mission_mode",
                    None,
                    choices={"same": "Same", "different": "Different"},
                    selected="same",
                ),
            ),
 
            ui.output_ui("card_same"),
            ui.output_ui("card_different"),
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
                ui.span("Simulation time (unit)", style="font-size: 0.95rem;"),
                ui.input_numeric(
                    id="param_simulation_time", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Time step (unit)", style="font-size: 0.95rem;"),
                ui.input_numeric(
                    id="param_time_step", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.div(
                ui.span("Writing step (unit)", style="font-size: 0.95rem;"),
                ui.input_numeric(
                    id="param_writing_step", label="", value=0, min=0, step=1, update_on='blur', width="100px"
                ).add_class("mb-0"),
                class_="d-flex align-items-center gap-2",
            ),
            ui.input_task_button(id="run_simulation", label=ui.HTML('<i class="fa-solid fa-play"></i> Run Simulation'), class_="btn-primary", label_busy="Running..."),
            ui.input_task_button(id="save_simulation", label=ui.HTML('<i class="fa-solid fa-save"></i> Save Simulation'), class_="btn-light", label_busy="Saving..."),
        # Sidebar layout options
        bg="",
        width=350,
        gap=10 # Vertical spacing in the sidebar
        ),
        # Main panel content
        ui.navset_tab(
            ui.nav_panel(
                "Deployment Map"
            ),
            ui.nav_panel(
                "Simulation Results"
            ),
        ),
    ),
    # use brand theme
    theme=ui.Theme.from_brand(__file__),
)
