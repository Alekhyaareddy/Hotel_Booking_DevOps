"""PostgreSQL-backed API test fixtures."""

import os
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app import create_app, db, initialize_database
from app.models import Room


@pytest.fixture()
def app():
    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://hotel_app:hotel_app@localhost:5432/hotel_booking",
    )
    test_app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": database_url})
    initialize_database(test_app)
    with test_app.app_context():
        db.session.execute(text("TRUNCATE reservations, rooms RESTART IDENTITY CASCADE"))
        db.session.add_all(
            [
                Room(room_number="101", room_type="standard"),
                Room(room_number="102", room_type="standard"),
                Room(room_number="201", room_type="deluxe"),
            ]
        )
        db.session.commit()
    yield test_app
    with test_app.app_context():
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def dates():
    start = date.today() + timedelta(days=30)
    return start.isoformat(), (start + timedelta(days=2)).isoformat()


@pytest.fixture()
def reservation_payload(dates):
    return {
        "guest_name": "Ada Lovelace",
        "guest_email": "ada@example.test",
        "room_type": "standard",
        "check_in": dates[0],
        "check_out": dates[1],
    }
