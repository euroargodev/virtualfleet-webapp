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


def test_option_a_is_selected_by_default(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    expect(page.locator("#card_a .option-card")).to_have_class(re.compile(r"\bselected\b"))
    expect(page.locator("#card_b .option-card")).to_have_class(re.compile(r"\bcollapsed\b"))
    controller.InputNumeric(page, "num_floats").expect_value("0")


def test_clicking_option_b_header_switches_the_active_card(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    option_header(page, "Option B").click()

    expect(page.locator("#card_a .option-card")).to_have_class(re.compile(r"\bcollapsed\b"))
    expect(page.locator("#card_b .option-card")).to_have_class(re.compile(r"\bselected\b"))
    controller.InputFile(page, "plan_file").expect.to_be_visible()

    # Switching back to A restores its inputs.
    option_header(page, "Option A").click()
    expect(page.locator("#card_a .option-card")).to_have_class(re.compile(r"\bselected\b"))


def test_mission_mode_toggle(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    expect(page.locator("#card_same .option-card")).to_have_class(re.compile(r"\bselected\b"))
    expect(page.locator("#card_different .option-card")).to_have_class(re.compile(r"\bcollapsed\b"))

    option_header(page, "Different mission per float").click()

    expect(page.locator("#card_same .option-card")).to_have_class(re.compile(r"\bcollapsed\b"))
    expect(page.locator("#card_different .option-card")).to_have_class(re.compile(r"\bselected\b"))
    controller.InputFile(page, "mission_config_file").expect.to_be_visible()


def test_validate_plan_without_any_geometry_shows_an_error(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    controller.InputActionButton(page, "validate_plan").click()

    notification = page.locator("#shiny-notification-panel .shiny-notification-content-text")
    expect(notification).to_contain_text(
        "Place markers, draw a deployment line, or draw a polygon first."
    )
