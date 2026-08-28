import os
os.environ["DATABASE_URL"] = "sqlite:///./test_qr_studio.db"

from fastapi.testclient import TestClient
from app.main import app


def test_static_qr_can_be_created_and_downloaded():
    with TestClient(app) as client:
        create = client.post("/api/qr-codes", json={"destination_url": "https://example.com", "type": "static"})
        assert create.status_code == 201
        code = create.json()
        assert code["public_url"] == "https://example.com/"
        download = client.get(f"/api/qr-codes/{code['id']}/download")
        assert download.status_code == 200
        assert download.headers["content-type"] == "image/png"


def test_dynamic_qr_redirects_and_counts_scan():
    with TestClient(app) as client:
        register = client.post("/api/auth/register", json={"email": "test@example.com", "password": "safe-password"})
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        create = client.post("/api/qr-codes", headers=headers, json={"destination_url": "https://example.com/path", "type": "dynamic"})
        assert create.status_code == 201
        code = create.json()
        redirected = client.get(f"/q/{code['short_code']}", follow_redirects=False)
        assert redirected.status_code == 307
        assert redirected.headers["location"] == "https://example.com/path"
        analytics = client.get(f"/api/qr-codes/{code['id']}/analytics", headers=headers)
        assert analytics.json()["total_scans"] == 1
