from matplotlib import pyplot as plt
from matplotlib import rc
import pandas as pd
import numpy as np

from python.ftm.analyze_events import get_all_events_from_events_csv, df_columns_to_numeric, \
    get_refuel_events_from_events_csv, save_refuel_events_to_charging_events_csv
from python.ftm.util import colors, range_inclusive, get_latest_run, get_run_dir, get_iteration_dir

########### CONFIG

#path_to_events_csv = "/data/lucas/SA/Simulation Runs/munich-simple_24h_DEBUG_replanning__2020-05-12_11-03-13/ITERS/it.2/2.events.csv"
baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = get_latest_run(baseDir)
#latest_run = "munich-simple__500agents_72h_30iters__2020-05-13_10-56-07"
#latest_run = "munich-simple_24h_DEBUG_replanning__2020-05-12_11-03-13"
run_dir = get_run_dir(baseDir, latest_run)
first_iteration = 1
last_iteration = 1
iteration_stepsize = 1
max_hour = 24
show_title = False
path_to_output_png = '/home/lucas/IdeaProjects/beam/output/' + 'number_of_charging_events_with_acttype_' + latest_run + '.png'
font = {'size': 15}
rc('font', **font)
############


def main():
    plot_data = {}
    y_max = 0
    act_types = ['Home', 'Work', 'Other', 'Education', 'Shopping']
    for iteration in range_inclusive(first_iteration, last_iteration, iteration_stepsize):
        # Setup working directory and plot configuration
        working_dir = get_iteration_dir(run_dir, iteration)
        path_to_events_csv = working_dir + "events.csv"

        # Get refuel events
        df_refuel_events = get_refuel_events_from_events_csv(path_to_events_csv)
        df_refuel_events_has_act_type = df_refuel_events[df_refuel_events['actType'].notna()]

        if len(df_refuel_events_has_act_type.index) == 0:
            # Get vehicle events
            df_events = get_all_events_from_events_csv(path_to_events_csv)
            df_events_has_vehicle = df_events[df_events['vehicle'].notna()]
            df_events_has_driving_vehicle = df_columns_to_numeric(df_events_has_vehicle[df_events_has_vehicle['vehicle'].str.isnumeric()], ['vehicle'])
            #df_events_has_driving_vehicle = get_driving_events_from_events_csv(path_to_events_csv)

            df_refuel_events = df_refuel_events.assign(actType=pd.Series(np.zeros(len(df_refuel_events.index))))

            # Get person events
            df_events_has_person = df_columns_to_numeric(df_events[df_events['person'].notna()], ['person'])

            for time, vehicle_id in zip(df_refuel_events.time, df_refuel_events.vehicle):
                df_events_has_driving_vehicle_filtered = df_events_has_driving_vehicle[df_events_has_driving_vehicle['vehicle'] == vehicle_id]
                df_events_vehicle_filtered_has_person_id = df_columns_to_numeric(df_events_has_driving_vehicle_filtered[df_events_has_driving_vehicle_filtered['person'].notna()], ['person'])
                person_id = df_events_vehicle_filtered_has_person_id['person'].unique()[0]
                df_events_person_filtered = df_columns_to_numeric(df_events_has_person[df_events_has_person['person'] == person_id], ['time'])

                # Correct activity ist the first Start act after the last end act
                df_events_actstart = df_events_person_filtered[df_events_person_filtered['type'] == 'actstart']
                df_events_actend = df_events_person_filtered[df_events_person_filtered['type'] == 'actend']
                df_events_actend_preceding = df_events_actend[df_events_actend['time'] <= time].sort_values(by='time')
                df_events_actstart_after_last_actend = df_events_actstart[df_events_actstart['time'] > df_events_actend_preceding.time.iloc[-1]]
                if len(df_events_actstart_after_last_actend.index) > 0:
                    preceding_act_type = df_events_actstart_after_last_actend['actType'].iloc[0]
                    df_refuel_events.loc[df_refuel_events.time.eq(time) & df_refuel_events.vehicle.eq(vehicle_id), 'actType'] = preceding_act_type

                else:
                    print('could not find activity')
                    df_refuel_events.loc[df_refuel_events.time.eq(time) & df_refuel_events.vehicle.eq(vehicle_id), 'actType'] = 'Other'

                    #df_appended = df_events_person_filtered.append(df_events_has_driving_vehicle_filtered)
                    #df_appended = df_appended.sort_values(by='time')

            save_refuel_events_to_charging_events_csv(path_to_events_csv, df_refuel_events)
        # Init bins
        bin = {}
        for act_type in act_types:
            bin[act_type] = np.zeros(max_hour + 1)
        for time, act_type in zip(df_refuel_events.time, df_refuel_events.actType):
            hour = int(time / 3600)
            if act_type not in act_types:
                act_type = 'Other'
            bin[act_type][hour] += 1

        # Update y max
        for act_type in act_types:
            for y in bin[act_type]:
                if y > y_max:
                    y_max = y
        plot_data[iteration] = bin

    fig, axes = plt.subplots(len(plot_data), 1, figsize=(8, 8))
    plot_row = 0
    for iteration in range_inclusive(first_iteration, last_iteration, iteration_stepsize):
        data = plot_data[iteration]
        for index, act_type in enumerate(act_types):
            if first_iteration == last_iteration:
                ax = axes
            else:
                ax = axes[plot_row]
            ax.plot(np.arange(0, max_hour+1), data[act_type], label=act_type+', Iteration '+str(iteration), color=colors[index])
            ax.set_xlim([0, max_hour])
            ax.set_ylim([0, y_max*1.1])
            ax.grid(axis='y', linestyle='--')
            ax.legend(loc='upper left', ncol=1)
        plot_row += 1

    # add a big axis, hide frame
    fig.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
    plt.xlabel('Simulationszeit in Stunden')
    plt.ylabel('Anzahl der abgeschlossenen Ladevorgänge')
    if show_title:
        plt.title('Iteration '+str(iteration)+', '+latest_run)
    print('Saving file to ', path_to_output_png)
    plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()

if __name__ == '__main__':
    main()
"""
for time in zip(df_refuel_events_filtered.time):
    df_events_actstart = df_columns_to_numeric(df_events_person_filtered[df_events_person_filtered['type'] == 'actstart'], ['time'])
    df_events_actstart_preceding = df_events_actstart[df_events_actstart['time'] <= time].sort_values(by='time')
    preceding_act_type = df_events_actstart_preceding['actType'].iloc[-1]
    debug = 0

debug = 0
"""


"""
def plot_charging_vehicles(iteration):
    max_hour = 72
    # Setup directory
    working_dir = get_iteration_dir(run_dir, iteration)
    path_to_events_csv = working_dir + "events.csv"
    print("-------------- ITERATION", iteration, "--------------------")
    print("Working on path: ", working_dir)

    df_events = get_all_events_from_events_csv(path_to_events_csv)
    event_types = ["ChargingPlugInEvent", "ChargingPlugOutEvent"]
    #df_plug_events = df_events[df_events['type'] in event_types]
    df_plug_events = df_events[(df_events['type'] == "ChargingPlugInEvent") | (df_events['type'] == "ChargingPlugOutEvent")]
    df_plug_events = df_plug_events.sort_values(by=['time'])
    df_plug_in_events = df_events[df_events['type'] == "ChargingPlugInEvent"]
    df_plug_out_events = df_events[df_events['type'] == "ChargingPlugOutEvent"]
    vehicle_charging_time = {}

    # init hours
    hourly_charging_time = {}
    for hour in range(0, max_hour):
        hourly_charging_time[hour] = 0
    for time, vehicle, type in zip(df_plug_events.time, df_plug_events.vehicle, df_plug_events.type):
        hour_of_event = int(time / 3600)
        if type == "ChargingPlugInEvent":
            vehicle_charging_time[vehicle] = hour_of_event
        elif type == "ChargingPlugOutEvent":
            plug_in_time = vehicle_charging_time[vehicle]
            vehicle_charging_time[vehicle] = 0
            if plug_in_time > 0:
                for hour in range(plug_in_time, hour_of_event):
                    if hour in hourly_charging_time:
                        hourly_charging_time[hour] += 1
                    else:
                        hourly_charging_time[hour] = 1
            else:
                print("Found ChargingPlugOutEvent without ChargingPlugInEvent")

    plotly_figure.add_trace(
        go.Bar(
            x=hourly_charging_time.keys(),
            y=hourly_charging_time.values(),
            name="It " + str(iteration) + " (events.csv)"
        ),
        row=2,
        col=1
    )
    """