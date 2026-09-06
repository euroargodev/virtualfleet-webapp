import asyncio

import xarray as xr
from shiny import module, reactive, ui
from shiny_validate import InputValidator
from virtualargofleet import Velocity

from virtualfleet_webapp.logic.utils import check_config_file, get_velocity_extent, read_config_file, section_title


@module.ui
def speed_field_ui():
    return ui.TagList(
        section_title(
            1,
            "Velocity Field",
            tooltip="Path to the velocity field used by VirtualFleet to simulate float trajectories.",
        ),
        ui.input_file(id="speed_field_path", label="", placeholder="Import velocity field data", accept=[".nc"], multiple=True),
        ui.input_file(id="upload_config_file", label="", placeholder="Import variable mapping file", accept=[".json"]),
        ui.hr({"class": "section-divider"}),
    )


@module.server
def speed_field_server(input, output, session):

    # Add InputValidator to validate path to speed field
    iv = InputValidator()
    iv.add_rule("upload_config_file", check_config_file)
    iv.enable()

    # Variable mapping
    var_mapping = reactive.value(None)

    @reactive.effect
    @reactive.event(input.upload_config_file)
    def _():
        try:
            config = read_config_file(input.upload_config_file()[0]["datapath"])
        except Exception: # Technically, should not happen because of check_config_file() occuring before.
            ui.notification_show("Could not read the config file.", type="error")
            return
        var_mapping.set(config)

    def _build_velocity_field(paths, mapping): # Internal use, should not be used elsewhere
        src = xr.combine_by_coords([xr.open_dataset(p) for p in paths])
        return Velocity(
            model="custom",
            src=src,
            variables=mapping["variables"],
            dimensions=mapping["dimensions"],
        )

    # Opening a NetCDF can take a while (e.g. size) so better 
    # use an async process (if app deployed on server at some point)  
    @reactive.extended_task
    async def _load_velocity_field(paths, mapping):
        return await asyncio.to_thread(_build_velocity_field, paths, mapping)

    @reactive.effect
    def _():
        mapping = var_mapping()
        if mapping is None: # Check if mapping exists
            return
        files = input.speed_field_path()
        if not files:  # No file uploaded yet
            return
        paths = [f["datapath"] for f in files]
        _load_velocity_field(paths, mapping)

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

    @reactive.calc
    def velocity_field_extent():
        v = velocity_field()
        if v is None:
            return None
        return get_velocity_extent(v)

    return velocity_field, velocity_field_extent
