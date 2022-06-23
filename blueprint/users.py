import json
from datetime import datetime
from flask import Blueprint, request, Response, jsonify
from bson import json_util, ObjectId


# ENTITIES
import database_entities.user as user
import database_entities.item as item
import database_entities.route as route
import database_entities.token as token
from data.points import FREQUENCY, LOGIN_FREQUENTLY, MAKE_ROUTE_FREQUENTLY, SIGNUP
from data.routes_processing import do_route, calculate_distance_and_time, get_points_to_assign, delete_duplicates

# Firebase
import firebase.firebase as firebase_management

users = Blueprint('users', __name__)


@users.route('/favicon.ico')
def favicon():
    return "/static/images/favicon.ico", 200


@users.route('/')
def init():
    return "Hola, soy el servidor Flask!"


@users.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    logged_user = user.find_user_by_email(email)
    if logged_user != None:
        user_id = str(logged_user["_id"])
        print(user_id)

        token_value = token.get_token_value(user_id)
        encoded_token = token.encode_token_value(token_value)
        token.store_token_value(token_value)

        last_login = user.get_last_access(user_id)
        last_login_lower_bound = last_login + user.TWENTY_THREE_HOURS_SECONDS
        last_login_upper_bound = last_login + user.TWENTY_FIVE_HOURS_SECONDS
        access_frequency = user.get_access_frequency(user_id)
        print(access_frequency)
        if access_frequency == -1 or last_login_lower_bound <= datetime.now().timestamp() <= last_login_upper_bound:
            user.update_last_access(user_id)
            access_frequency = (access_frequency + 1) % 7
            user.update_access_frequency(user_id, access_frequency)
            points_updated = user.update_points(
                user_id, LOGIN_FREQUENTLY[access_frequency])
            user.update_available_points(
                user_id, LOGIN_FREQUENTLY[access_frequency])
            if points_updated:
                user.update_last_points_received(
                user_id, LOGIN_FREQUENTLY[access_frequency])
                response = jsonify({
                    'id': user_id,
                    'token': encoded_token
                })
            else:
                response = jsonify({
                    'message': 'No se ha podido actualizar la puntuación del usuario.'
                })
        elif datetime.now().timestamp() > last_login_upper_bound:
            user.update_last_access(user_id)
            access_frequency = 0
            # More than 24h without logging in so points fall back to 5
            user.update_access_frequency(user_id, access_frequency)
            points_updated = user.update_points(
                user_id, LOGIN_FREQUENTLY[access_frequency])
            user.update_available_points(
                user_id, LOGIN_FREQUENTLY[access_frequency])
            user.update_last_points_received(
                user_id, LOGIN_FREQUENTLY[access_frequency])
            if points_updated:
                response = jsonify({
                    'id': user_id,
                    'token': encoded_token
                })
            else:
                response = jsonify({
                    'message': 'No se ha podido actualizar la puntuación del usuario.'
                })
        else:
            user.update_last_points_received(user_id, 0) #The user does not receive points because he received them previously
            response = jsonify({
                'id': user_id,
                'token': encoded_token
            })
        return response
    else:
        return not_found("No se ha encontrado el usuario")


@users.route('/users', methods=['POST'])
def create_user():
    email = request.json.get('email')
    nickname = request.json.get('nickname')
    result = user.create_user(email, nickname)
    if result:
        new_user = user.find_user_by_email(email)
        user_id = str(new_user["_id"])
        user.update_last_points_received(
                user_id, SIGNUP)

        token_value = token.get_token_value(user_id)
        encoded_token = token.encode_token_value(token_value)
        token.store_token_value(token_value)

        response = jsonify({
            'id': user_id,
            'token': encoded_token
        })
        return response
    else:
        return server_error("No se ha podido crear el nuevo usuario")


@users.route('/users/<id>', methods=['GET'])
def get_user_information(id):
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(id)
            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + id)
            else:
                requested_user["avatars"] = item.process_items_information(
                    requested_user["avatars"])
                requested_user["headers"] = item.process_items_information(
                    requested_user["headers"])
                requested_user["badges"] = item.process_items_information(
                    requested_user["badges"])
                requested_user["completed_routes_number"] = user.get_completed_routes_number(
                    id)
                ordered_routes = route.get_users_public_routes_ordered_by_date_descending(
                    id)
                ranking_positions = user.get_ranking_information()
                index = 0
                not_found = True
                while not_found and index < len(ranking_positions):
                    if ranking_positions[index]["_id"] == id:
                        not_found = False
                    index = index + 1
                # The index contains the position in the list + 1
                requested_user["ranking"] = index
                processed_routes = route.process_routes_information(ordered_routes)
                requested_user["routes"] = processed_routes
                response = json.loads(json_util.dumps(requested_user))
                return response
        else:
            return unauthorized("Credenciales inválidas para obtener la información del usuario, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@users.route('/users/<id>', methods=['PUT'])
def update_user_information(id):
    nickname = request.json.get('nickname')
    avatar = request.json.get('avatar')
    header = request.json.get('header')
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(id)
            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + id)
            else:
                result = user.update_information(id, nickname, avatar, header)
                if result:
                    response = jsonify({'id': id})
                    return response
                else:
                    return server_error("No se ha actualizado el usuario con id: " + id)
        else:
            return unauthorized("Credenciales inválidas para actualizar tu perfil, no estás autorizado")
    else:
        return unauthorized("Token mal formado")

@users.route('/users/<id>', methods=['DELETE'])
def delete_user(id):
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(id)
            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + id)
            else:
                email = requested_user["email"]
                firebase_management.delete_firebase_user_by_email(email)
                user.remove_user(id)
                route.invalidate_users_routes(id)
                token.delete_token_value(decoded_token_value)
                response = jsonify({'message': 'OK'})
                return response
        else:
            return unauthorized("Credenciales inválidas para eliminar tu perfil, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@users.route('/logout', methods=['GET'])
def logout():
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            token.delete_token_value(decoded_token_value)
            response = jsonify({'message': 'OK'})
            return response
        else:
            return unauthorized("Credenciales inválidas para cerrar sesión, no estás autorizado")
    else:
        return unauthorized("Token mal formado")



@users.route('/users/<id>/points', methods=['GET'])
def get_user_points(id):
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(id)
            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + id)
            else:
                points, last_points = user.get_user_points_and_last_points(id)
                available_points = user.get_user_available_points(id)
                response = jsonify(
                    {'points': last_points,
                    'user_points': points,
                    'available_points': available_points})
                return response
        else:
            return unauthorized("Credenciales inválidas para obtener los puntos, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@users.route('/users/<user_id>/routes/<route_id>', methods=['POST'])
def do_route_by_user(user_id, route_id):
    user_coordinates = request.json.get('coordinates')
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(user_id)
            target_route = route.get_route(route_id)

            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + user_id)
            elif target_route is None:
                return not_found("No se ha encontrado la ruta con id: " + route_id)
            else:
                total_distance, total_time, exercise_time, filtered_user_coordinates = calculate_distance_and_time(
                    user_coordinates)
                print("-----------------------------------------------------------")
                print(filtered_user_coordinates)
                print("-----------------------------------------------------------")
                print("Tiempo total " + str(total_time) +
                    " tiempo haciendo ejercicio " + str(exercise_time))
                print("-----------------------------------------------------------")
                print("Puntos filtrados: " + str(len(filtered_user_coordinates)))
                print("-----------------------------------------------------------")
                print("Puntos originales: " + str(len(user_coordinates)))
                print("-----------------------------------------------------------")
                print(target_route["coordinates"])
                completed_route = do_route(
                    filtered_user_coordinates, target_route["coordinates"])
                if completed_route:
                    route.add_new_time_to_complete(
                        route_id, user_id, total_time, exercise_time)
                    route.update_route_frequency(route_id)
                    user_is_author = route.check_user_is_author(user_id, route_id)
                    if not user_is_author:
                        user.add_completed_route(user_id, route_id)
                    slow, fast = route.get_slow_and_fast_time(route_id)
                    completed_routes_user = list(user.get_completed_routes(user_id))
                    route_frequency = completed_routes_user.count(ObjectId(route_id))
                    print("Frecuencia de la ruta")
                    print(route_frequency)
                    frequency_points = 0
                    if route_frequency >= FREQUENCY:
                        frequency_points = MAKE_ROUTE_FREQUENTLY
                        completed_routes_user_no_duplicates = delete_duplicates(
                            completed_routes_user)
                        user.update_completed_routes(
                            user_id, completed_routes_user_no_duplicates)
                    points = get_points_to_assign(slow, fast, exercise_time)
                    points_updated = user.update_points(
                        user_id, points + frequency_points)
                    user.update_available_points(
                        user_id, points + frequency_points)
                    if points_updated:
                        user_points = user.get_user_points(user_id)
                        response = jsonify({
                            'points': points,
                            'user_points': user_points,
                            'frequency_points': frequency_points
                        })
                    else:
                        response = jsonify({
                            'message': 'No se ha podido actualizar la puntuación del usuario.'
                        })
                else:
                    response = jsonify(
                        {'message': 'No ha cubierto el número de puntos mínimo para completar la ruta'})
                return response
        else:
            return unauthorized("Credenciales inválidas para realizar la ruta de un usuario, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@users.route('/users/<user_id>/routes/<route_id>', methods=['DELETE'])
def remove_completed_route(user_id, route_id):
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(user_id)
            target_route = route.get_route(route_id)

            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + user_id)
            elif target_route is None:
                return not_found("No se ha encontrado la ruta con id: " + route_id)
            else:
                result = user.remove_completed_route(user_id, route_id)
                if result:
                    response = jsonify({'message': 'OK'})
                    return response
                else:
                    return server_error("No se ha podido eliminar de la lista de rutas completadas por el usuario " + requested_user["nickname"] + " la ruta " + target_route["name"])
        else:
            return unauthorized("Credenciales inválidas para eliminar una de las rutas completadas, no estás autorizado")
    else:
        return unauthorized("Token mal formado")

@users.route('/users/<id>/routes', methods=['GET'])
def get_user_routes(id):
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(id)

            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + id)
            else:
                owned_routes = route.get_users_owned_routes_ordered_by_date_descending(id)
                owned_routes_processed = route.process_routes_information(owned_routes)
                # Array of ObjectId with the routes the user completed
                completed_routes = user.get_completed_routes(id)
                completed_routes_information = route.get_routes_information(
                    completed_routes)
                completed_routes_information_processed = route.process_routes_information(
                    completed_routes_information)
                #Removing duplicates from the list of completed routes
                completed_routes_information_processed_final_list = []
                for completed_route in completed_routes_information_processed:
                    if completed_route not in completed_routes_information_processed_final_list:
                        completed_routes_information_processed_final_list.append(completed_route)
                response_dict = {
                    "owned_routes": owned_routes_processed,
                    "completed_routes": completed_routes_information_processed_final_list
                }
                response = json_util.dumps(response_dict)
                return Response(response, mimetype='application/json')
        else:
            return unauthorized("Credenciales inválidas para obtener las rutas de un usuario, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@users.route('/users/<id>/items', methods=['GET'])
def get_items_and_user_items(id):
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(id)
            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + id)
            else:
                avatars = item.get_avatars()
                headers = item.get_headers()
                badges = item.get_badges()
                users_avatars = item.process_users_items_information(
                    avatars, requested_user["avatars"])
                users_headers = item.process_users_items_information(
                    headers, requested_user["headers"])
                users_badges = item.process_users_items_information(
                    badges, requested_user["badges"])
                available_points = user.get_user_available_points(id)
                response_dict = {
                    "avatars": users_avatars,
                    "headers": users_headers,
                    "badges": users_badges,
                    "available_points": available_points
                }
                response = json_util.dumps(response_dict)
                return Response(response, mimetype='application/json')
        else:
            return unauthorized("Credenciales inválidas para obtener los elementos de la tienda, no estás autorizado")
    else:
        return unauthorized("Token mal formado")

@users.route('/users/<user_id>/items/<item_id>', methods=['PUT'])
def buy_item(user_id, item_id):
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            requested_user = user.get_user(user_id)
            requested_item = item.get_item(item_id)
            if requested_user is None:
                return not_found("No se ha encontrado el usuario con id: " + user_id)
            elif requested_item is None:
                return not_found("No se ha encontrado el artículo con id: " + item_id)
            else:
                user_points = requested_user["available_points"]
                item_points = requested_item["points"]
                if user_points >= item_points:
                    #User can buy the item
                    points_after_buying = user_points - item_points
                    user.add_item_to_collection(user_id, item_id, requested_item["type"], points_after_buying)
                    remaining_points = user.get_user_available_points(user_id)
                    response = jsonify({
                        'message': '¡Has añadido el artículo a tu colección! 🤭 ¡Continúa así para conseguir más puntos y canjearlos en la tienda! 😉 Tras esta compra tienes ' + str(remaining_points) + ' puntos disponibles. 👏'
                    })
                else:
                    #User can't buy the item
                    response = jsonify({
                            'message': 'No tienes los suficientes puntos para comprar el artículo. 😥'
                    }) 
                return response 
        else:
            return unauthorized("Credenciales inválidas para comprar un artículo, no estás autorizado")
    else:
        return unauthorized("Token mal formado")

# Error 400


@users.errorhandler(400)
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

# Error 404


@users.errorhandler(404)
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



@users.errorhandler(401)
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

# Error 500


@users.errorhandler(500)
def server_error(error):
    response = jsonify({
        'message': 'Server error: ' + request.url,
        'status': 500
    })
    response.status_code = 500
    return response
