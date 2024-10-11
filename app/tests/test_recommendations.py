from fastapi.testclient import TestClient
import os

# relies on conftest.py import to manage main.py being outside /app
from main import app

client = TestClient(app)

def test_recommendations_authentication():
    secret_token = os.getenv("SECRET_TOKEN")

    response = client.get("/recommendations/cosine-similarity/3wzAXBZ6mhuYEzf2IJAbDc", params={"token": "test_token"})
    assert response.status_code == 401

    response = client.get("/recommendations/cosine-similarity/3wzAXBZ6mhuYEzf2IJAbDc", params={"token": secret_token})
    assert response.status_code == 200
    assert 'recommendations' in response.json()

