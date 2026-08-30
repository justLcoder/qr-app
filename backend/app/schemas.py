"""Pydantic schemas that define and validate the public API contract.

Request schemas validate JSON before route handlers run, while response
schemas define which values are sent back to the browser. They are distinct
from SQLAlchemy models so database internals, such as password hashes, are not
automatically exposed by the API.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from app.models import QRType


class RegisterRequest(BaseModel):
    # The 72-character maximum matches bcrypt's effective password limit.
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QRCreate(BaseModel):
    # HttpUrl validates URLs at the API boundary before they reach the database.
    destination_url: HttpUrl
    type: QRType = QRType.static
    label: str | None = Field(default=None, max_length=120)
    foreground: str = Field(default="#111827", pattern=r"^#[0-9a-fA-F]{6}$")
    background: str = Field(default="#ffffff", pattern=r"^#[0-9a-fA-F]{6}$")


class QRUpdate(BaseModel):
    destination_url: HttpUrl | None = None
    label: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None


class QRResponse(BaseModel):
    id: int
    type: QRType
    destination_url: str
    short_code: str | None
    public_url: str
    label: str | None
    foreground: str
    background: str
    is_active: bool
    created_at: datetime
    scan_count: int = 0


class AnalyticsResponse(BaseModel):
    total_scans: int
    recent_scans: list[datetime]
