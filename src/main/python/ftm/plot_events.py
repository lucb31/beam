import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import tikzplotlib
import numpy as np
from os import path

from python.ftm.charging_power_calculation import calc_avg_charging_power_numeric
from python.ftm.util import seconds_to_time_string


def get_persons_to_vehicle_df(input_filename):
    tree = ET.parse(input_filename)
    root = tree.getroot()
    df = pd.DataFrame(columns=['person', 'vehicle'])

    # parse XML
    for event in root:
        if 'type' in event.attrib and event.attrib['type'] == 'PathTraversal':
            if 'driver' in event.attrib:
                driver = int(event.attrib['driver'])
                try:
                    vehicle = int(event.attrib['vehicle'])
                except ValueError as ex:
                    vehicle = 0
                if driver > 0 and vehicle > 0 and len(df[df['person'] == driver].index) == 0:
                    df = df.append({
                        'person': driver,
                        'vehicle': vehicle,
                    }, ignore_index=True)

    return df


def get_refuel_and_parking_events_from_event_xml(input_filename):
    tree = ET.parse(input_filename)
    root = tree.getroot()
    refuel_df = pd.DataFrame(columns=['endTime', 'vehicle', 'fuel', 'duration', 'fuelAfterCharging', 'parkingTaz', 'locX', 'locY'])
    parking_df = pd.DataFrame(columns=['time', 'vehicle', 'parkingTaz', 'locX', 'locY'])

    # parse XML
    for event in root:
        if 'type' in event.attrib:
            event_type = event.attrib['type']
            if event_type == 'RefuelSessionEvent':
                refuel_df = refuel_df.append({
                    'endTime': float(event.attrib['time']),
                    'vehicle': int(event.attrib['vehicle']),
                    'fuel': float(event.attrib['fuel']),
                    'duration': float(event.attrib['duration']),
                    'fuelAfterCharging': 0.0,
                    'parkingTaz': int(event.attrib['parkingTaz']),
                    'locX': float(event.attrib['locationX']),
                    'locY': float(event.attrib['locationY'])
                }, ignore_index=True)
            elif event_type == 'ChargingPlugOutEvent':
                if refuel_df.endTime.iloc[-1] == float(event.attrib['time']):
                    refuel_df.fuelAfterCharging.iloc[-1] = float(event.attrib['primaryFuelLevel'])
            elif event_type == 'ParkEvent':
                try:
                    parking_taz = int(event.attrib['parkingTaz'])
                except ValueError as ex:
                    parking_taz = -1
                parking_df = parking_df.append({
                    'time': float(event.attrib['time']),
                    'vehicle': int(event.attrib['vehicle']),
                    'parkingTaz': parking_taz,
                    'locX': float(event.attrib['locationX']),
                    'locY': float(event.attrib['locationY'])
                }, ignore_index=True)

    return refuel_df, parking_df


def get_all_events_from_events_csv(path_to_events_csv):
    assert path.exists(path_to_events_csv)
    return pd.read_csv(path_to_events_csv, sep=",", index_col=None, header=0)


def get_refuel_events_from_events_csv(path_to_events_csv="", df=None, add_missing_refuel_events=False):
    # Check if events already parsed
    path_to_charging_events_csv = path_to_events_csv.split(".events.")[0] + ".chargingEvents.csv"
    if path.exists(path_to_charging_events_csv):
        return df_columns_to_numeric(pd.read_csv(path_to_charging_events_csv, sep=",", index_col=None, header=0), ['vehicle', 'fuel'])

    if df is None:
        df = get_all_events_from_events_csv(path_to_events_csv)

    print("Parsing refuel events from event.csv...")
    simulation_end_time = df.time.max()
    df_refuel = df[df['type'] == "RefuelSessionEvent"]
    df_refuel = df_refuel.reset_index(drop=True)
    df_refuel = df_refuel.assign(fuelAfterCharging=pd.Series(np.zeros(len(df_refuel.index))))

    # Get fuel after charging
    df_plug_out = df[df['type'] == "ChargingPlugOutEvent"]
    for fuelAfterCharging, time, vehicle in zip(df_plug_out['primaryFuelLevel'], df_plug_out['time'],  df_plug_out['vehicle']):
        df_refuel.loc[df_refuel.time.eq(time) & df_refuel.vehicle.eq(vehicle), 'fuelAfterCharging'] = fuelAfterCharging

    # Look for missing PlugOutEvents
    if add_missing_refuel_events:
        df_plug_in = df[df['type'] == "ChargingPlugInEvent"]
        for index, plug_in_event in df_plug_in.iterrows():
            df_plug_out_filtered_by_vehicle = df_plug_out[df_plug_out.vehicle.eq(plug_in_event['vehicle'])]
            df_following_plug_out_events = df_plug_out_filtered_by_vehicle.loc[df_plug_out_filtered_by_vehicle.time.astype('int32') > int(plug_in_event['time'])]
            if len(df_following_plug_out_events.index) == 0:
                # Add fake refuel session
                # Calculate charged fuel
                vehicle_types = df[df.vehicle.eq(plug_in_event.vehicle)]
                vehicle_type = vehicle_types.loc[vehicle_types['vehicleType'].notnull(), ['vehicleType']].iloc[0].values[0]
                vehicle_battery_capacity_in_j = df[df.vehicleType.eq(vehicle_type)].primaryFuelLevel.max()
                try:
                    max_charging_power = float(plug_in_event.chargingType.split("|")[0].split("(")[1])
                except:
                    max_charging_power = 7.2
                stepsize = 100
                charging_power = calc_avg_charging_power_numeric(plug_in_event.primaryFuelLevel, vehicle_battery_capacity_in_j, max_charging_power, vehicle_battery_capacity_in_j, stepsize)
                max_charging_duration = simulation_end_time - plug_in_event.time
                charging_duration = (vehicle_battery_capacity_in_j - plug_in_event.primaryFuelLevel) / (charging_power * 1000)
                charging_duration = min(charging_duration, max_charging_duration)
                charged_fuel = min(charging_power * charging_duration * 1000, vehicle_battery_capacity_in_j - plug_in_event.primaryFuelLevel)
                fuel_after_charging = plug_in_event.primaryFuelLevel + charged_fuel

                df_refuel = df_refuel.append({
                    'time': simulation_end_time,
                    'type': "RefuelSessionEvent",
                    'vehicle': plug_in_event.vehicle,
                    'vehicleType': 0,
                    'parkingTaz': plug_in_event.parkingTaz,
                    'chargingType': plug_in_event.chargingType,
                    'pricingModel': plug_in_event.pricingModel,
                    'parkingType': plug_in_event.parkingType,
                    'locationX': plug_in_event.locationX,
                    'locationY': plug_in_event.locationY,
                    'price': plug_in_event.price,
                    'fuel': charged_fuel,
                    'duration': charging_duration,
                    'fuelAfterCharging': fuel_after_charging
                }, ignore_index=True)

    # Save analysis data to csv file
    if path_to_charging_events_csv != "" and not path.exists(path_to_charging_events_csv):
        with open(path_to_charging_events_csv, mode='w') as charging_events_file:
            df_refuel.to_csv(charging_events_file, mode='w', header=True, index=False)
    return df_columns_to_numeric(df_refuel, ['vehicle', 'fuel'])


def get_parking_events_from_events_csv(path_to_events_csv="", df=None):
    if df is None:
        df = get_all_events_from_events_csv(path_to_events_csv)
    df_parking = df[df['type'] == "ParkEvent"]
    df_parking = df_parking.reset_index(drop=True)
    return df_columns_to_numeric(df_parking, ['vehicle', 'driver'])


def get_events_with_fuel_level_from_events_csv(path_to_events_csv="", df=None):
    if df is None:
        df = get_all_events_from_events_csv(path_to_events_csv)
    df_events = df[df['primaryFuelLevel'].notnull()]
    df_events = df_events.reset_index(drop=True)
    return df_events


def get_driving_events_from_events_csv(path_to_events_csv="", df=None):
    if df is None:
        df = get_all_events_from_events_csv(path_to_events_csv)
    df_events = df[df['mode'].eq("car") & df['vehicle'].notnull()]
    df_events = df_events.reset_index(drop=True)
    return df_columns_to_numeric(df_events, ['vehicle', 'driver', 'primaryFuelLevel'])


def get_walking_events_from_events_csv(path_to_events_csv="", df=None):
    if df is None:
        df = get_all_events_from_events_csv(path_to_events_csv)
    df_events = df[df['mode'].eq("walk") & df['vehicle'].notnull()]
    df_events = df_events.reset_index(drop=True)
    return df_columns_to_numeric(df_events, ['driver'])


def get_charging_events_from_events_csv(path_to_events_csv="", df=None):
    if df is None:
        df = get_all_events_from_events_csv(path_to_events_csv)
    df_events = df[df['type'].eq("ChargingPlugInEvent") | df['type'].eq("ChargingPlugOutEvent")]
    df_events = df_events.reset_index(drop=True)
    return df_columns_to_numeric(df_events, ['vehicle', 'driver', 'primaryFuelLevel'])


def get_total_walking_distances_from_events_csv(path_to_events_csv="", df_walking_events=None):
    # Check if events already parsed
    path_to_walking_distances_csv = path_to_events_csv.split(".events.")[0] + ".walkingDistances.csv"
    if path.exists(path_to_walking_distances_csv):
        return df_columns_to_numeric(pd.read_csv(path_to_walking_distances_csv, sep=",", index_col=None, header=0), ['person', 'length'])
    if df_walking_events is None:
        df_walking_events = get_walking_events_from_events_csv(path_to_events_csv)
    df_sum = df_walking_events.groupby(['driver']).sum()
    df_sum.person = df_sum.index
    df_result = df_sum[['person', 'length']]


    # Save analysis data to csv file
    if path_to_walking_distances_csv != "" and not path.exists(path_to_walking_distances_csv):
        with open(path_to_walking_distances_csv, mode='w') as charging_events_file:
            df_result.to_csv(charging_events_file, mode='w', header=True, index=False)
    return df_columns_to_numeric(df_result, ['person', 'length'])



def df_columns_to_numeric(df, columns):
    df[columns] = df[columns].apply(pd.to_numeric)
    return df


def parse_event_xml_to_pandas_dataframe_float_time(input_filename, tree=None, ignore_body_vehicles=True):
    if tree is None:
        tree = ET.parse(input_filename)
    root = tree.getroot()
    df = pd.DataFrame(columns=['time', 'departureTime', 'arrivalTime', 'vehicle', 'fuel', 'eventType', 'parkingTaz',
                               'person', 'length'])

    # parse XML
    for event in root:
        if 'primaryFuelLevel' in event.attrib and (
                (ignore_body_vehicles and 'body' not in event.attrib['vehicle']) or (not ignore_body_vehicles)
        ):
            arrival_time = seconds_to_time_string(float(event.attrib['time']))
            departure_time = arrival_time
            parking_taz = 0
            person = ""
            length = 0
            if 'parkingTaz' in event.attrib:
                parking_taz = int(event.attrib['parkingTaz'])
            if event.attrib['type'] == 'PathTraversal':
                arrival_time = seconds_to_time_string(float(event.attrib['arrivalTime']))
                departure_time = seconds_to_time_string(float(event.attrib['departureTime']))
                length = float(event.attrib['length'])
            if 'person' in event.attrib:
                person = event.attrib['person']
            if 'driver' in event.attrib and person == "":
                person = event.attrib['driver']
            df = df.append({
                'time': float(event.attrib['time']),
                'departureTime': departure_time,
                'arrivalTime': arrival_time,
                'vehicle': event.attrib['vehicle'],
                'fuel': float(event.attrib['primaryFuelLevel']) / 3.6 / 10 ** 6,
                'eventType': event.attrib['type'],
                'parkingTaz': parking_taz,
                'person': person,
                'length': length
            }, ignore_index=True)

    return df


def plot_dataframe(df):
    output_filename = "soc_from_events"

    # Plot Data
    fig, ax = plt.subplots()
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    for name, group in df.groupby('vehicle'):
        group.plot(kind='line', x='time', y='fuel', label=name, ax=ax)
        xvals = group['time'].values
        yvals = group['fuel'].values
        ax.scatter(xvals, yvals)

    # Plot settings
    plt.xlabel('Simulation Time in h')
    plt.ylabel('SOC in kW')
    plt.title('SOC of Vehicles')
    plt.grid()

    plt.savefig(output_filename + '.png')
    tikzplotlib.save(output_filename + ".tex")

    plt.show()


def filter_events(input_filename, vehicle_ids, output_filename=None):
    tree = ET.parse(input_filename)
    root = tree.getroot()

    # parse XML
    for parent in tree.iter():
        for child in parent.findall('event'):
            vehicle = 0
            if 'vehicle' in child.attrib:
                try:
                    vehicle = int(child.attrib['vehicle'])
                except ValueError as ex:
                    vehicle = 0
                    if child.attrib['vehicle'] in vehicle_ids:
                        vehicle = child.attrib['vehicle']
            if 'vehicle' not in child.attrib or vehicle not in vehicle_ids:
                parent.remove(child)

    header = '<?xml version="1.0" encoding="utf-8"?>'
    body = ET.tostring(root).decode('utf-8')
    #print(body)

    if output_filename is not None:
        fileHandle = open(outputFile, "w")
        fileHandle.write(header + body)
        fileHandle.close()

    return tree


# specify a date to use for the times
zero = datetime.datetime(2019,12,19)

# Filter
inputFile = 'events/0.events.xml'
outputFile = 'events/0.events.filtered.xml'
vehicleIds = ["22"]
#tree = filter_events(inputFile, vehicleIds, outputFile)

# Plot
#plotData = parse_event_xml_to_pandas_dataframe(outputFile)
#plot_dataframe(plotData)
