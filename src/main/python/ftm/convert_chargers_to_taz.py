import xml.etree.ElementTree as ET
import pandas as pd
import geopandas
import csv

input_filename = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/munich-enclosing-counties-chargers.xml"
tree = ET.parse(input_filename)
root = tree.getroot()
df = pd.DataFrame(columns=['latitude', 'longitude', 'numStalls', 'power', 'x', 'y'])

# parse XML
for node in root:
    is_charging_station = False
    lat, lon, power, num_stalls = 0, 0, 22, 2

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
                num_stalls += int(tag_value)
            except:
                print("Capacity: ", tag_value)
        if "socket:" in str(tag_type):
            print(tag_type, tag_value)
        if tag_type == 'amenity' and tag_value == 'charging_station':
            is_charging_station = True

    if is_charging_station and lat > 0 and lon > 0:
        # Add to dataframe
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
#df.x = gdf.geometry.x
#df.y = gdf.geometry.y

# Convert to csv
# Config
taz_centers_path = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/taz-centers.csv"
taz_parking_path = "/home/lucas/IdeaProjects/beam/test/input/munich-simple/conversion-input/taz-parking.csv"
taz_id_offset = 100
taz_default_area = 5000
parking_default_type = 'Public'
parking_default_pricing_model = 'FlatFee'
parking_default_fee = 100
parking_default_reserved = 'Any'

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
with open(taz_centers_path, mode='w') as taz_centers_file:
    centers_df.to_csv(taz_centers_file, mode='a', header=taz_centers_file.tell() == 0, index=False)

with open(taz_parking_path, mode='w') as taz_parking_file:
    parking_df.to_csv(taz_parking_file, mode='a', header=taz_parking_file.tell() == 0, index=False)
"""
        taz_parking_writer = csv.writer(taz_parking_file, delimiter=',')
        for x, y, num_stalls, power in zip(df.x, df.y, df.numStalls, df.power):
            taz_centers_writer.writerow([taz_id_iterator, x, y, taz_default_area])
            taz_parking_writer.writerow([taz_id_iterator, parking_default_type, parking_default_pricing_model, 'Level2('+str(power)+'|AC)', num_stalls, parking_default_fee, parking_default_reserved])
            taz_id_iterator += 1
"""
