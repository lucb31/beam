from matplotlib import rc
from matplotlib import pyplot as plt

########## CONFIG #############
from python.ftm.plot_energy_consumption import pyplot_soc_event_based, plot_soc_dt_pyplot_multiple_iterations
from python.ftm.util import get_run_dir, range_inclusive, get_iteration_dir

baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = 'munich-simple__500agents_72h_1iters_linear_replanning_two_vehicleTypes__2020-05-21_18-12-59'
vehicle_id = 153

image_format = 'svg'
iteration = 0
max_hour = 24
max_soc = 60
min_soc = 0
plot_engine = 'pyplot' # Options: pyplot, plotly
font = {'size': 15}
rc('font', **font)

run_dir = get_run_dir(baseDir, latest_run)
################

def main():
    x_lim = [15, 15.6]
    x_lim = [14.7, 15.2]
    y_lim = [18, 22.5]
    y_lim = [17.5, 20]
    figsize = (8,8)
    legend_loc = 'upper right'
    """
    ax_event_based = pyplot_soc_event_based(
        run_dir, iteration, vehicle_id,
        y_max=max_soc,
        plot_scatter=True,
        x_lim=[0, max_hour],
        y_lim=[0, max_soc],
        figsize=figsize,
        legend=False)
        """
    ax_event_based = plot_soc_dt_pyplot_multiple_iterations(
        run_dir, [iteration], vehicle_id,
        plot_scatter=True,
        y_lim=[0, 10],
        data_source='event',
        x_lim=[0, max_hour],
        figsize=figsize,
        legend=False)
    ax_event_based.set_xlim(x_lim)
    ax_event_based.set_ylim(y_lim)
    ax_event_based.legend(['Eventdaten'], loc=legend_loc)
    output_file = get_iteration_dir(run_dir, iteration) + 'soc_analyse_event_based_vehicle' + str(vehicle_id) + '.'+ image_format
    print('Saving figure to ', output_file)
    plt.savefig(output_file, dpi=300, bbox_inches='tight', pad_inches=0)


    ax_consumption_based = plot_soc_dt_pyplot_multiple_iterations(
        run_dir, [iteration], vehicle_id,
        plot_scatter=True,
        y_lim=[0, 10],
        data_source='consumption',
        x_lim=[0, max_hour],
        figsize=figsize,
        legend=False)
    ax_consumption_based.set_xlim(x_lim)
    ax_consumption_based.set_ylim(y_lim)
    ax_consumption_based.legend(['Verbrauchsdaten'], loc=legend_loc)
    output_file = get_iteration_dir(run_dir, iteration) + 'soc_analyse_consumption_based_vehicle' + str(vehicle_id) + '.'+ image_format
    print('Saving figure to ', output_file)
    plt.savefig(output_file, dpi=300, bbox_inches='tight', pad_inches=0)

    plt.show()

if __name__ == '__main__':
    main()