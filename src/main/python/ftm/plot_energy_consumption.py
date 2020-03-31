import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from random import randrange

from python.ftm.filter_plans import filter_plans_by_vehicle_id
from python.ftm.plot_events import get_driving_events_from_events_csv, \
    get_walking_events_from_events_csv, get_parking_events_from_events_csv, get_all_events_from_events_csv, \
    get_refuel_events_from_events_csv, get_charging_events_from_events_csv
from python.ftm.util import get_run_dir, get_latest_run, get_iteration_dir, seconds_to_time_string


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


def plotTripConsumptionOverDuration(df_consumption_per_link, df_consumption_per_trip, df_refueling_events, plot_separate, max_hour = 36):
    linkDurations = df_consumption_per_link['linkLength'] / df_consumption_per_link['linkAvgSpeed']
    xlabel = 'Time of day in h'
    ylabel = 'Current SOC in kWh'
    title = 'SOC during one day: Vehicle ' + str(df_consumption_per_link['vehicleId'].iloc[0])
    markerSize = 10
    plot_sub_trips = False

    # Divide data into trips
    trips = df_consumption_per_link.groupby('legStartTime')
    print("found", trips.ngroups, "different trips and ", len(df_refueling_events.index), " refuel events")
    if plot_sub_trips:
        fig, ax = plt.subplots()

    # starting soc
    first_trip = df_consumption_per_trip[df_consumption_per_trip['legStartTime'] == df_consumption_per_trip.legStartTime.min()]
    xvals_sum = pd.Series([0])
    yvals_sum = pd.Series([first_trip.primaryFuelLevelAfterLeg.iloc[0] + first_trip.primaryEnergyConsumedInJoule.iloc[0]]) / 3.6e6

    if plot_separate:
        fig, ax = plt.subplots(2, 2)
    plotted_trips = 0
    for name, trip in trips:
        socRow = df_consumption_per_trip[df_consumption_per_trip['legStartTime'] == trip['legStartTime'].iloc[0]]
        current_soc_in_kwh = (socRow.primaryFuelLevelAfterLeg.iloc[0] + socRow.primaryEnergyConsumedInJoule.iloc[
            0]) / 3.6e6
        linkConsumptions = trip['energyConsumedInJoule'].values / 3.6e6
        linkDurations = trip['linkLength'] / trip['linkAvgSpeed']
        xvals = (trip['legStartTime'] + linkDurations.cumsum()) / 3600
        yvals = pd.Series(current_soc_in_kwh - linkConsumptions.cumsum())
        startTime = socRow.legStartTime.iloc[0]
        endTime = startTime + socRow.legDuration.iloc[0]

        xvals_sum = xvals_sum.append(xvals, ignore_index=True)
        yvals_sum = yvals_sum.append(yvals, ignore_index=True)
        print("Trip from", seconds_to_time_string(startTime), "to", seconds_to_time_string(endTime), ": ",
              current_soc_in_kwh, "kW, ", current_soc_in_kwh * 3.6e6, "J")
        if plot_separate:
            title = 'SOC during trip starting at ' + seconds_to_time_string(name)
            ax[int(plotted_trips / 2)][plotted_trips % 2].plot(xvals, yvals, label='Trip starting at ' + str(name))
            ax[int(plotted_trips / 2)][plotted_trips % 2].set_xlabel(xlabel)
            ax[int(plotted_trips / 2)][plotted_trips % 2].set_ylabel(ylabel)
            ax[int(plotted_trips / 2)][plotted_trips % 2].set_title(title)
            ax[int(plotted_trips / 2)][plotted_trips % 2].grid()
        else:
            if plot_sub_trips:
                ax.plot(xvals, yvals, label='Trip starting at ' + seconds_to_time_string(name))

            # plot preceding refuel events
            filteredRefuelDf = df_refueling_events[df_refueling_events.endTime == startTime]
            if len(filteredRefuelDf.index) > 0 and filteredRefuelDf.iloc[0].duration > 0:
                xvals = pd.Series()
                yvals = pd.Series()
                if plot_sub_trips:
                    # plot additional connecting line (optional)
                    precedingTripsDf = df_consumption_per_trip[df_consumption_per_trip['legStartTime'] < trip['legStartTime'].iloc[0]]
                    previous_trip_df = precedingTripsDf[
                        precedingTripsDf.legStartTime == precedingTripsDf['legStartTime'].max()]
                    if len(previous_trip_df.index) > 0:
                        xvals = xvals.append(
                            pd.Series([previous_trip_df.iloc[0].legStartTime + previous_trip_df.iloc[0].legDuration]), ignore_index=True)
                        yvals = yvals.append(pd.Series([previous_trip_df.iloc[0].primaryFuelLevelAfterLeg / 3.6e6]), ignore_index=True)

                xvals = xvals.append(pd.Series([
                    float(filteredRefuelDf.endTime.iloc[0]) - filteredRefuelDf.duration.iloc[0],
                    float(filteredRefuelDf.endTime.iloc[0])]) / 3600, ignore_index=True)
                yvals = yvals.append(pd.Series([
                    filteredRefuelDf.fuelAfterCharging.iloc[0] - filteredRefuelDf.fuel.iloc[0],
                    filteredRefuelDf.fuelAfterCharging.iloc[0]]) / 3.6e6, ignore_index=True)


                xvals_sum = xvals_sum.append(xvals, ignore_index=True)
                yvals_sum = yvals_sum.append(yvals, ignore_index=True)
                if plot_sub_trips:
                    ax.plot(xvals, yvals, label='Refuel session ending at ' + seconds_to_time_string(name))
        plotted_trips += 1

    # plot refueling at end of day events
    maxLegStartTime = df_consumption_per_trip['legStartTime'].max()
    filteredRefuelDf = df_refueling_events[df_refueling_events.endTime > maxLegStartTime]
    if len(filteredRefuelDf) > 0 and filteredRefuelDf.iloc[0].duration > 0:
        xvals = pd.Series()
        yvals = pd.Series()
        if plot_sub_trips:
            # plot additional connecting line (optional)
            previous_trip_df = df_consumption_per_trip[df_consumption_per_trip.legStartTime == maxLegStartTime]
            xvals = xvals.append(pd.Series([previous_trip_df.iloc[0].legStartTime + previous_trip_df.iloc[0].legDuration]), ignore_index=True)
            yvals = yvals.append(pd.Series([previous_trip_df.iloc[0].primaryFuelLevelAfterLeg / 3.6e6]), ignore_index=True)

        # Refueling late
        # xvals = np.append(xvals, [int(filteredRefuelDf.endTime.iloc[0] - filteredRefuelDf.duration.iloc[0]), int(filteredRefuelDf.endTime.iloc[0])]) / 3600

        # Refueling as soon as plugged in
        xvals = xvals.append(pd.Series([float(filteredRefuelDf.endTime.iloc[0]) - filteredRefuelDf.duration.iloc[0],
                                        float(filteredRefuelDf.endTime.iloc[0])]) / 3600, ignore_index=True)

        yvals = yvals.append(pd.Series([filteredRefuelDf.fuelAfterCharging.iloc[0] - filteredRefuelDf.fuel.iloc[0],
                                        filteredRefuelDf.fuelAfterCharging.iloc[0]]) / 3.6e6, ignore_index=True)

        xvals_sum = xvals_sum.append(xvals, ignore_index=True)
        yvals_sum = yvals_sum.append(yvals, ignore_index=True)
        if plot_sub_trips:
            ax.plot(xvals, yvals, label='Refuel session ending at ' + seconds_to_time_string(name))

    xvals_sum = xvals_sum.append(pd.Series([max_hour]))
    yvals_sum = yvals_sum.append(pd.Series([yvals.iloc[-1]]))
    if not plot_sub_trips:
        return xvals_sum, yvals_sum
    else:
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xlim(0, max_hour)
        ax.grid()
        ax.legend()

        plt.show()


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
    if taz > 0:
        return info_string + str(event_type) + " (TAZ " + str(int(taz)) + ")"
    else:
        return info_string + str(event_type)


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



pd.set_option('display.max_columns', 500)
baseDir = "/home/lucas/IdeaProjects/beam/output/munich-simple/"
latest_run = get_latest_run(baseDir)
#run_dir = "/home/lucas/IdeaProjects/beam/output/munich-simple/munich-simple__2020-03-23_11-24-47/"
#run_dir = "/home/lucas/IdeaProjects/beam/output/munich-simple/munich-simple__2020-03-24_09-15-22/"
vehicleId = 38   #38
last_iteration = 3
num_plot_rows = int(last_iteration / 2) + 1
num_plot_cols = last_iteration % 2 + 1

# Plot setup
xlabel = 'Time of day in h'
ylabel = 'Current SOC in kWh'
plotly_stacked_layout = True


# Initialize plot figures
fig, ax = plt.subplots()
fig_separate, ax_separate = plt.subplots(num_plot_rows, num_plot_cols)
fig_separate_events, ax_separate_events = plt.subplots(num_plot_rows, num_plot_cols)
plotly_figure = make_subplots(rows=num_plot_rows, cols=num_plot_cols, subplot_titles=("Iteration 0", "Iteration 1", "Iteration 2", "Iteration 3"))
if plotly_stacked_layout:
    plotly_figure = make_subplots(rows=last_iteration+1, cols=1, subplot_titles=("Iteration 0", "Iteration 1", "Iteration 2", "Iteration 3"), shared_xaxes=True, vertical_spacing=0.02)

# Draw plots for every iteration
for iteration in range(last_iteration + 1):
    # Setup working directory and plot configuration
    working_dir = get_iteration_dir(run_dir, iteration)
    path_to_events_csv = working_dir + "events.csv"
    print("-------------- ITERATION", iteration, "--------------------")
    print("Working on path: ", working_dir)
    plot_row = int(iteration / 2) + 1        # Grid layout
    plot_col = iteration % 2 + 1             # Grid layout
    if plotly_stacked_layout:
        plot_row = iteration + 1             # Stacked layout
        plot_col = 1                         # Stacked layout

    # Read and filter consumption data from csv data
    df_consumption_per_trip = pd.read_csv(working_dir + "vehConsumptionPerTrip.csv")
    df_consumption_per_link = pd.read_csv(working_dir + "vehConsumptionPerLink.csv")
    while vehicle_id == 0:
        vehicle_id = randrange(df_consumption_per_trip.vehicleId.max())
    df_consumption_per_trip = df_consumption_per_trip[df_consumption_per_trip.vehicleId == vehicle_id]
    df_consumption_per_link = df_consumption_per_link[df_consumption_per_link.vehicleId == vehicle_id]

    # Get refueling data
    df_events_csv = get_all_events_from_events_csv(path_to_events_csv)
    df_refueling_events = get_refuel_events_from_events_csv(df=df_events_csv)
    df_refueling_events = df_refueling_events[df_refueling_events.vehicle.eq(vehicle_id)]

    print("Plotting energy consumption for vehicle with the id", vehicle_id, "of the provided csv data")
    if len(df_consumption_per_trip.index) > 0:
        # Plot data from link consumption
        xvals, yvals = plotTripConsumptionOverDuration(df_consumption_per_link, df_consumption_per_trip, df_refueling_events, False, 24)
        plot_df = pd.DataFrame({
            'xval': xvals,
            'yval': yvals,
            'info': [concat_trip_info_string(x, y) for x, y in zip(xvals, yvals)]})
        plot_df = plot_df.sort_values(by=['xval'])
        plotly_figure.add_trace(
            go.Scatter(
                x=plot_df.xval.values,
                y=plot_df.yval.values.astype('float64'),
                name="It "+str(iteration)+" (CSV)",
                hovertemplate='%{text}',
                text=plot_df['info'].values,
            ),
            row=plot_row,
            col=plot_col
        )

        ax_separate[int(iteration / 2)][iteration % 2].scatter(plot_df.xval, plot_df.yval, label='Iteration ' + str(iteration))
        ax_separate[int(iteration / 2)][iteration % 2].set_xlabel(xlabel)
        ax_separate[int(iteration / 2)][iteration % 2].set_ylabel(ylabel)
        ax_separate[int(iteration / 2)][iteration % 2].set_xlim(0, 36)
        ax_separate[int(iteration / 2)][iteration % 2].set_ylim(5, 15)
        ax_separate[int(iteration / 2)][iteration % 2].set_title('Iteration ' + str(iteration))
        ax_separate[int(iteration / 2)][iteration % 2].grid()
        ax.scatter(plot_df.xval, plot_df.yval, label='Iteration ' + str(iteration))

        # Parse events from csv
        # TODO Check for PlugInEvents w/o PlugOut
        df_driving_events = get_driving_events_from_events_csv(df=df_events_csv)
        df_driving_events = df_driving_events[df_driving_events['vehicle'] == vehicle_id]
        df_walking_events = get_walking_events_from_events_csv(df=df_events_csv)
        df_walking_events = df_walking_events[df_walking_events['driver'].eq(df_driving_events['driver'].iloc[0])]
        df_parking_events = get_parking_events_from_events_csv(df=df_events_csv)
        df_parking_events = df_parking_events[df_parking_events['vehicle'] == vehicle_id]
        df_parking_events.time = [seconds_to_time_string(time[0]) for (time) in zip(df_parking_events['time'])]
        df_charging_events = get_charging_events_from_events_csv(df=df_events_csv)
        df_charging_events = df_charging_events[df_charging_events['vehicle'] == vehicle_id]

        print("Driving events\n", df_driving_events[['type', 'departureTime', 'arrivalTime', 'primaryFuelLevel', 'parkingTaz']].head(20))
        print("Walking events\n", df_walking_events[['type', 'departureTime', 'arrivalTime', 'length']].head(20))
        print("Parking events\n", df_parking_events[['parkingTaz', 'time', 'locationX', 'locationY']].head(20))
        #print("All events \n")

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
        ax_separate_events[int(iteration / 2)][iteration % 2].plot(events_plot_df.xval, events_plot_df.yval)
        ax_separate_events[int(iteration / 2)][iteration % 2].scatter(events_plot_df.xval, events_plot_df.yval)
        ax_separate_events[int(iteration / 2)][iteration % 2].set_xlabel(xlabel)
        ax_separate_events[int(iteration / 2)][iteration % 2].set_ylabel(ylabel)
        ax_separate_events[int(iteration / 2)][iteration % 2].set_xlim(0, 36)
        ax_separate_events[int(iteration / 2)][iteration % 2].set_ylim(5, 15)
        ax_separate_events[int(iteration / 2)][iteration % 2].set_title('Iteration ' + str(iteration))
        ax_separate_events[int(iteration / 2)][iteration % 2].grid()
        fig_separate_events.suptitle("Data from events")

        plotly_figure.add_trace(
            go.Scatter(
                x=events_plot_df.xval.values,
                y=events_plot_df.yval.values.astype('float64'),
                name="It " + str(iteration) + " (events.xml)",
                hovertemplate='%{text}',
                text=events_plot_df['info'].values
            ),
            row=plot_row,
            col=plot_col
        )
    else:
        print("ERR: Empty dataframe on iteration " + str(iteration))

title = "SOC of Vehicle " + str(vehicle_id) + " in simulation " + str(run_dir)
ax.set_xlabel(xlabel)
ax.set_ylabel(ylabel)
ax.set_title(title)
ax.set_xlim(0, 36)
ax.set_ylim(0, 15)
ax.grid()
ax.legend()
#plt.show()

# Show plotly figure
plotly_figure.update_layout(title_text=title)
plotly_figure.show()

# Print plans
filter_plans_by_vehicle_id(
    "/home/lucas/IdeaProjects/beam/test/input/munich-simple/households.xml",
    get_iteration_dir(run_dir, 3) + "plans.xml.gz",
    vehicle_id)
