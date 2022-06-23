from flask import Blueprint, request, jsonify, Response
from data.routes_processing import calculate_stops, calculate_distance_and_time, calculate_velocity
from bson import json_util

# ENTITIES
import database_entities.route as route
import database_entities.user as user
import database_entities.token as token
from data.points import NEW_ROUTE

routes = Blueprint('routes', __name__)


@routes.route('/routes', methods=['GET'])
def get_routes_ordered_by_most_recent_date():
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            ordered_routes = route.get_routes_ordered_by_date_descending()
            processed_routes = route.process_routes_information(ordered_routes)
            response = json_util.dumps(processed_routes)
            return Response(response, mimetype='application/json')
        else:
            return unauthorized("Credenciales inválidas para obtener las rutas, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@routes.route('/routes', methods=['POST'])
def create_route():
    route_name = request.json.get('name')  # string
    rate = request.json.get('rate')  # int but cast to float
    private = request.json.get('private')  # bool
    author = request.json.get('author')  # string
    coordinates = request.json.get('coordinates')  # list
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            total_distance, total_time, exercise_time, filtered_points = calculate_distance_and_time(
                coordinates)  # distance in meters

            print("After filter")
            print(filtered_points)
            print(len(filtered_points))
            number_of_stops = 0
            if len(coordinates) > 0 and len(filtered_points) > 0:
                number_of_stops = calculate_stops(
                    filtered_points, coordinates[0], coordinates[len(coordinates)-1])  # int with the number of stops
            general_velocity = 0
            velocity_during_exercise = 0
            if total_time > 0:
                general_velocity = calculate_velocity(
                total_distance, total_time)  # velocity in meters per second
            if exercise_time > 0:
                velocity_during_exercise = calculate_velocity(
                total_distance, exercise_time)
            print("Before filter")
            print(coordinates)
            print(len(coordinates))
            print("User stopped " + str(number_of_stops) + " times")
            print("Total distance: " + str(total_distance) + ", total time: " +
                str(total_time) + ", exercise time: " + str(exercise_time))
            print("User speed, general: " + str(general_velocity) +
                ", without stops: " + str(velocity_during_exercise))
            if len(filtered_points) > 0:
                result = route.create_route(route_name, rate, private, author, filtered_points, velocity_during_exercise, general_velocity,
                                  total_distance, number_of_stops, total_time, exercise_time)
                if result:
                    points_updated = user.update_points(author, NEW_ROUTE)
                    user.update_available_points(author, NEW_ROUTE)
                    if points_updated:
                        user_points = user.get_user_points(author)
                        response = jsonify({
                            'points': NEW_ROUTE,
                            'user_points': user_points
                        })
                        return response
                    else:
                        response = jsonify({
                            'message': 'No se ha podido actualizar la puntuación del usuario'
                        })
                        return response
            else:
                response = jsonify({
                    'message': 'Las coordenadas proporcionadas para crear la ruta son cercanas entre sí.'
                })
                return response
        else:
            return unauthorized("Credenciales inválidas para crear una ruta, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@routes.route('/routes/<id>', methods=['PUT'])
def update_route_information(id):
    route_name = request.json.get('name')  # string
    private = request.json.get('private')  # bool
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_route = route.get_route(id)
            if requested_route is None:
                return not_found("No se ha encontrado la ruta con id: " + id)
            else:
                result = route.update_route_information(id, route_name, private)
                if result:
                    response = jsonify({'id': id})
                    return response
                else:
                    return not_found("No se ha actualizado la ruta con id: " + id)
        else:
            return unauthorized("Credenciales inválidas para actualizar la información de la ruta, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@routes.route('/routes/<id>', methods=['DELETE'])
def delete_route(id):
    author = request.json.get('author')  # string
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_route = route.get_route(id)
            if requested_route is None:
                return not_found("No se ha encontrado la ruta con id: " + id)
            else:
                result = route.invalidate_author_field_change_visibility(id, author)
                if result:
                    response = jsonify({'id': id})
                    return response
                else:
                    return not_found("No se ha borrado la ruta con id: " + id)
        else:
            return unauthorized("Credenciales inválidas para eliminar la ruta, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


# Error 400


@routes.errorhandler(400)
def not_found(error=None):
    if error is None:
        response = jsonify({
            'message': 'Bad request: ' + request.url,
            'status': 400
        })
    else:
        response = jsonify({
            'message': error,
            'status': 400
        })
    response.status_code = 400
    return response


@routes.errorhandler(401)
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

# Error 404


@routes.errorhandler(404)
def not_found(error=None):
    if error is None:
        response = jsonify({
            'message': 'Not found: ' + request.url,
            'status': 404
        })
    else:
        response = jsonify({
            'message': error,
            'status': 404
        })
    response.status_code = 404
    return response
