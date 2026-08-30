"""Reusable FastAPI dependencies for turning bearer tokens into users.

Routes declare ``Depends(current_user)`` when authentication is mandatory or
``Depends(optional_user)`` when anonymous access is also meaningful. This
keeps token parsing and user lookup out of every individual route handler.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    # FastAPI resolves both dependencies before this function: the Authorization
    # header becomes credentials and get_db yields a request-scoped session.
    user_id = decode_access_token(credentials.credentials) if credentials else None
    user = db.get(User, int(user_id)) if user_id and user_id.isdigit() else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def optional_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    # Static QR creation is allowed without an account, so this dependency
    # returns None instead of raising when no bearer token is present.
    if not credentials:
        return None
    user_id = decode_access_token(credentials.credentials)
    return db.get(User, int(user_id)) if user_id and user_id.isdigit() else None
