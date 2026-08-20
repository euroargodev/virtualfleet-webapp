import asyncio

import matplotlib as mpl
import matplotlib.colors as mcolors
import numpy as np
import xarray as xr
from ipyleaflet import Map, Polyline, ScaleControl, basemaps
from shiny import module, reactive, ui
from shinywidgets import output_widget, render_widget


@module.ui
def simulated_traj_ui():
    return ui.TagList(
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
            label_busy="Reading...",
            width="300px",
        ),
        ui.card(output_widget("map_traj")),
    )


@module.server
def simulated_traj_server(input, output, session):

    #######
    # MAP #
    #######
    m = Map(
        center=(0, 0),
        zoom=2,
        basemap=basemaps.Esri.WorldImagery,
        scroll_wheel_zoom=True,
    )

    # Add options
    m.add(ScaleControl(position="bottomleft"))

    trajectory_layers = []

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

    # Plot one trajectory (polyline) per float, replacing whatever was drawn
    # for a previously read file.
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

        for layer in trajectory_layers: # For previous plotted trajectories
            m.remove(layer)
        trajectory_layers.clear()

        ds = read_zarr_file.result()
        if "lat" not in ds or "lon" not in ds:
            return

        lats = np.atleast_2d(ds["lat"].values) # To make sure it's 2D even if only 1 float
        lons = np.atleast_2d(ds["lon"].values)
        if lats.size == 0:
            return

        n_floats = lats.shape[0]
        cmap = mpl.colormaps["viridis"].resampled(n_floats) if n_floats > 1 else None
        colors = [mcolors.to_hex(cmap(i)) for i in range(n_floats)] if cmap else ["#2c7fb8"]

        for color, lat_row, lon_row in zip(colors, lats, lons, strict=True):
            path = list(zip(lat_row.tolist(), lon_row.tolist()))
            line = Polyline(locations=path, color=color, weight=2, fill=False)
            m.add(line)
            trajectory_layers.append(line)

    return read_zarr_file
