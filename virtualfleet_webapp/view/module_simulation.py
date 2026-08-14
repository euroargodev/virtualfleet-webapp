import asyncio
import contextvars
import io
import json
import os
import zipfile

from shiny import ui, module, reactive, render
from tqdm import tqdm as _tqdm_cls
from virtualargofleet import VirtualFleet

from virtualfleet_webapp.logic.utils import build_deployment_plan_geojson, flatten_mission_config, section_title

SIMULATIONS_FOLDER = "./simulations/"

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
        ui.output_ui("simulation_progress"),
        ui.output_ui("save_simulation_slot"),
    )


@module.server
def simulation_server(input, output, session, speed_field, deployment_plan, mission_config):

    # One mutable [n, total] slot per session, reused across runs.
    progress_slot = [0, None]

    def _run_blocking(plan, fieldset, mission, duration, step, record, output_file):
        vfleet = VirtualFleet(plan=plan, fieldset=fieldset, mission=mission)
        vfleet.simulate(duration=duration, step=step, record=record, output=True, output_file=output_file, output_folder=SIMULATIONS_FOLDER)
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

    # The actual download link only exists in the DOM once a run has
    # succeeded — a disabled placeholder button sits there otherwise, so
    # there's no clickable link that could kick off a broken/empty download.
    @render.ui
    def save_simulation_slot():
        if run_simulation.status() != "success":
            return ui.input_action_button(
                id="save_simulation_disabled",
                label=ui.HTML('<i class="fa-solid fa-save"></i> Save Simulation'),
                class_="btn-light",
                disabled=True,
            )
        return ui.download_button(id="save_simulation", label=ui.HTML('<i class="fa-solid fa-save"></i> Save Simulation'), class_="btn-light")

    @render.download_button(filename=lambda: f"{input.simulation_name()}.zip")
    def save_simulation():
        if run_simulation.status() != "success":
            ui.notification_show("Run a simulation successfully before saving.", type="error")
            raise Exception("No completed simulation to save yet.")

        name = input.simulation_name()
        zarr_name = name if name.endswith(".zarr") else f"{name}.zarr"
        zarr_path = os.path.join(SIMULATIONS_FOLDER, zarr_name)
        if not os.path.isdir(zarr_path):
            ui.notification_show(f"Could not find simulation output at {zarr_path}.", type="error")
            raise Exception(f"Missing zarr output: {zarr_path}")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Simulation output (zarr store is a directory of many small files).
            for root, _dirs, files in os.walk(zarr_path):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    arcname = os.path.join(zarr_name, os.path.relpath(full_path, zarr_path))
                    zf.write(full_path, arcname)

            # Deployment plan, as GeoJSON.
            plan = deployment_plan()
            if plan:
                zf.writestr("deployment_plan.geojson", json.dumps(build_deployment_plan_geojson(plan), indent=2))

            # Mission configuration(s).
            config = mission_config()
            if config:
                zf.writestr("mission_config.json", json.dumps(config, indent=2))

            # Variable mapping, read back off the built velocity field.
            fieldset = speed_field()
            if fieldset:
                mapping = {"variables": fieldset.var, "dimensions": fieldset.dim}
                zf.writestr("variable_mapping.json", json.dumps(mapping, indent=2))

        yield buffer.getvalue()

    return run_simulation