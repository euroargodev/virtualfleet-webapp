import re

from playwright.sync_api import Page, expect
from shiny.playwright import controller
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

# Path is relative to this test file.
app = create_app_fixture("../../app.py")


def option_header(page: Page, text: str):
    """Locate a sidebar card's clickable header by its visible text."""
    return page.locator(".option-header", has_text=text)


def notification_text(page: Page):
    return page.locator("#shiny-notification-panel .shiny-notification-content-text")


def test_speed_field_defaults_are_visible(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    controller.InputText(page, "speed_field-speed_field_path").expect_value("./data/cmems_speed_field.nc")
    controller.InputFile(page, "speed_field-upload_config_file").expect.to_be_visible()


def test_option_a_is_selected_by_default(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    expect(page.locator("#deployment_plan-card_a .option-card")).to_have_class(re.compile(r"\bselected\b"))
    expect(page.locator("#deployment_plan-card_b .option-card")).to_have_class(re.compile(r"\bcollapsed\b"))
    controller.InputNumeric(page, "deployment_plan-num_floats").expect_value("0")


def test_clicking_option_b_header_switches_the_active_card(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    option_header(page, "Option B").click()

    expect(page.locator("#deployment_plan-card_a .option-card")).to_have_class(re.compile(r"\bcollapsed\b"))
    expect(page.locator("#deployment_plan-card_b .option-card")).to_have_class(re.compile(r"\bselected\b"))
    controller.InputFile(page, "deployment_plan-plan_file").expect.to_be_visible()

    # Switching back to A restores its inputs.
    option_header(page, "Option A").click()
    expect(page.locator("#deployment_plan-card_a .option-card")).to_have_class(re.compile(r"\bselected\b"))


def test_mission_mode_toggle(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    expect(page.locator("#mission_config-card_same .option-card")).to_have_class(re.compile(r"\bselected\b"))
    expect(page.locator("#mission_config-card_different .option-card")).to_have_class(re.compile(r"\bcollapsed\b"))

    option_header(page, "Different mission per float").click()

    expect(page.locator("#mission_config-card_same .option-card")).to_have_class(re.compile(r"\bcollapsed\b"))
    expect(page.locator("#mission_config-card_different .option-card")).to_have_class(re.compile(r"\bselected\b"))
    controller.InputFile(page, "mission_config-mission_config_file").expect.to_be_visible()


def test_validate_plan_without_any_geometry_shows_an_error(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    controller.InputActionButton(page, "deployment_plan-validate_plan_a").click()

    expect(notification_text(page)).to_contain_text("Place markers, draw a deployment line, or draw a polygon first.")


def test_validate_plan_b_without_a_file_shows_an_error(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)
    option_header(page, "Option B").click()

    controller.InputActionButton(page, "deployment_plan-validate_plan_b").click()

    expect(notification_text(page)).to_contain_text("Upload a .geojson file first.")


def test_show_current_plan_switch_is_visible(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)
    controller.InputSwitch(page, "deployment_plan-show_plan").expect.to_be_visible()


def test_validate_mission_same_shows_confirmation(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    controller.InputActionButton(page, "mission_config-validate_mission_same").click()

    expect(notification_text(page)).to_contain_text("Mission OK")


def test_validate_mission_different_without_a_file_shows_an_error(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)
    option_header(page, "Different mission per float").click()

    controller.InputActionButton(page, "mission_config-validate_mission_different").click()

    expect(notification_text(page)).to_contain_text("Upload a mission config file first.")


def test_simulation_parameters_defaults_are_visible(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    controller.InputNumeric(page, "simulation-simulation_time").expect_value("1")
    controller.InputNumeric(page, "simulation-time_step").expect_value("5")
    controller.InputNumeric(page, "simulation-writing_step").expect_value("1")
    controller.InputText(page, "simulation-simulation_name").expect_value("default")
    expect(controller.InputTaskButton(page, "simulation-run_simulation").loc).to_be_visible()

    # Before any successful run, Save is a disabled placeholder (not the real
    # download link) so there's nothing clickable that could produce a broken
    # download.
    save_button = controller.InputActionButton(page, "simulation-save_simulation_disabled")
    save_button.expect.to_be_visible()
    save_button.expect.to_be_disabled()


def test_run_simulation_without_a_config_file_shows_an_error(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    controller.InputTaskButton(page, "simulation-run_simulation").click()

    expect(notification_text(page)).to_contain_text("Upload a variable mapping config file first.")
