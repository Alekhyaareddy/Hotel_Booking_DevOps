"""One-time schema setup, run before starting the web workers."""

from app import create_app, initialize_database

initialize_database(create_app())
