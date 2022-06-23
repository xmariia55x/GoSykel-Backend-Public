from urllib import request
import json
from datetime import datetime, timedelta
from geopy import distance
import certifi
import ssl

import database_entities.bycicle_lane as bycicle_lane_database

last_update = datetime.now()
bycicle_lanes_data = None 
METERS_FACTOR = 12.0
COVERAGE_FACTOR = 0.9

def get_updated_bycicle_lanes():
    global last_update, bycicle_lanes_data 
    next_update = last_update + timedelta(hours = 24) 
    if bycicle_lanes_data is None:
        bycicle_lanes_data = download()
    elif datetime.now() > next_update: 
        last_update = next_update
        bycicle_lanes_data = download()
    return bycicle_lanes_data

def download():
    link = 'https://datosabiertos.malaga.eu/recursos/transporte/trafico/da_carrilesBici-4326.geojson'
    file = request.urlopen(link, context=ssl.create_default_context(cafile=certifi.where()))
    data = file.read()
    data_loaded = json.loads(data)
    return data_loaded

def remove_closest_points(coordinates):
    filtered_list = []
    global METERS_FACTOR
    for first, second in zip(coordinates, coordinates[1:]):
        first_point = (first.get('latitude'), first.get('longitude'))
        second_point = (second.get('latitude'), second.get('longitude'))
        dst = distance.distance(first_point, second_point).km
        dst_meters = dst*1000
        if dst_meters >= METERS_FACTOR:
            if first not in filtered_list:
                filtered_list.append(first)
            if second not in filtered_list:
                filtered_list.append(second)
    return filtered_list


def check_duplicates(user_coordinates, coordinates_list): 
    global METERS_FACTOR, COVERAGE_FACTOR
    coverage = 0
    existing_bycicle_lane = False
    for coordinate in user_coordinates:
        i = 0
        points_far = True
        while points_far and i < len(coordinates_list):
            user = (coordinate.get('latitude'), coordinate.get('longitude'))
            unofficial = (coordinates_list[i].get('latitude'),
                    coordinates_list[i].get('longitude'))
            dst = distance.distance(unofficial, user).km
            dst_meters = dst*1000
            if dst_meters <= METERS_FACTOR:
                coverage = coverage + 1
                points_far = False
            i = i + 1
    points_covered = coverage/len(coordinates_list)
    print("Coverage " + str(coverage))
    print("-----------------------------------------------------------")
    print("Points covered " + str(points_covered))
    print("-----------------------------------------------------------")
    
    if points_covered >= COVERAGE_FACTOR:
        existing_bycicle_lane = True
    return existing_bycicle_lane

def calculate_distance(coordinates):
    #format [{},{},{},{}]
    total_distance = 0
    global METERS_FACTOR
    for first, second in zip(coordinates, coordinates[1:]):
        first_point = (first.get('latitude'), first.get('longitude'))
        second_point = (second.get('latitude'), second.get('longitude'))
        dst = distance.distance(first_point, second_point).km
        dst_meters = dst*1000
        total_distance += dst_meters
    return total_distance


def get_open_data_bycicle_lanes():
    official_list = []
    for item in get_updated_bycicle_lanes()["features"]:
        if item["geometry"]["type"] == "LineString":
            official_list.append(item["geometry"]["coordinates"])
    return official_list


def convert_to_list_of_dicts(open_data_bycicle_lanes):
    #The input is like this: [[-4.123434, 36.244543], [-4.12345, 36.134556]]
    #The output will be: [{latitude: 36.23546, longitude: -4.25466}, {latitude: 36.345465, longitude: -4.134446}]
    result = []
    for coordinate in open_data_bycicle_lanes:
        dictionary = {"latitude": coordinate[1], "longitude": coordinate[0]}
        result.append(dictionary)
    return result 


def convert_to_set(list_of_dicts):
    dicts_set = set()
    for dictionary in list_of_dicts: 
        dicts_set.add(json.dumps(dictionary, sort_keys=True))
    return dicts_set 

def check_filtered_coordinates_are_in_open_data(coordinates):
    open_data_bycicle_lanes = get_open_data_bycicle_lanes()
    bycicle_lanes_list = [] #This will have this structure: [[{}, {}, {}], [{},{},{}]]
    for sublist in open_data_bycicle_lanes:
        bycicle_lanes_list_of_dictionaries = convert_to_list_of_dicts(sublist)
        bycicle_lanes_list.append(bycicle_lanes_list_of_dictionaries)
    
    coords_dset = convert_to_set(coordinates)
    index = 0
    present = False
    while not present and index < len(bycicle_lanes_list):
        open_data_set = convert_to_set(bycicle_lanes_list[index])
        if coords_dset.issubset(open_data_set):
            present = True
        index = index + 1
    return present, bycicle_lanes_list[index-1]

def check_if_its_longer_than_the_bycicle_lane(segment, coordinates):
    new_distance = calculate_distance(coordinates)
    distance = calculate_distance(segment)
    if new_distance > distance: 
        return True
    else:
        return False
    
def check_filtered_coordinates_are_in_database(coordinates):
    coords_dset = convert_to_set(coordinates)
    database_bycicle_lanes = list(bycicle_lane_database.get_bycicle_lanes())
    index = 0
    present = False
    while not present and index < len(database_bycicle_lanes):
        open_data_set = convert_to_set(database_bycicle_lanes[index]["coordinates"])
        if coords_dset.issubset(open_data_set):
            present = True
        index = index + 1
    return present, database_bycicle_lanes[index-1]

