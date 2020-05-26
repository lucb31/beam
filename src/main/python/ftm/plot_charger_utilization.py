import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from matplotlib import pyplot as plt
from matplotlib import rc
import numpy as np
import os

from python.ftm.analyze_events import get_refuel_events_from_events_csv, get_total_walking_distances_from_events_csv, \
    get_parking_events_from_events_csv, get_all_events_from_events_csv, df_columns_to_numeric
from python.ftm.util import get_run_dir, get_latest_run, get_iteration_dir, get_last_iteration, range_inclusive

####### CONFIG
path_to_taz_parking = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-parking.csv"
baseDir = "/home/lucas/IdeaProjects/beam/output/munich-simple/"
baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = get_latest_run(baseDir)
#latest_run = "munich-simple__500agents_72h_30iters__2020-05-13_10-56-07"
first_iteration = 1
last_iteration = 1
max_hour = 24
step_size = 1
run_dir = get_run_dir(baseDir, latest_run)
compare_iterations = False
show_charger_util = False
show_number_of_charging_vehicles = True
show_activity_types = False
show_title = False
plotting_engine = "pyplot" # Options: pyplot, plotly
path_to_output_png_charger_util = '/home/lucas/IdeaProjects/beam/output/' + "charger_utilization_barplot.png"
path_to_output_png_number_charging_multiple_iterations = '/home/lucas/IdeaProjects/beam/output/' + "number_charging_multiple_iterations.png"
ytitle = "Transferred energy in kwh"
y_min = 999
y_max = 0
font = {'size': 15}
rc('font', **font)
###########


def get_plotdata_charging_vehicles(iteration):
    # Setup directory
    working_dir = get_iteration_dir(run_dir, iteration)
    print("-------------- ITERATION", iteration, "--------------------")
    print("Working on path: ", working_dir)

    if os.path.exists(working_dir + "chargingNumberVehicles.csv"):
        plot_data = pd.read_csv(working_dir + "chargingNumberVehicles.csv")
    else:
        plot_data = pd.DataFrame({'x': [], 'charging-vehicle': []})

    plot_data = df_columns_to_numeric(plot_data, ['x', 'charging-vehicle'])
    if len(plot_data[plot_data['x'] == 0].index) == 0:
        plot_data =  plot_data.append({
            'x': 0,
            'charging-vehicle': 0
        }, ignore_index=True)
    if len(plot_data[plot_data['x'] == max_hour].index) == 0:
        plot_data =  plot_data.append({
            'x': max_hour,
            'charging-vehicle': 0
        }, ignore_index=True)
    plot_data = plot_data.sort_values(by=['x'])
    return plot_data


def plot_iteration(iteration):
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
    df_refueling_sum = df_events_refueling.groupby('parkingTaz').sum()
    if len(df_refueling_sum.index) > 0:
        x = df_refueling_sum.index
        y = df_refueling_sum.fuel / 3.6e6
    else:
        x = pd.Series()
        y = pd.Series()

    # TODO Normalize
    """
    def my_func(value, taz):
        return value / df_taz_info[df_taz_info['taz'] == int(taz)].numStalls.iloc[0]
    df_taz_info = pd.read_csv(path_to_taz_parking)
    for index, value in y.items():
        y.iloc[int(index)] = my_func(value, index)
    """

    """
    # Print parking events
    df_parking = get_parking_events_from_events_csv(working_dir + "events.csv")
    df_parking_group = df_parking.groupby('parkingTaz')
    for name, group in df_parking_group:
        print("TAZ ", name, "has ", len(group.index), "parking events")
    """
    return x, y

def plot_util_barplot():
    global last_iteration
    num_rows = int(last_iteration / step_size) + 1
    if last_iteration % step_size > 0:
        num_rows += 1
    if last_iteration == first_iteration:
        num_rows = 1
    col = 1
    y_min = 999999
    y_max = 0
    if plotting_engine == 'pyplot':
        fig, ax = plt.subplots(num_rows, col, sharex=True, sharey=True)
        row = 0
        for iteration in range_inclusive(first_iteration, last_iteration, step_size):
            (x, y) = plot_iteration(iteration)
            ax[row].bar(x, y, label='Iteration '+str(iteration))
            ax[row].legend(loc='upper left')
            #ax[row].plot(pd.Series([0, x.max()]), pd.Series([y.mean(), y.mean()]), label="Iteration " + str(iteration) + " Durchschnitt")
            print('Iteration ', iteration, ', avg ', y.mean(), 'kWh')
            row += 1

        # add a big axis, hide frame
        fig.add_subplot(111, frameon=False)
        # hide tick and tick label of the big axis
        plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
        plt.xlabel("Parkzone der Ladestation")
        plt.ylabel("Übertragene Energie in kWh")
        print('Saving figure to', path_to_output_png_charger_util)
        plt.savefig(path_to_output_png_charger_util, dpi=300, bbox_inches='tight', pad_inches=0)
        plt.show()
    else:
        plotly_figure = make_subplots(rows=num_rows, cols=1, subplot_titles=subplot_titles, shared_xaxes=True, vertical_spacing=0.02)
        row = 1
        for iteration in range_inclusive(first_iteration, last_iteration, step_size):
            (x, y) = plot_iteration(iteration)
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
            if y.min() < y_min: y_min = y.min()
            if y.max() > y_max: y_max = y.max()
            row += 1

        for y_axis in range(1, row):
            plotly_figure['layout']['yaxis'+str(y_axis)].update(title=ytitle)
            plotly_figure['layout']['yaxis'+str(y_axis)].update(range=[0, y_max * 1.1])

        plotly_figure['layout']['xaxis'+str(row-1)].update(title="Charging TAZ")
        plotly_figure['layout']['xaxis'+str(row-1)].update(range=[100, 700])
        plotly_figure.update_layout(
            title_text="Charger utilization for simulation "+latest_run,
            height=350
        )
        plotly_figure.show()



def plot_charging_vehicles():
    global last_iteration
    num_rows = int(last_iteration / step_size) + 1
    if last_iteration % step_size > 0:
        num_rows += 1
    if last_iteration == first_iteration:
        num_rows = 1
    y_min = 0
    y_max = 0
    col = 1
    x_title = 'Hour'
    y_title = '# of charging vehicles'

    # Get min max values
    for iteration in range_inclusive(first_iteration, last_iteration, step_size):
        working_dir = get_iteration_dir(run_dir, iteration)
        if os.path.exists(working_dir + "chargingNumberVehicles.csv"):
            plot_data = pd.read_csv(working_dir + "chargingNumberVehicles.csv")
            if len(plot_data.index) > 0:
                if plot_data['charging-vehicle'].min() < y_min: y_min = plot_data['charging-vehicle'].min()
                if plot_data['charging-vehicle'].max() > y_max: y_max = plot_data['charging-vehicle'].max()

    if plotting_engine == 'pyplot':
        fig, axes = plt.subplots(num_rows, col, sharex=True, sharey=True, figsize=(8,8))
        row = 0
        iteration = first_iteration
        for iteration in range_inclusive(first_iteration, last_iteration, step_size):
            plot_data = get_plotdata_charging_vehicles(iteration)
            if last_iteration > first_iteration:
                ax = axes[row]
            else:
                ax = axes
            ax.plot(plot_data['x'], plot_data['charging-vehicle'], label='Iteration '+str(iteration))
            ax.legend(loc='upper left')
            ax.set_xlim([0, max_hour])
            ax.set_ylim([y_min, y_max*1.1])
            ax.grid(axis='y', linestyle='--')
            row += 1

        # add a big axis, hide frame
        fig.add_subplot(111, frameon=False)
        # hide tick and tick label of the big axis
        plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
        plt.xlabel("Simulationszeit in Stunden")
        plt.ylabel("Anzahl der ladenden Fahrzeuge")
        if show_title:
            plt.title('Iteration '+str(iteration)+', '+latest_run)
        path_to_output_png = run_dir+'summaryStats/number_charging_multiple_iterations.png'
        print('Saving figure to ', path_to_output_png)
        plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)
        plt.show()
    else:
        plotly_figure = make_subplots(rows=num_rows, cols=1, subplot_titles=subplot_titles, shared_xaxes=True, vertical_spacing=0.02)
        row = 1
        for iteration in range_inclusive(first_iteration, last_iteration, step_size):
            plot_data = get_plotdata_charging_vehicles(iteration)

            plotly_figure.add_trace(
                go.Line(
                    x=plot_data['x'],
                    y=plot_data['charging-vehicle'],
                    name="It " + str(iteration) + ""
                ),
                row=row,
                col=col
            )
            plotly_figure['layout']['yaxis'+str(row)].update(title=ytitle)
            plotly_figure['layout']['yaxis'+str(row)].update(range=[0, y_max * 1.1])
            row += 1

        plotly_figure['layout']['xaxis'+str(row-1)].update(title=x_title)
        plotly_figure['layout']['xaxis'+str(row-1)].update(range=[0, max_hour])
        plotly_figure.update_layout(
            title_text="Number of charging vehicles for simulation "+latest_run,
            height=350*num_rows
        )
        plotly_figure.show()


def plot_charging_events():
    for iteration in range_inclusive(first_iteration, last_iteration, step_size):
        working_dir = get_iteration_dir(run_dir, iteration)
        plot_data = pd.read_csv(working_dir + "activityType.csv")
        fig, ax = plt.subplots(figsize=(8,6))
        for col in plot_data.columns:
            if not col == 'x':
                ax.plot(plot_data['x'], plot_data[col], label=str(col))
        ax.set_xlabel('Hour')
        ax.set_ylabel('Number of agents')
        ax.set_xlim([0, max_hour])
        ax.grid(axis='y', linestyle='--')
        plt.legend()
        plt.title('Activity Type')
        path_to_output_png = working_dir + "activityType_fixedScaling.png"
        print('Saving figure to ', path_to_output_png)
        plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)
        plt.show()



def plot_heatmaps(show_total_fuel = True, show_avg_duration = False, show_avg_fuel = False):
    # Load map data
    print("Loading map data...")
    taz_centers = pd.read_csv(path_to_taz_centers_csv)
    taz_parking = pd.read_csv(path_to_taz_parking_csv)
    #munich_enclosing_roads_masked = gpd.read_file(path_to_munich_road_masked)
    #munich_enclosing_roads_masked.to_crs(crs=crs)
    munich_polygon = gpd.read_file(path_to_munich_polygon)
    munich_polygon.to_crs(crs=crs)
    taz_geometry = [Point(x, y) for x, y in zip(taz_centers['coord-x'], taz_centers['coord-y'])]
    print("...done")

    total_fuel_max = 0
    avg_duration_max = 0
    avg_fuel_max = 0
    plot_dataframes_collection = {}
    for iteration in iterations:
        working_dir = get_iteration_dir(run_dir, iteration)
        output_prefix = working_dir + 'heatmap_'
        print('Working dir:  '+str(working_dir))
        path_to_events_csv = working_dir+"events.csv"
        # Load charging event and charging station data
        print('Loading event data from ', path_to_events_csv, '...')
        charging_events = get_refuel_events_from_events_csv(path_to_events_csv)
        print("...done")

        # Aggregate data from taz-centers and events
        print("Aggregating data...")
        sum_df = pd.DataFrame({
            'totalFuel': np.zeros(len(taz_centers.index)),
            'totalDuration': np.zeros(len(taz_centers.index)),
            'avgDuration': np.zeros(len(taz_centers.index)),
            'avgFuel': np.zeros(len(taz_centers.index)),
            'eventCount': np.zeros(len(taz_centers.index)),
            'parkingTaz': taz_centers.taz,
            'numStalls': taz_parking.numStalls,
            'geometry': taz_geometry
        })
        for group, df in charging_events.groupby("parkingTaz"):
            fuelSum = df['fuel'].sum()
            duration_sum = df['duration'].sum()

            # Normalize by number of stalls
            fuelSum = fuelSum / sum_df.loc[sum_df['parkingTaz'] == group, 'numStalls']

            sum_df.loc[sum_df['parkingTaz'] == group, 'totalFuel'] = fuelSum
            sum_df.loc[sum_df['parkingTaz'] == group, 'totalDuration'] = duration_sum
            sum_df.loc[sum_df['parkingTaz'] == group, 'eventCount'] = len(df.index)
            sum_df.loc[sum_df['parkingTaz'] == group, 'avgDuration'] = duration_sum / len(df.index)
            sum_df.loc[sum_df['parkingTaz'] == group, 'avgFuel'] = fuelSum / len(df.index)
        geo_df = gpd.GeoDataFrame(sum_df, crs=taz_centers_crs)
        geo_df = geo_df.to_crs(crs)
        # Unit conversions
        geo_df['totalFuel'] = geo_df['totalFuel'] / 3.6e6       # Joule to kWh
        geo_df['avgFuel'] = geo_df['avgFuel'] / 3.6e6       # Joule to kWh
        geo_df['avgDuration'] = geo_df['avgDuration'] / 60       # seconds to minutes
        print('Total fuel transferred: ', geo_df.totalFuel.sum(), 'kWh')
        print("...done")

        # Filter by polygon shape
        print("Filtering charging events by polygon shape ...")
        mask = geo_df.geometry.within(munich_polygon.geometry.to_crs(crs)[0])
        geo_df_masked = geo_df[mask]
        print("...location data done")

        # Update max values
        if geo_df_masked.totalFuel.max() > total_fuel_max:
            total_fuel_max = geo_df_masked.totalFuel.max()
        if geo_df_masked.avgDuration.max() > avg_duration_max:
            avg_duration_max = geo_df_masked.avgDuration.max()
        if geo_df_masked.avgFuel.max() > avg_fuel_max:
            avg_fuel_max = geo_df_masked.avgFuel.max()

        # Save to shapefile and dataframe
        geo_df_masked.to_file(output_prefix+str(iteration)+'.shp')
        plot_dataframes_collection[iteration] = geo_df_masked

    # Plot points and basemap
    for iteration in iterations:
        geo_df_masked = plot_dataframes_collection[iteration]
        geo_df_masked = geo_df_masked.to_crs(epsg=3857)
        chargers = geo_df_masked.centroid.geometry.values
        x_c = [c.x for c in chargers]
        y_c = [c.y for c in chargers]
        if show_total_fuel:
            fig, ax = plt.subplots(figsize=(12, 9))
            scheme = mapclassify.Quantiles([0, total_fuel_max], k=10)
            """
            # Plot all values
            values = [totalFuel for totalFuel in zip(geo_df_masked.totalFuel)]
            sizes = [scale_by_scheme(totalFuel, scheme) for totalFuel in values]
            """
            # Plot null values
            geo_df_masked_null = geo_df_masked[geo_df_masked.totalFuel == 0]
            chargers = geo_df_masked_null.centroid.geometry.values
            x_c = [c.x for c in chargers]
            y_c = [c.y for c in chargers]
            values = [totalFuel for totalFuel in zip(geo_df_masked_null.totalFuel)]
            sizes = [scale_by_scheme(totalFuel, scheme) for totalFuel in values]
            ax.scatter(x_c, y_c, marker="o", c='grey', s=sizes)

            # Only plot not null values
            geo_df_masked_not_null = geo_df_masked[geo_df_masked.totalFuel > 0]
            chargers = geo_df_masked_not_null.centroid.geometry.values
            x_c = [c.x for c in chargers]
            y_c = [c.y for c in chargers]
            values = [totalFuel for totalFuel in zip(geo_df_masked_not_null.totalFuel)]
            sizes = [scale_by_scheme(totalFuel, scheme) for totalFuel in values]
            ax.scatter(x_c, y_c, marker="o", c=values, cmap=cmap_name, s=sizes)
            ctx.add_basemap(ax)

            # Add Colorbar
            sm = plt.cm.ScalarMappable(cmap=cmap_name, norm=plt.Normalize(vmin=0, vmax=total_fuel_max))
            sm.set_array([])
            cbar = plt.colorbar(sm, orientation="horizontal", pad=0.02, aspect=40)
            cbar.set_label("Übertragene Energie in kWh")
            cbar.orientation = "horizontal"

            plot_title = 'Übertragene Energie pro Ladepunkt (Iteration '+str(iteration)+', '+latest_run+')'
            if show_title:
                plt.title(plot_title)
            plt.xticks([], [])
            plt.yticks([], [])
            ax.set_axis_off()
            path_to_output_png = output_prefix+'totalFuel.png'
            print('Saving fig to ', path_to_output_png)
            plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)

        if show_avg_duration:
            scheme = mapclassify.Quantiles([0, avg_duration_max], k=10)
            values = [avg_duration for avg_duration in zip(geo_df_masked.avgDuration)]
            sizes = [scale_by_scheme(value, scheme) for value in values]

            fig, ax = plt.subplots(figsize=(12, 9))
            ax.scatter(x_c, y_c, marker="o", c=values, cmap=cmap_name, s=sizes)
            ctx.add_basemap(ax)

            # Add Colorbar
            sm = plt.cm.ScalarMappable(cmap=cmap_name, norm=plt.Normalize(vmin=0, vmax=avg_duration_max))
            sm.set_array([])
            cbar = plt.colorbar(sm, orientation="horizontal", pad=0.02, aspect=40)
            cbar.set_label("Durchschnittliche Ladedauer in Minuten ")
            cbar.orientation = "horizontal"

            plot_title = 'Durchschnittliche Ladedauer eines Ladevorgangs (Iteration '+str(iteration)+')'
            if show_title:
                plt.title(plot_title)
            plt.xticks([], [])
            plt.yticks([], [])
            ax.set_axis_off()
            path_to_output_png = output_prefix+'avgDuration.png'
            print('Saving fig to ', path_to_output_png)
            plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)

        if show_avg_fuel:
            scheme = mapclassify.Quantiles([0, avg_fuel_max], k=10)
            values = [val for val in zip(geo_df_masked.avgFuel)]
            sizes = [scale_by_scheme(value, scheme) for value in values]

            fig, ax = plt.subplots(figsize=(12, 9))
            ax.scatter(x_c, y_c, marker="o", c=values, cmap=cmap_name, s=sizes)
            ctx.add_basemap(ax)

            # Add Colorbar
            sm = plt.cm.ScalarMappable(cmap=cmap_name, norm=plt.Normalize(vmin=0, vmax=avg_fuel_max))
            sm.set_array([])
            cbar = plt.colorbar(sm, orientation="horizontal", pad=0.02, aspect=40)
            cbar.set_label("Durchschnittliche Energiemenge in kWh ")
            cbar.orientation = "horizontal"

            plot_title = 'Durchschnittliche übertragene Energiemenge eines Ladevorgangs (Iteration '+str(iteration)+')'
            if show_title:
                plt.title(plot_title)
            plt.xticks([], [])
            plt.yticks([], [])
            ax.set_axis_off()
            path_to_output_png = output_prefix+'avgFuel.png'
            print('Saving fig to ', path_to_output_png)
            plt.savefig(path_to_output_png, dpi=300, bbox_inches='tight', pad_inches=0)

    plt.show()


def main():
    subplot_titles = ["Iteration "+str(iteration) for iteration in range_inclusive(first_iteration, last_iteration, step_size)]

    if show_charger_util:
        plot_util_barplot()

    if show_number_of_charging_vehicles:
        plot_charging_vehicles()

    if show_activity_types:
        plot_charging_events()

    if False:
        last_iteration = get_last_iteration(run_dir)
        plotly_figure = make_subplots(rows=1, cols=1, subplot_titles=("Iteration " + str(last_iteration), ""), shared_xaxes=True, vertical_spacing=0.02)
        plot_iteration(last_iteration, 1, 1, plotly_figure)


if __name__ == '__main__':
    main()

