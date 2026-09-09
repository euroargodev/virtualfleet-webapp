import asyncio
import tempfile

import numpy as np
import xarray as xr
from ipyleaflet import (
    basemaps,
    basemap_to_tiles,
    CircleMarker, 
    LayersControl,
    Map,
    Polyline, 
    ScaleControl
)
from ipywidgets import HTML
from shiny import module, reactive, ui
from shinywidgets import output_widget, render_widget
from virtualargofleet.utilities import simu2csv

from virtualfleet_webapp.logic.utils import read_index_prof


@module.ui
def simulated_traj_ui():
    # Sidebar layout
    return ui.layout_sidebar(
        ui.sidebar(
            ui.input_text(
                id="simulated_traj_path",
                label="Path to simulation output",
                value="./simulations/default.zarr",
                placeholder="Path to simulation results",
            ),
            ui.input_task_button(
                id="read_zarr_file",
                label=ui.HTML("Read zarr file"),
                class_="btn-primary",
                label_busy="Reading..."
            ),
            gap=10,  # Vertical spacing in the sidebar
        ),
        # Main panel
        ui.card(
            output_widget("map_traj"),
            max_height="80vh", # 80% of the viewport height
        )
    )


@module.server
def simulated_traj_server(input, output, session):

    #######
    # MAP #
    #######
    # Allow the user to choose between different basemaps
    # Also check https://github.com/jupyter-widgets/ipyleaflet/issues/970
    esri_world_imagery = basemap_to_tiles(basemaps.Esri.WorldImagery)
    esri_world_imagery.base = True
    
    openstreetmap = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
    openstreetmap.base = True

    opentopomap = basemap_to_tiles(basemaps.OpenTopoMap)
    opentopomap.base = True

    m = Map(
        center=(0, 0),
        zoom=3,
        layers=[openstreetmap, opentopomap, esri_world_imagery],
        scroll_wheel_zoom=True,
    )

    m.add_control(LayersControl(position="topright"))

    # Add options
    m.add(ScaleControl(position="bottomleft"))

    deployment_markers = [] # Markers for the floats' initial positions
    selected_profile_layers = [] # Trajectory currently shown on click

    @output
    @render_widget
    def map_traj():
        return m

    ###################
    # Read .zarr file #
    ###################
    def _read_zarr_file(file):
        return xr.open_zarr(file)

    @ui.bind_task_button(button_id="read_zarr_file")
    @reactive.extended_task
    async def read_zarr_file(file):
        return await asyncio.to_thread(_read_zarr_file, file)

    @reactive.effect
    @reactive.event(input.read_zarr_file)
    def _():
        read_zarr_file(input.simulated_traj_path())

    ######################
    # Read index profile #
    ######################
    def _read_index_data(zarr_path):
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_file = simu2csv(zarr_path, index_file=f"{tmp_dir}/index.txt")
            return read_index_prof(index_file)

    @reactive.extended_task
    async def read_index_data(zarr_path):
        return await asyncio.to_thread(_read_index_data, zarr_path)

    @reactive.effect
    def _():
        # No need to read the index data if the zarr file was not successiully loaded
        if read_zarr_file.status() != "success":
            return
        read_index_data(input.simulated_traj_path())

    @reactive.effect
    def _():
        if read_index_data.status() == "error":
            try:
                read_index_data.result()
            except Exception as e:
                ui.notification_show(f"Could not read index data: {e}", type="error")

    @reactive.calc
    def index_data():
        if read_index_data.status() != "success":
            return None
        return read_index_data.result()
    
    #@reactive.effect
    #def _():
    #    print(read_index_data.result())

    def _show_trajectory(float_index, lat_init, lon_init):
        """
        Returns a function that shows the trajectory of the float with the given index
        when called. The trajectory is built from the profile index data.
        """
        def _on_click(**kwargs): # need to accept **kwargs because of ipyleaflet's on_click 
            for layer in selected_profile_layers:
                m.remove(layer)
            selected_profile_layers.clear() # clear previous trajectory

            df = index_data() # read index data from the reactive value
            if df is None:
                return

            unique_wmos = sorted(df["wmo"].unique()) # Get unique WMO numbers

            profile = df[df["wmo"] == unique_wmos[float_index]].sort_values("cycle_number")
            if profile.empty:
                return

            trajectory = list(zip(profile["latitude"], profile["longitude"], strict=True))
            trajectory.insert(0, (lat_init, lon_init)) # Add initial position at the beginning
            line = Polyline(locations=trajectory, color="#2c7fb8", weight=2, fill=False)
            m.add(line)
            selected_profile_layers.append(line)

            for row in profile.itertuples(): # Better than iterrows() here (simpler acess to fields)
                popup = HTML(
                    value=(
                        f"<b>Float</b> {row.wmo}<br>"
                        f"<b>Cycle</b> {row.cycle_number}<br>"
                        f"<b>Datetime</b> {row.date}<br>"
                        f"<b>Latitude</b> {row.latitude:.3f}<br>"
                        f"<b>Longitude</b> {row.longitude:.3f}"
                    )
                )
                point = CircleMarker(
                    location=(row.latitude, row.longitude),
                    radius=5,
                    color="#2c7fb8",
                    fill_color="#2c7fb8",
                    fill_opacity=1,
                    weight=1,
                    popup=popup,
                )
                m.add(point)
                selected_profile_layers.append(point)

        return _on_click

    # Plot each float's initial (deployment) position, replacing whatever was
    # drawn for a previously read file. Click a marker to reveal its
    # full trajectory, built from the profile index data.
    @reactive.effect
    def _():
        status = read_zarr_file.status()

        if status == "error":
            try:
                read_zarr_file.result()
            except Exception as e:
                ui.notification_show(f"Could not read zarr file: {e}", type="error")
            return
        if status != "success":
            return

        for marker in deployment_markers: # For previous markers/trajectory
            m.remove(marker)
        deployment_markers.clear()
        for layer in selected_profile_layers:
            m.remove(layer)
        selected_profile_layers.clear()

        ds = read_zarr_file.result()
        if "lat" not in ds or "lon" not in ds:
            return

        lats = np.atleast_2d(ds["lat"].values) # To make sure it's 2D even if only 1 float
        lons = np.atleast_2d(ds["lon"].values)
        if lats.size == 0:
            return

        for i, (lat_row, lon_row) in enumerate(zip(lats, lons, strict=True)):
            marker = CircleMarker(
                location=(float(lat_row[0]), float(lon_row[0])),
                draggable=False,
                radius=5,
                color="#2c7fb8",
                fill_color="#2c7fb8",
                fill_opacity=1,
                weight=1,
                #popup=HTML(value=f"<b>Float {i}</b><br>")
            )
            marker.on_click(_show_trajectory(i, float(lat_row[0]), float(lon_row[0])))
            m.add(marker)
            deployment_markers.append(marker)

    return read_zarr_file
