from flask import Blueprint, request, jsonify, Response
from data.bycicle_lanes_processing import check_filtered_coordinates_are_in_database, check_if_its_longer_than_the_bycicle_lane, check_filtered_coordinates_are_in_open_data, get_open_data_bycicle_lanes, remove_closest_points
from bson import json_util

#ENTITIES 
import database_entities.bycicle_lane as bycicle_lane
import database_entities.user as user
import database_entities.token as token
from data.points import NEW_BYCICLE_LANE

bycicle_lanes = Blueprint('bycicle_lanes', __name__)


@bycicle_lanes.route('/byciclelanes', methods=['GET'])
def get_bycicle_lanes():
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            official_list = get_open_data_bycicle_lanes()
            bycicle_lanes_users = bycicle_lane.get_bycicle_lanes()
            unofficial_list = []
            for individual_bycicle_lane in bycicle_lanes_users:
                segment_coordinates = []
                for bycicle_lane_coordinates in individual_bycicle_lane["coordinates"]:
                    segment_coordinates.append([bycicle_lane_coordinates.get('longitude'), bycicle_lane_coordinates.get('latitude')])
                unofficial_list.append(segment_coordinates)
            
            official_dict = {}
            key = 0 
            for coordinates_array in official_list:
                official_dict[key] = coordinates_array 
                key += 1 
            
            unofficial_dict = {}
            key = 0 
            for coordinates_array in unofficial_list:
                unofficial_dict[key] = coordinates_array 
                key += 1 
            
            result_dict = {"official": official_dict, "unofficial": unofficial_dict}
            response = json_util.dumps(result_dict)    
            return Response(response, mimetype='application/json')
        else:
            return unauthorized("Credenciales inválidas para obtener los carriles bici, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@bycicle_lanes.route('/byciclelanes', methods=['POST'])
def add_bycicle_lane():
    coordinates = request.json.get('coordinates')
    author = request.json.get('author')
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            give_points = False
            filtered_coordinates = remove_closest_points(coordinates)
            filtered_coordinates = bycicle_lane.process_data(filtered_coordinates) #[{},{},{},{}]
            if len(filtered_coordinates) > 0: #By checking this we avoid DB documents with an empty coordinates list 
                present, segment = check_filtered_coordinates_are_in_open_data(filtered_coordinates)
                present_in_db, bycicle_lane_db = check_filtered_coordinates_are_in_database(filtered_coordinates)
                if not present and not present_in_db:
                        bycicle_lane.create_bycicle_lane(filtered_coordinates)
                        give_points = True
                else:
                    longer = check_if_its_longer_than_the_bycicle_lane(segment, filtered_coordinates)
                    if longer and not present_in_db:
                            bycicle_lane.create_bycicle_lane(filtered_coordinates)
                            give_points = True
                
                present_in_db, bycicle_lane_db = check_filtered_coordinates_are_in_database(filtered_coordinates)
                if not present_in_db:
                    bycicle_lane.create_bycicle_lane(filtered_coordinates)
                    give_points = True
                else:
                    longer = check_if_its_longer_than_the_bycicle_lane(bycicle_lane_db["coordinates"], filtered_coordinates)
                    if longer:
                        bycicle_lane.create_bycicle_lane(filtered_coordinates)
                        bycicle_lane.remove_bycicle_lane(bycicle_lane_db["_id"])
                        give_points = True
            else:
                response = jsonify({
                    'message': 'Las coordenadas proporcionadas para crear el carril bici son cercanas entre sí.'
                })
                return response   

            if give_points: 
                points_updated = user.update_points(author, NEW_BYCICLE_LANE)
                user.update_available_points(author, NEW_BYCICLE_LANE)
                if points_updated:
                    user_points = user.get_user_points(author)
                    response = jsonify({
                        'points': NEW_BYCICLE_LANE,
                        'user_points': user_points
                    })
                    return response
                else:
                    response = jsonify({
                        'message': 'No se ha podido actualizar la puntuación del usuario.'
                    })
                    return response
            else:
                response = jsonify({
                        'message': 'El carril bici que intentas añadir ya está registrado o es un carril bici oficial.'
                    })
                return response
        else:
            return unauthorized("Credenciales inválidas para añadir un tramo de carril bici, no estás autorizado")
    else:
        return unauthorized("Token mal formado")        

@bycicle_lanes.errorhandler(401)
def unauthorized(error=None):
    if error is None:
        response = jsonify({
            'message': 'Not authorized: ' + request.url,
            'status': 401
        })
    else:
        response = jsonify({
            'message': error,
            'status': 401
        })
    response.status_code = 401
    return response