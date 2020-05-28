from matplotlib import rc
from matplotlib import pyplot as plt

########## CONFIG #############
from python.ftm.plot_energy_consumption import plot_soc_dt_pyplot_multiple_vehicles
from python.ftm.util import get_run_dir, get_iteration_dir

baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = 'munich-simple__500agents_72h_1iters_linear_replanning_two_vehicleTypes__2020-05-21_18-12-59'
vehicle_ids = [153, 425]

image_format = 'svg'
iteration = 1
max_hour = 72
max_soc = 60
min_soc = 0
plot_engine = 'pyplot' # Options: pyplot, plotly
font = {'size': 15}
rc('font', **font)

run_dir = get_run_dir(baseDir, latest_run)
################

def main():
    ax = plot_soc_dt_pyplot_multiple_vehicles(run_dir, iteration, vehicle_ids, y_lim=[0, 60])
    ax[0].legend(['Smart'], loc='upper left')
    ax[1].legend(['Tesla'], loc='lower left')
    output_path = get_iteration_dir(run_dir, iteration) + 'vehicle_consumption_comparison.' + image_format
    print('Saving figure to ', output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)

    ax_zoomed = plot_soc_dt_pyplot_multiple_vehicles(run_dir, iteration, vehicle_ids, zoom=True)
    ax_zoomed[0].set_xlim([15, 15.6])
    ax_zoomed[0].set_ylim([18, 23])
    ax_zoomed[1].set_xlim([60.5,61.5])
    ax_zoomed[1].set_ylim([45,52])
    ax_zoomed[0].legend(['Smart'], loc='upper right')
    ax_zoomed[1].legend(['Tesla'], loc='upper right')
    output_path = get_iteration_dir(run_dir, iteration) + 'vehicle_consumption_comparison_zoomed.' + image_format
    print('Saving figure to ', output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)

    plt.show()
    pass

if __name__ == '__main__':
    main()