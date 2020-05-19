import xml.etree.ElementTree as ET
import pandas as pd
import geopandas
import csv
import random

###### CONFIG #######
input_filename = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/munich-enclosing-counties-chargers.xml"
taz_centers_path = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/taz-centers-small.csv"
taz_parking_path = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/taz-parking-small.csv"
taz_id_offset = 100
taz_default_area = 5000
parking_default_type = 'Public'
parking_default_pricing_model = 'FlatFee'
parking_default_fee = 100
parking_default_reserved = 'Any'
def_num_stalls = 2
def_power = 22
max_num_stalls = 8
regular_parking_taz = 1
regular_parking_x = 4466208
regular_parking_y = 5334723
regular_parking_area = 60000
sampling_rate = 1

# Small LIS
sampling_rate = 0.1
max_num_stalls = 1

# All chargers are Level 2 AC
#####################

def main():
    # parse XML
    tree = ET.parse(input_filename)
    root = tree.getroot()
    df = pd.DataFrame(columns=['latitude', 'longitude', 'numStalls', 'power', 'x', 'y'])
    for node in root:
        is_charging_station = False
        lat, lon, power, num_stalls = 0, 0, def_power, def_num_stalls

        # Get position
        if 'lat' in node.attrib:
            lat = float(node.attrib['lat'])
        if 'lon' in node.attrib:
            lon = float(node.attrib['lon'])
        for tag in node.findall('tag'):
            tag_type = tag.attrib['k']
            tag_value = tag.attrib['v']
            if tag_type == 'capacity':
                try:
                    num_stalls = int(tag_value)
                except:
                    print("Capacity: ", tag_value)
            if "socket:" in str(tag_type):
                print(tag_type, tag_value)
            if tag_type == 'amenity' and tag_value == 'charging_station':
                is_charging_station = True

        num_stalls = min(num_stalls, max_num_stalls)
        # Validate
        if is_charging_station and lat > 0 and lon > 0:
            # Add to dataframe
            random_val = 0
            if sampling_rate < 1:
                random_val = random.random()

            if random_val <= sampling_rate:
                df = df.append({
                    'latitude': lat,
                    'longitude': lon,
                    'numStalls': num_stalls,
                    'power': power,
                    'x': 0,
                    'y': 0
                }, ignore_index=True)

    print("We found ", len(df.index)," charging stations with a total capacity of ", df.numStalls.sum())

    # Convert to GK 4 CRS
    gdf = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.longitude, df.latitude))
    gdf.crs = 'epsg:4326'
    gdf = gdf.to_crs('epsg:31468')

    # Convert to csv
    charging_types = ["Level2(%s|AC)" % (power) for power in zip(df.power)]
    centers_df = pd.DataFrame({
        'taz': df.index + taz_id_offset,
        'coord-x': gdf.geometry.x,
        'coord-y': gdf.geometry.y,
        'area': taz_default_area
    })
    parking_df = pd.DataFrame({
        'taz': df.index + taz_id_offset,
        'parkingType': parking_default_type,
        'pricingModel': parking_default_pricing_model,
        'chargingType': charging_types,
        'numStalls': df.numStalls.astype('int32'),
        'feeInCents': parking_default_fee,
        'reservedFor': parking_default_reserved
    })

    # Add regular parking taz
    centers_df = centers_df.append(pd.DataFrame({
        'taz': [regular_parking_taz],
        'coord-x': [regular_parking_x],
        'coord-y': [regular_parking_y],
        'area': [regular_parking_area]
    }), ignore_index=True)
    parking_df = parking_df.append(pd.DataFrame({
        'taz': [regular_parking_taz],
        'parkingType': ['Public'],
        'pricingModel': ['FlatFee'],
        'chargingType': ['None'],
        'numStalls': [1000000],
        'feeInCents': [0],
        'reservedFor': ['Any']
    }), ignore_index=True)

    with open(taz_centers_path, mode='w') as taz_centers_file:
        centers_df.to_csv(taz_centers_file, mode='a', header=taz_centers_file.tell() == 0, index=False)

    with open(taz_parking_path, mode='w') as taz_parking_file:
        parking_df.to_csv(taz_parking_file, mode='a', header=taz_parking_file.tell() == 0, index=False)


if __name__ == '__main__':
    main()