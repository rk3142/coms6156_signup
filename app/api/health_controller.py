from operator import add
import re
from flask import jsonify, request, url_for, current_app, json, Response
from . import health
from flask_dance.contrib.google import google
from . import google_bp

@health.route('/', methods = ['GET'])
def respond_to_aws():
    google_data = None
    user_info_endpoint = '/outh2/v2/userinfo'
    if google.authorized:
        google_data = google.get(user_info_endpoint)

        print(google_data)
        print(json.dumps(google_data), indent = 2)
        bp = google_bp.blueprints.get("google")
        session = bp.session
        token = session.token

        print("Token [" + str(token) + "]")
        return jsonify(google_data)
    #return Response(status=200)
