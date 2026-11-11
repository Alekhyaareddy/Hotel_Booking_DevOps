"""Repeatably create a small inventory of rooms."""

from app import create_app, db, initialize_database
from app.models import Room

ROOMS = [
    ("101", "standard"),
    ("102", "standard"),
    ("103", "standard"),
    ("201", "deluxe"),
    ("202", "deluxe"),
    ("301", "suite"),
]


def seed() -> int:
    app = create_app()
    initialize_database(app)
    with app.app_context():
        created = 0
        for number, room_type in ROOMS:
            if db.session.scalar(db.select(Room.id).where(Room.room_number == number)) is None:
                db.session.add(Room(room_number=number, room_type=room_type))
                created += 1
        db.session.commit()
        return created


if __name__ == "__main__":
    print(f"Seed complete; added {seed()} rooms (safe to run again).")
