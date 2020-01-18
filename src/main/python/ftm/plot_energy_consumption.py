import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from random import randrange
from plot_events import parse_event_xml_to_pandas_dataframe_float_time
from plot_events import get_refuel_events_from_event_xml
from plot_events import plot_refuel_events_over_duration

def plotConsumptionOverLength(df,plotSpeedBasedConsumption, plotLengthBasedConsumption):
    # Plot Data
    fig, ax = plt.subplots(2,1)
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


def plotTripConsumptionOverDuration(df, socDf, refuelDf, plot_separate):
    linkDurations = df['linkLength'] / df['linkAvgSpeed']
    xlabel = 'Time of day in h'
    ylabel = 'Current SOC in kWh'
    title = 'SOC during one day'
    markerSize = 10

    # Divide data into trips
    trips = df.groupby('legStartTime')
    print("found", trips.ngroups, "different trips")
    #eventsDf = parse_event_xml_to_pandas_dataframe_float_time("events/0.events.filtered.xml")
    #ax.plot(eventsDf.time / 3600, eventsDf.fuel, label='Event data')

    if plot_separate:
        fig, ax = plt.subplots(2,2)
    else:
        fig, ax = plt.subplots()
    i = 0
    for name, trip in trips:
        socRow = socDf[socDf['legStartTime'] == trip['legStartTime'].iloc[0]]
        current_soc_in_kwh = (socRow.primaryFuelLevelAfterLeg.iloc[0] + socRow.primaryEnergyConsumedInJoule.iloc[0]) / 3.6e6
        linkConsumptions = trip['energyConsumedInJoule'].values / 3.6e6
        linkDurations = trip['linkLength'] / trip['linkAvgSpeed']
        xvals = (trip['legStartTime'] + linkDurations.cumsum()) / 3600
        yvals = current_soc_in_kwh - linkConsumptions.cumsum()
        startTime = socRow.legStartTime.iloc[0]
        endTime = startTime + socRow.legDuration.iloc[0]

        print("Trip from",seconds_to_time_string(startTime),"to",seconds_to_time_string(endTime), ": ", current_soc_in_kwh, "kW, ", current_soc_in_kwh*3.6e6, "J")
        if plot_separate:
            title = 'SOC during trip starting at ' + seconds_to_time_string(name)
            ax[int(i/2)][i%2].plot(xvals, yvals, label='Trip starting at '+str(name))
            ax[int(i/2)][i%2].set_xlabel(xlabel)
            ax[int(i/2)][i%2].set_ylabel(ylabel)
            ax[int(i/2)][i%2].set_title(title)
            ax[int(i/2)][i%2].grid()
        else:
            ax.plot(xvals, yvals, label='Trip starting at '+seconds_to_time_string(name))

            # plot preceding refuel events
            filteredRefuelDf = refuelDf[refuelDf.endTime == startTime]
            if len(filteredRefuelDf) > 0:
                # plot additional connecting line (optional)
                precedingTripsDf = socDf[socDf['legStartTime'] < trip['legStartTime'].iloc[0]]
                previous_trip_df = precedingTripsDf[precedingTripsDf.legStartTime == precedingTripsDf['legStartTime'].max()]
                print(previous_trip_df)
                xvals = np.array([previous_trip_df.iloc[0].legStartTime + previous_trip_df.iloc[0].legDuration / 3600])
                yvals = np.array([previous_trip_df.iloc[0].primaryFuelLevelAfterLeg / 3.6e6])

                xvals = np.append(xvals, [int(filteredRefuelDf.endTime.iloc[0] - filteredRefuelDf.duration.iloc[0]), int(filteredRefuelDf.endTime.iloc[0])]) / 3600
                yvals = np.append(yvals, [current_soc_in_kwh - filteredRefuelDf.fuel.iloc[0] / 3.6e6, current_soc_in_kwh])
                ax.plot(xvals, yvals, label='Refuel session ending at '+seconds_to_time_string(name))

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.set_xlim(0, 24)
            ax.grid()
            ax.legend()

        i += 1
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

def seconds_to_time_string(seconds):
    hour = int(seconds / 3600)
    minute = int((seconds - hour*3600) / 60)
    string = ""
    if hour < 10:
        string += "0"
    string += str(hour) + ":"
    if minute < 10:
        string += "0"
    string += str(minute)
    return string


def get_last_dir(path):
    dirs = os.listdir(path)
    res = dirs[0]
    for file in dirs:
        if file > res:
            res = file
    return res


pd.set_option('display.max_columns', 500)
baseDir = "/home/lucas/IdeaProjects/beam/output/munich-simple/"
runDir = baseDir + str(get_last_dir(baseDir)) + "/"

df = pd.read_csv(runDir + "vehConsumptionPerTrip.csv")
dfPerLink = pd.read_csv(runDir + "vehConsumptionPerLink.csv")
vehicleId = randrange(df.vehicleId.max())
vehicleId = 22

#plotConsumptionOverDuration(df, True, True)
#plotConsumptionOverLength(df, True, True)

# Filter data by vehicle
print("Plotting energy consumption for vehicle with the id", vehicleId, "of:", runDir)
df = df[df.vehicleId == vehicleId]
dfPerLink = dfPerLink[dfPerLink.vehicleId == vehicleId]

# Compare refuel events
refuelDf = get_refuel_events_from_event_xml(runDir + "ITERS/it.0/0.events.xml")
refuelDf['chargingType'] = 'NonLinear'
refuelDfLinear = get_refuel_events_from_event_xml(baseDir + "__LINEAR_CHARGING_munich-simple/" + "ITERS/it.0/0.events.xml")
refuelDfLinear['chargingType'] = 'Linear'
refuelDfLinearSocDep = get_refuel_events_from_event_xml(baseDir + "__LINEAR_SOC_DEP_CHARGING_munich-simple/" + "ITERS/it.0/0.events.xml")
refuelDfLinearSocDep['chargingType'] = 'LinearSocDep'

plot_refuel_events_over_duration([refuelDf, refuelDfLinear, refuelDfLinearSocDep])
refuelDf = refuelDf[refuelDf.vehicle == str(vehicleId)]

# Draw plots
#printTripsSummary(df)
#plot_avg_speed_per_link(dfPerLink)
#plotTripConsumptionOverDuration(dfPerLink, df, refuelDf, True)
plotTripConsumptionOverDuration(dfPerLink, df, refuelDf, False)
