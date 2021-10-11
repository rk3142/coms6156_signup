from flask import jsonify
from exceptions import ValidationError
from api import api


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response

def resouce_already_exists(message):
    response = jsonify({'error': 'resouce_already_exists', 'message': message})
    response.status_code = 409
    return response

def resource_not_found(message):
    response = jsonify({'error': 'resource_not_found', 'message': message})
    response.status_code = 404
    return response

def internal_server_error(message):
    response = jsonify({'error': 'We are facing some technical difficulties. Please try after sometime.', 'message': message})
    response.status_code = 500
    return response


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])