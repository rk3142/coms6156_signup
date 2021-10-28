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

@dataclass
class User(db.Model):
    __tablename__ = 'users'

    id: int
    first_name: String
    last_name: String
    username: String
    email: String
    gender: String
    dob: Date
    bio: String
    address_id: int

    id = Column(Integer, primary_key=True)
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

    def to_json(self):
        json_user = {
            'links': self.get_links_arr(),
            'id': self.id,
            'username': self.username,
            'member_since': self.created_at,
            'last_seen': self.updated_at,
            'gender': self.gender,
            'dob': self.dob,
            'bio': self.bio,
            'address_id': self.address_id,
        'first_name': self.first_name,
        'last_name': self.last_name
        }
        return json_user

    def get_links_arr(self):
        links_list = []
        user_json = {}
        user_json['rel'] = 'self'
        user_json['href'] = url_for('api.get_user_details', id=self.id)
        links_list.append(user_json)
        address_json = {}
        address_json['rel'] = 'address'
        address_json['href'] = url_for('api.get_address_by_id', id=self.address_id)
        links_list.append(address_json)
        return links_list

    @staticmethod
    def to_json_address(self, address):
        json_user = {
            'id': address.id,
            'house_number': address.house_number,
            'street_name_1': address.street_name_1,
            'street_name_2': address.street_name_2,
            'city': address.city,
            'region': address.region,
            'country_code': address.country_code,
            'postal_code': address.postal_code,
            'links': self.get_links_arr()
        }
        return json_user

    @staticmethod
    def list_to_json(users_list):
        return [ item.to_json() for item in users_list]

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
