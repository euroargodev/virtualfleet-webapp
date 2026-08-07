"""
Server logic
"""

from shiny import reactive, render, ui

def server(input, output, session):

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

        return ui.div(
            {"class": card_class},
            header,
            ui.input_numeric(id="num_floats", label=ui.span("Number of floats", style="font-size: 0.90rem;"), value=0),
            ui.input_date(id="start_date", label=ui.span("Start date", style="font-size: 0.90rem;")),
            ui.input_action_button(
                id="validate_plan", label=ui.HTML('<i class="fa-solid fa-check"></i> Validate plan'),
                style="width: 100%; background: var(--bs-primary); color: white; border: none; margin-top: 8px;",
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
            ui.input_file(id="plan_file", label="", accept=[".json"]),
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
                ui.div(ui.input_numeric(id="cycle_duration", label=ui.span("Cycle length (day)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
                ui.div(ui.input_numeric(id="parking_depth", label=ui.span("Parking depth (m)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
                ui.div(ui.input_numeric(id="profile_depth", label=ui.span("Profile depth (m)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
                ui.div(ui.input_numeric(id="lifespan", label=ui.span("Lifespan (unit)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
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
            ui.input_file(id="mission_config_file", label="", accept=[".csv", ".txt"]),
        )
    