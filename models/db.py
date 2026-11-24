import os
from datetime import datetime, timezone

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


def connection():
    return psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    )


def table(name: str):
    if name not in {
        "parking_area", "road_segment", "driver", "vehicle", "trip",
        "location_ping", "vehicle_assignment", "vehicle_status", "vehicle_type",
        "vehicle_kind", "fuel_type"
    }:
        raise ValueError("Invalid table")

    return sql.Identifier(
        os.getenv("DB_SCHEMA", "public"),
        name
    )


def normalize_record(record):
    """Convert timestamps to JSON-friendly ISO 8601 strings."""

    if record is None:
        return None

    out = dict(record)

    for key, value in out.items():
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)

            out[key] = value.isoformat().replace("+00:00", "Z")

    return out


def check_postgis_geometry(geom_json: str, geometry_type: str):
    """Validate geometry with PostGIS before inserting or updating."""

    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    ST_IsValid(g) AS valid,
                    ST_GeometryType(g) AS kind
                FROM (
                    SELECT ST_SetSRID(
                        ST_GeomFromGeoJSON(%s),
                        4326
                    ) AS g
                ) AS q;
            """, (geom_json,))

            result = cur.fetchone()

    if (
        not result["valid"]
        or result["kind"] != "ST_" + geometry_type
    ):
        raise ValueError("Invalid or unsupported geometry")
