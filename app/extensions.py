from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter

db = SQLAlchemy()


def get_real_client_ip():
    """Return the real client IP behind a reverse proxy.

    Reads X-Forwarded-For header (first entry = original client).
    Falls back to request.remote_addr when running without a proxy.
    """
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr


limiter = Limiter(key_func=get_real_client_ip, storage_uri="memory://")
