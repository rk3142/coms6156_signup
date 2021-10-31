# coding: utf-8
from operator import add
from sqlalchemy import Column, Enum, Integer, String, TIMESTAMP, Date, Text, text
from sqlalchemy.sql.functions import user
from exceptions import ValidationError
from flask import current_app, request, url_for
from datetime import datetime
from sqlalchemy.orm import relationship
from . import db
from dataclasses import dataclass
import config.constants as CONSTANTS
import re

@dataclass
class User(db.Model):
    __tablename__ = 'users'

    id: String
    first_name: String
    last_name: String
    username: String
    email: String
    gender: String
    dob: Date
    bio: String
    address_id: int

    id = Column(String(32), primary_key=True)
    first_name = Column(String(128))
    last_name = Column(String(128))
    username = Column(String(32))
    email = Column(String(512))
    gender = Column(Enum('M', 'F'))
    dob = Column(Date)
    password = Column(Text)
    bio = Column(Text)
    status = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    address_id = Column(db.ForeignKey('address.id', ondelete='SET NULL'), index=True)

    @staticmethod
    def check_account_already_exists(email):
        user = User.query.filter_by(email = email).first()
        return user.id if hasattr(user, 'id') else None

    @staticmethod
    def check_username_exists(username):
        if User.query.filter_by(username = username).first() is not None:
            return False
        return True

    @staticmethod
    def get_user_password(id):
        user_password = User.query.with_entities(User.password).filter_by(id=id).first()
        return user_password if user_password else None

    def validate_email_and_password(password, email='', username=''):
        user_record = User.query.filter((User.email==email) | (User.username==username) & (User.password == password)).first()
        return user_record.id if hasattr(user_record, 'id') else None

    def check_email_or_user_exists(email='', username=''):
        user_record = User.query.filter((User.email==email) | (User.username==username)).first()
        return user_record.id if hasattr(user_record, 'id') else None

    @staticmethod
    def custom_query(query):
        result_set = db.session.execute(query)
        result_list = []
        if result_set is not None:
            for row in result_set:
                result_list.append(dict(row))
        
        return result_list

    @staticmethod
    def to_json(result):
        json_user = result
        return json_user

    def to_dict(self):
        json_user = {
            'id': self.id,
            'username': self.username,
            'gender': self.gender,
            'bio': self.bio,
            'address_id': self.address_id,
            'first_name': self.first_name,
            'last_name': self.last_name
        }
        return json_user

    @staticmethod
    def get_links_arr(users, path_parameters=None):
        links_list = []
        user_json = {}
        user_json['rel'] = 'self'
        user_json['href'] = url_for('api.get_user_details', id=users['id'])
        links_list.append(user_json)
        address_json = {}
        address_json['rel'] = 'address'
        address_json['href'] = url_for('api.get_address_by_id', id=users['address_id'])
        links_list.append(address_json)
        return links_list

    @staticmethod
    def to_json_address(user, address):
        json_user = {
            'id': address['id'],
            'house_number': address['house_number'],
            'street_name_1': address['street_name_1'],
            'street_name_2': address['street_name_2'],
            'city': address['city'],
            'region': address['region'],
            'country_code': address['country_code'],
            'postal_code': address['postal_code'],
            'links': User.get_links_arr(user)
        }
        return json_user

    @staticmethod
    def list_to_json(users_list):
        return [ User.to_json(item) for item in users_list]

    @staticmethod
    def from_json(user_json, address_id=0):
            return User(first_name = user_json.get('first_name'),
                        last_name = user_json.get('last_name'),
                        username = user_json.get('username'),
                        email = user_json.get('email'),
                        password = user_json.get('password'),
                        bio = user_json.get('bio'),
                        gender = user_json.get('gender'),
                        status = 1,
                        dob = datetime.strptime(user_json.get('dob'), '%Y-%m-%d'),
                        address_id = address_id)


    @staticmethod
    def get_pagination_data(request, id = None):
        pagination_resp  = {}
        request_args = request.args.to_dict()
        if request_args is not None:
            limit = request_args.get('limit', None)
            offset = request_args.get('offset', None)
            if limit is not None and offset is not None:
                pagination_resp = User.get_pagination_resp(request, id)
        
        return pagination_resp

    @staticmethod
    def get_pagination_resp(request, id = None):
        links = []
        path = request.path
        path_parameters = request.args.to_dict()
        total_count = 0
        if id is None:
            total_count = User.query.count()
        else:
            total_count = User.query.filter_by(address_id=id).count()
    
        current_count = path_parameters.get('offset')
        rendered_count = int(path_parameters.get('offset')) + int(path_parameters.get('limit'))
        previous_count = int(path_parameters.get('offset')) - int(CONSTANTS.PAGE_SIZE)
        
        next_count = int(rendered_count) - int(CONSTANTS.PAGE_SIZE)
        if previous_count < 0:
            previous_count = 0


        if next_count > total_count:
            next_count = total_count

        print("Previous count" + str(previous_count))
        print("Next count" + str(next_count))
        print("Current count" + str(current_count))

        path_parameters.pop('limit')
        path_parameters.pop('offset')
        path_parameters['limit'] =  CONSTANTS.PAGE_SIZE
        path_parameters['offset'] = CONSTANTS.OFFSET_IDENTIFIER

        query_string =  ''
        for key, values in path_parameters.items():
            current_str = key + '=' + str(values)
            query_string += current_str + "&"

        query_string = query_string[:-1]
        print(query_string)
        previous_link_str = request.path + "?" + re.sub(CONSTANTS.OFFSET_IDENTIFIER, str(previous_count), query_string)
        current_link_str = request.path + "?" + re.sub(CONSTANTS.OFFSET_IDENTIFIER, str(current_count), query_string)
        next_link_str = request.path + "?" + re.sub(CONSTANTS.OFFSET_IDENTIFIER, str(rendered_count), query_string)
        previous_link = {}
        previous_link['rel'] = 'prev'
        previous_link['href'] = previous_link_str
        curr_link = {}
        curr_link['rel'] = 'curr'
        curr_link['href'] = current_link_str
        next_link = {}
        next_link['rel'] = 'next'
        next_link['href'] = next_link_str
        links.append(previous_link)
        links.append(curr_link)
        links.append(next_link)
        links_json  = {}
        links_json['links'] = links
        return links