from matplotlib import rc
from matplotlib import pyplot as plt

from python.ftm.filter_plans import filter_plans_by_vehicle_id
from python.ftm.plot_energy_consumption import pyplot_soc_event_based, get_random_vehicle_id, \
    plot_soc_dt_pyplot_multiple_iterations
from python.ftm.util import get_latest_run, get_run_dir, range_inclusive, get_iteration_dir

########## CONFIG #############

baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = 'munich-simple__2020-04-22_11-35-35'
vehicle_id = 120

image_format = 'svg'
max_hour = 72
max_soc = 10
min_soc = 0
font = {'size': 15}
rc('font', **font)

run_dir = get_run_dir(baseDir, latest_run)
iterations = [0, 1, 25, 50]
################

def timestring_to_hour(timestring):
    split_result = timestring.split(':')
    hour = float(split_result[0]) + float(split_result[1])/60
    return hour


def add_activities_to_soc_plot(ax, iteration):

    filepath_households = run_dir + 'outputHouseholds.xml.gz'
    filepath_plans = get_iteration_dir(run_dir, iteration)+'plans.xml.gz'
    plans_xml = filter_plans_by_vehicle_id(filepath_households, filepath_plans, vehicle_id=vehicle_id)
    for population in plans_xml.iter():
        for person in population.findall('person'):
            for plan in person.findall('plan'):
                if 'selected' in plan.attrib and plan.attrib['selected'] == 'yes':
                    for activity in plan.findall('activity'):
                        type = activity.attrib['type']
                        x = 0
                        if 'end_time' in activity.attrib:
                            endTime = activity.attrib['end_time']
                            x = timestring_to_hour(endTime)
                        if x > 0:
                            ax.axvline(x, color='red', label=type+' Aktivität', linestyle='dashed')
def main():
    # 370 schaut gut aus, aber negativer ladezustand in letzter iter
    # 120 sehr gut, aber zwei ladevorg in it 1
    # 271 auch gut, weil nur leicht negativ am anfang
    #93 gut, aber zacken am ende, verbrauch sehr gering
    vehicle_id = get_random_vehicle_id(run_dir)
    vehicle_id = 370
    axes = plot_soc_dt_pyplot_multiple_iterations(run_dir, iterations, vehicle_id)
    row = 0
    for ax in axes:
        ax.set_xlim([0, 72])
        ax.set_xticks(range(0, 72, 10))
        ax.set_ylim([-25,10])
        ax.axhline(y=0, color='red')
        #add_activities_to_soc_plot(ax, iterations[row])
        row += 1

    output_path = run_dir+'summaryStats/soc_multiple_iterations_vehicle'+str(vehicle_id)+'.'+image_format
    print('Saving figure to path: ', output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()


if __name__ == '__main__':
    main()