from shiny import ui

def section_title(number, text, tooltip=None):
    """Numbered circle badge + header used at the top of each sidebar section."""
    children = [
        ui.span({"class": "section-badge"}, str(number)),
        ui.h5(text, style="margin: 0;"),
    ]
    if tooltip:
        children.append(ui.HTML('<i class="fa-regular fa-circle-question"></i>'))

    heading = ui.div({"class": "section-title"}, *children)

    if tooltip:
        return ui.tooltip(heading, tooltip, placement="right")
    return heading