from datetime import datetime, timezone

from psycopg import sql
from backend.database import connection, database_schema


def table(name: str):
    if name not in {"parking_area", "road_segment", "vehicle", "driver", "trip", "location_ping"}:
        raise ValueError("Invalid table")

    return sql.Identifier(
        database_schema(),
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
