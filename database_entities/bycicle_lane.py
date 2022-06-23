from mongoDB import bycicle_lane

#This method returns a list containing dicts with latitude and longitude.
def process_data(coordinates_list):
    result = []
    for coordinate in coordinates_list:
        #In case latitude or longitude fields dont exist in dictionary, it returns 0.
        result.append({"latitude": coordinate.get('latitude', 0), "longitude": coordinate.get('longitude', 0)})
    return result


def get_bycicle_lanes():
    bycicle_lanes = bycicle_lane.find()
    return bycicle_lanes


def create_bycicle_lane(coordinates):
    try:
        bycicle_lane.insert_one(
            {
                "coordinates": coordinates
            }
        )
        return True
    except Exception as e:
        print("An exception occurred ::", e)
        return False

def remove_bycicle_lane(bycicle_lane_object_id):
    result = bycicle_lane.delete_one({'_id': bycicle_lane_object_id})
    return result



