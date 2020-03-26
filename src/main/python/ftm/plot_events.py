import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import tikzplotlib


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

def get_refuel_events_from_event_xml(input_filename):
    tree = ET.parse(input_filename)
    root = tree.getroot()
    df = pd.DataFrame(columns=['endTime', 'vehicle', 'fuel', 'duration', 'fuelAfterCharging', 'parkingTaz', 'locX', 'locY'])

    # parse XML
    for event in root:
        if 'type' in event.attrib and event.attrib['type'] == 'RefuelSessionEvent':
            df = df.append({
                'endTime': float(event.attrib['time']),
                'vehicle': int(event.attrib['vehicle']),
                'fuel': float(event.attrib['fuel']),
                'duration': float(event.attrib['duration']),
                'fuelAfterCharging': 0.0,
                'parkingTaz': int(event.attrib['parkingTaz']),
                'locX': float(event.attrib['locationX']),
                'locY': float(event.attrib['locationY'])
            }, ignore_index=True)
        if 'type' in event.attrib and event.attrib['type'] == 'ChargingPlugOutEvent':
            if df.endTime.iloc[-1] == float(event.attrib['time']):
                df.fuelAfterCharging.iloc[-1] = float(event.attrib['primaryFuelLevel'])

    return df


def parse_event_xml_to_pandas_dataframe_float_time(input_filename, tree = None, ignore_body_vehicles=True):
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


def seconds_to_time_string(seconds):
    hour = int(seconds / 3600)
    minute = int((seconds - hour * 3600) / 60)
    string = ""
    if hour < 10:
        string += "0"
    string += str(hour) + ":"
    if minute < 10:
        string += "0"
    string += str(minute)
    return string

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
