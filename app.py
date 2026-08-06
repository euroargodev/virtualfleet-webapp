"""
Entry point for the application. Run with: uv run shiny run app.py
"""

import os

from shiny import App

from app_server import server
from app_ui import app_ui

app = App(
    app_ui,
    server,
    static_assets=os.path.join(os.path.dirname(__file__), "www"),
)
