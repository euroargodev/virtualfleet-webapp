from shiny import ui, module, reactive, render
from virtualfleet_webapp.logic.utils import section_title, build_mission_config, read_mission_config

@module.ui
def mission_config_ui():
    return ui.TagList(
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
        ui.hr({"class": "section-divider"})
    )


@module.server
def mission_config_server(input, output, session):

    mission_config = reactive.Value(None)          # "same": built from the mission inputs
    uploaded_mission_config = reactive.Value(None) # "different": parsed from an uploaded file
    last_validated_mission_option = reactive.Value(None)  # "same" or "different"

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