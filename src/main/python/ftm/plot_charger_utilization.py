import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from python.ftm.plot_events import get_refuel_events_from_events_csv
from python.ftm.util import get_run_dir, get_latest_run, get_iteration_dir

# Configuration
baseDir = "/home/lucas/IdeaProjects/beam/output/munich-simple/"
latest_run = get_latest_run(baseDir)
run_dir = get_run_dir(baseDir, latest_run)
last_iteration = 3
num_rows = int(last_iteration / 2) + 1
num_cols = last_iteration % 2 + 1

plotly_figure = make_subplots(rows=last_iteration+1, cols=1, subplot_titles=("Iteration 0", "Iteration 1", "Iteration 2", "Iteration 3"), shared_xaxes=True, vertical_spacing=0.02)
# Get parking events from events.xml
for iteration in range(last_iteration + 1):
    # Setup directory
    working_dir = get_iteration_dir(run_dir, iteration)
    print("-------------- ITERATION", iteration, "--------------------")
    print("Working on path: ", working_dir)
    row = iteration + 1             # Stacked layout
    col = 1                         # Stacked layout

    df_events_refueling = get_refuel_events_from_events_csv(working_dir + "events.csv")
    size_before_filtering = len(df_events_refueling.index)
    df_events_refueling = df_events_refueling[df_events_refueling.fuel > 0]
    print('Refuel_Event_Analysis: Ignored ', size_before_filtering - len(df_events_refueling.index), ' events with 0 fuel')
    print("Total of ", len(df_events_refueling.index), "Refuel Events")

    # Group by charger
    df_chargers = df_events_refueling.groupby('parkingTaz')
    x = pd.Series()
    y = pd.Series()
    for parking_taz, df_parking_taz in df_chargers:
        x = x.append(pd.Series(parking_taz))
        y = y.append(pd.Series(df_parking_taz.fuel.sum() / 3.6e6))

    plotly_figure.add_trace(
        go.Bar(
            x=x,
            y=y,
            name="It " + str(iteration) + " (events.xml)"
        ),
        row=row,
        col=col
    )

ytitle = "# of charging events"
ytitle = "transferred energy in kwh"
plotly_figure['layout']['xaxis4'].update(title="Charging TAZ")
plotly_figure['layout']['yaxis1'].update(title=ytitle)
plotly_figure['layout']['yaxis2'].update(title=ytitle)
plotly_figure['layout']['yaxis3'].update(title=ytitle)
plotly_figure['layout']['yaxis4'].update(title=ytitle)
plotly_figure.update_layout(
    title_text="Charger utilization for simulation "+latest_run
)
plotly_figure.show()
