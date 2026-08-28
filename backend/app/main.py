from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import Base, engine, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import current_user, optional_user
from app.models import QRCode, QRType, ScanEvent, User
from app.schemas import AnalyticsResponse, LoginRequest, QRCreate, QRResponse, QRUpdate, RegisterRequest, TokenResponse
from app.services import make_short_code, render_qr

settings = get_settings()
app = FastAPI(title="QR Studio API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


def serialize_qr(code: QRCode, scans: int = 0) -> QRResponse:
    style = code.style_config or {}
    public_url = f"{settings.public_base_url}/q/{code.short_code}" if code.type == QRType.dynamic else code.destination_url
    return QRResponse(id=code.id, type=code.type, destination_url=code.destination_url, short_code=code.short_code, public_url=public_url, label=code.label, foreground=style.get("foreground", "#111827"), background=style.get("background", "#ffffff"), is_active=code.is_active, created_at=code.created_at, scan_count=scans)


def owned_code(code_id: int, user: User, db: Session) -> QRCode:
    code = db.get(QRCode, code_id)
    if not code or code.owner_id != user.id:
        raise HTTPException(status_code=404, detail="QR code not found")
    return code


@app.get("/health")
def health(): return {"status": "ok"}


@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(email=data.email.lower(), password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@app.post("/api/qr-codes", response_model=QRResponse, status_code=status.HTTP_201_CREATED)
def create_qr(data: QRCreate, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    if data.type == QRType.dynamic and not user:
        raise HTTPException(status_code=401, detail="Sign in to create dynamic QR codes")
    code = QRCode(owner_id=user.id if user else None, type=data.type, destination_url=str(data.destination_url), short_code=make_short_code(db) if data.type == QRType.dynamic else None, label=data.label, style_config={"foreground": data.foreground, "background": data.background})
    db.add(code); db.commit(); db.refresh(code)
    return serialize_qr(code)


@app.get("/api/qr-codes", response_model=list[QRResponse])
def list_qrs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    codes = db.query(QRCode).filter_by(owner_id=user.id).order_by(QRCode.created_at.desc()).all()
    return [serialize_qr(code, db.query(func.count(ScanEvent.id)).filter_by(qr_code_id=code.id).scalar() or 0) for code in codes]


@app.patch("/api/qr-codes/{code_id}", response_model=QRResponse)
def update_qr(code_id: int, data: QRUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    code = owned_code(code_id, user, db)
    if code.type != QRType.dynamic:
        raise HTTPException(status_code=400, detail="Static QR codes cannot be updated")
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
    data = serialize_qr(code).public_url
    media_type = "image/svg+xml" if image_format == "svg" else "image/png"
    return Response(render_qr(data, code.style_config.get("foreground", "#111827"), code.style_config.get("background", "#ffffff"), image_format), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="qr-{code.id}.{image_format}"'})


@app.get("/api/qr-codes/{code_id}/analytics", response_model=AnalyticsResponse)
def analytics(code_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    code = owned_code(code_id, user, db)
    scans = db.query(ScanEvent).filter_by(qr_code_id=code.id).order_by(ScanEvent.created_at.desc()).limit(20).all()
    return AnalyticsResponse(total_scans=db.query(func.count(ScanEvent.id)).filter_by(qr_code_id=code.id).scalar() or 0, recent_scans=[scan.created_at for scan in scans])


@app.get("/q/{short_code}")
def redirect(short_code: str, request: Request, db: Session = Depends(get_db)):
    code = db.query(QRCode).filter_by(short_code=short_code, type=QRType.dynamic).first()
    if not code or not code.is_active: raise HTTPException(status_code=404, detail="QR code is unavailable")
    db.add(ScanEvent(qr_code_id=code.id, referrer=request.headers.get("referer"), user_agent=request.headers.get("user-agent", "")[:512]))
    db.commit()
    return RedirectResponse(code.destination_url, status_code=307)
