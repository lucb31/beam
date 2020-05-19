import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from random import randrange

from python.ftm.filter_plans import filter_plans_by_vehicle_id, filter_plans_by_vehicle_id_from_plans_csv, \
    filter_plans_by_person_id_from_plans_csv, get_vehicle_id_from_population_csv
from python.ftm.analyze_events import get_driving_events_from_events_csv, \
    get_walking_events_from_events_csv, get_parking_events_from_events_csv, get_all_events_from_events_csv, \
    get_refuel_events_from_events_csv, get_charging_events_from_events_csv
from python.ftm.util import get_run_dir, get_latest_run, get_iteration_dir, seconds_to_time_string, range_inclusive

########## CONFIG #############
pd.set_option('display.max_columns', 500)
baseDir = "/home/lucas/IdeaProjects/beam/output/munich-simple/"
baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = get_latest_run(baseDir)
latest_run = "munich-simple__500agents_72h_30iters__2020-05-13_10-23-13"
#latest_run = "munich-simple_24h_DEBUG_replanning__2020-05-12_11-43-34"
#latest_run = "munich-simple_24h_50iter_500agents__2020-04-24_10-32-55"
run_dir = get_run_dir(baseDir, latest_run)
vehicle_id = 0
vehicle_id = 439
last_iteration = 5
iteration_stepsize = 1
max_hour = 72
max_soc = 22
plot_scoring_means = False
plot_multiple_vehicles = True
num_vehicles = 1
plot_engine = 'pyplot' # Options: pyplot, plotly


# Plot setup
xlabel = 'Time of day in h'
ylabel = 'Current SOC in kWh'
################


def plotConsumptionOverLength(df, plotSpeedBasedConsumption, plotLengthBasedConsumption):
    # Plot Data
    fig, ax = plt.subplots(2, 1)
    xvals = df['legLength'].values / 1000
    xlabel = 'Trip length in km'
    ylabel = 'Consumed energy in kWh'
    ax[0].set_title('Vehicle energy consumed for different trips')
    markerSize = 10

    if plotSpeedBasedConsumption:
        yvals = df['primaryEnergyConsumedInJoule'].values / 3.6e6
        ax[0].scatter(xvals, yvals, label='Speed based calculation', color='blue', s=markerSize)
        ax[0].plot([xvals.min(), xvals.max()], [yvals.min(), yvals.max()], color='blue')
        ax[0].set_xlabel(xlabel)
        ax[0].set_ylabel(ylabel)
        ax[0].legend()
        plt.grid()

    if plotLengthBasedConsumption:
        yvals = df['onlyLengthPrimaryEnergyConsumedInJoule'].values / 3.6e6
        ax[1].scatter(xvals, yvals, label='Length based calculation', color='orange', s=markerSize)
        ax[1].plot([xvals.min(), xvals.max()], [yvals.min(), yvals.max()], color='orange')
        ax[1].set_xlabel(xlabel)
        ax[1].set_ylabel(ylabel)
        ax[1].legend()

    plt.grid()
    plt.show()


def plotConsumptionOverDuration(df, plotSpeedBasedConsumption, plotLengthBasedConsumption):
    # Plot Data
    fig, ax = plt.subplots(2, 1)
    xvals = df['legDuration'].values / 60
    xlabel = 'Trip duration in min'
    ylabel = 'Consumed energy in kWh'
    ax[0].set_title('Vehicle energy consumed for different trips')
    markerSize = 10

    if plotSpeedBasedConsumption:
        yvals = df['primaryEnergyConsumedInJoule'].values / 3.6e6
        ax[0].scatter(xvals, yvals, label='Speed based calculation', color='blue', s=markerSize)
        ax[0].plot([xvals.min(), xvals.max()], [yvals.min(), yvals.max()], color='blue')
        ax[0].set_xlabel(xlabel)
        ax[0].set_ylabel(ylabel)
        ax[0].legend()
        plt.grid()

    if plotLengthBasedConsumption:
        yvals = df['onlyLengthPrimaryEnergyConsumedInJoule'].values / 3.6e6
        ax[1].scatter(xvals, yvals, label='Length based calculation', color='orange', s=markerSize)
        ax[1].plot([xvals.min(), xvals.max()], [yvals.min(), yvals.max()], color='orange')
        ax[1].set_xlabel(xlabel)
        ax[1].set_ylabel(ylabel)
        ax[1].legend()

    plt.grid()
    plt.show()


def get_plotdata_soc_over_duration_event_based(iteration, vehicle_id):
    # Setup working directory and plot configuration
    working_dir = get_iteration_dir(run_dir, iteration)
    path_to_events_csv = working_dir + "events.csv"
    print("-------------- ITERATION", iteration, "--------------------")
    print("Working on path: ", working_dir)

    # Collect and filter data from events.csv
    df_events = get_driving_events_from_events_csv(path_to_events_csv)
    df_events = df_events[df_events['vehicle'] == vehicle_id]
    df_refueling_events = get_refuel_events_from_events_csv(path_to_events_csv)
    df_refueling_events = df_refueling_events[df_refueling_events['vehicle'] == vehicle_id]

    # Unit conversion
    df_events['primaryFuelLevel'] /= 3.6e6
    df_events['primaryFuel'] /= 3.6e6
    df_events['time'] /= 3600
    df_events['departureTime'] /= 3600
    df_events['arrivalTime'] /= 3600
    df_refueling_events['time'] /= 3600
    df_refueling_events['fuel'] /= 3.6e6

    # Calc. starting soc
    first_trip = df_events[df_events['time'] == df_events.time.min()]
    soc_start = first_trip['primaryFuelLevel'].iloc[0] + first_trip['primaryFuel'].iloc[0]

    # Calc plot points
    xvals = pd.Series([0])
    yvals = pd.Series([soc_start])
    for departure_time, arrival_time, fuel_used, fuel_arrival in zip(df_events.departureTime, df_events.arrivalTime, df_events.primaryFuel, df_events.primaryFuelLevel):
        xvals = xvals.append(pd.Series([departure_time, arrival_time]), ignore_index=True)
        yvals = yvals.append(pd.Series([fuel_arrival + fuel_used, fuel_arrival]), ignore_index=True)

    """
    for time, fuel in zip(df_refueling_events.time, df_refueling_events.fuel):
        prev_trips = df_events[df_events['arrivalTime'] <= time]
        prev_trip = df_events[df_events['arrivalTime'] == df_events['arrivalTime'].min()]
        xvals = xvals.append(pd.Series([time]), ignore_index=True)
        yvals = yvals.append(pd.Series([prev_trip.primaryFuelLevel + fuel]), ignore_index=True)
        """
    xvals = xvals.append(pd.Series([max_hour]), ignore_index=True)
    yvals = yvals.append(pd.Series([yvals.iloc[-1]]), ignore_index=True)

    return xvals, yvals


def get_plotdata_soc_over_duration_consumption_based(iteration, vehicle_id, max_hour = 36):
    # Setup working directory and plot configuration
    working_dir = get_iteration_dir(run_dir, iteration)
    path_to_events_csv = working_dir + "events.csv"
    path_to_output_png = working_dir + "soc_link_consumption_based_vehicle_" + str(vehicle_id) + ".png"
    print("-------------- ITERATION", iteration, "--------------------")
    print("Working on path: ", working_dir)

    # Read and filter consumption data from csv data
    df_consumption_per_trip = pd.read_csv(working_dir + "vehConsumptionPerTrip.csv")
    df_consumption_per_link = pd.read_csv(working_dir + "vehConsumptionPerLink.csv")
    df_consumption_per_trip = df_consumption_per_trip[df_consumption_per_trip.vehicleId == vehicle_id]
    df_consumption_per_link = df_consumption_per_link[df_consumption_per_link.vehicleId == vehicle_id]

    # Get refueling data
    df_events_csv = get_all_events_from_events_csv(path_to_events_csv)
    df_refueling_events = get_refuel_events_from_events_csv(path_to_events_csv, df=df_events_csv, add_missing_refuel_events=False)
    df_refueling_events = df_refueling_events[df_refueling_events.vehicle.eq(vehicle_id)]

    if len(df_consumption_per_trip.index) > 0:
        # Divide data into trips
        trips = df_consumption_per_link.groupby('legStartTime')
        print("found", trips.ngroups, "different trips and ", len(df_refueling_events.index), " refuel events")

        # starting soc
        first_trip = df_consumption_per_trip[df_consumption_per_trip['legStartTime'] == df_consumption_per_trip.legStartTime.min()]
        xvals_sum = pd.Series([0])
        yvals_sum = pd.Series([first_trip.primaryFuelLevelAfterLeg.iloc[0] + first_trip.primaryEnergyConsumedInJoule.iloc[0]]) / 3.6e6

        for name, trip in trips:
            socRow = df_consumption_per_trip[df_consumption_per_trip['legStartTime'] == trip['legStartTime'].iloc[0]]
            current_soc_in_kwh = (socRow.primaryFuelLevelAfterLeg.iloc[0] + socRow.primaryEnergyConsumedInJoule.iloc[
                0]) / 3.6e6
            linkConsumptions = trip['energyConsumedInJoule'].values / 3.6e6
            linkDurations = trip['linkLength'] / trip['linkAvgSpeed']
            xvals = (trip['legStartTime'] + linkDurations.cumsum()) / 3600
            yvals = pd.Series(current_soc_in_kwh - linkConsumptions.cumsum())
            startTime = socRow.legStartTime.iloc[0]
            tripLength = socRow.legLength.iloc[0]
            tripConsumption = socRow.primaryEnergyConsumedInJoule.iloc[0]
            endTime = startTime + socRow.legDuration.iloc[0]

            xvals_sum = xvals_sum.append(xvals, ignore_index=True)
            yvals_sum = yvals_sum.append(yvals, ignore_index=True)
            print("Trip from", seconds_to_time_string(startTime), "to", seconds_to_time_string(endTime), ": ",
                  current_soc_in_kwh, "kW, ", current_soc_in_kwh * 3.6e6, "J", 'avg consumption: ', tripConsumption / tripLength)

            # plot preceding refuel events
            filteredRefuelDf = df_refueling_events[df_refueling_events.time == startTime]
            if len(filteredRefuelDf.index) > 0 and filteredRefuelDf.iloc[0].duration > 0:
                xvals = pd.Series()
                yvals = pd.Series()
                # plot additional connecting line (optional)
                precedingTripsDf = df_consumption_per_trip[df_consumption_per_trip['legStartTime'] < trip['legStartTime'].iloc[0]]
                previous_trip_df = precedingTripsDf[
                    precedingTripsDf.legStartTime == precedingTripsDf['legStartTime'].max()]
                if len(previous_trip_df.index) > 0:
                    xvals = xvals.append(
                        pd.Series([previous_trip_df.iloc[0].legStartTime + previous_trip_df.iloc[0].legDuration]), ignore_index=True)
                    yvals = yvals.append(pd.Series([previous_trip_df.iloc[0].primaryFuelLevelAfterLeg / 3.6e6]), ignore_index=True)

                xvals = xvals.append(pd.Series([
                    float(filteredRefuelDf.time.iloc[0]) - filteredRefuelDf.duration.iloc[0],
                    float(filteredRefuelDf.time.iloc[0])]) / 3600, ignore_index=True)
                yvals = yvals.append(pd.Series([
                    filteredRefuelDf.fuelAfterCharging.iloc[0] - filteredRefuelDf.fuel.iloc[0],
                    filteredRefuelDf.fuelAfterCharging.iloc[0]]) / 3.6e6, ignore_index=True)


                xvals_sum = xvals_sum.append(xvals, ignore_index=True)
                yvals_sum = yvals_sum.append(yvals, ignore_index=True)

        # plot refueling at end of day events
        maxLegStartTime = df_consumption_per_trip['legStartTime'].max()
        filteredRefuelDf = df_refueling_events[df_refueling_events.time > maxLegStartTime]
        if len(filteredRefuelDf) > 0 and filteredRefuelDf.iloc[0].duration > 0:
            xvals = pd.Series()
            yvals = pd.Series()
            # plot additional connecting line (optional)
            previous_trip_df = df_consumption_per_trip[df_consumption_per_trip.legStartTime == maxLegStartTime]
            xvals = xvals.append(pd.Series([previous_trip_df.iloc[0].legStartTime + previous_trip_df.iloc[0].legDuration]), ignore_index=True)
            yvals = yvals.append(pd.Series([previous_trip_df.iloc[0].primaryFuelLevelAfterLeg / 3.6e6]), ignore_index=True)

            # Refueling late
            # xvals = np.append(xvals, [int(filteredRefuelDf.time.iloc[0] - filteredRefuelDf.duration.iloc[0]), int(filteredRefuelDf.time.iloc[0])]) / 3600

            # Refueling as soon as plugged in
            xvals = xvals.append(pd.Series([float(filteredRefuelDf.time.iloc[0]) - filteredRefuelDf.duration.iloc[0],
                                            float(filteredRefuelDf.time.iloc[0])]) / 3600, ignore_index=True)
            yvals = yvals.append(pd.Series([filteredRefuelDf.fuelAfterCharging.iloc[0] - filteredRefuelDf.fuel.iloc[0],
                                            filteredRefuelDf.fuelAfterCharging.iloc[0]]) / 3.6e6, ignore_index=True)
            xvals_sum = xvals_sum.append(xvals, ignore_index=True)
            yvals_sum = yvals_sum.append(yvals, ignore_index=True)

        xvals_sum = xvals_sum.append(pd.Series([max_hour]), ignore_index=True)
        yvals_sum = yvals_sum.append(pd.Series([yvals.iloc[-1]]), ignore_index=True)
        return xvals_sum, yvals_sum
    else:
        return [], []



def plotTripConsumptionOverDistance(df, plotSpeedBasedConsumption, plotLengthBasedConsumption, startingSocInKwh):
    # Plot Data
    fig, ax = plt.subplots(2, 1)
    xvals = df['linkLength'].cumsum() / 1000
    xlabel = 'Distance in km'
    ylabel = 'Consumed energy in kWh'
    ax[0].set_title('Vehicle Energy consumed')
    markerSize = 10

    if plotSpeedBasedConsumption:
        linkConsumptions = df['energyConsumedInJoule'].values / 3.6e6
        xvals = df['linkLength'].cumsum() / 1000
        yvals = startingSocInKwh - linkConsumptions.cumsum()
        ax[0].scatter(xvals, yvals, label='Speed based', s=markerSize)
        ax[0].set_xlabel(xlabel)
        ax[0].set_ylabel(ylabel)
        ax[0].legend()
        plt.grid()

    if plotLengthBasedConsumption:
        yvals = df['onlyLengthEnergyConsumedInJoule'].values / 3.6e6
        ax[1].scatter(xvals, yvals, label='Length based calculation', color='orange', s=markerSize)
        ax[1].plot([xvals.min(), xvals.max()], [yvals.min(), yvals.max()], color='orange')
        ax[1].set_xlabel(xlabel)
        ax[1].set_ylabel(ylabel)
        ax[1].legend()

    plt.grid()
    plt.show()


def plot_avg_speed_per_link(df):
    # Plot Data
    fig, ax = plt.subplots()
    xlabel = 'Average link speed in m/s'
    ylabel = 'Number of links'
    ax.set_title('Average link speed distribution')
    markerSize = 10

    plt.hist(df['linkAvgSpeed'])
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()


def printTripsSummary(df):
    avgConsumption = (df.primaryEnergyConsumedInJoule / df.legLength) / 36
    print("Avg kwh / 100km: \n", avgConsumption)


def concat_event_info_string(x, y, event_type, taz):
    info_string = concat_trip_info_string(x, y) + "<br>"
    try:
        return info_string + str(event_type) + " (TAZ " + str(int(taz)) + ")"
    except:
        return info_string + str(event_type) + " (TAZ " + str(taz) +")"


def concat_trip_info_string(x, y):
    return seconds_to_time_string(x*3600) + ": " + ("%.2f" % y) + "kWh"


def print_refuel_events_for_taz(taz_ids, df_events):
    for taz in taz_ids:
        filtered_df = df_events[df_events.parkingTaz == taz]
        if len(filtered_df.index) > 0:
            print("Refuel events for TAZ", taz)
            print(filtered_df[['vehicle', 'parkingTaz', 'locationX', 'locationY', 'fuel']].head(5))
        else:
            print("No Refuel events for TAZ", taz)


def print_parking_events_for_taz(taz_ids, parking_df):
    for taz in taz_ids:
        filtered_df = parking_df[parking_df.parkingTaz == taz]
        if len(filtered_df.index) > 0:
            print("5 Parking events for TAZ", taz)
            print(filtered_df[['vehicle', 'parkingTaz', 'locationX', 'locationY']].head(5))
        else:
            print("No Parking events for TAZ", taz)


def calc_end_and_min_soc_means(df):
    end_socs = pd.Series([])
    min_socs = pd.Series([])
    negative_socs = 0
    for name, group in df.groupby(['vehicleId']):
        end_soc = df.iloc[group['spaceTime'].idxmax()].primaryFuelLevelAfterLeg
        min_soc = group.primaryFuelLevelAfterLeg.min()
        if min_soc < 0:
            negative_socs += 1
        end_socs = end_socs.append(pd.Series([end_soc]))
        min_socs = min_socs.append(pd.Series([min_soc]))
    print("mean end soc [kWh]: ", end_socs.mean() / 3.6e6, "mean min soc [kWh]", min_socs.mean() / 3.6e6)
    return end_socs.mean() / 3.6e6, min_socs.mean() / 3.6e6, negative_socs


def calc_refueling_events_mean(df):
    if len(df.index) > 0:
        refueling_events = pd.Series([])
        for name, group in df.groupby(['vehicle']):
            df_group_filtered = group[group['fuel'] > 0]
            refueling_events = refueling_events.append(pd.Series([len(df_group_filtered.index)]))
        print("mean refueling events: ", refueling_events.mean())
        return refueling_events.mean()
    else:
        return 0


def get_random_vehicle_id(run_dir):
    working_dir = get_iteration_dir(run_dir, 0)
    df_consumption_per_link = pd.read_csv(working_dir + "vehConsumptionPerLink.csv")

    vehicle_ids = df_consumption_per_link.vehicleId.unique()
    index = randrange(vehicle_ids.size)
    vehicle_id = vehicle_ids[index]
    return vehicle_id


def plot_soc_dt_pyplot_multiple_iterations(start_iter, stop_iter, vehicle_id):
    fig, ax = plt.subplots(4, 1, sharex=True, sharey=True)
    row = 0
    path_to_output_png = '/home/lucas/IdeaProjects/beam/output/' + "socs_linear_replanning_vehicle" + str(vehicle_id) + ".png"
    for iteration in range(start_iter, stop_iter):
        print("Plotting energy consumption for vehicle with the id", vehicle_id, "of the provided csv data")
        # Plot data from link consumption
        xvals, yvals = get_plotdata_soc_over_duration_consumption_based(iteration, vehicle_id, max_hour)
        plot_df = pd.DataFrame({
            'xval': xvals,
            'yval': yvals,
            'info': [concat_trip_info_string(x, y) for x, y in zip(xvals, yvals)]})
        plot_df = plot_df.sort_values(by=['xval'])
        ax[row].plot(plot_df.xval.values, plot_df.yval.values.astype('float64'), label="Fahrzeug "+str(vehicle_id) + ', Iteration '+str(iteration))
        ax[row].grid(axis='y', linestyle='--')
        ax[row].set_xlim([0, max_hour])
        ax[row].set_ylim([0, 10])
        ax[row].legend(loc='lower left')
        #plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)
        #plt.savefig(path_to_output_png.split('.png')[0] + 'zoomed.png', dpi=300, bbox_inches='tight', pad_inches=0)
        row += 1

    # add a big axis, hide frame
    fig.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
    plt.xlabel("Simulationszeit in Stunden")
    plt.ylabel("Ladezustand in kWh")
    plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()


def plot_soc_dt(iteration, row, figure, vehicle_id, ytitle, plot_events=False):
    plot_col = 1
    working_dir = get_iteration_dir(run_dir, iteration)
    generate_pyplot = False
    generate_pyplot_subplots = True
    path_to_output_png = working_dir + "soc_event_based_vehicle_" + str(vehicle_id) + ".png"

    print("Plotting energy consumption for vehicle with the id", vehicle_id, "of the provided csv data")
    # Plot data from link consumption
    xvals, yvals = get_plotdata_soc_over_duration_consumption_based(iteration, vehicle_id, max_hour)
    plot_df = pd.DataFrame({
        'xval': xvals,
        'yval': yvals,
        'info': [concat_trip_info_string(x, y) for x, y in zip(xvals, yvals)]})
    plot_df = plot_df.sort_values(by=['xval'])
    figure.add_trace(
        go.Scatter(
            x=plot_df.xval.values,
            y=plot_df.yval.values.astype('float64'),
            name="Fahrzeug "+str(vehicle_id)+", Iteration "+str(iteration)+" (CSV)",
            hovertemplate='%{text}',
            text=plot_df['info'].values,
            textfont_size=25
        ),
        row=row,
        col=plot_col
    )
    figure['layout']['yaxis'+str(row)].update(title=ytitle)
    figure['layout']['yaxis'+str(row)].update(range=[0, max_soc]) #Todo Make this dynamic


    if generate_pyplot:
        fig, ax = plt.subplots()
        ax.plot(plot_df.xval.values, plot_df.yval.values.astype('float64'), label="Fahrzeug "+str(vehicle_id))
        #ax.set_title('SOC during one day: Vehicle ' + str(vehicle_id) + "iter " + str(iteration))
        ax.set_xlim([0, max_hour])
        ax.set_ylim([0, 10])
        ax.set_xlabel('Simulationszeit in Stunden')
        ax.set_ylabel('Ladezustand in kWh')
        ax.grid(axis='y', linestyle='--')
        plt.legend()
        plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)
        ax.set_xlim([14.5, 16.5])
        plt.savefig(path_to_output_png.split('.png')[0] + 'zoomed.png', dpi=300, bbox_inches='tight', pad_inches=0)
        plt.show()

    if plot_events:
        path_to_events_csv = working_dir + "events.csv"
        df_events_csv = get_all_events_from_events_csv(path_to_events_csv)
        # Parse events from csv
        df_driving_events = get_driving_events_from_events_csv(df=df_events_csv)
        df_driving_events = df_driving_events[df_driving_events['vehicle'] == vehicle_id]
        df_walking_events = get_walking_events_from_events_csv(df=df_events_csv)
        df_walking_events = df_walking_events[df_walking_events['driver'].eq(df_driving_events['driver'].iloc[0])]
        df_parking_events = get_parking_events_from_events_csv(df=df_events_csv)
        df_parking_events = df_parking_events[df_parking_events['vehicle'] == vehicle_id]
        df_parking_events.time = [seconds_to_time_string(time[0]) for (time) in zip(df_parking_events['time'])]
        df_charging_events = get_charging_events_from_events_csv(df=df_events_csv)
        df_charging_events = df_charging_events[df_charging_events['vehicle'] == vehicle_id]

        #print("Driving events\n", df_driving_events[['type', 'departureTime', 'arrivalTime', 'primaryFuelLevel', 'parkingTaz']].head(20))
        #print("Walking events\n", df_walking_events[['type', 'departureTime', 'arrivalTime', 'length']].head(20))
        #print("Parking events\n", df_parking_events[['parkingTaz', 'time', 'locationX', 'locationY']].head(20))
        #print("Refuel events\n", df_refueling_events[['time', 'fuel', 'parkingTaz', 'locationX', 'locationY']].head(20))
        events_plot_df = pd.DataFrame({
            'xval': df_driving_events.time / 3600,
            'yval': df_driving_events.primaryFuelLevel / 3.6e6,
            'info': [concat_event_info_string(x, y, event_type, taz) for x, y, event_type, taz in zip(df_driving_events.time / 3600, df_driving_events.primaryFuelLevel / 3.6e6, df_driving_events.type, df_driving_events.parkingTaz)]
        })
        events_plot_df = events_plot_df.append(pd.DataFrame({
            'xval': df_charging_events.time / 3600,
            'yval': df_charging_events.primaryFuelLevel / 3.6e6,
            'info': [concat_event_info_string(x, y, event_type, taz) for x, y, event_type, taz in zip(df_charging_events.time / 3600, df_charging_events.primaryFuelLevel / 3.6e6, df_charging_events.type, df_charging_events.parkingTaz)]
        }))
        events_plot_df = events_plot_df.sort_values(by=['xval'])
        figure.add_trace(
            go.Scatter(
                x=events_plot_df.xval.values,
                y=events_plot_df.yval.values.astype('float64'),
                name="It " + str(iteration) + " (events.xml)",
                hovertemplate='%{text}',
                text=events_plot_df['info'].values,
                textfont_size=25
            ),
            row=row,
            col=plot_col
        )
    else:
        print("ERR: Empty dataframe on iteration " + str(iteration))


def pyplot_soc_event_based(iteration, vehicle_id):
    xvals, yvals = get_plotdata_soc_over_duration_event_based(iteration, vehicle_id)

    fig, ax = plt.subplots()
    ax.plot(xvals, yvals, label="Fahrzeug "+str(vehicle_id)+' Iteration ' + str(iteration))
    #ax.scatter(xvals, yvals)
    ax.set_xlim([0, max_hour])
    ax.set_ylim([0, max_soc])
    ax.set_xlabel('Simulationszeit in Stunden')
    ax.set_ylabel('Ladezustand in kWh')
    ax.grid(axis='y', linestyle='--')
    plt.legend()
    #plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()


def main():
    global vehicle_id
    if vehicle_id == 0:
        vehicle_id = get_random_vehicle_id(run_dir)

    # DEBUG
    #plot_soc_dt_pyplot_multiple_iterations(0, 4, vehicle_id)
    #exit()

    num_rows = int(last_iteration / iteration_stepsize) + 1
    if last_iteration % iteration_stepsize > 0:
        num_rows += 1

    if plot_engine == 'pyplot':
        plot_multiple_iterations_in_one = True
        if plot_multiple_iterations_in_one:
            fig, ax = plt.subplots(num_rows, 1, sharex=True, sharey=True)
            plot_row = 0
            for iteration in range_inclusive(0, last_iteration, iteration_stepsize):
                xvals, yvals = get_plotdata_soc_over_duration_event_based(iteration, vehicle_id)

                ax[plot_row].plot(xvals, yvals, label="Fahrzeug "+str(vehicle_id)+' Iteration ' + str(iteration))
                #ax[plot_row].scatter(xvals, yvals)
                ax[plot_row].set_xlim([0, max_hour])
                ax[plot_row].set_ylim([0, max_soc])
                ax[plot_row].grid(axis='y', linestyle='--')
                ax[plot_row].legend(loc='lower left')
                plot_row += 1

            # add a big axis, hide frame
            fig.add_subplot(111, frameon=False)
            # hide tick and tick label of the big axis
            plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
            plt.xlabel("Simulationszeit in Stunden")
            plt.ylabel("Ladezustand in kWh")
            #plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)
            plt.show()
        else:
            for iteration in range_inclusive(0, last_iteration, iteration_stepsize):
                pyplot_soc_event_based(iteration, vehicle_id)

    else:
        # Init plotly figure
        subplot_titles = ["Iteration "+str(iteration) for iteration in range_inclusive(0, last_iteration, iteration_stepsize)]
        plotly_figure = make_subplots(rows=num_rows, cols=1, subplot_titles=subplot_titles, shared_xaxes=True, vertical_spacing=0.02)

        # Draw plots for every iteration
        plot_row = 1
        for iteration in range_inclusive(0, last_iteration, iteration_stepsize):
            plot_soc_dt(iteration, plot_row, plotly_figure, vehicle_id, ylabel, True)
            plot_row += 1


        # Show plotly figure
        plotly_figure.update_layout(title_text=title, height=350*plot_row)
        plotly_figure['layout']['xaxis'+str(plot_row)].update(title=xlabel)
        plotly_figure.show()

    if plot_multiple_vehicles:
        # Init vehicle_comparison figure
        vehicle_ids = [get_random_vehicle_id(run_dir) for vehicle in range(0, num_vehicles)]
        subplot_titles = ["Iteration "+str(last_iteration)+" (Vehicle "+str(vehicle_id)+")" for vehicle_id in vehicle_ids]
        # Hacky
        vehicle_ids = [439]
        subplot_titles = []
        plotly_figure_vehicle_comparison = make_subplots(rows=num_vehicles, cols=1, subplot_titles=subplot_titles, shared_xaxes=True, vertical_spacing=0.02)
        plot_row = 1
        for vehicle_id in vehicle_ids:
            plot_soc_dt(last_iteration, plot_row, plotly_figure_vehicle_comparison, vehicle_id, ylabel)
            plotly_figure_vehicle_comparison['layout']['xaxis'+str(plot_row)].update(range=[0, max_hour])
            plot_row += 1
        #plotly_figure_vehicle_comparison['layout']['xaxis'+str(plot_row - 1)].update(xlabel='Simulationszeit in Stunden')
        plotly_figure_vehicle_comparison.update_layout(
            xaxis_title='Simulationszeit in Stunden',
            yaxis_title='Ladezustand in kWh',
            showlegend=True,
            font=dict(
                size=30
            ))
        plotly_figure_vehicle_comparison.show()


    if plot_scoring_means:
        # Init mean Series
        mean_end_socs = pd.Series()
        mean_min_socs = pd.Series()
        mean_refueling_events = pd.Series()
        negative_socs_series = pd.Series()

        # Plot scoring parameters mean end and min soc plot
        plotly_figure_mean_socs = go.Figure()
        plotly_figure_mean_socs = make_subplots(rows=1, cols=1, subplot_titles=("Iterations"), shared_xaxes=True, vertical_spacing=0.02, )
        # Gather data
        for iteration in range(0, last_iteration + 1):
            # Setup working directory
            working_dir = get_iteration_dir(run_dir, iteration)
            path_to_events_csv = working_dir + "events.csv"
            df_consumption_per_trip = pd.read_csv(working_dir + "vehConsumptionPerTrip.csv")

            # Log mean socs
            (mean_end_soc, mean_min_soc, negative_socs) = calc_end_and_min_soc_means(df_consumption_per_trip)
            mean_end_socs = mean_end_socs.append(pd.Series([mean_end_soc]), ignore_index=True)
            mean_min_socs = mean_min_socs.append(pd.Series([mean_min_soc]), ignore_index=True)
            negative_socs_series = negative_socs_series.append(pd.Series([negative_socs]), ignore_index=True)
            df_refueling_events = get_refuel_events_from_events_csv(path_to_events_csv, add_missing_refuel_events=False)
            mean_refueling_events = mean_refueling_events.append(pd.Series([calc_refueling_events_mean(df_refueling_events)]), ignore_index=True)

        plotly_figure_mean_socs.add_trace(go.Scatter(x=mean_end_socs.index, y=mean_end_socs, name='Mean End Soc'))
        plotly_figure_mean_socs.add_trace(go.Scatter(x=mean_min_socs.index.values, y=mean_min_socs.values, name='Mean Min Soc'))
        plotly_figure_mean_socs.add_trace(go.Scatter(x=mean_refueling_events.index.values, y=mean_refueling_events.values, name='Mean number of refueling events'), row=1, col=1)
        plotly_figure_mean_socs.add_trace(go.Scatter(x=negative_socs_series.index.values, y=negative_socs_series.values, name='Number of vehicles with negative soc'), row=1, col=1)
        plotly_figure_mean_socs.update_layout(title_text="Mean end soc, min soc, # of refueling events in simulation " + str(run_dir),
                                              xaxis_title='Iteration',
                                              yaxis_title='Energy in kWh',
                                              yaxis2={
                                                'title': '[kN.m/(m/s)²]',
                                                'overlaying': 'y',
                                                'side': 'right',
                                                'showgrid': False
        })
        plotly_figure_mean_socs.show()


if __name__ == '__main__':
    main()