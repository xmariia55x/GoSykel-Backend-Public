from mongoDB import item
from bson import ObjectId

def get_item(id):
    item_result = item.find_one({'_id': ObjectId(id)})
    return item_result
    
def process_items_information(object_list):
    items_processed = []
    for object in object_list:
        item_result = item.find_one({'_id': ObjectId(object)})
        items_processed.append({'_id': str(item_result["_id"]), 'name': item_result["name"],
                               'description': item_result["description"], 'location': item_result["location"]})
    return items_processed


def get_first_avatar():
    avatar = str(item.find_one({'type': 'AVATAR', 'first': True})["_id"])
    return avatar


def get_first_header():
    header = str(item.find_one({'type': 'HEADER', 'first': True})["_id"])
    return header


def get_first_badge():
    badge = str(item.find_one({'type': 'BADGE', 'first': True})["_id"])
    return badge


def get_avatar_url(avatar_id):
    avatar_url = item.find_one({'_id': avatar_id})["location"]
    return avatar_url


def get_avatars():
    avatars = item.find({'type': 'AVATAR'})
    return avatars


def get_headers():
    headers = item.find({'type': 'HEADER'})
    return headers


def get_badges():
    badges = item.find({'type': 'BADGE'})
    return badges


def process_users_items_information(items_list, users_items):
    items_result = []
    for shop_item in items_list: 
        i = 0
        not_found = True
        while not_found and i < len(users_items):
            if str(shop_item.get('_id')) == str(users_items[i]):
                not_found = False #The user has bought that item 
                shop_item["bought"] = True 
            i = i + 1
        shop_item_object_id = shop_item["_id"]
        shop_item_id_string = str(shop_item_object_id)
        shop_item["_id"] = shop_item_id_string
        items_result.append(shop_item)
    return items_result
