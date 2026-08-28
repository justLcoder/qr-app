from io import BytesIO
import secrets
import qrcode
from qrcode.image.svg import SvgPathImage
from sqlalchemy.orm import Session
from app.models import QRCode


def make_short_code(db: Session) -> str:
    while True:
        code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8]
        if not db.query(QRCode).filter_by(short_code=code).first():
            return code


def render_qr(data: str, foreground: str, background: str, image_format: str) -> bytes:
    factory = SvgPathImage if image_format == "svg" else None
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4, image_factory=factory)
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color=foreground, back_color=background)
    output = BytesIO()
    image.save(output)
    return output.getvalue()
