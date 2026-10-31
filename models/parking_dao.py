import os

import psycopg
from psycopg.rows import dict_row


def list_parking_areas(limit: int, offset: int) -> list[dict]:
    """Retrieve parking areas with GeoJSON geometry."""

    query = """
        SELECT
            parking_area_id,
            name,
            capacity,
            created_at,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM public.parking_area
        ORDER BY parking_area_id
        LIMIT %s OFFSET %s;
    """

    with psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit, offset))
            return cur.fetchall()


def get_parking_area_by_id(parking_area_id: int) -> dict | None:
    """Retrieve a parking area by its ID."""

    query = """
        SELECT
            parking_area_id,
            name,
            capacity,
            created_at,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM public.parking_area
        WHERE parking_area_id = %s;
    """

    with psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (parking_area_id,))
            return cur.fetchone()
