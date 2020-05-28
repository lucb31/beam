import xml.etree.ElementTree as ET
import gzip
import pandas as pd
from os import path

from python.ftm.analyze_events import df_columns_to_numeric


def filter_plans_by_vehicle_id_from_plans_csv(path_to_population_csv, path_to_plans_csv, vehicle_id):
    assert path.exists(path_to_population_csv)
    df_population = df_columns_to_numeric(pd.read_csv(path_to_population_csv, sep=",", index_col=None, header=0), ['personId', 'householdId'])
    df_filtered = df_population[df_population['householdId'] == vehicle_id]
    if len(df_filtered.index > 0):
        person_id = df_filtered.personId.iloc[0]
        return filter_plans_by_person_id_from_plans_csv(path_to_plans_csv, person_id)
    else:
        return None


def filter_plans_by_person_id_from_plans_csv(path_to_plans_csv, person_id):
    assert path.exists(path_to_plans_csv)
    df_plans = df_columns_to_numeric(pd.read_csv(path_to_plans_csv, sep=",", index_col=None, header=0), ['personId'])
    df_plans = df_plans[df_plans['personId'] == person_id]
    return df_plans


def get_vehicle_id_from_population_csv(path_to_population_csv, person_id):
    assert path.exists(path_to_population_csv)
    df_population = df_columns_to_numeric(pd.read_csv(path_to_population_csv, sep=",", index_col=None, header=0), ['personId', 'householdId'])
    df_filtered = df_population[df_population['personId'] == person_id]
    if len(df_filtered.index > 0):
        return df_filtered.householdId.iloc[0]
    else :
        return 0


def filter_plans_by_vehicle_id(filepath_households_xml, filepath_plans_xml, vehicle_id = 0, output_filename=None):
    # get person id from households.xml
    if '.gz' in str(filepath_households_xml):
        with gzip.open(filepath_households_xml, 'rb') as f_in:
            tree = ET.parse(f_in)
    else:
        tree = ET.parse(filepath_households_xml)
    person_id = 0
    household_tag = '{dtd}household'
    household_tag = '{http://www.matsim.org/files/dtd}household'

    for parent in tree.iter():
        for household in parent.findall(household_tag):
            if 'id' in household.attrib:
                household_id = 0
                try:
                    household_id = int(household.attrib['id'])
                except ValueError as ex:
                    household_id = 0
                if household_id == int(vehicle_id):
                    for members_element in household.findall('{http://www.matsim.org/files/dtd}members'):
                        for person_id_element in members_element.iter():
                            if 'refId' in person_id_element.attrib:
                                person_id = person_id_element.attrib['refId']
                    """
                    for household_elements in household.iter():
                        for person_id_element in household_elements.findall('{dtd}personId'):
                            if 'refId' in person_id_element.attrib:
                                person_id = person_id_element.attrib['refId']
                                """

    if person_id != 0:
        print('Found person ID: ', person_id)
    # get plans form plans.xml
    with gzip.open(filepath_plans_xml, 'rb') as f_in:
        tree = ET.parse(f_in)
        root = tree.getroot()
        for parent in tree.iter():
            for person in parent.findall('person'):
                if 'id' not in person.attrib or person.attrib['id'] != person_id:
                    parent.remove(person)

        header = '<?xml version="1.0" encoding="utf-8"?>'
        body = ET.tostring(root).decode('utf-8')
        print(body)
        if output_filename is not None:
            fileHandle = open(output_filename, "w")
            fileHandle.write(header + body)
            fileHandle.close()

        return tree


def main():
    filepath_households = '/data/lucas/SA/Simulation Runs/munich-simple__2020-04-22_11-35-35/outputHouseholds.xml.gz'
    filepath_plans = '/data/lucas/SA/Simulation Runs/munich-simple__2020-04-22_11-35-35/ITERS/it.50/50.plans.xml.gz'
    plans_xml = filter_plans_by_vehicle_id(filepath_households, filepath_plans, vehicle_id=475)
    pass


if __name__ == '__main__':
    main()
