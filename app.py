"""
Entry point for the application. Run with: uv run shiny run app.py
"""

from pathlib import Path

from shiny import App

from virtualfleet_webapp.app_server import server
from virtualfleet_webapp.app_ui import app_ui

app = App(
    app_ui,
    server,
    static_assets=Path(__file__).parent / "www",
)
