import re
from flask import jsonify, request, url_for, current_app, Response
from sqlalchemy.sql.functions import user
from models.address import Address
from . import api
from models.users import User
from app import app, db
from error import bad_request, unauthorized, resouce_already_exists, internal_server_error, resource_not_found
from datetime import datetime


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
        users = User.query.all()
        return jsonify(users = User.list_to_json(users))
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
        user = User.query.get_or_404(id)
        return jsonify(user.to_json())
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_user_details")
        return internal_server_error("Internal server error")

@api.route('/user/<int:id>/update_password', methods=['POST','PUT'])
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

@api.route('/user/<int:id>', methods=['DELETE'])
def deactivate_profile(id):
    try:
        user = User.query.get_or_404(id)
        password = request.get_json().get('password')
        if user.password == password:
            user.status = 0
            db.session.add(user)
            db.session.commit()
            status_code = Response(status=200)
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
            request_json = request.data
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
            {'Location': url_for('api.get_address_by_id', id=user_db.id)}
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
        if users is not None:
            address = Address.query.filter_by(id = users.address_id).first()
            print(address)
            return jsonify(User.to_json_address(users, address))
        else:
            return resource_not_found("No user exists for address")
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_users_by_address")
        return internal_server_error("Internal server error")