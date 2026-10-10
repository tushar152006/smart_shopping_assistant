import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.service import get_service

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_products"] > 0


def test_product_search() -> None:
    response = client.get("/api/products/search?q=banana&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    assert any("banana" in item["product_name"].lower() for item in data)


def test_sample_users() -> None:
    response = client.get("/api/users/sample")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "user_id" in data[0]
    assert "order_count" in data[0]


def test_predict_endpoint() -> None:
    service = get_service()
    # pick first two products
    sample_ids = [p["product_id"] for p in service.products[:2]]
    
    payload = {
        "context_product_ids": sample_ids,
        "user_id": service.sample_users[0]["user_id"] if service.sample_users else None,
        "top_k": 3,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) > 0
    first_pred = data["predictions"][0]
    assert "product_id" in first_pred
    assert "product_name" in first_pred
    assert "score" in first_pred
    assert "reason" in first_pred
    assert len(first_pred["reason"]) > 0


def test_predict_empty_basket_rejected() -> None:
    payload = {
        "context_product_ids": [],
        "top_k": 3,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code in (400, 422)


def test_security_headers_present() -> None:
    response = client.get("/api/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_search_query_max_length_enforced() -> None:
    oversized_query = "a" * 150
    response = client.get(f"/api/products/search?q={oversized_query}")
    assert response.status_code == 422

