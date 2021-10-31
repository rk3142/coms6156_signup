from operator import add
import re
from flask import jsonify, request, url_for, current_app, json, Response
from . import health
from flask_dance.contrib.google import google
from . import google_bp

@health.route('/', methods = ['GET'])
def respond_to_aws():
    return Response(status=200)


@health.route("/site-map")
def list_routes():
    routes = []

    print(current_app.url_map)
    for rule in current_app.url_map.iter_rules():
        routes.append('%s' % rule)

    return jsonify(routes= routes)