from shiny import ui, module
from shiny_validate import InputValidator
from virtualfleet_webapp.logic.utils import section_title, check_config_file, check_nc_file

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
    iv = InputValidator() # Add InputValidator to validate path to speed field

    iv.add_rule("speed_field_path", check_nc_file)
    iv.add_rule("upload_config_file", check_config_file)
    iv.enable()