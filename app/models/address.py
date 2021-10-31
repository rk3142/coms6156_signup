# coding: utf-8
from os import link
from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import TINYINT
from flask import current_app, json, request, url_for
from . import db
from dataclasses import dataclass
import config.constants as CONSTANTS
import re

@dataclass
class Address(db.Model):
    __tablename__ = 'address'

    id: int
    house_number: String
    street_name_1: String
    street_name_2: String
    city: String
    region: String
    country_code: String
    postal_code: String


    id = Column(Integer, primary_key=True)
    house_number = Column(String(16))
    street_name_1 = Column(String(64))
    street_name_2 = Column(String(128))
    city = Column(String(128), nullable=False)
    region = Column(String(128))
    country_code = Column(String(6), nullable=False)
    postal_code = Column(String(8), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    users = db.relationship('User', backref='address', lazy=True)

    
    @staticmethod
    def to_json(result, path_parameters=None):
        json_address = result
        json_address['links'] = Address.get_links_arr(result ,path_parameters)
        return json_address

    @staticmethod
    def custom_query(query):
        result_set = db.session.execute(query)
        result_list = []
        if result_set is not None:
            for row in result_set:
                result_list.append(dict(row))
        
        return result_list


    @staticmethod
    def get_pagination_data(request):
        pagination_resp  = {}
        request_args = request.args.to_dict()
        if request_args is not None:
            limit = request_args.get('limit', None)
            offset = request_args.get('offset', None)
            if limit is not None and offset is not None:
                pagination_resp = Address.get_pagination_resp(request)
        
        return pagination_resp

    @staticmethod
    def list_to_json(address_list, request=None):
        address_resp = [Address.to_json(item) for item in address_list]
        return address_resp

    @staticmethod
    def get_links_arr(address, path_parameters=None):
        links_list = []
        address_json = {}
        address_json['rel'] = 'self'
        address_json['href'] = url_for('api.get_address_by_id', id=address['id'])
        links_list.append(address_json)
        user_ids = Address.custom_query(f"select id from users where address_id={address['id']}")
        for user in user_ids:
            user_json = {}
            user_json['rel'] = 'user'
            user_json['href'] = url_for('api.get_user_details', id = user['id'])
            links_list.append(user_json)
        
        return links_list


    @staticmethod
    def get_pagination_resp(request):
        links = []
        path = request.path
        path_parameters = request.args.to_dict()
        total_count = Address.query.count()
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

    @staticmethod
    def from_json(address_json):
            return Address(house_number = address_json.get('house_number'), 
                        street_name_1 = address_json.get('street_name_1'),
                        street_name_2 = address_json.get('street_name_2'),
                        city = address_json.get('city'),
                        region = address_json.get('region'),
                        country_code = address_json.get('country_code'),
                        postal_code = address_json.get('postal_code'))

    def to_dict(self):
        json_address = {
            'id': self.id,
            'house_number': self.house_number,
            'street_name_1': self.street_name_1,
            'street_name_2': self.street_name_2,
            'city': self.city,
            'region': self.region,
            'country_code': self.country_code,
            'postal_code': self.postal_code
        }
        return json_address