from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from app.models import QRType


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QRCreate(BaseModel):
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
