import geopandas as gpd
import pandas as pd
from matplotlib import pyplot as plt
from shapely.geometry import Point
import geoplot
from os import path
import mapclassify
import contextily as ctx
from matplotlib import cm
import numpy as np

from python.ftm.analyze_events import get_refuel_events_from_events_csv
from python.ftm.util import get_latest_run, get_run_dir, range_inclusive

### CONFIG ####

pd.set_option('display.max_columns', 500)
path_to_taz_centers_csv = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-centers.csv"
path_to_taz_parking_csv = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-parking.csv"
baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = get_latest_run(baseDir)
#latest_run = "munich-simple__500agents_72h_30iters__2020-05-13_10-56-07"
path_to_simulation_run = get_run_dir(baseDir, latest_run)
output_prefix = '/data/lucas/SA/tmp/heatmap'
#path_to_simulation_run = "/data/lucas/SA/Simulation Runs/munich-simple_72h_10000agents_50iter__2020-04-28_18-46-18/"
path_to_munich_shape = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/shapefiles/munich_area_hybrid_shape.shp"
path_to_munich_polygon = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/munich-polygon.geojson"
path_to_munich_road_masked = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/shapefiles/munich_enclosing_roads_masked.shp"
crs = "EPSG:4326"
taz_centers_crs = "EPSG:31468"
iteration_start = 1
iteration_end = 1
iteration_step = 1
use_small_lis = True
cmap_name = 'inferno'
color_TUM_BLUE = '#0065BD'
plot_only_chargers = False
plot_total_fuel = True
plot_avg_duration = False
plot_avg_fuel = False
show_title = False
# Small LIS
if use_small_lis:
    path_to_taz_centers_csv = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-centers-small.csv"
    path_to_taz_parking_csv = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-parking-small.csv"

### END CONFIG ####


def mask_munich_road_shape(path_to_munich_shape, path_to_munich_polygon, path_to_munich_road_masked):
    munich_enclosing_roads = gpd.read_file(path_to_munich_shape)
    munich_enclosing_roads.to_crs(crs=crs)
    munich_polygon = gpd.read_file(path_to_munich_polygon)
    munich_polygon.to_crs(crs=crs)
    mask = munich_enclosing_roads.within(munich_polygon.geometry[0])
    munich_enclosing_roads_masked = munich_enclosing_roads[mask]
    munich_enclosing_roads_masked[['osm_id', 'name', 'z_order', 'geometry']].to_file(path_to_munich_road_masked)


def scale_within_boundaries(minval, maxval):
    def scalar(val):
        new_scheme = mapclassify.UserDefined([val], bins=scheme.bins)
        bin = new_scheme.yb[0]
        return bin*2 + 5
    return scalar


def scale_by_scheme(val, scheme):
    new_scheme = mapclassify.UserDefined([val], bins=scheme.bins)
    bin = new_scheme.yb[0]
    return (bin*2 + 5)*6


def main():
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
    for iteration in range_inclusive(iteration_start, iteration_end, iteration_step):
        print('Iteration '+str(iteration))
        path_to_events_csv = path_to_simulation_run+"ITERS/it."+str(iteration)+"/"+str(iteration)+".events.csv"
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
    for iteration in range_inclusive(iteration_start, iteration_end, iteration_step):
        geo_df_masked = plot_dataframes_collection[iteration]
        geo_df_masked = geo_df_masked.to_crs(epsg=3857)
        chargers = geo_df_masked.centroid.geometry.values
        x_c = [c.x for c in chargers]
        y_c = [c.y for c in chargers]
        if plot_total_fuel:
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
            if plot_only_chargers and iteration == 0:
                # Hide Colorbar
                ax.scatter(x_c, y_c, marker="o", c=color_TUM_BLUE, s=sizes)
                ctx.add_basemap(ax)
            else:
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
            plt.savefig(output_prefix+str(iteration)+'_totalFuel.png', dpi=300, bbox_inches='tight', pad_inches=0)

        if plot_avg_duration:
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
            plt.savefig(output_prefix+str(iteration)+'_avgDuration.png', dpi=300, bbox_inches='tight', pad_inches=0)

        if plot_avg_fuel:
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
            plt.savefig(output_prefix+str(iteration)+'_avgFuel.png', dpi=300, bbox_inches='tight', pad_inches=0)

    plt.show()


if __name__ == '__main__':
    main()
"""
geometry = [Point(x, y) for x, y in zip(charging_events['locationX'], charging_events['locationY'])]
geo_charging_events = gpd.GeoDataFrame(charging_events.fuel, geometry=geometry)
ax = geoplot.kdeplot(
    geo_charging_events, clip=munich_polygon.geometry,
    n_levels=100, cmap='Reds', shade=True#, scale='fuel'
    #projection=geoplot.crs.AlbersEqualArea()
)
"""
