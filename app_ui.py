"""
Application User Interface
"""

from shiny import ui

# import custom modules
from virtualfleet_webapp.view.module_speed_field import speed_field_ui
from virtualfleet_webapp.view.module_deployment_plan import deployment_plan_ui, deployment_plan_map_ui
from virtualfleet_webapp.view.module_mission import mission_config_ui
from virtualfleet_webapp.view.module_simulation import simulation_ui

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
            speed_field_ui("speed_field"),
            # Part 2 - Deployment Plan
            deployment_plan_ui("deployment_plan"),
            # Part 3 - Mission Parameters
            mission_config_ui("mission_config"),
            # Part 4 - Simulation Parameters
            simulation_ui("simulation"),
            # Sidebar layout options
            bg="",
            width=400,
            gap=10 # Vertical spacing in the sidebar
        ),
        # Main panel content
        ui.navset_card_underline(
            ui.nav_panel(
                "Deployment Map",
                deployment_plan_map_ui("deployment_plan"),
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
