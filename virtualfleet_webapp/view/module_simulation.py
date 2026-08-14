import asyncio

from shiny import ui, module, reactive
from virtualargofleet import VirtualFleet

from virtualfleet_webapp.logic.utils import section_title, flatten_mission_config

@module.ui
def simulation_ui():
    return ui.TagList(
        section_title(4, "Simulation Parameters", tooltip="TBD"),
        ui.div(
            {"class": "mission-grid"},
            ui.div(ui.input_numeric(id="simulation_time", label=ui.span("Simulation length (days)", style="font-size: 0.90rem;"), value=0, update_on='blur')),
            ui.div(ui.input_numeric(id="time_step", label=ui.span("Time step (minutes)", style="font-size: 0.90rem;"), value=5, update_on='blur')),
            ui.div(ui.input_numeric(id="writing_step", label=ui.span("Writing time step (hours)", style="font-size: 0.90rem;"), value=1, update_on='blur')),
            ui.div(ui.input_text(id="simulation_name", label=ui.span("Simulation name", style="font-size: 0.90rem;"), value="default", update_on='blur')),
        ),
        ui.input_task_button(id="run_simulation", label=ui.HTML('<i class="fa-solid fa-play"></i> Run Simulation'), class_="btn-primary", label_busy="Running..."),
        ui.input_task_button(id="save_simulation", label=ui.HTML('<i class="fa-solid fa-save"></i> Save Simulation'), class_="btn-light", label_busy="Saving..."),
    )

@module.server
def simulation_server(input, output, session, speed_field, deployment_plan, mission_config):

    def _run_blocking(plan, fieldset, mission, duration, step, record, output_file):
        vfleet = VirtualFleet(plan=plan, fieldset=fieldset, mission=mission)
        vfleet.simulate(duration=duration, step=step, record=record, output=True, output_file=output_file, output_folder='./simulations/')
        return vfleet

    @ui.bind_task_button(button_id="run_simulation")
    @reactive.extended_task
    async def run_simulation(plan, fieldset, mission, duration, step, record, output_file):
        return await asyncio.to_thread(_run_blocking, plan, fieldset, mission, duration, step, record, output_file)

    @reactive.effect
    def _():
        if run_simulation.status() == "error":
            try:
                run_simulation.result()
            except Exception as e:
                ui.notification_show(f"Simulation failed: {e}", type="error")

    @reactive.effect
    @reactive.event(input.run_simulation)
    def _():
        fieldset = speed_field()
        if not fieldset:
            ui.notification_show("Upload a variable mapping config file first.", type="error")
            return
        plan = deployment_plan()
        if not plan:
            ui.notification_show("Validate a deployment plan first.", type="error")
            return
        config = mission_config()
        if not config:
            ui.notification_show("Validate a mission configuration first.", type="error")
            return

        run_simulation(
            plan,
            fieldset,
            flatten_mission_config(config),
            input.simulation_time(),
            input.time_step(),
            input.writing_step(),
            input.simulation_name()
        )

    return run_simulation
