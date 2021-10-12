from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from . import address
from . import users