import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from python.ftm.analyze_events import get_refuel_events_from_events_csv, get_total_walking_distances_from_events_csv, \
    get_parking_events_from_events_csv, get_all_events_from_events_csv
from python.ftm.util import get_run_dir, get_latest_run, get_iteration_dir, get_last_iteration


def plot_iteration(iteration, row, col, y_min_value, y_max_value):
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
    plotly_figure.add_trace(
        go.Bar(
            x=x,
            y=y,
            name="It " + str(iteration) + " (events.xml)"
        ),
        row=row,
        col=col
    )
    plotly_figure.add_trace(
        go.Line(
            x=pd.Series([0, x.max()]),
            y=pd.Series([y.mean(), y.mean()]),
            name="It " + str(iteration) + " Average"
        ),
        row=row,
        col=col
    )

    # Print parking events
    df_parking = get_parking_events_from_events_csv(working_dir + "events.csv")
    df_parking_group = df_parking.groupby('parkingTaz')
    for name, group in df_parking_group:
        print("TAZ ", name, "has ", len(group.index), "parking events")

    # Update min / max y
    if y.min() < y_min_value: y_min_value = y.min()
    if y.max() > y_max_value: y_max_value = y.max()
    return y_min_value, y_max_value

# Configuration
baseDir = "/home/lucas/IdeaProjects/beam/output/munich-simple/"
latest_run = get_latest_run(baseDir)
path_to_taz_parking = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-parking.csv"
#latest_run = "munich-simple__2020-04-06_11-04-37"
run_dir = get_run_dir(baseDir, latest_run)
last_iteration = 50
step_size = 25
compare_iterations = True
ytitle = "Transferred energy in kwh"
y_min_value = 999
y_max_value = 0

if compare_iterations:
    num_rows = int(last_iteration / step_size) + 1
    if last_iteration % step_size > 0:
        num_rows += 1
    subplot_titles = ["Iteration "+str(iteration) for iteration in range(0, last_iteration, step_size)]
    subplot_titles.append("Iteration "+str(last_iteration))
    plotly_figure = make_subplots(rows=num_rows, cols=1, subplot_titles=subplot_titles, shared_xaxes=True, vertical_spacing=0.02)
    row = 1
    for iteration in range(0, last_iteration, step_size):
        (y_min_value, y_max_value) = plot_iteration(iteration, row, 1, y_min_value, y_max_value)
        plotly_figure['layout']['yaxis'+str(row)].update(title=ytitle)
        row += 1
    (y_min_value, y_max_value) = plot_iteration(last_iteration, row, 1, y_min_value, y_max_value)

    for y_axis in range(1, row + 1):
        plotly_figure['layout']['yaxis'+str(y_axis)].update(title=ytitle)
        plotly_figure['layout']['yaxis'+str(y_axis)].update(range=[0, y_max_value*1.1])

    plotly_figure['layout']['xaxis'+str(row)].update(title="Charging TAZ")
    plotly_figure['layout']['xaxis'+str(row)].update(range=[100, 700])

else:
    last_iteration = get_last_iteration(run_dir)
    plotly_figure = make_subplots(rows=1, cols=1, subplot_titles=("Iteration " + str(last_iteration), ""), shared_xaxes=True, vertical_spacing=0.02)
    plot_iteration(last_iteration, 1, 1)
plotly_figure.update_layout(
    title_text="Charger utilization for simulation "+latest_run,
    height=350*row
)
plotly_figure.show()
