"""QR-specific operations that are independent of HTTP route handling.

``make_short_code`` creates a unique identifier for the public dynamic QR
redirect URL. ``render_qr`` turns a URL and visual options into downloadable
PNG or SVG bytes. Route handlers in ``main.py`` call these functions.
"""

from io import BytesIO
import secrets
import qrcode
from qrcode.image.svg import SvgPathImage
from sqlalchemy.orm import Session
from app.models import QRCode


def make_short_code(db: Session) -> str:
    while True:
        # token_urlsafe uses cryptographically secure randomness. The lookup is
        # needed because randomness makes collisions unlikely, not impossible.
        code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8]
        if not db.query(QRCode).filter_by(short_code=code).first():
            return code


def render_qr(data: str, foreground: str, background: str, image_format: str) -> bytes:
    # The QR library uses a different image factory when creating SVG output.
    factory = SvgPathImage if image_format == "svg" else None
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4, image_factory=factory)
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color=foreground, back_color=background)
    # BytesIO behaves like a file in memory, allowing the API to return a file
    # response without first writing a generated image to disk.
    output = BytesIO()
    image.save(output)
    return output.getvalue()
