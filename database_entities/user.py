from mongoDB import user, route
from datetime import datetime
from bson import ObjectId
import pymongo

# ITEM entity
from database_entities.item import get_first_avatar, get_first_badge, get_first_header, get_avatar_url
from data.points import SIGNUP


DAY_IN_SECONDS = 86400 #300 5 min in seconds
ONE_HOUR_SECONDS = 3600 #60 1 min in seconds 
TWENTY_THREE_HOURS_SECONDS = DAY_IN_SECONDS - ONE_HOUR_SECONDS 
TWENTY_FIVE_HOURS_SECONDS = DAY_IN_SECONDS + ONE_HOUR_SECONDS 


def get_user(id):
    user_result = user.find_one({'_id': ObjectId(id)})
    return user_result


def get_completed_routes_number(id):
    user_result = user.find_one({'_id': ObjectId(id)})
    completed_routes = len(user_result["completed_routes"])
    routes = route.find({'author': ObjectId(id)})
    created_routes = 0
    for r in routes:
        created_routes += 1
    return completed_routes + created_routes

def get_completed_routes(id):
    user_result = user.find_one({'_id': ObjectId(id)})
    completed_routes = user_result["completed_routes"]
    return completed_routes

def create_user(email, nickname):
    try:
        user.insert_one(
            {
                "email": email,
                "nickname": nickname,
                "points": SIGNUP,  
                "available_points": SIGNUP,
                "last_access": datetime.now().timestamp(),
                "access_frequency": -1,
                "completed_routes": [],
                "avatars": [ObjectId(get_first_avatar())],
                "headers": [ObjectId(get_first_header())],
                "badges": [ObjectId(get_first_badge())],
                "last_points_received": SIGNUP
            }
        )
        return True
    except Exception as e:
        print("An exception occurred ::", e)
        return False


def update_last_access(id):
    filter = {"_id": ObjectId(id)}
    new_values = {"$set": {
        "last_access": datetime.now().timestamp()
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def update_last_points_received(id, points):
    filter = {"_id": ObjectId(id)}
    new_values = {"$set": {
        "last_points_received": points
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def organize_items_list(duplicate_list):
    items_string = []
    for item in duplicate_list:
        items_string.append(str(item))
    items_string_no_duplicates = list(dict.fromkeys(items_string))
    items_ids_object_id = []
    for item in items_string_no_duplicates:
        items_ids_object_id.append(ObjectId(item))
    return items_ids_object_id

def remove_completed_route(user_id, route_id):
    filter = {"_id": ObjectId(user_id)}
    new_values = {"$pull": {
        "completed_routes": ObjectId(route_id)
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully


def update_information(id, nickname, avatar, header):
    user_object = get_user(id)
    # Before updating the user info in the database it is necessary to deal with avatars and headers lists.
    # I have to put the selected avatar/header in the first position in the list. It will indicate that
    # the header in the first position is the one that the user is using right now.
    user_object["avatars"].insert(0, ObjectId(avatar))
    user_object["headers"].insert(0, ObjectId(header))
    avatars_ids_object_id = organize_items_list(user_object["avatars"])
    headers_ids_object_id = organize_items_list(user_object["headers"])

    filter = {"_id": ObjectId(id)}
    new_values = {"$set": {
        "nickname": nickname,
        "avatars": avatars_ids_object_id,
        "headers": headers_ids_object_id
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def update_completed_routes(user_id, completed_routes_list):
    filter = {"_id": ObjectId(user_id)}
    new_values = {"$set": {
        "completed_routes": completed_routes_list
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def update_access_frequency(user_id, frequency):
    filter = {"_id": ObjectId(user_id)}
    new_values = {"$set": {
        "access_frequency": frequency
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def remove_user(id):
    result = user.delete_one({'_id': ObjectId(id)})
    return result


def find_user_by_email(email):
    user_result = user.find_one({'email': email})
    return user_result


def get_user_nickname(user_id):
    user_result = user.find_one({'_id': user_id})
    return user_result["nickname"]

def get_last_access(user_id):
    user_result = user.find_one({'_id': ObjectId(user_id)})
    print(user_result)
    return user_result["last_access"]

def get_user_profile_picture(user_id):
    user_result = user.find_one({'_id': user_id})
    avatar_id = user_result["avatars"][0]
    avatar_url = get_avatar_url(avatar_id)
    return avatar_url

def get_access_frequency(user_id):
    user_result = user.find_one({'_id': ObjectId(user_id)})
    return user_result["access_frequency"]

def get_user_points_and_last_points(user_id):
    user_result = user.find_one({'_id': ObjectId(user_id)})
    return user_result["points"], user_result["last_points_received"]

def add_completed_route(user_id, route_id):
    filter = {"_id": ObjectId(user_id)}
    new_values = {"$push": {
        "completed_routes": ObjectId(route_id)
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully


def get_ranking_information():
    users_ordered_by_points = user.find({}).sort('points', pymongo.DESCENDING)
    processed_users = []
    for usr in users_ordered_by_points: 
        user_info = {}
        user_id_str = str(usr["_id"])
        avatar_object_id = usr["avatars"][0] 
        avatar_url = get_avatar_url(avatar_object_id)
        user_info = {"_id": user_id_str, "nickname": usr["nickname"], "avatar": avatar_url, "points": usr["points"]}
        processed_users.append(user_info)
    return processed_users


def get_user_points(user_id):
    user_result = user.find_one({'_id': ObjectId(user_id)})
    return user_result["points"]


def get_user_available_points(user_id):
    user_result = user.find_one({'_id': ObjectId(user_id)})
    return user_result["available_points"]

def update_points(user_id, points_number):
    filter = {"_id": ObjectId(user_id)}
    new_values = {"$inc": {
        "points": points_number
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def update_available_points(user_id, points_number):
    filter = {"_id": ObjectId(user_id)}
    new_values = {"$inc": {
        "available_points": points_number
    }}
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully

def add_item_to_collection(user_id, item_id, item_type, points_after_buying):
    filter = {"_id": ObjectId(user_id)}
    new_values = {"$set": {
        "available_points": points_after_buying
    }}
    result = user.update_one(filter, new_values)
    if item_type == "HEADER":
        new_values = {"$push": {
            "headers": ObjectId(item_id)
        }}  
    elif item_type == "BADGE":
        new_values = {"$push": {
            "badges": ObjectId(item_id)
        }} 
    elif item_type == "AVATAR":
        new_values = {"$push": {
            "avatars": ObjectId(item_id)
        }} 
    result = user.update_one(filter, new_values)
    if result.matched_count != 1:
        return False  # no document was updated
    else:
        return True  # the document was updated succesfully