# syntax=docker/dockerfile:1
FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv/hotel-api
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.lock ./
RUN python -m pip install --no-cache-dir -r requirements.txt -c requirements.lock \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app

COPY --chown=app:app app ./app
COPY --chown=app:app database ./database
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1
CMD ["sh", "-c", "python -m app.init_db && exec gunicorn --bind=0.0.0.0:8000 --workers=2 --access-logfile=- --error-logfile=- app.wsgi:app"]
