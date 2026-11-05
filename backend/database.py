"""Shared PostgreSQL connection settings for the REST API."""
import os
import re

import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row


def database_schema():
    name = os.environ.get("DB_SCHEMA", "public")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise RuntimeError("DB_SCHEMA must be a PostgreSQL schema name.")
    return name


def connection():
    settings = {
        "connect_timeout": 10,
        "row_factory": dict_row,
        "options": "-c timezone=UTC",
    }
    url = os.environ.get("DATABASE_URL")
    if not url:
        password = os.environ.get("DB_PASSWORD")
        if not password:
            raise HTTPException(503, "Set DATABASE_URL or DB_PASSWORD before connecting.")
        settings.update(
            host=os.environ.get("DB_HOST", "dpg-dau56j893c1s73cpaaj0-a.virginia-postgres.render.com"),
            port=os.environ.get("DB_PORT", "5432"),
            dbname=os.environ.get("DB_NAME", "dbclass_hanm"),
            user=os.environ.get("DB_USER", "edgar1"),
            password=password,
            sslmode="require",
        )
    return psycopg.connect(url or "", **settings)


def get_db():
    try:
        with connection() as db:
            yield db
    except psycopg.OperationalError:
        raise HTTPException(503, "Database connection unavailable.") from None
