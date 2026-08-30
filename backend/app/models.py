"""SQLAlchemy ORM models for the persistent QR Studio data.

These classes map Python objects to the ``users``, ``qr_codes``, and
``scan_events`` database tables. Relationships express how a user owns QR
codes and how a dynamic QR code accumulates scan events. API input/output is
defined separately in ``schemas.py``.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class QRType(str, Enum):
    # Inheriting from str makes enum values serialize cleanly in JSON/Pydantic.
    static = "static"
    dynamic = "dynamic"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # ``cascade`` means deleting a user also deletes its owned QR records,
    # rather than leaving database rows pointing to a missing user.
    qr_codes: Mapped[list["QRCode"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class QRCode(Base):
    __tablename__ = "qr_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    type: Mapped[QRType] = mapped_column(SqlEnum(QRType))
    destination_url: Mapped[str] = mapped_column(String(2048))
    short_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True, nullable=True)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # JSON keeps small styling choices flexible without needing a column for
    # each possible visual option.
    style_config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    owner: Mapped[User | None] = relationship(back_populates="qr_codes")
    scans: Mapped[list["ScanEvent"]] = relationship(back_populates="qr_code", cascade="all, delete-orphan")


class ScanEvent(Base):
    __tablename__ = "scan_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    qr_code_id: Mapped[int] = mapped_column(ForeignKey("qr_codes.id"), index=True)
    referrer: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    qr_code: Mapped[QRCode] = relationship(back_populates="scans")
