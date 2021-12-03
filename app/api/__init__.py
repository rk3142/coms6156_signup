from flask import Blueprint
from flask_dance.contrib.google import make_google_blueprint
import os


google_bp = make_google_blueprint(
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        reprompt_consent=True,
        scope=["profile", "email"],
        redirect_url=os.environ.get('GOOGLE_REDIRECT_URL'))
        #redirect_to=os.environ.get('UI_URL'))

api = Blueprint('api', __name__)
health = Blueprint('health', __name__)

from . import user_controller
from . import address_controller
from . import health_controller
