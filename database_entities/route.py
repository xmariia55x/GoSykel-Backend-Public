from mongoDB import route
from bson import ObjectId
from datetime import datetime
import pymongo

from database_entities.user import get_user_nickname, get_user_profile_picture
import dates.dates as dates



def create_route(route_name, rate, private, author, coordinates, velocity_during_exercise, general_velocity,
                 total_distance, number_of_stops, total_time, exercise_time):
    try:
        route.insert_one(
            {
                "name": route_name,
                "date": datetime.now().timestamp(),
                "frequency": 1,  
                "speed": {"general": general_velocity,  # Includes stops
                          # The velocity the user had when he was moving
                          "moving": velocity_during_exercise,
                          },
                "rate": rate,
                "private": bool(private),
                "author": ObjectId(author),
                "distance":  total_distance,
                "stops": number_of_stops,
                "time_to_complete": [
                    {
                        "user": ObjectId(author),
                        "general": total_time,
                        "moving": exercise_time
                    }
                ],
                "coordinates": coordinates
            }
        )
        return True
    except Exception as e:
        print("An exception occurred ::", e)
        return False


def invalidate_users_routes(user_id):
    filter = {'author': ObjectId(user_id)}
    new_values = {"$set": {
        "author": None
    }}
    result = route.update_many(filter, new_values)

    filter = {"time_to_complete.user": ObjectId(user_id)}
    new_values = {"$set": {
        "time_to_complete.$.user": None
    }}
    result = route.update_many(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully


def add_new_time_to_complete(route_id, user_id, total_time, exercise_time):
    filter = {"_id": ObjectId(route_id)}
    new_values = {"$push": {
        "time_to_complete": {
            "user": ObjectId(user_id),
            "general": total_time,
            "moving": exercise_time
        }
    }}
    result = route.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def update_route_frequency(route_id):
    filter = {"_id": ObjectId(route_id)}
    new_values = {"$inc": {"frequency": 1}}
    result = route.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def update_route_information(route_id, route_name, private):
    filter = {"_id": ObjectId(route_id)}
    new_values = {"$set": {
        "name": route_name,
        "private": private
    }}
    result = route.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully


def invalidate_author_field_change_visibility(id, author):
    if str(get_route(id)["author"]) == author:
        filter = {'_id': ObjectId(id)}
        new_values = {"$set": {
            "author": None,
            "private": False
        }}
        result = route.update_one(filter, new_values)
        if result.matched_count == 1:
            return True  # the document was updated succesfully
    return False


def get_routes_ordered_by_date_descending():
    public_routes_ordered = route.find().sort('date', pymongo.DESCENDING)
    result_list = []
    for result in public_routes_ordered:
        result_list.append(result)
    return result_list


def process_routes_information(routes):
    processed_routes = []
    for rt in routes:
        day, hour = dates.timestamp_to_date(rt["date"])
        route_id_str = str(rt["_id"])
        rt["_id"] = route_id_str
        rt["date"] = day
        formatted_coords = []
        for rt_coordinate in rt["coordinates"]:
            formatted_coords.append({"latitude": rt_coordinate.get(
                "latitude"), "longitude": rt_coordinate.get("longitude")})
        rt["coordinates"] = formatted_coords
        if rt["author"] is None:
            rt["author"] = "ChoppSykler"
            rt["author_id"] = "ChoppSykler"
        else:
            author_id = rt["author"]
            author_nickname = get_user_nickname(author_id)
            author_profile_picture = get_user_profile_picture(author_id)
            rt["author_id"] = str(author_id)
            rt["author"] = author_nickname
            rt["author_profile_picture"] = author_profile_picture

        for time_by_user in rt["time_to_complete"]:
            user_object_id = time_by_user.get("user")
            if user_object_id is None:
                time_by_user["user"] = "ChoppSykler"
            else:
                username = get_user_nickname(user_object_id)
                time_by_user["user_id"] = str(user_object_id)
                time_by_user["user_profile_picture"] = get_user_profile_picture(
                    user_object_id)
                time_by_user["user"] = username
        sorted_time = sorted(rt["time_to_complete"],
                             key=lambda x: x.get('moving', 0))
        rt["time_to_complete"] = sorted_time
        processed_routes.append(rt)
    return processed_routes

def get_slow_and_fast_time(route_id):
    requested_route = get_route(route_id)
    sorted_time = sorted(requested_route["time_to_complete"],
                             key=lambda x: x.get('moving', 0))
    slow = sorted_time[len(sorted_time) - 1].get('moving', 0)
    fast = sorted_time[0].get('moving', 0)
    return slow, fast 

def get_users_public_routes_ordered_by_date_descending(user_id):
    # Given a user id we get the public routes where that user is the author
    public_routes_ordered = route.find({'author': ObjectId(user_id)}, {
                                       'private': False}).sort('date', pymongo.DESCENDING)
    result_list = []
    for result in public_routes_ordered:
        result_list.append(result)
    return result_list


def get_users_owned_routes_ordered_by_date_descending(user_id):
    routes_ordered = route.find({'author': ObjectId(user_id)}).sort(
        'date', pymongo.DESCENDING)
    result_list = []
    for result in routes_ordered:
        result_list.append(result)
    return result_list


def get_route(id):
    requested_route = route.find_one({'_id': ObjectId(id)})
    return requested_route


def check_user_is_author(user_id, route_id):
    requested_route = route.find_one({'_id': ObjectId(route_id)})
    if str(requested_route["author"]) == user_id:
        return True
    else:
        return False


def get_routes_information(completed_routes):
    # Parameter: Array of Object Id containing a reference to the users completed routes
    # Returns: Array of Object containing the each route information
    route_information_list = []
    for completed_route_id in completed_routes:
        route_info = get_route(str(completed_route_id))
        route_information_list.append(route_info)
    return route_information_list
