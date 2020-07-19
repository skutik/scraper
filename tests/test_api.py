import pytest
from src.flask_api import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_ping(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json["ping"] == "pong"
    assert response.json == {"ping": "pong"}


def test_not_allowed_method(client):
    response = client.post("/ping")
    assert response.status_code == 405
    assert response.json == {"status": "failed", "message": "Method Not Allowed"}


def test_query_estate_limit(client):
    response = client.get("/query_estates?estate_type=1&estate_agr_type=2&limit=99999")
    assert response.status_code == 400
    assert response.json.get("message", "") == "Out of the Allowed Limit or Wrong Value"


def test_query_estate_missing_param(client):
    response = client.get("/query_estates?estate_type=1")
    assert response.status_code == 400
    assert response.json.get("message", "") == "Missing One or More Required Params"


def test_query_estate_unsupported_sorting(client):
    response = client.get("/query_estates?estate_type=1&estate_agr_type=2&sort=last_update_utc&sort_type=-1&sort_type=-1")
    assert response.status_code == 400
    assert response.json.get("message", "") == "Sorting Params Contains More Sorting Types Then Keys"
