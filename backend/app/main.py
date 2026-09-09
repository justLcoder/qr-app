"""FastAPI application, HTTP routes, and public dynamic-QR redirect endpoint.

This module wires together validation schemas, ORM models, security
dependencies, and QR services. It contains account endpoints, authenticated
QR management endpoints, image downloads, analytics, and the public ``/q``
route that records a dynamic scan before redirecting a visitor.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from urllib.parse import urlencode
import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import Base, engine, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import current_user, optional_user
from app.models import OAuthLoginCode, QRCode, QRType, ScanEvent, User
from app.schemas import AnalyticsResponse, GoogleCodeExchangeRequest, LoginRequest, QRCreate, QRResponse, QRUpdate, RegisterRequest, TokenResponse
from app.services import make_short_code, render_qr

settings = get_settings()
GOOGLE_STATE_COOKIE = "google_oauth_state"
app = FastAPI(title="QR Studio API", version="0.1.0")
# CORS controls which browser origins may call this API. It is necessary in
# development because Vite (5173) and FastAPI (8000) use different origins.
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def create_tables():
    # This creates missing tables for the MVP. It does not manage schema
    # changes to existing production tables; migration tooling would do that.
    Base.metadata.create_all(bind=engine)


def serialize_qr(code: QRCode, scans: int = 0) -> QRResponse:
    style = code.style_config or {}
    # Static QR images encode their destination directly. Dynamic QR images
    # encode the stable redirect endpoint so their destination can change later.
    public_url = f"{settings.public_base_url}/q/{code.short_code}" if code.type == QRType.dynamic else code.destination_url
    return QRResponse(id=code.id, type=code.type, destination_url=code.destination_url, short_code=code.short_code, public_url=public_url, label=code.label, foreground=style.get("foreground", "#111827"), background=style.get("background", "#ffffff"), is_active=code.is_active, created_at=code.created_at, scan_count=scans)


def owned_code(code_id: int, user: User, db: Session) -> QRCode:
    code = db.get(QRCode, code_id)
    # Returning 404 for both missing and non-owned codes avoids revealing the
    # existence of another user's resource by ID.
    if not code or code.owner_id != user.id:
        raise HTTPException(status_code=404, detail="QR code not found")
    return code


def google_configured() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret)


def google_login_error(message: str) -> RedirectResponse:
    return RedirectResponse(f"{settings.frontend_origin}/login?{urlencode({'google_error': message})}")


@app.get("/health")
def health(): return {"status": "ok"}


@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(email=data.email.lower(), password_hash=hash_password(data.password))
    # commit persists the row; refresh loads generated fields such as its ID,
    # which is needed as the token's subject.
    db.add(user); db.commit(); db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.lower()).first()
    # The same generic response avoids revealing whether an email exists.
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@app.get("/api/auth/google/login")
def google_login():
    if not google_configured():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured")
    state = secrets.token_urlsafe(32)
    params = urlencode({"client_id": settings.google_client_id, "redirect_uri": settings.google_redirect_uri, "response_type": "code", "scope": "openid email profile", "state": state, "prompt": "select_account"})
    response = RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")
    response.set_cookie(GOOGLE_STATE_COOKIE, state, max_age=600, httponly=True, samesite="lax", secure=settings.public_base_url.startswith("https://"))
    return response


@app.get("/api/auth/google/callback")
def google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    if error or not code:
        return google_login_error("Google sign-in was cancelled")
    cookie_state = request.cookies.get(GOOGLE_STATE_COOKIE)
    if not cookie_state or not state or not secrets.compare_digest(cookie_state, state):
        return google_login_error("Google sign-in verification failed")
    try:
        token_response = httpx.post("https://oauth2.googleapis.com/token", data={"code": code, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret, "redirect_uri": settings.google_redirect_uri, "grant_type": "authorization_code"}, timeout=10)
        token_response.raise_for_status()
        google_token = token_response.json()["id_token"]
        signing_key = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs").get_signing_key_from_jwt(google_token)
        identity = jwt.decode(google_token, signing_key.key, algorithms=["RS256"], audience=settings.google_client_id, issuer=["https://accounts.google.com", "accounts.google.com"])
        email = identity.get("email", "").lower()
        if not email or not identity.get("email_verified"):
            return google_login_error("A verified Google email is required")
    except (httpx.HTTPError, jwt.PyJWTError, KeyError, ValueError):
        return google_login_error("Google sign-in could not be verified")

    user = db.query(User).filter_by(email=email).first()
    if not user:
        # Google has already verified this email. A random hash keeps the
        # existing password-based schema intact without storing a usable password.
        user = User(email=email, password_hash=hash_password(secrets.token_urlsafe(48)))
        db.add(user)
        db.flush()
    raw_exchange_code = secrets.token_urlsafe(32)
    db.add(OAuthLoginCode(token_hash=hashlib.sha256(raw_exchange_code.encode()).hexdigest(), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(minutes=2)))
    db.commit()
    response = RedirectResponse(f"{settings.frontend_origin}/dashboard?{urlencode({'code': raw_exchange_code})}")
    response.delete_cookie(GOOGLE_STATE_COOKIE)
    return response


@app.post("/api/auth/google/exchange", response_model=TokenResponse)
def exchange_google_code(data: GoogleCodeExchangeRequest, db: Session = Depends(get_db)):
    code_record = db.query(OAuthLoginCode).filter_by(token_hash=hashlib.sha256(data.code.encode()).hexdigest()).first()
    if not code_record:
        raise HTTPException(status_code=400, detail="Google sign-in has expired. Please try again.")
    expires_at = code_record.expires_at if code_record.expires_at.tzinfo else code_record.expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        db.delete(code_record); db.commit()
        raise HTTPException(status_code=400, detail="Google sign-in has expired. Please try again.")
    user = db.get(User, code_record.user_id)
    db.delete(code_record)
    db.commit()
    if not user:
        raise HTTPException(status_code=400, detail="Google account is unavailable")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@app.post("/api/qr-codes", response_model=QRResponse, status_code=status.HTTP_201_CREATED)
def create_qr(data: QRCreate, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    if data.type == QRType.dynamic and not user:
        raise HTTPException(status_code=401, detail="Sign in to create dynamic QR codes")
    # Anonymous static codes have no owner. Dynamic codes get a stable short
    # code because the public QR must point to this application first.
    code = QRCode(owner_id=user.id if user else None, type=data.type, destination_url=str(data.destination_url), short_code=make_short_code(db) if data.type == QRType.dynamic else None, label=data.label, style_config={"foreground": data.foreground, "background": data.background})
    db.add(code); db.commit(); db.refresh(code)
    return serialize_qr(code)


@app.get("/api/qr-codes", response_model=list[QRResponse])
def list_qrs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    codes = db.query(QRCode).filter_by(owner_id=user.id).order_by(QRCode.created_at.desc()).all()
    # Each response includes its count so the dashboard does not need a second
    # HTTP request per card.
    return [serialize_qr(code, db.query(func.count(ScanEvent.id)).filter_by(qr_code_id=code.id).scalar() or 0) for code in codes]


@app.patch("/api/qr-codes/{code_id}", response_model=QRResponse)
def update_qr(code_id: int, data: QRUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    code = owned_code(code_id, user, db)
    if code.type != QRType.dynamic:
        raise HTTPException(status_code=400, detail="Static QR codes cannot be updated")
    # exclude_unset enables PATCH semantics: omitted JSON fields retain their
    # existing database values rather than being overwritten with defaults.
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "destination_url" and value is not None: value = str(value)
        setattr(code, field, value)
    db.commit(); db.refresh(code)
    return serialize_qr(code, db.query(func.count(ScanEvent.id)).filter_by(qr_code_id=code.id).scalar() or 0)


@app.delete("/api/qr-codes/{code_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qr(code_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(owned_code(code_id, user, db)); db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/qr-codes/{code_id}/download")
def download_qr(code_id: int, image_format: str = "png", user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    code = db.get(QRCode, code_id)
    if not code or (code.owner_id and (not user or code.owner_id != user.id)):
        raise HTTPException(status_code=404, detail="QR code not found")
    if image_format not in {"png", "svg"}: raise HTTPException(status_code=400, detail="Format must be png or svg")
    # The renderer receives exactly what a scanner should encode: direct URL
    # for static codes, or this application's stable redirect URL for dynamic.
    data = serialize_qr(code).public_url
    media_type = "image/svg+xml" if image_format == "svg" else "image/png"
    return Response(render_qr(data, code.style_config.get("foreground", "#111827"), code.style_config.get("background", "#ffffff"), image_format), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="qr-{code.id}.{image_format}"'})


@app.get("/api/qr-codes/{code_id}/analytics", response_model=AnalyticsResponse)
def analytics(code_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    code = owned_code(code_id, user, db)
    # The endpoint returns a lightweight recent sample rather than every event.
    scans = db.query(ScanEvent).filter_by(qr_code_id=code.id).order_by(ScanEvent.created_at.desc()).limit(20).all()
    return AnalyticsResponse(total_scans=db.query(func.count(ScanEvent.id)).filter_by(qr_code_id=code.id).scalar() or 0, recent_scans=[scan.created_at for scan in scans])


@app.get("/q/{short_code}")
def redirect(short_code: str, request: Request, db: Session = Depends(get_db)):
    code = db.query(QRCode).filter_by(short_code=short_code, type=QRType.dynamic).first()
    if not code or not code.is_active: raise HTTPException(status_code=404, detail="QR code is unavailable")
    # This public route intentionally records a scan before issuing the
    # redirect; static QR codes bypass it and therefore cannot be tracked.
    db.add(ScanEvent(qr_code_id=code.id, referrer=request.headers.get("referer"), user_agent=request.headers.get("user-agent", "")[:512]))
    db.commit()
    return RedirectResponse(code.destination_url, status_code=307)
