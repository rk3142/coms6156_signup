import os, json
from flask import Flask, request, redirect, url_for, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import logging, sys
from models import db
from api import user_controller, health_controller, address_controller
from middleware import security
from middleware.notification import NotificationMiddlewareHandler
from flask_dance.contrib.google import google
from api import google_bp as google_bp

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
    app.config['IS_DEVELOPMENT_MODE'] = os.environ.get("IS_APP_ON_DEVELOPMENT")
    app.config['SS_API_KEY'] = os.getenv("SS_API_KEY" , None)
    app.config['SS_AUTH_TOKEN'] = os.getenv("SS_AUTH_TOKEN", None)
    app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
    app.secret_key = "some secret"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    # app.config['PASSWORD_HASH'] = os.environ.get("PASSWORD_HASH")
    # app.config['REGSALT'] = os.environ.get("REGSALT")
    db.init_app(app)
    CORS(app)

    from api import api as api_bp
    from api import health as health_bp
    
    app.register_blueprint(google_bp, url_prefix="/reg-service/v1/auth")
    app.register_blueprint(api_bp, url_prefix='/reg-service/v1/')
    app.register_blueprint(health_bp, url_prefix='/')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

    
    return app

application = create_app()

@application.before_request
def before_request_func():
    result_ok = security.check_security(request, google)
    if not result_ok:
        return jsonify(redirect_url = url_for('google.login')), 302


@application.after_request
def after_request_func(response):
    if response.status_code == 201:
        notification = NotificationMiddlewareHandler.get_notification_request(request)
        if notification is not None:
            NotificationMiddlewareHandler.send_sns_message(
                os.environ.get('SNS_TOPIC_NAME', None), notification)
    return response
    
if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)
