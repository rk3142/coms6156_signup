from operator import add
import re, json
from flask import jsonify, request, url_for, current_app, json, Response
from . import api
from models.address import Address
from models.users import User
from app import db
import config.constants as CONSTANTS
from utils.smarty_streets import AddressValidator
from utils.query_creator import QueryCreator
from error import bad_request, unauthorized, forbidden, resouce_already_exists, internal_server_error, resource_not_found


@api.route('/addresses', methods = ['GET'])
def get_all_addresses():
    current_app.logger.info('Processing request to get all address')
    try:
        request_args = request.args.to_dict()
        if not request_args:
            addresses = []
            for address in Address.query.all():
                request_args = None
                addresses.append(QueryCreator.row2dict(address))
        else:
            query_string = QueryCreator.get_sql_query('address', request_args)
            addresses = Address.custom_query(query_string)

        return jsonify(addresses = Address.list_to_json(addresses), links = Address.get_pagination_data(request))
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_all_addresses")
        return internal_server_error("Internal server error")

@api.route('/addresses', methods = ['POST'])
def add_new_address():
    current_app.logger.info('Proceeding to create a new record')
    try:
        if request.data:
            request_data = request.get_json()
            current_app.logger.info("The value of request_data is [" + str(request_data) + "]")
            address_json = request_data.get('Payload').get('address')
            '''
            ss_response = AddressValidator.validate_street_details(address_json)
            if ss_response is not None:
                ss_dict = json.loads(ss_response)[0]
                analysis = ss_dict.get('analysis')
                verfication_status = analysis.get('verification_status', None)
                if not (verfication_status is not None and verfication_status.lower() in CONSTANTS.SS_VERIFIED):
                    return resource_not_found("Address not verfied")    
            else:
                return resource_not_found(message='Address not verified')
            '''
            address = Address.from_json(address_json)
            db.session.add(address)
            db.session.commit()

            address = Address.query.get_or_404(address.id)
            address_resp = address.to_dict()
            return jsonify(address=Address.to_json(address_resp)), 201, \
            {'Location': url_for('api.get_address_by_id', id=address.id)}
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: add_new_address")
        return internal_server_error("Internal server error")

@api.route('/validate_address', methods = ['GET', 'POST'])
def validate_input_address():
    current_app.logger.info('Proceeding to validate address using smarty streets API')
    try:
        if request.data:
            ss_response = AddressValidator.validate_street_details(request.get_json())
            if ss_response is not None:
                    return jsonify(json.loads(ss_response)), 200
            else:
                return bad_request(message='Invalid request format')
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: add_new_address")
        return internal_server_error("Internal server error")

@api.route('/addresses/<int:id>', methods = ['GET'])
def get_address_by_id(id):
    current_app.logger.info(f'Processing request to details of address with id={id}')
    try:
        request_args = request.args.to_dict()
        if not request_args:
            addresses = Address.query.get(id)
            if not addresses:
                return Response(status=404)
            
            addresses = addresses.to_dict()
        else:
            request_args['id'] = id
            query_string = QueryCreator.get_sql_query('address', request_args)
            addresses = Address.custom_query(query_string)[0]
        return jsonify(addresses = Address.to_json(addresses))
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_address_by_id")
        return internal_server_error("Internal server error")

@api.route('/addresses/<int:id>', methods = ['PUT'])
def update_address_by_id(id):
    current_app.logger.info(f'Proceeding to update record of address with id={id}')
    try:
        if request.data:
            address = Address.from_json(request.get_json(force=True))
            address_db = Address.query.get_or_404(id)
            address_db.house_number = address.house_number
            address_db.street_name_1 = address.street_name_1
            address_db.street_name_2 = address.street_name_2
            address_db.city = address.city
            address_db.region = address.region
            address_db.country_code = address.country_code
            address_db.postal_code = address.postal_code
            db.session.add(address_db)
            db.session.commit()
            address_resp = Address.query.get_or_404(address_db.id)
            address_data = address_resp.to_dict()
            return jsonify(Address.to_json(address_data)), 201, \
            {'Location': url_for('api.get_address_by_id', id=address_db.id)}
        else:
            return bad_request(message='Invalid request format')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: update_address_by_id")
        return internal_server_error("Internal server error")


@api.route('/addresses/<int:id>', methods = ['DELETE'])
def delete_address_by_id(id):
    current_app.logger.info(f"Proceeding to delete an address id={id}")
    try:
        Address.query.filter_by(id=id).delete()
        db.session.commit()
        status_code = Response(status=204)
        return status_code
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: delete_address_by_id")
        return internal_server_error("Internal server error")

@api.route('/addresses/<int:id>/users', methods = ['GET'])
def get_users_by_address(id):
    current_app.logger.info("Proceeding to get the list of users by address")
    try:
        request_args = request.args.to_dict()
        if not request_args:
            users = User.query.filter_by(address_id=id)
        else:
            request_args['address_id'] = id
            query_string = QueryCreator.get_sql_query('users', request_args)
            users = Address.custom_query(query_string)

        if users is not None:
            return jsonify(users = User.list_to_json(users), links = User.get_pagination_data(request, id))
        else:
            return resource_not_found("No user exists for address")
    except Exception:
        current_app.logger.exception("Exception occured while processing function: get_users_by_address")
        return internal_server_error("Internal server error")

'''
@api.route('/addresses/<int:id>/users', methods = ['POST'])
def add_user_by_address(id):
    current_app.logger.info(f"Proceeding add a new user for address with id={id}")
    try:
        if request.data:
            user = User.from_json(request.get_json(force=True), address_id=id)
            db.session.add(user)
            db.session.commit()
            address_resp = Address.query.get_or_404(id)
            return jsonify(address_resp.to_json()), 201, \
            {'Location': url_for('api.get_address_by_id', id=address_resp.id)}
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Exception occured while processing function: add_user_by  _address")
        return internal_server_error("Internal server error")
'''