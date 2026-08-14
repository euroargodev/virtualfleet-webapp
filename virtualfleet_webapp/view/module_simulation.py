import asyncio
import contextvars

from shiny import ui, module, reactive, render
from tqdm import tqdm as _tqdm_cls
from virtualargofleet import VirtualFleet

from virtualfleet_webapp.logic.utils import section_title, flatten_mission_config

# ContextVar holding a mutable [n, total] progress slot for the current run.
# asyncio.to_thread copies the calling context into the worker thread, so this
# "just works" per-session/per-run without any thread-id bookkeeping.
_current_progress = contextvars.ContextVar("current_progress", default=None)

if not getattr(_tqdm_cls, "_progress_tracking_patched", False):
    _original_tqdm_update = _tqdm_cls.update

    def _tracked_tqdm_update(self, n=1):
        _original_tqdm_update(self, n)
        slot = _current_progress.get()
        if slot is not None:
            slot[0] = self.n
            slot[1] = self.total

    _tqdm_cls.update = _tracked_tqdm_update
    _tqdm_cls._progress_tracking_patched = True


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
        ui.output_ui("simulation_progress"),
    )


@module.server
def simulation_server(input, output, session, speed_field, deployment_plan, mission_config):

    # One mutable [n, total] slot per session, reused across runs.
    progress_slot = [0, None]

    def _run_blocking(plan, fieldset, mission, duration, step, record, output_file):
        vfleet = VirtualFleet(plan=plan, fieldset=fieldset, mission=mission)
        vfleet.simulate(duration=duration, step=step, record=record, output=True, output_file=output_file, output_folder='./simulations/')
        return vfleet

    @ui.bind_task_button(button_id="run_simulation")
    @reactive.extended_task
    async def run_simulation(plan, fieldset, mission, duration, step, record, output_file):
        progress_slot[0], progress_slot[1] = 0, None
        _current_progress.set(progress_slot)
        return await asyncio.to_thread(_run_blocking, plan, fieldset, mission, duration, step, record, output_file)

    @reactive.effect
    def _():
        if run_simulation.status() == "error":
            try:
                run_simulation.result()
            except Exception as e:
                ui.notification_show(f"Simulation failed: {e}", type="error")

    @render.ui
    def simulation_progress():
        if run_simulation.status() != "running":
            return None
        reactive.invalidate_later(1)
        n, total = progress_slot
        pct = (n / total * 100) if total else 0
        return ui.div(
            {"class": "progress", "style": "height: 1.25rem;"},
            ui.div(
                {
                    "class": "progress-bar",
                    "role": "progressbar",
                    "style": f"width: {pct:.0f}%;",
                    "aria-valuenow": f"{pct:.0f}",
                    "aria-valuemin": "0",
                    "aria-valuemax": "100",
                },
                f"{pct:.0f}%",
            ),
        )

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