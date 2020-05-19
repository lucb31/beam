import matplotlib.pyplot as plt
import matplotlib.ticker
import tikzplotlib
import locale
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from scipy.interpolate import griddata

colors=['#0065BD', '#003359', '#98C6EA', '#7F7F7F', '#CCCCCC', '#A2AD00', '#E37222']
legend_loc = "center"
legend_bbox_to_anchor = (-0.1, 0)


def plot_pie_with_annotations(sizes, labels, startangle=-90):
    sizes_sum = sum(sizes)
    annotations = ['{:.1f} %'.format(size / sizes_sum * 100) for size in sizes]

    fig, ax = plt.subplots(figsize=(9,6))
    wedges, texts = ax.pie(sizes, startangle=startangle, colors=colors
                           # , wedgeprops=dict(width=0.5)
                           )
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
              zorder=0, va="center",
              # bbox=bbox_props
              )
    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1) / 2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        # ax.annotate(annotations[i], xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
        ax.annotate(annotations[i], xy=(x, y), xytext=(1.1 * np.sign(x), 1.1 * y),
                    horizontalalignment=horizontalalignment, fontsize=20, **kw)
    ax.legend(labels, loc="center", ncol=2, bbox_to_anchor=(0.5, -0.18), fontsize=20)
    return fig, ax


def plot_fahrzeugklassen():
    # Utility, Vans to Sonstige
    # Obere Mittelklasse to Mittelklasse
    labels = ['Mini', 'Kleinwagen', 'Kompaktklasse', 'Mittelklasse', 'Oberklasse', 'SUV', 'Sportwagen', 'Geländewagen', 'Sonstige']
    sizes = [22735, 60559, 55212, 29854, 12473, 28611, 1749, 9686, 9866]
    # Mini to Sonstige
    labels= ['Kleinwagen', 'Kompaktklasse', 'Mittelklasse', 'Oberklasse', 'SUV', 'Sportwagen', 'Geländewagen', 'Sonstige']
    sizes = [83294, 55212, 29854, 12473, 28611, 1749, 9686, 9866]
    #Kompakt to Mittel
    labels= ['Kleinwagen', 'Mittelklasse', 'Oberklasse',   'SUV', 'Sportwagen',    'Geländewagen', 'Sonstige']
    sizes = [83294,         85066,          12473,          28611, 1749,            9686,           9866]
    #Sport to Sonstige
    labels= ['Kleinwagen', 'Mittelklasse', 'Oberklasse',   'SUV', 'Geländewagen', 'Sonstige']
    sizes = [83294,         85066,          12473,          28611, 9686,           11615]
    # Sorted
    labels= ['Mittelklasse', 'Kleinwagen', 'SUV',   'Oberklasse','Sonstige', 'Geländewagen']
    sizes = [85066,         83294,         28611,   12473,        11615, 9686]

    fig, ax = plot_pie_with_annotations(sizes, labels, 45)

    plt.axis('equal')
    #plt.title("Fahrzeugklassen von Elektro-PKw in Deutschland 2019")
    plt.savefig('output/bev-fahrzeugklassen.png', dpi=300, bbox_inches='tight', pad_inches=0)
    #tikzplotlib.save("bev-fahrzeugklassen.tex")


def plot_verteilung_ladestationen():
    # Handel = Handel + Automobilhändler
    # Gastronomie = Hotel + Restaurant
    labels = ['Parkplatz/-haus', 'Öff. Straße', 'Handel', 'Gastronomie', 'Unternehmen', 'Autobahn', 'Sonstige']
    sizes = [24.7, 12.8, 6.9+6, 7.2+1.9, 6.8, 2.6]
    sizes.append(100 - sum(sizes)) # fill sonstige

    fig, ax = plot_pie_with_annotations(sizes, labels, 90)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    #plt.title("Verteilung der Ladestationen in Deutschland")
    plt.savefig("output/verteilung-ladestationen-deutschland.png", dpi=300, bbox_inches='tight', pad_inches=0)


def format_big_number(number):
    return '{:,}'.format(number).replace(',', '.')


def plot_neuzulassungen():
    xs = ['2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020']
    ys = [28,61,47,19,8,36,162,541,2154,2956,6051,8522,12363,11410,25056,36062,63281,25975]
    fig, ax = plt.subplots(figsize=(9,6))
    ax.plot(xs, ys, color=colors[0])
    ax.scatter(xs, ys, color=colors[0])
    for x, y in zip(xs, ys):
        label = format_big_number(y)
        ax.annotate(label,  # this is the text
                     (x, y),  # this is the point to label
                     textcoords="offset points",  # how to position the text
                     xytext=(0, 8),  # distance from text to points (x,y)
                     ha='center',
                    fontsize=8
                    )  # horizontal alignment can be left, right or center
    ax.set_xlabel('Jahr')
    ax.set_ylabel('Anzahl der Elektroautos')
    ax.set_ylim([0, 70000])
    ax.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format_big_number(int(x))))
    ax.grid(axis='y', linestyle='--')
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    plt.savefig('output/bev_neuzulassungen_03_bis_20.png', dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()


def plot_ladestationen():
    xs = ['06/2018', '09/2018', '12/2018', '03/2019', '06/2019', '09/2019', '12/2019', '03/2020', '04/2020']
    xs = ['Q2 2018', 'Q3 2018', 'Q4 2018', 'Q1 2019', 'Q2 2019', 'Q3 2019', 'Q4 2019', 'Q1 2020', 'Q2 2020']
    xs = ['Juni 2018', 'September 2018', 'Dezember 2018', 'März 2019', 'Juni 2019', 'September 2019', 'Dezember 2019', 'März 2020', 'Juni 2020']
    ys = [8805, 11531, 12707, 14083, 15501, 16633, 17819, 18961, 18961]
    fig, ax = plt.subplots(figsize=(9,6))
    ax.plot(xs, ys, color=colors[0])
    ax.scatter(xs, ys, color=colors[0])
    for x, y in zip(xs, ys):
        label = format_big_number(y)
        ax.annotate(label,  # this is the text
                     (x, y),  # this is the point to label
                     textcoords="offset points",  # how to position the text
                     xytext=(0, 8),  # distance from text to points (x,y)
                     ha='center',
                    fontsize=8
                    )  # horizontal alignment can be left, right or center
    ax.set_xlabel('Quartal')
    ax.set_ylabel('Anzahl der Ladestationen')
    ax.set_ylim([0, 22000])
    ax.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format_big_number(int(x))))
    ax.grid(axis='y', linestyle='--')
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    plt.savefig('output/anzahl_ladestationen_18_bis_20.png', dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()


def create_barplot_annotations(rects, ax):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(format_big_number(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


def plot_neubedarf_ladestationen():
    data = [
        [19002, 9591, 7734, 5526, 3791],
        [22690, 11453, 9236, 6598, 4527],
        [47698, 24074, 19414, 13871, 9517],
        [89694, 45271, 36508, 26083, 17896]
    ]
    cities = ['Berlin', 'Hamburg', 'München', 'Köln', 'Frankfurt']
    labels = ['2019', '2020', '2022', '2025']
    fig, ax = plt.subplots(figsize=(12,6))
    X = np.array([1.5*i for i in range(len(cities))])

    padding_inside = 0.02
    width = 0.3
    for index, label in enumerate(labels):
        rects = ax.bar(X + (width + padding_inside) * index, data[index], color=colors[len(labels)-index], width=width, label=label, zorder=3)
        create_barplot_annotations(rects, ax)

    ax.set_xticks(X + width*1.55)
    ax.set_xticklabels(cities)
    ax.set_xlabel('Stadt')
    ax.set_ylabel('Anzahl benötigter Ladestationen')
    ax.set_ylim([0, 100000])
    ax.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format_big_number(int(x))))
    ax.xaxis.set_tick_params(length=0)
    ax.grid(axis='y', linestyle='--', zorder=0)
    plt.legend()
    plt.savefig('output/neubedarf_ladestationen.png', dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()


def plot_kennfeld_verbrauch():
    def split_bin(bin_string):
        splitted = bin_string.split(',')
        min_val = int(splitted[0].split('(')[1])
        max_val = int(splitted[1].split(']')[0])
        return min_val, max_val

    path_to_csv = '/home/lucas/IdeaProjects/beam/test/input/munich-simple/default-energy-primary-flat-expensive.csv'
    path_to_csv = '/home/lucas/IdeaProjects/beam/test/input/munich-simple/default-energy-primary-flat.csv'
    num_lanes_bin = '(0, 1]'
    #num_lanes_bin = '(0, 5]'
    linspace_steps = 50
    font_size = 8
    df = pd.read_csv(path_to_csv)


    # Read and plot consumption data from csv data
    working_dir = "/data/lucas/SA/Simulation Runs/munich-simple_debug_consumption__2020-05-05_09-07-52/ITERS/it.0/0."
    working_dir = "/data/lucas/SA/Simulation Runs/munich-simple_500agents_24h_5iter__2020-05-06_08-48-47/ITERS/it.0/0."
    df_consumption_per_trip = pd.read_csv(working_dir + "vehConsumptionPerTrip.csv")
    df_consumption_per_link = pd.read_csv(working_dir + "vehConsumptionPerLink.csv")
    average_consumption = pd.DataFrame(columns=['trip_data', 'link_data'])
    average_consumption['trip_data'] = df_consumption_per_trip['primaryEnergyConsumedInJoule'] / df_consumption_per_trip['legLength']
    average_consumption['link_data'] = link_average_consumption = df_consumption_per_link['energyConsumedInJoule'] / df_consumption_per_link['linkLength']
    print("Mean consumption", average_consumption['trip_data'].mean(), average_consumption['link_data'].mean())
    fig, ax = plt.subplots(figsize=(8,6))
    average_consumption.plot.box(ax=ax)
    ax.set_xlabel('Data source')
    ax.set_ylim([0,700])
    ax.set_ylabel('Consumption in J/m')
    plt.show()


    df = df[df['num_lanes_int_bins'] == num_lanes_bin]
    all_speeds = np.array([])
    all_grades = np.array([])
    all_rates = np.array([])
    num_rows = 0
    for speed_bin in df['speed_mph_float_bins'].unique():
        rows = df[df['speed_mph_float_bins'] == speed_bin]
        speed_min, speed_max = split_bin(speed_bin)
        grade_min = 50
        grade_max = -50
        for grade_bin, rate in zip(rows['grade_percent_float_bins'], rows['rate']):
            row_grade_min, row_grade_max = split_bin(grade_bin)
            if row_grade_min < grade_min:
                grade_min = row_grade_min
                rate_min = rate
            if row_grade_max > grade_max:
                grade_max = row_grade_max
                rate_max = rate
        speeds = np.linspace(speed_min, speed_max, linspace_steps)
        grades = np.linspace(grade_min, grade_max, linspace_steps)
        rates = np.linspace(rate_min, rate_max, linspace_steps)
        all_speeds = np.append(all_speeds, speeds)
        all_grades = np.append(all_grades, grades)
        all_rates = np.append(all_rates, rates)
        num_rows += 1

    x = np.reshape(all_speeds, (num_rows, linspace_steps))
    y = np.reshape(all_grades, (num_rows, linspace_steps))
    z = np.reshape(all_rates, (num_rows, linspace_steps))
    #x *= 1.60934    # mph to kmh
    x *= 1.60934 / 3.6    # mph to m/s
    z *= 22.37 # kWh / 100miles to J/m
    z *= 10 # Plausible werte
    print('z min is ', z.min())

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(x,y,z)
    #ax.set_xlabel('Geschwindigkeit in km/h')
    ax.set_xlabel('Geschwindigkeit in m/s', fontsize=font_size)
    ax.set_ylabel('Steigung in Grad', fontsize=font_size)
    ax.set_zlabel('Verbrauch in J/m', fontsize=font_size)
    ax.set_zlim([0, z.max()])
    ax.tick_params(labelsize=font_size)
    plt.savefig('/home/lucas/IdeaProjects/beam/output/kennfeld_verbrauch.png', dpi=300, bbox_inches='tight', pad_inches=0.15)
    plt.show()
    """
    for speed_bin, grade_bin, rate in zip(df['speed_mph_float_bins'], df['grade_percent_float_bins'], df['rate']):
        speed_min, speed_max = split_bin(speed_bin)
        grade_min, grade_max = split_bin(grade_bin)
        speeds = np.linspace(speed_min, speed_max)
        grades = np.linspace(grade_min, grade_max)
        ax.scatter(speeds, grades, rate)
"""
    #ax.scatter(geschwindigkeiten, steigung, verbrauch)
    #ax.plot_surface(geschwindigkeiten, steigung, verbrauch)


def plot_scoring_parameters():
    xs_min_soc = [100,    80,    79.9,   60,    59.9,   30,    29.9,   20,    19.9,   1,   0]
    ys_min_soc = [1,    1,      0.8,    0.8,    0.6,    0.6,    0.3,    0.3,    0.2,    0.2,    0]
    xs_end_soc = [100, 0]
    ys_end_soc = [1, 0]
    max_walking_dist = 500
    residual_utility = 0.2
    xs_walk_dist = np.linspace(0, 700)
    ys_walk_dist = [calcNormalizedWalkingDistance(x, max_walking_dist, residual_utility) for x in xs_walk_dist]

    fig, ax = plt.subplots(figsize=(8,8))
    ax.plot(xs_min_soc, ys_min_soc, label='Minimaler Ladezustand', color=colors[0])
    ax.plot(xs_end_soc, ys_end_soc, label='Endladezustand', color=colors[1])
    ax.set_xlabel('Ladezustand in %')
    ax.set_ylabel('Resultierender Nutzen')
    ax.set_ylim([0,1.1])
    ax.legend(loc='upper left')
    plt.savefig('/home/lucas/IdeaProjects/beam/output/scoring_parameter_soc.png', dpi=300, bbox_inches='tight', pad_inches=0)

    fig, ax = plt.subplots(figsize=(8,8))
    ax.plot(xs_walk_dist, ys_walk_dist, color=colors[0])
    ax.set_xlabel('Laufdistanz in m')
    ax.set_ylabel('Resultierender Nutzen')
    ax.set_ylim([0,1.1])
    plt.savefig('/home/lucas/IdeaProjects/beam/output/scoring_parameter_walk_dist.png', dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()
    """
    fig, ax = plt.subplots(1, 2, figsize=(12,6))
    ax[0].plot(xs_min_soc, ys_min_soc, label='Minimaler Ladezustand')
    ax[0].plot(xs_end_soc, ys_end_soc, label='Endladezustand')
    ax[0].set_xlabel('Ladezustand in %')
    ax[0].set_ylabel('Resultierender Nutzen')
    ax[0].legend()


    ax[1].plot(xs_walk_dist, ys_walk_dist)
    ax[1].set_xlabel('Laufdistanz in m')
    ax[1].set_ylabel('Resultierender Nutzen')
    plt.savefig('/home/lucas/IdeaProjects/beam/output/scoring_parameter.png', dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()
    """

def plot_runtimes():
    xs = [50, 500, 5000, 50000]
    ys_matsim = [41, 51, 170, 1544] #s
    ys_beam = [91, 5*60 + 5, 17*60 + 11, 3600 + 43*60 + 37] #s

    fig, ax = plt.subplots(figsize=(8,8))
    ax.plot(xs, ys_beam, color=colors[0], label='Laufzeit BEAM')
    ax.plot(xs, ys_matsim, color=colors[1], label='Laufzeit MATSim')
    ax.scatter(xs, ys_beam, color=colors[0])
    ax.scatter(xs, ys_matsim, color=colors[1])
    ax.set_xlabel('Anzahl der Agenten')
    ax.set_xscale('log')
    ax.set_xlim([10,100000])
    ax.set_ylabel('Laufzeit in s')
    ax.set_ylim([0,8000])
    ax.grid()
    ax.legend(loc='upper left')
    plt.savefig('/home/lucas/IdeaProjects/beam/output/benchmark_runtimes.png', dpi=300, bbox_inches='tight', pad_inches=0)


def plot_cpu_ram_usage(seperate=True):
    xs = [50, 500, 5000, 50000]
    ys_max_ram_matsim = [800, 976, 1138, 1400] #MB
    ys_max_ram_beam = [4000, 5340, 7705, 11000] #MB
    ys_avg_cpu_matsim = [30, 30, 30, 30] # in %
    ys_avg_cpu_beam = [45, 50, 55, 70] # in %
    if seperate:
        fig, ax_ram = plt.subplots(figsize=(8,8))
        ax_ram.plot(xs, ys_max_ram_beam, color=colors[0], label='Arbeitsspeichernutzung BEAM')
        ax_ram.plot(xs, ys_max_ram_matsim, color=colors[1], label='Arbeitsspeichernutzung MATSim')
        ax_ram.scatter(xs, ys_max_ram_beam, color=colors[0])
        ax_ram.scatter(xs, ys_max_ram_matsim, color=colors[1])
        ax_ram.set_xlabel('Anzahl der Agenten')
        ax_ram.set_xscale('log')
        ax_ram.set_xlim([10,100000])
        ax_ram.set_ylabel('Maximale Arbeitsspeichernutzung in MB')
        ax_ram.set_ylim([0,12000])
        ax_ram.grid()
        ax_ram.legend(loc='upper left')
        plt.savefig('/home/lucas/IdeaProjects/beam/output/benchmark_ram_usage.png', dpi=300, bbox_inches='tight', pad_inches=0)

        #ax_cpu = ax_ram.twinx()
        fig, ax_cpu = plt.subplots(figsize=(8,8))
        ax_cpu.plot(xs, ys_avg_cpu_beam, color=colors[0], label='CPU Auslastung BEAM')
        ax_cpu.plot(xs, ys_avg_cpu_matsim, color=colors[1], label='CPU Auslastung MATSim')
        ax_cpu.scatter(xs, ys_avg_cpu_beam, color=colors[0])
        ax_cpu.scatter(xs, ys_avg_cpu_matsim, color=colors[1])
        ax_cpu.set_xlabel('Anzahl der Agenten')
        ax_cpu.set_xscale('log')
        ax_cpu.set_xlim([10,100000])
        ax_cpu.set_ylabel('Durchschnittliche CPU Auslastung in %')
        ax_cpu.set_ylim([0,100])
        ax_cpu.grid()
        ax_cpu.legend(loc='upper left')
        plt.savefig('/home/lucas/IdeaProjects/beam/output/benchmark_cpu_usage.png', dpi=300, bbox_inches='tight', pad_inches=0)


def plot_nonlinear_charging():
    xs = np.linspace(0, 1, 50)
    font_size = 16
    a = 0.6
    b = 0.05
    c = 0.4
    ys = np.array([a*b**x + c for x in xs])
    fig, ax = plt.subplots(figsize=(12,8))
    #ax.plot(xs * 100, ys*100)
    ax.plot(xs * 100, ys*100, label='a=0.6, b=0.05, c=0.4')
    ax.set_ylim([0, 105])
    ax.set_xlabel('Ladezustand in % der Batteriekapazität', fontsize=font_size)
    ax.set_ylabel('Ladeleistung in % der maximalen Ladeleistung', fontsize=font_size)
    ax.legend(loc='upper right', fontsize=font_size)
    ax.tick_params(labelsize=font_size)
    ax.grid()
    plt.savefig('/home/lucas/IdeaProjects/beam/output/nonlinear_charging_power.png', dpi=300, bbox_inches='tight', pad_inches=0)


def calcNormalizedWalkingDistance(walkingDistance, maxWalkingDistance, residualUtility):
    a = walkingDistance / maxWalkingDistance
    b = residualUtility ** a
    c = max(b, residualUtility)
    return max(residualUtility**(walkingDistance / maxWalkingDistance), residualUtility)

plot_nonlinear_charging()
#plot_cpu_ram_usage()
#plot_runtimes()
#plt.show()
#plot_scoring_parameters()
#plot_kennfeld_verbrauch()
#plot_neuzulassungen()
#plot_ladestationen()
#plot_fahrzeugklassen()
#plot_verteilung_ladestationen()
#plot_neubedarf_ladestationen()
#plt.show()