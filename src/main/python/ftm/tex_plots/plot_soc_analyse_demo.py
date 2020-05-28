from matplotlib import rc
from matplotlib import pyplot as plt

from python.ftm.filter_plans import filter_plans_by_vehicle_id
from python.ftm.plot_energy_consumption import pyplot_soc_event_based, get_random_vehicle_id
from python.ftm.util import get_latest_run, get_run_dir, range_inclusive, get_iteration_dir

########## CONFIG #############

baseDir = "/data/lucas/SA/Simulation Runs/"
latest_run = 'munich-simple__2020-04-22_11-35-35'
vehicle_id = 370

image_format = 'svg'
first_iteration = 50
last_iteration = 50
iteration_stepsize = 1
max_hour = 72
max_soc = 10
min_soc = 0
plot_engine = 'pyplot' # Options: pyplot, plotly
font = {'size': 15}
rc('font', **font)

run_dir = get_run_dir(baseDir, latest_run)
iterations = range_inclusive(first_iteration, last_iteration, iteration_stepsize)
################

def timestring_to_hour(timestring):
    split_result = timestring.split(':')
    hour = float(split_result[0]) + float(split_result[1])/60
    return hour


def main():
    # 370 schaut gut aus, aber negativer ladezustand
    #120 sehr gut

    #vehicle_id = get_random_vehicle_id(run_dir)
    iteration = first_iteration
    ax = pyplot_soc_event_based(run_dir, iteration, vehicle_id, y_max=max_soc)

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
    ax.legend(['Ladezustand', 'Aktivitätszeitpunkte'])
    ax.set_xlim([0, 72])
    ax.set_xticks(range(0, 72, 10))

    output_path = get_iteration_dir(run_dir, iteration)+'soc_with_activities_vehicle'+str(vehicle_id)+'.'+image_format
    print('Saving figure to path: ', output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()


if __name__ == '__main__':
    main()