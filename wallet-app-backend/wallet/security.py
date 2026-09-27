import re
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from .extensions import db
from .models import User
from .timeutils import as_utc, utcnow

MOBILE_RE = re.compile(r"^[6-9]\d{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PIN_RE = re.compile(r"^\d{4}$")


def hash_secret(secret: str) -> str:
    """Salted scrypt hash — used for both PINs and OTP codes."""
    from werkzeug.security import generate_password_hash

    return generate_password_hash(secret, method="scrypt")


def verify_secret(hashed: str, secret: str) -> bool:
    from werkzeug.security import check_password_hash

    if not hashed:
        return False
    return check_password_hash(hashed, secret)


def issue_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(hours=current_app.config["JWT_EXPIRES_HOURS"]),
    }
    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
        )
    except jwt.PyJWTError:
        return None
    try:
        return int(payload.get("sub"))
    except (TypeError, ValueError):
        return None


def auth_error(message="Authentication required"):
    return jsonify({"message": message}), 401


def require_auth(view):
    """Populates g.user_id from the Bearer token or returns 401."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return auth_error()
        user_id = decode_token(header[len("Bearer ") :].strip())
        if not user_id:
            return auth_error("Invalid or expired session. Please log in again.")
        g.user_id = user_id
        return view(*args, **kwargs)

    return wrapper


def current_user() -> User:
    return db.session.get(User, g.user_id)


def pin_is_locked(user: User):
    locked_until = as_utc(user.pin_locked_until)
    if locked_until and utcnow() < locked_until:
        minutes = max(1, int((locked_until - utcnow()).total_seconds() // 60) + 1)
        return f"PIN locked after too many wrong attempts. Try again in {minutes} minute(s)."
    return None
