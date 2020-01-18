import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import tikzplotlib

def get_refuel_events_from_event_xml(input_filename):
    tree = ET.parse(input_filename)
    root = tree.getroot()
    df = pd.DataFrame(columns=['endTime', 'vehicle', 'fuel', 'duration'])

    # parse XML
    for event in root:
        if 'type' in event.attrib and event.attrib['type'] == 'RefuelSessionEvent':
            df = df.append({
                'endTime': float(event.attrib['time']),
                'vehicle': event.attrib['vehicle'],
                'fuel': float(event.attrib['fuel']),
                'duration': float(event.attrib['duration']),
            }, ignore_index=True)

    return df

def parse_event_xml_to_pandas_dataframe(input_filename):
    tree = ET.parse(input_filename)
    root = tree.getroot()
    df = pd.DataFrame(columns=['time', 'vehicle', 'fuel'])

    # parse XML
    for event in root:
        if 'primaryFuelLevel' in event.attrib and not 'body' in event.attrib['vehicle']:
            time = zero + datetime.timedelta(seconds=float(event.attrib['time']))
            time = mdates.date2num(time)
            df = df.append({
                'time': time,
                'vehicle': event.attrib['vehicle'],
                'fuel': float(event.attrib['primaryFuelLevel']) / 3.6 / 10 ** 6
            }, ignore_index=True)

    return df

def parse_event_xml_to_pandas_dataframe_float_time(input_filename):
    tree = ET.parse(input_filename)
    root = tree.getroot()
    df = pd.DataFrame(columns=['time', 'vehicle', 'fuel'])

    # parse XML
    for event in root:
        if 'primaryFuelLevel' in event.attrib and not 'body' in event.attrib['vehicle']:
            df = df.append({
                'time': float(event.attrib['time']),
                'vehicle': event.attrib['vehicle'],
                'fuel': float(event.attrib['primaryFuelLevel']) / 3.6 / 10 ** 6
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
            if 'vehicle' not in child.attrib or child.attrib['vehicle'] not in vehicle_ids:
                parent.remove(child)

    header = '<?xml version="1.0" encoding="utf-8"?>'
    body = ET.tostring(root).decode('utf-8')
    #print(body)

    if output_filename is not None:
        fileHandle = open(outputFile, "w")
        fileHandle.write(header + body)
        fileHandle.close()

    return tree

def plot_refuel_events_over_duration(dfs):
    df = dfs[0]

    # Plot Data
    fig, ax = plt.subplots(3,1, figsize=(12,12))
    title = 'Vehicle energy charged for different refuel events'
    markerSize = 10

    for df in dfs:
        print()
        xvals = df['duration'].values / 60
        yvals = df['fuel'].values / 3.6e6
        ax[0].scatter(xvals, yvals, label=df['chargingType'].iloc[0], s=markerSize)

        yvals = df['fuel'].values / df['duration'].values / 1000
        ax[1].scatter(xvals, yvals, label=df['chargingType'].iloc[0], s=markerSize)

        xvals = df['fuel'].values / 3.6e6
        yvals = df['fuel'].values / df['duration'].values / 1000
        ax[2].scatter(xvals, yvals, label=df['chargingType'].iloc[0], s=markerSize)

    ax[0].set_xlabel('Refueling duration in min')
    ax[0].set_ylabel('Refueled energy in kWh')
    ax[0].set_title(title)
    ax[0].legend()
    ax[1].set_xlabel('Refueling duration in min')
    ax[1].set_ylabel('Average charging power in kW')
    ax[1].set_title(title)
    ax[1].legend()
    ax[2].set_xlabel('Charged energy in kWh')
    ax[2].set_ylabel('Average charging power in kW')
    ax[2].set_title(title)
    ax[2].legend()

    plt.grid()
    plt.show()

# specify a date to use for the times
zero = datetime.datetime(2019,12,19)

# Filter
#inputFile = 'events/0.events.xml'
#outputFile = 'events/0.events.filtered.xml'
#vehicleIds = ["22"]
#tree = filter_events(inputFile, vehicleIds, outputFile)

# Plot
#plotData = parse_event_xml_to_pandas_dataframe(outputFile)
#plot_dataframe(plotData)
