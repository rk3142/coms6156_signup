from flask import Blueprint

api = Blueprint('api', __name__)
health = Blueprint('health', __name__)

from . import user_controller
from . import address_controller
from . import health_controller