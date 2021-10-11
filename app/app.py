import os
from flask import Flask
from datetime import timedelta 
import json
from flask.wrappers import Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import logging, sys

db = SQLAlchemy()

def get_db_uri(username, password, host, port, datbase_name):
    return 'mysql+pymysql://' + username + ':' + password + '@' + host + ':' + port + '/' + datbase_name

def load_db_connection(app):
    DBUSER = os.environ.get("DBUSER")
    DBPASSWORD = os.environ.get("DBPASSWORD")
    DBHOST = os.environ.get("DBHOST")
    DBPORT = os.environ.get("DBPORT")
    DBNAME = os.environ.get("DBNAME")
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_uri(DBUSER, DBPASSWORD, DBHOST, DBPORT, DBNAME)

def create_app():
    
    app = Flask(__name__)
    load_db_connection(app)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    # app.config['PASSWORD_HASH'] = os.environ.get("PASSWORD_HASH")
    # app.config['REGSALT'] = os.environ.get("REGSALT")
    db.init_app(app)
    CORS(app)

    from api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/reg-service/v1/')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    return app



app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)