from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier

import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Reservation, Room


def test_health_and_readiness(client):
    assert client.get("/health").status_code == 200
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json["database"] == "available"


def test_availability_returns_room_type_and_dates(client, dates):
    response = client.get(
        "/api/availability",
        query_string={
            "check_in": dates[0],
            "check_out": dates[1],
            "room_type": "standard",
        },
    )
    assert response.status_code == 200
    assert response.json["available_count"] == 2
    assert {room["room_number"] for room in response.json["rooms"]} == {"101", "102"}


def test_reservation_has_unique_reference_and_persists(client, app, reservation_payload):
    first = client.post("/api/reservations", json=reservation_payload)
    second_payload = {**reservation_payload, "guest_email": "grace@example.test"}
    second = client.post("/api/reservations", json=second_payload)
    assert first.status_code == second.status_code == 201
    assert first.json["booking_reference"] != second.json["booking_reference"]
    with app.app_context():
        assert db.session.query(Reservation).count() == 2


def test_reservation_can_be_retrieved_with_reference_and_email(client, reservation_payload):
    created = client.post("/api/reservations", json=reservation_payload)
    reference = created.json["booking_reference"]

    lookup = {"booking_reference": reference, "guest_email": "ADA@EXAMPLE.TEST"}
    found = client.post("/api/reservations/lookup", json=lookup)
    assert found.status_code == 200
    assert found.json["booking_reference"] == reference
    assert found.json["guest_name"] == reservation_payload["guest_name"]
    assert found.json["room_type"] == "standard"

    hidden = client.post(
        "/api/reservations/lookup",
        json={"booking_reference": reference, "guest_email": "someone@example.test"},
    )
    assert hidden.status_code == 404


def test_no_room_returns_conflict(client, reservation_payload):
    assert client.post("/api/reservations", json=reservation_payload).status_code == 201
    assert client.post("/api/reservations", json=reservation_payload).status_code == 201
    response = client.post("/api/reservations", json=reservation_payload)
    assert response.status_code == 409
    assert response.json["error"]["code"] == "no_availability"


def test_invalid_dates_rejected(client, reservation_payload):
    bad = {**reservation_payload, "check_out": reservation_payload["check_in"]}
    assert client.post("/api/reservations", json=bad).status_code == 400
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    bad = {**reservation_payload, "check_in": yesterday}
    assert client.post("/api/reservations", json=bad).status_code == 400


def test_adjacent_stays_do_not_overlap(client, reservation_payload):
    first = client.post("/api/reservations", json=reservation_payload)
    next_day = reservation_payload["check_out"]
    checkout = date.fromisoformat(next_day) + timedelta(days=2)
    second_payload = {
        **reservation_payload,
        "guest_email": "next@example.test",
        "check_in": next_day,
        "check_out": checkout.isoformat(),
    }
    second = client.post("/api/reservations", json=second_payload)
    assert first.status_code == second.status_code == 201
    assert first.json["room_number"] == second.json["room_number"]


def test_database_rejects_overlapping_confirmed_reservations(app, client, reservation_payload):
    """The PostgreSQL exclusion constraint remains effective below the HTTP layer."""
    created = client.post("/api/reservations", json=reservation_payload)
    assert created.status_code == 201
    with app.app_context():
        room = db.session.query(Room).filter_by(room_number=created.json["room_number"]).one()
        duplicate = Reservation(
            guest_name="Concurrent guest",
            guest_email="race@example.test",
            room_id=room.id,
            check_in=date.fromisoformat(reservation_payload["check_in"]),
            check_out=date.fromisoformat(reservation_payload["check_out"]),
        )
        db.session.add(duplicate)
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()


def test_concurrent_requests_cannot_confirm_the_same_room(app, reservation_payload):
    """Two requests racing for the only matching room result in one confirmed stay."""
    with app.app_context():
        extra_room = db.session.query(Room).filter_by(room_number="102").one()
        db.session.delete(extra_room)
        db.session.commit()

    barrier = Barrier(2)

    def submit(email):
        payload = {**reservation_payload, "guest_email": email}
        with app.test_client() as client:
            barrier.wait(timeout=10)
            return client.post("/api/reservations", json=payload).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(submit, ["first@example.test", "second@example.test"]))

    assert sorted(statuses) == [201, 409]


def test_missing_fields_and_invalid_room_type(client, reservation_payload):
    assert client.post("/api/reservations", json={}).status_code == 400
    assert (
        client.get(
            "/api/availability",
            query_string={
                "check_in": reservation_payload["check_in"],
                "check_out": reservation_payload["check_out"],
            },
        ).status_code
        == 400
    )
