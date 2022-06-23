from geopy import distance
import math 
from collections import Counter

from data.points import COMPLETE_ROUTE, FREQUENCY, INTERVALS_NUMBER

METERS_FACTOR = 12.0
PERIODS_NUMBER = 24
INTERVAL_SECONDS = 5
COVERAGE_FACTOR = 0.85


def calculate_stops(points_list, first_coordinate, last_coordinate):
    # Given a filtered list without similar points if between two points the time difference is
    # greater than PERIODS_NUMBER * INTERVAL_SECONDS it means that the user has stopped
    # It makes sense because before we have already deleted those similar points generated during the stop
    # It is also necessary to check the stops in the start-end of the route because those points would be deleted and
    # stopping data would not be real at all.
    number_of_stops = 0
    for first, second in zip(points_list, points_list[1:]):
        first_time = first.get('time')
        second_time = second.get('time')
        time_difference = second_time - first_time
        if time_difference > PERIODS_NUMBER * INTERVAL_SECONDS:
            number_of_stops += 1

    # Checking if the user stopped when he started the route
    if points_list[0].get('time') - first_coordinate.get('time') > PERIODS_NUMBER * INTERVAL_SECONDS:
        number_of_stops += 1
    # Checking if the user stopped when he was about to end the route
    if last_coordinate.get('time') - points_list[-1].get('time') > PERIODS_NUMBER * INTERVAL_SECONDS:
        number_of_stops += 1
    return number_of_stops

# This method calculates the distance from a list of points. It saves in a list points that are further than METERS_FACTOR meters.
# It returns the distance and the list of points without duplicates.


def calculate_distance_and_time(coordinates):
    filtered_list = []
    total_distance = 0
    total_time = 0
    exercise_time = 0  # Represent the time that the user is exercising without stopping
    global METERS_FACTOR
    for first, second in zip(coordinates, coordinates[1:]):
        first_point = (first.get('latitude'), first.get('longitude'))
        second_point = (second.get('latitude'), second.get('longitude'))
        time = second.get('time') - first.get('time')
        dst = distance.distance(first_point, second_point).km
        dst_meters = dst*1000
        if dst_meters >= METERS_FACTOR:
            if first not in filtered_list:
                filtered_list.append(first)
            if second not in filtered_list:
                filtered_list.append(second)
            # Add excercise time
            exercise_time += time
        total_distance += dst_meters
        # Total time
        total_time += time
    return total_distance, total_time, exercise_time, filtered_list


def calculate_velocity(distance, time):
    return distance/time


# To complete the route at least more than 85% of the points should be similar.
def do_route(user_coordinates, target_route_coordinates):
    global METERS_FACTOR, COVERAGE_FACTOR
    coverage = 0
    route_completed = False
    for coordinate in target_route_coordinates:
        i = 0
        points_far = True
        while points_far and i < len(user_coordinates):
            target = (coordinate.get('latitude'), coordinate.get('longitude'))
            user = (user_coordinates[i].get('latitude'),
                    user_coordinates[i].get('longitude'))
            dst = distance.distance(user, target).km
            dst_meters = dst*1000
            if dst_meters <= METERS_FACTOR:
                coverage = coverage + 1
                points_far = False
            i = i + 1
    points_covered = coverage/len(target_route_coordinates)
    print("Coverage " + str(coverage))
    print("-----------------------------------------------------------")
    print("Points covered " + str(points_covered))
    print("-----------------------------------------------------------")
    if points_covered >= COVERAGE_FACTOR:
        route_completed = True
    return route_completed


def get_points_to_assign(slow, fast, exercise_time):
    gap = slow - fast 
    interval_slots = math.ceil(gap / INTERVALS_NUMBER)
    #To know the quantity of time to add to the fastest time in order to construct the interval
    checkpoints_list = []
    checkpoints_list.append(fast)
    for i in range(INTERVALS_NUMBER):
        component = checkpoints_list[i] + interval_slots
        checkpoints_list.append(component)
    #We calculate the fastest and slowest and we create an interval with the times to assign the points depending if the user
    #belongs to a certain time slot, he will receive a different amount of points
    closest_checkpoint = min(checkpoints_list, key=lambda x:abs(x - exercise_time))
    checkpoint_index = checkpoints_list.index(closest_checkpoint)
    return COMPLETE_ROUTE[checkpoint_index] 


def delete_duplicates(list):
    count = Counter(list)
    resultado = []
    for c in count:
        cuenta = count[c]
        print(cuenta)
        if cuenta >= FREQUENCY:
            resultado.append(c)
        else:
            for i in range(cuenta):
                resultado.append(c)
    return resultado