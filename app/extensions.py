from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
session = Session()
