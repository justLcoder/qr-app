"""Password hashing and JSON Web Token helpers for authentication.

Passwords are stored only as bcrypt hashes. JWTs carry a user identifier and
expiry so API routes can authenticate requests without a server-side session
table. ``dependencies.py`` uses these helpers to turn a bearer token into a
database ``User`` object.
"""

from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from app.core.config import get_settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_context.verify(password, hashed)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    # ``sub`` is the standard JWT subject claim; here it contains the user ID.
    # ``exp`` lets JWT libraries reject the token after its configured lifetime.
    return jwt.encode({"sub": subject, "exp": expires}, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> str | None:
    try:
        # Limiting accepted algorithms prevents algorithm-confusion attacks.
        return jwt.decode(token, get_settings().secret_key, algorithms=["HS256"]).get("sub")
    except jwt.PyJWTError:
        # Authentication dependencies convert an invalid/expired token into an
        # HTTP 401 response instead of exposing JWT-library implementation details.
        return None
