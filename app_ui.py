"""
Application User Interface
"""

from shiny import ui
from virtualfleet_webapp.logic.utils import section_title
# import custom modules
from virtualfleet_webapp.view.module_map import map_ui

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
        navbar_options=ui.navbar_options(bg="var(--bs-primary)", theme="dark"),
        title=ui.row(
            ui.column(
                4,
                ui.div(
                    ui.a(
                        ui.img(
                            src="images/logo-EuroArgo.png",
                            style="height:60px; display:block; pointer-events:none;",
                        ),
                        href="https://www.euro-argo.eu/",
                        target="_blank",
                        style="display:inline-block; cursor:pointer; position:relative;",
                    ),
                    ui.span("VirtualFleet", style="font-weight: 700; font-size: 1.2rem;"),
                    style="display: flex; align-items: center; gap: 12px;",
                ),
            ),
        ),
    ),
    # Sidebar layout
    ui.layout_sidebar(
        ui.sidebar(
            # Part 1 - Speed Field
            section_title(
                1, "Speed Field",
                tooltip="Path to the velocity field used by VirtualFleet to simulate float trajectories.",
            ),
            ui.input_text(id="speed_field_path", label="", value="./data/cmems_speed_field.nc", placeholder="Path to speed field"),
            ui.input_file(id="upload_config_file", label="", placeholder="Import variable mapping file"),
            ui.hr({"class": "section-divider"}),

            # Part 2 - Deployment Plan
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
            ui.hr({"class": "section-divider"}),

            # Part 3 - Mission Parameters
            section_title(3, "Mission Parameters", tooltip="TBD"),
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
            ui.hr({"class": "section-divider"}),

            # Part 4 - Simulation Parameters
            section_title(4, "Simulation Parameters", tooltip="TBD"),

            ui.div(
                {"class": "mission-grid"},
                ui.div(ui.input_numeric(id="simulation_time", label=ui.span("Simulation length (days)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
                ui.div(ui.input_numeric(id="time_step", label=ui.span("Time step (minutes)", style="font-size: 0.90rem;"), value=5, update_on='blur')),
                ui.div(
                    {"class": "full-row"},
                    ui.input_numeric(id="writing_step", label=ui.span("Output writing time step (hours)", style="font-size: 0.90rem;"), value=1, update_on='blur'),
                ),
            ),
            ui.input_task_button(id="run_simulation", label=ui.HTML('<i class="fa-solid fa-play"></i> Run Simulation'), class_="btn-primary", label_busy="Running..."),
            ui.input_task_button(id="save_simulation", label=ui.HTML('<i class="fa-solid fa-save"></i> Save Simulation'), class_="btn-light", label_busy="Saving..."),
        # Sidebar layout options
        bg="",
        width=400,
        gap=10 # Vertical spacing in the sidebar
        ),
        # Main panel content
        ui.navset_card_underline(
            ui.nav_panel(
                "Deployment Map",
                map_ui("map"),
            ),
            ui.nav_panel(
                "Simulation Results"
            ),
        ),
    ),
    # Footer
    ui.div(
        ui.div(
            ui.div(
                ui.a(
                    ui.HTML('<i class="fa-brands fa-github"></i> GitHub'),
                    href="https://github.com/euroargodev",
                    target="_blank",
                    class_="footer-link",
                    style="font-weight: 700; margin-right: 20px;",
                ),
                ui.a(
                    ui.HTML('<i class="fa-solid fa-envelope"></i> Contact'),
                    href="mailto:florian@fricour.com",
                    class_="footer-link",
                    style="font-weight: 700;",
                ),
            ),
            ui.div(
                "Built with ",
                ui.a(
                    "Shiny for Python",
                    href="https://shiny.posit.co/py/",
                    target="_blank",
                    class_="footer-link",
                    style="font-weight: 700;",
                ),
            ),
            style="display: flex; align-items: center; justify-content: space-between; padding: 15px; font-size: 0.85rem; color: var(--bs-secondary-color);",
        ),
        style="border-top: 1px solid var(--bs-secondary-colour); margin-top: 20px;",
    ),
    # use brand theme
    theme=ui.Theme.from_brand(__file__),
)
