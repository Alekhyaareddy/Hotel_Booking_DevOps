"""JSON API endpoints."""

import re
from datetime import date

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Reservation, Room

api = Blueprint("api", __name__, url_prefix="/api")
DATE_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ROOM_TYPES = {"standard", "deluxe", "suite"}


def parse_dates(check_in_value: object, check_out_value: object) -> tuple[date, date] | None:
    if not isinstance(check_in_value, str) or not isinstance(check_out_value, str):
        return None
    if not DATE_FORMAT.fullmatch(check_in_value) or not DATE_FORMAT.fullmatch(check_out_value):
        return None
    try:
        check_in = date.fromisoformat(check_in_value)
        check_out = date.fromisoformat(check_out_value)
    except ValueError:
        return None
    if check_in < date.today() or check_out <= check_in:
        return None
    return check_in, check_out


def invalid_dates_response():
    return jsonify(
        error={
            "code": "invalid_dates",
            "message": (
                "Use YYYY-MM-DD dates; check_in cannot be in the past and "
                "check_out must be after check_in"
            ),
        }
    ), 400


@api.get("/availability")
def availability():
    """Find rooms available for a room type and date range.
    ---
    tags:
      - Availability
    parameters:
      - name: check_in
        in: query
        type: string
        format: date
        required: true
        description: Arrival date in YYYY-MM-DD format; today or a future date.
      - name: check_out
        in: query
        type: string
        format: date
        required: true
        description: Departure date in YYYY-MM-DD format; must be after check_in.
      - name: room_type
        in: query
        type: string
        enum: [standard, deluxe, suite]
        required: true
    responses:
      200:
        description: Available rooms matching the requested type and dates.
        schema:
          $ref: '#/definitions/AvailabilityResponse'
        examples:
          application/json:
            check_in: '2030-06-10'
            check_out: '2030-06-12'
            room_type: standard
            available_count: 1
            rooms:
              - room_number: '101'
                room_type: standard
      400:
        description: Dates are invalid or room_type is unsupported.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error:
              code: invalid_dates
              message: >-
                Use YYYY-MM-DD dates; check_in cannot be in the past and check_out
                must be after check_in
      500:
        description: An unexpected server error occurred.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error:
              code: internal_error
              message: Internal server error
    """
    values = parse_dates(request.args.get("check_in"), request.args.get("check_out"))
    room_type = request.args.get("room_type", "").strip()
    if values is None:
        return invalid_dates_response()
    if room_type not in ROOM_TYPES:
        return jsonify(
            error={
                "code": "invalid_room_type",
                "message": "room_type must be standard, deluxe, or suite",
            }
        ), 400
    check_in, check_out = values
    reserved_room_ids = select(Reservation.room_id).where(
        Reservation.status == "confirmed",
        Reservation.check_in < check_out,
        Reservation.check_out > check_in,
    )
    rooms = db.session.scalars(
        select(Room)
        .where(Room.room_type == room_type, Room.id.not_in(reserved_room_ids))
        .order_by(Room.room_number)
    ).all()
    return jsonify(
        check_in=check_in.isoformat(),
        check_out=check_out.isoformat(),
        room_type=room_type,
        available_count=len(rooms),
        rooms=[{"room_number": room.room_number, "room_type": room.room_type} for room in rooms],
    ), 200


@api.post("/reservations")
def create_reservation():
    """Create a confirmed reservation for the first available matching room.
    ---
    tags:
      - Reservations
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: reservation
        required: true
        description: Guest details, room type, and stay dates.
        schema:
          $ref: '#/definitions/ReservationRequest'
    responses:
      201:
        description: Reservation created.
        schema:
          $ref: '#/definitions/ReservationCreated'
        examples:
          application/json:
            booking_reference: HB-ABC123XYZ9
            status: confirmed
            room_number: '101'
            room_type: standard
            check_in: '2030-06-10'
            check_out: '2030-06-12'
      400:
        description: The JSON body, required fields, guest details, room type, or dates are invalid.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error:
              code: invalid_dates
              message: >-
                Use YYYY-MM-DD dates; check_in cannot be in the past and check_out
                must be after check_in
      409:
        description: No matching room is available, or a concurrent request booked it first.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error:
              code: no_availability
              message: No room is available for those dates
      500:
        description: An unexpected server or integrity error occurred.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error:
              code: internal_error
              message: Internal server error
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error={"code": "invalid_json", "message": "A JSON object is required"}), 400
    required = ("guest_name", "guest_email", "room_type", "check_in", "check_out")
    if any(not isinstance(payload.get(key), str) or not payload[key].strip() for key in required):
        return jsonify(error={"code": "missing_fields", "message": "All fields are required"}), 400
    values = parse_dates(payload["check_in"], payload["check_out"])
    if values is None:
        return invalid_dates_response()
    check_in, check_out = values
    guest_name = payload["guest_name"].strip()
    guest_email = payload["guest_email"].strip().lower()
    room_type = payload["room_type"].strip()
    if room_type not in ROOM_TYPES:
        return jsonify(
            error={
                "code": "invalid_room_type",
                "message": "room_type must be standard, deluxe, or suite",
            }
        ), 400
    if len(guest_name) > 120 or len(guest_email) > 254 or "@" not in guest_email:
        return jsonify(
            error={"code": "invalid_guest", "message": "Guest name or email is invalid"}
        ), 400

    reserved_room_ids = select(Reservation.room_id).where(
        Reservation.status == "confirmed",
        Reservation.check_in < check_out,
        Reservation.check_out > check_in,
    )
    room = db.session.scalar(
        select(Room)
        .where(Room.room_type == room_type, Room.id.not_in(reserved_room_ids))
        .order_by(Room.room_number)
        .limit(1)
    )
    if room is None:
        return jsonify(
            error={"code": "no_availability", "message": "No room is available for those dates"}
        ), 409

    reservation = Reservation(
        guest_name=guest_name,
        guest_email=guest_email,
        room_id=room.id,
        check_in=check_in,
        check_out=check_out,
    )
    db.session.add(reservation)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        # PostgreSQL exclusion violations have SQLSTATE 23P01. Other integrity errors are not
        # booking conflicts and should be reported as server errors.
        if getattr(error.orig, "sqlstate", None) == "23P01":
            return jsonify(
                error={
                    "code": "no_availability",
                    "message": "The room was booked by another request; please retry",
                }
            ), 409
        current_app.logger.exception("Reservation integrity error")
        raise
    current_app.logger.info(
        "Reservation created reference=%s room=%s", reservation.booking_reference, room.room_number
    )
    return jsonify(
        booking_reference=reservation.booking_reference,
        status=reservation.status,
        room_number=room.room_number,
        room_type=room.room_type,
        check_in=check_in.isoformat(),
        check_out=check_out.isoformat(),
    ), 201


@api.post("/reservations/lookup")
def get_reservation():
    """Look up a reservation using its reference and the guest email used to create it.
    ---
    tags:
      - Reservations
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: lookup
        required: true
        description: Booking reference and matching guest email.
        schema:
          $ref: '#/definitions/ReservationLookupRequest'
    responses:
      200:
        description: Matching reservation details.
        schema:
          $ref: '#/definitions/ReservationLookupResponse'
        examples:
          application/json:
            booking_reference: HB-ABC123XYZ9
            status: confirmed
            guest_name: Ada Lovelace
            room_number: '101'
            room_type: standard
            check_in: '2030-06-10'
            check_out: '2030-06-12'
      400:
        description: The JSON body, booking reference, or guest email is missing or invalid.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error:
              code: missing_reference
              message: Booking reference is required
      404:
        description: No reservation matches both the reference and guest email.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error:
              code: reservation_not_found
              message: Booking not found
      500:
        description: An unexpected server error occurred.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error:
              code: internal_error
              message: Internal server error
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error={"code": "invalid_json", "message": "A JSON object is required"}), 400
    booking_reference = payload.get("booking_reference")
    email = payload.get("guest_email")
    if not isinstance(booking_reference, str) or not booking_reference.strip():
        return jsonify(
            error={"code": "missing_reference", "message": "Booking reference is required"}
        ), 400
    if not isinstance(email, str) or not email.strip():
        return jsonify(error={"code": "missing_email", "message": "Guest email is required"}), 400
    booking_reference = booking_reference.strip().upper()
    email = email.strip().lower()

    reservation = db.session.scalar(
        select(Reservation).where(
            Reservation.booking_reference == booking_reference,
            Reservation.guest_email == email,
        )
    )
    if reservation is None:
        return jsonify(error={"code": "reservation_not_found", "message": "Booking not found"}), 404

    return jsonify(
        booking_reference=reservation.booking_reference,
        status=reservation.status,
        guest_name=reservation.guest_name,
        room_number=reservation.room.room_number,
        room_type=reservation.room.room_type,
        check_in=reservation.check_in.isoformat(),
        check_out=reservation.check_out.isoformat(),
    ), 200
