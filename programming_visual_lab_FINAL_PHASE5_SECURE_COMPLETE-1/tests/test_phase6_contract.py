from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_phase6_health_and_academy():
    health = client.get("/api/health")
    assert health.status_code == 200
    data = health.json()
    assert data["version"] == "6.0.0"
    assert "6" in data["phases"]
    assert set(["python", "java", "c", "cpp", "javascript"]).issubset(set(data["languages"]))

    page = client.get("/")
    assert page.status_code == 200
    html = page.text
    assert "pvl-academy-open" in html
    assert "Choose your language" in html
    assert "Manual Code Playground" in html
    assert "phase6" not in html.lower() or "Programming Visual Lab — Phase 6" in html


def test_auth_contracts():
    config = client.get("/api/auth/config")
    assert config.status_code == 200
    assert "google" in config.json()
    assert "github" in config.json()

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["authenticated"] is False

    guest = client.post("/api/auth/guest")
    assert guest.status_code == 200
    assert guest.json()["user"]["provider"] == "guest"

    me2 = client.get("/api/auth/me")
    assert me2.status_code == 200
    assert me2.json()["authenticated"] is True

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200

    me3 = client.get("/api/auth/me")
    assert me3.status_code == 200
    assert me3.json()["authenticated"] is False
