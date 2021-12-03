import re, os
from flask import jsonify, request, redirect, url_for, current_app, Response, make_response
from flask_session import Session
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
        bp = current_app.blueprints.get("google")
        session = bp.session
        if already_exists:
            user_obj = User.query.get_or_404(already_exists)
            user_resp = user_obj.to_dict()
            user_resp['is_profile_created'] = True
        else:
            
            user_resp = {}
            user_resp['id'] = google_data.get('id')
            user_resp['first_name'] = google_data.get('given_name')
            user_resp['last_name'] = google_data.get('family_name')
            user_resp['username'] = uni
            user_resp['email'] = email_address
            user_resp['is_profile_created'] = False
            user_resp['address_id'] = 0
        
        #print(str(session['id_token']))
        #Response.set_cookie('session', session['id_token'])

        '''
        response = Response(jsonify(user = User.to_json(user_resp), redirect_url = ""))
        response.set_cookie('session', request.cookies.get('session'))
        response.status_code = 302
        response.location = os.environ.get("UI_URL", None)+ "/user/" + google_data.get('id')
        return response
        '''
        print("Before session")
        response = make_response(redirect(os.environ.get("BACKEND_URL", None)+ "/update_sid?session=" + \
            request.cookies.get('session') + "&user_id=" + google_data.get('id')))
        return response

        '''
        return jsonify(user = User.to_json(user_resp), redirect_url = ""), 302, \
                    {'Location': os.environ.get("UI_URL", None)+ "/user/" + google_data.get('id'),
                    'Set-Cookie': 'session=' + request.cookies.get('session')}
        '''
        
    else:
        current_app.config.update(
            SESSION_COOKIE_DOMAIN=os.environ.get('BEANSTALK_DOMAIN')
        )
        
        return jsonify(user="", redirect_url = url_for('google.login')), 302

@api.route('/update_sid')
def update_session_id():
    
    params = request.args
    session_id = params.get('session')
    user_id = params.get('user_id')
    current_app.config.update(
        SESSION_COOKIE_DOMAIN=os.environ.get('')
    )
    response = make_response(redirect(os.environ.get("UI_URL", None)+ "/users/" + str(user_id)))
    response.set_cookie('session', session_id)
    return response
    

@api.route('/addresses/<int:id>/users', methods = ['POST'])
def create_new_users(id):
    current_app.logger.info('Processing request to create new user')
    try:
        if request.data:
            request_data = request.get_json()
            current_app.logger.info("Received request to create user = " + str(request_data))
            user_req_obj = request_data.get('Payload').get('user')
            user = User.from_json(user_req_obj, address_id=id)
            if not User.check_account_already_exists(user.email):
                if User.check_username_exists(user.username):
                    db.session.add(user)
                    db.session.commit()
                    user = User.query.get_or_404(user.id)
                    user_resp = user.to_dict()
                    user_resp['is_profile_created'] = True
                    return jsonify(user = User.to_json(user_resp)), 201, \
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


@api.route('/users/<string:id>', methods=['GET'])
def get_user_details(id):
    current_app.logger.info(f'Proceeding to process get_user_details for user {id}')
    try:
        request_args = request.args.to_dict()
        if not request_args:
            users = User.query.get(id)
            if not users:
                user_info_endpoint = '/oauth2/v2/userinfo'
                user_resp = {}
                user_resp['is_profile_created'] = False
                user_resp['id'] = id
                if google.authorized:
                    google_data = google.get(user_info_endpoint).json()
                    email_address = google_data.get('email')
                    [uni, domain] = email_address.split('@')
                    user_resp['id'] = google_data.get('id')
                    user_resp['first_name'] = google_data.get('given_name')
                    user_resp['last_name'] = google_data.get('family_name')
                    user_resp['username'] = uni
                    user_resp['email'] = email_address
                    user_resp['is_profile_created'] = False
                    user_resp['address_id'] = 0
                    user_resp['bio'] = ''
                    return jsonify(user=user_resp), 200
                else:
                    return jsonify(user=user_resp), 200
            user = users.to_dict()
            user['is_profile_created'] = True
        else:
            request_args['id'] = id
            query_string = QueryCreator.get_sql_query('users', request_args)
            user = Address.custom_query(query_string)[0]
        
        print(user)
        return jsonify(User.to_json(user))
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_user_details")
        return internal_server_error("Internal server error")

@api.route('/users/multiple', methods=['GET'])
def get_multiple_users():
    current_app.logger.info(f'Proceeding to get multiple users for user')
    try:
        request_args = request.args.to_dict()
        user_resp_list = []
        invalid_user_list = []
        if request_args:
            user_list = request_args.get('users').split(',')
            for user in user_list:
                user_resp = User.query.get(user)
                print(user_resp)
                if user_resp:
                    user_resp_list.append(user_resp.to_dict())
                else:
                    invalid_user_list.append(user)

        return jsonify(users=User.list_to_json(user_resp_list), invalid_users=invalid_user_list)
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_multiple_users")
        return internal_server_error("Internal server error")

@api.route('/user/<string:id>/update_password', methods=['POST',	'PUT'])
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

@api.route('/users/<string:id>', methods=['DELETE'])
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

@api.route('/users/<string:id>', methods = ['PUT'])
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
            user_db.profile_pic_id = request_json.get('profile_pic_id')
            db.session.add(user_db)
            db.session.commit()
            user_resp = User.query.get_or_404(user_db.id)
            user_resp = user_resp.to_dict()
            return jsonify(User.to_json(user_resp)), 201, \
            {'Location': url_for('api.get_user_details', id=user_resp['id'])}
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: update_address_by_id")
        return internal_server_error("Internal server error")

@api.route('/users/<string:id>/address', methods = ['GET'])
def get_address_by_user(id):
    current_app.logger.info(f"Proceeding to get the list of address of user with id={id}")
    try:
        users = User.query.filter_by(id=id).first()
        if users:
            users = users.to_dict()
            if users is not None:
                address = Address.query.filter_by(id = users['address_id']).first()
                address = address.to_dict()
                return jsonify(User.to_json_address(users, address))
            else:
                return resource_not_found("No user exists for address")
        else:
            return resource_not_found("User does not exists")
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_users_by_address")
        return internal_server_error("Internal server error")


@api.route('/update_address_id', methods = ['PUT'])
def update_address_id():
    current_app.logger.info("Proceeding to update address for user")
    try:
        if request.data:
            user_req_obj = request.get_json().get('Payload')
            user_id = user_req_obj.get('user').get('user_id')
            address_id = user_req_obj.get('address').get('address_id')
            user = User.query.get_or_404(user_id)
            user.address_id = address_id
            db.session.add(user)
            db.session.commit()
            user_resp = user.to_dict()
            user_resp['is_profile_created'] = True
            return jsonify(user = User.to_json(user_resp)), 201, \
            {'Location': url_for('api.get_user_details', id=user_resp['id'])}
        else:
            return bad_request(message='Invalid request format')
        
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: create_new_users")
        return internal_server_error("Internal server error")  
@api.route('/users', methods = ['POST'])
def create_new_user_with_address():
    current_app.logger.info('Processing request to create new user ' + str(request.data))
    try:
        if request.data:
            user_req_obj = request.get_json().get('Payload').get('user')
            address_id = user_req_obj.get('address_id')
            user = User.from_json(user_req_obj, address_id=address_id)
            if not User.check_account_already_exists(user.email):
                if User.check_username_exists(user.username):
                    db.session.add(user)
                    db.session.commit()
                    user = User.query.get_or_404(user.id)
                    user_resp = user.to_dict()
                    user_resp['is_profile_created'] = True
                    user_resp['address_id'] = address_id
                    return jsonify(user = User.to_json(user_resp)), 201, \
                    {'Location': url_for('api.get_user_details', id=user_resp['id'])}
                else:
                    current_app.logger.warn("username already exists")
                    return resouce_already_exists("username already exists")
            else:
                current_app.logger.warn("Email already exists")
                user_obj = User.query.get_or_404(user.id)
                user_resp = user_obj.to_dict()
                user_resp['is_profile_created'] = True
                return jsonify(user = User.to_json(user_resp)), 201, \
                {'Location': url_for('api.get_user_details', id=user_resp['id'])}
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: create_new_users")
        return internal_server_error("Internal server error")