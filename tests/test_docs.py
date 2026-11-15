"""Swagger UI and generated API specification tests."""

from pathlib import Path

import pytest

from app import create_app


@pytest.fixture()
def docs_client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    return app.test_client()


def test_swagger_ui_is_available_at_docs(docs_client):
    response = docs_client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.content_type
    assert b"/apispec_1.json" in response.data
    assert docs_client.get("/flasgger_static/swagger-ui-bundle.js").status_code == 200


def test_docs_trailing_slash_redirects_to_canonical_path(docs_client):
    response = docs_client.get("/docs/", follow_redirects=False)

    assert response.status_code == 308
    assert response.headers["Location"] == "/docs"


def test_openapi_spec_documents_all_api_operations(docs_client):
    response = docs_client.get("/apispec_1.json")

    assert response.status_code == 200
    spec = response.get_json()
    assert spec["info"]["title"] == "Hotel Booking API"
    assert spec["info"]["description"]
    assert spec["info"]["version"]

    availability = spec["paths"]["/api/availability"]["get"]
    assert {parameter["name"] for parameter in availability["parameters"]} == {
        "check_in",
        "check_out",
        "room_type",
    }
    assert {"200", "400", "500"} <= set(availability["responses"])
    assert availability["responses"]["200"]["examples"]["application/json"]

    create_reservation = spec["paths"]["/api/reservations"]["post"]
    assert create_reservation["parameters"][0]["in"] == "body"
    assert {"201", "400", "409", "500"} <= set(create_reservation["responses"])
    assert create_reservation["responses"]["201"]["examples"]["application/json"]

    lookup = spec["paths"]["/api/reservations/lookup"]["post"]
    assert lookup["parameters"][0]["in"] == "body"
    assert {"200", "400", "404", "500"} <= set(lookup["responses"])
    assert lookup["responses"]["200"]["examples"]["application/json"]


def test_local_nginx_proxies_swagger_routes_to_flask():
    nginx_config = (Path(__file__).parents[1] / "nginx" / "nginx.conf").read_text()

    for location in (
        "location = /docs {",
        "location = /docs/ {",
        "location = /apispec_1.json {",
        "location /flasgger_static/ {",
    ):
        start = nginx_config.index(location)
        block = nginx_config[start : nginx_config.index("\n    }", start)]
        assert "proxy_pass http://api:8000" in block
