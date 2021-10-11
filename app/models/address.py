# coding: utf-8
from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import TINYINT
from app import db
from flask import current_app, json, request, url_for


class Address(db.Model):
    __tablename__ = 'address'

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

    def to_json(self):
        json_user = {
            'id': self.id,
            'house_number': self.house_number,
            'street_name_1': self.street_name_1,
            'street_name_2': self.street_name_2,
            'city': self.city,
            'region': self.region,
            'country_code': self.country_code,
            'postal_code': self.postal_code,
            'links': self.get_links_arr()
        }
        return json_user

    @staticmethod
    def list_to_json(address_list):
        return [ item.to_json() for item in address_list]
        
    def get_links_arr(self):
        links_list = []
        address_json = {}
        address_json['rel'] = 'self'
        address_json['href'] = url_for('api.get_address_by_id', id=self.id)
        links_list.append(address_json)
        user_list = []
        for user in self.users:
            user_json = {}
            user_json['rel'] = 'user'
            user_json['href'] = url_for('api.get_user_details', id = user.id)
            links_list.append(user_json)
        
        print(links_list)
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