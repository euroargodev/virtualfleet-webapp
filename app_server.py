"""
Server logic
"""

from shiny import reactive, render, ui

def server(input, output, session):
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
            ui.input_numeric(id="num_floats", label="Number of floats", value=0),
            ui.input_date(id="start_date", label="Start date"),
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