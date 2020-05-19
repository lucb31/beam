import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from matplotlib import pyplot as plt
import os

from python.ftm.analyze_events import get_refuel_events_from_events_csv, get_total_walking_distances_from_events_csv, \
    get_parking_events_from_events_csv, get_all_events_from_events_csv, df_columns_to_numeric
from python.ftm.util import get_run_dir, get_latest_run, get_iteration_dir, get_last_iteration, range_inclusive

####### CONFIG
baseDir = "/home/lucas/IdeaProjects/beam/output/munich-simple/"
baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = get_latest_run(baseDir)
latest_run = "munich-simple__500agents_72h_30iters__2020-05-06_15-21-00"
latest_run = "munich-simple_24h_DEBUG_replanning__2020-05-12_11-03-13"
path_to_taz_parking = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-parking.csv"
run_dir = get_run_dir(baseDir, latest_run)
last_iteration = 8
max_hour = 24
step_size = 1
compare_iterations = False
plot_charger_util = True
plot_number_of_charging_vehicles = True
plot_activity_types = False
ytitle = "Transferred energy in kwh"
y_min = 999
y_max = 0
###########


def plot_charging_vehicles(iteration, row, col, figure, y_min, y_max):
    # Setup directory
    working_dir = get_iteration_dir(run_dir, iteration)
    print("-------------- ITERATION", iteration, "--------------------")
    print("Working on path: ", working_dir)

    if os.path.exists(working_dir + "chargingNumberVehicles.csv"):
        plot_data = pd.read_csv(working_dir + "chargingNumberVehicles.csv")

        fig, ax = plt.subplots(figsize=(8,6))
        ax.plot(plot_data['x'], plot_data['charging-vehicle'])
        ax.set_xlabel('Hour')
        ax.set_ylabel('Number of charging vehicles')
        ax.set_xlim([0, max_hour])
        ax.set_ylim([y_min, y_max])
        ax.grid(axis='y', linestyle='--')
        plt.title('Vehicles Charging')
        plt.savefig(working_dir + "chargingNumberVehicles_fixedScaling.png", dpi=300, bbox_inches='tight', pad_inches=0)
        plt.show()

        figure.add_trace(
            go.Line(
                x=plot_data['x'],
                y=plot_data['charging-vehicle'],
                name="It " + str(iteration) + ""
            ),
            row=row,
            col=col
        )


def plot_iteration(iteration, row, col, figure):
    # Setup directory
    working_dir = get_iteration_dir(run_dir, iteration)
    print("-------------- ITERATION", iteration, "--------------------")
    print("Working on path: ", working_dir)

    df_events_refueling = get_refuel_events_from_events_csv(working_dir + "events.csv")
    size_before_filtering = len(df_events_refueling.index)
    df_events_refueling = df_events_refueling[df_events_refueling.fuel > 0]
    print('Refuel_Event_Analysis: Ignored ', size_before_filtering - len(df_events_refueling.index), ' events with 0 fuel')
    print("Total of ", len(df_events_refueling.index), "Refuel Events")

    # Group by charger
    x = pd.Series()
    y = pd.Series()
    df_refueling_sum = df_events_refueling.groupby('parkingTaz').sum()
    if len(df_refueling_sum.index) > 0:
        x = df_refueling_sum.index
        y = df_refueling_sum.fuel / 3.6e6

    # TODO Normalize
    """
    def my_func(value, taz):
        return value / df_taz_info[df_taz_info['taz'] == int(taz)].numStalls.iloc[0]
    df_taz_info = pd.read_csv(path_to_taz_parking)
    for index, value in y.items():
        y.iloc[int(index)] = my_func(value, index)
    """

    figure.add_trace(
        go.Bar(
            x=x,
            y=y,
            name="It " + str(iteration) + " (events.xml)"
        ),
        row=row,
        col=col
    )
    figure.add_trace(
        go.Line(
            x=pd.Series([0, x.max()]),
            y=pd.Series([y.mean(), y.mean()]),
            name="It " + str(iteration) + " Average"
        ),
        row=row,
        col=col
    )

    """
    # Print parking events
    df_parking = get_parking_events_from_events_csv(working_dir + "events.csv")
    df_parking_group = df_parking.groupby('parkingTaz')
    for name, group in df_parking_group:
        print("TAZ ", name, "has ", len(group.index), "parking events")
    """
    return y.min(), y.max()


num_rows = int(last_iteration / step_size) + 1
if last_iteration % step_size > 0:
    num_rows += 1
subplot_titles = ["Iteration "+str(iteration) for iteration in range(0, last_iteration, step_size)]
subplot_titles.append("Iteration "+str(last_iteration))

if plot_charger_util:
    plotly_figure = make_subplots(rows=num_rows, cols=1, subplot_titles=subplot_titles, shared_xaxes=True, vertical_spacing=0.02)
    row = 1
    y_min = 999999
    y_max = 0
    for iteration in range_inclusive(0, last_iteration, step_size):
        (y_min_iteration, y_max_iteration) = plot_iteration(iteration, row, 1, plotly_figure)
        if y_min_iteration < y_min: y_min = y_min_iteration
        if y_max_iteration > y_max: y_max = y_max_iteration

        plotly_figure['layout']['yaxis'+str(row)].update(title=ytitle)
        row += 1

    for y_axis in range(1, row):
        plotly_figure['layout']['yaxis'+str(y_axis)].update(title=ytitle)
        plotly_figure['layout']['yaxis'+str(y_axis)].update(range=[0, y_max * 1.1])

    plotly_figure['layout']['xaxis'+str(row-1)].update(title="Charging TAZ")
    plotly_figure['layout']['xaxis'+str(row-1)].update(range=[100, 700])
    plotly_figure.update_layout(
        title_text="Charger utilization for simulation "+latest_run,
        height=350
    )
    plotly_figure.show()

if plot_number_of_charging_vehicles:
    plotly_figure = make_subplots(rows=num_rows, cols=1, subplot_titles=subplot_titles, shared_xaxes=True, vertical_spacing=0.02)
    row = 1
    y_min = 0
    y_max = 0
    x_title = 'Hour'
    y_title = '# of charging vehicles'

    # Get min max values
    for iteration in range_inclusive(0, last_iteration, step_size):
        working_dir = get_iteration_dir(run_dir, iteration)
        if os.path.exists(working_dir + "chargingNumberVehicles.csv"):
            plot_data = pd.read_csv(working_dir + "chargingNumberVehicles.csv")
            if len(plot_data.index) > 0:
                if plot_data['charging-vehicle'].min() < y_min: y_min = plot_data['charging-vehicle'].min()
                if plot_data['charging-vehicle'].max() > y_max: y_max = plot_data['charging-vehicle'].max()

    for iteration in range_inclusive(0, last_iteration, step_size):
        plot_charging_vehicles(iteration, row, 1, plotly_figure, y_min, y_max)
        plotly_figure['layout']['yaxis'+str(row)].update(title=ytitle)
        plotly_figure['layout']['yaxis'+str(row)].update(range=[0, y_max * 1.1])
        row += 1

    plotly_figure['layout']['xaxis'+str(row-1)].update(title=x_title)
    plotly_figure['layout']['xaxis'+str(row-1)].update(range=[0, max_hour])
    plotly_figure.update_layout(
        title_text="Number of charging vehicles for simulation "+latest_run,
        height=350*num_rows
    )
    plotly_figure.show()

if plot_activity_types:
    for iteration in range_inclusive(0, last_iteration, step_size):
        working_dir = get_iteration_dir(run_dir, iteration)
        plot_data = pd.read_csv(working_dir + "activityType.csv")
        fig, ax = plt.subplots(figsize=(8,6))
        for col in plot_data.columns:
            if not col == 'x':
                ax.plot(plot_data['x'], plot_data[col], label=str(col))
        ax.set_xlabel('Hour')
        ax.set_ylabel('Number of charging vehicles')
        ax.set_xlim([0, max_hour])
        ax.grid(axis='y', linestyle='--')
        plt.legend()
        plt.title('Activity Type')
        plt.savefig(working_dir + "activityType_fixedScaling.png", dpi=300, bbox_inches='tight', pad_inches=0)
        plt.show()

else:
    last_iteration = get_last_iteration(run_dir)
    plotly_figure = make_subplots(rows=1, cols=1, subplot_titles=("Iteration " + str(last_iteration), ""), shared_xaxes=True, vertical_spacing=0.02)
    plot_iteration(last_iteration, 1, 1, plotly_figure)
