"""
tests/test_app.py - pytest unit tests for the Iris Prediction Service.

Tests cover:
    1. Health endpoint returns HTTP 200 and expected JSON.
    2. Predict endpoint returns correct class for known Iris features.
    3. Bad-input handling — missing fields, wrong type, wrong content-type.

Run with:
    pytest tests/ -v
"""

import json
import sys
import os

import pytest

# Make the project root importable when running pytest from the root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.model import load_model  # noqa: E402
from app.app import app           # noqa: E402


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """
    Create a Flask test client with the model loaded.
    scope='module' means the model is loaded once per test file.
    """
    load_model()                     # loads model.pkl from disk
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── 1. Health endpoint ─────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_status_200(self, client):
        """GET /health must return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )

    def test_health_body_has_status_ok(self, client):
        """GET /health response body must contain status=ok."""
        response = client.get("/health")
        data = json.loads(response.data)
        assert data.get("status") == "ok", (
            f"Expected status='ok', got {data}"
        )

    def test_health_body_has_service_name(self, client):
        """GET /health response must include service name."""
        response = client.get("/health")
        data = json.loads(response.data)
        assert "service" in data


# ── 2. Predict endpoint — happy path ──────────────────────────────────────────

class TestPredictEndpoint:
    # Well-known Iris-setosa sample (from the UCI dataset)
    SETOSA_FEATURES = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }

    # Well-known Iris-virginica sample
    VIRGINICA_FEATURES = {
        "sepal_length": 6.3,
        "sepal_width": 3.3,
        "petal_length": 6.0,
        "petal_width": 2.5,
    }

    def test_predict_returns_200(self, client):
        """POST /predict with valid JSON must return HTTP 200."""
        response = client.post(
            "/predict",
            json=self.SETOSA_FEATURES,
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. "
            f"Body: {response.data}"
        )

    def test_predict_setosa(self, client):
        """Setosa features must predict 'setosa'."""
        response = client.post("/predict", json=self.SETOSA_FEATURES)
        data = json.loads(response.data)
        assert data["class_name"] == "setosa", (
            f"Expected 'setosa', got '{data['class_name']}'"
        )

    def test_predict_virginica(self, client):
        """Virginica features must predict 'virginica'."""
        response = client.post("/predict", json=self.VIRGINICA_FEATURES)
        data = json.loads(response.data)
        assert data["class_name"] == "virginica", (
            f"Expected 'virginica', got '{data['class_name']}'"
        )

    def test_predict_response_has_class_index(self, client):
        """Response must include 'class_index' (int)."""
        response = client.post("/predict", json=self.SETOSA_FEATURES)
        data = json.loads(response.data)
        assert "class_index" in data
        assert isinstance(data["class_index"], int)

    def test_predict_response_has_features(self, client):
        """Response must echo back the 4 input features."""
        response = client.post("/predict", json=self.SETOSA_FEATURES)
        data = json.loads(response.data)
        assert "features" in data
        assert len(data["features"]) == 4


# ── 3. Bad-input handling ─────────────────────────────────────────────────────

class TestBadInputHandling:
    def test_missing_field_returns_400(self, client):
        """Request missing 'petal_width' must return HTTP 400."""
        incomplete = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            # petal_width intentionally omitted
        }
        response = client.post("/predict", json=incomplete)
        assert response.status_code == 400, (
            f"Expected 400 for missing field, got {response.status_code}"
        )

    def test_non_json_content_type_returns_400(self, client):
        """Requests with wrong Content-Type must return HTTP 400."""
        response = client.post(
            "/predict",
            data="sepal_length=5.1",
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 400

    def test_invalid_numeric_value_returns_422(self, client):
        """Non-numeric string value must return HTTP 422."""
        bad_data = {
            "sepal_length": "not-a-number",
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        response = client.post("/predict", json=bad_data)
        assert response.status_code == 422

    def test_empty_body_returns_400(self, client):
        """Empty JSON object must return HTTP 400."""
        response = client.post("/predict", json={})
        assert response.status_code == 400
