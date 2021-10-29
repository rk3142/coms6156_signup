# coding: utf-8
from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import TINYINT
from flask import current_app, json, request, url_for
from . import db
from dataclasses import dataclass

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
    def to_json(result):
        json_address = result
        json_address['links'] = Address.get_links_arr(result)
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
    def list_to_json(address_list):
        return [ Address.to_json(item) for item in address_list]

    @staticmethod
    def get_links_arr(address):
        links_list = []
        address_json = {}
        address_json['rel'] = 'self'
        address_json['href'] = url_for('api.get_address_by_id', id=address['id'])
        links_list.append(address_json)
        user_ids = Address.custom_query(f"select id from users where address_id={address['id']}")
        for user in user_ids:
            print(user)
            user_json = {}
            user_json['rel'] = 'user'
            user_json['href'] = url_for('api.get_user_details', id = user['id'])
            links_list.append(user_json)
        return links_list


    @staticmethod
    def from_json(address_json):
            return Address(house_number = address_json.get('house_number'), 
                        street_name_1 = address_json.get('street_name_1'),
                        street_name_2 = address_json.get('street_name_2'),
                        city = address_json.get('city'),
                        region = address_json.get('region'),
                        country_code = address_json.get('country_code'),
                        postal_code = address_json.get('postal_code'))