import geopandas as gpd
import pandas as pd
from matplotlib import pyplot as plt
from shapely.geometry import Point
import geoplot
from os import path
import mapclassify

from python.ftm.plot_events import get_refuel_events_from_events_csv

def mask_munich_road_shape(path_to_munich_shape, path_to_munich_polygon, path_to_munich_road_masked):
    munich_enclosing_roads = gpd.read_file(path_to_munich_shape)
    munich_enclosing_roads.to_crs(crs=crs)
    munich_polygon = gpd.read_file(path_to_munich_polygon)
    munich_polygon.to_crs(crs=crs)
    mask = munich_enclosing_roads.within(munich_polygon.geometry[0])
    munich_enclosing_roads_masked = munich_enclosing_roads[mask]
    munich_enclosing_roads_masked[['osm_id', 'name', 'z_order', 'geometry']].to_file(path_to_munich_road_masked)


### CONFIG ####
pd.set_option('display.max_columns', 500)
plot_unused_cs = False
plot_heatmap = True
plot_all_cs = True
path_to_taz_centers_csv = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-centers.csv"
#path_to_simulation_run = "/data/lucas/SA/Simulation Runs/history/munich-simple__2020-04-15_10-53-58_10000agents_withinday_inactive/"
path_to_simulation_run = "/data/lucas/SA/Simulation Runs/munich-simple_72h_10000agents_50iter__2020-04-28_18-46-18/"
path_to_munich_shape = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/shapefiles/munich_area_hybrid_shape.shp"
path_to_munich_polygon = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/munich-polygon.geojson"
path_to_munich_road_masked = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/shapefiles/munich_enclosing_roads_masked.shp"
crs = "EPSG:4326"
taz_centers_crs = "EPSG:31468"
iteration_start = 0
iteration_end = 23
iteration_step = 5
### END CONFIG ####


# Load map data
print("Loading map data...")
taz_centers = pd.read_csv(path_to_taz_centers_csv)
munich_enclosing_roads_masked = gpd.read_file(path_to_munich_road_masked)
munich_enclosing_roads_masked.to_crs(crs=crs)
munich_polygon = gpd.read_file(path_to_munich_polygon)
munich_polygon.to_crs(crs=crs)
print("...done")
scheme = mapclassify.Quantiles([0,350], k=10)

def scale_within_boundaries(minval, maxval):
    def scalar(val):
        new_scheme = mapclassify.UserDefined([val], bins=scheme.bins)
        bin = new_scheme.yb[0]
        return bin*2 + 5
    return scalar

taz_geometry = [Point(x, y) for x, y in zip(taz_centers['coord-x'], taz_centers['coord-y'])]
for iteration in range(iteration_start, iteration_end, iteration_step):
    print('Iteration '+str(iteration))
    path_to_events_csv = path_to_simulation_run+"ITERS/it."+str(iteration)+"/"+str(iteration)+".events.csv"
    # Load charging event and charging station data
    print("Loading event data ...")
    charging_events = get_refuel_events_from_events_csv(path_to_events_csv)
    print("...done")

    # Aggregate data from taz-centers and events
    print("Aggregating data...")
    sum_df = pd.DataFrame({
        'totalFuel': [0 for i in range(0, len(taz_centers.index))],
        'parkingTaz': taz_centers.taz,
        'geometry': taz_geometry
    })
    for group, df in charging_events.groupby("parkingTaz"):
        fuelSum = df['fuel'].sum()
        sum_df.loc[sum_df['parkingTaz'] == group, 'totalFuel'] = fuelSum
    geo_df = gpd.GeoDataFrame(sum_df, crs=taz_centers_crs)
    geo_df = geo_df.to_crs(crs)
    geo_df['totalFuel'] = geo_df['totalFuel'] / 3.6e6       # Joule to kWh
    print("...done")

    # Filter by polygon shape
    print("Filtering charging events by polygon shape ...")
    mask = geo_df.geometry.within(munich_polygon.geometry.to_crs(crs)[0])
    geo_df_masked = geo_df[mask]
    print("...location data done")

    # Plot points, polygon border shape and road network
    if geo_df_masked.totalFuel.max() > 0:
        ax = geoplot.pointplot(
            geo_df_masked,
            hue='totalFuel', scheme=scheme, cmap='inferno',
            legend=True, legend_var='hue',
            scale='totalFuel', limits=(5, 20), scale_func=scale_within_boundaries,
            figsize=(12, 6))
    else:
        ax = geoplot.pointplot(
            geo_df_masked,
            color='black',
            #legend=True, hue='totalFuel', scale='totalFuel', limits=(5, 20), cmap='inferno', legend_var='hue',
            figsize=(12, 6))
    geoplot.polyplot(munich_polygon, ax=ax, zorder=1)
    munich_enclosing_roads_masked.plot(ax=ax, alpha=0.4, color='grey')
    plot_title = 'Übertragene Energie pro Ladestation (Iteration '+str(iteration)+')'
    plt.title(plot_title)
    plt.savefig('/data/lucas/SA/tmp/13_heatmap_iteration'+str(iteration)+'.png')

plt.show()

"""
geometry = [Point(x, y) for x, y in zip(charging_events['locationX'], charging_events['locationY'])]
geo_charging_events = gpd.GeoDataFrame(charging_events.fuel, geometry=geometry)
ax = geoplot.kdeplot(
    geo_charging_events, clip=munich_polygon.geometry,
    n_levels=100, cmap='Reds', shade=True#, scale='fuel'
    #projection=geoplot.crs.AlbersEqualArea()
)
"""
