import xml.etree.ElementTree as ET
from xml.dom import minidom
import geopandas as gpd
from shapely.geometry import Point, MultiPolygon


###### Configuration
inputFile = "mito_assignment.50.plans.xml"
polygonFile = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/munich-polygon.geojson"
outputFile = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/mito_assignment.50.plans.min.shapefiltered.xml"
populationSize = 999999999999999999999999
activitiesDict = {
    "home": "Home",
    "other": "Other",
    "shopping": "Shopping",
    "work": "Work",
    "education": "Education"
}
###############

def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


def main():
    # Load shapedata
    df = gpd.read_file(polygonFile)
    geoPolygon = df.geometry.to_crs({'init': 'epsg:31468'})[0]

    # Parse input XML and create output tree
    tree = ET.parse(inputFile)
    root = tree.getroot()
    populationTree = ET.ElementTree()
    populationEl = ET.Element('population')
    print("Found", len(root), "persons inside original xml file")

    # Iter over input
    populationCount = 0
    for person in root:
        if (populationCount >= populationSize):
            break
        for plan in person:
            if (plan.attrib['selected'] == 'yes'):
                # Check if home activity exists and within bounds
                homeActExists = False
                withinBounds = True
                for element in plan:
                    if (element.tag == "activity" and element.attrib['type'] == "home"):
                        homeActExists = True
                    if ('x' in element.attrib and 'y' in element.attrib):
                        activityPoint = Point(float(element.attrib['x']), float(element.attrib['y']))
                        if not geoPolygon.contains(activityPoint):
                            print("Skipping person " + person.attrib['id'] + ": Out of bounds")
                            withinBounds = False
                            break

                if not withinBounds:
                    break
                # Create person
                personEl = ET.SubElement(populationEl, 'person')
                personEl.set('id', person.attrib['id'])
                populationCount += 1

                # Create plan
                planEl = ET.SubElement(personEl, 'plan')
                planEl.set('selected', "yes")

                for element in plan:
                    if (element.tag == "activity"):

                        # Create activity
                        activityEl = ET.SubElement(planEl, 'activity')
                        activityType = activitiesDict.get(element.attrib['type'], "Other")
                        # Overwrite type of first activity to home if no home activity exists
                        if not homeActExists and len(planEl) == 1:
                            activityType = "Home"

                        activityEl.set('type', activityType)
                        activityEl.set('x', element.attrib['x'])
                        activityEl.set('y', element.attrib['y'])
                        if ('end_time' in element.attrib):
                            activityEl.set('end_time', element.attrib['end_time'])
                    elif (element.tag == "leg" and element.attrib['mode'] == 'car'):
                        # Create leg
                        legEl = ET.SubElement(planEl, 'leg')
                        legEl.set('mode', element.attrib['mode'])
                        if ('dep_time' in element.attrib):
                            legEl.set('dep_time', element.attrib['dep_time'])

    print("Generated", populationCount, "persons")
    header = '<?xml version="1.0" encoding="utf-8"?><!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">'
    prettyBody = prettify(populationEl)
    #print(prettyBody)
    body = ET.tostring(populationEl).decode('utf-8')

    fileHandle = open(outputFile, "w")
    fileHandle.write(header + body)


if __name__ == '__main__':
    main()
