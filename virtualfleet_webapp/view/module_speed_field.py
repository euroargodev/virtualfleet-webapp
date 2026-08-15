import asyncio

from shiny import ui, module, reactive
from shiny_validate import InputValidator
from virtualfleet_webapp.logic.utils import section_title, check_config_file, check_nc_file, read_config_file
from virtualargofleet import Velocity

@module.ui
def speed_field_ui():
    return ui.TagList(
        section_title(
            1, "Speed Field",
            tooltip="Path to the velocity field used by VirtualFleet to simulate float trajectories.",
        ),
        ui.input_text(id="speed_field_path", label="", value="./data/cmems_speed_field.nc", placeholder="Path to speed field"),
        ui.input_file(id="upload_config_file", label="", placeholder="Import variable mapping file", accept=[".json"]),
        ui.hr({"class": "section-divider"})
    )


@module.server
def speed_field_server(input, output, session):

    # Add InputValidator to validate path to speed field
    iv = InputValidator()
    iv.add_rule("speed_field_path", check_nc_file)
    iv.add_rule("upload_config_file", check_config_file)
    iv.enable()

    # variable mapping
    var_mapping = reactive.value(None)

    @reactive.effect
    @reactive.event(input.upload_config_file)
    def _():
        try:
            config = read_config_file(input.upload_config_file()[0]["datapath"])
        except Exception:
            ui.notification_show("Could not read the config file.", type="error")
            return
        var_mapping.set(config)

    def _build_velocity_field(path, mapping):
        return Velocity(
            model='custom',
            src={"U": path, "V": path},
            variables=mapping["variables"],
            dimensions=mapping["dimensions"],
        )

    # Opening/indexing the velocity NetCDF file(s) can take a while (large or
    # remote files) and must not block the single-threaded reactive flush
    # shared by every connected session, so it's run in a worker thread.
    @reactive.extended_task
    async def _load_velocity_field(path, mapping):
        return await asyncio.to_thread(_build_velocity_field, path, mapping)

    @reactive.effect
    def _():
        mapping = var_mapping()
        if mapping is None:
            return
        path = input.speed_field_path()
        if check_nc_file(path) is not None:
            return
        _load_velocity_field(path, mapping)

    @reactive.effect
    def _():
        if _load_velocity_field.status() == "error":
            try:
                _load_velocity_field.result()
            except Exception as e:
                ui.notification_show(f"Could not load speed field: {e}", type="error")

    @reactive.calc
    def velocity_field():
        if _load_velocity_field.status() != "success":
            return None
        return _load_velocity_field.result()

    return velocity_field