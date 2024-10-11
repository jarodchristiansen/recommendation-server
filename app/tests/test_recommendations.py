# from fastapi.testclient import TestClient
# from main import app
# import os

# client = TestClient(app)

# def test_recommendations():
#     secret_token = os.getenv("SECRET_TOKEN")

#     response = client.get("/recommendations/cosine-similarity/3wzAXBZ6mhuYEzf2IJAbDc", params={"token": "test_token"})
#     assert response.status_code == 200
#     assert "recommendations" in response.json()