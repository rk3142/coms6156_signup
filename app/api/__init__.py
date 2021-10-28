from flask import Blueprint
from flask_dance.contrib.google import make_google_blueprint
import os

google_bp = make_google_blueprint(
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        reprompt_consent=True,
        scope=["profile", "email"],
	redirect_url='http://127.0.0.1:5000/reg-service/v1/auth/register')

api = Blueprint('api', __name__)
health = Blueprint('health', __name__)

from . import user_controller
from . import address_controller
from . import health_controller