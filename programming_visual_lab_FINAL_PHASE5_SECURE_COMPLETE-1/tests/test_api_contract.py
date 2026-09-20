import os
os.environ["PVL_EXECUTION_MODE"] = "local"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_contract():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert set(["status","version","languages","execution_mode"]).issubset(data)

def test_run_python_success():
    r = client.post("/api/run", json={"language":"python","code":"print('hello')"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["language"] == "python"
    assert "hello" in data["stdout"]
    assert isinstance(data["events"], list)

def test_run_python_input():
    r = client.post("/api/run", json={"language":"python","code":"name=input()\nprint(name)","stdin":"Yash\n"})
    assert r.status_code == 200
    assert r.json()["stdout"].strip() == "Yash"

def test_invalid_language():
    r = client.post("/api/run", json={"language":"ruby","code":"puts 1"})
    assert r.status_code == 422

def test_empty_code():
    r = client.post("/api/run", json={"language":"python","code":""})
    assert r.status_code == 422
