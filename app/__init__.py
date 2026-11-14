"""Hotel Room Availability and Reservation API."""

import json
import logging
import os
import time
from datetime import UTC, datetime
from logging.config import dictConfig

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def configure_logging() -> None:
    """Emit structured JSON logs to stdout for Docker and log collectors."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {"stdout": {"class": "logging.StreamHandler", "formatter": "json"}},
            "root": {"level": os.getenv("LOG_LEVEL", "INFO"), "handlers": ["stdout"]},
        }
    )


def create_app(test_config: dict | None = None) -> Flask:
    configure_logging()
    app = Flask(__name__)
    database_url_value = (
        test_config.get("SQLALCHEMY_DATABASE_URI")
        if test_config and test_config.get("SQLALCHEMY_DATABASE_URI")
        else os.getenv("DATABASE_URL")
    )
    if not database_url_value:
        raise RuntimeError("DATABASE_URL must be set for database connections")
    database_url = make_url(database_url_value)
    # Neon and many hosted providers supply a generic PostgreSQL URL. This app uses
    # Psycopg 3, so select its explicit SQLAlchemy dialect when one is not specified.
    if database_url.drivername in {"postgres", "postgresql"}:
        database_url = database_url.set(drivername="postgresql+psycopg")

    engine_options = {}
    if database_url.host and database_url.host.endswith(".neon.tech"):
        # Encrypt every Neon connection. Preserve stronger sslmode values supplied
        # in DATABASE_URL, and add require when the connection string omits it.
        sslmode = database_url.query.get("sslmode")
        if sslmode not in {"require", "verify-ca", "verify-full"}:
            database_url = database_url.set(
                query={**database_url.query, "sslmode": "require"}
            )
        engine_options["pool_pre_ping"] = True

    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_ENGINE_OPTIONS=engine_options,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=True,
        APP_VERSION=os.getenv("APP_VERSION", "dev"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.routes import api

    app.register_blueprint(api)

    @app.get("/health")
    def health():
        return jsonify(status="ok", version=app.config["APP_VERSION"]), 200

    @app.get("/ready")
    def ready():
        try:
            db.session.execute(text("SELECT 1"))
        except OperationalError:
            db.session.rollback()
            return jsonify(status="not_ready", database="unavailable"), 503
        return jsonify(status="ready", database="available"), 200

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error={"code": "not_found", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Unhandled request error: %s", error)
        db.session.rollback()
        return jsonify(error={"code": "internal_error", "message": "Internal server error"}), 500

    return app


def initialize_database(app: Flask, attempts: int = 20, delay: float = 2.0) -> None:
    """Create schema once the database is accepting connections."""
    from app import models  # noqa: F401

    last_error = None
    with app.app_context():
        for attempt in range(attempts):
            try:
                db.session.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
                db.session.commit()
                db.create_all()
                app.logger.info("Database schema is ready")
                return
            except OperationalError as error:
                db.session.rollback()
                last_error = error
                if attempt + 1 < attempts:
                    app.logger.warning(
                        "Database not ready; retrying (%d/%d)", attempt + 1, attempts
                    )
                    time.sleep(delay)
    raise RuntimeError("Could not initialize database") from last_error
