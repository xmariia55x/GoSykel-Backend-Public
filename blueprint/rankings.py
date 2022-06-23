from flask import Blueprint, request, jsonify, Response
from bson import json_util

#ENTITIES 
import database_entities.user as user
import database_entities.token as token

rankings = Blueprint('rankings', __name__)

@rankings.route('/rankings', methods=['GET'])
def get_ranking():
    token_header = request.headers.get('Authorization')
    decoded_token = token.decode_token(token_header)
    decoded_token = token.decode_token(token_header)
    if decoded_token is not None:
        decoded_token_value = decoded_token.get('value')
        valid = token.token_value_is_valid(decoded_token_value)
        if valid:
            rankings = user.get_ranking_information()
            response = json_util.dumps(rankings)
            return Response(response, mimetype='application/json')
        else:
            return unauthorized("Credenciales inválidas para obtener la información del ranking, no estás autorizado")
    else:
        return unauthorized("Token mal formado")


@rankings.errorhandler(401)
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
