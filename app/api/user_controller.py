import re
from flask import jsonify, request, redirect, url_for, current_app, Response, render_template, session
from sqlalchemy.sql.functions import user
from models.address import Address
from . import api
from models.users import User
from app import db
from error import bad_request, unauthorized, resouce_already_exists, internal_server_error, resource_not_found
from datetime import datetime
from . import google_bp
from flask_dance.contrib.google import google
import json
from utils.query_creator import QueryCreator
import config.constants as CONSTANTS
from middleware.notification import NotificationMiddlewareHandler

@google_bp.route('/register', methods=['POST', 'GET'])
def register():
    google_data = None
    user_info_endpoint = '/oauth2/v2/userinfo'
    if google.authorized:
        google_data = google.get(user_info_endpoint).json()
        email_address = google_data.get('email')
        [uni, domain] = email_address.split('@')
        if domain != CONSTANTS.DOMAIN_NAME:
            return unauthorized("This application is only for Columbia Affiliates")

        already_exists = User.check_account_already_exists(email_address)
        if already_exists:
            return resouce_already_exists("You are already registered with us")

        bp = current_app.blueprints.get("google")
        session = bp.session
        # token = session.token

        user_obj = User(id = google_data.get('id'),
                        first_name = google_data.get('given_name'),
                        last_name = google_data.get('family_name'),
                        username = uni,
                        email = email_address,
                        address_id = 2,
                        status = 1)

        db.session.add(user_obj)
        db.session.commit()

        user_resp = user_obj.to_dict()
        ''''
        NotificationMiddlewareHandler.send_sns_message(
                                                        "arn:aws:sns:us-east-2:892513566331:app-topic",
                                                        User.to_json(user_resp))
        '''
        return jsonify(User.to_json(user_resp)), 201, \
                    {'Location': url_for('api.get_user_details', id=user_obj.id)}
        return jsonify(google_data)
    else:
        return redirect(url_for("google.login"))


@api.route('/addresses/<int:id>/users', methods = ['POST'])
def create_new_users(id):
    current_app.logger.info('Processing request to create new user')
    try:
        if request.data:
            user = User.from_json(request.get_json(force=True), address_id=id)
            if not User.check_account_already_exists(user.email):
                if User.check_username_exists(user.username):
                    db.session.add(user)
                    db.session.commit()
                    user = User.query.get_or_404(user.id)
                    return jsonify(user.to_json()), 201, \
                    {'Location': url_for('api.get_user_details', id=user.id)}
                else:
                    current_app.logger.warn("username already exists")
                    return resouce_already_exists("username already exists")
            else:
                current_app.logger.warn("Email already exists")
                return resouce_already_exists("Email already exists")
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: create_new_users")
        return internal_server_error("Internal server error")

@api.route('/users', methods = ['GET'])
def get_all_users():
    current_app.logger.info('Processing request to get all users')
    try:
        request_args = request.args.to_dict()
        if not request_args:
            users = []
            for user in User.query.all():
                users.append(QueryCreator.row2dict(user))
        else:
            query_string = QueryCreator.get_sql_query('users', request_args)
            users = Address.custom_query(query_string)

        return jsonify(users = User.list_to_json(users), links = User.get_pagination_data(request, id=None))
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_all_users")
        return internal_server_error("Internal server error")

@api.route('/login', methods = ['POST'])
def login_user():
    current_app.logger.info('Proceeding to process request login request for user')
    try:
        if request.data:
            request_json = request.get_json(force=True)
            if request_json.get('email') is not None:
                user_id = User.validate_email_and_password(password=request_json.get('password'), email=request_json.get('email'))
                print(user_id)
                if user_id is not None:
                    user = User.query.get_or_404(user_id)
                    return jsonify(user.to_json()), 201, \
                    {'Location': url_for('api.get_user_details', id=user_id)}
                else:
                    return unauthorized("Incorrect combination of email and password")

            elif request_json.get('username') is not None:
                user_id = User.validate_email_and_password(password=request_json.get('password'), username=request_json.get('username'))
                if user_id is not None:
                    user = User.query.get_or_404(user_id)
                    return jsonify(user.to_json()), 201, \
                    {'Location': url_for('api.get_user_details', id=user_id)}
                else:
                    return unauthorized("Incorrect combination of username and password")
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        current_app.logger.exception("Exception occured while processing function: login_user")
        return internal_server_error("Internal server error")


@api.route('/users/<int:id>', methods=['GET'])
def get_user_details(id):
    current_app.logger.info('Proceeding to process get_user_details for user {id}')
    try:
        request_args = request.args.to_dict()
        if not request_args:
            user = User.query.get(id)
            if not user:
                return Response(status=404)
            user = user.to_dict()
        else:
            request_args['id'] = id
            query_string = QueryCreator.get_sql_query('users', request_args)
            user = Address.custom_query(query_string)

        return jsonify(User.to_json(user))
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_user_details")
        return internal_server_error("Internal server error")

@api.route('/user/<int:id>/update_password', methods=['POST',	'PUT'])
def update_password(id):
    try:
        user = User.query.get_or_404(id)
        previous_password = request.get_json().get('previous_password')
        print(User.get_user_password(id)[0])
        if User.get_user_password(id)[0] == previous_password:
            user.password = request.get_json(force=True).get('password')
            db.session.add(user)
            db.session.commit()
            return jsonify(user.to_json()), 201, \
                {'Location': url_for('api.get_user_details', id=user.id)}
        else:
            return unauthorized("Invalid password provided")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: update_password")
        return internal_server_error("Internal server error")

@api.route('/users/<int:id>', methods=['DELETE'])
def deactivate_profile(id):
    try:
        user = User.query.get_or_404(id)
        password = request.get_json().get('password')
        if user.password == password:
            user.status = 0
            db.session.add(user)
            db.session.commit()
            status_code = Response(status=204)
            return status_code
        else:
            return unauthorized("Invalid password provided")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: deactivate_profile")
        return internal_server_error("Internal server error")

@api.route('/users/<int:id>', methods = ['PUT'])
def update_user_by_id(id):
    current_app.logger.info(f'Proceeding to update record of user with id={id}')
    try:
        if request.data:
            request_json = request.get_json()
            user_db = User.query.get_or_404(id)
            user_db.first_name = request_json.get('first_name')
            user_db.last_name = request_json.get('last_name')
            user_db.gender = request_json.get('gender')
            user_db.bio = request_json.get('bio')
            user_db.dob = datetime.strptime(request_json.get('dob'), '%Y-%m-%d')
            db.session.add(user_db)
            db.session.commit()
            user_resp = User.query.get_or_404(user_db.id)
            return jsonify(user_db.to_json()), 201, \
            {'Location': url_for('api.get_user_details', id=user_resp.id)}
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: update_address_by_id")
        return internal_server_error("Internal server error")

@api.route('/users/<int:id>/address', methods = ['GET'])
def get_address_by_user(id):
    current_app.logger.info(f"Proceeding to get the list of address of user with id={id}")
    try:
        users = User.query.filter_by(id=id).first()
        users = users.to_dict()
        if users is not None:
            address = Address.query.filter_by(id = users['address_id']).first()
            address = address.to_dict()
            return jsonify(User.to_json_address(users, address))
        else:
            return resource_not_found("No user exists for address")
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_users_by_address")
        return internal_server_error("Internal server error")

@api.route('/users', methods = ['POST'])
def create_new_user_with_address():
    current_app.logger.info('Processing request to create new user')
    try:
        if request.data:
            address_id = request.get_json().get('address_id')
            user = User.from_json(request.get_json(force=True), address_id=address_id)
            if not User.check_account_already_exists(user.email):
                if User.check_username_exists(user.username):
                    db.session.add(user)
                    db.session.commit()
                    user = User.query.get_or_404(user.id)
                    return jsonify(user.to_json()), 201, \
                    {'Location': url_for('api.get_user_details', id=user.id)}
                else:
                    current_app.logger.warn("username already exists")
                    return resouce_already_exists("username already exists")
            else:
                current_app.logger.warn("Email already exists")
                return resouce_already_exists("Email already exists")
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: create_new_users")
        return internal_server_error("Internal server error")