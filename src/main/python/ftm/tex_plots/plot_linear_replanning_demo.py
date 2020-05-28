from python.ftm.plot_charger_utilization import plot_util_barplot
from python.ftm.util import get_latest_run, range_inclusive, get_run_dir
from matplotlib import rc

# Config
# Map files
path_to_taz_centers_csv = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-centers.csv"
path_to_taz_parking = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/taz-parking.csv"
path_to_munich_shape = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/shapefiles/munich_area_hybrid_shape.shp"
path_to_munich_polygon = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/munich-polygon.geojson"
path_to_munich_road_masked = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/shapefiles/munich_enclosing_roads_masked.shp"
crs = "EPSG:4326"
taz_centers_crs = "EPSG:31468"

# Sim run data
baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = "munich-simple__500agents_24h_4iters_small_lis_linear_replanning__2020-05-19_14-12-30"
iterations = [0,1,2,3]
max_hour = 24
run_dir = get_run_dir(baseDir, latest_run)

# plot config
compare_iterations = False
show_charger_util = False
show_number_of_charging_vehicles = True
show_activity_types = False
show_heatmap_fuel = False
show_heatmap_avg_fuel = False
show_heatmap_avg_duration = True
show_title = False
plotting_engine = "pyplot" # Options: pyplot, plotly
y_min = 999
y_max = 0
font = {'size': 15}
rc('font', **font)
cmap_name = 'inferno'
color_TUM_BLUE = '#0065BD'


def main():
    plot_util_barplot(run_dir, iterations, y_ticks=[0, 40, 80], legend_loc='upper left', image_format='svg')

if __name__ == '__main__':
    main()
