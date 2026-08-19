"""
Entry point for the application. Run with: uv run shiny run app.py
"""

from app_server import server
from app_ui import app_ui
from pathlib import Path
from shiny import App

app = App(
    app_ui,
    server,
    static_assets=Path(__file__).parent / "www",
)
