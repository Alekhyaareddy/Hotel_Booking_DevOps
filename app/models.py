"""Database models and PostgreSQL booking overlap protection."""

import secrets
import string
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


def new_booking_reference() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "HB-" + "".join(secrets.choice(alphabet) for _ in range(10))


class Room(db.Model):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    room_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="room")


class Reservation(db.Model):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="ck_reservation_dates_ordered"),
        ExcludeConstraint(
            ("room_id", "="),
            (text("daterange(check_in, check_out, '[)')"), "&&"),
            where=text("status = 'confirmed'"),
            using="gist",
            name="ex_reservation_room_dates_no_overlap",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_reference: Mapped[str] = mapped_column(
        String(13), unique=True, nullable=False, default=new_booking_reference
    )
    guest_name: Mapped[str] = mapped_column(String(120), nullable=False)
    guest_email: Mapped[str] = mapped_column(String(254), nullable=False)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False
    )
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="confirmed")

    room: Mapped[Room] = relationship(back_populates="reservations")
