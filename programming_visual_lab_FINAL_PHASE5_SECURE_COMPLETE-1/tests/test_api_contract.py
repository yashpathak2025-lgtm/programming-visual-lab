import os
import shutil
import pytest
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


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc unavailable in this test environment")
def test_c_execution():
    r = client.post("/api/run", json={"language":"c","code":"#include <stdio.h>\nint main(){ int x=2; printf(\"%d\\n\",x); return 0; }"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["stdout"].strip() == "2"
    assert data["events"]

@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ unavailable in this test environment")
def test_cpp_execution():
    r = client.post("/api/run", json={"language":"cpp","code":"#include <iostream>\nint main(){ std::cout << \"ok\\n\"; return 0; }"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["stdout"].strip() == "ok"
    assert data["events"]

@pytest.mark.skipif(shutil.which("node") is None, reason="node unavailable in this test environment")
def test_javascript_execution():
    r = client.post("/api/run", json={"language":"javascript","code":"console.log(\"ok\")"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["stdout"].strip() == "ok"
    assert data["events"]

def test_python_syntax_error_is_structured():
    r = client.post("/api/run", json={"language":"python","code":"if True print('x')"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert data["language"] == "python"
    assert data["error"]
    assert isinstance(data["events"], list)

def test_empty_code():
    r = client.post("/api/run", json={"language":"python","code":""})
    assert r.status_code == 422
