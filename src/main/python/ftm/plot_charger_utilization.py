import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from python.ftm.plot_events import get_refuel_and_parking_events_from_event_xml
from python.ftm.util import get_run_dir, get_latest_run, get_iteration_dir

# Configuration
baseDir = "/home/lucas/IdeaProjects/beam/output/munich-simple/"
latest_run = get_latest_run(baseDir)
run_dir = get_run_dir(baseDir)
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

    # Get refuel and parking events from xml, ignore fuel = 0 events
    df_events_refueling, df_events_parking = get_refuel_and_parking_events_from_event_xml(working_dir + "events.xml")
    size_before_filtering = len(df_events_refueling.index)
    df_events_refueling = df_events_refueling[df_events_refueling.fuel > 0]
    print('Ignored ', size_before_filtering - len(df_events_refueling.index), ' events with 0 fuel')

    # Group by charger
    df_chargers = df_events_refueling.groupby('parkingTaz')
    x = pd.Series()
    y = pd.Series()
    for parking_taz, df_parking_taz in df_chargers:
        x = x.append(pd.Series(parking_taz))
        #y = y.append(pd.Series(len(df_parking_taz.index)))
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

    # Save analysis data to csv file
    with open(working_dir + "chargingEvents.csv", mode='w') as charging_events_file:
        df_events_refueling.to_csv(charging_events_file, mode='w', header=True, index=False)

plotly_figure['layout']['xaxis4'].update(title="Charging TAZ")
plotly_figure['layout']['yaxis1'].update(title="# of charging events")
plotly_figure['layout']['yaxis2'].update(title="# of charging events")
plotly_figure['layout']['yaxis3'].update(title="# of charging events")
plotly_figure['layout']['yaxis4'].update(title="# of charging events")
plotly_figure.update_layout(
    title_text="Charger utilization for simulation "+latest_run
)
plotly_figure.show()
