from fastapi.testclient import TestClient
from pytest import raises
from app import app, lifespan
    

def test_get():
    with TestClient(app) as client:
        response = client.get("/restaurants/2025-05-19 09:14")
        assert response.status_code == 200
        assert response.json() == ["Tupelo Honey"]

def test_get_no_open():
    with TestClient(app) as client:
        response = client.get("/restaurants/2025-05-19 05:14")
        assert response.status_code == 200
        assert response.json() == []

def test_get_raises_bad_datetime_str():
    with TestClient(app) as client:
        response = client.get("/restaurants/2025-05-19 24:14")
        assert response.status_code == 400

